# Lesson 2 — Feature Store Comparison

> **Type:** Article · Module 6 · Feature Stores & ML Data Infrastructure
> Feast vs Tecton vs Featureform vs the cloud-platform built-ins.

---

## The feature store landscape in 2026

```
   FEATURE STORES (2026)
   ─────────────────────
   Open-source             Managed (cloud-native)
   ───────────             ──────────────────────
   Feast                   Tecton
   Featureform             AWS SageMaker Feature Store
   Hopsworks               GCP Vertex AI Feature Store
                           Azure ML Feature Store
                           Databricks Feature Store
                           Snowflake Feature Store

   Cloud-native means: tightly coupled to that cloud's storage + serving,
                       less work to wire up, less portable.
```

Each has the same three jobs (definitions, offline store, online store) but differs in **how much glue you write**.

---

## Feast

The default open-source option. Python-first, plugs into your existing cloud.

| Aspect | Detail |
|---|---|
| Owner | Feast community (Linux Foundation) |
| Storage | Offline: Parquet on S3/GCS/ADLS, BigQuery, Snowflake, Redshift. Online: Redis, DynamoDB |
| Definitions | Python decorators (`@feature_view`) |
| Strengths | Free, portable, mature, integrates with everything |
| Weaknesses | You run it. Glue code for streaming ingest, registry UI is basic. |
| Best for | 10–100 models, you have a platform team |

```python
# Feast example
from feast import FeatureView, Field, FileSource
from feast.types import Float32, Int64

clicks_source = FileSource(path="s3://bucket/clicks.parquet")

user_clicks_fv = FeatureView(
    name="user_clicks_30d",
    entities=[user_entity],
    schema=[Field(name="clicks", dtype=Int64)],
    source=clicks_source,
    ttl=timedelta(days=30),
    online=True,
)
```

---

## Tecton

The managed, enterprise-grade feature store.

| Aspect | Detail |
|---|---|
| Owner | Tecton (founded by the Uber Michelangelo team) |
| Storage | Offline: managed Iceberg. Online: managed DynamoDB / Redis |
| Definitions | YAML / Python (declarative) |
| Strengths | Best-in-class feature engineering (time-window aggs, embeddings), SLA, governance, registry UI |
| Weaknesses | $$$ (commercial), vendor lock-in, requires Tecton deployment |
| Best for | 100+ models, regulated, online + offline, large ML platform |

```python
# Tecton example (declarative)
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

---

## Featureform

The "feature store as a virtual layer" approach. Doesn't own storage.

| Aspect | Detail |
|---|---|
| Owner | Featureform (open-core) |
| Storage | Reuses your warehouse (Snowflake, BigQuery, Databricks) and online DB (Redis, DynamoDB) |
| Definitions | Python / YAML |
| Strengths | Lightweight, lives on top of your warehouse, less infra |
| Weaknesses | Less mature streaming, smaller ecosystem |
| Best for | You already have a warehouse, want feature-store semantics without a new system |

---

## Hopsworks

Open-source, ML-platform-focused (not just feature store).

| Aspect | Detail |
|---|---|
| Owner | Hopsworks |
| Storage | HopsFS (Parquet) + RonDB (online) |
| Strengths | One platform for features + model registry + notebooks |
| Weaknesses | Heavy to operate, smaller ecosystem |
| Best for | Self-contained ML platform, on-prem or hybrid |

---

## Cloud-platform built-ins

### AWS SageMaker Feature Store

| Aspect | Detail |
|---|---|
| Storage | Offline: S3 + Parquet. Online: low-latency in-memory store |
| Strengths | Tight SageMaker integration, IAM, managed |
| Weaknesses | AWS-only, less flexible than Feast |
| Best for | AWS shop, heavy SageMaker user |

### GCP Vertex AI Feature Store

| Aspect | Detail |
|---|---|
| Storage | Offline: BigQuery. Online: Vertex AI online store |
| Strengths | BigQuery-native point-in-time joins, managed |
| Weaknesses | GCP-only |
| Best for | GCP shop, BigQuery-centric |

### Azure ML Feature Store

| Aspect | Detail |
|---|---|
| Storage | Offline: ADLS + Delta. Online: Azure Cache for Redis |
| Strengths | Azure-integrated, Synapse / Fabric compatible |
| Weaknesses | Azure-only, less mature than GCP/AWS |
| Best for | Azure shop, Synapse / Fabric stacks |

### Databricks Feature Store

| Aspect | Detail |
|---|---|
| Storage | Offline: Delta Lake. Online: online tables (sync from Delta) |
| Strengths | Delta-native, tight MLflow / Spark integration |
| Weaknesses | Databricks-only, online store less mature than dedicated systems |
| Best for | Databricks shop, Spark-heavy |

### Snowflake Feature Store (Cortex)

| Aspect | Detail |
|---|---|
| Storage | Offline: Snowflake tables. Online: Snowpark + dynamic tables |
| Strengths | Snowflake-native, no data movement |
| Weaknesses | Snowflake-only, online is newer |
| Best for | Snowflake-heavy data team, want zero data movement |

---

## Decision framework

```
   ┌──────────────────────────────────────────────────┐
   │  "Do we need an online store at all?"             │
   │                                                  │
   │   NO  ──► don't adopt a feature store.           │
   │           Use a DAG that writes to a table.       │
   │                                                  │
   │   YES ──► ┌─────────────────────────────────┐    │
   │           │  Are you on a single cloud?      │    │
   │           │   YES ─► use that cloud's        │    │
   │           │          built-in (least glue).   │    │
   │           │   NO  ─► Feast (open-source)     │    │
   │           │          or Tecton (managed).     │    │
   │           └─────────────────────────────────┘    │
   │                                                  │
   │   Regulated, 100+ models, governance ─► Tecton.   │
   │   Tight budget, single cloud       ─► built-in.   │
   │   Multi-cloud, ML platform team    ─► Feast.      │
   │   On top of warehouse, lightweight  ─► Featureform│
   └──────────────────────────────────────────────────┘
```

---

## Cost comparison (rough, 2026)

| Option | Cost driver | 100M features, 50ms p95 online |
|---|---|---|
| Feast (self-hosted) | Engineer time + Redis/Dynamo + S3 | ~$1k–3k/mo infra + 0.5 FTE |
| Tecton (managed) | Per-feature, per-request | ~$10k–30k/mo |
| AWS Feature Store | Online reads + storage | ~$2k–5k/mo |
| GCP Vertex Feature Store | Online node-hours + storage | ~$2k–5k/mo |
| Databricks Feature Store | DBU + online table compute | ~$3k–8k/mo |
| Snowflake Cortex | Warehouse + online compute | ~$2k–6k/mo |

Managed options are 3–10× more expensive than self-hosted Feast, but you save 1–2 FTE.

---

## What "good" looks like in production

- **Time-to-feature for a new model:** < 1 day (registry + reuse)
- **Online p95 latency:** < 50ms
- **Point-in-time join correctness:** validated against leakage tests
- **Freshness:** SLA per feature, monitored, alerted
- **Discoverability:** every feature has owner + description + examples

If your feature store doesn't hit these, you built a data warehouse with extra steps.

---

## What Comes Next

> Lesson 3 — **Training Data Versioning** — version training datasets, tie them to model versions and configs, reproduce a run six months later.