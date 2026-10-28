-- =====================================================================
-- 03_queries_and_settings.sql
-- Course: BigQuery for Big Data Engineers
-- Covers: Chapters 15 (query settings & caching), 16 (wildcard tables),
--         17 (scheduled queries), 24-25 (execution plans)
--
-- Usage:
--   bq query --use_legacy_sql=false --dry_run < 03_queries_and_settings.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Query settings you can control
-- ---------------------------------------------------------------------

-- Maximum bytes billed — the query FAILS if it would exceed this
SELECT
  COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = DATE '2026-01-15'
/* BigQuery.config.query.maximum_bytes_billed = 1000000000 */;

-- Labels — every query gets tagged for cost attribution
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders`
/* BigQuery.config.query.labels = [{'tier': 'silver', 'env': 'dev'}] */;

-- Use the query cache (default is true)
/* BigQuery.config.query.use_query_cache = true */;

-- Maximum rows returned
SELECT *
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = DATE '2026-01-15'
/* BigQuery.config.query.maximum_rows_billed = 1000000 */;

-- Disable the cache for a "what would this cost right now" check
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = DATE '2026-01-15'
/* BigQuery.config.query.use_query_cache = false */;

-- ---------------------------------------------------------------------
-- 2. Parameters — never interpolate user input
-- ---------------------------------------------------------------------

DECLARE target_date DATE DEFAULT DATE '2026-01-15';
DECLARE min_amount NUMERIC DEFAULT 100;
DECLARE channel STRING DEFAULT 'web';

SELECT
  order_id,
  customer_id,
  total_amount
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = target_date
  AND total_amount >= min_amount
  AND source_channel = channel;

-- ---------------------------------------------------------------------
-- 3. Wildcard tables
-- ---------------------------------------------------------------------

-- Single wildcard: matches one character
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders_2026_01_1?`;

-- Multiple wildcards: matches any number of characters
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders_2026_*`;

-- The table_id pseudo-column tells you which file a row came from
SELECT
  _TABLE_ID AS source_table,
  COUNT(*) AS row_count,
  MIN(order_date) AS min_date,
  MAX(order_date) AS max_date
FROM `YOUR_PROJECT_ID.curated.orders_2026_*`
GROUP BY _TABLE_ID
ORDER BY source_table;

-- Wildcards work on partitioned tables too
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders$202601*`;

-- ---------------------------------------------------------------------
-- 4. Partition decorators
-- ---------------------------------------------------------------------

-- A single partition
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders$20260115`;

-- A range of partitions
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders$20260101:20260131`;

-- All partitions
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders$*`;

-- ---------------------------------------------------------------------
-- 5. The cache — when it hits and when it misses
-- ---------------------------------------------------------------------

-- Same query text within 24 hours -> cache hit, zero bytes billed
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = DATE '2026-01-15';

-- A query with a destination table NEVER uses the cache
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.mart.daily_orders` AS
SELECT * FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = DATE '2026-01-15';

-- ---------------------------------------------------------------------
-- 6. Reading the query cache and job history
-- ---------------------------------------------------------------------

SELECT
  job_id,
  creation_time,
  total_bytes_processed,
  total_bytes_billed,
  cache_hit,
  state,
  destination_table
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE job_type = 'QUERY'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
ORDER BY creation_time DESC
LIMIT 20;

-- ---------------------------------------------------------------------
-- 7. Most expensive queries in the last 30 days
-- ---------------------------------------------------------------------

SELECT
  user_email,
  COUNT(*) AS query_count,
  ROUND(SUM(total_bytes_billed) / POWER(1024, 4) * 6.25, 2) AS est_cost_usd,
  ROUND(AVG(total_bytes_billed) / POWER(1024, 4) * 6.25, 4) AS avg_cost_usd
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND state = 'DONE'
GROUP BY user_email
ORDER BY est_cost_usd DESC
LIMIT 20;

-- ---------------------------------------------------------------------
-- 8. Scheduled queries
-- ---------------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.jobs`
OPTIONS(location = "US", description = "Scheduled query targets");

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.jobs.daily_revenue` (
  order_date DATE,
  revenue   NUMERIC
)
OPTIONS(description = "Target table for the scheduled revenue query");

CREATE OR REPLACE SCHEDULED_QUERY
OPTIONS(
  enabled = TRUE,
  description = "Daily revenue rollup at 05:30 UTC",
  schedule = "30 5 * * *",
  time_zone = "UTC",
  expiration_time = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 365 DAY),
  max_retries = 3,
  destination_table = "YOUR_PROJECT_ID.jobs.daily_revenue",
  write_disposition = "WRITE_TRUNCATE",
  use_query_cache = TRUE,
  labels = [("tier", "gold"), ("owner", "data-eng")]
)
AS
SELECT
  order_date,
  SUM(total_amount) AS revenue
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
GROUP BY order_date;

-- Inspect scheduled queries
SELECT
  schedule_id,
  state,
  schedule,
  destination_table,
  creation_time
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.SCHEDULED_QUERIES
ORDER BY creation_time DESC;

-- ---------------------------------------------------------------------
-- 9. EXPLAIN — what the engine plans to do
-- ---------------------------------------------------------------------

EXPLAIN
SELECT order_date, SUM(total_amount) AS revenue
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = DATE '2026-01-15'
GROUP BY order_date;

-- ---------------------------------------------------------------------
-- 10. Common analytical patterns
-- ---------------------------------------------------------------------

-- Top-N per group using a window function
WITH ranked AS (
  SELECT
    customer_id,
    order_date,
    total_amount,
    ROW_NUMBER() OVER (
      PARTITION BY customer_id
      ORDER BY total_amount DESC
    ) AS rn
  FROM `YOUR_PROJECT_ID.curated.orders`
  WHERE order_date = DATE '2026-01-15'
)
SELECT * EXCEPT(rn) FROM ranked WHERE rn <= 3;

-- Running total
SELECT
  order_date,
  revenue,
  SUM(revenue) OVER (ORDER BY order_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM `YOUR_PROJECT_ID.mart.daily_revenue`
ORDER BY order_date;

-- Cohort retention
WITH cohorts AS (
  SELECT
    customer_id,
    DATE_TRUNC(MONTH, MIN(order_date)) AS cohort_month
  FROM `YOUR_PROJECT_ID.curated.orders`
  GROUP BY customer_id
),
activity AS (
  SELECT DISTINCT
    customer_id,
    DATE_TRUNC(MONTH, order_date) AS activity_month
  FROM `YOUR_PROJECT_ID.curated.orders`
  GROUP BY customer_id, activity_month
)
SELECT
  c.cohort_month,
  a.activity_month,
  DATE_DIFF(a.activity_month, c.cohort_month, MONTH) AS month_number,
  COUNT(*) AS retained_customers
FROM cohorts c
JOIN activity a USING (customer_id)
GROUP BY c.cohort_month, a.activity_month, month_number
ORDER BY c.cohort_month, month_number;
