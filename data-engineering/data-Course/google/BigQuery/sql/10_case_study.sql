-- =====================================================================
-- 10_case_study.sql
-- Course: BigQuery for Big Data Engineers
-- Covers: Chapters 46 (case study), 47-48 (Beam + Airflow),
--         49-50 (Pub/Sub + streaming)
--
-- The complete RetailMart pipeline: raw -> staging -> curated -> mart,
-- plus the data quality gate.
--
-- Usage:
--   bq query --use_legacy_sql=false --dry_run < 10_case_study.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. The full storage layout
-- ---------------------------------------------------------------------

-- raw: ingestion-time partitioned, immutable
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.retailmart.raw.app_orders` (
  order_id     STRING    NOT NULL,
  customer_id  STRING    NOT NULL,
  order_ts     TIMESTAMP NOT NULL,
  order_date   DATE      NOT NULL,
  channel      STRING    NOT NULL,
  region       STRING    NOT NULL,
  currency     STRING    NOT NULL,
  amount_local NUMERIC   NOT NULL,
  status       STRING    NOT NULL,
  line_count   INTEGER   NOT NULL,
  ingested_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
PARTITION BY _PARTITIONDATE
OPTIONS(
  description = "Raw app orders, streamed from Pub/Sub",
  partition_expiration_days = 730,
  labels = [("tier", "raw"), ("owner", "data-eng"), ("domain", "sales")]
);

-- raw.pos_orders: batch-loaded from GCS
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.retailmart.raw.pos_orders` (
  order_id     STRING    NOT NULL,
  store_id     STRING    NOT NULL,
  order_ts     TIMESTAMP NOT NULL,
  order_date   DATE      NOT NULL,
  currency     STRING    NOT NULL,
  amount_local NUMERIC   NOT NULL,
  status       STRING    NOT NULL,
  line_count   INTEGER   NOT NULL,
  ingested_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
PARTITION BY order_date
OPTIONS(
  description = "Raw POS orders, batch loaded from the legacy system",
  partition_expiration_days = 730,
  require_partition_filter = TRUE
);

-- raw.fx_rates: reference data
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.retailmart.raw.fx_rates` (
  rate_date   DATE   NOT NULL,
  currency    STRING NOT NULL,
  rate_to_eur NUMERIC,
  source      STRING
)
OPTIONS(description = "Daily FX rates to EUR");

-- staging: cleaned, business-date partitioned
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.retailmart.staging.orders` (
  order_id      STRING    NOT NULL,
  customer_id   STRING    NOT NULL,
  order_ts      TIMESTAMP NOT NULL,
  order_date    DATE      NOT NULL,
  channel       STRING    NOT NULL,
  region        STRING    NOT NULL,
  currency      STRING    NOT NULL,
  amount_local  NUMERIC   NOT NULL,
  status        STRING    NOT NULL,
  line_count    INTEGER   NOT NULL,
  source_system STRING    NOT NULL,
  ingested_at   TIMESTAMP NOT NULL
)
PARTITION BY order_date
OPTIONS(
  description = "Conformed staging orders from all sources",
  partition_expiration_days = 30,
  labels = [("tier", "silver"), ("owner", "data-eng")]
);

-- curated: the conformed model
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.retailmart.curated.orders` (
  order_id      STRING    NOT NULL,
  customer_id   STRING    NOT NULL,
  order_ts      TIMESTAMP NOT NULL,
  order_date    DATE      NOT NULL,
  channel       STRING    NOT NULL,
  region        STRING    NOT NULL,
  currency      STRING    NOT NULL,
  amount_local  NUMERIC   NOT NULL,
  amount_eur    NUMERIC   NOT NULL,
  status        STRING    NOT NULL,
  line_count    INTEGER   NOT NULL,
  source_system STRING    NOT NULL,
  ingested_at   TIMESTAMP NOT NULL
)
PARTITION BY order_date
CLUSTER BY customer_id, channel
OPTIONS(
  description = "Conformed orders, EUR-normalised",
  partition_expiration_days = 1825,
  require_partition_filter = TRUE,
  labels = [("tier", "curated"), ("owner", "data-eng"), ("domain", "sales")]
);

-- mart: the serving layer
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.retailmart.mart.daily_revenue` (
  order_date      DATE NOT NULL,
  region          STRING NOT NULL,
  channel         STRING NOT NULL,
  order_count     INT64 NOT NULL,
  customer_count  INT64 NOT NULL,
  revenue_eur     NUMERIC NOT NULL,
  aov_eur         NUMERIC,
  order_count_7d  INT64,
  revenue_eur_7d  NUMERIC
)
PARTITION BY order_date
CLUSTER BY region
OPTIONS(
  description = "Daily revenue serving table",
  partition_expiration_days = 1095,
  labels = [("tier", "gold"), ("owner", "analytics-eng")]
);

-- ---------------------------------------------------------------------
-- 2. Stage 1: conform raw -> staging
-- ---------------------------------------------------------------------

-- This is what the Airflow "daily_conform" task runs.
-- It is parameterised by target_date, which is what makes backfills work.
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.retailmart.staging.orders` AS
SELECT
  order_id,
  customer_id,
  order_ts,
  order_date,
  channel,
  region,
  currency,
  amount_local,
  status,
  line_count,
  source_system,
  ingested_at
FROM (
  -- App orders
  SELECT
    order_id,
    customer_id,
    order_ts,
    DATE(order_ts) AS order_date,
    channel,
    region,
    currency,
    amount_local,
    status,
    line_count,
    'app' AS source_system,
    ingested_at
  FROM `YOUR_PROJECT_ID.retailmart.raw.app_orders`
  WHERE DATE(ingested_at) = DATE '2026-01-15'   -- @target_date

  UNION ALL

  -- POS orders: the store becomes the customer surrogate
  SELECT
    order_id,
    CONCAT('store_', store_id) AS customer_id,
    order_ts,
    DATE(order_ts) AS order_date,
    'store' AS channel,
    store_id AS region,
    currency,
    amount_local,
    status,
    line_count,
    'pos' AS source_system,
    ingested_at
  FROM `YOUR_PROJECT_ID.retailmart.raw.pos_orders`
  WHERE order_date = DATE '2026-01-15'           -- @target_date
);

-- ---------------------------------------------------------------------
-- 3. Stage 2: curate staging -> curated (with FX conversion)
-- ---------------------------------------------------------------------

INSERT INTO `YOUR_PROJECT_ID.retailmart.curated.orders`
  (order_id, customer_id, order_ts, order_date, channel, region,
   currency, amount_local, amount_eur, status, line_count,
   source_system, ingested_at)
SELECT
  o.order_id,
  o.customer_id,
  o.order_ts,
  o.order_date,
  o.channel,
  o.region,
  o.currency,
  o.amount_local,
  ROUND(o.amount_local * fx.rate_to_eur, 2) AS amount_eur,
  o.status,
  o.line_count,
  o.source_system,
  o.ingested_at
FROM `YOUR_PROJECT_ID.retailmart.staging.orders` AS o
JOIN `YOUR_PROJECT_ID.retailmart.raw.fx_rates` AS fx
  ON o.currency = fx.currency
 AND fx.rate_date = o.order_date
WHERE o.order_date = DATE '2026-01-15';

-- ---------------------------------------------------------------------
-- 4. Stage 3: build the marts
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.retailmart.mart.daily_revenue` AS
WITH daily AS (
  SELECT
    order_date,
    region,
    channel,
    COUNT(*) AS order_count,
    COUNT(DISTINCT customer_id) AS customer_count,
    SUM(amount_eur) AS revenue_eur
  FROM `YOUR_PROJECT_ID.retailmart.curated.orders`
  WHERE order_date = DATE '2026-01-15'
  GROUP BY order_date, region, channel
),
rolling AS (
  SELECT
    order_date,
    region,
    channel,
    SUM(order_count) OVER (
      PARTITION BY region, channel
      ORDER BY order_date
      RANGE BETWEEN INTERVAL 6 DAY PRECEDING AND CURRENT ROW
    ) AS order_count_7d,
    SUM(revenue_eur) OVER (
      PARTITION BY region, channel
      ORDER BY order_date
      RANGE BETWEEN INTERVAL 6 DAY PRECEDING AND CURRENT ROW
    ) AS revenue_eur_7d
  FROM `YOUR_PROJECT_ID.retailmart.curated.orders`
  WHERE order_date BETWEEN DATE_SUB(DATE '2026-01-15', INTERVAL 6 DAY)
                     AND DATE '2026-01-15'
  GROUP BY order_date, region, channel
)
SELECT
  d.order_date,
  d.region,
  d.channel,
  d.order_count,
  d.customer_count,
  d.revenue_eur,
  ROUND(d.revenue_eur / d.order_count, 2) AS aov_eur,
  r.order_count_7d,
  r.revenue_eur_7d
FROM daily d
LEFT JOIN rolling r
  ON d.order_date = r.order_date
 AND d.region = r.region
 AND d.channel = r.channel;

-- ---------------------------------------------------------------------
-- 5. The data quality gate
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.retailmart.dq_results` AS
WITH control AS (
  SELECT
    COUNT(*) AS n,
    SUM(amount_local) AS total
  FROM `YOUR_PROJECT_ID.retailmart.raw.pos_orders`
  WHERE order_date = DATE '2026-01-15'
),
curated AS (
  SELECT
    COUNT(*) AS n,
    SUM(amount_eur) AS total
  FROM `YOUR_PROJECT_ID.retailmart.curated.orders`
  WHERE order_date = DATE '2026-01-15'
    AND source_system = 'pos'
),
fx_check AS (
  SELECT COUNT(*) AS n
  FROM `YOUR_PROJECT_ID.retailmart.staging.orders` o
  LEFT JOIN `YOUR_PROJECT_ID.retailmart.raw.fx_rates` fx
    ON o.currency = fx.currency AND fx.rate_date = o.order_date
  WHERE o.order_date = DATE '2026-01-15'
    AND fx.rate_to_eur IS NULL
),
nulls AS (
  SELECT COUNT(*) AS n
  FROM `YOUR_PROJECT_ID.retailmart.curated.orders`
  WHERE order_date = DATE '2026-01-15'
    AND (order_id IS NULL OR customer_id IS NULL OR amount_eur IS NULL)
)
SELECT
  DATE '2026-01-15' AS check_date,
  'pos_row_count_parity' AS check_name,
  control.n AS control_value,
  curated.n AS actual_value,
  ABS(control.n - curated.n) AS diff,
  IF(control.n = 0, 0, ROUND(100 * ABS(control.n - curated.n) / control.n, 4)) AS diff_pct,
  IF(control.n = curated.n, 'PASS', 'FAIL') AS status
FROM control, curated
UNION ALL
SELECT
  DATE '2026-01-15',
  'missing_fx_rate',
  0, fx_check.n, fx_check.n, 100.0,
  IF(fx_check.n = 0, 'PASS', 'FAIL')
FROM fx_check
UNION ALL
SELECT
  DATE '2026-01-15',
  'null_required_fields',
  0, nulls.n, nulls.n, 100.0,
  IF(nulls.n = 0, 'PASS', 'FAIL')
FROM nulls;

-- The gate: the DAG task raises if any check failed
SELECT
  check_name,
  diff_pct,
  status
FROM `YOUR_PROJECT_ID.retailmart.dq_results`
WHERE check_date = DATE '2026-01-15'
  AND status = 'FAIL';

-- ---------------------------------------------------------------------
-- 6. The serving layer for Looker Studio
-- ---------------------------------------------------------------------

-- A logical view with the joins the dashboard needs
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.retailmart.mart.v_revenue_dashboard` AS
SELECT
  d.order_date,
  d.region,
  d.channel,
  d.order_count,
  d.customer_count,
  d.revenue_eur,
  d.aov_eur,
  d.order_count_7d,
  d.revenue_eur_7d
FROM `YOUR_PROJECT_ID.retailmart.mart.daily_revenue` AS d;

-- A materialized view for the heaviest tile
CREATE MATERIALIZED VIEW `YOUR_PROJECT_ID.retailmart.mart.mv_region_monthly` AS
SELECT
  DATE_TRUNC(MONTH, order_date) AS month,
  region,
  SUM(revenue_eur) AS revenue_eur,
  SUM(order_count) AS order_count
FROM `YOUR_PROJECT_ID.retailmart.curated.orders`
GROUP BY month, region;

-- ---------------------------------------------------------------------
-- 7. Backfill support — the same logic, a different date
-- ---------------------------------------------------------------------

-- Backfill a single day (the task parameter becomes the date)
-- INSERT INTO `YOUR_PROJECT_ID.retailmart.curated.orders`
-- SELECT ... WHERE order_date = DATE '2026-01-14';

-- Backfill a range using a loop
DECLARE d DATE DEFAULT DATE '2026-01-01';
DECLARE end_date DATE DEFAULT DATE '2026-01-31';

WHILE d <= end_date DO
  -- (In production this is a Python loop issuing one MERGE per day.)
  SET d = DATE_ADD(d, INTERVAL 1 DAY);
END WHILE;

-- The idempotent form of a backfill: MERGE per partition
MERGE `YOUR_PROJECT_ID.retailmart.curated.orders` AS t
USING (
  SELECT
    o.order_id, o.customer_id, o.order_ts, o.order_date, o.channel,
    o.region, o.currency, o.amount_local,
    ROUND(o.amount_local * fx.rate_to_eur, 2) AS amount_eur,
    o.status, o.line_count, o.source_system, o.ingested_at
  FROM `YOUR_PROJECT_ID.retailmart.staging.orders` o
  JOIN `YOUR_PROJECT_ID.retailmart.raw.fx_rates` fx
    ON o.currency = fx.currency AND fx.rate_date = o.order_date
  WHERE o.order_date = DATE '2026-01-15'
) AS s
ON t.order_id = s.order_id
  AND t.order_date = s.order_date
WHEN MATCHED THEN UPDATE SET
  t.status = s.status,
  t.amount_local = s.amount_local,
  t.amount_eur = s.amount_eur,
  t.ingested_at = s.ingested_at
WHEN NOT MATCHED THEN INSERT
  (order_id, customer_id, order_ts, order_date, channel, region,
   currency, amount_local, amount_eur, status, line_count,
   source_system, ingested_at)
VALUES
  (s.order_id, s.customer_id, s.order_ts, s.order_date, s.channel,
   s.region, s.currency, s.amount_local, s.amount_eur, s.status,
   s.line_count, s.source_system, s.ingested_at);

-- ---------------------------------------------------------------------
-- 8. The live operations view (streaming)
-- ---------------------------------------------------------------------

-- The last 24 hours of streamed events
SELECT
  event_type,
  COUNT(*) AS event_count,
  COUNT(DISTINCT user_id) AS unique_users
FROM `YOUR_PROJECT_ID.retailmart.raw.app_events`
WHERE _PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
GROUP BY event_type
ORDER BY event_count DESC;

-- Hourly event volume (the streaming buffer is never cached)
SELECT
  TIMESTAMP_TRUNC(event_ts, HOUR) AS hour,
  COUNT(*) AS n
FROM `YOUR_PROJECT_ID.retailmart.raw.app_events`
WHERE event_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 6 HOUR)
GROUP BY hour
ORDER BY hour;

-- ---------------------------------------------------------------------
-- 9. Cost monitoring for the pipeline
-- ---------------------------------------------------------------------

-- Bytes scanned per day, by table
SELECT
  DATE(creation_time) AS day,
  REGEXP_EXTRACT(statement, r'FROM\s+`([^`]+)`') AS table_scanned,
  COUNT(*) AS queries,
  ROUND(SUM(total_bytes_billed) / POWER(1024, 4) * 6.25, 4) AS cost_usd
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE job_type = 'QUERY'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY day, table_scanned
ORDER BY day DESC, cost_usd DESC;

-- Storage by layer
SELECT
  CASE
    WHEN table_schema = 'raw' THEN 'raw'
    WHEN table_schema = 'staging' THEN 'staging'
    WHEN table_schema = 'curated' THEN 'curated'
    WHEN table_schema = 'mart' THEN 'mart'
    ELSE table_schema
  END AS layer,
  ROUND(SUM(size_bytes) / POWER(1024, 3), 2) AS size_gb,
  ROUND(SUM(size_bytes) / POWER(1024, 3) * 0.02, 2) AS est_monthly_cost_usd
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.TABLE_STORAGE
GROUP BY layer
ORDER BY size_gb DESC;

-- ---------------------------------------------------------------------
-- 10. The pipeline's health at a glance
-- ---------------------------------------------------------------------

SELECT
  'rows_curated' AS metric,
  CAST(COUNT(*) AS STRING) AS value
FROM `YOUR_PROJECT_ID.retailmart.curated.orders`
WHERE order_date = DATE '2026-01-15'
UNION ALL
SELECT 'dq_failures', CAST(COUNT(*) AS STRING)
FROM `YOUR_PROJECT_ID.retailmart.dq_results`
WHERE check_date = DATE '2026-01-15' AND status = 'FAIL'
UNION ALL
SELECT 'revenue_eur', CAST(ROUND(SUM(amount_eur), 2) AS STRING)
FROM `YOUR_PROJECT_ID.retailmart.curated.orders`
WHERE order_date = DATE '2026-01-15';
