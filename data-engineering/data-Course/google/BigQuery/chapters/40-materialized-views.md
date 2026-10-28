# 5.4 — Materialized Views

> **Section 5 · External Data, Views & Materialized Views · Lectures 5.7–5.11 · 4:25 + 7:50 + 2:12 + 4:13 + 7:21**

## 🎯 What you will learn

- How materialized views differ from logical views
- The complete limitations and quotas
- `max_staleness`, auto-refresh, and manual refresh
- How to design a query that a materialized view can accelerate
- The real-world cost-benefit

---

## 🧠 Concept

A **materialized view** stores the results of a query. Unlike a logical view, it holds data.

### Logical view vs materialized view

| | Logical view | Materialized view |
|---|---|---|
| **Stores data** | ❌ No | ✅ Yes |
| **Query cost** | Same as base table | **Much lower** |
| **Storage cost** | None | Yes |
| **Refresh** | N/A — always fresh | Manual or automatic |
| **Freshness** | Always current | Up to `max_staleness` |
| **Can be partitioned** | ❌ | ✅ |
| **Can be clustered** | ❌ | ✅ |
| **Supports aggregations** | ✅ | ✅ (with restrictions) |
| **Source must be** | Any table | **A single base table** |

💡 **A materialized view is the answer to "this aggregate query is expensive and I run it 500 times
a day."** It trades a little storage and some staleness for a large query-cost reduction.

---

## 🧠 The Critical Design Constraint

**A materialized view can only be created from a single base table.** This is the most common
reason an MV creation fails.

```sql
-- ❌ FAILS: two base tables
CREATE MATERIALIZED VIEW `YOUR_PROJECT_ID.mart.mv_revenue_by_region` AS
SELECT c.region, SUM(o.total_amount) AS revenue
FROM `YOUR_PROJECT_ID.curated.orders` o
JOIN `YOUR_PROJECT_ID.curated.customers` c USING (customer_id)
GROUP BY c.region;
-- Error: Materialized view creation is not supported for a query with multiple base tables
```

### The workaround: aggregate first, then join

```sql
-- ✅ Step 1: MV over a single base table
CREATE MATERIALIZED VIEW `YOUR_PROJECT_ID.mart.mv_customer_daily_revenue`
PARTITION BY order_date
CLUSTER BY customer_id
OPTIONS (
  max_staleness = INTERVAL 1 HOUR,
  enable_refresh = TRUE
)
AS
SELECT
    order_date,
    customer_id,
    SUM(total_amount) AS revenue,
    COUNT(*) AS order_count
FROM `YOUR_PROJECT_ID.curated.orders`
GROUP BY order_date, customer_id;
```

```sql
-- ✅ Step 2: a logical view joins the MV to the dimension
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.mart.v_revenue_by_region` AS
SELECT
    c.region,
    SUM(mv.revenue) AS revenue,
    SUM(mv.order_count) AS order_count
FROM `YOUR_PROJECT_ID.mart.mv_customer_daily_revenue` mv
JOIN `YOUR_PROJECT_ID.curated.customers` c USING (customer_id)
GROUP BY c.region;
```

💡 **This two-layer pattern is the standard BigQuery materialized-view architecture**: MVs
aggregate one base table; views join MVs to dimensions.

### Aggregate function restrictions

| Function | Supported in an MV? |
|----------|---------------------|
| `SUM`, `COUNT`, `MIN`, `MAX`, `AVG` | ✅ |
| `COUNT(DISTINCT)` | ✅ (with caveats) |
| `ARRAY_AGG`, `ARRAY_CONCAT_AGG` | ✅ |
| `STRING_AGG` | ✅ |
| `APPROX_COUNT_DISTINCT` | ✅ |
| `ANY_VALUE` | ✅ |
| `BIT_AND`/`BIT_OR`/`BIT_XOR` | ✅ |
| `LOGICAL_AND`/`LOGICAL_OR` | ✅ |
| Window functions | ❌ |
| `GROUP BY` on a non-grouped expression | ❌ |
| `LIMIT`/`OFFSET` | ❌ |
| `HAVING` | ❌ |
| `ORDER BY` | ❌ |

---

## 🧠 Refresh Behaviour

### Automatic refresh

```sql
CREATE MATERIALIZED VIEW `YOUR_PROJECT_ID.mart.mv_customer_daily_revenue`
PARTITION BY order_date
CLUSTER BY customer_id
OPTIONS (
  enable_refresh = TRUE,             -- automatic refresh enabled
  max_staleness = INTERVAL 1 HOUR,   -- refresh at least hourly
  refresh_interval_minutes = 60
)
AS
SELECT
    order_date,
    customer_id,
    SUM(total_amount) AS revenue,
    COUNT(*) AS order_count
FROM `YOUR_PROJECT_ID.curated.orders`
GROUP BY order_date, customer_id;
```

| Option | Meaning |
|--------|---------|
| `enable_refresh` | `TRUE` = automatic refresh; `FALSE` = manual only |
| `max_staleness` | Maximum staleness before a query on the MV triggers a refresh |
| `refresh_interval_minutes` | How often the refresh job runs |

💡 **`max_staleness` is the key to correctness.** When a query hits an MV that is staler than
`max_staleness`, BigQuery refreshes it (or blocks waiting for the refresh) before returning
results. This gives you near-real-time freshness without manual orchestration.

### Manual refresh

```sql
-- Refresh now
CALL YOUR_PROJECT_ID.mart.BQ.REFRESH_MATERIALIZED_VIEW(
    'YOUR_PROJECT_ID.mart.mv_customer_daily_revenue'
);
```

```bash
# Via the CLI
bq query --use_legacy_sql=false \
  'CALL `YOUR_PROJECT_ID.mart.BQ.REFRESH_MATERIALIZED_VIEW`("YOUR_PROJECT_ID.mart.mv_customer_daily_revenue")'
```

```python
# Via Python
from google.cloud import bigquery

client = bigquery.Client()
job = client.query(
    "CALL `YOUR_PROJECT_ID.mart.BQ.REFRESH_MATERIALIZED_VIEW`"
    "('YOUR_PROJECT_ID.mart.mv_customer_daily_revenue')"
)
job.result()
print("Refreshed")
```

### The staleness trade-off

| `max_staleness` | Freshness | Refresh cost | Query cost |
|-----------------|-----------|--------------|------------|
| `INTERVAL 0 HOUR` | Always fresh | Refresh on every query | Higher |
| `INTERVAL 1 HOUR` | Up to 1 hour | Hourly | Low |
| `INTERVAL 24 HOUR` | Up to 1 day | Daily | Lowest |
| Not set | May be arbitrarily stale | No auto-refresh | Lowest |

💡 **Start with `INTERVAL 1 HOUR`** and tighten only if a stakeholder requires it. Every
tightening multiplies refresh cost.

---

## 🛠️ Hands-On

### 1. Create a materialized view

```sql
CREATE MATERIALIZED VIEW `YOUR_PROJECT_ID.mart.mv_daily_customer_revenue`
PARTITION BY order_date
CLUSTER BY customer_id
OPTIONS (
  description = "Daily revenue per customer, refreshed hourly",
  max_staleness = INTERVAL 1 HOUR,
  enable_refresh = TRUE,
  refresh_interval_minutes = 60,
  labels = [('tier', 'gold'), ('owner', 'analytics-eng')]
)
AS
SELECT
    order_date,
    customer_id,
    SUM(total_amount) AS revenue,
    COUNT(*) AS order_count,
    AVG(total_amount) AS avg_order_value,
    COUNT(DISTINCT status) AS distinct_statuses
FROM `YOUR_PROJECT_ID.curated.orders`
GROUP BY order_date, customer_id;
```

### 2. Query it and compare the cost

```sql
-- The original query
SELECT
    order_date, customer_id, SUM(total_amount) AS revenue, COUNT(*) AS order_count
FROM `YOUR_PROJECT_ID.curated.orders`
GROUP BY order_date, customer_id;

-- The materialized view
SELECT order_date, customer_id, revenue, order_count
FROM `YOUR_PROJECT_ID.mart.mv_daily_customer_revenue`;
```

```sql
-- Compare
SELECT
    CASE
        WHEN query LIKE '%mv_daily_customer_revenue%' THEN 'materialized_view'
        ELSE 'base_table'
    END AS source,
    ROUND((total_bytes_processed / POW(1024, 3)), 2) AS mb_processed,
    ROUND((total_bytes_processed / POW(1024, 4)) * 6.25, 4) AS est_cost_usd,
    ROUND(total_slot_ms / 1000, 2) AS slot_seconds
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE (query LIKE '%mv_daily_customer_revenue%' OR query LIKE '%curated.orders%')
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY creation_time DESC;
```

### 3. Inspect the MV

```sql
-- Metadata
SELECT
    table_name,
    table_type,
    creation_time,
    ROUND(size_bytes / POW(1024, 3), 2) AS size_gb
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.TABLES`
WHERE table_name = 'mv_daily_customer_revenue';

-- The MV definition
SELECT table_name, view_definition
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.VIEWS`
WHERE table_name = 'mv_daily_customer_revenue';

-- Refresh history
SELECT
    table_name,
    refresh_time,
    error_count,
    REFRESH_STATUS_TEXT AS status,
    total_live_rows,
    total_logical_bytes
FROM `YOUR_PROJECT_ID.mart.INFORMATION_SCHEMA.MATERIALIZED_VIEW_REFRESH_HISTORY`
ORDER BY refresh_time DESC
LIMIT 20;
```

### 4. The MV + view pattern

```sql
-- The MV: aggregate over one table
CREATE MATERIALIZED VIEW `YOUR_PROJECT_ID.mart.mv_customer_daily_revenue`
PARTITION BY order_date
CLUSTER BY customer_id
OPTIONS (max_staleness = INTERVAL 1 HOUR, enable_refresh = TRUE)
AS
SELECT
    order_date,
    customer_id,
    SUM(total_amount) AS revenue,
    COUNT(*) AS order_count
FROM `YOUR_PROJECT_ID.curated.orders`
GROUP BY order_date, customer_id;

-- The view: join the MV to dimensions
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.mart.v_revenue_by_region` AS
SELECT
    c.region,
    SUM(mv.revenue) AS revenue,
    SUM(mv.order_count) AS order_count,
    ROUND(SUM(mv.revenue) / COUNT(DISTINCT mv.customer_id), 2) AS revenue_per_customer
FROM `YOUR_PROJECT_ID.mart.mv_customer_daily_revenue` mv
JOIN `YOUR_PROJECT_ID.curated.customers` c USING (customer_id)
WHERE mv.order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY c.region;
```

### 5. Manual refresh

```sql
CALL YOUR_PROJECT_ID.mart.BQ.REFRESH_MATERIALIZED_VIEW(
    'YOUR_PROJECT_ID.mart.mv_customer_daily_revenue'
);
```

### 6. Altering an MV

```sql
-- Change the refresh settings (cheap)
ALTER MATERIALIZED VIEW `YOUR_PROJECT_ID.mart.mv_customer_daily_revenue`
SET OPTIONS (max_staleness = INTERVAL 30 MINUTE);

-- Change the query definition — this REBUILDS the MV
ALTER MATERIALIZED VIEW `YOUR_PROJECT_ID.mart.mv_customer_daily_revenue` AS
SELECT
    order_date,
    customer_id,
    SUM(total_amount) AS revenue,
    COUNT(*) AS order_count,
    COUNTIF(status = 'refunded') AS refund_count   -- new column
FROM `YOUR_PROJECT_ID.curated.orders`
GROUP BY order_date, customer_id;
```

⚠️ **Changing the MV's query rebuilds it** — a full recompute. Changing only `max_staleness` or
`enable_refresh` is cheap.

---

## ⚠️ Limitations & Quotas

| Limitation | Detail |
|------------|--------|
| **Single base table** | ❌ Cannot join multiple tables |
| **No `GROUP BY` on arbitrary expressions** | ❌ Limited |
| **No window functions** | ❌ |
| **No `HAVING`, `LIMIT`, `OFFSET`** | ❌ |
| **No `ORDER BY`** | ❌ |
| **Source must be a managed table** | ❌ Cannot be an external table |
| **Cannot reference a view** | ❌ The source must be a physical table |
| **Cannot reference another MV** | ❌ |
| **Max columns** | 500 (table limit) |
| **Max MVs per dataset** | Limited by quota |
| **Refresh job counts as a query job** | 💰 Costs money |
| **Storage cost** | 💰 The MV's data is billed |

💡 **MV refresh jobs are billed as queries.** An MV over a 10 TB table refreshed hourly costs
`10 TB × 24 × $6.25/TiB ≈ $1,500/month` in refresh fees alone. Always measure this.

---

## 💡 Production Notes

- **Create an MV only when the base query is expensive AND run frequently.** A query run twice a
  day does not justify an MV.
- **The refresh cost can exceed the query savings.** Always compare: total refresh cost vs
  (baseline query cost × number of queries avoided).
- **One base table per MV.** Design your base tables so the aggregations you need are possible
  on a single table.
- **Use `max_staleness` rather than aggressive refresh intervals** — it lets BigQuery skip
  unnecessary refreshes when nobody is querying.
- **Partition and cluster the MV.** Otherwise you are trading one slow query for another.
- **Monitor `MATERIALIZED_VIEW_REFRESH_HISTORY`** for refresh failures — a failing MV silently
  serves stale data.

---

## 🔑 Key Takeaways

- A materialized view **stores data**; a logical view does not.
- **One base table per MV** — the most important constraint. Use the MV + view pattern for joins.
- `max_staleness` controls freshness; `enable_refresh` controls automation.
- **Refresh jobs cost money** — an hourly refresh over 10 TB is ~$1,500/month.
- MVs cannot be created over external tables, views, or other MVs.
- Partition and cluster the MV itself.

---

## 📚 Practice Exercises

1. **MV business case.** A dashboard runs the same 5 TB aggregate 800 times/day. Compute the
   cost with and without an MV, including the MV's refresh cost and storage. Should they build it?

2. **MV + view architecture.** Design a materialized-view hierarchy for a retail business that
   needs: daily revenue by product, monthly revenue by region, and customer segment performance.
   Show which are MVs and which are views, and why.

3. **Restriction discovery.** Write queries that attempt to create MVs with: a join, a window
   function, a `HAVING` clause, a `LIMIT`, and an external table source. Record each error.

4. **Refresh economics.** Create an MV over a table, measure the cost of one manual refresh, and
   calculate the monthly cost at hourly, 6-hourly, and daily refresh intervals. Compare against
   the query cost saved.

5. **Staleness policy.** Design a staleness policy per metric: revenue (needs to be fresh),
   monthly cohort analysis (can be a day old), and historical aggregates (can be a week old).
   Justify each with the business impact of staleness.

---

## 📖 Further Reading

- Materialized views — https://cloud.google.com/bigquery/docs/materialized-views-intro
- Materialized view limitations — https://cloud.google.com/bigquery/docs/materialized-views-limitations
- Refresh history — https://cloud.google.com/bigquery/docs/information-schema-materialized-view-refresh-history
- `REFRESH_MATERIALIZED_VIEW` — https://cloud.google.com/bigquery/docs/reference/standard-sql/procedural-language
