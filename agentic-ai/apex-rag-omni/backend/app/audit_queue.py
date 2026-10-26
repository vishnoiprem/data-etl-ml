"""Bounded asyncio.Queue for the audit log.

The request path (async handlers) must NOT do sync I/O — `open()` + `write()`
on a JSONL file blocks the event loop and serializes all in-flight requests
on the GIL. Instead:

  1. `enqueue_audit(trace_id, kind, payload)` is `await queue.put(...)` —
     bounded, never blocks longer than the queue's internal mutex.
  2. `_drain_loop()` runs as a single background task started by the
     FastAPI `lifespan` startup. It pulls items from the queue and writes
     them with `aiofiles` (already approved: `aiofiles==24.1.0` in
     requirements after this change).
  3. If the queue is full we increment `dropped_count` and log a WARN —
     the request still returns 200 because the audit log is for
     observability, not transactional correctness.

On shutdown, the lifespan exit phase calls `flush_on_shutdown(timeout=5.0)`
which drains any remaining items with a deadline.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("apex.audit")

# Module-level state. Initialized in `init_audit_queue` at lifespan startup.
_queue: asyncio.Queue[dict] | None = None
_drain_task: asyncio.Task[None] | None = None
_dropped_count: int = 0
_written_count: int = 0
_audit_path: Path | None = None
_maxsize: int = 10_000


def _default_audit_path() -> Path:
    """Default location of the JSONL audit log. Overridden in `init_audit_queue`."""
    return Path(__file__).parent.parent.parent / "audit" / "audit.jsonl"


def init_audit_queue(*, maxsize: int, audit_path: Path | None = None) -> None:
    """Initialize the queue and ensure the audit directory exists.

    Called once at lifespan startup. Safe to call from tests; idempotent.
    """
    global _queue, _audit_path, _maxsize
    if _queue is not None:
        return  # already initialized
    _maxsize = maxsize
    _audit_path = (audit_path or _default_audit_path())
    _audit_path.parent.mkdir(parents=True, exist_ok=True)
    _queue = asyncio.Queue(maxsize=maxsize)
    logger.info("audit queue initialized: max=%d path=%s", maxsize, _audit_path)


async def enqueue_audit(trace_id: str, kind: str, payload: dict[str, Any]) -> None:
    """Enqueue an audit event from the request path. Non-blocking.

    If the queue is full, increments `dropped_count` and returns.
    Never raises. The request path is not allowed to fail because of audit.
    """
    global _dropped_count
    if _queue is None:
        # Not initialized — treat as a drop with a warning. This shouldn't
        # happen in production (lifespan guarantees init), but a test
        # importing the app without going through lifespan will hit this.
        _dropped_count += 1
        logger.warning("audit queue not initialized; dropping event")
        return
    ev = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "kind": kind,
        "payload": payload,
    }
    try:
        _queue.put_nowait(ev)
    except asyncio.QueueFull:
        _dropped_count += 1
        if _dropped_count % 100 == 1:
            logger.warning("audit queue full; dropped=%d", _dropped_count)


async def start_drain() -> None:
    """Start the background drain task. Called from lifespan startup."""
    global _drain_task
    if _drain_task is not None and not _drain_task.done():
        return
    _drain_task = asyncio.create_task(_drain_loop(), name="apex-audit-drain")
    logger.info("audit drain task started")


async def stop_drain() -> None:
    """Stop the drain task. Called from lifespan shutdown."""
    global _drain_task
    if _drain_task is None:
        return
    _drain_task.cancel()
    try:
        await _drain_task
    except (asyncio.CancelledError, Exception):
        pass
    _drain_task = None
    logger.info("audit drain task stopped")


async def flush_on_shutdown(timeout: float = 5.0) -> None:
    """Drain remaining items with a hard deadline. Best-effort."""
    if _queue is None or _audit_path is None:
        return
    deadline = asyncio.get_event_loop().time() + timeout
    while not _queue.empty() and asyncio.get_event_loop().time() < deadline:
        try:
            ev = _queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        await _write_line(_audit_path, ev)
    logger.info("audit flush complete: written=%d dropped=%d remaining=%d",
                _written_count, _dropped_count, _queue.qsize())


async def _drain_loop() -> None:
    """Background task. Pulls from queue, writes with aiofiles."""
    global _written_count
    import aiofiles  # local import: the dep is only required at runtime
    if _audit_path is None or _queue is None:
        return
    while True:
        ev = await _queue.get()
        try:
            async with aiofiles.open(_audit_path, mode="a") as f:
                await f.write(json.dumps(ev) + "\n")
            _written_count += 1
        except Exception as exc:
            logger.exception("audit write failed: %s", exc)


async def _write_line(path: Path, ev: dict) -> None:
    """Used only by the shutdown flush path."""
    global _written_count
    import aiofiles
    async with aiofiles.open(path, mode="a") as f:
        await f.write(json.dumps(ev) + "\n")
    _written_count += 1


def stats() -> dict[str, int]:
    """Test introspection. Returns queue size + drop count + written count."""
    return {
        "queue_size": _queue.qsize() if _queue is not None else 0,
        "queue_max": _maxsize,
        "dropped": _dropped_count,
        "written": _written_count,
    }


def audit_path() -> Path | None:
    """The path the drain task writes to. None if not initialized.

    `apex_audit.recent_traces` uses this so the reader and writer
    always agree on the file. Without this, the queue could be
    configured to write to a tmp file in tests while the reader
    reads from the project path — and the two surfaces silently
    diverge.
    """
    return _audit_path


def reset_for_test() -> None:
    """Reset module state. Tests only — never call from prod."""
    global _queue, _drain_task, _dropped_count, _written_count, _audit_path
    _queue = None
    _drain_task = None
    _dropped_count = 0
    _written_count = 0
    _audit_path = None
