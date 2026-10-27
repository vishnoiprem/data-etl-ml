# 10.2 — Cost Optimization Techniques

> **Section 10 · Pricing & Cost Optimization · Lecture 10.2 · 6:25**

## 🎯 What you will learn

- The eight cost levers that matter, ranked by impact
- Partitioning, clustering, and selective scans in practice
- Materialized views and BI Engine
- Storage lifecycle: expiration, long-term, and capacity-optimized tables
- A measurement-driven optimization workflow

---

## 🧠 Concept

BigQuery charges for **bytes scanned**. Almost every optimization is a way to scan fewer
bytes. Rank the levers by impact:

| # | Lever | Typical saving | Effort |
|---|-------|---------------|--------|
| 1 | **Partition filters** | 90–99% | Low |
| 2 | **Avoid `SELECT *`** | 50–90% | Low |
| 3 | **Materialized views** | 80–95% | Medium |
| 4 | **Clustering** | 30–70% | Medium |
| 5 | **BI Engine** | 90%+ (reserved) | Medium |
| 6 | **Storage expiration / long-term** | 50% of storage | Low |
| 7 | **Capacity-optimized tables** | ~30% (on scans) | Low |
| 8 | **Query cache & result reuse** | 100% for repeats | Low |

---

## 🛠️ Hands-On

### 1. Partition filters — the biggest lever

```sql
-- ❌ Scans the whole table
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders`;

-- ✅ Scans one partition
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = DATE '2026-01-15';

-- ✅ Partition decorator — even more precise
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders$20260115`;

-- ✅ Range decorator
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders$20260101:20260131`;

-- ✅ On an ingestion-time partitioned table
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.raw.events`
WHERE _PARTITIONDATE = DATE '2026-01-15';
```

💡 **The filter must be on the partition column itself** — not on a function of it, and not
inside an OR. BigQuery's partition pruning only works when it can prove the filter is
selective.

```sql
-- ❌ No pruning — the function hides the column
SELECT * FROM `t` WHERE DATE(order_date) = '2026-01-15';

-- ✅ Pruning works
SELECT * FROM `t` WHERE order_date = '2026-01-15';
```

### 2. Enable `require_partition_filter` so mistakes become errors

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders`
PARTITION BY order_date
OPTIONS(require_partition_filter = TRUE);
```

```bash
# Verify it is on
bq show --format=json YOUR_PROJECT_ID:curated.orders | jq '.requirePartitionFilter'
```

💡 **A full scan becomes a hard error instead of a $400 surprise.** This is the single most
valuable cost setting in BigQuery.

### 3. Never `SELECT *`

```sql
-- ❌ Reads every column
SELECT * FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = '2026-01-15';

-- ✅ Reads only what you need
SELECT order_id, customer_id, total_amount
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = '2026-01-15';
```

```python
# The column pruning rule, demonstrated
job = client.query(
    """
    SELECT order_id, total_amount
    FROM `YOUR_PROJECT_ID.curated.orders`
    WHERE order_date = '2026-01-15'
    """,
    job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False),
)
print(job.total_bytes_processed)   # Only the two columns
```

### 4. Clustering — reducing bytes within a partition

```sql
-- A clustered table scans only the blocks matching the filter
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = '2026-01-15'
  AND customer_id = 'c0042';
```

```bash
# Check the clustering
bq show --format=json YOUR_PROJECT_ID:curated.orders | jq '.clustering'
```

💡 **Clustering helps most when the filter is on a high-cardinality column and the table is
large.** It does nothing for `WHERE true` or for low-cardinality filters.

| Table size | Clustering benefit |
|-----------|-------------------|
| < 1 GB | Negligible |
| 1–10 GB | 10–30% |
| 10–100 GB | 30–60% |
| > 100 GB | 50–80% |

### 5. Materialized views — the biggest architectural lever

```sql
CREATE MATERIALIZED VIEW `YOUR_PROJECT_ID.mart.mv_daily_revenue`
PARTITION BY order_date
CLUSTER BY region
AS
SELECT
  order_date,
  region,
  COUNT(*) AS order_count,
  SUM(amount_eur) AS revenue_eur
FROM `YOUR_PROJECT_ID.curated.orders`
GROUP BY order_date, region;
```

```sql
-- The dashboard query now reads a tiny MV instead of scanning `curated.orders`
SELECT order_date, region, revenue_eur
FROM `YOUR_PROJECT_ID.mart.mv_daily_revenue`
WHERE order_date = '2026-01-15';
```

💡 **An MV is pre-computed, so the query reads the aggregated rows instead of the raw rows.**
On a 10× reduction in scanned rows, the cost drops 10×. The trade-off is storage and refresh
latency.

**MV restrictions to remember:**
- Exactly **one** base table
- No subqueries, no `GROUP BY` on an aggregate
- `JOIN` is not allowed directly
- The base table's partition filter is inherited

```sql
-- MV + view pattern — join in the view, aggregate in the MV
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.mart.v_orders_with_region` AS
SELECT o.*, r.region_name
FROM `YOUR_PROJECT_ID.curated.orders` o
JOIN `YOUR_PROJECT_ID.curated.regions` r USING (region);

CREATE MATERIALIZED VIEW `YOUR_PROJECT_ID.mart.mv_revenue_by_region` AS
SELECT order_date, region_name, SUM(amount_eur) AS revenue
FROM `YOUR_PROJECT_ID.mart.v_orders_with_region`
GROUP BY order_date, region_name;
```

### 6. BI Engine — reserved capacity for your dashboard

```sql
-- Create a BI Engine reservation
CREATE BI ENGINE RESERVATION
  `YOUR_PROJECT_ID.BI_RESERVATION`
  OPTIONS(
    edition = "ENTERPRISE",
    capacity_bi_units = 1024.0,
    timeout_ms = 3600000
  );
```

```sql
-- Attach a table to BI Engine
ALTER TABLE `YOUR_PROJECT_ID.mart.daily_revenue`
  SET OPTIONS (enable_bi_engine = true);
```

```sql
-- Check the status
SELECT
  t.table_name,
  r.reservation_name,
  t.bi_engine_status
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.TABLES` t
LEFT JOIN `YOUR_PROJECT_ID.INFORMATION_SCHEMA.BI_CAPACITIES` r
  USING (project_id, dataset_id)
WHERE t.table_name = 'daily_revenue';
```

💡 **BI Engine makes eligible queries free** and runs them on reserved capacity. It is built
for dashboards with a small, well-defined set of queries. It does not work on queries with
`GROUP BY` over a large table, or on unbounded scans.

### 7. Storage cost control

```sql
-- Expire old partitions automatically
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.raw.events`
PARTITION BY _PARTITIONDATE
OPTIONS(partition_expiration_days = 90);
```

```sql
-- Move cold data to long-term storage
ALTER TABLE `YOUR_PROJECT_ID.curated.archive_2024`
  SET OPTIONS(storage_billing_model = 'STORAGE_BILLING_MODEL_LONG_TERM');
```

```sql
-- Capacity-optimized tables: ~30% cheaper scans, ~2× the storage
CREATE TABLE `YOUR_PROJECT_ID.curated.orders_co`
PARTITION BY order_date
CLUSTER BY customer_id
OPTIONS(storage_billing_model = 'CAPACITY_OPTIMIZED');
```

| Model | Storage $/GiB/mo | Scan cost | Use when |
|-------|-----------------|-----------|----------|
| Standard | $0.02 | Full | Data is hot, scanned constantly |
| Capacity-optimized | $0.04 | ~30% of standard | Data is large, scanned occasionally |
| Long-term | $0.01 | Full | Archived, rarely scanned |

💡 **Capacity-optimized tables cost twice as much to store but ~70% less to scan.** They win
when a table is stored once and queried occasionally. They lose badly on hot data.

### 8. Use the query cache

```python
# First run: computes
job = client.query(sql, job_config=bigquery.QueryJobConfig(use_query_cache=True))
# Second run within 24h: cache_hit = True, zero bytes billed
```

```sql
-- Explicitly enable (it is on by default)
SELECT * FROM `t` OPTIONS(use_query_cache = TRUE);
```

💡 **The cache is per-project, per-user, and keyed on the query text.** It does not apply to
queries with a `destination` table, and it is bypassed by `use_query_cache = FALSE`.

### 9. Byte-counting views

```sql
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.monitoring.v_query_costs` AS
SELECT
  job_id,
  user_email,
  creation_time,
  total_bytes_processed,
  total_bytes_billed,
  ROUND(total_bytes_billed / POWER(1024, 4) * 6.25, 4) AS est_cost_usd,
  labels
FROM `YOUR_PROJECT_ID.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE job_type = 'QUERY'
  AND state = 'DONE'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY);
```

```sql
-- Top 20 most expensive queries in the last 30 days
SELECT
  ROUND(SUM(total_bytes_billed) / POWER(1024, 4) * 6.25, 2) AS total_cost_usd,
  COUNT(*) AS query_count,
  ANY_VALUE(user_email) AS user_email,
  ANY_VALUE(REGEXP_EXTRACT(job_id, r'job_[a-zA-Z0-9_-]+')) AS sample_job
FROM `YOUR_PROJECT_ID.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY user_email
ORDER BY total_cost_usd DESC
LIMIT 20;
```

### 10. The measurement-driven workflow

```python
"""
A/B two query formulations and compare scanned bytes.
"""
def compare(sql_a: str, sql_b: str, label_a="A", label_b="B") -> None:
    client = get_client()

    results = []
    for label, sql in ((label_a, sql_a), (label_b, sql_b)):
        job = client.query(
            sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        )
        tib = (job.total_bytes_processed or 0) / (1024**4)
        results.append((label, tib, tib * 6.25))

    print(f"{'Variant':<10} {'TiB':>10} {'Cost':>12}")
    print("-" * 34)
    for label, tib, cost in results:
        print(f"{label:<10} {tib:>10.4f} ${cost:>11.4f}")
```

### 11. Partition-aware incremental processing

```sql
-- ❌ Recomputes everything
CREATE OR REPLACE TABLE `mart.summary` AS
SELECT order_date, SUM(total_amount) FROM `curated.orders` GROUP BY 1;

-- ✅ Recomputes only what changed
MERGE `mart.summary` AS t
USING (
  SELECT order_date, SUM(total_amount) AS total
  FROM `curated.orders`
  WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  GROUP BY 1
) AS s
ON t.order_date = s.order_date
WHEN MATCHED THEN UPDATE SET t.total = s.total
WHEN NOT MATCHED THEN INSERT (order_date, total) VALUES (s.order_date, s.total);
```

### 12. Reduce DML cost

```sql
-- ❌ UPDATE rewrites the whole table
UPDATE `curated.orders` SET status = 'complete' WHERE order_date = '2026-01-15';

-- ✅ REPLACE PARTITION rewrites one partition
CREATE OR REPLACE TABLE `curated.orders$20260115` AS
SELECT * EXCEPT(status), 'complete' AS status FROM `curated.orders$20260115`;
```

💡 **`REPLACE PARTITION` is dramatically cheaper** than `UPDATE` when you are changing most
rows in a partition. The rule of thumb: if you change more than ~10% of a partition's rows,
replace the partition.

---

## 🛠️ Common Errors and Fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Query costs $200 | No partition filter | Add the filter; enable `require_partition_filter` |
| Query costs the same with fewer columns | `SELECT *` somewhere in a subquery | Project columns explicitly everywhere |
| MV not used by the dashboard | Query does not match the MV shape | Match the predicate and columns exactly |
| BI Engine says `unsupported` | Query has `GROUP BY` over a large table | Use an MV instead |
| Long-term move did not reduce cost | Move takes up to a few hours | Wait; check `storage_billing_model` |
| Capacity-optimized table is more expensive | Data is hot and scanned constantly | Switch back to standard |
| `UPDATE` on a 1 TB table took 20 minutes | Full table rewrite | Use `REPLACE PARTITION` or `MERGE` |
| Cache never hits | Query text varies, or cache disabled | Normalize the SQL; keep the cache on |

---

## 💡 Production Notes

- **Enable `require_partition_filter = TRUE` on every partitioned table.** It converts the
  most common BigQuery cost accident into a compile-time error.
- **Measure before optimising.** `INFORMATION_SCHEMA.JOBS_BY_PROJECT` tells you exactly where
  the bytes went.
- **Materialize the queries that run constantly** — a dashboard with 20 tiles hitting the same
  1 TB table is the textbook case.
- **Use `REPLACE PARTITION` instead of `UPDATE` for bulk changes** within a partition.
- **Column pruning is free.** There is no reason to `SELECT *` in production code.
- **Capacity-optimized tables for cold, large data; standard for hot data.** Never the reverse.
- **Long-term storage for anything you will not touch for 30+ days.**
- **Cache-friendly SQL.** Normalise whitespace and literals if you have a query that runs
  hundreds of times a day.
- **Set `maximum_bytes_billed` everywhere.** Even with a partition filter, a bad join can scan
  a lot.

---

## 🔑 Key Takeaways

- **Almost all optimization is "scan fewer bytes."**
- Partition filters first, then column pruning, then clustering, then MVs.
- **`require_partition_filter = TRUE`** prevents the expensive mistake.
- MVs: pre-aggregate, then query. BI Engine: reserve capacity for eligible dashboard queries.
- `REPLACE PARTITION` beats `UPDATE` for bulk changes inside a partition.
- Storage-optimized vs capacity-optimized vs long-term: pick per table, not per project.
- **Measure with `INFORMATION_SCHEMA.JOBS_BY_PROJECT`** — optimization without measurement is
  guesswork.

---

## 📚 Practice Exercises

1. **Optimize the worst query.** Find the three most expensive queries in the billing export.
   Rewrite each one to be cheaper. Show before/after bytes and the saving.

2. **MV design.** Take a dashboard with 12 tiles. Design the MV set. Include the base table
   restriction workaround for anything that needs a join. Show the storage cost and the scan
   reduction.

3. **Storage strategy.** Take a 40 TB dataset with 3 years of history and a 30-day hot window.
   Design the storage layout across standard, capacity-optimized, and long-term storage. Show
   the monthly cost under each strategy.

4. **DML benchmark.** Benchmark `UPDATE`, `MERGE`, and `REPLACE PARTITION` on a 100 GB
   partitioned table. Report time and bytes modified for each.

5. **Cost guardrail.** Build a decorator that dry-runs a query and raises if the estimated cost
   exceeds a threshold. Apply it to every query function in a pipeline. Prove it blocks a
   runaway query.

---

## 📖 Further Reading

- BigQuery best practices — https://cloud.google.com/bigquery/docs/best-practices
- Partitioned tables — https://cloud.google.com/bigquery/docs/partitioned-tables
- Clustered tables — https://cloud.google.com/bigquery/docs/clustered-tables
- Materialized views — https://cloud.google.com/bigquery/docs/materialized-view-intro
- BI Engine — https://cloud.google.com/bigquery/docs/bi-engine-intro
- Storage billing models — https://cloud.google.com/bigquery/docs/storage-billing-models
