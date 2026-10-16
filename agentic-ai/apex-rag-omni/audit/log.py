"""Append-only audit log for retrieval + answer calls.

Every retrieval, every answer, every eval — written here, never deleted.
This is the compliance + debugging surface. If the answer was refused,
the reason is here. If the system was wrong, the trace is here.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    """One event in the audit log."""
    ts: str
    event_type: str  # retrieve, answer, eval, cdc, dual_write, cutover
    trace_id: str
    payload: dict


def emit(event_type: str, trace_id: str, payload: dict,
         log_path: str = "audit/audit.jsonl") -> None:
    """Append an event to the audit log. Never overwrites, never deletes."""
    ev = AuditEvent(
        ts=datetime.now(timezone.utc).isoformat(),
        event_type=event_type, trace_id=trace_id, payload=payload,
    )
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(asdict(ev)) + "\n")


def recent(event_type: str | None = None, limit: int = 100,
           log_path: str = "audit/audit.jsonl") -> list[AuditEvent]:
    """Read recent events from the audit log."""
    if not Path(log_path).exists():
        return []
    events: list[AuditEvent] = []
    with open(log_path) as f:
        for line in f:
            try:
                d = json.loads(line)
                if event_type is None or d.get("event_type") == event_type:
                    events.append(AuditEvent(**d))
            except Exception:
                continue
    return events[-limit:]
