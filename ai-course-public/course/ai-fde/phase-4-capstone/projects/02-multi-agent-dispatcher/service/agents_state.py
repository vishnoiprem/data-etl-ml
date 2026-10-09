"""
service/agents_state.py — Shared state object for the multi-agent dispatcher.

What this file does
-------------------
A single dataclass that flows through the orchestrator graph. Each agent
(Mei, Sarah, Daniel) reads from this state, mutates a slice, and passes it
on. The shared state is the "bus" that makes the 3 agents cooperate
without re-querying the email or the shipment data.

In production (Phase 5), this state would be a Redis hash. In Phase 4,
it's an in-memory dict — fast to test, no infra to stand up.

Key design choices
------------------
1. **One state, three writers** — Mei writes `mei_draft`; Sarah writes
   `sarah_summary`; Daniel writes `daniel_note`. The orchestrator
   guarantees no two agents write to the same field.
2. **The state is typed** — every field has a type, so a wrong shape
   surfaces as a TypeError at the agent boundary, not a runtime KeyError
   deep in a prompt.
3. **The state is append-only on `trace`** — agents append, never replace.
   The trace is the audit log; rewriting it would lose data.
4. **The state carries the user identity** — `user_id` and `role` flow
   through. Each sub-agent uses them to enforce per-user rate limits
   and RBAC when calling the MCP server.

Why a separate file
-------------------
The state is the contract between agents. If you change a field name
without updating every reader, the orchestrator silently drops data.
A dedicated file with a dataclass + a `to_dict()` method makes the
contract explicit and testable.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class DispatcherState:
    """The state that flows through the LangGraph orchestrator.

    The orchestrator instantiates one of these per request. Each agent
    reads from it, mutates a slice, and returns it. The trace list is
    append-only.
    """

    # ---- Input (set by the orchestrator at the start) ---------------------
    request_id: str = ""                    # correlation id
    user_id: str = ""                       # the CS user asking
    role: str = "cs_junior"                 # for RBAC
    email_body: str = ""                    # the raw email text
    shipment_ids: list[str] = field(default_factory=list)  # extracted PF-XXXX ids
    # The email might reference multiple shipments; the orchestrator
    # extracts them via regex at the start of the run.

    # ---- Per-agent outputs (set by each agent) ----------------------------
    mei_draft: Optional[str] = None         # Mei's reply to the customer
    sarah_summary: Optional[str] = None     # Sarah's ops summary
    daniel_note: Optional[str] = None       # Daniel's cost/risk note
    agent_path: list[str] = field(default_factory=list)  # which agents ran, in order

    # ---- Cross-cutting state ---------------------------------------------
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    # Each MCP tool call the orchestrator made. Used for the audit log.

    cost_usd: float = 0.0                   # running total for the request
    risk_level: str = "low"                 # "low" | "medium" | "high"

    trace: list[dict[str, Any]] = field(default_factory=list)
    # Append-only audit log: one entry per agent that ran, with timestamps.

    # ---- Bookkeeping -----------------------------------------------------
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    error: Optional[str] = None             # the error message if the run failed

    # ---- Methods --------------------------------------------------------
    def append_trace(self, agent: str, **kwargs: Any) -> None:
        """Append a structured trace entry. The trace is the audit log."""
        self.trace.append({
            "ts": time.time(),
            "agent": agent,
            **kwargs,
        })

    def mark_finished(self, error: Optional[str] = None) -> None:
        self.finished_at = time.time()
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        """JSON-safe serialization for the /dispatch response + audit log."""
        d = asdict(self)
        # dataclasses.asdict recurses into lists/dicts; we don't have any
        # non-JSON values, so this is safe.
        return d

    def latency_ms(self) -> int:
        if self.finished_at is None:
            return 0
        return int((self.finished_at - self.started_at) * 1000)
