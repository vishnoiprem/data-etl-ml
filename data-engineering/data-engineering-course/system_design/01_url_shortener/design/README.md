# 01 — URL Shortener (TinyURL / bit.ly)

> **Lesson 1 of 6 — Read-Heavy Systems**

A complete, runnable design + implementation of a URL shortener. The
service takes a long URL and returns a short, opaque key. Visiting the
short URL redirects to the original.

---

## 1. Requirements

### Functional
- Given a long URL, return a short key (e.g. `https://sho.rt/aB3xY9`).
- Given a short key, return (302 redirect to) the original long URL.
- Custom aliases (`/my-link`).
- Optional: TTL / expiry; analytics (click counts).

### Non-functional
- **High read QPS** — reads are 100× writes in production.
- Short links must be **< 10 chars** (a 7-char base62 key fits ~3.5T unique URLs).
- **Low redirect latency** — p99 < 50 ms.
- **Highly available** — losing the redirector means losing customer traffic.

### Out of scope (for this lesson)
- Anti-abuse / bot detection.
- Multi-region active-active.
- User accounts.

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| Writes | 100 M URLs / month → ~40 writes/sec |
| Reads | 100:1 read:write → ~4,000 reads/sec (peak ~12,000/sec) |
| Storage (5y) | 100 M × 12 × 5 ≈ 6 B records × 500 B ≈ 3 TB |
| Short URL length | 7 chars base62 (3.5T keyspace) |

Reads dominate. **Optimize for the read path.**

---

## 3. High-level design

```
client ──► [ API / app tier ] ──► [ cache ] ──► [ key-DB ]
                                        │             │
                                        └─miss────────┘
```

- App tier: stateless Flask service. N replicas behind a load balancer.
- Cache: Redis. Hot keys live ~24h here. Misses fall through to the DB.
- DB: write-optimized for `INSERT (key, long_url, created_at)`. In
  production this is a sharded MySQL or DynamoDB. We use `KeyValueStore`.

---

## 4. API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/shorten` | `{"url": "...", "alias": "optional"}` | `{"key": "aB3xY9", "short_url": "http://.../aB3xY9"}` |
| `GET`  | `/<key>` | — | 302 redirect to long URL |
| `GET`  | `/api/stats/<key>` | — | `{"key", "long_url", "clicks", "created_at"}` |
| `GET`  | `/metrics` | — | counters + histograms |
| `GET`  | `/health` | — | `{"ok": true}` |

---

## 5. Data model

### Key generator
- Default: SHA-256 of long URL → first 8 bytes → base62 → first 7 chars.
  Deterministic: same long URL always gets same short key. **Hot cache
  friendliness**: deduplicates writes.
- Custom: caller supplies `alias`; reserved-words check.

### Storage

`kv["url:<key>"] = {"url": "...", "created_at": ..., "clicks": 0}`

In production you'd split this into two tables:
- `urls (key PK, long_url, user_id, created_at, expires_at)`
- `clicks (key, ts, ip, ua, country)` for analytics.

---

## 6. Read path deep dive

`GET /<key>` (the hot path):

1. Look up `key` in Redis cache. **Hit** (~95% of the time) → 302 to
   `long_url`. Done.
2. **Miss** → query the DB.
3. If found, write to cache (TTL 24h), 302 redirect, increment clicks.
4. If not found → 404.

Caching is the whole game. The 95% cache hit rate means the DB sees
~5% of reads ≈ 200 QPS, which a single small Postgres handles.

---

## 7. Write path deep dive

`POST /api/shorten`:

1. Validate URL (scheme, length).
2. If `alias` provided, check not reserved; reserve atomically.
3. Else, compute `key = short_hash(url)`. If `kv` already has it (idempotent
   retry), return existing.
4. Else, on collision, append a counter to the URL and re-hash (max 5 tries).
5. Persist `url:<key>` to DB, write-through to cache, return.

Idempotency: if the same long URL is shortened twice, we want the same key.
Hence the deterministic hash. This also deduplicates analytics.

---

## 8. Sharding & replication

In production:
- **Sharding**: hash(key) mod N. Sticky to a shard = sticky to a cache.
- **Replication**: each shard has 1 primary + ≥2 replicas. Reads served
  from replicas; writes go to primary. Async replication → small
  staleness window, acceptable for redirects.
- **Cache locality**: pick a hash function that co-locates hot keys
  with their DB shard so cache misses don't fan out.

---

## 9. Failure modes

| Failure | Mitigation |
|---|---|
| DB down | Serve from cache only. Disable shortening, serve redirects. |
| Cache down | Throttle; degrade to direct DB reads. Rate-limit writes. |
| Hot key (viral link) | 95% of traffic to one key. Mitigate with **request coalescing** at the LB and **local in-process LRU** at each app replica. |
| Key collision | Loop with counter; alert on collision rate. |

---

## 10. Tradeoffs

- **MD5/SHA-256 vs random**: hashing is idempotent, deduplicates. Random
  is simpler. Real systems use counter + base62 with sharded counters.
- **302 vs 301**: 302 means client may re-hit, 301 means client caches.
  For analytics, use 302 + custom analytics rewrite.
- **Custom aliases**: opens the door to squatting / abuse. Reserve
  common words, allow reporting.

---

## 11. How the code maps to this design

| File | Role |
|---|---|
| `code/service.py` | The core URLShortener class — short_hash, collision handling, cache. |
| `code/app.py` | Flask HTTP service exposing the API + /metrics + /health. |
| `code/loadtest.py` | Synthetic read-heavy load tester. |
| `tests/test_service.py` | Unit tests for the core service. |
| `tests/test_app.py` | HTTP-level tests using Flask's test client. |
