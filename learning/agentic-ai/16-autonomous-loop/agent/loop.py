"""
Autonomous agent loop with guardrails.

Step budget, cost budget, per-tool rate limit, per-tool allowlist,
output schema validation, and a kill switch.

The shape AutoGPT popularized, but with the bits that make it safe
to actually run on a real machine.
"""
from __future__ import annotations
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Callable, Optional

from pydantic import BaseModel, ValidationError


class ToolCall(BaseModel):
    tool: str
    args: dict


@dataclass
class Guardrails:
    max_steps: int = 50
    max_cost_usd: float = 2.0
    max_runtime_s: int = 1800
    tool_allowlist: set[str] = field(default_factory=set)
    per_tool_rate_limit: dict[str, int] = field(default_factory=lambda: defaultdict(lambda: 5))

    steps_used: int = 0
    cost_used: float = 0.0
    started_at: float = field(default_factory=time.time)
    stopped: bool = False
    _tool_calls: dict[str, deque] = field(default_factory=lambda: defaultdict(lambda: deque(maxlen=100)))

    def can_call(self, tool: str) -> tuple[bool, str]:
        if self.stopped:
            return False, "kill switch"
        if self.steps_used >= self.max_steps:
            return False, "step budget"
        if self.cost_used >= self.max_cost_usd:
            return False, "cost ceiling"
        if time.time() - self.started_at >= self.max_runtime_s:
            return False, "runtime cap"
        if tool not in self.tool_allowlist:
            return False, f"tool not in allowlist: {tool}"
        # Per-tool rate limit: 5 calls in any 60s window
        recent = [t for t in self._tool_calls[tool] if time.time() - t < 60]
        limit = self.per_tool_rate_limit[tool]
        if len(recent) >= limit:
            return False, f"rate limit: {limit}/min on {tool}"
        return True, ""

    def record(self, tool: str, cost: float):
        self.steps_used += 1
        self.cost_used += cost
        self._tool_calls[tool].append(time.time())


class Agent:
    def __init__(
        self,
        planner: Callable[[dict], ToolCall],
        runner: Callable[[ToolCall], dict],
        guardrails: Guardrails,
    ):
        self.planner = planner
        self.runner = runner
        self.g = guardrails

    def step(self) -> dict:
        state = {}
        call = self.planner(state)
        ok, reason = self.g.can_call(call.tool)
        if not ok:
            return {"status": "blocked", "tool": call.tool, "reason": reason}
        try:
            out = self.runner(call)
        except ValidationError as e:
            return {"status": "schema_error", "tool": call.tool, "errors": e.errors()}
        self.g.record(call.tool, cost=out.get("cost_usd", 0.0))
        return {"status": "ok", "tool": call.tool, "output": out}

    def run(self, max_iters: int = 100) -> list[dict]:
        out = []
        for _ in range(max_iters):
            r = self.step()
            out.append(r)
            if r["status"] != "ok":
                break
        return out


if __name__ == "__main__":
    # Toy: agent that wants to call 'read' 100 times
    g = Guardrails(max_steps=10, max_cost_usd=1.0, tool_allowlist={"read", "search"})
    def toy_planner(state): return ToolCall(tool="read", args={"path": "x.py"})
    def toy_runner(call): return {"cost_usd": 0.01, "content": "..."}
    a = Agent(planner=toy_planner, runner=toy_runner, guardrails=g)
    for r in a.run():
        print(r)
