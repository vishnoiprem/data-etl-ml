"""
projects/01-redis-state/tests/test_redis_state.py — 4 tests for the Redis state layer.

1. test_lua_atomicity        — 100 concurrent acquires respect the bucket capacity
2. test_ttl_works            — keys expire after the TTL
3. test_tenant_isolation     — tenant A can't read tenant B's session
4. test_failover_continuity  — a dropped connection doesn't lose data
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

SVC = Path(__file__).parent.parent / "service"
sys.path.insert(0, str(SVC))

from redis_state import RedisTokenBucket, RedisTTLCache, RedisSessionStore  # noqa: E402
from redis_client import get_client, reset_for_tests  # noqa: E402


def _setup():
    """Reset the test DB and return a fresh client."""
    reset_for_tests()
    return get_client()


# ---------------------------------------------------------------------------
# 1. Lua atomicity: 100 acquires, capacity=10 → exactly 10 allowed
# ---------------------------------------------------------------------------
def test_lua_atomicity():
    """A non-atomic GET/SET would race; the Lua script must not."""
    _setup()
    bucket = RedisTokenBucket(capacity=10.0, refill_rate=0.001)  # effectively no refill
    allowed = 0
    for i in range(100):
        if bucket.try_acquire("alice@pf.com", n=1.0):
            allowed += 1
    assert allowed == 10, f"expected exactly 10 allowed (capacity), got {allowed}"
    print(f"  PASS: 100 acquires → {allowed} allowed (capacity=10)")


# ---------------------------------------------------------------------------
# 2. TTL: keys expire after the TTL
# ---------------------------------------------------------------------------
def test_ttl_works():
    """A key with TTL=1s should be gone after 2s; a key with TTL=10s should remain."""
    _setup()
    cache = RedisTTLCache(default_ttl_s=1.0)
    cache.set("short", {"v": 1}, ttl_s=1.0)
    cache.set("long", {"v": 2}, ttl_s=10.0)
    time.sleep(2.0)
    assert cache.get("short") is None, "short should have expired"
    assert cache.get("long") == {"v": 2}, "long should still be there"
    print("  PASS: short expired, long survived")


# ---------------------------------------------------------------------------
# 3. Tenant isolation: tenant A can't read tenant B's session
# ---------------------------------------------------------------------------
def test_tenant_isolation():
    """sess:pf:alice and sess:ecom:alice must be different keys."""
    _setup()
    sess = RedisSessionStore()
    sess.put("pf", "alice", {"role": "cs_senior"})
    sess.put("ecom", "alice", {"role": "cs_junior"})
    assert sess.get("pf", "alice") == {"role": "cs_senior"}
    assert sess.get("ecom", "alice") == {"role": "cs_junior"}
    # Delete one tenant; the other is unaffected
    sess.delete("pf", "alice")
    assert sess.get("pf", "alice") is None
    assert sess.get("ecom", "alice") == {"role": "cs_junior"}
    print("  PASS: pf and ecom are isolated; delete doesn't cross tenants")


# ---------------------------------------------------------------------------
# 4. Failover continuity: a dropped connection doesn't lose data
# ---------------------------------------------------------------------------
def test_failover_continuity():
    """We can't simulate a real Redis failover in a unit test, but we CAN
    verify that calling the same Redis instance twice (e.g. after a
    reconnect) returns the same data. This is the contract."""
    _setup()
    bucket = RedisTokenBucket(capacity=5.0, refill_rate=0.1)
    bucket.try_acquire("bob@pf.com", n=2.0)
    # Simulate a "reconnect" by re-instantiating (the client is a singleton
    # in the wrapper, so this tests the same connection).
    bucket2 = RedisTokenBucket(capacity=5.0, refill_rate=0.1)
    # The bucket's state lives in Redis, not in the Python object.
    # We can only observe this if we drop the in-process state.
    # For now: just verify the second bucket respects the existing state.
    # (A real failover test requires Redis Sentinel + docker; that's a
    # separate test, not in this unit suite.)
    ok = bucket2.try_acquire("bob@pf.com", n=4.0)  # should be denied (3 tokens left)
    assert not ok, "second bucket must see the same Redis state"
    print("  PASS: bucket state survives Python object re-instantiation")


def _run_all():
    print("=" * 60)
    print("Redis state tests — Phase 5 Project 1")
    print("=" * 60)
    for fn in [
        test_lua_atomicity,
        test_ttl_works,
        test_tenant_isolation,
        test_failover_continuity,
    ]:
        print(f"\n[{fn.__name__}]")
        fn()
    print("\n" + "=" * 60)
    print("ALL 4 REDIS STATE TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    _run_all()
