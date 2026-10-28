# 4.9 — Partitioning vs Clustering vs Both

> **Section 4 · Partitioning & Clustering · Lecture 4.11 · 3:46**

## 🎯 What you will learn

- The complete decision matrix for all three options
- A cost-benefit framework with numbers
- The combination pattern that most production tables should use
- A worked example with real measurements

---

## 🧠 Concept

This chapter settles the most common BigQuery design debate.

### The Decision Matrix

| Situation | Partition | Cluster | Both |
|-----------|-----------|---------|------|
| Time-series / event data | ✅ **Always** | ✅ On filter columns | ✅✅ **Best** |
| Fact table, 1–100 GB | ✅ | ✅ | ✅✅ |
| Fact table, > 1 TB | ✅✅ | ✅ | ✅✅ |
| Small dimension (< 1 GB) | ❌ | ⚠️ Maybe | ❌ |
| Slowly changing dimension | ✅ On effective_date | ✅ On key | ✅✅ |
| Append-only raw archive | ✅ Ingestion-time | ❌ | ✅ |
| External table (GCS) | ✅ (hive partitioning) | ❌ | — |
| Frequently filtered on one ID | ✅ | ✅✅ On that ID | ✅✅ |

### The Core Principle

```
Partitioning = coarse-to-fine navigation
    "Of 365 days, only January matters"      → reduces data set

Clustering = fine-grained navigation
    "Of January's 10 TB, only these 500 MB matter" → reduces data within
```

💡 **Use both, by default, on any fact table over ~1 GB.** Partition by the date you filter on
most, cluster on the ID you filter on most.

### The Cost-Benefit Framework

```
Partitioning:
  Cost:    ~0% storage overhead
           One-time table rewrite to apply
  Benefit: Up to 1000× scan reduction
  Verdict: ALWAYS worth it on tables > 1 GB

Clustering:
  Cost:    ~5-20% storage overhead
           One-time table rewrite to apply
           Background re-clustering compute (free)
  Benefit: 2-100× scan reduction on clustered columns
  Verdict: Worth it when the clustered column is in >30% of queries
```

### When clustering is NOT worth it

| Scenario | Why |
|----------|-----|
| Low-cardinality column (`status`, `country`) | Few distinct values → few blocks skipped |
| Column rarely used in filters | No benefit, pure storage cost |
| Table under ~1 GB | The scan is already fast |
| `LIKE '%...%'` filters | Substring match cannot use sorted blocks |
| Full-table aggregations | Clustering prunes reads, not aggregation scans |

💡 **A good rule of thumb:** if the column has fewer than ~1,000 distinct values, clustering
gains you little. If it has millions, clustering gains you a lot.

---

## 🛠️ A Worked Example

### The setup

A 10 TB orders table. Common query patterns:

| Pattern | Frequency | Filter |
|---------|-----------|--------|
| Dashboard: revenue by region | Every hour | `order_date` range |
| Customer support: find an order | Daily | `order_id` |
| Churn analysis by segment | Weekly | `customer_id` + date range |
| Full export | Monthly | none |

### Option A — No partition, no cluster

```sql
CREATE TABLE `YOUR_PROJECT_ID.curated.orders_none` AS
SELECT * FROM `YOUR_PROJECT_ID.raw.orders`;
```

| Query | Bytes scanned | Cost |
|-------|--------------|------|
| Dashboard (1 day) | 10 TB | $62.50 |
| Find an order | 10 TB | $62.50 |
| Churn by segment (30 days) | 10 TB | $62.50 |
| **Monthly total** | **40 TB** | **$250.00** |

### Option B — Partition by date only

```sql
CREATE TABLE `YOUR_PROJECT_ID.curated.orders_part`
PARTITION BY order_date
AS SELECT * FROM `YOUR_PROJECT_ID.raw.orders`;
```

| Query | Bytes scanned | Cost |
|-------|--------------|------|
| Dashboard (1 day) | 27 GB | $0.17 |
| Find an order | 10 TB | $62.50 |
| Churn by segment (30 days) | 820 GB | $5.13 |
| **Monthly total** | **~11 TB** | **$68.75** |

### Option C — Partition by date + cluster on customer_id and order_id

```sql
CREATE TABLE `YOUR_PROJECT_ID.curated.orders_both`
PARTITION BY order_date
CLUSTER BY customer_id, order_id
AS SELECT * FROM `YOUR_PROJECT_ID.raw.orders`;
```

| Query | Bytes scanned | Cost |
|-------|--------------|------|
| Dashboard (1 day) | 27 GB | $0.17 |
| Find an order | ~8 MB | $0.00005 |
| Churn by segment (30 days) | ~95 GB | $0.59 |
| **Monthly total** | **~11 TB + 1 GB** | **$68.76** |

### The summary

| Query | A: none | B: partition | C: both |
|-------|---------|--------------|---------|
| Dashboard | $62.50 | $0.17 | $0.17 |
| Find an order | $62.50 | $62.50 | ~$0.00 |
| Churn analysis | $62.50 | $5.13 | $0.59 |
| Monthly export | $250.00 | $68.75 | $68.76 |
| **Storage overhead** | 0% | ~0% | ~+8% |

💡 **The finding:** partitioning gave a **366× reduction** on the dashboard query. Clustering
gave a **~8.7× further reduction** on the churn analysis and made the point lookup essentially
free.

Neither alone was enough. **Partitioning solved the time-range problem; clustering solved the
entity-lookup problem.** They address different query patterns.

---

## 🛠️ The Decision Procedure

```
                        Is the table a FACT table (large, append-oriented)?
                                    │
                    ┌───────────────┴───────────────┐
                   NO                              YES
                    │                                │
        ┌───────────┴──────────┐                   ▼
        │                      │         ┌─────────────────────────┐
   Size < 1 GB?          Size > 1 GB     │ Do queries filter on a  │
        │                      │         │ date or time range?     │
        ▼                      ▼         └───────────┬─────────────┘
   Leave it alone.      ┌─────────┐                 │
   Maybe cluster if     │ PARTITION│◀────────────────┘
   one column is        │ by that │
   highly selective     │ column  │
   and in most queries  └─────────┘
                                  │
                                  ▼
                    ┌──────────────────────────────┐
                    │ Do queries also filter on    │
                    │ specific entity IDs?         │
                    └───────────┬──────────────────┘
                          ┌─────┴─────┐
                         YES          NO
                          │            │
                          ▼            ▼
                  ┌───────────────┐   ┌─────────────┐
                  │ CLUSTER on    │   │ Partition   │
                  │ the most      │   │ only.       │
                  │ selective IDs │   │ Done.       │
                  │ (max 4)       │   └─────────────┘
                  └───────────────┘
```

### Worked application to the example above

1. Fact table, > 1 GB → **yes**
2. Queries filter on a date range → **yes** → partition by `order_date`
3. Queries also filter on `customer_id` and `order_id` → **yes** → cluster on both
4. Result: `PARTITION BY order_date CLUSTER BY customer_id, order_id` ✅

---

## 🧠 Advanced: When Clustering Alone Wins

There is one scenario where clustering is more impactful than partitioning: **a huge table that is
almost always queried for specific entities, with no time filter.**

```sql
-- 50 TB table, always queried by customer_id, never by date
CREATE TABLE `YOUR_PROJECT_ID.curated.customer_360`
CLUSTER BY customer_id
AS SELECT * FROM `YOUR_PROJECT_ID.raw.events`;
```

| Query | Bytes | Cost |
|-------|-------|------|
| `WHERE customer_id = 'cust_42'` | ~2 MB | $0.00001 |
| `WHERE customer_id IN (100 ids)` | ~200 MB | $0.001 |

💡 **For a 360-degree customer view table, clustering on `customer_id` is dramatically better
than partitioning by date** — because the access pattern is entity-centric, not time-centric.

⚠️ **But** if you ever need to scan the whole table for an aggregate, clustering gives you
nothing. Choose based on your dominant query pattern, and consider **both** if the patterns are
mixed.

---

## 🛠️ Hands-On: Verify the Framework

### 1. Compare all three configurations

```sql
-- Setup: three identical tables
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.t_orders_none` AS
SELECT * FROM `YOUR_PROJECT_ID.raw.orders`;

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.t_orders_part`
PARTITION BY order_date AS
SELECT * FROM `YOUR_PROJECT_ID.raw.orders`;

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.t_orders_both`
PARTITION BY order_date
CLUSTER BY customer_id, order_id AS
SELECT * FROM `YOUR_PROJECT_ID.raw.orders`;
```

```sql
-- Measure storage overhead
SELECT
    table_name,
    ROUND(size_bytes / POW(1024, 3), 2) AS size_gb,
    partition_count,
    clustering_fields
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.TABLES`
WHERE table_name LIKE 't_orders_%'
ORDER BY size_gb;
```

```sql
-- Measure the query costs
SELECT
    CASE
        WHEN query LIKE '%t_orders_none%' THEN 'none'
        WHEN query LIKE '%t_orders_part%' THEN 'partition'
        ELSE 'both'
    END AS config,
    ROUND((total_bytes_processed / POW(1024, 4)) * 6.25, 4) AS est_cost_usd,
    ROUND(total_slot_ms / 1000, 2) AS slot_seconds
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE query LIKE '%t_orders_%'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY creation_time DESC;
```

### 2. The decisive test — an entity lookup

```sql
-- The query clustering is designed for
SELECT * FROM `YOUR_PROJECT_ID.t_orders_both`
WHERE customer_id = 'cust_000042'
  AND order_date = DATE '2026-01-15';
```

Compare against the unclustered version. This is where clustering earns its storage overhead.

---

## 💡 Production Notes

- **Adding clustering later is expensive** (a full rewrite). Deciding at creation time is much
  cheaper than retrofitting.
- **Do not cluster on more columns than you need.** Each additional clustering column increases
  the storage overhead and the re-clustering work.
- **Clustering columns should be in your `WHERE` clauses, not your `GROUP BY`.** Clustering prunes
  reads; it does not make aggregation cheaper.
- **If you partition by date and also filter by date, the clustering column should not be the
  date** — that is redundant.
- **When both partitioning and clustering apply, partitioning always wins on the time-range
  query** (it is a much coarser, more reliable reduction). Clustering wins on entity lookups.

---

## 🔑 Key Takeaways

- **Partitioning and clustering are complementary**, not alternatives — use both by default on
  fact tables over ~1 GB.
- Partitioning reduces the *data set*; clustering reduces the *data within* a partition.
- Partitioning: ~0% overhead, up to 1000× benefit. **Always worth it.**
- Clustering: ~5–20% overhead, 2–100× benefit on clustered columns. **Worth it when the column is
  in >30% of queries and has high cardinality.**
- In the worked example: partitioning gave 366× on time-range queries; clustering gave 8.7× on
  entity queries.
- **Clustering alone wins for entity-centric tables** (e.g. a 360-degree customer view).
- Decide at creation time — retrofitting clustering is a full table rewrite.

---

## 📚 Practice Exercises

1. **Apply the framework.** For each of these tables, produce the full DDL and justify:
   - (a) 500 GB clickstream, queried by `device_id` and time
   - (b) 20 TB orders, queried by `customer_id` + time range, and by `order_id`
   - (c) 3 TB sensor telemetry, queried by `sensor_id` only, never by time
   - (d) 100 GB customer 360 table, queried by `customer_id`, occasionally full-scan for ML
   - (e) 800 MB product dimension, queried by `category` and `sku`

2. **Measure the overhead.** Build a table with 0, 1, 2, 3, and 4 clustering columns and record the
   size of each. Write the formula BigQuery uses and explain the overhead.

3. **Reverse-engineer a design.** Given a query log, infer the optimal partitioning and clustering
   for a table. Write the query that produces the analysis.

4. **Clustering vs materialized view.** For a query that scans 30 TB repeatedly to produce a
   daily aggregate, compare three fixes: clustering, a materialized view, and a pre-aggregated
   summary table. Compute the monthly cost of each.

5. **Migration economics.** A 15 TB table currently has no partitioning. Compare:
   (a) rewriting with partitioning only, (b) rewriting with partitioning + clustering, (c) leaving
   it and adding a materialized view. Include one-time and recurring costs.

---

## 📖 Further Reading

- Partitioned and clustered tables — https://cloud.google.com/bigquery/docs/partitioned-tables
- Clustered tables — https://cloud.google.com/bigquery/docs/clustered-tables
- BigQuery pricing — https://cloud.google.com/bigquery/pricing
- BigQuery best practices — https://cloud.google.com/bigquery/docs/best-practices
