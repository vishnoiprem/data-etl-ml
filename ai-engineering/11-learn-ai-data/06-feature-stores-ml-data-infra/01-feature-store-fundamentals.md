# Lesson 1 — Feature Store Fundamentals

> **Type:** Article · Module 6 · Feature Stores & ML Data Infrastructure
> What a feature store is, what it solves, and the three components it owns.

---

## What is a feature store?

A feature store is a **data system that serves pre-computed features to ML models in a consistent way** — both at training time (offline, bulk) and at inference time (online, low-latency). It is the ML equivalent of a curated data warehouse for analytics, but with two extra outputs the warehouse doesn't have:

1. **Point-in-time correctness** for training (no future leakage)
2. **Online serving** with sub-50ms latency

```
   FEATURE STORE
   ─────────────
   ┌──────────────────┐
   │  feature          │ ← single source of truth for "what is this feature"
   │  definitions      │    (SQL + owner + version + freshness SLA)
   └────────┬─────────┘
            │
   ┌────────┴──────────────────────────┐
   │                                   │
   ▼                                   ▼
   OFFLINE STORE                ONLINE STORE
   (Parquet/Iceberg,             │  (Redis/DynamoDB,
    point-in-time correct)      │   sub-50ms reads)
   │                                   │
   ▼                                   ▼
   Training pipelines           Online inference
   (millions of rows,            (1 row, milliseconds)
    point-in-time joins)
```

---

## The three things it owns

| Component | What it does | Tech |
|---|---|---|
| **Feature definitions** | Code that defines each feature as SQL/Python + metadata (owner, version, type, SLA) | Feast, Tecton, Featureform |
| **Offline store** | Historical, point-in-time correct features for training and batch scoring | Parquet + Iceberg/Delta, BigQuery, Snowflake |
| **Online store** | Latest feature values for low-latency serving | Redis, DynamoDB, Bigtable, Cassandra |

Optional but common: a **feature registry** (UI to browse/discover features) and **monitoring** (drift, freshness, distribution).

---

## Why the feature store exists: the problems it solves

### Problem 1 — Training/serving skew
The model behaves differently in production than in evaluation because the features it sees are computed differently.

```
   TRAINING                              SERVING
   ────────                              ───────
   feature: clicks_last_30d
   SQL: SUM(click) WHERE ts >= NOW()-30d
   data:   batch, today 02:00 UTC        feature: clicks_last_30d
                                         code: looks up a precomputed value
                                                in Redis
                                         data: updated 5 minutes ago

   These can disagree for trivial reasons:
   - timezone drift
   - null handling
   - delayed upstream events
   - "last 30 days" recomputed slightly differently
```

A feature store enforces **one definition** used in both paths.

### Problem 2 — Point-in-time leakage in training
If you join features to labels naively, you can leak future information into the past. A feature store uses **point-in-time joins** that respect the timestamp of each label.

```sql
-- WRONG: leaks future clicks into the label row
SELECT l.user_id, l.churned, f.clicks_last_30d
FROM labels l
JOIN features f ON l.user_id = f.user_id;

-- RIGHT: only use feature values as of label timestamp
SELECT l.user_id, l.churned, f.clicks_last_30d
FROM labels l
ASOF JOIN features f
  ON l.user_id = f.user_id
 AND f.event_ts <= l.label_ts;  -- no future info
```

### Problem 3 — Discoverability / re-use
Without a registry, every team reinvents "user_lifetime_value" slightly differently. A feature store publishes features once, used by many models.

### Problem 4 — Online/offline consistency
Without the online store, teams roll their own Redis caches with bespoke backfills. The result: drift, outage, on-call pain.

### Problem 5 — Freshness SLOs
Who is responsible for keeping `user_lifetime_value` fresh every 5 minutes? Without ownership, nobody. The feature store **makes ownership explicit**.

---

## The anatomy of a feature definition

```python
@feature_view(
    name="user_clicks_30d",
    entities=["user_id"],
    ttl=timedelta(days=90),
    online=True,
    owner="growth-team",
    freshness_sla="5m",
    description="Total clicks per user in the last 30 days",
)
def user_clicks_30d(user_id: str, ts: datetime) -> pd.DataFrame:
    return f"""
        SELECT
          user_id,
          event_ts,
          SUM(1) as clicks
        FROM events
        WHERE event_type = 'click'
          AND event_ts >= ts - INTERVAL 30 DAY
        GROUP BY user_id, event_ts
    """
```

The definition has four parts:
- **Logic** — what to compute (the SQL/Python)
- **Entity** — what key identifies a row (`user_id`, `product_id`, ...)
- **TTL** — how long values stay valid
- **Metadata** — owner, SLA, description (so others can find and trust it)

---

## The online/offline consistency pattern

```
   source events (Kafka, S3, ...)
        │
        ▼
   ┌────────────────┐
   │  streaming     │ Flink/Spark Structured Streaming
   │  transform     │ compute features on the fly
   └────────┬───────┘
            │
   ┌────────┴─────────────────────────┐
   │                                   │
   ▼                                   ▼
   offline store                 online store
   (Parquet, partitioned           (Redis / DynamoDB,
    by event_ts)                    key: entity_id,
    point-in-time correct           value: feature map)
                                   │
                                   ▼
                              online inference
                              (model pulls by entity_id)
```

The trick: **the same transform runs against both stores**. The only difference is the destination and the trigger.

---

## The "should you build one" question

Most teams **should not build a feature store from scratch**. Use an open-source or managed one:

| Scale | Recommendation |
|---|---|
| < 10 models, batch-only | Don't. Use a DAG that writes features to a table. |
| 10–100 models, some online | Feast (open-source, hosted in your cloud) |
| 100+ models, regulated, online + offline | Tecton (managed) or AWS / GCP / Databricks built-ins |
| Tightly coupled to a platform | Use the platform's feature store (BigQuery Feature Store, Databricks Feature Store, Snowflake Feature Store) |

Build from scratch only when none of the above fit. Most "we need a feature store" projects actually need: **(a) a feature registry, (b) point-in-time correct offline features, (c) an online cache**. You can get there without writing your own system.

---

## The "data scientist vs platform team" ownership question

The feature definition is **owned by the data scientist** (they know what the model needs). The **infrastructure is owned by the platform team**. The feature store is the contract between them.

```
   data scientist             platform team
   ─────────────              ─────────────
   "I need clicks_last_30d"    "I'll wire the pipeline"
   "definition = SQL + TTL"    "online store is up"
   "test set: precision=0.4"   "freshness = 4m, in SLA"
```

If the data scientist writes the SQL and the platform team wires the infra, you get velocity without sacrificing correctness.

---

## Common mistakes

1. **Building a feature store as a side project.** It is infrastructure. Treat it like one.
2. **Skipping the registry.** If features aren't discoverable, every team reinvents them.
3. **Mixing online and offline logic.** The single biggest source of skew. One definition, two stores.
4. **No freshness SLA.** If nobody owns freshness, every consumer rolls their own retry.
5. **Backfilling without a plan.** Re-running a feature over 3 years of history at 02:00 UTC will cause an outage somewhere.

---

## What Comes Next

> Lesson 2 — **Feature Store Comparison** — Feast, Tecton, Featureform, AWS / GCP / Databricks / Snowflake built-ins. The decision framework.