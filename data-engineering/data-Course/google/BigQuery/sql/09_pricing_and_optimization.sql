-- =====================================================================
-- 09_pricing_and_optimization.sql
-- Course: BigQuery for Big Data Engineers
-- Covers: Chapters 51 (pricing models), 52 (cost optimization)
--
-- Usage:
--   bq query --use_legacy_sql=false --dry_run < 09_pricing_and_optimization.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Build a query cost tracker
-- ---------------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.monitoring`
OPTIONS(location = "US", description = "Cost and performance monitoring");

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.monitoring.query_costs` (
  query_id            STRING,
  run_at              TIMESTAMP,
  user_email          STRING,
  job_name            STRING,
  total_bytes_processed INT64,
  total_bytes_billed  INT64,
  est_cost_usd        FLOAT64,
  cache_hit           BOOL,
  duration_ms         INT64,
  labels              JSON
)
PARTITION BY DATE(run_at)
OPTIONS(
  description = "Query cost audit log",
  partition_expiration_days = 90
);

-- ---------------------------------------------------------------------
-- 2. The top-20 most expensive queries in the last 30 days
-- ---------------------------------------------------------------------

SELECT
  ANY_VALUE(user_email) AS user_email,
  ANY_VALUE(job_id) AS sample_job_id,
  COUNT(*) AS query_count,
  ROUND(SUM(total_bytes_billed) / POWER(1024, 4) * 6.25, 2) AS total_cost_usd,
  ROUND(AVG(total_bytes_billed) / POWER(1024, 4) * 6.25, 4) AS avg_cost_usd,
  ROUND(MAX(total_bytes_billed) / POWER(1024, 4) * 6.25, 4) AS max_cost_usd
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE job_type = 'QUERY'
  AND state = 'DONE'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY user_email
ORDER BY total_cost_usd DESC
LIMIT 20;

-- ---------------------------------------------------------------------
-- 3. Cost by label (cost attribution)
-- ---------------------------------------------------------------------

SELECT
  labels.tier AS tier,
  labels.env AS env,
  COUNT(*) AS query_count,
  ROUND(SUM(total_bytes_billed) / POWER(1024, 4) * 6.25, 2) AS cost_usd
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE job_type = 'QUERY'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY tier, env
ORDER BY cost_usd DESC;

-- ---------------------------------------------------------------------
-- 4. Cache hit rate
-- ---------------------------------------------------------------------

SELECT
  ROUND(100 * COUNTIF(cache_hit) / COUNT(*), 2) AS cache_hit_pct,
  COUNT(*) AS total_queries,
  ROUND(SUM(IF(cache_hit, 0, total_bytes_billed)) / POWER(1024, 4) * 6.25, 2) AS cost_usd
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE job_type = 'QUERY'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY);

-- ---------------------------------------------------------------------
-- 5. Full table scans — the queries to fix first
-- ---------------------------------------------------------------------

SELECT
  job_id,
  user_email,
  ROUND(total_bytes_billed / POWER(1024, 4) * 6.25, 4) AS cost_usd,
  ROUND(total_bytes_billed / POWER(1024, 3), 1) AS billed_mb,
  creation_time
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE job_type = 'QUERY'
  AND total_bytes_billed > 10737418240   -- more than 10 GiB
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
ORDER BY total_bytes_billed DESC
LIMIT 50;

-- ---------------------------------------------------------------------
-- 6. Storage cost by dataset
-- ---------------------------------------------------------------------

SELECT
  table_schema AS dataset,
  COUNT(*) AS table_count,
  ROUND(SUM(size_bytes) / POWER(1024, 3), 2) AS size_gb,
  ROUND(SUM(size_bytes) / POWER(1024, 3) * 0.02, 2) AS est_monthly_storage_cost_usd,
  ROUND(SUM(row_count) / 1e6, 2) AS total_rows
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.TABLE_STORAGE
GROUP BY dataset
ORDER BY size_gb DESC;

-- ---------------------------------------------------------------------
-- 7. Storage billing models — set them
-- ---------------------------------------------------------------------

-- Move a cold table to long-term storage (half the price)
ALTER TABLE `YOUR_PROJECT_ID.curated.archive_2024`
  SET OPTIONS (storage_billing_model = 'STORAGE_BILLING_MODEL_LONG_TERM');

-- Switch to capacity-optimized (2x storage, ~30% cheaper scans)
ALTER TABLE `YOUR_PROJECT_ID.curated.orders_co`
  SET OPTIONS (storage_billing_model = 'CAPACITY_OPTIMIZED');

-- Back to standard
ALTER TABLE `YOUR_PROJECT_ID.curated.orders_co`
  SET OPTIONS (storage_billing_model = 'STORAGE_BILLING_MODEL_STANDARD');

-- ---------------------------------------------------------------------
-- 8. Partition expiration — the cheapest cost control
-- ---------------------------------------------------------------------

ALTER TABLE `YOUR_PROJECT_ID.raw.events`
  SET OPTIONS (partition_expiration_days = 90);

ALTER TABLE `YOUR_PROJECT_ID.staging.orders`
  SET OPTIONS (partition_expiration_days = 30);

-- Set a dataset-wide default for new tables
ALTER SCHEMA `YOUR_PROJECT_ID.scratch`
  SET OPTIONS (default_table_expiration_days = 7);

-- ---------------------------------------------------------------------
-- 9. require_partition_filter — prevent the expensive mistake
-- ---------------------------------------------------------------------

ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
  SET OPTIONS (require_partition_filter = TRUE);

-- ---------------------------------------------------------------------
-- 10. BI Engine — reserved capacity for the dashboard
-- ---------------------------------------------------------------------

CREATE BI ENGINE RESERVATION
  `YOUR_PROJECT_ID.BI_RESERVATION`
OPTIONS(
  edition = "ENTERPRISE",
  capacity_bi_units = 1024.0,
  timeout_ms = 3600000
);

-- Attach a table
ALTER TABLE `YOUR_PROJECT_ID.mart.daily_revenue`
  SET OPTIONS (enable_bi_engine = TRUE);

-- Detach
ALTER TABLE `YOUR_PROJECT_ID.mart.daily_revenue`
  SET OPTIONS (enable_bi_engine = FALSE);

-- Check the status
SELECT
  t.table_name,
  t.bi_engine_status,
  r.reservation_name
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.TABLES AS t
LEFT JOIN `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.BI_CAPACITIES AS r
  USING (project_id, dataset_id)
WHERE t.bi_engine_status IS NOT NULL;

-- ---------------------------------------------------------------------
-- 11. A query review query — flag expensive patterns
-- ---------------------------------------------------------------------

SELECT
  job_id,
  user_email,
  ROUND(total_bytes_billed / POWER(1024, 4) * 6.25, 4) AS cost_usd,
  REGEXP_EXTRACT(statement, r'FROM\s+`([^`]+)`') AS table_scanned,
  IF(REGEXP_CONTAINS(statement, r'WHERE'), 'has_where', 'NO_WHERE_CLAUSE') AS where_status,
  IF(REGEXP_CONTAINS(statement, r'SELECT\s+\*'), 'SELECT_STAR', 'specific_columns') AS column_status,
  creation_time
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE job_type = 'QUERY'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND total_bytes_billed > 1073741824
  AND (NOT REGEXP_CONTAINS(statement, r'WHERE')
       OR REGEXP_CONTAINS(statement, r'SELECT\s+\*'))
ORDER BY total_bytes_billed DESC;

-- ---------------------------------------------------------------------
-- 12. Partition pruning verification
-- ---------------------------------------------------------------------

SELECT
  job_id,
  total_partitions_scanned,
  ROUND(total_bytes_billed / POWER(1024, 4) * 6.25, 4) AS cost_usd,
  creation_time
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE job_type = 'QUERY'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
ORDER BY total_partitions_scanned DESC
LIMIT 20;

-- ---------------------------------------------------------------------
-- 13. Before / after optimisation comparison
-- ---------------------------------------------------------------------

-- BEFORE: full scan + SELECT *
SELECT COUNT(*) AS rows_before
FROM `YOUR_PROJECT_ID.curated.orders`;

-- AFTER: pruned + specific columns
SELECT
  COUNT(*) AS rows_after,
  ROUND(SUM(total_amount), 2) AS revenue
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date BETWEEN DATE '2026-01-01' AND DATE '2026-01-31';

-- The byte comparison, side by side
SELECT
  'full_scan' AS variant,
  ROUND((SELECT total_bytes_billed FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
         WHERE statement_type LIKE '%COUNT(*) AS rows_before%' ORDER BY creation_time DESC LIMIT 1)
        / POWER(1024, 4) * 6.25, 4) AS cost_usd
UNION ALL
SELECT
  'pruned' AS variant,
  ROUND((SELECT total_bytes_billed FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
         WHERE statement_type LIKE '%rows_after%' ORDER BY creation_time DESC LIMIT 1)
        / POWER(1024, 4) * 6.25, 4);

-- ---------------------------------------------------------------------
-- 14. The daily cost report
-- ---------------------------------------------------------------------

WITH daily AS (
  SELECT
    DATE(creation_time) AS day,
    SUM(total_bytes_billed) AS bytes_billed,
    COUNT(*) AS query_count
  FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
  WHERE job_type = 'QUERY'
    AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  GROUP BY day
)
SELECT
  day,
  query_count,
  ROUND(bytes_billed / POWER(1024, 4), 2) AS tib_billed,
  ROUND(bytes_billed / POWER(1024, 4) * 6.25, 2) AS est_cost_usd,
  ROUND(AVG(bytes_billed) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
        / POWER(1024, 4) * 6.25, 2) AS moving_avg_7d_cost_usd
FROM daily
ORDER BY day DESC;

-- ---------------------------------------------------------------------
-- 15. Reserved capacity monitoring
-- ---------------------------------------------------------------------

SELECT
  reservation_name,
  slot_ms,
  ROUND(slot_ms / 3600000.0, 1) AS slot_hours,
  ROUND(slot_ms / 3600000.0 * 0.04, 2) AS capacity_cost_usd
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.RESERVATIONS
ORDER BY slot_hours DESC;
