"""Append-only audit log + cursor-paginated trace reader.

The trace log is the source of truth for the frontend trace reviewer.
Cursor pagination uses (day, trace_id) as the sort key, so the
query plan is a range scan with keyset pagination — O(1) per page,
not OFFSET O(N).

WRITES are off the event loop: the request path calls
`audit_queue.enqueue_audit()` which is non-blocking. The actual disk
write happens in the background drain task (see audit_queue.py). This
file owns the READ path and a small sync `append_audit` helper used
by bootstrap scripts and tests that don't go through the FastAPI
lifespan (and therefore don't have the queue initialized).

The audit log path is shared with the queue: the queue writes to
`_audit_path()` and the reader reads from the same. This avoids the
"writer in one place, reader in another" bug that would let a
configurable path silently diverge.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

Collection = Literal["hr_policies", "tech_docs", "product_docs"]

_DEFAULT_AUDIT_PATH = Path(__file__).parent.parent.parent / "audit" / "audit.jsonl"
_DEFAULT_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
_LOCK = threading.Lock()


def _audit_path() -> Path:
    """Return the active audit log path.

    Falls back to the default project path when the queue is not
    initialized (e.g. from scripts and tests that don't go through
    the FastAPI lifespan). When the queue IS initialized, the path
    it was given is the source of truth.
    """
    # Local import to avoid a circular dep: audit_queue imports nothing
    # from apex_audit at module level, but apex_audit is read by the
    # route layer which also imports audit_queue.
    from . import audit_queue as _q
    qp = _q.audit_path()
    if qp is not None:
        return qp
    return _DEFAULT_AUDIT_PATH


def append_audit(trace_id: str, kind: str, payload: dict) -> None:
    """Sync write to the audit log. NEVER call from the async request path —
    use `audit_queue.enqueue_audit()` instead. This helper is for bootstrap
    scripts, tests, and one-off admin tasks.
    """
    ev = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "kind": kind,
        "payload": payload,
    }
    line = json.dumps(ev)
    path = _audit_path()
    with _LOCK:
        with open(path, "a") as f:
            f.write(line + "\n")


def recent_traces(day: str, after_id: str = "", limit: int = 50) -> list[dict]:
    """Read traces for a given day, starting after `after_id` (cursor).

    In production this is a DB query: SELECT * FROM traces
    WHERE day = ? AND trace_id > ? ORDER BY trace_id LIMIT ?
    Uses an index on (day, trace_id). O(log N) per page.

    For the prototype we read the audit log and filter in memory.
    Reads from the same path the queue writes to.
    """
    path = _audit_path()
    if not path.exists():
        return []
    out: list[dict] = []
    with open(path) as f:
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


def audit_path() -> Path:
    """Public accessor. Used by callers that need to know the active path."""
    return _audit_path()
