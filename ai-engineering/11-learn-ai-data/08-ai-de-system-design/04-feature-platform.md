# Lesson 4 — Feature Platform

> **Type:** Article · Module 8 · AI DE System Design
> A feature store + online serving + drift monitoring, designed for 500 models.

---

## The problem

> Design a feature platform for 500 ML models (recommendation, fraud, churn, LTV, ad CTR, ...). 1000+ features. Both online and offline. Multiple teams contributing features. Strict freshness SLAs (sub-second to daily). Onboarding for a new model should take < 1 week.

---

## Step 1 — CLARIFY

```
   models:         500 (recommendation, fraud, churn, LTV, ad CTR, ...)
   features:       1000+ (entity-keyed: user_id, item_id, transaction_id)
   entities:       user, item, transaction, account
   freshness:      sub-second (fraud features)
                   5 min (recommendation)
                   hourly (churn)
                   daily (LTV)
   latency:        online < 50ms p95
                   offline: bulk reads (millions of rows / query)
   consumers:      10+ data science teams, 5+ use cases
   cost:           < $200k/mo for online + offline + compute
   failure mode:   online/offline skew → silent model degradation
                   freshness miss → stale features → bad predictions
                   single-tenant leak → security breach
```

---

## Step 2 — SKETCH

```
   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │   [SOURCE DATA]                                              │
   │       │  Kafka / S3 / RDBMS                                  │
   │       ▼                                                      │
   │   [FEATURE INGEST DAG]                                       │
   │     │                                                        │
   │     ├──► [Streaming transform (Flink / Spark Streaming)]    │
   │     │       (sub-second, 5-min features)                    │
   │     │                                                        │
   │     └──► [Batch transform (Spark / dbt)]                    │
   │             (hourly, daily features)                        │
   │             │                                                │
   │             ▼                                                │
   │   [OFFLINE STORE: Parquet on S3 + Iceberg/Delta]             │
   │     point-in-time correct, versioned                         │
   │             │                                                │
   │             ▼                                                │
   │   [ONLINE SYNC (CDC, every 1 min)]                          │
   │             │                                                │
   │             ▼                                                │
   │   [ONLINE STORE: Redis / DynamoDB]                          │
   │     p95 < 10ms read                                          │
   │                                                              │
   │   ──── serving ────                                         │
   │                                                              │
   │   [MODEL ONLINE INFERENCE]                                  │
   │       ├──► Fetch features from online store                  │
   │       ├──► Combine with context                              │
   │       └──► Predict                                           │
   │                                                              │
   │   ──── operations ────                                      │
   │                                                              │
   │   [FEATURE REGISTRY (UI + API)]                              │
   │     discoverability, ownership, lineage                      │
   │                                                              │
   │   [MONITORING: drift, freshness, skew, ACL]                  │
   │   [EVAL HARNESS for retraining triggers]                     │
   │   [COST DASHBOARD per team / per feature]                    │
   └──────────────────────────────────────────────────────────────┘
```

---

## Step 3 — DEEP-DIVE

### Box 1: Feature definition (the contract)

```python
# Feast / Tecton-style definition
@feature_view(
    name="user_clicks_30d",
    entities=["user_id"],
    ttl=timedelta(days=90),
    online=True,
    owner="growth-platform",
    freshness_sla="5m",
    description="Total clicks per user in the last 30 days",
    data_source="kafka://events/clicks",
    version="1.2",
)
def user_clicks_30d(user_id, ts):
    return f"""
        SELECT user_id, event_ts, COUNT(*) as clicks
        FROM events
        WHERE event_type = 'click'
          AND event_ts >= ts - INTERVAL 30 DAY
        GROUP BY user_id, event_ts
    """
```

This **single definition** is reused in:
- Online transform (streaming)
- Offline batch transform
- Point-in-time training join
- Online serving lookup

The definition is **versioned, owned, documented**. The moat of the platform is consistency.

### Box 2: Online/offline consistency

```
   SOURCE EVENTS
        │
        ▼
   STREAMING TRANSFORM (Flink)
        │
        ├──► write to offline (Parquet, idempotent by entity+ts)
        │
        └──► write to online (Redis, last-write-wins)

   CDC CONSUMER (catches any misses)
        │
        └──► updates online from offline
```

The streaming transform is the source of truth. If it succeeds, both stores get the update. If online fails, offline catches up via CDC. **No dual-write atomicity problem.**

### Box 3: Point-in-time correctness for training

```sql
-- For training data generation
SELECT
  l.user_id,
  l.event_ts AS label_ts,
  l.label,
  f.clicks_30d
FROM labels l
ASOF JOIN features f
  ON l.user_id = f.user_id
 AND f.feature_ts <= l.event_ts;
```

The `ASOF JOIN` semantics prevent future feature leakage. Critical: any model trained without this will silently degrade.

### Box 4: Freshness monitoring

```
   FRESHNESS SLA (per feature)
   ────────────────────────────
   fraud features:       < 5s
   recommendation:      < 1 min
   churn:               < 1 hour
   LTV:                 < 24 hours

   MONITORING
   ──────────
   Per-feature lag (now - max(event_ts)) vs SLA
   Alert if lag > SLA for 2 consecutive runs
```

If a feature misses SLA, page the owner. The owner is in the feature definition metadata.

---

## Step 4 — TRADEOFFS

| Choice | Alternative | Why | Revisit if |
|---|---|---|---|
| **Feast (open-source)** | Tecton (managed) | Cost; team has 1+ FTE to operate | team < 1 FTE OR 200+ models |
| **Online store = Redis cluster** | DynamoDB / Cassandra | Lowest latency at sub-50ms | ops complexity > benefit |
| **Offline store = Parquet + Iceberg** | BigQuery / Snowflake | Lakehouse architecture; cheap | warehouse shop, can use native feature store |
| **Streaming transform in Flink** | Spark Streaming | Sub-second latency | ops complexity > benefit (5-min SLA ok) |
| **Per-feature freshness SLA** | Single global SLA | Different features have different needs | SLA violations cause model regressions |
| **Feature registry (Feast / Tecton)** | Self-managed wiki | Discoverability, ownership | team < 5 features |

---

## Step 5 — SUMMARY

**Decision:**
- Open-source Feast on top of S3 + Iceberg (offline) + Redis (online)
- Streaming transform in Flink for sub-second features; Spark for batch
- Per-feature definitions with TTL, owner, freshness SLA
- Point-in-time joins for training data generation
- Feature registry with ownership + lineage
- Drift + freshness + skew monitoring with alerts
- Cost dashboards per team

**Cost (rough):**
- Redis cluster (online, 10k QPS): ~$15k/mo
- S3 + Iceberg (offline, 1PB): ~$10k/mo
- Flink / Spark compute: ~$30k/mo
- Feast / Tecton license: ~$20k/mo (or 1 FTE for Feast)
- Monitoring / dashboards: ~$5k/mo
- **Total: ~$80k/mo for 500 models**

**Revisit if:**
- Online p95 > 50ms → cache hot entities, drop unused features
- Drift detected within hours → add streaming feature recompute
- New model onboarding > 1 week → improve feature discoverability
- Cost > $200k/mo → consolidate features, drop low-ROI features
- Online/offline skew detected → pause model, fix transform

---

## The "feature lifecycle" diagram

```
   ┌────────────────────────────────────────────────────────────┐
   │                                                            │
   │   design ──► build ──► test ──► register ──► serve ──► deprecate │
   │      │         │         │         │            │            │
   │      ▼         ▼         ▼         ▼            ▼            │
   │   owner     version    PIT      registry     monitoring    archive
   │   SLA       metadata   tests    discover    freshness      mark
   │                                                            │
   └────────────────────────────────────────────────────────────┘
```

A feature should never silently appear or disappear. Every state transition is logged, owned, auditable.

---

## What Comes Next

> Lesson 5 — **Fraud Detection** — real-time fraud with sub-second features, model serving, and a feedback loop for label delay.