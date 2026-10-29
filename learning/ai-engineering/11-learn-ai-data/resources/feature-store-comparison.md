# Feature Store Comparison

> Feast vs Tecton vs Featureform vs cloud-platform built-ins vs in-house. Decision framework for 2026.

---

## TL;DR decision framework

```
   ┌──────────────────────────────────────────────────────────┐
   │  Batch-only, < 10 models, < 100 features                 │
   │   ──► You don't need a feature store. Use a DAG that      │
   │       writes features to a table.                         │
   │                                                          │
   │  AWS SageMaker shop, 10-100 models                        │
   │   ──► SageMaker Feature Store.                            │
   │                                                          │
   │  GCP / BigQuery shop                                      │
   │   ──► Vertex AI Feature Store.                            │
   │                                                          │
   │  Azure / Synapse / Fabric shop                            │
   │   ──► Azure ML Feature Store.                             │
   │                                                          │
   │  Databricks / Delta Lake shop                             │
   │   ──► Databricks Feature Store.                           │
   │                                                          │
   │  Snowflake shop                                           │
   │   ──► Snowflake Feature Store (Cortex-era).               │
   │                                                          │
   │  Multi-cloud / portable, want OSS, 10-100+ models        │
   │   ──► Feast (self-host) or Tecton (managed).              │
   │                                                          │
   │  On top of warehouse, want minimum infra                  │
   │   ──► Featureform.                                        │
   └──────────────────────────────────────────────────────────┘
```

---

## Feature comparison

| Feature | Feast | Tecton | Featureform | SageMaker | Vertex | Azure ML | Databricks | Snowflake |
|---|---|---|---|---|---|---|---|---|
| **License** | Apache 2.0 | Closed | Open-core | Closed | Closed | Closed | Closed | Closed |
| **Managed** | via 3rd parties | Yes (Tecton Cloud) | via 3rd parties | Yes | Yes | Yes | Yes | Yes |
| **Self-host** | Yes | No (managed only) | Yes | No | No | No | No | No |
| **Offline store** | Parquet, BigQuery, Snowflake, Redshift | Managed Iceberg | Reuses warehouse | S3 + Parquet | BigQuery / GCS | ADLS + Delta | Delta Lake | Snowflake |
| **Online store** | Redis, DynamoDB | Managed (Dynamo / Redis) | Redis, DynamoDB | Managed | Managed | Azure Cache for Redis | Online tables | Snowflake online tables |
| **Point-in-time joins** | Native | Native (best-in-class) | Manual | Manual | Manual | Manual | Native | Manual |
| **Feature registry UI** | Basic | Strong | Basic | Strong | Strong | Moderate | Strong | Moderate |
| **Streaming transform** | Custom (Spark / Flink) | Native (declarative) | Custom | Native | Native | Native | Native (DLT) | Native (Streams) |
| **Embedding features** | Code in transform | Native | Code in transform | Native | Native | Native | Native | Native |
| **Cost (100M features)** | $1-3k/mo + 0.5 FTE | $10-30k/mo | $1-3k/mo | $2-5k/mo | $2-5k/mo | $2-5k/mo | $3-8k/mo | $2-6k/mo |

---

## Decision criteria

### 1. Are you on a single cloud?

If yes, **use that cloud's feature store**. It's the path of least glue.

| Cloud | Feature Store |
|---|---|
| AWS | SageMaker Feature Store |
| GCP | Vertex AI Feature Store |
| Azure | Azure ML Feature Store |
| Databricks | Databricks Feature Store |
| Snowflake | Snowflake Feature Store (Cortex) |

### 2. Multi-cloud or no cloud?

Use **Feast** (OSS) or **Tecton** (managed).

```
   FEAST                    TECTON
   ──────                   ──────
   Apache 2.0               Managed ($$$)
   You run it               They run it
   Pluggable offline/online Same, but managed
   Code in Python           Declarative YAML
   0.5 FTE ops              0 FTE ops
   Strong if platform team  Strong if 100+ models
   Free licence             $10-30k/mo
```

### 3. Is your data already in a warehouse?

If yes, look at **Featureform** or use the warehouse-native feature store (Snowflake / BigQuery).

Featureform shines when:
- You have ≤ 50 models
- You want feature-store semantics without a new system
- You don't have a platform team to run Feast

---

## Cost comparison (rough, 2026)

For 100M features, online p95 < 50ms, multi-tenant:

| Option | Monthly cost |
|---|---|
| **Feast (self-hosted)** | $1-3k/mo infra + 0.5 FTE engineer (~10k/mo fully loaded) |
| **Tecton (managed)** | $10-30k/mo |
| **SageMaker Feature Store** | $2-5k/mo |
| **Vertex AI Feature Store** | $2-5k/mo |
| **Azure ML Feature Store** | $2-5k/mo |
| **Databricks Feature Store** | $3-8k/mo + DBU |
| **Snowflake Feature Store** | $2-6k/mo + warehouse |

Managed options cost 3–10× more than self-hosted Feast, but you save 1–2 FTE.

---

## The "what does a feature definition look like" comparison

### Feast

```python
from feast import FeatureView, Field, FileSource
from feast.types import Float32
from datetime import timedelta

clicks_source = FileSource(
    path="s3://bucket/clicks.parquet",
    timestamp_field="event_ts",
)

user_clicks_fv = FeatureView(
    name="user_clicks_30d",
    entities=[user_entity],
    schema=[Field(name="clicks", dtype=Int64)],
    source=clicks_source,
    ttl=timedelta(days=30),
    online=True,
)
```

### Tecton

```python
from tecton import FeatureView, batch_feature_view

@batch_feature_view(
    sources=[events_source],
    entities=[user_entity],
    mode="spark_sql",
    batch_schedule=timedelta(minutes=5),
)
def user_clicks_30d(events):
    return f"""
        SELECT user_id, event_ts, COUNT(*) as clicks
        FROM {events}
        WHERE event_type = 'click'
          AND event_ts >= {events} - INTERVAL 30 DAY
        GROUP BY user_id, event_ts
    """
```

### Snowflake / Cortex-style

```sql
CREATE OR REPLACE TABLE ml.user_clicks_30d AS
SELECT
  user_id,
  DATE_TRUNC('hour', event_ts) AS event_ts,
  COUNT(*) AS clicks
FROM events
WHERE event_type = 'click'
  AND event_ts >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY 1, 2;
```

(Snowflake's offline = the warehouse table; online sync is via Dynamic Tables or Snowpark.)

---

## The "online serving latency" comparison

All claim sub-50ms. Reality varies by config:

| Option | Online p50 | Online p95 |
|---|---|---|
| **Redis cluster (Feast)** | 1-3ms | 5-10ms |
| **DynamoDB (Feast / SageMaker)** | 5-10ms | 10-20ms |
| **Tecton online (managed)** | 5-10ms | 10-30ms |
| **Vertex AI online** | 5-15ms | 15-30ms |
| **Snowflake online** | 20-50ms | 50-200ms (warehouse-bound) |

If you're consistently at p95 < 30ms target, **Redis or DynamoDB-backed** wins. If 50–200ms is acceptable, cloud native is fine.

---

## The "streaming feature transform" decision

| Option | Streaming support |
|---|---|
| Feast | Bring-your-own (Flink / Spark Streaming) |
| Tecton | Native (declarative time-window aggs) |
| SageMaker Feature Store | Native (Feature Processor) |
| Vertex AI Feature Store | Native (Vertex Pipelines + Dataflow) |
| Databricks Feature Store | Native (Structured Streaming) |
| Snowflake Feature Store | Native (Streams + Tasks) |

For complex time-window aggregations (last 30 days, sliding windows), **Tecton** has the cleanest API. For "I'll write the Flink job myself," Feast (or anything) works.

---

## Migration path

```
   NO FEATURE STORE ─────────► Feast (self-host)
        (ad-hoc)              (start OSS, low cost)

   Feast ─────────► Tecton / Cloud-native
        (when team / model count grows OR you want managed)

   Cloud-native ─────────► Feast / Tecton (rare reverse)
        (rarely happens; lock-in is the cost)
```

---

## Decision flowchart

```
   ┌──────────────────────────────────────────────────┐
   │ START                                             │
   │                                                  │
   │ Are you on a single cloud?                       │
   │   YES ─► use that cloud's feature store           │
   │   NO  ─► Feast or Tecton                          │
   │                                                  │
   │ Do you have < 10 models, batch-only?             │
   │   YES ─► skip a feature store. Use a DAG.        │
   │   NO  ─► build / buy a feature store              │
   │                                                  │
   │ Do you have a platform team (1+ FTE)?            │
   │   YES ─► Feast (save $$)                         │
   │   NO  ─► managed (Tecton / cloud-native)         │
   │                                                  │
   │ Are you tightly integrated with a warehouse?     │
   │   YES ─► Featureform or warehouse-native         │
   │                                                  │
   │ END                                               │
   └──────────────────────────────────────────────────┘
```

---

## Anti-patterns

1. **Building a "feature store" as a side project.** It's infrastructure. Treat it like infrastructure.
2. **Skipping the registry.** Features that aren't discoverable get reinvented. Every team rolls their own `_v2`.
3. **Mixing online and offline logic.** Single biggest source of skew. One definition, two stores.
4. **No freshness SLA.** If nobody owns freshness, every consumer rolls their own retry.
5. **Backfilling without a plan.** Re-running a feature over 3 years of history at 02:00 UTC will cause an outage somewhere.
6. **Online store without offline parity testing.** If you can't prove online == offline for entity X at time T, you have skew somewhere.
7. **Treating the feature store as the source of truth.** Source data is the truth. Feature store is derived. Always.
