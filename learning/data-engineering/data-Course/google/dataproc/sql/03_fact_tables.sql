-- =====================================================================
-- 03_fact_tables.sql
-- Course: Dataproc + PySpark for Big Data Engineers
--
-- The GOLD layer: facts. And the QUARANTINE layer: the rows that did
-- not make it into the facts.
--
-- Partitioning rule used throughout:
--   PARTITION BY <the DATE column the fact is filtered on>
-- Partitioning on a DATE column (not DATE(<timestamp>)) is deliberate.
-- BigQuery lets you partition by a DATE column directly, and when you
-- do, the physical partition value IS that column's value. That buys
-- two things:
--   1. A query that filters `sales_date = DATE '2026-10-27'` prunes to
--      exactly one partition — no expression to evaluate, no decorator
--      to strip.
--   2. A MERGE into a partitioned target can match on the partition key
--      itself. BigQuery requires a predicate on the partition column in
--      the MERGE `ON` clause; with `PARTITION BY DATE(order_ts)` that
--      predicate would have to be written as `DATE(t.order_ts) = ...`,
--      which BigQuery will not accept as a partition predicate on a
--      MERGE target. With `PARTITION BY sales_date` the predicate is
--      `t.sales_date = s.sales_date` and the MERGE prunes.
-- The event timestamp is still carried in the table (`order_ts`,
-- `submitted_at`) — partitioning on the DATE column is about physical
-- layout, not about dropping precision from the data.
--
-- Clustering rule:
--   CLUSTER BY <the dimension key the fact joins on>
-- BigQuery sorts blocks within a partition by the clustering columns,
-- so the join or filter reads a narrow range of blocks.
--
-- Usage:
--   bq query --use_legacy_sql=false < 03_fact_tables.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. gold.fact_sales  (retail case study)
--
--    One row per POS transaction (order_id). Grain is stated in the
--    description because "one row per order" is the single most
--    important fact about a fact table and the most often forgotten.
--
--    CLUSTER BY store_id — the dominant BI filter is date + store.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID`.gold.fact_sales (
  order_id            STRING          NOT NULL,
  order_ts            TIMESTAMP       NOT NULL,
  sales_date          DATE            NOT NULL,
  store_id            STRING          NOT NULL,
  product_id          STRING          NOT NULL,
  category_id         STRING,
  category_name       STRING,
  product_name        STRING,
  region_id           STRING,
  region_name         STRING,
  quantity            INT64,
  unit_price          NUMERIC(18,2),
  discount_amount     NUMERIC(18,2),
  tax_amount          NUMERIC(18,2),
  net_amount          NUMERIC(18,2),
  payment_method      STRING,
  promo_code          STRING,
  status              STRING,
  is_promo            BOOL,
  product_sk          INT64,
  store_sk            INT64,
  source_file         STRING,
  run_date            DATE,
  loaded_at           TIMESTAMP       NOT NULL
)
PARTITION BY sales_date
CLUSTER BY store_id
OPTIONS(
  description = "Conformed POS transactions. Grain: one row per order_id. net_amount is revenue after discount, excluding tax. COMPLETED rows only.",
  labels = [("tier", "gold"), ("entity", "fact"), ("domain", "retail")],
  require_partition_filter = FALSE,
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- ---------------------------------------------------------------------
-- 2. gold.fact_claims  (healthcare case study)
--
--    One row per submitted claim (claim_id). A claim may carry several
--    diagnosis codes; this table keeps the PRIMARY one and a count of
--    the rest. The full dx array lives in bronze.
--
--    CLUSTER BY provider_id.
--
--    Note what is NOT here: no member_name, no member_dob, no member_ssn.
--    PHI is dropped at the parse boundary in PySpark, not loaded and
--    then deleted.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID`.gold.fact_claims (
  claim_id            STRING          NOT NULL,
  member_id           STRING,
  provider_id         STRING          NOT NULL,
  service_date        DATE            NOT NULL,
  submitted_at        TIMESTAMP,
  claim_amount        NUMERIC(18,2),
  primary_dx_code     STRING,
  dx_code_count       INT64,
  procedure_count     INT64,
  is_denied           BOOL,
  denial_code         STRING,
  denial_reason       STRING,
  provider_sk         INT64,
  provider_name       STRING,
  provider_type       STRING,
  source_file         STRING,
  run_date            DATE,
  loaded_at           TIMESTAMP       NOT NULL
)
PARTITION BY service_date
CLUSTER BY provider_id
OPTIONS(
  description = "Validated insurance claims. Grain: one row per claim_id. Contains no member PII. Invalid rows are routed to quarantine.rejected_claims.",
  labels = [("tier", "gold"), ("entity", "fact"), ("domain", "healthcare")],
  require_partition_filter = FALSE,
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- ---------------------------------------------------------------------
-- 3. gold.quarantine_rejected_sales
--
--    The retail case study's quarantine. Same shape and same rules as
--    the claims quarantine below:
--      - what was rejected?      (the row)
--      - why was it rejected?    (reject_reason)
--      - when was it rejected?   (rejected_at)
--
--    Partitioned by run_date so a replay of a bad run is cheap to
--    select and cheap to delete. The raw_payload column keeps the
--    original record so the data team can diagnose the rejection
--    without re-reading the source.
--
--    CLUSTER BY reject_reason so the "show me everything rejected for
--    reason X" query is a block-range read.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID`.gold.quarantine_rejected_sales (
  order_id            STRING,
  store_id            STRING,
  product_id          STRING,
  order_timestamp     STRING,
  quantity            STRING,
  unit_price          STRING,
  discount            STRING,
  reject_reason       STRING,
  raw_payload         STRING,
  source_file         STRING,
  run_date            DATE,
  rejected_at         TIMESTAMP
)
PARTITION BY run_date
CLUSTER BY reject_reason
OPTIONS(
  description = "POS transactions that failed validation. Never silently dropped, never loaded into the fact table.",
  labels = [("tier", "quarantine"), ("entity", "reject"), ("domain", "retail")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 2 YEAR)
);

-- ---------------------------------------------------------------------
-- 4. gold.quarantine_rejected_claims
--
--    The healthcare case study's quarantine. Same shape and same rules
--    as the sales quarantine above.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID`.gold.quarantine_rejected_claims (
  claim_id            STRING,
  member_id           STRING,
  provider_id         STRING,
  service_date        DATE,
  claim_amount        NUMERIC(18,2),
  reject_reason       STRING,
  raw_payload         STRING,
  source_file         STRING,
  run_date            DATE,
  rejected_at         TIMESTAMP
)
PARTITION BY run_date
CLUSTER BY reject_reason
OPTIONS(
  description = "Claims that failed validation. Reviewed by provider enablement. Never silently dropped, never loaded into the fact table.",
  labels = [("tier", "quarantine"), ("entity", "reject"), ("domain", "healthcare")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 2 YEAR)
);

-- ---------------------------------------------------------------------
-- 4. Verify the facts landed and check their grain
--
--    A fact table whose row count exceeds the distinct key count has
--    duplicates — usually a re-run that appended instead of replaced.
--    This is the single most common pipeline bug in this course.
-- ---------------------------------------------------------------------

SELECT
  'fact_sales' AS table_name,
  COUNT(*) AS total_rows,
  COUNT(DISTINCT order_id) AS distinct_keys,
  COUNT(*) - COUNT(DISTINCT order_id) AS duplicate_rows,
  MIN(sales_date) AS min_date,
  MAX(sales_date) AS max_date
FROM `YOUR_PROJECT_ID`.gold.fact_sales
UNION ALL
SELECT
  'fact_claims',
  COUNT(*),
  COUNT(DISTINCT claim_id),
  COUNT(*) - COUNT(DISTINCT claim_id),
  MIN(service_date),
  MAX(service_date)
FROM `YOUR_PROJECT_ID`.gold.fact_claims;

-- Quarantine volume by reason. A sudden spike in one reason is a signal
-- that a source system changed shape, not that the pipeline broke.
SELECT
  reject_reason,
  COUNT(*) AS rejected_rows,
  MIN(run_date) AS first_run,
  MAX(run_date) AS last_run
FROM `YOUR_PROJECT_ID`.gold.quarantine_rejected_claims
GROUP BY reject_reason
ORDER BY rejected_rows DESC;
