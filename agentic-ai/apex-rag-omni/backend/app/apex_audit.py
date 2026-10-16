"""Append-only audit log + cursor-paginated trace reader.

The trace log is the source of truth for the frontend trace reviewer.
Cursor pagination uses (day, trace_id) as the sort key, so the
query plan is a range scan with keyset pagination — O(1) per page,
not OFFSET O(N).
"""
from __future__ import annotations

import json
import threading
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

Collection = Literal["hr_policies", "tech_docs", "product_docs"]

_AUDIT_PATH = Path(__file__).parent.parent.parent / "audit" / "audit.jsonl"
_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
_LOCK = threading.Lock()


def append_audit(trace_id: str, kind: str, payload: dict) -> None:
    """Append an event to the audit log. Never overwrites."""
    ev = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "kind": kind,
        "payload": payload,
    }
    line = json.dumps(ev)
    with _LOCK:
        with open(_AUDIT_PATH, "a") as f:
            f.write(line + "\n")


def recent_traces(day: str, after_id: str = "", limit: int = 50) -> list[dict]:
    """Read traces for a given day, starting after `after_id` (cursor).

    In production this is a DB query: SELECT * FROM traces
    WHERE day = ? AND trace_id > ? ORDER BY trace_id LIMIT ?
    Uses an index on (day, trace_id). O(log N) per page.

    For the prototype we read the audit log and filter in memory.
    """
    if not _AUDIT_PATH.exists():
        return []
    out: list[dict] = []
    with open(_AUDIT_PATH) as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("kind") != "query":
                continue
            ts = d.get("ts", "")
            trace_day = ts[:10] if ts else ""
            if trace_day != day:
                continue
            if after_id and d.get("trace_id", "") <= after_id:
                continue
            payload = d.get("payload", {})
            out.append({
                "trace_id": d["trace_id"],
                "day": trace_day,
                "ts": ts,
                "collection": payload.get("collection", "hr_policies"),
                "query": payload.get("query", ""),
                "latency_ms": payload.get("elapsed_ms", 0.0),
                "refused": payload.get("refused", False),
                "rating": None,
            })
    out.sort(key=lambda r: r["trace_id"])
    return out[:limit]
