-- =====================================================================
-- 01_bigquery_setup.sql
-- Course: Dataproc + PySpark for Big Data Engineers
-- Covers: Chapter 02 (cluster & project setup), the BigQuery side of
--          the medallion model used throughout the course.
--
-- Usage:
--   bq query --use_legacy_sql=false --dry_run < 01_bigquery_setup.sql
--   bq query --use_legacy_sql=false < 01_bigquery_setup.sql
--
-- Replace YOUR_PROJECT_ID with your project before running. The
-- scripts are idempotent: re-running them is safe and cheap.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. The medallion datasets
--
--    bronze  -> raw, immutable, exactly as it landed. Never updated.
--    silver  -> typed, deduplicated, conformed. SCD2 dimensions live here.
--    gold    -> facts and serving tables. Append-only, partitioned.
--    quarantine -> rows that failed validation. Reviewed, never dropped.
--    mart    -> business-facing aggregates for BI.
--
--    The `staging` dataset is a scratch area for the Spark jobs:
--    intermediate Parquet, and the temp bucket the BigQuery connector
--    writes to before a LOAD job. It is short-lived by design.
-- ---------------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.bronze`
OPTIONS(
  description = "Immutable raw landing zone. Append-only. Never UPDATEd, never DELETEd by a pipeline.",
  location = "US",
  default_table_expiration_days = 730,
  default_partition_expiration_days = 730,
  labels = [("tier", "bronze"), ("env", "prod"), ("owner", "data-eng"), ("course", "dataproc")]
);

CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.silver`
OPTIONS(
  description = "Typed, deduplicated, conformed models. SCD2 dimensions. Join-ready.",
  location = "US",
  default_table_expiration_days = 1095,
  default_partition_expiration_days = 1095,
  labels = [("tier", "silver"), ("env", "prod"), ("owner", "data-eng"), ("course", "dataproc")]
);

CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.gold`
OPTIONS(
  description = "Facts and serving tables. Partitioned by event date. Append-only.",
  location = "US",
  default_table_expiration_days = 1095,
  default_partition_expiration_days = 1095,
  labels = [("tier", "gold"), ("env", "prod"), ("owner", "data-eng"), ("course", "dataproc")]
);

CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.quarantine`
OPTIONS(
  description = "Rows that failed validation. Retained for review and replay. Never silently dropped.",
  location = "US",
  default_table_expiration_days = 365,
  default_partition_expiration_days = 365,
  labels = [("tier", "quarantine"), ("env", "prod"), ("owner", "data-eng"), ("course", "dataproc")]
);

CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.mart`
OPTIONS(
  description = "BI serving layer. Pre-aggregated so dashboards never scan the fact tables.",
  location = "US",
  default_table_expiration_days = 1095,
  default_partition_expiration_days = 1095,
  labels = [("tier", "mart"), ("env", "prod"), ("owner", "analytics-eng"), ("course", "dataproc")]
);

-- The staging dataset is intentionally short-lived. The Spark jobs use it
-- for intermediate Parquet and for the BigQuery connector's temporary
-- staging area. Anything that survives a week is a design smell.
CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.staging`
OPTIONS(
  description = "Scratch space for Spark intermediates and BigQuery LOAD-job staging. Auto-expires.",
  location = "US",
  default_table_expiration_days = 7,
  default_partition_expiration_days = 7,
  labels = [("tier", "staging"), ("env", "prod"), ("owner", "data-eng"), ("course", "dataproc")]
);

-- A sandbox for experiments. Seven days, then it disappears.
CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.sandbox`
OPTIONS(
  description = "Experiments and scratch analysis. Auto-expires in 7 days.",
  location = "US",
  default_table_expiration_days = 7,
  labels = [("tier", "sandbox"), ("env", "dev"), ("course", "dataproc")]
);

-- ---------------------------------------------------------------------
-- 2. Dataset-level access for the pipeline service account
--
--    Grant at the DATASET level, not the project level. A pipeline that
--    can write to `mart` has no business writing to `bronze`.
--
--    bq add-iam-policy-binding --dataset YOUR_PROJECT_ID:gold \
--      --member="serviceAccount:dataproc-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
--      --role="roles/bigquery.dataEditor"
--
--    bq add-iam-policy-binding --dataset YOUR_PROJECT_ID:bronze \
--      --member="serviceAccount:dataproc-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
--      --role="roles/bigquery.dataViewer"
--
--    bq add-iam-policy-binding --dataset YOUR_PROJECT_ID:quarantine \
--      --member="serviceAccount:dataproc-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
--      --role="roles/bigquery.dataEditor"
-- ---------------------------------------------------------------------

-- ---------------------------------------------------------------------
-- 3. Verify the datasets exist
-- ---------------------------------------------------------------------

SELECT
  dataset_id,
  location,
  description,
  labels,
  ROUND(default_table_expiration_ms / 86400000, 1) AS default_table_expiration_days,
  creation_time
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.SCHEMATA
WHERE dataset_id IN ('bronze', 'silver', 'gold', 'quarantine', 'mart', 'staging', 'sandbox')
ORDER BY dataset_id;

-- ---------------------------------------------------------------------
-- 4. Project-level table inventory
--
--    Run this after the pipeline has run once. It shows what exists,
--    how big it is, and how it is partitioned and clustered.
-- ---------------------------------------------------------------------

SELECT
  t.table_schema,
  t.table_name,
  t.table_type,
  COALESCE(t.is_partitioned, FALSE) AS is_partitioned,
  t.partitioning_type,
  t.clustering_fields,
  t.row_count,
  ROUND(t.size_bytes / 1024 / 1024, 2) AS size_mib,
  t.last_modified_time
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.TABLES AS t
WHERE t.table_schema IN ('bronze', 'silver', 'gold', 'quarantine', 'mart', 'staging')
ORDER BY t.table_schema, t.table_name;
