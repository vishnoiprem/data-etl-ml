"""
Computer-use agent: VLM -> action -> verify -> log -> repeat.

Each step:
  1. Take a screenshot.
  2. Ask the VLM: "given this task, what's the next action?"
  3. Parse the action.
  4. Verify the action's target is actually visible.
  5. Execute.
  6. Log (screenshot, action, result) for replay.
"""
from __future__ import annotations
import base64
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from pydantic import BaseModel


class Action(BaseModel):
    kind: str           # "click" | "type" | "scroll" | "wait" | "done"
    x: int | None = None
    y: int | None = None
    text: str | None = None
    target: str | None = None       # human-readable description of the target element


@dataclass
class ReplayEntry:
    ts: float
    task: str
    screenshot_before: str         # base64 or path
    action: Action
    result: str                    # "ok" | "no_button_at_xy" | "modal_unexpected" | etc.
    reasoning: str = ""


class VLM:
    """Toy VLM. Real impl: Claude / GPT-4V / Gemini."""

    def next_action(self, task: str, screenshot_b64: str) -> Action:
        # Real impl:
        # response = client.messages.create(
        #     model="claude-3-5-sonnet-20241022",
        #     messages=[{"role": "user",
        #                "content": [{"type": "image", "source": {"type": "base64", "data": screenshot_b64}},
        #                            {"type": "text", "text": f"task: {task}. respond with JSON action."}]}],
        # )
        # return Action(**json.loads(response.content[0].text))
        return Action(kind="click", x=420, y=210, target="Submit")


def is_button_visible(screenshot_b64: str, target: str) -> bool:
    """Toy. Real impl: ask the VLM 'is this exact button visible at coordinates X,Y?'"""
    return True  # placeholder


class Agent:
    def __init__(
        self,
        vlm: VLM,
        executor: Callable[[Action], str],   # returns "ok" / "no_button" / etc.
        task: str,
        max_actions: int = 30,
        replay_dir: Optional[Path] = None,
    ):
        self.vlm = vlm
        self.executor = executor
        self.task = task
        self.max_actions = max_actions
        self.replay_dir = replay_dir or Path("/tmp/computer_use_replay")
        self.history: list[ReplayEntry] = []

    def step(self, screenshot_b64: str) -> tuple[Action, str]:
        """Take one action. Returns (action, result)."""
        action = self.vlm.next_action(self.task, screenshot_b64)
        if action.kind == "done":
            return action, "done"

        # Verification: is the target actually visible?
        if action.target and not is_button_visible(screenshot_b64, action.target):
            result = "no_button_at_xy"
        else:
            result = self.executor(action)

        entry = ReplayEntry(
            ts=time.time(), task=self.task,
            screenshot_before=screenshot_b64[:32] + "...",
            action=action, result=result,
        )
        self.history.append(entry)
        if self.replay_dir:
            self.replay_dir.mkdir(parents=True, exist_ok=True)
            (self.replay_dir / f"{int(entry.ts*1000)}.json").write_text(entry.model_dump_json() if hasattr(entry, 'model_dump_json') else json.dumps(entry.__dict__, default=str))
        return action, result

    def run(self, screenshot_provider: Callable[[], str]) -> dict:
        """Run until done or max_actions. screenshot_provider returns base64 PNG."""
        for i in range(self.max_actions):
            ss = screenshot_provider()
            action, result = self.step(ss)
            if action.kind == "done" or result == "done":
                return {"status": "done", "actions": len(self.history)}
            if result.startswith("no_button"):
                # Could not find the target. The agent should re-plan.
                continue
        return {"status": "max_actions_hit", "actions": len(self.history)}


if __name__ == "__main__":
    vlm = VLM()
    def toy_exec(a): return "ok"
    def toy_ss(): return base64.b64encode(b"png-bytes").decode()
    a = Agent(vlm=vlm, executor=toy_exec, task="click submit")
    a.run(toy_ss)
    print(f"log: {len(a.history)} entries")
