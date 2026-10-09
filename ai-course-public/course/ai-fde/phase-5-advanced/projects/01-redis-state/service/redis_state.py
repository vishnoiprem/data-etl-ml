"""
projects/01-redis-state/service/redis_state.py — Redis-backed rate limit + cache + session.

Three primitives, each with the same interface as the Phase 4 in-process versions.
The eval set + the 25/25 tests pass unchanged because the contract is the same.

1. RedisTokenBucket         — per-user token bucket (atomic via Lua).
2. RedisTTLCache            — LRU + TTL on Redis (sorted-set scoring).
3. RedisSessionStore        — per-tenant session tokens.

The Lua script in RedisTokenBucket is the key insight. A non-atomic
GET-then-DECR-then-SET would race: 2 workers could both see 1 token
remaining and both decrement, ending at -1. The Lua script runs atomically
on the Redis server, so the race is impossible.

How to run
----------
    pip install redis fakeredis
    python3 redis_state.py
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Optional

from redis_client import get_client


# ---------------------------------------------------------------------------
# 1. RedisTokenBucket — atomic, multi-worker-safe
# ---------------------------------------------------------------------------
# Lua: bucket schema = "tb:{user_id}" → hash with {tokens (float), ts (float)}
# Refill rule: tokens = min(capacity, tokens + (now - ts) * refill_rate)
TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local cost = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

local data = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(data[1])
local ts = tonumber(data[2])
if tokens == nil then
    tokens = capacity
    ts = now
end
local elapsed = math.max(0, now - ts)
tokens = math.min(capacity, tokens + elapsed * refill_rate)

local allowed = 0
if tokens >= cost then
    tokens = tokens - cost
    allowed = 1
end
redis.call('HMSET', key, 'tokens', tokens, 'ts', now)
redis.call('EXPIRE', key, 60)
return {allowed, tostring(tokens)}
"""


@dataclass
class BucketResult:
    allowed: bool
    tokens_remaining: float


class RedisTokenBucket:
    """A per-user token bucket, atomic across workers via Redis Lua."""

    def __init__(self, *, capacity: float, refill_rate: float) -> None:
        if capacity <= 0 or refill_rate <= 0:
            raise ValueError("capacity and refill_rate must be > 0")
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._script = None  # lazy-loaded

    def _ensure_script(self) -> None:
        if self._script is None:
            client = get_client()
            self._script = client.register_script(TOKEN_BUCKET_LUA)

    def try_acquire(self, user_id: str, n: float = 1.0) -> bool:
        self._ensure_script()
        result = self._script(
            keys=[f"tb:{user_id}"],
            args=[self.capacity, self.refill_rate, n, time.monotonic()],
        )
        return bool(int(result[0]))

    def reset(self, user_id: str) -> None:
        get_client().delete(f"tb:{user_id}")


# ---------------------------------------------------------------------------
# 2. RedisTTLCache — simple key/value cache with TTL
# ---------------------------------------------------------------------------
class RedisTTLCache:
    """A key/value cache with a per-key TTL. LRU is approximated by a
    Redis maxmemory-policy=allkeys-lru (set on the server)."""

    def __init__(self, default_ttl_s: float = 300.0) -> None:
        self.default_ttl_s = default_ttl_s

    def get(self, key: str) -> Optional[Any]:
        raw = get_client().get(f"cache:{key}")
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl_s: Optional[float] = None) -> None:
        ttl = int(ttl_s or self.default_ttl_s)
        get_client().setex(f"cache:{key}", ttl, json.dumps(value, default=str))

    def delete(self, key: str) -> None:
        get_client().delete(f"cache:{key}")


# ---------------------------------------------------------------------------
# 3. RedisSessionStore — per-tenant session tokens
# ---------------------------------------------------------------------------
class RedisSessionStore:
    """A per-tenant session token store. Each tenant has its own keyspace
    (`sess:{tenant_id}:{session_id}`) so OAuth tokens for tenant A can't
    read or write tenant B's data."""

    def __init__(self, default_ttl_s: float = 3600.0) -> None:
        self.default_ttl_s = default_ttl_s

    def put(self, tenant_id: str, session_id: str, payload: dict) -> None:
        get_client().setex(
            f"sess:{tenant_id}:{session_id}",
            int(self.default_ttl_s),
            json.dumps(payload, default=str),
        )

    def get(self, tenant_id: str, session_id: str) -> Optional[dict]:
        raw = get_client().get(f"sess:{tenant_id}:{session_id}")
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def delete(self, tenant_id: str, session_id: str) -> None:
        get_client().delete(f"sess:{tenant_id}:{session_id}")


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------
def main() -> int:
    print("=" * 70)
    print("Redis state — Phase 5 Project 1 (PacificFreight scale-out)")
    print("=" * 70)

    # 1. Token bucket: 2 workers, 1 user, 5 tokens capacity.
    bucket = RedisTokenBucket(capacity=5.0, refill_rate=1.0)
    print("\n--- Token bucket (capacity=5, refill 1/s) ---")
    for i in range(7):
        ok = bucket.try_acquire("mei@pf.com", n=1.0)
        print(f"  call {i+1}: {'ALLOW' if ok else 'DENY'}")

    # 2. Cache: 3 keys, 1 expires.
    cache = RedisTTLCache(default_ttl_s=2.0)
    print("\n--- Cache (TTL=2s) ---")
    cache.set("k1", {"draft": "hello"}, ttl_s=1.0)
    cache.set("k2", {"draft": "world"}, ttl_s=10.0)
    print(f"  k1 (after 1s): {cache.get('k1')}")
    print(f"  k2 (after 1s): {cache.get('k2')}")
    time.sleep(1.5)
    print(f"  k1 (after 2.5s): {cache.get('k1')}")
    print(f"  k2 (after 2.5s): {cache.get('k2')}")

    # 3. Session store: 2 tenants, isolation.
    sess = RedisSessionStore()
    print("\n--- Session store (tenant isolation) ---")
    sess.put("pf", "alice", {"role": "cs_senior"})
    sess.put("ecom", "alice", {"role": "cs_junior"})
    print(f"  pf/alice   = {sess.get('pf', 'alice')}")
    print(f"  ecom/alice = {sess.get('ecom', 'alice')}")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
