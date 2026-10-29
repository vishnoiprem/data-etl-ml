"""
Terminal agent loop with approval gate.

The agent:
  1. Plans a sub-task.
  2. Picks a tool.
  3. If the tool is destructive, ask the user.
  4. Runs the tool.
  5. If the result is "stuck" (same tool, same args, no progress), stop.
"""
from __future__ import annotations
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Optional

from pydantic import BaseModel


class ToolCall(BaseModel):
    tool: str
    args: dict
    is_destructive: bool = False


DESTRUCTIVE = {"delete", "drop", "kill", "force_push", "rm", "truncate"}


class AgentLoop:
    def __init__(
        self,
        tool_runner: Callable[[ToolCall], dict],
        approval_fn: Optional[Callable[[ToolCall], bool]] = None,
        max_steps: int = 30,
        stuck_window: int = 3,
    ):
        self.tool_runner = tool_runner
        self.approval_fn = approval_fn
        self.max_steps = max_steps
        self.stuck_window = stuck_window
        self._recent: deque[ToolCall] = deque(maxlen=stuck_window)

    def _is_stuck(self, call: ToolCall) -> bool:
        return len(self._recent) == self.stuck_window and all(
            c.tool == call.tool and c.args == call.args for c in self._recent
        )

    def step(self, call: ToolCall) -> dict:
        # Destructive? Ask.
        if call.tool in DESTRUCTIVE or call.is_destructive:
            if self.approval_fn and not self.approval_fn(call):
                return {"status": "rejected", "call": call.model_dump()}

        # Stuck? Stop.
        if self._is_stuck(call):
            return {"status": "stuck", "reason": f"same call {self.stuck_window}x in a row", "call": call.model_dump()}

        # Run.
        t0 = time.time()
        result = self.tool_runner(call)
        result["duration_ms"] = int((time.time() - t0) * 1000)
        result["status"] = "ok"
        self._recent.append(call)
        return result

    def run(self, planner: Callable[[dict], ToolCall]) -> list[dict]:
        """Run the loop until the planner returns a 'finish' tool or max_steps."""
        out = []
        state = {}
        for i in range(self.max_steps):
            call = planner(state)
            if call.tool == "finish":
                break
            result = self.step(call)
            out.append(result)
            if result.get("status") in ("rejected", "stuck"):
                break
            state[call.tool] = result
        return out


if __name__ == "__main__":
    # Toy run
    def toy_tool_runner(call: ToolCall) -> dict:
        return {"output": f"ran {call.tool} with {call.args}"}

    def toy_planner(state: dict) -> ToolCall:
        return ToolCall(tool="read", args={"path": f"file_{len(state)}.py"})

    loop = AgentLoop(tool_runner=toy_tool_runner, approval_fn=lambda c: True)
    results = loop.run(toy_planner)
    print(f"executed {len(results)} steps")
