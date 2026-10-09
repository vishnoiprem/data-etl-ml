# 14 — Distributed Rate Limiter

> **Lesson 14 of the Distributed Data Storage & Partitioning track**

A multi-strategy rate limiter that combines three classic algorithms:
**token bucket** (bursty traffic), **fixed window** (cheap), and
**sliding window log** (precise). Per-key counters, lockfree atomic
checks where possible, and a clean strategy-strategy interface that
matches production designs (NGINX limit_req, Stripe, Cloudflare).

---

## 1. Requirements

### Functional
- `check(key, limit, window_seconds, cost=1)` returns `{allowed, remaining, reset_in}`.
- Multiple strategies: `token_bucket`, `fixed_window`, `sliding_window`.
- Atomic check across strategies (no double-spend under concurrency).
- Optional Lua-style scriptable check (we evaluate the algorithm in Python).

### Non-functional
- **High QPS**: ~100k checks/sec per node.
- **Bounded memory**: at most O(active keys) state kept.
- **Low latency**: p99 < 1ms in-process.
- **No external dependencies**.

### Out of scope
- Distributed rate limiting across processes (would need Redis / sliding window in Redis).
- Persistent state across restarts.

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| QPS | 100k checks/sec |
| Active keys | ~10M concurrent |
| State per key | 8–32 bytes |
| Memory | ~320 MB for 10M active keys |

---

## 3. High-level design

```
   client ──► [ Flask ] ──► [ RateLimiter ]
                                   │
                ┌──────────────────┼─────────────────┐
                ▼                  ▼                 ▼
         [ token bucket ]   [ fixed window ]   [ sliding window log ]
              │                  │                    │
              └─ per-key state in LRUCache (bounded) ┘
```

- **Strategy** is selected per call (parameter) so callers can pick the
  best fit per use-case (login throttling → token bucket; abuse → fixed).
- **State** lives in an `LRUCache` keyed by `(strategy, key)` so cold
  keys automatically evict.
- **Synchronization** uses one global `RLock` per cache — sufficient for
  in-process demonstration; production uses atomic compare-and-set.

---

## 4. API

| Method | Path | Body / Params | Returns |
|---|---|---|---|
| `POST` | `/api/check` | `{"key":"u:42","limit":100,"window_seconds":60,"strategy":"token_bucket","cost":1}` | `{"allowed","remaining","reset_in","strategy"}` |
| `GET`  | `/api/keys/<key>` | optional `?strategy=...` | current bucket/window state |
| `DELETE` | `/api/keys/<key>` | reset state for key |
| `GET`  | `/metrics` | — | counters |
| `GET`  | `/health` | — | `{"ok": true}` |

---

## 5. Data model

### Token-bucket record
```
{bucket_size, refill_rate, tokens, ts}
```
- `tokens` ≤ `bucket_size` at all times.
- On check: refill by `(now - ts) * refill_rate`, clamp to bucket_size,
  subtract `cost`. If `tokens < cost` → deny.

### Fixed window
```
{count, window_start}
```
- Reset `count=0` whenever `now >= window_start + window_seconds`.

### Sliding window log
```
{timestamps: list[float]}
```
- On check: drop timestamps older than `now - window_seconds`.
- If `len(timestamps) + cost > limit` → deny.
- Else push `now` `cost` times.

### LRU cache
Bound entries; eviction = drop oldest key.

---

## 6. Read/write path

### `POST /api/check`
1. Validate parameters: limit ≥ 1, window ≥ 1, cost ≥ 1.
2. Compute cache key: `(strategy, user_key)`.
3. Acquire bucket state from LRU (lazy-init).
4. Call strategy.check(state, now, limit, cost).
5. Write back updated state.
6. Return `{allowed, remaining, reset_in}`.

`reset_in` semantics:
- token_bucket: `(bucket_size - tokens) / refill_rate`
- fixed_window: `window_start + window_seconds - now`
- sliding_window: `min(timestamps) + window_seconds - now` (when denied)

---

## 7. Failure modes

| Failure | Mitigation |
|---|---|
| State eviction (LRU pressure) | Cold key gets a fresh bucket — slightly more lenient. Document. |
| Clock skew | Token refill uses monotonic-ish `time.time()`. Real systems use `time.monotonic()`. |
| Hot key (one user spamming) | Token bucket + cost > 1 per check naturally absorbs bursts. |
| Check storm | Use `LRUCache` for O(1) lookup; `RLock` per cache write. |

---

## 8. Tradeoffs

- **Token bucket** — smooths bursts, simple state, good default.
- **Fixed window** — cheapest (one int + ts), but boundary spike (2x at edge).
- **Sliding log** — most precise, memory grows with `limit * window` per key.
  Use only for low-limit / high-precision endpoints.
- **LRU + lock** — simple, correct, but not lockfree. Redis scripts are the
  production answer for distributed correctness.

---

## 9. How the code maps to this design

| File | Role |
|---|---|
| `code/service.py` | `TokenBucket`, `FixedWindow`, `SlidingWindow`, `RateLimiter`. |
| `code/app.py` | Flask HTTP service exposing `/api/check` + `/api/keys`. |
| `tests/test_service.py` | Algorithm correctness tests. |
| `tests/test_app.py` | HTTP-level tests using Flask test client. |
