-- =====================================================================
-- 05_data_quality_checks.sql
-- Course: Dataproc + PySpark for Big Data Engineers
--
-- A library of STANDALONE validation queries. Each one runs on its
-- own and returns a small result set. Run them in order after every
-- pipeline execution.
--
-- How to read the results:
--
--   * A query that returns ZERO ROWS PASSED.
--   * A query that returns rows FAILED — the rows ARE the problem.
--
-- Every query has a comment header stating what it checks and what
-- "failure" looks like. The PySpark job runs the equivalent checks
-- in-process (chapter 10 and 11) and raises on failure; these SQL
-- versions are the independent audit trail — they check the data
-- AFTER it landed in BigQuery, not before.
--
-- Usage:
--   bq query --use_legacy_sql=false < 05_data_quality_checks.sql
-- =====================================================================


-- ---------------------------------------------------------------------
-- CHECK 1: Row count vs expectation
--
-- What it checks:
--   The fact table's row count for the run date against an expected
--   count. Replace 1000 with your expectation (typically the count
--   the source system reported, or a prior-run count plus a tolerance).
--
-- What failure looks like:
--   A row is returned with actual_rows <> expected_rows. The pipeline
--   either dropped data (actual too low) or duplicated it (actual too
--   high). Both are release blockers.
-- ---------------------------------------------------------------------

SELECT
  'fact_sales' AS check_name,
  DATE '2026-10-27' AS run_date,
  COUNT(*) AS actual_rows,
  1000 AS expected_rows,
  COUNT(*) - 1000 AS delta,
  CASE
    WHEN COUNT(*) = 1000 THEN 'PASS'
    WHEN COUNT(*) BETWEEN 900 AND 1100 THEN 'WARN'
    ELSE 'FAIL'
  END AS status
FROM `YOUR_PROJECT_ID`.gold.fact_sales
WHERE sales_date = DATE '2026-10-27'
GROUP BY run_date;


-- ---------------------------------------------------------------------
-- CHECK 2: Null-rate check on required columns
--
-- What it checks:
--   The percentage of NULLs in each column of the fact table for the
--   run date. A column that is 100% NULL is a broken pipeline; a
--   column that is 1% NULL might be a genuine source gap.
--
-- What failure looks like:
--   A row where null_rate > 0.01 (1%). The threshold is a policy
--   choice; adjust it, but make it explicit rather than implicit.
-- ---------------------------------------------------------------------

SELECT
  'fact_sales.order_id' AS column_name,
  COUNTIF(order_id IS NULL) AS null_count,
  COUNT(*) AS total_rows,
  SAFE_DIVIDE(COUNTIF(order_id IS NULL), COUNT(*)) AS null_rate,
  'FAIL' AS status
FROM `YOUR_PROJECT_ID`.gold.fact_sales
WHERE sales_date = DATE '2026-10-27'
GROUP BY column_name
HAVING SAFE_DIVIDE(COUNTIF(order_id IS NULL), COUNT(*)) > 0.01

UNION ALL

SELECT
  'fact_sales.store_id',
  COUNTIF(store_id IS NULL),
  COUNT(*),
  SAFE_DIVIDE(COUNTIF(store_id IS NULL), COUNT(*)),
  'FAIL'
FROM `YOUR_PROJECT_ID`.gold.fact_sales
WHERE sales_date = DATE '2026-10-27'
GROUP BY column_name
HAVING SAFE_DIVIDE(COUNTIF(store_id IS NULL), COUNT(*)) > 0.01

UNION ALL

SELECT
  'fact_sales.product_id',
  COUNTIF(product_id IS NULL),
  COUNT(*),
  SAFE_DIVIDE(COUNTIF(product_id IS NULL), COUNT(*)),
  'FAIL'
FROM `YOUR_PROJECT_ID`.gold.fact_sales
WHERE sales_date = DATE '2026-10-27'
GROUP BY column_name
HAVING SAFE_DIVIDE(COUNTIF(product_id IS NULL), COUNT(*)) > 0.01

UNION ALL

SELECT
  'fact_sales.net_amount',
  COUNTIF(net_amount IS NULL),
  COUNT(*),
  SAFE_DIVIDE(COUNTIF(net_amount IS NULL), COUNT(*)),
  'FAIL'
FROM `YOUR_PROJECT_ID`.gold.fact_sales
WHERE sales_date = DATE '2026-10-27'
GROUP BY column_name
HAVING SAFE_DIVIDE(COUNTIF(net_amount IS NULL), COUNT(*)) > 0.01;


-- ---------------------------------------------------------------------
-- CHECK 3: Referential integrity — orphan fact rows
--
-- What it checks:
--   Every fact row must have a matching current dimension row. An
--   orphan is a transaction whose product or store is not in the
--   master. That usually means the dimension load ran AFTER the fact
--   load, or the dimension filter dropped a row.
--
-- What failure looks like:
--   Any row returned. Every returned row is an orphan. A non-zero
--   count means the fact's surrogate key is NULL for those rows,
--   which is the visible symptom.
-- ---------------------------------------------------------------------

SELECT
  f.order_id,
  f.product_id,
  f.store_id,
  'orphan_product' AS orphan_type
FROM `YOUR_PROJECT_ID`.gold.fact_sales AS f
LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_product AS p
  ON f.product_id = p.product_id AND p.is_current
WHERE p.product_id IS NULL
  AND f.sales_date = DATE '2026-10-27'
LIMIT 100

UNION ALL

SELECT
  f.order_id,
  f.product_id,
  f.store_id,
  'orphan_store'
FROM `YOUR_PROJECT_ID`.gold.fact_sales AS f
LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_store AS s
  ON f.store_id = s.store_id AND s.is_current
WHERE s.store_id IS NULL
  AND f.sales_date = DATE '2026-10-27'
LIMIT 100;


-- ---------------------------------------------------------------------
-- CHECK 3b: Referential integrity — orphan claims
--
-- What it checks:
--   Every claim must have a matching current provider, and every
--   primary diagnosis code must exist in the ICD-10 reference.
--
-- What failure looks like:
--   Any row returned. An orphan provider means the provider master
--   is behind the claims feed. An unknown diagnosis code means the
--   reference data is stale or the source emitted a malformed code.
-- ---------------------------------------------------------------------

SELECT
  c.claim_id,
  c.provider_id,
  c.primary_dx_code,
  'orphan_provider' AS orphan_type
FROM `YOUR_PROJECT_ID`.gold.fact_claims AS c
LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_provider AS p
  ON c.provider_id = p.provider_npi AND p.is_current
WHERE p.provider_npi IS NULL
  AND c.service_date = DATE '2026-10-27'
LIMIT 100

UNION ALL

SELECT
  c.claim_id,
  c.provider_id,
  c.primary_dx_code,
  'unknown_diagnosis'
FROM `YOUR_PROJECT_ID`.gold.fact_claims AS c
LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_diagnosis AS d
  ON c.primary_dx_code = d.icd10_code AND d.is_current
WHERE d.icd10_code IS NULL
  AND c.service_date = DATE '2026-10-27'
LIMIT 100;


-- ---------------------------------------------------------------------
-- CHECK 4: Duplicate key check
--
-- What it checks:
--   The fact table's grain is one row per order_id / claim_id. A
--   duplicate means the pipeline appended a re-run without deleting
--   the prior load.
--
-- What failure looks like:
--   Any row returned. The duplicate_count column shows how many
--   extra copies exist. A single duplicate is as much of a bug as a
--   thousand — it means revenue is being double-counted.
-- ---------------------------------------------------------------------

SELECT
  'fact_sales' AS table_name,
  order_id AS business_key,
  COUNT(*) AS duplicate_count,
  MIN(loaded_at) AS first_loaded,
  MAX(loaded_at) AS last_loaded
FROM `YOUR_PROJECT_ID`.gold.fact_sales
GROUP BY order_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC
LIMIT 100;

-- Same check for claims.
SELECT
  'fact_claims' AS table_name,
  claim_id AS business_key,
  COUNT(*) AS duplicate_count,
  MIN(loaded_at) AS first_loaded,
  MAX(loaded_at) AS last_loaded
FROM `YOUR_PROJECT_ID`.gold.fact_claims
GROUP BY claim_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC
LIMIT 100;


-- ---------------------------------------------------------------------
-- CHECK 5: Amount reconciliation between fact and source
--
-- What it checks:
--   The sum of net_amount in the fact table must equal the sum in the
--   bronze/staging source for the same run date. This is the
--   end-to-end check: if it passes, no money was lost or invented
--   anywhere between landing and the model.
--
-- What failure looks like:
--   The two sums differ. The pipeline must have dropped rows, applied
--   a filter the source did not have, or duplicated rows. NOTE: the
--   comparison is only meaningful when the fact table's load was
--   scoped to a single run date — otherwise the fact table is
--   cumulative and the sums will not match by construction.
-- ---------------------------------------------------------------------

WITH source_totals AS (
  SELECT
    -- The bronze net amount, computed the same way the pipeline computes
    -- it: gross (quantity x unit_price) minus the discount. The column
    -- names come from the bronze.pos_orders schema, where the price and
    -- discount are still raw STRINGS.
    SUM(
      SAFE_CAST(quantity AS INT64) * SAFE_CAST(unit_price AS NUMERIC(18,2))
      - SAFE_CAST(discount AS NUMERIC(18,2))
    ) AS source_amount,
    COUNT(*) AS source_rows
  FROM `YOUR_PROJECT_ID`.bronze.pos_orders
  -- SAFE.PARSE_TIMESTAMP returns NULL for an unparseable value instead
  -- of raising an error, so the dirty rows do not abort the check.
  WHERE DATE(SAFE.PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S', order_timestamp)) = DATE '2026-10-27'
    AND SAFE_CAST(unit_price AS NUMERIC(18,2)) IS NOT NULL
    AND SAFE_CAST(quantity AS INT64) IS NOT NULL
),
fact_totals AS (
  SELECT
    SUM(net_amount) AS fact_amount,
    COUNT(*) AS fact_rows
  FROM `YOUR_PROJECT_ID`.gold.fact_sales
  WHERE sales_date = DATE '2026-10-27'
    AND status = 'COMPLETED'
)
SELECT
  'sales_amount_reconciliation' AS check_name,
  s.source_amount,
  f.fact_amount,
  f.fact_amount - s.source_amount AS amount_delta,
  s.source_rows,
  f.fact_rows,
  f.fact_rows - s.source_rows AS row_delta,
  CASE
    WHEN ABS(f.fact_amount - s.source_amount) < 0.01 THEN 'PASS'
    ELSE 'FAIL'
  END AS status
FROM source_totals AS s
CROSS JOIN fact_totals AS f;


-- ---------------------------------------------------------------------
-- CHECK 6: Late-arrival detection
--
-- What it checks:
--   Rows whose event timestamp is much older than the run date. A
--   "late" row arrived today but describes an event from days ago.
--   Late data is normal in real pipelines, but a spike in late arrivals
--   means a source system was down or a backfill ran.
--
-- What failure looks like:
--   A count of late rows above the agreed threshold (say, more than
--   1% of the run's rows are more than 2 days late). Individually
--   these are fine; a sudden increase is a signal.
-- ---------------------------------------------------------------------

SELECT
  'fact_sales' AS table_name,
  DATE '2026-10-27' AS run_date,
  COUNTIF(DATE_SUB(DATE '2026-10-27', INTERVAL 2 DAY) > sales_date) AS late_rows,
  COUNT(*) AS total_rows,
  SAFE_DIVIDE(COUNTIF(DATE_SUB(DATE '2026-10-27', INTERVAL 2 DAY) > sales_date), COUNT(*)) AS late_rate,
  MIN(sales_date) AS earliest_event_date,
  MAX(sales_date) AS latest_event_date,
  CASE
    WHEN SAFE_DIVIDE(COUNTIF(DATE_SUB(DATE '2026-10-27', INTERVAL 2 DAY) > sales_date), COUNT(*)) <= 0.01 THEN 'PASS'
    ELSE 'WARN'
  END AS status
FROM `YOUR_PROJECT_ID`.gold.fact_sales
WHERE DATE(loaded_at) = DATE '2026-10-27';

-- The same question asked the other way round: which EVENT dates did
-- this run's load actually touch? A run that writes to more than one
-- event date is either a backfill or a bug.
SELECT
  sales_date AS event_date,
  COUNT(*) AS rows_loaded,
  COUNT(DISTINCT order_id) AS distinct_orders,
  MIN(loaded_at) AS first_load,
  MAX(loaded_at) AS last_load
FROM `YOUR_PROJECT_ID`.gold.fact_sales
WHERE DATE(loaded_at) = DATE '2026-10-27'
GROUP BY sales_date
ORDER BY sales_date;


-- ---------------------------------------------------------------------
-- CHECK 7: Quarantine volume and rejection-reason breakdown
--
-- What it checks:
--   How many rows were quarantined in this run, and why. A quarantine
--   rate of 0.1% is normal. A quarantine rate of 60% means a source
--   format change went unnoticed.
--
-- What failure looks like:
--   A quarantine rate above the threshold (say 5%), or a single
--   reject_reason accounting for a sudden jump versus previous runs.
-- ---------------------------------------------------------------------

SELECT
  run_date,
  reject_reason,
  COUNT(*) AS rejected_rows,
  SAFE_DIVIDE(
    COUNT(*),
    SUM(COUNT(*)) OVER (PARTITION BY run_date)
  ) AS pct_of_quarantine
FROM `YOUR_PROJECT_ID`.gold.quarantine_rejected_claims
WHERE run_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY run_date, reject_reason
ORDER BY run_date DESC, rejected_rows DESC;


-- ---------------------------------------------------------------------
-- CHECK 8: Amount sanity — negative and implausible values
--
-- What it checks:
--   Negative revenue, negative quantities, and amounts beyond a
--   plausible ceiling. These should have been quarantined by the
--   Spark job; finding them in gold means the validation rules and
--   the actual data have diverged.
--
-- What failure looks like:
--   Any row returned.
-- ---------------------------------------------------------------------

SELECT
  order_id,
  order_ts,
  quantity,
  unit_price,
  net_amount,
  'negative_quantity' AS violation,
  'FAIL' AS status
FROM `YOUR_PROJECT_ID`.gold.fact_sales
WHERE quantity < 0
  AND sales_date = DATE '2026-10-27'

UNION ALL

SELECT
  order_id,
  order_ts,
  quantity,
  unit_price,
  net_amount,
  'negative_amount',
  'FAIL'
FROM `YOUR_PROJECT_ID`.gold.fact_sales
WHERE net_amount < 0
  AND sales_date = DATE '2026-10-27'

UNION ALL

SELECT
  order_id,
  order_ts,
  quantity,
  unit_price,
  net_amount,
  'implausible_amount',
  'FAIL'
FROM `YOUR_PROJECT_ID`.gold.fact_sales
WHERE net_amount > 1000000
  AND sales_date = DATE '2026-10-27';


-- ---------------------------------------------------------------------
-- CHECK 9: Future-dated events
--
-- What it checks:
--   Events dated in the future. These usually mean a timezone bug —
--   a UTC timestamp read as local time, or a date parsed with the
--   wrong format. They silently corrupt every time-based aggregate.
--
-- What failure looks like:
--   Any row returned.
-- ---------------------------------------------------------------------

SELECT
  'fact_sales' AS table_name,
  order_id,
  order_ts,
  sales_date,
  'event_after_run_date' AS violation
FROM `YOUR_PROJECT_ID`.gold.fact_sales
WHERE sales_date > DATE '2026-10-27'
LIMIT 100

UNION ALL

SELECT
  'fact_claims',
  claim_id,
  submitted_at,
  service_date,
  'event_after_run_date'
FROM `YOUR_PROJECT_ID`.gold.fact_claims
WHERE service_date > DATE '2026-10-27'
LIMIT 100;


-- ---------------------------------------------------------------------
-- CHECK 10: Mart-to-fact reconciliation
--
-- What it checks:
--   The mart total must equal the fact total. A mismatch means the
--   mart's join dropped rows or fanned out.
--
-- What failure looks like:
--   mart_net_revenue <> fact_net_revenue, or mart_order_count <>
--   fact_order_count.
-- ---------------------------------------------------------------------

SELECT
  (SELECT SUM(net_amount) FROM `YOUR_PROJECT_ID`.gold.fact_sales WHERE status = 'COMPLETED') AS fact_net_revenue,
  (SELECT SUM(net_revenue) FROM `YOUR_PROJECT_ID`.mart.daily_store_category_sales) AS mart_net_revenue,
  (SELECT COUNT(DISTINCT order_id) FROM `YOUR_PROJECT_ID`.gold.fact_sales WHERE status = 'COMPLETED') AS fact_order_count,
  (SELECT SUM(order_count) FROM `YOUR_PROJECT_ID`.mart.daily_store_category_sales) AS mart_order_count,
  CASE
    WHEN (SELECT SUM(net_amount) FROM `YOUR_PROJECT_ID`.gold.fact_sales WHERE status = 'COMPLETED')
       = (SELECT SUM(net_revenue) FROM `YOUR_PROJECT_ID`.mart.daily_store_category_sales)
     AND (SELECT COUNT(DISTINCT order_id) FROM `YOUR_PROJECT_ID`.gold.fact_sales WHERE status = 'COMPLETED')
       = (SELECT SUM(order_count) FROM `YOUR_PROJECT_ID`.mart.daily_store_category_sales)
    THEN 'PASS'
    ELSE 'FAIL'
  END AS status;


-- ---------------------------------------------------------------------
-- CHECK 11: INFORMATION_SCHEMA job audit
--
-- What it checks:
--   Every BigQuery job that ran in the project in the last 24 hours:
--   its type, state, bytes processed, and the identity that ran it.
--   This is the audit trail for who ran what and what it cost.
--
-- What failure looks like:
--   A row with state = 'ERROR' — a job failed and may have left a
--   partially-written table. Also worth reviewing: any job whose
--   total_bytes_billed is unexpectedly large.
--
--   NOTE: INFORMATION_SCHEMA.JOBS_BY_PROJECT is a REGION-qualified
--   view. 'region-us' covers the US multi-region. Use
--   'region-eu' or the specific region if your datasets live there.
-- ---------------------------------------------------------------------

SELECT
  job_id,
  job_type,
  state,
  creation_time,
  start_time,
  end_time,
  ROUND(total_bytes_billed / 1024 / 1024, 2) AS billed_mib,
  ROUND(total_bytes_processed / 1024 / 1024, 2) AS processed_mib,
  user_email,
  destination_table,
  error_result
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
ORDER BY creation_time DESC
LIMIT 100;


-- ---------------------------------------------------------------------
-- CHECK 12: Cost audit — bytes billed by job type
--
-- What it checks:
--   Total bytes billed per job type over the last 7 days. On-demand
--   pricing is $6.25 per TiB, so this converts directly into dollars.
--
-- What failure looks like:
--   A sudden jump in one job type. Usually an unfiltered scan — a
--   query missing its partition filter, or a MERGE that rewrote
--   every partition instead of one.
-- ---------------------------------------------------------------------

SELECT
  job_type,
  COUNT(*) AS job_count,
  SUM(total_bytes_billed) AS total_bytes_billed,
  ROUND(SUM(total_bytes_billed) / POW(1024, 4), 4) AS tib_billed,
  ROUND(SUM(total_bytes_billed) / POW(1024, 4) * 6.25, 4) AS estimated_usd,
  COUNTIF(state = 'ERROR') AS failed_jobs
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY job_type
ORDER BY total_bytes_billed DESC;
