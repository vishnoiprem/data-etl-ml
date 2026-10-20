"""agent.gates — pure-function budget/retry reasoning.

The mirror principle this file enforces:

    Every action that costs money (training step, served request) must ask
    the gate first. The gate returns (allowed: bool, reason: str).

Mirrors `16-autonomous-loop/agent/loop.py:Guardrails` semantics, but adapted
for ML cost instead of agent-step cost. The reason string is logged to MLflow
on every denial, so you can audit *why* a run stopped.

The contracts here are deliberately *pure functions* — no I/O, no logging side
effects. That makes them cheap to test and safe to call from a tight loop.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Tuple


# Public type alias — every gate returns (allowed, reason).
Decision = Tuple[bool, str]


@dataclass
class TrainSpend:
    """Running counters for a training run."""

    spent_usd: float = 0.0
    started_at: float = field(default_factory=time.monotonic)
    steps: int = 0


def train_budget(spend: TrainSpend, max_usd: float, max_seconds: int) -> Decision:
    """Stop training the next time we are asked.

    Returns `(True, "ok")` while spend is under both caps, otherwise
    `(False, "exceeded_...")` with the specific reason. The reason matters
    because it's the only signal a human sees if the run dies silently.
    """
    elapsed = time.monotonic() - spend.started_at
    if spend.spent_usd >= max_usd:
        return False, f"exceeded_budget_usd ({spend.spent_usd:.2f} >= {max_usd:.2f})"
    if elapsed >= max_seconds:
        return False, f"exceeded_wall_clock ({elapsed:.0f}s >= {max_seconds}s)"
    return True, "ok"


def retry_policy(attempt: int, max_retry: int, last_error: str = "") -> Decision:
    """Why this exists: a 429 from vLLM should back off; a 500 from
    a malformed prompt should not. Both surface as a generic exception in
    the client; the gate makes the policy decision deterministic.
    """
    if attempt >= max_retry:
        return False, f"retry_exhausted (attempt={attempt} >= max={max_retry}): {last_error}"
    return True, "ok"


def cost_estimate_usd(input_tokens: int, output_tokens: int, input_per_1m: float, output_per_1m: float) -> float:
    """One-liner used by both training cost attribution and serving cost reports.

    Keeping it here (not in `monitor.py`) avoids a circular import — monitor
    imports gates for the budget reasoning, not the other way around.
    """
    return (input_tokens / 1_000_000.0) * input_per_1m + (output_tokens / 1_000_000.0) * output_per_1m


def per_request_cost_usd(input_tokens: int, output_tokens: int, input_per_1m: float, output_per_1m: float) -> float:
    """Per-request cost; same math as `cost_estimate_usd`, named for readability at the call site."""
    return cost_estimate_usd(input_tokens, output_tokens, input_per_1m, output_per_1m)
