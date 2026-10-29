"""
Guardrails for a general-purpose agent.

Hard limits on steps, cost, runtime, and tool allowlist. When any
limit is hit, the agent stops and returns what it has.

The shape every Manus / AutoGPT / Devin productionization converges on.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field


@dataclass
class Guardrails:
    max_steps: int = 50
    max_cost_usd: float = 2.00
    max_runtime_s: int = 1800
    tool_allowlist: set[str] = field(default_factory=lambda: {"browser", "read", "write", "search"})

    # State
    steps_used: int = 0
    cost_used: float = 0.0
    started_at: float = field(default_factory=time.time)

    def record_step(self, cost: float = 0.0):
        self.steps_used += 1
        self.cost_used += cost

    def check(self) -> tuple[bool, str]:
        """Returns (ok, reason_if_not)."""
        if self.steps_used >= self.max_steps:
            return False, f"step budget exhausted ({self.steps_used}/{self.max_steps})"
        if self.cost_used >= self.max_cost_usd:
            return False, f"cost ceiling hit (${self.cost_used:.2f}/${self.max_cost_usd:.2f})"
        runtime = time.time() - self.started_at
        if runtime >= self.max_runtime_s:
            return False, f"runtime cap hit ({runtime:.0f}s/{self.max_runtime_s}s)"
        return True, ""

    def is_tool_allowed(self, tool: str) -> bool:
        return tool in self.tool_allowlist

    def status(self) -> dict:
        runtime = time.time() - self.started_at
        return {
            "steps": f"{self.steps_used}/{self.max_steps}",
            "cost": f"${self.cost_used:.2f}/${self.max_cost_usd:.2f}",
            "runtime": f"{runtime:.0f}s/{self.max_runtime_s}s",
            "tools": sorted(self.tool_allowlist),
        }


if __name__ == "__main__":
    g = Guardrails()
    for i in range(5):
        g.record_step(cost=0.05)
        ok, reason = g.check()
        print(f"step {i+1}: ok={ok} status={g.status()}")
