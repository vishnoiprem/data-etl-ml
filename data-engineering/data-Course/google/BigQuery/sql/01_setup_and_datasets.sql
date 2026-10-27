-- =====================================================================
-- 01_setup_and_datasets.sql
-- Course: BigQuery for Big Data Engineers
-- Covers: Chapters 11 (setup), 13 (datasets & regions), 43 (Python datasets)
--
-- Usage:
--   bq query --use_legacy_sql=false --dry_run < 01_setup_and_datasets.sql
--   bq query --use_legacy_sql=false < 01_setup_and_datasets.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Create the course datasets
-- ---------------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.raw`
OPTIONS(
  description = "Immutable raw landing zone. Never updated, never deleted manually.",
  location = "US",
  default_table_expiration_days = 730,
  default_partition_expiration_days = 730,
  labels = [("tier", "raw"), ("env", "prod"), ("owner", "data-eng")]
);

CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.staging`
OPTIONS(
  description = "Cleaned, typed, deduplicated intermediate data",
  location = "US",
  default_table_expiration_days = 30,
  default_partition_expiration_days = 30,
  labels = [("tier", "staging"), ("env", "prod"), ("owner", "data-eng")]
);

CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.curated`
OPTIONS(
  description = "Curated, conformed, queryable models",
  location = "US",
  default_table_expiration_days = 365,
  default_partition_expiration_days = 730,
  labels = [("tier", "curated"), ("env", "prod"), ("owner", "data-eng")]
);

CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.mart`
OPTIONS(
  description = "BI serving layer",
  location = "US",
  labels = [("tier", "gold"), ("env", "prod"), ("owner", "analytics-eng")]
);

CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.sandbox`
OPTIONS(
  description = "Experiments. Auto-expires in 7 days.",
  location = "US",
  default_table_expiration_days = 7,
  labels = [("tier", "scratch"), ("env", "dev")]
);

-- ---------------------------------------------------------------------
-- 2. A case-insensitive dataset (created with the bq CLI, shown here for
--    completeness — the SQL flag is is_case_insensitive)
-- ---------------------------------------------------------------------

-- CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.case_insensitive_ds`
-- OPTIONS(is_case_insensitive = TRUE, location = "US");

-- ---------------------------------------------------------------------
-- 3. Inspect the datasets you just created
-- ---------------------------------------------------------------------

SELECT
  dataset_id,
  location,
  description,
  labels,
  default_table_expiration_ms,
  default_partition_expiration_ms,
  creation_time
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.SCHEMATA
WHERE dataset_id IN ('raw', 'staging', 'curated', 'mart', 'sandbox')
ORDER BY dataset_id;

-- ---------------------------------------------------------------------
-- 4. Project-level inventory
-- ---------------------------------------------------------------------

SELECT
  t.table_name,
  t.table_type,
  t.creation_time,
  COALESCE(t.is_partitioned, FALSE) AS is_partitioned,
  t.partitioning_type,
  t.clustering_fields,
  t.row_count,
  t.size_bytes,
  t.labels
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.TABLES AS t
WHERE t.table_schema IN ('raw', 'staging', 'curated', 'mart')
ORDER BY t.table_schema, t.table_name;

-- ---------------------------------------------------------------------
-- 5. Grant dataset-level access to an analytics service account
-- ---------------------------------------------------------------------

-- GRANT `roles/bigquery.dataViewer` ON SCHEMA `YOUR_PROJECT_ID.curated`
-- TO "SERVICE_ACCOUNT:analytics@YOUR_PROJECT_ID.iam.gserviceaccount.com";

-- GRANT `roles/bigquery.jobUser` ON PROJECT `YOUR_PROJECT_ID`
-- TO "SERVICE_ACCOUNT:analytics@YOUR_PROJECT_ID.iam.gserviceaccount.com";
