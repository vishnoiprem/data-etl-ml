-- =====================================================================
-- 07_external_tables.sql
-- Course: BigQuery for Big Data Engineers
-- Covers: Chapters 33 (Cloud Storage buckets), 34 (external tables)
--
-- Usage:
--   bq query --use_legacy_sql=false --dry_run < 07_external_tables.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. A Parquet external table
-- ---------------------------------------------------------------------

CREATE OR REPLACE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.events_parquet` (
  event_id   STRING,
  user_id    STRING,
  event_type STRING,
  event_ts   TIMESTAMP,
  event_date DATE,
  amount     NUMERIC,
  props      JSON
)
WITH FORMAT OPTIONS(
  format = 'PARQUET',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/raw/events_*.parquet'],
  hive_partitioning_uri_prefix = 'gs://YOUR_PROJECT_ID-bq-course/raw/events/'
)
OPTIONS(
  description = "External Parquet table over GCS",
  labels = [("tier", "bronze"), ("owner", "data-eng")]
);

-- Query it like any other table
SELECT
  event_type,
  COUNT(*) AS event_count,
  SUM(amount) AS total_amount
FROM `YOUR_PROJECT_ID.raw.events_parquet`
WHERE event_date = DATE '2026-01-15'
GROUP BY event_type
ORDER BY event_count DESC;

-- The hive partition columns appear as regular columns
SELECT
  event_date,
  COUNT(*) AS n
FROM `YOUR_PROJECT_ID.raw.events_parquet`
GROUP BY event_date
ORDER BY event_date DESC;

-- ---------------------------------------------------------------------
-- 2. A CSV external table with an explicit schema
-- ---------------------------------------------------------------------

CREATE OR REPLACE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.orders_csv` (
  order_id     STRING,
  customer_id  STRING,
  order_date   DATE,
  total_amount NUMERIC,
  status       STRING
)
WITH FORMAT OPTIONS(
  format = 'CSV',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/staging/orders_*.csv'],
  skip_leading_rows = 1,
  field_delimiter = ',',
  quote = '"',
  max_bad_records = 10,
  allow_jagged_rows = FALSE,
  allow_quoted_newlines = FALSE
);

-- ---------------------------------------------------------------------
-- 3. A CSV external table with auto-detection
-- ---------------------------------------------------------------------

CREATE OR REPLACE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.orders_csv_autodetect`
WITH FORMAT OPTIONS(
  format = 'CSV',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/staging/orders_sample.csv'],
  skip_leading_rows = 1,
  autodetect = TRUE
);

-- ---------------------------------------------------------------------
-- 4. Other formats
-- ---------------------------------------------------------------------

-- Newline-delimited JSON
CREATE OR REPLACE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.events_ndjson`
WITH FORMAT OPTIONS(
  format = 'NEWLINE_DELIMITED_JSON',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/raw/events_*.ndjson']
);

-- Avro
CREATE OR REPLACE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.events_avro`
WITH FORMAT OPTIONS(
  format = 'AVRO',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/raw/events_*.avro']
);

-- ORC
CREATE OR REPLACE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.events_orc`
WITH FORMAT OPTIONS(
  format = 'ORC',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/raw/events_*.orc']
);

-- Google Sheets
-- CREATE OR REPLACE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.sheet_ref`
-- WITH FORMAT OPTIONS(
--   format = 'GOOGLE_SHEETS',
--   uris = ['https://docs.google.com/spreadsheets/d/SHEET_ID/...'],
--   sheet_range = 'Sheet1!A1:Z1000',
--   skip_leading_rows = 1,
--   autodetect = TRUE
-- );

-- Bigtable
-- CREATE OR REPLACE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.bt_table`
-- WITH FORMAT OPTIONS(
--   format = 'BIGTABLE',
--   source_uri = 'projects/YOUR_PROJECT_ID/instances/YOUR_INSTANCE/tables/YOUR_TABLE',
--   read_rowkey_as_string = TRUE
-- );

-- ---------------------------------------------------------------------
-- 5. Partitioned external table
-- ---------------------------------------------------------------------

CREATE OR REPLACE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.events_partitioned` (
  event_id   STRING,
  user_id    STRING,
  event_type STRING,
  amount     NUMERIC
)
WITH PARTITION BY DATE(event_ts)
WITH FORMAT OPTIONS(
  format = 'PARQUET',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/raw/events/*'],
  hive_partitioning_uri_prefix = 'gs://YOUR_PROJECT_ID-bq-course/raw/events/'
);

-- ---------------------------------------------------------------------
-- 6. Load an external table into a managed table
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.events_internal` AS
SELECT *
FROM `YOUR_PROJECT_ID.raw.events_parquet`;

-- ---------------------------------------------------------------------
-- 7. External table metadata and performance
-- ---------------------------------------------------------------------

SELECT
  table_name,
  table_type,
  creation_time,
  size_bytes,
  row_count
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.TABLES
WHERE table_schema = 'raw'
ORDER BY table_name;

-- Compare external vs managed query cost
SELECT
  'external' AS table_type,
  ROUND(AVG(total_bytes_billed) / POWER(1024, 4) * 6.25, 4) AS avg_cost_usd
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE statement_type LIKE '%events_parquet%'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
UNION ALL
SELECT
  'managed' AS table_type,
  ROUND(AVG(total_bytes_billed) / POWER(1024, 4) * 6.25, 4)
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE statement_type LIKE '%events_internal%'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY);

-- ---------------------------------------------------------------------
-- 8. Hive partitioning in practice
-- ---------------------------------------------------------------------

-- The layout on GCS looks like:
--   gs://bucket/events/date=2026-01-15/hour=00/part-000.parquet
--   gs://bucket/events/date=2026-01-15/hour=01/part-000.parquet
--
-- The prefix tells BigQuery where the partition keys live in the path.

-- Query with the hive partition column
SELECT
  date AS event_date,
  COUNT(*) AS n
FROM `YOUR_PROJECT_ID.raw.events_partitioned`
WHERE date = '2026-01-15'
GROUP BY date;

-- ---------------------------------------------------------------------
-- 9. When to use an external table vs a managed table
-- ---------------------------------------------------------------------

-- EXTERNAL TABLE when:
--   * The data is already in GCS and you do not want to copy it
--   * The files are large and read rarely (cheaper than duplicating)
--   * You need to query files that arrive continuously
--
-- MANAGED TABLE when:
--   * The data is queried frequently (managed tables are faster)
--   * You need schema enforcement, partitioning, or clustering
--   * You need to transform, deduplicate, or join
--   * You want the data inside BigQuery's managed storage
--
-- Rule of thumb: external for the landing zone, managed for everything
-- you actually query repeatedly.

-- ---------------------------------------------------------------------
-- 10. BigLake (managed lakehouse) — external tables with BigQuery features
-- ---------------------------------------------------------------------

-- A BigLake table gives you external data WITH BigQuery's
-- partitioning, clustering, and materialized view support.
-- (Created via the console/API with a connection; shown here for
--  reference because the SQL surface is limited.)

-- CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.biglake_events`
-- WITH CONNECTION `YOUR_PROJECT_ID.us.my_connection`
-- OPTIONS (
--   file_format = 'PARQUET',
--   table_format = 'ICEBERG',
--   storage_uri = 'gs://YOUR_PROJECT_ID-bq-course/lake/events',
--   hive_partition_uri_prefix = 'gs://YOUR_PROJECT_ID-bq-course/lake/events/',
--   require_partition_filter = TRUE
-- );
