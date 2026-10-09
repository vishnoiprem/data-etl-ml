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
    Redis is not reachable."""
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
            sys.stderr.write(
                "redis_client: neither redis-py nor fakeredis is installed. "
                "Install one: `pip install redis fakeredis`.\n"
            )
            raise


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
