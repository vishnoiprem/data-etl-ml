# 4.3 — Partitioning: Concepts

> **Section 4 · Partitioning & Clustering · Lecture 4.3 · 5:01**

## 🎯 What you will learn

- What partitioning actually does inside BigQuery
- The three partitioning flavours and their trade-offs
- How partition pruning works and why it saves so much
- The hard limits that constrain your design

---

## 🧠 Concept

Partitioning divides a table into segments — "partitions" — that BigQuery can skip entirely.
It is the single highest-leverage design decision in BigQuery, because it reduces both **bytes
scanned** and **storage cost**.

### How partitioning works internally

```
Table: orders
PARTITION BY order_date

Physical layout:
├── _PARTITIONS/
│   ├── 20260101/    ← partition directory
│   │   └── data files...
│   ├── 20260102/
│   │   └── data files...
│   ├── ...
└── data files (for non-partitioned tables)
```

BigQuery maintains partition metadata separately. When you query with a filter on the partition
column, BigQuery reads the **partition metadata first**, determines which partitions can contain
matching rows, and never opens the others.

💡 **This is metadata-only access.** Skipping a partition costs essentially nothing — no bytes
scanned, no storage read. That is why partitioning can turn a $600 query into a $0.60 query.

### Partition pruning

Pruning happens when a filter on the partition column can be turned into a **definite partition
range**.

```sql
-- ✅ PRUNES: partition column in a comparable predicate
SELECT COUNT(*) FROM `p.analytics.orders`
WHERE order_date = DATE '2026-01-15';

SELECT COUNT(*) FROM `p.analytics.orders`
WHERE order_date >= DATE '2026-01-01' AND order_date < DATE '2026-02-01';

SELECT COUNT(*) FROM `p.analytics.orders`
WHERE order_date BETWEEN DATE '2026-01-01' AND DATE '2026-01-31';

-- ❌ DOES NOT PRUNE: filter on a different column
SELECT COUNT(*) FROM `p.analytics.orders`
WHERE status = 'completed';

-- ❌ DOES NOT PRUNE: function on the partition column
SELECT COUNT(*) FROM `p.analytics.orders`
WHERE DATE(order_ts) = DATE '2026-01-15';

-- ❌ DOES NOT PRUNE: non-sargable expression
SELECT COUNT(*) FROM `p.analytics.orders`
WHERE order_date + 1 = DATE '2026-01-16';
```

⚠️ **A function on the partition column kills pruning.** `DATE(order_ts) = ...` is not
sargable. `order_date = ...` is. This is the most common partitioning mistake.

### The three partitioning types

| Type | Partition key | Pseudo-column | Best for |
|------|---------------|---------------|----------|
| **Ingestion-time** | Automatic (load time) | `_PARTITIONTIME` | Append-only data where the source has no date |
| **Date column** | `DATE`, `DATETIME`, `TIMESTAMP` | The column itself | Data with a natural business date |
| **Integer range** | `INT64` | The column itself | Bucketed numeric data |

### Partitioning granularity

| Granularity | Partitions per day | Use when |
|-------------|-------------------|----------|
| **Hourly** | 24 | Real-time events, IoT, sub-hour latency needs |
| **Daily** | 1 | **The default. Almost always right.** |
| **Monthly** | 1 per month | Coarse retention, long histories |
| **Yearly** | 1 per year | Very coarse data |

💡 **Daily partitioning is the default for a reason.** It gives you the flexibility to scan any
date range, keeps partition counts manageable, and makes retention easy. Move to hourly only if
you genuinely need sub-day pruning, and understand that it multiplies your partition count by 24.

### The hard limits

| Limit | Value | Implication |
|-------|-------|-------------|
| Maximum partitions per table | **10,000** (default) | 27 years of daily, or ~12 months of hourly |
| Maximum columns in a partition expression | 1 | Cannot partition by two date columns |
| Maximum columns in a clustering expression | 4 | |
| Partitioning on `BOOL` | ❌ Not allowed | |
| Partitioning on `STRING` | ❌ Not allowed | Use date or integer |
| Changing partition scheme | ⚠️ **Rewrites the table** | Expensive |

⚠️ **The 10,000-partition limit is real and it will bite you.** An hourly-partitioned table
accumulates 8,760 partitions per year and hits the limit at just over a year. BigQuery will start
rejecting loads.

💡 **There is no automatic partition limit increase.** You must delete old partitions before the
limit is reached. This makes `partition_expiration_days` mandatory, not optional, for any
high-frequency table.

---

## 🛠️ Hands-On: Prove Partition Pruning Works

### 1. Create a partitioned table

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_partitioned`
PARTITION BY order_date
AS
SELECT
    order_date,
    order_id,
    customer_id,
    total_amount,
    status
FROM `YOUR_PROJECT_ID.curated.orders`;
```

### 2. Look at the partitions

```sql
-- The partition metadata table
SELECT
    partition_id,
    total_rows,
    total_logical_bytes
FROM `YOUR_PROJECT_ID.curated.orders_partitioned.INFORMATION_SCHEMA.PARTITIONS`
ORDER BY partition_id DESC
LIMIT 30;
```

```sql
-- Summary
SELECT
    COUNT(*) AS partition_count,
    SUM(total_rows) AS total_rows,
    ROUND(SUM(total_logical_bytes) / POW(1024, 3), 2) AS total_gb
FROM `YOUR_PROJECT_ID.curated.orders_partitioned.INFORMATION_SCHEMA.PARTITIONS`;
```

### 3. Measure the pruning benefit

```sql
-- ❌ No partition filter: reads everything
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_partitioned`;

-- ✅ Partition filter: reads ~1 day
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_partitioned`
WHERE order_date = DATE '2026-01-15';

-- ✅ Date range: reads ~1 month
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_partitioned`
WHERE order_date >= DATE '2026-01-01' AND order_date < DATE '2026-02-01';
```

### 4. Compare the bytes

```sql
SELECT
    job_id,
    CASE
        WHEN query LIKE '%= DATE%' THEN 'single_day'
        WHEN query LIKE '%>= DATE%' THEN 'date_range'
        ELSE 'full_scan'
    END AS query_type,
    ROUND((total_bytes_processed / POW(1024, 3)), 2) AS mb_processed,
    ROUND((total_bytes_processed / POW(1024, 4)) * 6.25, 4) AS est_cost_usd
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE query LIKE '%orders_partitioned%'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY creation_time DESC;
```

### 5. Demonstrate the non-sargable failure

```sql
-- ❌ NO PRUNING: function wraps the partition column
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_partitioned`
WHERE DATE(order_ts) = DATE '2026-01-15';

-- ✅ PRUNING: filter on the partition column directly
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_partitioned`
WHERE order_date = DATE '2026-01-15';
```

Compare `total_bytes_processed`. This single demonstration is the most valuable thing in this
chapter.

### 6. Monitor partition counts

```sql
-- Your partition-limit monitor
SELECT
    table_name,
    COUNT(*) AS partition_count,
    COUNT(*) / 10000.0 AS pct_of_limit,
    CASE
        WHEN COUNT(*) > 9000 THEN '⚠️ CRITICAL — near the 10,000 limit'
        WHEN COUNT(*) > 7000 THEN '⚠️ WARNING — schedule partition cleanup'
        ELSE 'OK'
    END AS status
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.PARTITIONS`
GROUP BY table_name
ORDER BY partition_count DESC;
```

💡 **This should be a scheduled alert.** Hitting the partition limit causes load failures in
production — and the failure message ("Exceeded maximum partitions") does not immediately point at
the real cause.

---

## 💡 Production Notes

- **Always partition large tables by date.** The only exception is a genuinely small table
  (under ~10 GB) that is scanned in full anyway.
- **Filter on the partition column directly.** No functions, no casts, no arithmetic.
- **Use `partition_expiration_days`** on every partitioned table. It is the only automatic defense
  against the 10,000-partition limit.
- **Adding a partition filter changes the query's cost profile dramatically.** A dashboard that
  forgets its date filter can cost 1000× more than one that remembers.
- **`require_partition_filter = TRUE`** turns the omission of a partition filter into a query
  error instead of a silent full scan. Enable it on production tables.

---

## 🔑 Key Takeaways

- Partitioning splits a table into segments BigQuery can skip entirely — **metadata-only access**.
- Pruning requires a **sargable** filter directly on the partition column.
- Three types: **ingestion-time**, **date column**, **integer range**.
- **Daily granularity is the default.** Hourly multiplies partition count by 24.
- **Hard limit: 10,000 partitions per table.** `partition_expiration_days` is mandatory.
- One partition column, up to 4 clustering columns.
- `require_partition_filter = TRUE` is a cheap, high-value safety net.

---

## 📚 Practice Exercises

1. **Pruning proof.** Create a table with 100 partitions of known size. Run six queries — full
   scan, equality, range, `BETWEEN`, non-sargable function, and an OR condition — and record
   `total_bytes_processed` for each. Explain every result.

2. **Partition design.** Design the partitioning scheme for:
   - (a) A 50 TB clickstream table, hourly events
   - (b) A 2 TB order table, daily orders
   - (c) A 500 GB product catalog, updated continuously
   - (d) A 10 PB IoT telemetry archive
   Include the granularity, expiration, and the `require_partition_filter` setting for each.

3. **Partition limit.** A table is hourly-partitioned and has been loading for 14 months. Write
   the SQL to find out exactly when it will hit the limit, and the fix. What happens to the loads
   in the meantime?

4. **Sargability audit.** Write a linter query that scans the SQL text of recent jobs and flags
   any query that references a partitioned table but contains a function call on the partition
   column. This is your preventive control.

5. **Migration.** A 30 TB unpartitioned table needs partitioning by `event_date`. Design the
   migration: the exact DDL, whether to use a copy or CTAS, how to handle the downtime, and the
   validation steps.

---

## 📖 Further Reading

- Partitioned tables — https://cloud.google.com/bigquery/docs/partitioned-tables
- Partition pruning — https://cloud.google.com/bigquery/docs/partitioned-tables#pruning
- Partition limits — https://cloud.google.com/bigquery/quotas
