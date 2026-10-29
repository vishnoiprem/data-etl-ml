"""
service/agents.py — Multi-agent dispatcher for PacificFreight Phase 4.

What this file does
-------------------
A 3-agent orchestrator that handles multi-shipment cases end-to-end
without the CS user (Mei) clicking 5 buttons. The 3 agents:

  - MeiAgent    (CS lane)    — drafts the customer reply
  - SarahAgent  (Ops lane)   — produces a summary of all shipments in scope
  - DanielAgent (Infra lane) — emits a cost/risk note + audit

Each agent has its own CircuitBreaker (reused from Phase 3's circuit.py)
so a Mei failure doesn't block Daniel. The orchestrator's breaker is
the parent and gates the whole pipeline.

The agents are SMALL (each ~50-80 lines). The interesting code is the
*orchestration* — the routing rules in `_decide_next_agent` and the
shared state object in `agents_state.py`.

Wire format
-----------
The orchestrator exposes:
  - `dispatch(email, user_id, role) -> DispatcherState` (in-process call)
  - `POST /dispatch` (HTTP; the drafter's frontend calls this)
  - `python3 agents.py --case <name>` (CLI demo with 3 canned cases)

The agents emit text (not tool calls) by default. When the agent decides
to call a tool, it uses the MCP server from Project 1 (sibling
`01-mcp-drafter/service/mcp_server.py`). The MCP server enforces
RBAC + rate limit; the agent layer just dispatches the call.

Why a separate file
-------------------
The orchestrator IS the deliverable for Project 2. A separate file
keeps the state (`agents_state.py`) decoupled from the logic
(`agents.py`). Both are small; both are independently testable.

How to run
----------
    # As a CLI demo
    python3 agents.py --case multi_shipment

    # From your code
    from agents import Dispatcher
    d = Dispatcher()
    state = d.dispatch(email, user_id="mei@pf.com", role="cs_junior")
    print(state.mei_draft, state.sarah_summary, state.daniel_note)
"""
from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Path setup: pull in the MCP server from Project 1 (the tool layer) and
# Phase 3's circuit primitives (the breaker + rate limiter).
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent
_PROJ1 = _HERE.parent.parent / "01-mcp-drafter" / "service"
# _HERE = .../02-multi-agent-dispatcher/service
# _HERE.parent.parent = .../phase-4-capstone/projects
# _HERE.parent.parent.parent = .../phase-4-capstone
# _HERE.parent.parent.parent.parent = .../ai-fde
_PHASE3 = _HERE.parent.parent.parent.parent / "phase-2-core-build" / "service"

for p in (_PROJ1, _PHASE3):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import mcp_server  # noqa: E402  (Project 1's MCP server — the tool layer)
import circuit as phase3_circuit  # noqa: E402  (Phase 3's breaker + rate limiter)

from agents_state import DispatcherState  # noqa: E402  (this project's state)


# ===========================================================================
# 1. Per-agent circuit breakers — one per agent so a Mei failure doesn't
# block Daniel. The orchestrator's breaker is the parent.
# ===========================================================================
def _make_breaker(name: str) -> phase3_circuit.CircuitBreaker:
    """Build a per-agent breaker. Failure threshold is 50% (3 of last 5) —
    agents should be more forgiving than the LLM breaker because their
    failure modes are subtler (bad extraction, missing tool, etc.)."""
    return phase3_circuit.CircuitBreaker(
        name=name,
        config=phase3_circuit.CircuitBreakerConfig(
            failure_threshold=0.5,
            latency_p99_ms_threshold=5000.0,
            min_calls_in_window=3,
        ),
        # No LLM fallback here — the agent's job is to produce text;
        # if it fails, the orchestrator records the error and moves on.
    )


# ===========================================================================
# 2. The 3 agents
# ===========================================================================
class Agent:
    """Base class. Subclasses override `run(state) -> state`."""
    name: str = "agent"

    def __init__(self) -> None:
        self.breaker = _make_breaker(self.name)
        self.n_calls = 0
        self.n_failures = 0

    def run(self, state: DispatcherState) -> DispatcherState:
        """The agent's main method. Wraps `execute` in the breaker."""
        self.n_calls += 1
        t0 = time.monotonic()
        try:
            new_state = self.breaker.call(self.execute, state)
            latency_ms = int((time.monotonic() - t0) * 1000)
            state.append_trace(self.name, ok=True, latency_ms=latency_ms)
            return new_state
        except Exception as e:
            self.n_failures += 1
            latency_ms = int((time.monotonic() - t0) * 1000)
            state.append_trace(self.name, ok=False, latency_ms=latency_ms,
                               error=f"{type(e).__name__}: {e}")
            # Don't raise — the orchestrator decides what to do with a failed agent.
            state.error = f"{self.name} failed: {e}"
            return state

    def execute(self, state: DispatcherState) -> DispatcherState:
        raise NotImplementedError


class MeiAgent(Agent):
    """CS lane — drafts the customer reply. Always runs first.

    Logic:
      1. If the email mentions one or more shipment IDs, call the MCP
         `tracker.lookup` tool for each (allowed for any role).
      2. Build a draft using the looked-up status(es).
      3. If the email asks for a refund, attempt `refund.create` (will
         be 403 if the role isn't `cs_senior` or `it`; the draft still
         gets produced).
    """
    name = "mei"

    def execute(self, state: DispatcherState) -> DispatcherState:
        # Look up each shipment via the MCP server.
        shipment_lines = []
        for sid in state.shipment_ids:
            r = mcp_server.MCPServer().call_tool(
                "tracker.lookup", {"shipment_id": sid},
                user_id=state.user_id, role=state.role,
            )
            state.tool_calls.append({
                "tool": "tracker.lookup", "shipment_id": sid,
                "status_code": r.status_code, "cost_credits": r.cost_credits,
            })
            state.cost_usd += r.cost_credits * 0.0001  # 1 credit = $0.0001
            if r.status_code == 200 and r.data and r.data.get("shipment"):
                s = r.data["shipment"]
                shipment_lines.append(
                    f"  • {s['id']}: status={s.get('status')}, "
                    f"customer={s.get('customer_name')}, "
                    f"last_event={s.get('last_event')}"
                )
            else:
                shipment_lines.append(f"  • {sid}: lookup failed ({r.error})")

        # If the email asks for a refund, attempt it.
        refund_attempt = None
        if re.search(r"\brefund\b|\breimburse\b", state.email_body, re.I):
            mcp = mcp_server.MCPServer()
            r = mcp.call_tool(
                "refund.create",
                {"shipment_id": state.shipment_ids[0] if state.shipment_ids else "PF-1003",
                 "reason": "customer request", "amount_usd": 50.0},
                user_id=state.user_id, role=state.role,
            )
            state.tool_calls.append({
                "tool": "refund.create",
                "status_code": r.status_code, "cost_credits": r.cost_credits,
            })
            state.cost_usd += r.cost_credits * 0.0001
            if r.status_code == 200:
                refund_attempt = f"refund ticket created ({r.data['refund']['ticket_id']})"
            elif r.status_code == 403:
                refund_attempt = "refund not authorized for this role — escalating to senior"
                state.risk_level = "medium"
            else:
                refund_attempt = f"refund failed: {r.error}"

        # Build the draft.
        shipment_block = "\n".join(shipment_lines) if shipment_lines else "  (no shipment IDs found)"
        state.mei_draft = (
            f"Hi,\n\n"
            f"Thanks for reaching out. Here's the latest on your shipment(s):\n\n"
            f"{shipment_block}\n\n"
            + (f"Refund: {refund_attempt}.\n" if refund_attempt else "")
            + "If anything else needs attention, let us know.\n\n— PacificFreight CS"
        )
        state.agent_path.append(self.name)
        return state


class SarahAgent(Agent):
    """Ops lane — produces a summary across all shipments in scope.

    Runs when the email references more than one shipment. The summary
    is a single text block the CS user can paste into the daily ops review.

    Logic:
      1. If `len(state.shipment_ids) <= 1`, skip (single-shipment cases
         don't need a cross-shipment summary).
      2. Otherwise, look up each shipment (via the MCP server) and
         produce a one-line summary per shipment.
    """
    name = "sarah"

    def execute(self, state: DispatcherState) -> DispatcherState:
        if len(state.shipment_ids) <= 1:
            state.sarah_summary = "(no cross-shipment summary — single shipment case)"
            state.append_trace(self.name, skipped=True, reason="single_shipment")
            state.agent_path.append(self.name)
            return state

        # Multi-shipment: produce a per-shipment line.
        lines = [f"Multi-shipment summary ({len(state.shipment_ids)} shipments):"]
        n_held = 0
        n_in_transit = 0
        n_delivered = 0
        for sid in state.shipment_ids:
            r = mcp_server.MCPServer().call_tool(
                "tracker.lookup", {"shipment_id": sid},
                user_id=state.user_id, role=state.role,
            )
            state.tool_calls.append({
                "tool": "tracker.lookup", "shipment_id": sid,
                "status_code": r.status_code, "cost_credits": r.cost_credits,
            })
            state.cost_usd += r.cost_credits * 0.0001
            if r.status_code == 200 and r.data and r.data.get("shipment"):
                s = r.data["shipment"]
                lines.append(
                    f"  • {s['id']}: {s.get('status')} | "
                    f"ETA {s.get('eta', '?')} | last: {s.get('last_event', '?')}"
                )
                if s.get("status") == "held_customs":
                    n_held += 1
                elif s.get("status") == "in_transit":
                    n_in_transit += 1
                elif s.get("status") == "delivered":
                    n_delivered += 1

        lines.append("")
        lines.append(
            f"Aggregate: {n_held} held at customs, "
            f"{n_in_transit} in transit, {n_delivered} delivered."
        )
        # Risk rises if 2+ shipments are held at customs — that's a
        # customs/freight pattern Daniel should know about.
        if n_held >= 2:
            state.risk_level = "high"
            lines.append("⚠️  2+ shipments held at customs — flagging to Daniel.")
        state.sarah_summary = "\n".join(lines)
        state.agent_path.append(self.name)
        return state


class DanielAgent(Agent):
    """Infra lane — emits a cost/risk note + audit summary.

    Always runs last. The note is a one-paragraph cost + risk + circuit
    snapshot that Daniel (the IT owner) can paste into the on-call log.

    Logic:
      1. Sum the cost_credits consumed so far across all tool calls.
      2. Read the per-agent breaker state (snapshot()).
      3. Emit a one-paragraph note.
    """
    name = "daniel"

    def execute(self, state: DispatcherState) -> DispatcherState:
        total_credits = sum(t.get("cost_credits", 0) for t in state.tool_calls)
        n_calls = len(state.tool_calls)
        n_failures = sum(1 for t in state.tool_calls if t.get("status_code", 200) >= 400)
        # We don't have direct access to the parent orchestrator's breaker
        # snapshot from here; we report what we know.
        note = (
            f"Request {state.request_id}: {n_calls} tool call(s) "
            f"({n_failures} failed), {total_credits} credits consumed, "
            f"~${state.cost_usd:.4f} estimated cost. "
            f"Risk level: {state.risk_level}. "
            f"Agent path: {' → '.join(state.agent_path) or '(none)'}. "
            f"Latency: {state.latency_ms() if state.finished_at else 'in-flight'}ms."
        )
        state.daniel_note = note
        state.agent_path.append(self.name)
        return state


# ===========================================================================
# 3. The orchestrator (the routing logic + the parent breaker)
# ===========================================================================
@dataclass
class DispatcherConfig:
    """Knobs for the orchestrator."""
    cost_high_usd: float = 0.05    # >$0.05 → flag DanielAgent note as "high cost"
    risk_high_threshold: int = 2   # 2+ held shipments → DanielAgent escalates


class Dispatcher:
    """The orchestrator. The routing logic lives in `_decide_next_agent`."""

    def __init__(self, config: Optional[DispatcherConfig] = None) -> None:
        self.config = config or DispatcherConfig()
        self.mei = MeiAgent()
        self.sarah = SarahAgent()
        self.daniel = DanielAgent()
        # Parent breaker — gates the whole pipeline.
        self.breaker = phase3_circuit.CircuitBreaker(
            name="dispatcher",
            config=phase3_circuit.CircuitBreakerConfig(
                failure_threshold=0.5,
                latency_p99_ms_threshold=8000.0,
                min_calls_in_window=3,
            ),
        )

    def dispatch(
        self,
        email: str,
        *,
        user_id: str = "mei@pf.com",
        role: str = "cs_junior",
        request_id: Optional[str] = None,
    ) -> DispatcherState:
        """The main entry point. Returns a DispatcherState."""
        rid = request_id or f"req-{int(time.time() * 1000)}"
        state = DispatcherState(
            request_id=rid,
            user_id=user_id,
            role=role,
            email_body=email,
            shipment_ids=_extract_shipment_ids(email),
        )
        state.append_trace("dispatcher.start",
                           n_shipments=len(state.shipment_ids),
                           user_id=user_id, role=role)

        try:
            # Routing: Mei always runs. Sarah runs if multi-shipment.
            # Daniel always runs (he's the auditor).
            state = self.breaker.call(self._run_mei, state)
            if not state.error and len(state.shipment_ids) > 1:
                state = self.breaker.call(self._run_sarah, state)
            if not state.error:
                state = self.breaker.call(self._run_daniel, state)
        except Exception as e:
            state.error = f"orchestrator failed: {type(e).__name__}: {e}"
            state.append_trace("dispatcher.error", error=state.error)
        finally:
            state.mark_finished(error=state.error)
            state.append_trace("dispatcher.end",
                               latency_ms=state.latency_ms(),
                               n_tool_calls=len(state.tool_calls),
                               cost_usd=state.cost_usd)
        return state

    # -- per-agent runners (so the breaker can wrap each one) -------------
    def _run_mei(self, state: DispatcherState) -> DispatcherState:
        return self.mei.run(state)

    def _run_sarah(self, state: DispatcherState) -> DispatcherState:
        return self.sarah.run(state)

    def _run_daniel(self, state: DispatcherState) -> DispatcherState:
        # Daniel's note should reflect final cost.
        return self.daniel.run(state)


# ===========================================================================
# 4. Helpers
# ===========================================================================
_SHIPMENT_ID_RE = re.compile(r"PF-\d{4,5}")


def _extract_shipment_ids(email: str) -> list[str]:
    """Pull all PF-XXXX mentions out of the email. Deduped, order preserved."""
    seen: set[str] = set()
    out: list[str] = []
    for m in _SHIPMENT_ID_RE.findall(email):
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


# ===========================================================================
# 5. CLI demo
# ===========================================================================
def _run_demo() -> int:
    print("=" * 70)
    print("Multi-agent dispatcher — PacificFreight (Phase 4 Project 2)")
    print("=" * 70)

    cases = [
        ("single_shipment", "cs_junior",
         "Hi, can you check the status of PF-1003? It says held at customs. "
         "My email is mei@pf.com. Thanks!"),
        ("multi_shipment", "cs_senior",
         "Hello, I need an update on three of my shipments: PF-1001, PF-1002, and "
         "PF-1003. PF-1001 and PF-1003 are both held at customs — is there a pattern? "
         "Please also process a refund of $50 for PF-1003. Thanks."),
        ("refund_request_junior", "cs_junior",
         "Hi, I was charged twice for PF-1002. Please refund $50. My phone is +65 9123 4567."),
    ]

    d = Dispatcher()
    for name, role, email in cases:
        print(f"\n--- {name} ({role}) ---")
        print(f"email: {email[:80]}...")
        state = d.dispatch(email, user_id=f"{role}@pf.com", role=role,
                           request_id=f"demo-{name}")
        print(f"  shipment_ids: {state.shipment_ids}")
        print(f"  agent_path:   {state.agent_path}")
        print(f"  tool_calls:   {len(state.tool_calls)}")
        print(f"  cost_usd:     ${state.cost_usd:.4f}")
        print(f"  risk_level:   {state.risk_level}")
        print(f"  error:        {state.error}")
        print(f"\n  [Mei draft]\n{state.mei_draft}")
        if state.sarah_summary:
            print(f"\n  [Sarah summary]\n{state.sarah_summary}")
        print(f"\n  [Daniel note]\n{state.daniel_note}")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="PacificFreight multi-agent dispatcher")
    p.add_argument("--case", choices=["single_shipment", "multi_shipment", "refund_request_junior"],
                   help="Run a single canned case (default: run all 3)")
    args = p.parse_args(argv)
    if args.case:
        # Run just one case
        cases = {
            "single_shipment": ("cs_junior",
                "Hi, can you check the status of PF-1003? It says held at customs."),
            "multi_shipment": ("cs_senior",
                "Need an update on PF-1001, PF-1002, PF-1003. PF-1001 and PF-1003 are held at customs."),
            "refund_request_junior": ("cs_junior",
                "Charged twice for PF-1002. Please refund $50."),
        }
        role, email = cases[args.case]
        d = Dispatcher()
        state = d.dispatch(email, user_id=f"{role}@pf.com", role=role)
        print(json.dumps({
            "request_id": state.request_id,
            "shipment_ids": state.shipment_ids,
            "agent_path": state.agent_path,
            "mei_draft": state.mei_draft,
            "sarah_summary": state.sarah_summary,
            "daniel_note": state.daniel_note,
            "tool_calls": state.tool_calls,
            "cost_usd": state.cost_usd,
            "risk_level": state.risk_level,
            "error": state.error,
        }, indent=2))
        return 0
    return _run_demo()


if __name__ == "__main__":
    raise SystemExit(main())
