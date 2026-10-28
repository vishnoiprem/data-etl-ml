# 4.5 — Date & Integer Partitioned Tables

> **Section 4 · Partitioning & Clustering · Lectures 4.5–4.6 · 6:49 + 5:05**

## 🎯 What you will learn

- Date-column partitioning in depth
- Integer range partitioning and when it beats date partitioning
- Partition filters, the decorator syntax, and the rules that make them work
- How to choose a partition granularity that fits your access patterns

---

## 🧠 Concept

### Date-column partitioning

The partition column is a `DATE`, `DATETIME`, or `TIMESTAMP` column in your schema. The partition
value is derived from it.

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_dp`
PARTITION BY order_date
OPTIONS (
  description = "Orders partitioned by order_date",
  partition_expiration_days = 730,
  require_partition_filter = TRUE
)
AS SELECT * FROM `YOUR_PROJECT_ID.curated.orders`;
```

#### Supported types

| Column type | Partition granularity available | Notes |
|-------------|--------------------------------|-------|
| `DATE` | Daily | Simplest, most common |
| `DATETIME` | Daily | |
| `TIMESTAMP` | Daily or hourly | Use `TIMESTAMP_TRUNC` for hourly |

```sql
-- Daily on a TIMESTAMP column
PARTITION BY DATE(event_ts)

-- Hourly on a TIMESTAMP column
PARTITION BY TIMESTAMP_TRUNC(event_ts, HOUR)

-- Weekly buckets (manual)
PARTITION BY DATE_TRUNC(event_date, WEEK)

-- Monthly buckets (manual)
PARTITION BY DATE_TRUNC(order_date, MONTH)
```

💡 **`DATE_TRUNC` gives you custom granularities.** BigQuery supports daily and hourly natively,
but `DATE_TRUNC(col, WEEK|MONTH|QUARTER|YEAR)` gives you any granularity you want.

⚠️ **Custom granularities have a cost.** Monthly partitions mean a query for a single day must
read a whole month of data. Only use coarser partitions if you genuinely query at that grain.

### The partition filter

A **partition filter** is a predicate on the partition column that BigQuery can use to prune.
There are three syntactic forms, and getting them right matters.

```sql
-- ✅ Form 1: equality
WHERE order_date = DATE '2026-01-15'

-- ✅ Form 2: comparison
WHERE order_date >= DATE '2026-01-01'
  AND order_date <  DATE '2026-02-01'

-- ✅ Form 3: IN with literals
WHERE order_date IN (DATE '2026-01-15', DATE '2026-01-16')

-- ✅ Form 4: BETWEEN (contiguous — prunes well)
WHERE order_date BETWEEN DATE '2026-01-01' AND DATE '2026-01-31'
```

```sql
-- ❌ Does NOT prune: function on the partition column
WHERE DATE_TRUNC(order_date, MONTH) = DATE '2026-01-01'

-- ❌ Does NOT prune: OR with a non-partition predicate
WHERE order_date = DATE '2026-01-15' OR status = 'completed'

-- ❌ Does NOT prune: subquery result
WHERE order_date IN (SELECT DISTINCT order_date FROM some_other_table)

-- ❌ Does NOT prune: dynamic expression
WHERE order_date = DATE_ADD(CURRENT_DATE(), INTERVAL -1 DAY)
```

⚠️ **A dynamic expression like `CURRENT_DATE()` does NOT prune** — BigQuery cannot know at plan
time what partitions it will need. This is why dashboards that use `CURRENT_DATE()` lose all
partition pruning benefit.

💡 **The fix for dynamic dates:** use the **partition decorator** with a wildcard, or use the
`_PARTITIONTIME` pseudo-column for ingestion-time tables.

```sql
-- ✅ Prunes with a dynamic date, using a decorator
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_dp$20260101:20260131`;

-- ✅ For ingestion-time tables, _PARTITIONTIME filters well
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.raw.events_it`
WHERE _PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY);
```

Hmm — wait. `_PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)` **does** prune, because
the pseudo-column is evaluated at plan time against partition metadata. The same expression on a
regular DATE column does not, because the value is row-level.

```sql
-- ❌ Regular column with a dynamic expression: no pruning
WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)

-- ✅ Ingestion-time pseudo-column with the same expression: prunes
WHERE _PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
```

---

## 🧠 Integer range partitioning

Partition a table by an `INT64` column. BigQuery buckets the values into ranges.

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.customers_ip`
PARTITION BY RANGE_BUCKET(customer_id, GENERATE_ARRAY(0, 1000000, 10000))
OPTIONS (
  description = "Customers partitioned by ID range",
  partition_expiration_days = 365
)
AS SELECT * FROM `YOUR_PROJECT_ID.curated.customers`;
```

### How it works

```
GENERATE_ARRAY(0, 1000000, 10000) creates:
  [0, 10000, 20000, ..., 1000000]

Partition 0:  customer_id in [0, 10000)
Partition 1:  customer_id in [10000, 20000)
...
Partition 99: customer_id in [990000, 1000000)
Partition 100: customer_id >= 1000000
```

| Property | Value |
|----------|-------|
| Partition count | `len(array) + 1` |
| Bucket boundaries | Fixed at creation — cannot be changed without a rewrite |
| Nullable | ❌ The partition column must be `NOT NULL` |
| Filter form | `WHERE customer_id BETWEEN 50000 AND 59999` |

### When integer partitioning makes sense

✅ **The query naturally filters on a numeric range.**
```sql
-- "Show me all orders for customer IDs 50000-50999"
WHERE customer_id BETWEEN 50000 AND 50999
```

✅ **The data is append-only and keyed by an increasing integer** (e.g. a monotonically
increasing event ID).

✅ **You need to distribute a huge table into a known number of partitions.**

❌ **The queries filter on something else.** Integer partitioning then buys nothing.

### Date vs integer partitioning — the comparison

| Aspect | Date partitioning | Integer partitioning |
|--------|-------------------|---------------------|
| Natural for | Time-series data | ID-ranged data |
| Filter form | `order_date BETWEEN ...` | `customer_id BETWEEN ...` |
| Granularity control | `DATE_TRUNC` for custom | Fixed bucket size at creation |
| Common use | 90% of real workloads | Rare — ID-range access patterns |
| NULL allowed | Partition column must be `NOT NULL` | Must be `NOT NULL` |

💡 **Almost always choose date partitioning.** Integer partitioning is a genuine tool but it has a
narrow use case. If you are considering it, first check whether you could partition by date
instead and cluster on the numeric column.

---

## 🧠 Clustered partitioning

You can combine both: partition by date, cluster by an integer.

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_dp_c`
PARTITION BY order_date
CLUSTER BY customer_id, status
AS SELECT * FROM `YOUR_PROJECT_ID.curated.orders`;
```

💡 **This is the workhorse pattern.** Partition gives you time-range pruning; clustering gives you
pruning within the remaining partitions for your most common filters.

---

## 🛠️ Hands-On

### 1. Create a date-partitioned table

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_dp`
PARTITION BY DATE(order_ts)
OPTIONS (
  description = "Orders partitioned by the DATE derived from order_ts",
  partition_expiration_days = 730,
  require_partition_filter = TRUE
)
AS
SELECT * FROM `YOUR_PROJECT_ID.curated.orders`;
```

### 2. Test every filter form

```sql
-- Run each of these and compare total_bytes_processed

-- A: equality
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_dp` WHERE order_ts = DATE '2026-01-15';

-- B: range
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_dp`
WHERE order_ts >= DATE '2026-01-01' AND order_ts < DATE '2026-02-01';

-- C: BETWEEN
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_dp`
WHERE order_ts BETWEEN DATE '2026-01-01' AND DATE '2026-01-31';

-- D: IN
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_dp`
WHERE order_ts IN (DATE '2026-01-15', DATE '2026-01-16', DATE '2026-01-17');

-- E: non-sargable (DOES NOT PRUNE)
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_dp`
WHERE DATE_TRUNC(order_ts, MONTH) = DATE '2026-01-01';

-- F: dynamic expression (DOES NOT PRUNE)
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_dp`
WHERE order_ts >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY);
```

### 3. Measure

```sql
SELECT
    job_id,
    ROUND((total_bytes_processed / POW(1024, 3)), 2) AS mb_processed,
    SUBSTR(REPLACE(query, '\n', ' '), 1, 90) AS query_head
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE query LIKE '%orders_dp%'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE)
ORDER BY creation_time DESC;
```

### 4. Integer range partitioning

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.customers_int`
PARTITION BY RANGE_BUCKET(customer_id, GENERATE_ARRAY(0, 100000, 10000))
OPTIONS (
  description = "Customers partitioned into ID ranges of 10,000",
  partition_expiration_days = 365
)
AS SELECT * FROM `YOUR_PROJECT_ID.curated.customers`;
```

```sql
-- Inspect the partitions
SELECT
    partition_id,
    total_rows,
    ROUND(total_logical_bytes / POW(1024, 2), 2) AS size_mb
FROM `YOUR_PROJECT_ID.curated.customers_int.INFORMATION_SCHEMA.PARTITIONS`
ORDER BY partition_id;
```

```sql
-- Query one bucket — prunes
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.customers_int`
WHERE customer_id BETWEEN 20000 AND 29999;

-- Query across all buckets — no pruning benefit
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.customers_int`
WHERE customer_id > 0;
```

### 5. Partition decorators with date ranges

```sql
-- A single day
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_dp$20260115`;

-- A range of days
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_dp$20260101:20260131`;

-- A month
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_dp$20260101:20260131`;  -- includes both ends
```

```bash
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_dp$20260101:20260131`'
```

### 6. Monthly partitions for coarse data

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_monthly`
PARTITION BY DATE_TRUNC(order_date, MONTH)
OPTIONS (partition_expiration_days = 3650)
AS SELECT * FROM `YOUR_PROJECT_ID.curated.orders`;
```

```sql
-- One month = one partition
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders_monthly`
WHERE DATE_TRUNC(order_date, MONTH) = DATE '2026-01-01';
```

---

## 💡 Production Notes

- **`require_partition_filter = TRUE` and dynamic date filters conflict.** If your workload uses
  `CURRENT_DATE()` filters, a date-column partition will not prune. Use ingestion-time
  partitioning or a partition decorator instead.
- **A `BETWEEN` on a date is inclusive on both ends.** For a half-open range (which avoids
  boundary bugs), use `>= start AND < end`.
- **`OR` conditions generally defeat partition pruning**, because BigQuery must scan the union of
  partition sets. Split them into separate queries and `UNION ALL` the results if needed.
- **Integer partition boundaries are fixed.** Changing the bucket size requires a full table
  rewrite.
- **Never partition by a `STRING` column.** BigQuery does not support it.

---

## 🔑 Key Takeaways

- Date partitioning uses your own `DATE`/`DATETIME`/`TIMESTAMP` column; `DATE_TRUNC` gives custom
  granularities.
- **Partition filters must be sargable** — direct comparisons on the column, no functions, no
  dynamic expressions on regular columns.
- **`_PARTITIONDATE` with dynamic expressions *does* prune** (plan-time evaluation), unlike a
  regular DATE column.
- **Partition decorators (`$20260101:20260131`) always prune** and solve the dynamic-date problem.
- Integer range partitioning is a niche tool; **date partitioning is right ~90% of the time**.
- The workhorse pattern is **partition by date + cluster by the filter columns**.

---

## 📚 Practice Exercises

1. **Filter form matrix.** For each of 12 filter forms (equality, range, BETWEEN, IN, OR,
   NOT, function-wrapped, dynamic, subquery, CASE, UNION, cross-join), state whether it prunes and
   explain why. Then verify each empirically.

2. **Granularity decision.** A 3 TB table has 2 years of daily data. Compare daily, weekly, and
   monthly partitioning on: partition count, pruning granularity for "last 7 days" queries,
   storage overhead, and operational complexity. Recommend one.

3. **Integer partitioning evaluation.** A table is queried with `WHERE customer_id BETWEEN x AND y`
   60% of the time and by date 30% of the time. Design the partitioning + clustering scheme and
   justify it.

4. **Dynamic date problem.** A BI tool generates `WHERE order_date >= DATE_SUB(CURRENT_DATE(),
   INTERVAL 30 DAY)`. The table is date-partitioned and the dashboard is slow. Diagnose the issue
   and provide three fixes, including one that requires no dashboard changes.

5. **Partition decorator library.** Build a set of reusable queries using partition decorators for:
   last 7 days, last 30 days, current month, previous month, year-to-date, and trailing 12 months.

---

## 📖 Further Reading

- Date and time partitioned tables — https://cloud.google.com/bigquery/docs/partitioned-tables#date_time
- Integer range partitioned tables — https://cloud.google.com/bigquery/docs/partitioned-tables#integer_range
- Partition filters — https://cloud.google.com/bigquery/docs/partitioned-tables#partition_filters
- Table decorators — https://cloud.google.com/bigquery/docs/table-decorators
