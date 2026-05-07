"""Short-term and long-term memory abstractions.

Short-term memory is the agent loop's working scratchpad. It holds the
running history of (thought, action, observation) tuples for the current
session.

Long-term memory holds entities and prior interactions across sessions.
In production this is DynamoDB (structured) + OpenSearch (semantic recall).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Step:
    thought: str
    action: str           # tool name
    args: dict
    observation: dict     # tool result data
    ok: bool = True
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ShortTermMemory:
    """Bounded working-memory queue."""
    max_steps: int = 50
    steps: deque[Step] = field(default_factory=deque)

    def add(self, step: Step) -> None:
        self.steps.append(step)
        while len(self.steps) > self.max_steps:
            self.steps.popleft()

    def loop_signature(self, n: int = 3) -> str:
        """Used to detect repetition: signature of the last n actions."""
        last = list(self.steps)[-n:]
        return " | ".join(f"{s.action}({sorted(s.args.items())})" for s in last)

    def to_prompt(self) -> str:
        if not self.steps:
            return "(no prior steps)"
        return "\n".join(
            f"- thought: {s.thought}\n  action: {s.action}({s.args})\n  obs: {s.observation}"
            for s in self.steps
        )


@dataclass
class LongTermMemory:
    """In-process key-value LTM stand-in for DynamoDB + OpenSearch."""
    store: dict[str, Any] = field(default_factory=dict)

    def remember(self, key: str, value: Any) -> None:
        self.store[key] = value

    def recall(self, key: str, default: Any = None) -> Any:
        return self.store.get(key, default)
