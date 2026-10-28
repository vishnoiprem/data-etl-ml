# 4.7 — Best Practices for Partitioning

> **Section 4 · Partitioning & Clustering · Lecture 4.8 · 7:27**

## 🎯 What you will learn

- The eight partitioning mistakes and their fixes
- A decision framework for choosing a partitioning strategy
- The interaction between partitioning, clustering, and query patterns
- How to audit and remediate an existing estate

---

## 🧠 Concept

Partitioning mistakes are expensive, silent, and permanent until fixed. This chapter is the
checklist.

---

## ⚠️ The Eight Mistakes

### Mistake 1 — Not partitioning at all

```sql
-- ❌ A 20 TB table with no partitioning: every query is a full scan
CREATE TABLE `YOUR_PROJECT_ID.curated.events_nopart` AS
SELECT * FROM `YOUR_PROJECT_ID.raw.events`;
```

**Fix:** partition by date. **Cost impact:** often 100–1000×.

### Mistake 2 — Filtering on a non-partition column

```sql
-- ❌ The table is partitioned by order_date, but the filter is on order_ts
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_dp`
WHERE order_ts >= TIMESTAMP '2026-01-01';
```

**Fix:** filter on `order_date`, the partition column. If you need timestamp precision, partition
by `DATE(order_ts)` and filter on the same expression.

### Mistake 3 — Wrapping the partition column in a function

```sql
-- ❌ Non-sargable — no pruning
WHERE DATE(order_date) = DATE '2026-01-15'
WHERE DATE_TRUNC(order_date, MONTH) = DATE '2026-01-01'
WHERE order_date + INTERVAL 1 DAY = DATE '2026-01-16'
```

**Fix:** compare the partition column directly. For monthly buckets, store a derived
`order_month` column and filter on that.

### Mistake 4 — Dynamic date expressions on a regular column

```sql
-- ❌ No pruning — the value is unknown at plan time
WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
```

**Fix:** use ingestion-time partitioning (`_PARTITIONDATE` prunes with dynamic expressions) or a
partition decorator (`$20260101:20260131`).

### Mistake 5 — Wrong granularity

```sql
-- ❌ Monthly partitions but daily queries: each query reads a whole month
PARTITION BY DATE_TRUNC(order_date, MONTH)
```

**Fix:** choose the granularity that matches your most frequent query pattern. If you query daily,
partition daily.

### Mistake 6 — No partition expiration

```sql
-- ❌ Grows without bound, eventually hits 10,000 partitions
CREATE TABLE `YOUR_PROJECT_ID.raw.events` PARTITION BY DATE(_PARTITIONTIME) AS ...
```

**Fix:** `OPTIONS (partition_expiration_days = 90)`.

⚠️ **This is the mistake that causes outages**, because the failure appears later as a load
error, not a design error.

### Mistake 7 — `OR` conditions defeating pruning

```sql
-- ❌ BigQuery must scan the union of partition sets
WHERE order_date = DATE '2026-01-15' OR status = 'completed'
```

**Fix:** split into two queries and `UNION ALL` them, or use a materialized view.

### Mistake 8 — Not enabling `require_partition_filter`

```sql
-- ❌ A forgotten date filter silently becomes a $600 query
CREATE TABLE `YOUR_PROJECT_ID.curated.orders_dp` PARTITION BY order_date AS ...
```

**Fix:**
```sql
OPTIONS (require_partition_filter = TRUE)
```

💡 **Turn this on by default for any table over ~1 GB.** The cost of a query error is far less
than the cost of an accidental full scan.

---

## 🧠 The Decision Framework

```
Step 1: Does the table exceed ~1 GB, or will it?
        │
        NO  → Skip partitioning. A 500 MB table scans in under a second.
        │
        YES ↓

Step 2: Do your queries filter on a date/time?
        │
        YES → Partition by that date column. (Most cases.)
        │
        NO ↓

Step 3: Do your queries filter on an integer range?
        │
        YES → Consider integer range partitioning. (Rare.)
        │
        NO ↓

Step 4: Is it a small dimension table?
        │
        YES → Do not partition. Cluster or leave it alone.
        │
        NO → Partition by the closest thing to your primary filter.
              Add clustering for the remaining filters.
```

### Choosing the partition column

| Data shape | Partition by | Example |
|------------|--------------|---------|
| Events with an event date | The event date | `PARTITION BY event_date` |
| Slowly changing dimension | The effective date | `PARTITION BY effective_date` |
| Append-only with no date | Ingestion time | `PARTITION BY DATE(_PARTITIONTIME)` |
| ID-ranged access | Integer range | `PARTITION BY RANGE_BUCKET(...)` |
| A small lookup | Nothing | — |

### Choosing the granularity

| Query pattern | Granularity |
|---------------|-------------|
| "Last 24 hours" | Hourly |
| "Last 7 days" | Daily |
| "Last 3 months" | Daily or monthly |
| "Last 3 years" | Monthly or yearly |
| A mix | **Daily** (the safe default) |

💡 **Daily is almost always correct.** It gives you flexibility to query any range, keeps the
partition count manageable, and makes retention easy to reason about.

---

## 🧠 Partitioning + Clustering: The Combination

These are complementary, not alternatives.

```
Partitioning  →  reduces the DATA SET      (which partitions to read)
Clustering    →  reduces the DATA WITHIN   (which blocks inside a partition)
```

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_combo`
PARTITION BY order_date
CLUSTER BY customer_id, status
OPTIONS (
  partition_expiration_days = 730,
  require_partition_filter = TRUE
)
AS SELECT * FROM `YOUR_PROJECT_ID.curated.orders`;
```

### The cost of clustering

| Table size | Clustering overhead |
|------------|---------------------|
| < 1 GB | Negligible |
| 1–10 GB | ~1–5% |
| 10–100 GB | ~2–10% |
| > 100 GB | ~5–20% |

⚠️ **Clustering rewrites the table.** Adding it to a large table is an expensive one-time
operation. Plan it as a migration.

---

## 🛠️ Hands-On: An Audit

### 1. Find unpartitioned large tables

```sql
SELECT
    table_name,
    ROUND(size_bytes / POW(1024, 3), 2) AS size_gb,
    row_count,
    partition_count
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.TABLES`
WHERE dataset_name = 'curated'
  AND type = 'TABLE'
  AND size_bytes > POW(1024, 4)   -- > 1 GB
  AND partition_count = 0
ORDER BY size_bytes DESC;
```

### 2. Find partitioned tables without expiration

```sql
SELECT
    t.table_name,
    t.partition_count,
    ROUND(t.size_bytes / POW(1024, 3), 2) AS size_gb,
    CASE
        WHEN t.partition_count > 9000 THEN '⚠️ CRITICAL'
        WHEN t.partition_count > 7000 THEN '⚠️ WARNING'
        ELSE 'OK'
    END AS partition_risk,
    s.default_partition_expiration_ms IS NULL AS no_expiration_set
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.TABLES` t
JOIN `YOUR_PROJECT_ID.INFORMATION_SCHEMA.SCHEMATA` s
  ON t.dataset_name = s.dataset_id
WHERE t.partition_count > 0
ORDER BY t.partition_count DESC;
```

### 3. Find queries that scanned far more than expected

```sql
-- Queries where bytes_processed >> the table size (no pruning)
SELECT
    j.job_id,
    j.user_email,
    ROUND(j.total_bytes_processed / POW(1024, 4), 3) AS tib_scanned,
    ROUND((j.total_bytes_processed / POW(1024, 4)) * 6.25, 2) AS est_cost_usd,
    REGEXP_EXTRACT(j.query, r'`([^`]+)`') AS table_ref,
    SUBSTR(j.query, 1, 100) AS query_head
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT` j
WHERE j.job_type = 'QUERY'
  AND j.creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND j.total_bytes_processed > POW(1024, 4)   -- > 1 TiB
ORDER BY j.total_bytes_processed DESC
LIMIT 50;
```

### 4. Find the most expensive queries by user

```sql
SELECT
    user_email,
    COUNT(*) AS query_count,
    ROUND(SUM(total_bytes_processed) / POW(1024, 4), 2) AS total_tib,
    ROUND(SUM((total_bytes_processed / POW(1024, 4)) * 6.25), 2) AS est_cost_usd,
    ROUND(SUM(total_slot_ms) / 1000 / 3600, 1) AS slot_hours
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE job_type = 'QUERY'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY user_email
ORDER BY est_cost_usd DESC;
```

💡 **This is your cost-attribution dashboard.** Run it monthly. The top user is usually running
one badly-designed query on a schedule, and fixing it is worth more than negotiating with
anyone.

### 5. Project the partition limit

```sql
-- When will each table hit 10,000 partitions?
SELECT
    table_name,
    partition_count,
    ROUND(partition_count / 10000.0 * 100, 1) AS pct_of_limit,
    CASE
        WHEN partition_count > 9000 THEN '⚠️ CRITICAL — act now'
        WHEN partition_count > 7000 THEN '⚠️ WARNING'
        ELSE 'OK'
    END AS status
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.TABLES`
WHERE partition_count > 0
ORDER BY pct_of_limit DESC;
```

---

## 💡 The Remediation Checklist

For an existing estate, work in this order:

1. **Add `require_partition_filter = TRUE`** to large partitioned tables (free, immediate).
2. **Set `partition_expiration_days`** on every partitioned table without it (a table rewrite —
   plan it).
3. **Identify the top 10 most expensive queries** and fix their partition filters.
4. **Add clustering** to the 5–10 tables where it helps most (a rewrite — plan it).
5. **Migrate the largest unpartitioned tables** to partitioned ones, one at a time, lowest risk
   first.
6. **Set up monitoring** for partition counts, cost by user, and unpartitioned large tables.

💡 **Do steps 1 and 3 first.** They are free or nearly free, and they stop the bleeding while
you plan the rest.

---

## 🔑 Key Takeaways

- Eight common mistakes: no partitioning, wrong filter column, non-sargable functions, dynamic
  expressions on regular columns, wrong granularity, no expiration, `OR` defeating pruning, and
  missing `require_partition_filter`.
- **Daily granularity** is the safe default.
- Partitioning reduces the *data set*; clustering reduces the *data within* it. Use both.
- **Audit first**: find large unpartitioned tables, partitioned tables without expiration, and
  expensive queries. Fix the top offenders.
- Enable `require_partition_filter = TRUE` — it is the cheapest safety net in BigQuery.
- Monitor partition counts against the 10,000 limit as a scheduled alert.

---

## 📚 Practice Exercises

1. **Mistake audit.** For each of these queries, state whether it prunes, and rewrite it correctly:
   - `WHERE DATE(ts) = '2026-01-01'`
   - `WHERE ts >= CURRENT_DATE() - 30`
   - `WHERE order_date = '2026-01-01' OR region = 'EU'`
   - `WHERE order_date + INTERVAL 0 DAY = '2026-01-01'`
   - `WHERE order_date IN (SELECT d FROM calendar WHERE is_holiday)`
   - `WHERE order_date >= '2026-01-01' AND order_date <= '2026-01-31'`

2. **Partition strategy.** For each table, write the full DDL including partitioning, clustering,
   expiration, and `require_partition_filter`:
   - (a) 15 TB IoT telemetry, 2M rows/day, queried by device_id and time
   - (b) 500 GB order table, queried by customer_id
   - (c) 80 TB raw event archive, queried rarely by month
   - (d) 2 GB dimension table with 50 columns

3. **Cost attribution.** Run the user-cost query on your project and write a one-page summary
   identifying the three biggest cost drivers and a specific fix for each.

4. **Migration plan.** A 40 TB table has no partitioning. Write the full migration plan: DDL, the
   copy method, downtime, validation, rollback, and the cost.

5. **Monitoring package.** Design a set of four scheduled queries that together detect:
   approaching partition limits, missing expiration settings, expensive unpruned queries, and
   cost anomalies. Specify the alert thresholds.

---

## 📖 Further Reading

- Partitioning best practices — https://cloud.google.com/bigquery/docs/partitioned-tables
- BigQuery cost optimization — https://cloud.google.com/bigquery/docs/best-practices
- `require_partition_filter` — https://cloud.google.com/bigquery/docs/partitioned-tables#require_partition_filter
- Cost monitoring — https://cloud.google.com/bigquery/docs/cost-monitoring
