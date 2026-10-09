"""Idempotency helpers: dedup a stream by key, build an idempotency
cache, and wrap a load function so it can be retried safely.

The two main pieces:

  * :class:`IdempotencyCache` — a small in-memory set of keys
    we've already processed. Used by the dedup pattern.
  * :func:`idempotent_load` — wraps a load function so a retry
    with the same ``load_id`` is a no-op.

Both are designed to be replaced with production equivalents
(Redis for the cache; a load_log table in the warehouse for
the load function).

Author: Prem Vishnoi <prem.vishnoi.example.com>
"""

from __future__ import annotations

import functools
import time
from collections import deque
from typing import Any, Callable, Deque, Dict, List, Optional, Set, Tuple


class IdempotencyCache:
    """A bounded in-memory set of "already seen" keys.

    Used to dedup a stream of events by an event_id (or any
    other stable key). Bounded so the set doesn't grow without
    limit in a long-running consumer.

    Parameters
    ----------
    max_size:
        Maximum number of keys to remember. Oldest keys are
        evicted (FIFO) when the set is full.
    """

    def __init__(self, max_size: int = 100_000) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self.max_size = max_size
        self._order: Deque[Any] = deque()
        self._set: Set[Any] = set()

    def __contains__(self, key: Any) -> bool:
        return key in self._set

    def __len__(self) -> int:
        return len(self._set)

    def add(self, key: Any) -> bool:
        """Add ``key`` to the cache. Return True if it was new."""
        if key in self._set:
            return False
        self._set.add(key)
        self._order.append(key)
        if len(self._set) > self.max_size:
            old = self._order.popleft()
            self._set.discard(old)
        return True

    def clear(self) -> None:
        self._order.clear()
        self._set.clear()


def dedup_by_key(
    rows: List[Dict[str, Any]],
    key_fn: Callable[[Dict[str, Any]], Any],
    cache: Optional[IdempotencyCache] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """Return ``(unique_rows, dropped_count)``.

    Rows are deduplicated by ``key_fn(row)``. The cache is
    optional; if None, a new one is created. A single cache
    can be reused across calls.
    """
    if cache is None:
        cache = IdempotencyCache()
    out: List[Dict[str, Any]] = []
    dropped = 0
    for row in rows:
        key = key_fn(row)
        if cache.add(key):
            out.append(row)
        else:
            dropped += 1
    return out, dropped


# ---- load_id tracking ------------------------------------------------


class LoadRegistry:
    """Tracks ``load_id`` → success/failure.

    A pipeline calls :meth:`mark` with a load_id before the load
    and :meth:`complete` after. A retry that sees the load_id
    already marked as complete is a no-op.

    In production this is a warehouse table; here it's an
    in-memory dict (good enough for tests).
    """

    def __init__(self) -> None:
        self._done: Dict[str, float] = {}
        self._inflight: Dict[str, float] = {}

    def is_done(self, load_id: str) -> bool:
        return load_id in self._done

    def mark(self, load_id: str) -> None:
        if load_id not in self._done:
            self._inflight[load_id] = time.time()

    def complete(self, load_id: str) -> None:
        self._inflight.pop(load_id, None)
        self._done[load_id] = time.time()


def idempotent_load(
    load_fn: Callable[[List[Dict[str, Any]]], Any],
    registry: LoadRegistry,
    load_id: str,
    rows: List[Dict[str, Any]],
) -> Tuple[bool, Any]:
    """Run ``load_fn(rows)`` only if ``load_id`` hasn't been completed.

    Returns ``(ran, result)``. If the load already completed,
    ``ran`` is False and ``result`` is the cached prior result
    (or None). The first call records the load_id in the
    registry and runs the function; subsequent calls with the
    same load_id are no-ops.

    The pattern matches the warehouse-side idempotency:
    every load is tagged with a load_id; the load_log table
    makes retries safe.
    """
    if registry.is_done(load_id):
        return False, None
    registry.mark(load_id)
    result = load_fn(rows)
    registry.complete(load_id)
    return True, result
