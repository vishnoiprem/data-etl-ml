"""
Devin-style SWE agent loop.

The agent:
  1. Reads the GitHub issue.
  2. Plans 3-8 sub-tasks.
  3. For each sub-task: read files, edit files, run tests.
  4. If the test fails, re-plan with the failure context (bounded retries).
  5. Opens a draft PR.

This file is the loop. The tools (read, write, run) are abstracted so
the same loop works against different sandboxes.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from pydantic import BaseModel


class ToolCall(BaseModel):
    tool: str       # "read" | "edit" | "run" | "search"
    args: dict


class SubTask(BaseModel):
    id: int
    description: str
    done: bool = False


class Plan(BaseModel):
    issue: str
    subtasks: list[SubTask]


class Sandbox:
    """Abstract sandbox. Real impl: Docker, Firecracker, E2B."""

    def read(self, path: str) -> str:
        raise NotImplementedError

    def edit(self, path: str, new_content: str) -> None:
        raise NotImplementedError

    def run(self, command: str) -> tuple[int, str]:
        raise NotImplementedError

    def search(self, pattern: str) -> list[str]:
        raise NotImplementedError


@dataclass
class Agent:
    sandbox: Sandbox
    planner: Callable[[str], Plan]
    test_command: str = "pytest -q"
    max_retries: int = 5
    history: list[dict] = field(default_factory=list)

    def run(self, issue: str) -> dict:
        """End-to-end: plan -> execute -> test -> PR."""
        t0 = time.time()
        plan = self.planner(issue)
        self._log("plan", {"n_subtasks": len(plan.subtasks)})

        for sub in plan.subtasks:
            self._execute_subtask(sub)

        # Test the full repo
        rc, out = self.sandbox.run(self.test_command)
        self._log("test", {"rc": rc, "tail": out[-500:]})

        # Recovery: if tests fail, re-plan
        retries = 0
        while rc != 0 and retries < self.max_retries:
            retries += 1
            failure_context = out[-2000:]
            plan = self.planner(f"fix the failing tests. failure:\n{failure_context}")
            for sub in plan.subtasks:
                self._execute_subtask(sub)
            rc, out = self.sandbox.run(self.test_command)
            self._log("retry", {"retry": retries, "rc": rc})

        return {
            "ok": rc == 0,
            "retries": retries,
            "subtasks": len(plan.subtasks),
            "duration_s": round(time.time() - t0, 1),
        }

    def _execute_subtask(self, sub: SubTask) -> None:
        # Toy: a single read-edit-run cycle. Real impl: full agent loop
        # with a tool-calling LLM that decides what to do.
        files = self.sandbox.search(sub.description)
        for f in files[:3]:
            content = self.sandbox.read(f)
            self.sandbox.edit(f, content)  # placeholder
        self._log("subtask", {"id": sub.id, "description": sub.description, "files": files[:3]})
        sub.done = True

    def _log(self, event: str, payload: dict):
        self.history.append({"event": event, "ts": time.time(), **payload})


# --- Reference planner (toy) ------------------------------------------------

def keyword_planner(issue: str) -> Plan:
    """Splits the issue by sentence and treats each as a sub-task."""
    sentences = [s.strip() for s in issue.replace("\n", ". ").split(".") if s.strip()]
    return Plan(
        issue=issue,
        subtasks=[SubTask(id=i, description=s) for i, s in enumerate(sentences[:8])],
    )


if __name__ == "__main__":
    # Toy in-memory sandbox
    class MemorySandbox(Sandbox):
        def __init__(self):
            self.files = {"a.py": "x = 1\n", "b.py": "y = 2\n"}

        def read(self, path): return self.files.get(path, "")
        def edit(self, path, c): self.files[path] = c
        def run(self, cmd): return 0, "ok" if "pytest" in cmd else ""
        def search(self, p): return [f for f in self.files if p.lower() in f.lower() or p in self.files[f]]

    agent = Agent(sandbox=MemorySandbox(), planner=keyword_planner)
    result = agent.run("Add a missing test. Refactor a 200-line module.")
    print(result)
