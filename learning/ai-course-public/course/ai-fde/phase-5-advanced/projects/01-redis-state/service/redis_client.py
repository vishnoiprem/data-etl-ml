"""
projects/01-redis-state/service/redis_client.py — thin wrapper around redis-py.

Why a wrapper
-------------
Phase 4's `circuit.py` calls `TokenBucketRateLimiter.try_acquire(user_id)`.
Phase 5's `RedisTokenBucket.try_acquire(user_id)` does the same thing but
holds the bucket state in Redis. The wrapper here makes the redis-py
import optional so unit tests that don't have Redis still run.

How to run
----------
    # In tests we use the FAKEREDIS_REDIS_URL to point at a local fakeredis
    # server (which is what pytest uses when no real Redis is available).
    export FAKEREDIS_URL=redis://localhost:6379/0
    python3 redis_client.py
"""
from __future__ import annotations

import os
import sys
from typing import Optional

# Lazy import so the module loads even when redis-py is missing
_client = None


def get_client(url: Optional[str] = None) -> "object":
    """Return a process-local Redis client. Falls back to fakeredis if real
    Redis is not reachable, then to a tiny in-process dict stub if neither
    is installed (so unit tests still run)."""
    global _client
    if _client is not None:
        return _client
    url = url or os.environ.get("FAKEREDIS_URL") or os.environ.get("REDIS_URL") or "redis://localhost:6379/0"
    # Prefer real Redis; fall back to fakeredis for unit tests
    try:
        import redis  # type: ignore
        c = redis.Redis.from_url(url, socket_timeout=2, socket_connect_timeout=2)
        c.ping()
        _client = c
        return c
    except Exception:
        try:
            import fakeredis  # type: ignore
            _client = fakeredis.FakeStrictRedis()
            return _client
        except ImportError:
            # Neither redis-py nor fakeredis available. Fall back to a
            # tiny in-process dict stub so unit tests still run. The stub
            # supports the subset of redis-py used by redis_state.py:
            # set, get, setex, delete, eval, hset/hget/hgetall/hdel,
            # expire, flushdb, ping.
            _client = _InProcessRedisStub()
            return _client


class _InProcessRedisStub:
    """Minimal in-process Redis stand-in. Only the methods used by
    redis_state.py are implemented. NOT for production use."""

    def __init__(self) -> None:
        self._kv: dict[str, str] = {}
        self._hashes: dict[str, dict[str, str]] = {}
        self._expiry: dict[str, float] = {}

    def _expired(self, key: str) -> bool:
        import time as _t
        exp = self._expiry.get(key)
        return exp is not None and _t.monotonic() > exp

    def _purge(self, key: str) -> None:
        self._kv.pop(key, None)
        self._expiry.pop(key, None)

    def ping(self) -> bool:
        return True

    def flushdb(self) -> bool:
        self._kv.clear()
        self._hashes.clear()
        self._expiry.clear()
        return True

    def get(self, key: str) -> "Optional[bytes]":
        if self._expired(key):
            self._purge(key)
        v = self._kv.get(key)
        return v.encode() if v is not None else None

    def set(self, key: str, value, ex: Optional[int] = None) -> bool:
        self._kv[key] = value.decode() if isinstance(value, bytes) else str(value)
        if ex is not None:
            import time as _t
            self._expiry[key] = _t.monotonic() + ex
        return True

    def setex(self, key: str, seconds: int, value) -> bool:
        return self.set(key, value, ex=seconds)

    def delete(self, *keys: str) -> int:
        n = 0
        for k in keys:
            if k in self._kv:
                self._purge(k)
                n += 1
        return n

    def expire(self, key: str, seconds: int) -> bool:
        if key not in self._kv:
            return False
        import time as _t
        self._expiry[key] = _t.monotonic() + seconds
        return True

    def hset(self, name: str, key: str, value) -> bool:
        self._hashes.setdefault(name, {})[key] = (
            value.decode() if isinstance(value, bytes) else str(value)
        )
        return True

    def hget(self, name: str, key: str) -> "Optional[bytes]":
        v = self._hashes.get(name, {}).get(key)
        return v.encode() if v is not None else None

    def hgetall(self, name: str) -> dict:
        return {
            k: v.encode() for k, v in self._hashes.get(name, {}).items()
        }

    def hdel(self, name: str, *keys: str) -> int:
        h = self._hashes.get(name, {})
        n = sum(1 for k in keys if h.pop(k, None) is not None)
        return n

    def eval(self, script: str, numkeys: int, *args) -> "object":
        """Stub Lua eval. Implements the token-bucket Lua script
        semantically: HMGET/HMSET on a single hash key. NOT for production.
        For any other Lua, raise NotImplementedError so we fail loudly
        instead of silently returning wrong data.
        """
        if "HMGET" in script and "HMSET" in script and "tokens" in script:
            # Token-bucket Lua: keys[0] is the hash key, args[0..3] are
            # capacity, refill_rate, cost, now.
            key = args[0]
            capacity = float(args[1])
            refill_rate = float(args[2])
            cost = float(args[3])
            now = float(args[4])
            h = self._hashes.get(key, {})
            tokens = float(h["tokens"]) if "tokens" in h else capacity
            ts = float(h["ts"]) if "ts" in h else now
            elapsed = max(0.0, now - ts)
            tokens = min(capacity, tokens + elapsed * refill_rate)
            allowed = 1 if tokens >= cost else 0
            if allowed:
                tokens -= cost
            self._hashes[key] = {"tokens": str(tokens), "ts": str(now)}
            return [allowed, str(tokens)]
        raise NotImplementedError(
            f"_InProcessRedisStub.eval: unsupported Lua script "
            f"(len={len(script)}). Install `redis` or `fakeredis` for production."
        )

    def register_script(self, script: str) -> "object":
        """Return a Script-like callable that delegates to self.eval().
        The real redis-py's Script() does SHA1 caching + EVALSHA; the
        stub just calls eval() directly (no caching benefit in-process).
        """

        class _Script:
            def __init__(_self, _client, _script: str) -> None:
                _self._client = _client
                _self._script = _script

            def __call__(_self, keys, args, client=None):
                # redis-py's Script.__call__ accepts (keys=[], args=[], client=None)
                if client is None:
                    client = _self._client
                return client.eval(_self._script, len(keys), *(keys + args))

        return _Script(self, script)


def ping() -> bool:
    """Health-check the underlying Redis. Used by `/health`."""
    try:
        get_client().ping()
        return True
    except Exception:
        return False


def reset_for_tests() -> None:
    """Drop all keys. Test-only utility."""
    global _client
    if _client is not None:
        try:
            _client.flushdb()
        except Exception:
            pass
