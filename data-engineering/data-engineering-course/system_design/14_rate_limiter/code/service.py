"""Distributed Rate Limiter — core service.

Implements three strategies:
  * TokenBucket       — smooths bursts, configurable refill.
  * FixedWindow       — cheapest, simplest, has edge-burst problem.
  * SlidingWindowLog  — precise; memory grows with rate.

Each strategy implements a `check(state, now, limit, window, cost)` method
that mutates ``state`` and returns `(allowed, remaining, reset_in)`.

All state lives in an LRUCache keyed by (strategy, key) so the worst-case
working set is bounded.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Optional

from common.cache import LRUCache

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class RateDecision:
    allowed: bool
    remaining: int
    reset_in: float  # seconds until more capacity is available
    strategy: str
    limit: int
    cost: int = 1


# ---------------------------------------------------------------------------
# Strategy interface (duck-typed; stateless functions over a mutable record)
# ---------------------------------------------------------------------------


class TokenBucket:
    """Classic token bucket. ``bucket_size`` == limit; refill_rate == limit / window.

    >>> b = TokenBucket()
    >>> state = b.init()
    >>> d = b.check(state, now=0.0, limit=10, window=60.0, cost=1)
    >>> d.allowed, d.remaining
    (True, 9)
    """

    name = "token_bucket"

    @staticmethod
    def init() -> dict:
        return {"tokens": 0.0, "ts": 0.0, "limit": 0}

    @staticmethod
    def check(state: dict, now: float, limit: int, window: float, cost: int = 1) -> RateDecision:
        if state["limit"] != limit or state["ts"] == 0.0:
            # First init or limit changed — start half-full (or at capacity).
            state["limit"] = limit
            state["tokens"] = min(limit, float(limit))
            state["ts"] = now
        # Refill since last check.
        refill_rate = limit / window  # tokens per second
        elapsed = max(0.0, now - state["ts"])
        state["tokens"] = min(float(limit), state["tokens"] + elapsed * refill_rate)
        state["ts"] = now
        if state["tokens"] >= cost:
            state["tokens"] -= cost
            tokens_after = state["tokens"]
            remaining = int(tokens_after)
            reset_in = 0.0
            return RateDecision(
                allowed=True,
                remaining=remaining,
                reset_in=reset_in,
                strategy=TokenBucket.name,
                limit=limit,
                cost=cost,
            )
        # Denied: compute wait until enough tokens accumulated.
        deficit = cost - state["tokens"]
        refill_rate = limit / window
        reset_in = deficit / refill_rate if refill_rate > 0 else window
        return RateDecision(
            allowed=False,
            remaining=0,
            reset_in=reset_in,
            strategy=TokenBucket.name,
            limit=limit,
            cost=cost,
        )


class FixedWindow:
    """Cheapest strategy. One counter per window. Edge doubling."""

    name = "fixed_window"

    @staticmethod
    def init() -> dict:
        return {"count": 0, "window_start": 0.0, "limit": 0}

    @staticmethod
    def check(state: dict, now: float, limit: int, window: float, cost: int = 1) -> RateDecision:
        ws = state["window_start"]
        if ws == 0.0 or now - ws >= window:
            state["window_start"] = now
            state["count"] = 0
            state["limit"] = limit
        if state["count"] + cost <= limit:
            state["count"] += cost
            reset_in = window - (now - state["window_start"])
            return RateDecision(
                allowed=True,
                remaining=limit - state["count"],
                reset_in=max(0.0, reset_in),
                strategy=FixedWindow.name,
                limit=limit,
                cost=cost,
            )
        reset_in = window - (now - state["window_start"])
        return RateDecision(
            allowed=False,
            remaining=0,
            reset_in=max(0.0, reset_in),
            strategy=FixedWindow.name,
            limit=limit,
            cost=cost,
        )


class SlidingWindow:
    """Sliding-window log. Most precise; O(limit) memory per key."""

    name = "sliding_window"

    @staticmethod
    def init() -> dict:
        return {"ts": []}

    @staticmethod
    def check(state: dict, now: float, limit: int, window: float, cost: int = 1) -> RateDecision:
        cutoff = now - window
        # Drop expired timestamps.
        state["ts"] = [t for t in state["ts"] if t > cutoff]
        if len(state["ts"]) + cost <= limit:
            for _ in range(cost):
                state["ts"].append(now)
            reset_in = 0.0 if state["ts"] else window
            return RateDecision(
                allowed=True,
                remaining=limit - len(state["ts"]),
                reset_in=reset_in,
                strategy=SlidingWindow.name,
                limit=limit,
                cost=cost,
            )
        reset_in = (state["ts"][0] + window) - now if state["ts"] else window
        return RateDecision(
            allowed=False,
            remaining=0,
            reset_in=max(0.0, reset_in),
            strategy=SlidingWindow.name,
            limit=limit,
            cost=cost,
        )


STRATEGIES = {
    TokenBucket.name: TokenBucket,
    FixedWindow.name: FixedWindow,
    SlidingWindow.name: SlidingWindow,
}


# ---------------------------------------------------------------------------
# RateLimiter — multi-strategy, LRU-bounded state, lock-protected
# ---------------------------------------------------------------------------


class RateLimiter:
    """High-level rate limiter. Bounded state via LRUCache.

    >>> rl = RateLimiter(capacity=100)
    >>> d = rl.check(key="u:1", limit=10, window_seconds=60,
    ...              strategy="token_bucket")
    >>> d.allowed
    True
    """

    def __init__(self, capacity: int = 100_000):
        self.capacity = capacity
        self._cache = LRUCache(max_entries=capacity)
        self._lock = threading.RLock()
        # Counters
        self.allow_count = 0
        self.deny_count = 0

    # ---- public -----------------------------------------------------------

    def check(
        self,
        key: str,
        limit: int,
        window_seconds: float,
        strategy: str = "token_bucket",
        cost: int = 1,
        now: Optional[float] = None,
    ) -> RateDecision:
        """Atomically check (and update) the rate-limit decision for ``key``.

        ``cost`` defaults to 1. Set higher for "expensive" operations.
        """
        if not isinstance(key, str) or not key:
            raise ValueError("key must be a non-empty string")
        if limit <= 0:
            raise ValueError("limit must be > 0")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        if cost <= 0:
            raise ValueError("cost must be > 0")
        strategy = (strategy or "token_bucket").lower()
        if strategy not in STRATEGIES:
            raise ValueError(f"unknown strategy {strategy!r}")
        if now is None:
            now = time.time()
        cache_key = f"{strategy}:{key}"
        with self._lock:
            state = self._cache.get(cache_key)
            if state is None:
                state = STRATEGIES[strategy].init()
            decision = STRATEGIES[strategy].check(
                state, now=now, limit=limit, window=window_seconds, cost=cost
            )
            self._cache.set(cache_key, state)
            if decision.allowed:
                self.allow_count += 1
            else:
                self.deny_count += 1
            return decision

    # ---- admin ------------------------------------------------------------

    def reset(self, key: Optional[str] = None, strategy: Optional[str] = None) -> int:
        """Drop state for one (key[, strategy]) or all keys. Returns # removed."""
        with self._lock:
            if key is None:
                n = self._cache.size() if hasattr(self._cache, "size") else len(self._cache._data)
                self._cache.clear()
                self.allow_count = 0
                self.deny_count = 0
                return n
            keys_to_delete: list[str] = []
            if strategy:
                keys_to_delete.append(f"{strategy}:{key}")
            else:
                for s in STRATEGIES:
                    keys_to_delete.append(f"{s}:{key}")
            for k in keys_to_delete:
                self._cache.delete(k)
            return 1

    def inspect(self, key: str, strategy: str = "token_bucket") -> dict:
        with self._lock:
            state = self._cache.get(f"{strategy}:{key}")
            return {"strategy": strategy, "key": key, "state": state}

    def stats(self) -> dict:
        with self._lock:
            return {
                "active_keys": self._cache.size() if hasattr(self._cache, "size") else len(self._cache._data),
                "capacity": self.capacity,
                "allow": self.allow_count,
                "deny": self.deny_count,
                "cache": self._cache.stats(),
            }
