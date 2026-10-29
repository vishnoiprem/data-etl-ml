# 8.1 — Case Study: Requirements & Architecture

> **Section 8 · Case Study · Lecture 8.1 · 4:30**

## 🎯 What you will learn

- Framing a realistic end-to-end BigQuery project
- Requirements, acceptance criteria, and the non-functional constraints
- The architecture: GCP services, data flow, and ownership
- Choosing the right tools for each stage of the pipeline

---

## 🧠 Concept

This section builds one complete project from start to finish. It touches every major topic in
the course:

- **Apache Beam** — batch and streaming ingestion
- **Apache Airflow (Cloud Composer)** — orchestration
- **BigQuery** — storage, transformation, serving
- **Looker Studio (Data Studio)** — visualization
- **Pub/Sub** — the streaming backbone

---

## 🧠 The business problem

> **RetailMart** wants a single source of truth for online + in-store sales, with a dashboard
> the executive team can trust, refreshed daily — and near-real-time for the live operations
> view.

### Requirements

| # | Requirement | Priority |
|---|-------------|----------|
| R1 | Ingest clickstream and order events from the web/mobile app | Must |
| R2 | Ingest daily order files from the legacy POS system | Must |
| R3 | Clean and conform orders from all sources into one model | Must |
| R4 | Serve an executive dashboard with revenue, orders, and AOV | Must |
| R5 | Serve a live operations view with < 5 minute latency | Should |
| R6 | Preserve raw data for 2 years, curated for 5 years | Must |
| R7 | Support backfill of any historical day without re-running the pipeline | Must |
| R8 | Cost per day under a fixed budget | Must |

### Non-functional constraints

- **Region:** `europe-west1` (EU data residency)
- **Freshness:** daily by 06:00 UTC; live within 5 minutes
- **RPO / RTO:** RPO 15 minutes (stream), RTO 2 hours (batch)
- **Quality:** 99.5% of daily orders reconciled against the POS control total
- **Security:** PII in raw and curated datasets is masked; analysts see only masked views

---

## 🧠 Data sources

| Source | Type | Volume/day | Arrival | Format |
|--------|------|-------------|---------|--------|
| Web/mobile clickstream | Stream | ~400M events | Continuous | NDJSON over HTTPS |
| Order events (app) | Stream | ~2M events | Continuous | Pub/Sub |
| Legacy POS extract | Batch file | ~1.2M rows | 01:00 UTC | CSV in GCS |
| Product master | Batch file | ~80k rows | Daily 02:00 UTC | CSV in GCS |
| Currency rates | Batch | Daily | Daily 03:00 UTC | CSV in GCS |

---

## 🧠 Target architecture

```
                          ┌─────────────────────────────┐
  Web/Mobile SDK ────────▶│  Pub/Sub topics            │
                          │  • events.raw              │
                          │  • orders.events           │
                          └──────────┬──────────────────┘
                                     │
                          ┌──────────▼──────────────────┐
                          │  Dataflow / Beam pipelines │
                          │  • stream → raw.events     │
                          │  • stream → raw.orders     │
                          └──────────┬──────────────────┘
                                     │
  POS CSV ──▶ GCS landing ──▶ Beam batch ──▶ raw.pos_orders
  Product ──▶ GCS landing ──▶ Beam batch ──▶ raw.products
  FX      ──▶ GCS landing ──▶ Beam batch ──▶ raw.fx_rates
                                     │
               ┌─────────────────────▼─────────────────────┐
               │  BigQuery                                │
               │  raw.*          (immutable, 2y retention) │
               │  staging.*     (30d, partitioned daily)   │
               │  curated.*     (5y, conformed, clustered) │
               │  mart.*        (BI serving, MVs)          │
               └─────────────────────┬─────────────────────┘
                                     │
               ┌─────────────────────▼─────────────────────┐
               │  Cloud Composer (Airflow)                 │
               │  • daily_extract (05:00 UTC)              │
               │  • daily_transform (05:30 UTC)            │
               │  • daily_marts (05:45 UTC)                │
               │  • backfill_trigger (on demand)           │
               └─────────────────────┬─────────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  Looker Studio      │
                          │  • Executive view   │
                          │  • Live ops view    │
                          └─────────────────────┘
```

---

## 🧠 Storage layout

| Dataset | Layer | Partitioning | Clustering | Retention |
|---------|-------|--------------|------------|-----------|
| `raw` | Landing | Ingestion-time (`_PARTITIONDATE`) | none | 730 days |
| `staging` | Cleaned | `event_date` (DATE) | `source_system` | 30 days |
| `curated` | Conformed | `order_date` (DATE) | `customer_id`, `channel` | 1825 days |
| `mart` | Serving | `order_date` (DATE) | `region` | 1095 days |
| `sandbox` | Experiments | none | none | 7 days |

💡 **Raw is ingestion-time partitioned** because raw files do not reliably carry a trustworthy
event date. Curated layers use the business date so analysts can filter naturally.

---

## 🧠 The conformed order model

Every source converges on one table: `curated.orders`.

```sql
CREATE OR REPLACE TABLE `retailmart.curated.orders` (
  order_id        STRING    NOT NULL,
  customer_id     STRING    NOT NULL,
  order_ts        TIMESTAMP NOT NULL,
  order_date      DATE      NOT NULL,
  channel         STRING    NOT NULL,   -- web | mobile | store
  region          STRING    NOT NULL,
  currency        STRING    NOT NULL,
  amount_local    NUMERIC   NOT NULL,
  amount_eur      NUMERIC   NOT NULL,   -- converted at the daily FX rate
  status          STRING    NOT NULL,
  line_count      INTEGER   NOT NULL,
  source_system   STRING    NOT NULL,   -- app | pos
  ingested_at     TIMESTAMP NOT NULL
)
PARTITION BY order_date
CLUSTER BY customer_id, channel
OPTIONS(
  description = "Conformed orders from all sources, EUR-normalised",
  require_partition_filter = TRUE,
  partition_expiration_days = 1825,
  labels = [("tier", "curated"), ("owner", "data-eng"), ("domain", "sales")]
);
```

---

## 🧠 Orchestration design

| DAG | Schedule | What it does | Depends on |
|-----|----------|--------------|------------|
| `stream_ingest` | Continuous (Dataflow) | Pub/Sub → `raw.*` | — |
| `daily_pos_extract` | `0 1 * * *` | Pull POS files → GCS → `raw.pos_orders` | — |
| `daily_conform` | `30 2 * * *` | `raw.*` → `staging.*` | `daily_pos_extract` |
| `daily_curate` | `0 3 * * *` | `staging.*` → `curated.orders` | `daily_conform` |
| `daily_marts` | `30 3 * * *` | `curated.orders` → `mart.*` | `daily_curate` |
| `refresh_mvs` | `45 3 * * *` | Refresh materialized views | `daily_marts` |
| `dq_checks` | `1 4 * * *` | Reconcile against POS control totals | `daily_marts` |
| `publish_marts` | `2 4 * * *` | Expose marts to Looker Studio | `dq_checks` |

💡 **The quality gate sits between the marts and publication.** If reconciliation fails, the
marts are not published and an alert fires. The executive dashboard must never show numbers
that did not reconcile.

---

## 🧠 Tool selection rationale

| Stage | Tool | Why not the alternative |
|-------|------|------------------------|
| Streaming ingest | **Dataflow (Beam)** | Cloud Functions cannot do stateful windowing; Dataflow can |
| Batch ingest | **Dataflow (Beam)** | `bq load` works, but Beam gives schema mapping and dedup in one place |
| Orchestration | **Composer (Airflow)** | Cloud Scheduler cannot express dependencies; GitHub Actions lacks managed state and backfill |
| Transformation | **BigQuery SQL** | Python/Spark would be more expensive and slower for SQL-shaped logic |
| Serving layer | **BigQuery MVs** | Serving from `curated` directly costs 10–50× more per query |
| Visualization | **Looker Studio** | Free, BigQuery-native, supports data freshness and push filters |

---

## 🧠 Cost model (target)

| Component | Daily cost | Notes |
|-----------|-----------|-------|
| BigQuery storage (raw + curated + marts) | ~$4 | ~1.8 TB total |
| BigQuery queries (batch + Looker Studio) | ~$9 | 4 MVs + ~30 ad-hoc |
| Dataflow streaming | ~$12 | n1 workers, continuous |
| Dataflow batch | ~$2 | 2 hr on n1 workers |
| Composer | ~$3 | 0.3 environments |
| Pub/Sub | ~$1 | ~400M messages/day |
| **Total** | **~$31/day (~$930/month)** | Budget: $1,200/month |

---

## 🛠️ Hands-On: sketch the model

```sql
-- The control total the reconciliation checks against
SELECT
  order_date,
  COUNT(*) AS pos_order_count,
  SUM(amount_local) AS pos_order_total
FROM `retailmart.raw.pos_orders`
WHERE order_date = @target_date
GROUP BY order_date;

-- The curated equivalent
SELECT
  order_date,
  COUNT(*) AS curated_order_count,
  SUM(amount_eur) AS curated_order_total
FROM `retailmart.curated.orders`
WHERE order_date = @target_date
  AND source_system = 'pos'
GROUP BY order_date;
```

```python
# The reconciliation, as it will run in the DQ DAG
def reconcile(target_date: str) -> bool:
    control = client.query(
        """
        SELECT COUNT(*) AS n, SUM(amount_local) AS total
        FROM `retailmart.raw.pos_orders`
        WHERE order_date = @d
        """,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("d", "DATE", target_date)]
        ),
    ).result().one()

    curated = client.query(
        """
        SELECT COUNT(*) AS n, SUM(amount_eur) AS total
        FROM `retailmart.curated.orders`
        WHERE order_date = @d AND source_system = 'pos'
        """,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("d", "DATE", target_date)]
        ),
    ).result().one()

    count_ok = control.n == curated.n
    total_ok = abs(float(control.total) - float(curated.total)) < 0.01
    return count_ok and total_ok
```

---

## 💡 Production Notes

- **Write the reconciliation before the pipeline.** It defines what "correct" means, and every
  transform is judged against it.
- **Partition raw by ingestion time, curated by business date.** Raw data cannot be trusted to
  carry a valid event date.
- **Curate to one canonical currency.** Without this, every downstream metric is a currency
  conversion bug waiting to happen.
- **Never publish unreconciled numbers.** The gate between `mart.*` and Looker Studio is the
  single most important control in the architecture.
- **Design for backfill from day one.** Every task must accept a `target_date` parameter, not
  `CURRENT_DATE()`. This is the difference between a backfill and a rewrite.
- **MVs for the dashboard, not for everything.** MVs have a single-base-table constraint and
  cost storage; use them for the queries you know run constantly.

---

## 🔑 Key Takeaways

- Frame the project with numbered requirements, explicit non-functional constraints, and a
  cost budget.
- **Raw (ingestion-time partitioned) → staging → curated (business-date partitioned) → mart.**
- Tool choice: Dataflow for ingest, Composer for orchestration, BigQuery SQL for transformation,
  MVs for serving, Looker Studio for consumption.
- The **quality gate before publication** is non-negotiable.
- Every task takes a `target_date` parameter — that is what makes backfills possible.

---

## 📚 Practice Exercises

1. **Requirement breakdown.** Expand this brief into 20 numbered requirements with acceptance
   criteria. Include data quality, security, cost, and operability.

2. **Architecture diagram.** Produce a diagram with data volumes, latency, and cost annotations at
   every hop. Use Mermaid or a text diagram.

3. **Cost model.** Rebuild the cost table from current BigQuery and Dataflow prices. Show the
   sensitivity to event volume and retention.

4. **Partitioning strategy.** Justify every partition/cluster choice in the storage layout table.
   Write the alternative you rejected and why.

5. **Failure modes.** List ten ways this pipeline can fail (late POS file, duplicate events, FX
   rate missing, bad schema, OOM, API quota, bad DAG, dashboard SLA breach, backfill
   collision, schema drift). For each: detection signal, impact, and remediation.

---

## 📖 Further Reading

- BigQuery architecture patterns — https://cloud.google.com/bigquery/docs/best-practices
- Dataflow pricing — https://cloud.google.com/dataflow/pricing
- Cloud Composer overview — https://cloud.google.com/composer/docs/composer-2/overview
