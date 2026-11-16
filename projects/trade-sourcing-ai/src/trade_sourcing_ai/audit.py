"""An append-only ledger of sourcing decisions.

Every decision the agent makes is written here as one JSON object per line.
That gives three things the demo and the API both need:

* an **audit trail** — what was asked, what was recommended, and why;
* a **history** — the value report can be computed from real decisions
  rather than from a simulation;
* a **defensive check** — if the agent ever recommends a supplier, you can
  find every decision it made about that supplier.

The format is JSONL, one object per line, append-only. Writes are flushed
immediately so a crash cannot lose a decision that was already reported to
the user.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import AUDIT_DIR


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DecisionEvent:
    """One recorded sourcing decision."""

    event_type: str
    decision_id: str
    ts: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "decision_id": self.decision_id,
            "ts": self.ts,
            "payload": self.payload,
        }


class AuditLog:
    """Append-only JSONL decision ledger."""

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else (AUDIT_DIR / "decisions.jsonl")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event_type: str, payload: dict[str, Any], decision_id: str | None = None) -> str:
        """Append one event. Returns the decision id."""
        identifier = decision_id or uuid.uuid4().hex[:12]
        event = DecisionEvent(
            event_type=event_type,
            decision_id=identifier,
            ts=_utc_now(),
            payload=payload,
        )
        line = json.dumps(event.to_dict(), default=str, sort_keys=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return identifier

    def recent(self, limit: int = 50, event_type: str | None = None) -> list[DecisionEvent]:
        """The most recent events, newest last."""
        if not self.path.exists():
            return []
        events: list[DecisionEvent] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for raw in handle:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if event_type and data.get("event_type") != event_type:
                    continue
                events.append(
                    DecisionEvent(
                        event_type=data.get("event_type", "unknown"),
                        decision_id=data.get("decision_id", ""),
                        ts=data.get("ts", ""),
                        payload=data.get("payload", {}),
                    )
                )
        return events[-limit:]

    def get(self, decision_id: str) -> DecisionEvent | None:
        """Find one decision by id."""
        for event in self.recent(limit=10_000):
            if event.decision_id == decision_id:
                return event
        return None

    def clear(self) -> None:
        """Remove the ledger. Used by tests."""
        if self.path.exists():
            self.path.unlink()
