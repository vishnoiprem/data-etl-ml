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

## Worked Example — a fraud-detection feature store, end-to-end

> **Goal:** Build a feature store for a real-time fraud-detection model. Three features, two freshness tiers, online + offline parity. Single definition used at both training and serving.

### The three features

```
   user_velocity_5m          sub-second freshness, used at serving
   user_amount_sum_1h        sub-second freshness, used at serving
   user_chargeback_rate_90d  daily freshness, used at training (not serving)
```

The first two need **online** because the model runs in <50ms at request time. The third is **offline-only** because it's a slowly-changing attribute that doesn't need live recompute.

### Step 1 — Define the features (one source of truth)

```python
# features/repo.py — the registry

from feast import (
    Entity, FeatureView, Field, FileSource, RedisSource,
    PushSource,
)
from feast.types import Float32, Int64
from datetime import timedelta

user_entity = Entity(
    name="user_id",
    description="Unique user identifier from the auth system",
)


# Feature 1: streaming, online + offline
user_velocity_5m_source = FileSource(
    path="s3://lake/fraud/events/",
    timestamp_field="event_ts",
    created_timestamp_column="ingest_ts",
)

user_velocity_5m = FeatureView(
    name="user_velocity_5m",
    entities=[user_entity],
    ttl=timedelta(minutes=15),
    schema=[
        Field(name="txn_count_5m", dtype=Int64),
        Field(name="txn_sum_amount_5m", dtype=Float32),
    ],
    source=user_velocity_5m_source,
    online=True,
    owner="fraud-platform",
    freshness_sla="5s",
    description="Count and total $ of transactions per user in last 5 min",
)


# Feature 2: nightly batch, offline only
user_chargeback_rate_90d_source = FileSource(
    path="s3://lake/fraud/chargebacks/",
    timestamp_field="as_of_ts",
)

user_chargeback_rate_90d = FeatureView(
    name="user_chargeback_rate_90d",
    entities=[user_entity],
    ttl=timedelta(days=120),
    schema=[Field(name="chargeback_rate_90d", dtype=Float32)],
    source=user_chargeback_rate_90d_source,
    online=False,             # offline-only
    owner="fraud-platform",
    freshness_sla="24h",
    description="Fraction of user's transactions over the last 90 days that resulted in a chargeback",
)
```

### Step 2 — Streaming transform (Flink)

```java
// flink-job/src/main/java/fraud/UserVelocityTransform.java
// Sub-second feature engineering. Reads from Kafka, writes to
// Parquet (offline) AND Redis (online). Idempotent by (user_id, event_ts).

public class UserVelocityTransform extends KeyedProcessFunction<String, Event, FeatureUpdate> {

    private transient ValueState<VelocityState> state;

    @Override
    public void open(Configuration parameters) {
        ValueStateDescriptor<VelocityState> descriptor =
            new ValueStateDescriptor<>("velocity", TypeInformation.of(VelocityState.class));
        state = getRuntimeContext().getState(descriptor);
    }

    @Override
    public void processElement(Event event, Context ctx, Collector<FeatureUpdate> out) throws Exception {
        VelocityState s = state.value();
        if (s == null) s = new VelocityState();

        long now = ctx.timestamp();
        s.addEvent(event, now);            // updates count and sum, evicts events > 5 min old

        state.update(s);

        // Emit to both stores
        FeatureUpdate update = new FeatureUpdate(
            event.userId,
            now,
            s.count,
            s.sumAmount
        );
        out.collect(update);
    }
}
```

The transform runs 24/7, processing every transaction event. Writes idempotently keyed on `(user_id, event_ts)`.

### Step 3 — Online/offline sync

```
   ┌──────────────┐         ┌─────────────────┐
   │  Flink job   │────────►│  S3 (Parquet)   │  offline, source of truth
   │  (streaming) │         └─────────────────┘
   │              │
   │              │         ┌─────────────────┐
   │              │────────►│  Redis (online) │  < 10ms reads
   └──────────────┘         └─────────────────┘
                                    ▲
                                    │  CDC sync catches any misses
                                    │  (every 1 min, idempotent)
                                    │
                             ┌─────────────────┐
                             │  Debezium CDC   │
                             └─────────────────┘
```

If Redis goes down or a write fails, the CDC consumer reads from the offline Parquet and rebuilds Redis. **Offline is the source of truth; online is always a cache of recent values.**

### Step 4 — Training data generation (point-in-time correct)

```python
# training/generate_training_set.py
# Joins labels (chargebacks confirmed T+45d) with features as-of the original txn time.

from feast import FeatureStore

store = FeatureStore(repo_path="features/")

training_df = store.get_historical_features(
    entity_df=f"""
        SELECT
          user_id,
          original_txn_ts AS event_ts,        -- the timestamp we want features as-of
          label_fraud AS label
        FROM fraud.labels
        WHERE original_txn_ts BETWEEN '2025-01-01' AND '2025-12-31'
    """,
    features=[
        "user_velocity_5m:txn_count_5m",
        "user_velocity_5m:txn_sum_amount_5m",
        "user_chargeback_rate_90d:chargeback_rate_90d",
    ],
).to_df()

# The ASOF JOIN happens inside Feast. Each row's features are joined
# as-of the row's event_ts. NO future leakage.
print(training_df.head())
#        user_id   event_ts   label  txn_count_5m  txn_sum_amount_5m  chargeback_rate_90d
# 0      u_42      2025-03-15 10:23  1        3              142.50               0.012
# 1      u_42      2025-03-15 10:31  0        2               87.00               0.012
# 2      u_43      2025-03-15 11:02  1        8              950.25               0.087
# 3      u_43      2025-03-15 11:15  0        5              410.00               0.087
```

The critical property: **`chargeback_rate_90d` is the rate as-of the txn time, not as-of today.** Without point-in-time correctness, your training data has look-ahead bias and the model fails in production.

### Step 5 — Online serving

```python
# serving/fraud_inference.py
# Latency budget: p99 < 100ms total.

from feast import FeatureStore

store = FeatureStore(repo_path="features/")

def score_transaction(txn):
    # 1. Fetch online features (target: 5-15ms)
    features = store.get_online_features(
        features=[
            "user_velocity_5m:txn_count_5m",
            "user_velocity_5m:txn_sum_amount_5m",
        ],
        entity_rows=[{"user_id": txn.user_id}],
    ).to_dict()

    # 2. Model inference (target: 20-30ms)
    feature_vector = [
        features["txn_count_5m"][0],
        features["txn_sum_amount_5m"][0],
    ]
    prob_fraud = model.predict_proba([feature_vector])[0]

    # 3. Decision
    if prob_fraud >= 0.95:
        return "DECLINE"
    elif prob_fraud >= 0.50:
        return "REVIEW"
    else:
        return "APPROVE"
```

Note: `chargeback_rate_90d` is NOT in the online feature fetch. It's offline-only because it doesn't change in real-time. The model that trains on it can include it; the model that serves doesn't need it.

### Step 6 — Drift monitoring

```python
# monitoring/feature_drift.py
# Run hourly. Alert if PSI > 0.25 for any feature.

import pandas as pd
from scipy.stats import ks_2samp

def psi(expected, actual, bins=10):
    """Population Stability Index. PSI > 0.25 = significant drift."""
    expected_percents = np.histogram(expected, bins=bins)[0] / len(expected)
    actual_percents = np.histogram(actual, bins=bins)[0] / len(actual)
    return np.sum(
        (actual_percents - expected_percents) * np.log(actual_percents / expected_percents)
    )

# Get baseline (training distribution) and current (last 24h)
baseline = store.get_historical_features(...).to_df()
current = get_last_24h_from_redis(...)

for feature in ["txn_count_5m", "txn_sum_amount_5m", "chargeback_rate_90d"]:
    psi_val = psi(baseline[feature], current[feature])
    if psi_val > 0.25:
        alert(f"Feature {feature} PSI = {psi_val:.3f}, drift detected")
        page_oncall("data-platform")
```

### Cost roll-up (production scale, 50M users, 100M txns/day)

```
   Redis (online, 50M user keys × 5 features × ~200 bytes):    ~$15k/mo
   S3 + Iceberg (offline, 100M events/day × 90d retention):     ~$10k/mo
   Flink cluster (streaming transform, 24/7):                   ~$30k/mo
   Feast control plane (self-hosted) OR Tecton licence:         ~$20k/mo (Feast)
                                                                  or $20k+/mo (Tecton)
   Monitoring + dashboards:                                      ~$3k/mo
   ────────────────────────────────────────────────────────
   Total: ~$78k/mo for 3 features, 1 model, 100M txns/day

   Per-query online inference cost: < 10ms Redis read = < $0.00001
   Per-training-set generation: ~$5 (one-time, 12mo of data)
```

### What this example demonstrates

- **One definition, two stores.** The FeatureView is the contract.
- **Streaming transform** for sub-second freshness; **batch transform** for daily.
- **Point-in-time joins** prevent look-ahead bias in training data.
- **Online inference is read-only** — no compute at request time, just a Redis fetch.
- **Drift monitoring** catches upstream pipeline changes before they silently degrade the model.
- **Cost roll-up** is real, defensible, and shows the dominant cost drivers (Redis + Flink).

This is the pattern every production ML team eventually lands on. **The feature store is the moat, not the model.** Three different teams could share this `user_velocity_5m` definition; the same definition, the same numbers, the same freshness SLA.

---

## What Comes Next

> Lesson 2 — **Feature Store Comparison** — Feast, Tecton, Featureform, AWS / GCP / Databricks / Snowflake built-ins. The decision framework.