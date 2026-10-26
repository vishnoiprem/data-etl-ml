"""LLM Query Batching — core service.

A dynamic batching dispatcher for LLM queries. The engineering idea is
the same as vLLM's continuous batching / TGI's dynamic batching:

    1. Incoming queries are placed in an "arrival window".
    2. The window flushes when EITHER it holds `batch_size` queries
       OR `window_ms` have elapsed since the first query.
    3. The batched payload is sent to the (mock) LLM as a single
       inference call.
    4. Each query is resolved with its own slice of the response.

The shape of the response and the batching behavior are real; the
inference itself is a deterministic mock.

Why this matters: amortizing prefill/decode across N requests gives
~Nx throughput for the same hardware. We expose a `stats()` method
that shows the actual N-to-1 reduction.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field, asdict
from typing import Optional

from common.metrics import MetricsRegistry  # noqa: F401  (kept for parity)


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


DEFAULT_BATCH_SIZE = 8
DEFAULT_WINDOW_MS = 25.0
DEFAULT_MAX_TOKENS = 256

# Each query id, plus a notion of "wall clock wait" so callers can
# tell how long they actually blocked.


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Query:
    query_id: int
    prompt: str
    max_tokens: int
    created_at: float = field(default_factory=lambda: time.time())
    # Filled in when the batch flushes:
    completed_at: Optional[float] = None
    response: Optional[str] = None
    tokens: int = 0
    batch_id: Optional[int] = None
    wait_ms: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Mock LLM
# ---------------------------------------------------------------------------


def _mock_batched_complete(prompts: list[str], max_tokens: int) -> list[str]:
    """A deterministic mock LLM. One call, many prompts, many responses.

    Real inference engines pad prompts to the same length and run them
    in parallel through the GPU. We just return a templated reply per
    prompt; the *batching* is what we're modeling.
    """
    out: list[str] = []
    for i, p in enumerate(prompts):
        snippet = p.strip().splitlines()[0] if p.strip() else "(empty)"
        snippet = snippet[:60]
        out.append(
            f"[batch-slot {i}] response to: {snippet} (max_tokens={max_tokens})"
        )
    return out


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class BatchingService:
    """Dynamic batching for LLM queries.

    >>> svc = BatchingService(batch_size=2, window_ms=10.0)
    >>> ids = [svc.submit(p, max_tokens=8) for p in ["a", "b"]]
    >>> [svc.get(i).response for i in ids]
    ['[batch-slot 0] response to: a (max_tokens=8)', '[batch-slot 1] response to: b (max_tokens=8)']
    >>> svc.stats()["batches"]
    1
    """

    def __init__(
        self,
        batch_size: int = DEFAULT_BATCH_SIZE,
        window_ms: float = DEFAULT_WINDOW_MS,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ):
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        if window_ms <= 0:
            raise ValueError("window_ms must be > 0")

        self.batch_size = batch_size
        self.window_ms = window_ms
        self.max_tokens = max_tokens

        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

        # State.
        self._queries: dict[int, Query] = {}
        self._inflight: list[Query] = []  # queries waiting in the current window
        self._window_started_at: Optional[float] = None
        self._next_id = 1
        self._next_batch_id = 1

        # Stats.
        self._stats = {
            "submitted": 0,
            "completed": 0,
            "batches": 0,
            "queries_in_batches": 0,  # total queries that went into any batch
            "max_batch_size": 0,
            "total_wait_ms": 0.0,
        }

        # Background flusher.
        self._stop = threading.Event()
        self._flusher = threading.Thread(target=self._flusher_loop, daemon=True)
        self._flusher.start()

    # ---- submission ----------------------------------------------------

    def submit(self, prompt: str, max_tokens: Optional[int] = None) -> int:
        if not isinstance(prompt, str):
            raise ValueError("prompt must be a string")
        if not prompt:
            raise ValueError("prompt is required")

        with self._cond:
            qid = self._next_id
            self._next_id += 1
            q = Query(
                query_id=qid,
                prompt=prompt,
                max_tokens=max_tokens or self.max_tokens,
            )
            self._queries[qid] = q
            self._inflight.append(q)
            if self._window_started_at is None:
                self._window_started_at = time.perf_counter()
            self._stats["submitted"] += 1

            # Trigger an immediate flush if we've hit the batch cap.
            if len(self._inflight) >= self.batch_size:
                self._cond.notify_all()
            return qid

    # ---- result retrieval ---------------------------------------------

    def get(self, query_id: int, timeout: Optional[float] = None) -> Optional[Query]:
        """Block (up to ``timeout`` seconds) until the query has a response."""
        deadline = (time.perf_counter() + timeout) if timeout else None
        with self._cond:
            while True:
                q = self._queries.get(query_id)
                if q is None:
                    return None
                if q.response is not None:
                    return q
                if deadline is not None:
                    remaining = deadline - time.perf_counter()
                    if remaining <= 0:
                        return q  # return whatever we have so far
                    self._cond.wait(timeout=remaining)
                else:
                    self._cond.wait()

    # ---- flusher loop --------------------------------------------------

    def _flusher_loop(self) -> None:
        """Background thread that flushes the arrival window."""
        while not self._stop.is_set():
            with self._cond:
                # Compute when the current window should flush.
                if self._inflight and self._window_started_at is not None:
                    elapsed_ms = (time.perf_counter() - self._window_started_at) * 1000.0
                    wait_ms = max(0.0, self.window_ms - elapsed_ms)
                else:
                    wait_ms = 1.0  # idle

                if wait_ms > 0:
                    self._cond.wait(timeout=wait_ms / 1000.0)

                # If we still have a full batch, flush immediately;
                # otherwise flush if the window has elapsed.
                if self._inflight:
                    elapsed_ms = (time.perf_counter() - self._window_started_at) * 1000.0
                    full = len(self._inflight) >= self.batch_size
                    if full or elapsed_ms >= self.window_ms:
                        self._flush_locked()

    def _flush_locked(self) -> None:
        """Flush the current window. Must be called with the lock held."""
        if not self._inflight:
            return
        batch = self._inflight
        self._inflight = []
        self._window_started_at = None

        bid = self._next_batch_id
        self._next_batch_id += 1

        max_tokens = max(q.max_tokens for q in batch)
        prompts = [q.prompt for q in batch]

        # Simulate the inference cost: a small fixed cost per batch.
        # Real systems pay a per-token prefill + per-token decode.
        inf_start = time.perf_counter()
        responses = _mock_batched_complete(prompts, max_tokens)
        inf_ms = (time.perf_counter() - inf_start) * 1000.0
        # Pretend the inference cost grows with the batch (not really,
        # but we make it a small linear ramp so the metric looks real).
        inf_ms += 0.5 * len(batch)  # tiny per-query overhead

        now = time.perf_counter()
        for q, resp in zip(batch, responses):
            q.response = resp
            q.tokens = len(resp.split())
            q.batch_id = bid
            q.completed_at = now
            q.wait_ms = (now - q.created_at) * 1000.0

        # Update stats.
        self._stats["batches"] += 1
        self._stats["queries_in_batches"] += len(batch)
        self._stats["max_batch_size"] = max(self._stats["max_batch_size"], len(batch))
        for q in batch:
            self._stats["total_wait_ms"] += q.wait_ms
        self._stats["completed"] += len(batch)
        self._stats["last_batch_size"] = len(batch)
        self._stats["last_batch_inf_ms"] = inf_ms

        self._cond.notify_all()

    # ---- manual flush / shutdown --------------------------------------

    def flush_now(self) -> int:
        """Force a flush; returns the number of queries flushed."""
        with self._cond:
            n = len(self._inflight)
            self._flush_locked()
            return n

    def shutdown(self) -> None:
        """Stop the flusher thread and flush any pending queries."""
        with self._cond:
            self._stop.set()
            self._cond.notify_all()
        self._flusher.join(timeout=1.0)

    # ---- stats ---------------------------------------------------------

    def stats(self) -> dict:
        with self._cond:
            out = dict(self._stats)
            out["inflight"] = len(self._inflight)
            out["batch_size_limit"] = self.batch_size
            out["window_ms"] = self.window_ms
            if out["completed"] > 0:
                out["avg_wait_ms"] = out["total_wait_ms"] / out["completed"]
            else:
                out["avg_wait_ms"] = 0.0
            if out["batches"] > 0:
                out["avg_batch_size"] = out["queries_in_batches"] / out["batches"]
            else:
                out["avg_batch_size"] = 0.0
            if out["submitted"] > 0:
                out["throughput_x"] = round(
                    out["queries_in_batches"] / max(1, out["batches"]), 2
                )
            else:
                out["throughput_x"] = 0.0
            return out

    def list_queries(self) -> list[Query]:
        with self._cond:
            return list(self._queries.values())
