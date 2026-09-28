# Lesson 4 — Online vs Offline Serving

> **Type:** Article · Module 6 · Feature Stores & ML Data Infrastructure
> The dual-write problem, freshness patterns, and keeping online in sync with offline.

---

## The two worlds

```
   OFFLINE (training)                  ONLINE (inference)
   ─────────────────                  ──────────────────
   100M rows batch                    1 row at a time
   minutes per query                  <50ms p95
   Parquet on S3                      Redis / DynamoDB
   point-in-time correct              latest value
   "history of user_X"                "what is user_X now"
   one-shot, async                    always-on, hot path
```

Same feature, two destinations, two read patterns. **Keeping them in sync is the hard part.**

---

## The dual-write problem

The naive approach is to write to both stores in one pipeline:

```python
# BAD: dual-write from a streaming job
def process_event(event):
    feature = compute_feature(event)

    # Write to offline (Parquet)
    offline_table.append(feature)

    # Write to online (Redis)
    redis.set(f"user:{event.user_id}", feature.to_json())
```

Why this is dangerous:
- **Atomicity**: if the offline write succeeds and online fails, they diverge
- **Backpressure**: a slow Redis write blocks the streaming job
- **Schema drift**: offline and online can drift if you change one path

The fix: **CDC + a separate sync**. Offline is the source of truth. Online is derived.

```
   source events
        │
        ▼
   ┌────────────────┐
   │  Flink/Spark   │  compute features
   └────────┬───────┘
            │
   ┌────────┴─────────────┐
   │                      │
   ▼                      ▼
   OFFLINE (Parquet)     ONLINE (Redis/Dynamo)
   source of truth        ◄─── CDC / streaming sync
                              (eventually consistent)
```

The online store is **always a cache** of recent offline values. If it drifts, the offline store is right.

---

## The freshness pattern

| Tier | Lag | How |
|---|---|---|
| Real-time | < 1s | Stream + direct write (with care for atomicity) |
| Near-real-time | < 1 min | Stream + Kafka buffer → offline → CDC → online |
| Minute | < 5 min | Spark Structured Streaming, 1-min micro-batches |
| Hour | < 1 hr | Cron / DAG, batched |

Most production systems are in the **minute-to-hour range**. Real-time is expensive.

```python
# Streaming example: write to offline, sync to online via CDC
def process_event(event):
    feature = compute_feature(event)
    offline_table.append(feature)
    # online is updated by a separate CDC consumer
```

```sql
-- Online sync consumer (Debezium / Flink CDC):
-- reads from the offline WAL and updates online.
```

---

## The "online store from offline" pattern

The most reliable pattern: **online is a projection of offline**.

```
   offline Parquet
        │
        ▼
   ┌──────────────────────┐
   │  Sync job (every 1m) │  reads latest partition, upserts Redis
   └──────────┬───────────┘
              │
              ▼
   Redis (online store)

   Online is *eventually consistent* with offline.
   Lag: < 1 minute.
```

**Why this wins:**
- Offline is the source of truth. If online drifts, recompute offline → re-sync.
- No dual-write atomicity issue.
- Schema changes go to offline; online updates automatically.

**Cost**: lag (minutes). For most ML, this is fine.

---

## The "online store from streaming" pattern

For sub-second freshness, write directly to online from the stream and use **idempotent keys** + **deferred offline backfill**.

```
   event
     │
     ▼
   Flink
     ├──► Redis (latest value, idempotent by entity+ts)
     └──► Parquet (offline, batched every 5 min)
```

The key trick: use **last-write-wins** in Redis (key = entity_id, value = feature map). The offline backfill catches anything missed.

---

## The serving pattern at the model

```
   ┌──────────────────────────────────────────────────────┐
   │  Online inference                                     │
   │                                                       │
   │  1. Model gets a request:                             │
   │       POST /predict                                    │
   │       { "user_id": "u_123", "context": {...} }         │
   │                                                       │
   │  2. Feature lookup:                                    │
   │       features = online_store.get(                    │
   │           entity_id="u_123",                          │
   │           feature_view="user_clicks_30d"              │
   │       )                                                │
   │                                                       │
   │  3. Model inference:                                   │
   │       prediction = model.predict(features)            │
   │                                                       │
   │  4. Log + return                                       │
   └──────────────────────────────────────────────────────┘
```

The model doesn't compute features. It only **fetches** them. The feature store owns the compute.

This is critical because:
- The training pipeline uses the **same** feature definitions
- The serving pipeline doesn't have access to historical data
- Drift between the two is impossible if you use the same store

---

## The "what about cold start" problem

When a new `user_id` appears, the online store has nothing. Options:

1. **Backfill on demand.** At request time, compute features from offline and populate online.
2. **Default values.** Return zeros / mean for missing features (model trains with this, so it knows).
3. **Async pre-warm.** When a user signs up, compute their features and warm the cache.

```
   request: user_id = "new_user_42"
   online store: MISS
        │
        ▼
   ┌──────────────────────┐
   │  fallback strategy   │
   │                      │
   │  if production:      │
   │   ► backfill (slow)  │  <-- 100ms hit, one-time
   │   ► return features  │
   │                      │
   │  if hot path:        │
   │   ► return defaults  │
   │   ► async warm cache │
   └──────────────────────┘
```

---

## The "consistency at read" trick

For high-throughput online, you can trade freshness for consistency:

```python
# Read with consistency
def read_features(user_id):
    # 1. Read online (latest cached)
    cached = online_store.get(user_id)
    cached_ts = cached.get("_ts", 0)

    # 2. If stale (> 5 min), refresh from offline
    if time.time() - cached_ts > 300:
        fresh = offline_store.get_as_of(user_id, time.time())
        online_store.set(user_id, fresh)
        return fresh
    return cached
```

This makes online reads **strongly consistent at the cost of latency** when stale. Good for models where stale features materially hurt predictions (fraud, recommender freshness).

---

## The "p99 latency" budget

For sub-50ms online inference, every microsecond matters:

| Component | Budget |
|---|---|
| API auth | 5ms |
| Feature fetch (Redis) | 5–10ms (network) |
| Feature fetch (DynamoDB) | 5–15ms |
| Feature assembly (parse, merge) | 1–3ms |
| Model inference (small) | 5–20ms |
| Model inference (LLM) | 200ms–2s |
| Logging | 5ms |
| **Total (small model)** | **30–50ms** |
| **Total (LLM)** | **250ms–2s** |

If you're missing the SLA, profile. Usually the culprit is **online fetch** (too many keys) or **model inference** (too large).

---

## The "what to monitor" checklist

- **Freshness**: max lag across all features (online vs offline)
- **Online hit rate**: % of fetches served from online (vs fallback)
- **p50 / p95 / p99 latency**: per-feature and end-to-end
- **Skew**: sample comparison of online vs offline values for same entity_id
- **Cache size & evictions**: online store memory pressure
- **Backfill lag**: how long to recover from cold start

---

## What Comes Next

> Lesson 5 — **ML Observability** — drift, skew, silent regressions. What to alert on and what to ignore.