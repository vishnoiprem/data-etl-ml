# 2.7 — Datasets & Regions

> **Section 2 · BigQuery Fundamentals · Lectures 2.7–2.8 · 3:23 + 4:16 + 7:17**

## 🎯 What you will learn

- Create datasets with the right location, labels, and lifecycle
- **Region vs multi-region** — the decision that affects data residency, cost, and latency
- Dataset-level defaults that save you time forever
- Table types and how to create each one

---

## 🧠 Concept

A **dataset** is the container that holds tables, views, and materialized views. It is the unit of
management, access control, and billing allocation. Everything inside a dataset shares a location.

### Location: the important choice

BigQuery offers three location types:

| Type | Examples | Data residency | Cost | Latency |
|------|----------|----------------|------|---------|
| **Regional** | `us-central1`, `europe-west2` | Confined to that region | **Baseline** | Lowest |
| **Multi-region** | `US`, `EU`, `asia-northeast1` | Confined to a *country group* | ~2× regional | Moderate |
| **Multi-region (dual)** | `US` (US + Canada) | Multiple countries | ~2× regional | Lowest |

💡 **Key rule: a multi-region dataset is roughly 2× the storage price of a regional dataset.**
For 10 TB of active data, that is ~$419/month vs ~$205/month. Use regional unless you have a
specific reason.

#### Which to choose

```
                        Do you have a legal/data-residency requirement?
                                    │
                    ┌───────────────┴───────────────┐
                   YES                              NO
                    │                                │
        Are users spread across         Do users cluster in
        multiple countries?            one country/region?
                    │                                │
        ┌───────────┴──────────┐          ┌────────┴────────┐
       YES                     NO          YES              NO
        │                      │           │                │
   Multi-region           Regional    Regional        Multi-region
   (e.g. `EU`)            (e.g.       (e.g.           (e.g. `US`)
                          europe-     us-central1)    for availability
                          west2)                       + local cache
```

#### The multi-region cache advantage

For a `US` multi-region dataset, BigQuery computes in whichever US region is closest to the
**user**, then replicates the result to the other regions. For a 3-second query, the user in
Oregon sees ~1.5s (computed locally) while a user in Virginia sees ~3s (computed in Oregon,
replicated back). This "local cache" is a genuine latency win for geographically distributed teams.

⚠️ **But** data in a multi-region is never left in the country group. `EU` means your data stays
in the EU, but it may be computed in any of several EU regions.

### Dataset options

```sql
CREATE SCHEMA `YOUR_PROJECT_ID.analytics`
OPTIONS (
  location                    = 'US',
  description                 = 'Curated analytics models',
  default_table_expiration_days = 90,
  default_partition_expiration_days = 60,
  max_staleness                = INTERVAL 1 HOUR,
  labels                       = [('env', 'prod'), ('team', 'data-eng')],
  is_case_insensitive          = OPTION("TRUE")
);
```

| Option | Purpose |
|--------|---------|
| `location` | Where data lives. **Immutable** — cannot be changed after creation. |
| `default_table_expiration_days` | Auto-expire new tables. Great for staging. |
| `default_partition_expiration_days` | Auto-expire old partitions. Excellent for raw zones. |
| `max_staleness` | For materialized views — how stale the MV may be before refresh. |
| `labels` | Cost attribution and governance. |
| `default_collation` | `und:ci` (case-insensitive) or `und:co` (case-sensitive). |
| `is_case_insensitive` | Case-insensitive dataset/table names. |

💡 **`default_partition_expiration_days` is under-used.** Setting it on a raw dataset gives you
automatic 90-day partition cleanup without a single cron job or Composer DAG. This alone prevents
the most common BigQuery cost problem: unbounded raw data growth.

⚠️ **The location of a dataset cannot be changed.** To move data, copy it to a new dataset in the
target location and swap. Plan this carefully at creation time.

---

## 🛠️ Hands-On

### 1. Create datasets for each tier

```sql
-- RAW: immutable landing zone, partitions expire after 180 days
CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.raw`
OPTIONS (
  location = 'US',
  description = 'Immutable raw landing zone. Never update. Never delete manually.',
  default_partition_expiration_days = 180,
  labels = [('tier', 'raw'), ('env', 'prod'), ('owner', 'data-eng')]
);

-- CURATED: cleaned and conformed models
CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.curated`
OPTIONS (
  location = 'US',
  description = 'Curated, conformed, queryable models',
  default_table_expiration_days = 365,
  default_partition_expiration_days = 730,
  labels = [('tier', 'curated'), ('env', 'prod'), ('owner', 'data-eng')]
);

-- MART: BI-facing serving layer
CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.mart`
OPTIONS (
  location = 'US',
  description = 'BI serving layer',
  labels = [('tier', 'gold'), ('env', 'prod'), ('owner', 'analytics-eng')]
);

-- SCRATCH: for experiments, expire fast
CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.scratch`
OPTIONS (
  location = 'US',
  default_table_expiration_days = 7,
  labels = [('tier', 'scratch'), ('env', 'dev')]
);
```

### 2. Compare regional vs multi-region cost

```sql
-- Storage cost for 5 TB active
SELECT
    'regional (us-central1)'  AS option,
    5 * 1024 * 1024 * 1024 * 0.02 / 100 AS monthly_usd
UNION ALL
SELECT
    'multi-region (US)',
    5 * 1024 * 1024 * 1024 * 0.04 / 100
UNION ALL
SELECT
    'multi-region (EU)',
    5 * 1024 * 1024 * 1024 * 0.04 / 100;
```

| Option | Monthly storage (5 TB) |
|--------|----------------------|
| regional | $~205 |
| multi-region (US) | $~419 |
| multi-region (EU) | $~419 |

### 3. Create tables of each type

```sql
-- 1. MANAGED table from a query
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.customers` AS
SELECT * FROM `YOUR_PROJECT_ID.raw.customers`;

-- 2. MANAGED table from DDL (schema-first)
CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.curated.orders` (
    order_id      STRING    NOT NULL,
    customer_id   STRING    NOT NULL,
    order_date    DATE      NOT NULL,
    order_ts      TIMESTAMP,
    total_amount  NUMERIC(12,2),
    status        STRING,
    line_items    ARRAY<STRUCT<
        product_id STRING,
        quantity   INT64,
        unit_price NUMERIC(10,2)
    >>
)
PARTITION BY order_date
CLUSTER BY customer_id, status
OPTIONS (
  description = 'Order line items',
  labels = [('tier', 'silver')],
  require_partition_filter = FALSE
);

-- 3. EXTERNAL table (no data movement)
CREATE EXTERNAL TABLE `YOUR_PROJECT_ID.curated.events_external`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/raw/events_*.parquet'],
  hive_partition_uri_prefix = 'gs://YOUR_PROJECT_ID-bq-course/raw/'
);

-- 4. SNAPSHOT table (point-in-time copy)
CREATE SNAPSHOT TABLE `YOUR_PROJECT_ID.curated.customers_snapshot`
FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY) AS
SELECT * FROM `YOUR_PROJECT_ID.curated.customers`;

-- 5. VIEW (logical, no data)
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.mart.v_active_customers` AS
SELECT customer_id, name, plan_type, signup_date
FROM `YOUR_PROJECT_ID.curated.customers`
WHERE status = 'active';

-- 6. MATERIALIZED VIEW (pre-computed)
CREATE MATERIALIZED VIEW `YOUR_PROJECT_ID.mart.mv_customer_order_stats`
PARTITION BY order_date
CLUSTER BY customer_id
AS
SELECT
    order_date,
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM `YOUR_PROJECT_ID.curated.orders`
GROUP BY order_date, customer_id;
```

### 4. Verify dataset configuration

```sql
SELECT
    dataset_id,
    location,
    default_table_expiration_ms,
    default_partition_expiration_ms,
    labels
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.SCHEMATA`
WHERE dataset_id IN ('raw', 'curated', 'mart', 'scratch');
```

---

## 💡 Production Notes

- **Dataset location is immutable.** Treat the initial choice as permanent. If you might need EU
  residency later, create the EU dataset now and migrate to it later rather than discovering the
  constraint at audit time.
- **Set `default_table_expiration_days` on every non-gold dataset.** The cost of forgetting is
  silent and unbounded.
- **`default_partition_expiration_days`** is the single most valuable dataset-level option for
  controlling storage cost on date-partitioned tables.
- **Case-insensitive naming** (`is_case_insensitive = OPTION("TRUE")`) prevents frustration with
  `Orders` vs `orders` — but it does not apply to column names.
- **Use labels religiously.** They are the only mechanism for per-team cost allocation.

---

## 🔑 Key Takeaways

- Datasets are containers; **location is immutable** and defines residency, cost, and latency.
- **Multi-region ≈ 2× the storage cost** of regional; use regional unless residency or
  distributed-user latency demands otherwise.
- `default_table_expiration_days` and `default_partition_expiration_days` are the cheapest cost
  controls in the platform.
- `labels` enable cost attribution and governance.
- BigQuery has 7+ table types; the table type you choose materially affects scan cost.
- Model your datasets as **tiers**: `raw` → `curated` → `mart` (+ `scratch`).

---

## 📚 Practice Exercises

1. **Location decision.** Three scenarios — pick the location type and justify:
   - (a) A UK retailer, all analysts in London, PCI scope
   - (b) A US SaaS with users in NY, SF, and Austin, no residency requirement
   - (c) A German automotive supplier with data that must never leave German jurisdiction

2. **Dataset design.** Write the complete DDL for a four-tier dataset layout for a company with
   GDPR obligations. Include expiration policies and labels.

3. **Expiration audit.** Write a query that finds every table in your project without a
   `default_table_expiration_days` on its dataset, and every partitioned table whose oldest
   partition is more than 90 days old. This is your cost-leak detector.

4. **Migration across regions.** Your dataset is in `us-central1` and you must move to `EU`. Write
   the exact migration procedure using `CREATE TABLE AS SELECT ... AS OF` and `EXPORT/IMPORT DATA`.
   What are the failure modes?

---

## 📖 Further Reading

- Dataset locations — https://cloud.google.com/bigquery/docs/locations
- Dataset options — https://cloud.google.com/bigquery/docs/dataset-options
- BigQuery table types — https://cloud.google.com/bigquery/docs/table-types
