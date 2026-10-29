"""In-process caches used to demonstrate caching layers in system designs.

These are *not* meant to replace Redis or Memcached. They exist so you can:

1. Run the services on a laptop with zero external dependencies.
2. See cache hits / misses, TTLs, and LRU eviction in action.
3. Reason about where a real distributed cache would slot in.

Swap TTLCache/LRUCache for Redis or Memcached in production.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from threading import RLock
from typing import Any, Optional, Tuple


class TTLCache:
    """A small thread-safe TTL cache.

    Used by every read-heavy service in this course: hot data goes in,
    cold data expires automatically after `ttl_seconds`.

    >>> c = TTLCache(ttl_seconds=60)
    >>> c.set("k", "v")
    True
    >>> c.get("k")
    'v'
    """

    def __init__(self, ttl_seconds: float = 300.0, max_entries: int = 10_000):
        self.ttl = ttl_seconds
        self.max = max_entries
        self._data: dict[str, Tuple[Any, float]] = {}
        self._lock = RLock()
        # Metrics — surfaces in /metrics endpoints.
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                self.misses += 1
                return default
            value, expires_at = entry
            if expires_at < time.time():
                # Expired — drop and miss.
                self._data.pop(key, None)
                self.misses += 1
                return default
            self.hits += 1
            return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> bool:
        ttl = ttl_seconds if ttl_seconds is not None else self.ttl
        with self._lock:
            # Simple bounded cache — drop oldest if over capacity.
            if len(self._data) >= self.max and key not in self._data:
                oldest = next(iter(self._data))
                self._data.pop(oldest, None)
                self.evictions += 1
            self._data[key] = (value, time.time() + ttl)
            return True

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
            self.hits = 0
            self.misses = 0
            self.evictions = 0

    def stats(self) -> dict:
        with self._lock:
            total = self.hits + self.misses
            return {
                "size": len(self._data),
                "capacity": self.max,
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "hit_rate": (self.hits / total) if total else 0.0,
            }


class LRUCache:
    """A thread-safe LRU cache, OrderedDict-backed.

    Where TTL answers "is this fresh?", LRU answers "is this popular?".
    Twitter timelines, Instagram profile feeds, and Netflix watch-history
    slices are classic LRU candidates — keep the recent reads hot, evict
    cold ones under pressure.
    """

    def __init__(self, max_entries: int = 1_000):
        self.max = max_entries
        self._data: "OrderedDict[str, Any]" = OrderedDict()
        self._lock = RLock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            if key not in self._data:
                self.misses += 1
                return default
            self._data.move_to_end(key)
            self.hits += 1
            return self._data[key]

    def set(self, key: str, value: Any) -> bool:
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
                self._data[key] = value
                return True
            self._data[key] = value
            self._data.move_to_end(key)
            if len(self._data) > self.max:
                self._data.popitem(last=False)
                self.evictions += 1
            return True

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
            self.hits = 0
            self.misses = 0
            self.evictions = 0

    def stats(self) -> dict:
        with self._lock:
            total = self.hits + self.misses
            return {
                "size": len(self._data),
                "capacity": self.max,
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "hit_rate": (self.hits / total) if total else 0.0,
            }
