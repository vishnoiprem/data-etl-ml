# Lesson 01 — State Externalization (Redis)

> **A service that holds state in-process can't horizontally scale. A service that holds state in Redis can.**

## 🎯 Outcome

By the end of this lesson you can:

1. Take the Phase 4 `TokenBucketRateLimiter` (in-process dict) and produce a `RedisTokenBucket` that shares state across 8 uvicorn workers.
2. Explain why the Lua script is the key insight (atomic GET-then-DECR).
3. Decide when state belongs in Redis vs in-process (the rule: anything that's checked more than once per request, or that affects fairness across requests, goes to Redis).

## 🧠 Mindset

The Phase 4 service runs on **1 VM with 1 uvicorn worker**. Adding a 2nd worker means each user gets 2× the rate limit (each worker has its own bucket). Adding a 3rd worker makes it 3×. **At 12 CS users and 15,000 drafts/day, the in-process rate limiter is the ceiling.**

The fix: move the bucket to Redis. Every worker reads/writes the same bucket. The bucket's state is consistent across all workers.

**The mental model:** think of Redis as the **single source of truth** for things that affect fairness, correctness, or observability. Everything else can be in-process.

| State | In-process (Phase 4) | Redis (Phase 5) | Why |
|---|---|---|---|
| Rate-limit bucket | ✓ | ✓ (use Redis) | Affects fairness across workers |
| LLM response cache | ✓ | ✓ (use Redis) | 60% of calls are repeats; cache hit rate is the P95 win |
| Session token | ✓ | ✓ (use Redis) | OAuth requires persistence across requests |
| Circuit breaker state | ✓ | ✓ (keep in-process) | Worker-local; each worker has its own breaker |
| Stream chunk buffer | ✓ | ✓ (keep in-process) | One request, one response |

## 🛠️ Practice

Open `projects/01-redis-state/service/redis_state.py`. Read it once. Notice:

1. **`RedisTokenBucket`** uses a Lua script (atomically refill + decrement).
2. **`RedisTTLCache`** is `setex` + `get`; trivially simple.
3. **`RedisSessionStore`** namespaces by tenant_id so OAuth tokens for tenant A can't read tenant B's data.

Run the demo:

```bash
cd projects/01-redis-state
pip install redis fakeredis
python3 service/redis_state.py
```

Then run the 4 tests:

```bash
cd ../..
python3 -m pytest phase-5-advanced/projects/01-redis-state/tests/test_redis_state.py -v
```

Expected: **4 passed.**

## 🏛️ FDE Lens — the production reality underneath

| What | Phase 4 | Phase 5 | Cost |
|---|---|---|---|
| State location | In-process Python dict | Redis hash / Lua | +$10/mo (small Redis instance) |
| State at risk | Lost on restart | Survives restart (Redis AOF) | |
| Consistency | Per-worker (eventually consistent across workers) | Globally consistent (atomic Lua) | |
| Multi-worker readiness | Bad (each worker has its own state) | Good (single source of truth) | |

**The migration is non-breaking.** Phase 4's `TokenBucketRateLimiter` becomes Phase 5's `RedisTokenBucket`. The interface (`try_acquire`) is unchanged. **The 13/13 Phase 3 tests still pass because the contract is the same.**

## 🌙 Reflect

1. What state in your service should move to Redis? What state should stay in-process?
2. Where in your codebase would a Lua script have prevented a bug (race condition)?
3. The Phase 4 service is single-tenant. The Phase 5 service is multi-tenant. **What state can NEVER leak across tenants?**
