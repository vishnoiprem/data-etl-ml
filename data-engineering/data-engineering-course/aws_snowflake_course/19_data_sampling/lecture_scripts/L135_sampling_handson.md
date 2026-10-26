---
l_id: L135
title: Sampling data: Hands-on
duration: "6:00"
prereqs: ["L134"]
---

# L135 — Sampling data: Hands-on

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 19 — Data Sampling
> **Duration:** 6:00

## Prereqs

L134 — Methods of data sampling.

## Key terms

- **TPC-H** — a standard analytics benchmark. Snowflake publishes
  a small TPC-H dataset in `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`
  (1 GB scale factor, ~6M rows in `ORDERS`).
- **Sample fraction** — the percent of rows to include. Common
  values: 0.1, 1, 10.
- **Estimate vs ground truth** — a sample's aggregation is an
  estimate; the full table's is the ground truth. The difference
  shrinks as the sample grows.

## Lecture

Welcome back. This is the hands-on for the section. We use
Snowflake's free sample dataset (`SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`)
to show, end-to-end, that sampled aggregations are close to
ground truth — and what the residual error looks like in practice.

### The setup

```sql
USE SCHEMA SNOWFLAKE_SAMPLE_DATA.TPCH_SF1;

-- Ground truth
SELECT COUNT(*)                  AS total_rows,
       SUM(O_TOTALPRICE)         AS total_revenue,
       AVG(O_TOTALPRICE)         AS avg_order
FROM   ORDERS;
```

Write down the three numbers. We'll sample and compare.

### A 1% sample

```sql
SELECT COUNT(*)                  AS sample_rows,
       SUM(O_TOTALPRICE)         AS sample_revenue,
       AVG(O_TOTALPRICE)         AS sample_avg
FROM   ORDERS SAMPLE BERNOULLI (1);
```

You should see roughly 1% of the row count, and the `SUM` should
be within a few percent of the ground truth. The `AVG` should be
*very* close to ground truth, because averages are less sensitive
to sample size than totals.

### A 0.1% sample (still meaningful)

```sql
SELECT COUNT(*)                  AS sample_rows,
       SUM(O_TOTALPRICE)         AS sample_revenue,
       AVG(O_TOTALPRICE)         AS sample_avg
FROM   ORDERS SAMPLE BERNOULLI (0.1);
```

At 0.1% (~6,000 rows), `AVG` is still close to ground truth; `SUM`
is a noisier estimate.

### Slicing by region

Combine `SAMPLE` with a `WHERE` to slice:

```sql
SELECT O_ORDERSTATUS, COUNT(*) AS cnt
FROM   ORDERS SAMPLE BERNOULLI (1)
WHERE  O_ORDERSTATUS IN ('O', 'F')
GROUP BY O_ORDERSTATUS;
```

The filter runs first, then the sample. This is the right order
for stratified-like analysis.

### Persisting a sample for test/dev

```sql
-- Create a 1% sample table for dev
CREATE OR REPLACE TRANSIENT TABLE DEV_DB.PUBLIC.ORDERS_DEV AS
  SELECT * FROM ORDERS SAMPLE BERNOULLI (1);

-- Or zero-copy, even cleaner:
CREATE OR REPLACE TRANSIENT TABLE DEV_DB.PUBLIC.ORDERS_DEV CLONE ORDERS
  -- Note: CLONE copies the whole table; for sampling, use CREATE AS
  ;
```

For an actual sample table, use `CREATE TABLE ... AS SELECT ...
SAMPLE ...`. Transient is the right type — no Fail Safe, no
retention overhead.

### Comparing SYSTEM vs BERNOULLI

Run the same query with each method and time them:

```sql
-- SYSTEM (block-level, faster)
SELECT COUNT(*) FROM ORDERS SAMPLE SYSTEM (1);

-- BERNOULLI (per-row, slower but uniform)
SELECT COUNT(*) FROM ORDERS SAMPLE BERNOULLI (1);
```

Use the *Query history* tab in Snowsight to compare runtimes. On
the TPC-H 1GB dataset, `SYSTEM` is typically 2–4× faster than
`BERNOULLI`. On multi-TB tables the difference is larger.

## Hands-on

```sql
-- 1. Ground truth
SELECT COUNT(*) AS total FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS;

-- 2. 1% sample
SELECT COUNT(*) AS sample_1pct
FROM   SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS SAMPLE BERNOULLI (1);

-- 3. Create a persistent sample table
CREATE OR REPLACE TRANSIENT TABLE DEMO_DB.PUBLIC.ORDERS_1PCT AS
  SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS SAMPLE BERNOULLI (1);

-- 4. Compare aggregation
SELECT 'ground_truth' AS src, COUNT(*) AS rows, SUM(O_TOTALPRICE) AS revenue
FROM   SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS
UNION ALL
SELECT 'sample_1pct',     COUNT(*),       SUM(O_TOTALPRICE)
FROM   DEMO_DB.PUBLIC.ORDERS_1PCT;
```

## Key takeaways

- TPC-H is the standard benchmark; Snowflake ships a 1 GB version
  for free.
- A 1% sample gives a `SUM` within a few percent of ground truth.
- `SYSTEM` is faster; `BERNOULLI` is more uniform.
- Use `CREATE TRANSIENT TABLE ... AS SELECT ... SAMPLE ...` to
  persist a sample for test/dev.

## What's next

Section 20 is **Extra topics** — 57 lectures on Tasks, Streams,
Materialized Views, Data Masking, Roles deep-dive, BI Tools, Best
Practices, and Bonus material. The largest section of the course.