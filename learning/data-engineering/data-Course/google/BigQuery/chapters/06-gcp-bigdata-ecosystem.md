# 1.6 — Big Data Ecosystem in GCP

> **Section 1 · Introduction to Google Cloud Platform · Lecture 1.6 · 4:47**

## 🎯 What you will learn

- How the GCP data services assemble into real architectures
- Three reference architectures you will actually build
- The design patterns that recur across every production GCP data platform

---

## 🧠 Concept

The previous lessons covered the individual services. This lesson is about how they compose — the
**patterns** that show up repeatedly in production GCP data platforms regardless of industry.

### Pattern 1 — The Lakehouse (batch)

```
Source DBs ──▶ Dataflow Batch ──▶ Cloud Storage (raw → curated)
                                          │
                              external table / multi-statement
                                          ▼
                                    BigQuery (serving)
                                          │
                                          ▼
                                   Looker Studio / API
```

**Where you see it:** every mid-size company with a nightly ETL and BI dashboards.

**Design rules:**
- Raw data lands in GCS as immutable, partitioned objects (date-partitioned, Parquet)
- BigQuery reads raw via **external tables** (cheap, no load cost) or loads to **managed tables**
  (fast queries, storage cost)
- Curated layers are BigQuery tables partitioned by date and clustered by filter columns
- BI tools connect to BigQuery views, never to raw tables

💡 **Raw zone discipline matters more than any tuning.** Once raw data is mutated, you cannot
replay it. Write raw data once, never update it, and partition it by ingestion date.

### Pattern 2 — Streaming Analytics (real-time)

```
Producers ──▶ Pub/Sub ──▶ Dataflow Streaming ──▶ BigQuery (buffered writes)
                              │                       │
                              │                       ▼
                              │                  Bigtable (hot state)
                              │                       │
                              └───────────────────────┴──▶ Dashboard
```

**Where you see it:** ad-tech, IoT, fintech risk, live dashboards.

**Design rules:**
- Pub/Sub decouples producers from the pipeline — you can replay from the subscription
- Dataflow handles windowing, deduplication, and state
- **BigQuery is not a real-time serving store.** For sub-second reads, use **Bigtable** or
  **Memorystore**. BigQuery is the *sink* for aggregated state and the *durable archive* for raw
  events.

### Pattern 3 — Unified Batch + Streaming (the modern default)

```
                    ┌───────────────────────────┐
   Batch sources ───▶                           │
                    │   Cloud Storage (raw)      │
   Stream sources ─▶│   + BigQuery (gold)       │──▶ BI / ML / API
                    └───────────────────────────┘
                              ▲
                              │ backfills + replay
                    ┌─────────┴─────────┐
                    │   Cloud Composer   │
                    └───────────────────┘
```

**Where you see it:** data platforms that have grown up and need both.

**Design rules:**
- Streams are *spooled* to GCS so that a pipeline bug can be replayed without re-sourcing upstream
- Composer orchestrates both batch and micro-batch (Dataflow) runs
- BigQuery holds the curated, queryable model

### The unifying design principles

1. **Immutable raw data.** Land once, never mutate.
2. **Partition everything.** By date at minimum, at every tier.
3. **Idempotent pipelines.** Re-running must not double-count.
4. **Pushdown of filters.** Filter as early as possible — partition pruning, cluster pruning.
5. **Govern from the top.** Organization policies, IAM by least privilege, Data Catalog tags.
6. **Cost as a first-class metric.** Every table has an owner and a cost allocation label.

---

## 🛠️ Hands-On: Build the Reference Architecture

### Step 1 — Ground rules and structure

```sql
-- Create a multi-region dataset with a default table expiration (30 days)
CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.analytics`
OPTIONS (
  location = 'US',
  default_table_expiration_days = 30,
  labels = [('env', 'prod'), ('team', 'data-eng'), ('cost_center', 'cc-1234')]
);

-- A dedicated raw layer — no expiration, for replay
CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.raw`
OPTIONS (
  location = 'US',
  labels = [('env', 'prod'), ('tier', 'raw')]
);

-- A curated layer
CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.curated`
OPTIONS (
  location = 'US',
  default_table_expiration_days = 90,
  labels = [('env', 'prod'), ('tier', 'curated')]
);
```

### Step 2 — Partitioned, clustered gold table

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.customer_daily_activity`
PARTITION BY activity_date
CLUSTER BY customer_id, activity_type
OPTIONS (
  description = 'Daily rollup of customer activity',
  partition_expiration_days = 400,
  require_partition_filter = TRUE,
  labels = [('tier', 'gold'), ('owner', 'data-eng')]
)
AS
SELECT
    activity_date,
    customer_id,
    activity_type,
    COUNT(*)              AS event_count,
    COUNT(DISTINCT session_id) AS session_count,
    SUM(duration_seconds) AS total_duration_seconds
FROM `YOUR_PROJECT_ID.raw.events`
WHERE activity_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 400 DAY)
GROUP BY activity_date, customer_id, activity_type;
```

💡 `require_partition_filter = TRUE` is a **safety feature worth enabling on every large
partitioned table**. It turns a catastrophic full-table scan into a query error. This single option
has saved countless engineering teams thousands of dollars.

### Step 3 — Serving view with row-level security

```sql
-- The view a BI tool queries
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.curated.v_customer_activity`
OPTIONS (
  description = 'Customer activity, row-filtered by sales territory',
  labels = [('tier', 'gold')]
) AS
SELECT
    activity_date,
    customer_id,
    activity_type,
    event_count,
    total_duration_seconds
FROM `YOUR_PROJECT_ID.curated.customer_daily_activity`
WHERE territory IN (
    SELECT territory
    FROM `YOUR_PROJECT_ID.security.user_territories`
    WHERE email = SESSION_USER()
);
```

### Step 4 — Cost attribution

```sql
-- Which tables are costing the most this month?
SELECT
    project_id,
    table_id,
    ROUND(SUM(ROUND((bytes_billed / POW(1024, 4)) * 6.25, 2)), 2) AS estimated_query_cost_usd,
    ROUND(SUM(storage_bytes) / POW(1024, 4), 2) AS storage_tib
FROM `YOUR_PROJECT_ID.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE creation_time >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY))
GROUP BY project_id, table_id
ORDER BY estimated_query_cost_usd DESC
LIMIT 20;
```

---

## 💡 Production Notes

- **Labels are not decoration.** `labels` on datasets and tables are the only reliable way to
  attribute cost to a team when you have dozens of pipelines. Set them at creation time; retrofitting
  them is painful.
- **`require_partition_filter`** — enable it on tables where a full scan would be genuinely expensive.
  It is a guardrail, not an optimization.
- **`default_table_expiration_days`** at the dataset level is a blunt but effective way to stop
  scratch tables from accumulating. Use it for staging datasets; never for gold data.
- **Information Schema** gives you `TABLES`, `COLUMNS`, `PARTITIONS`, `CLUSTERING_INFORMATION`, and
  `JOBS_BY_PROJECT` — treat it as your metadata catalog and your cost-monitoring tool.

---

## 🔑 Key Takeaways

- Three reference architectures: **Lakehouse**, **Streaming Analytics**, **Unified Batch + Streaming**.
- BigQuery is the query layer; Bigtable/Memorystore are the real-time serving layer.
- Raw data must be **immutable** and **partitioned** so that pipelines can be replayed.
- Enable `require_partition_filter` and `default_table_expiration_days` by default.
- Use labels for cost attribution from day one — retrofitting them is painful.
- Information Schema is the built-in catalog *and* the cost monitor.

---

## 📚 Practice Exercises

1. **Architecture selection.** Write a one-paragraph architecture proposal for:
   - (a) A ride-hailing company needing live ETA and daily driver payouts
   - (b) A retail chain needing nightly inventory reconciliation across 2,000 stores
   - (c) A healthcare startup needing HIPAA-compliant patient analytics

2. **Replay design.** A Dataflow job has a bug that corrupted the last 6 hours of the gold table.
   Design the replay procedure. What must be preserved? What is the exact SQL?

3. **Governance baseline.** Write the full set of DDL for a `raw` and `gold` dataset pair that
   enforces: partition filters required, 90-day expiry on gold, no expiry on raw, and team labels.

4. **Cost dashboard.** Write a query that reports **cost per pipeline** by joining
   `INFORMATION_SCHEMA.JOBS_BY_PROJECT` against your own pipeline registry table.

---

## 📖 Further Reading

- Cloud Architecture Framework: Data Analytics — https://cloud.google.com/architecture/data-analytics
- Lakehouse architecture on GCP — https://cloud.google.com/architecture/lakehouse
- BigQuery Information Schema — https://cloud.google.com/bigquery/docs/information-schema
