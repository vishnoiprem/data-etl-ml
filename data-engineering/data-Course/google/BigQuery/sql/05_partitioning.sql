-- =====================================================================
-- 05_partitioning.sql
-- Course: BigQuery for Big Data Engineers
-- Covers: Chapters 26-30 (partitioning concepts, ingestion-time,
--         date/integer partitioning, DML, best practices)
--
-- Usage:
--   bq query --use_legacy_sql=false --dry_run < 05_partitioning.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Ingestion-time partitioned table
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.raw.events_ingest_time` (
  event_id   STRING,
  user_id    STRING,
  event_type STRING,
  event_ts   TIMESTAMP,
  payload    JSON
)
PARTITION BY _PARTITIONDATE
OPTIONS(
  description = "Partitioned by ingestion date",
  partition_expiration_days = 90,
  labels = [("tier", "bronze"), ("owner", "data-eng")]
);

-- The pseudo-column
SELECT
  _PARTITIONDATE AS partition_date,
  COUNT(*) AS row_count
FROM `YOUR_PROJECT_ID.raw.events_ingest_time`
GROUP BY _PARTITIONDATE
ORDER BY partition_date DESC;

-- Filter with the pseudo-column
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.raw.events_ingest_time`
WHERE _PARTITIONDATE = DATE '2026-01-15';

-- The timestamp pseudo-column
SELECT
  _PARTITIONTIME AS partition_time,
  COUNT(*)
FROM `YOUR_PROJECT_ID.raw.events_ingest_time`
GROUP BY _PARTITIONTIME
ORDER BY partition_time DESC;

-- Insert into a specific partition (idempotent daily load)
INSERT INTO `YOUR_PROJECT_ID.raw.events_ingest_time$20260115`
  (event_id, user_id, event_type, event_ts, payload)
VALUES
  ('e001', 'u001', 'click', TIMESTAMP '2026-01-15 10:00:00', JSON '{"k": "v"}'),
  ('e002', 'u002', 'view',  TIMESTAMP '2026-01-15 10:05:00', JSON '{"k": "v"}');

-- ---------------------------------------------------------------------
-- 2. Date-column partitioned table
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders` (
  order_id     STRING    NOT NULL,
  customer_id  STRING    NOT NULL,
  order_date   DATE      NOT NULL,
  order_ts     TIMESTAMP,
  total_amount NUMERIC,
  status       STRING,
  region       STRING
)
PARTITION BY order_date
OPTIONS(
  description = "Partitioned by the business order date",
  partition_expiration_days = 730,
  require_partition_filter = TRUE,
  labels = [("tier", "curated"), ("owner", "data-eng")]
);

-- Partition pruning: only one partition is read
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = DATE '2026-01-15';

-- A range of partitions
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date BETWEEN DATE '2026-01-01' AND DATE '2026-01-31';

-- Partition decorator: precise and cheap
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders$20260115`;

SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders$20260101:20260131`;

-- Partition metadata
SELECT
  partition_id,
  total_rows,
  total_logical_bytes
FROM `YOUR_PROJECT_ID.curated.orders.__PARTITIONS__`
ORDER BY partition_id DESC
LIMIT 20;

-- ---------------------------------------------------------------------
-- 3. Integer-range partitioning
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.events_int_range` (
  event_id   STRING,
  event_ts   TIMESTAMP,
  user_id    STRING,
  event_type STRING
)
PARTITION BY RANGE_BUCKET(event_ts, GENERATE_ARRAY_ARRAY(
  TIMESTAMP '2026-01-01 00:00:00',
  TIMESTAMP '2026-12-31 00:00:00',
  INTERVAL 1 MONTH
))
OPTIONS(description = "Monthly integer-range partitions");

SELECT
  partition_id,
  total_rows
FROM `YOUR_PROJECT_ID.curated.events_int_range.__PARTITIONS__`
ORDER BY partition_id;

-- ---------------------------------------------------------------------
-- 4. Partitioning and DML
-- ---------------------------------------------------------------------

-- MERGE must match on the partition key — no partition filter required,
-- but a filter makes it far cheaper
MERGE `YOUR_PROJECT_ID.curated.orders` AS t
USING (
  SELECT
    order_id, customer_id, order_date, order_ts,
    total_amount, status, region
  FROM `YOUR_PROJECT_ID.staging.orders_incoming`
  WHERE order_date = DATE '2026-01-15'
) AS s
ON t.order_id = s.order_id
  AND t.order_date = s.order_date
WHEN MATCHED AND t.status != s.status THEN
  UPDATE SET t.status = s.status, t.total_amount = s.total_amount
WHEN NOT MATCHED THEN
  INSERT (order_id, customer_id, order_date, order_ts, total_amount, status, region)
  VALUES (s.order_id, s.customer_id, s.order_date, s.order_ts, s.total_amount, s.status, s.region);

-- Delete within a single partition
DELETE FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = DATE '2026-01-15'
  AND status = 'cancelled';

-- REPLACE PARTITION — far cheaper than UPDATE for bulk changes
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders$20260115` AS
SELECT
  * EXCEPT(status),
  'complete' AS status
FROM `YOUR_PROJECT_ID.curated.orders$20260115`;

-- ---------------------------------------------------------------------
-- 5. Altering partitions
-- ---------------------------------------------------------------------

-- Set the partition expiration
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
  SET OPTIONS (partition_expiration_days = 365);

-- Add a partition (required before inserting into a specific partition)
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
  ADD PARTITION DATE '20260115';

-- Drop a partition (deletes the data)
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
  DROP PARTITION DATE '20260115';

-- Require partition filters (a cost safety net)
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
  SET OPTIONS (require_partition_filter = TRUE);

-- ---------------------------------------------------------------------
-- 6. Verify partition pruning is happening
-- ---------------------------------------------------------------------

-- The execution details show how many partitions were scanned
SELECT
  total_partitions_scanned,
  total_bytes_billed,
  ROUND(total_bytes_billed / POWER(1024, 4) * 6.25, 4) AS est_cost_usd
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE job_type = 'QUERY'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
ORDER BY creation_time DESC
LIMIT 10;

-- A full scan vs a pruned scan
SELECT 'FULL SCAN' AS scan_type, COUNT(*) AS rows FROM `YOUR_PROJECT_ID.curated.orders`
UNION ALL
SELECT 'PRUNED', COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = DATE '2026-01-15';

-- ---------------------------------------------------------------------
-- 7. Partition maintenance
-- ---------------------------------------------------------------------

-- Copy a partition to another table
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.backup.orders_20260115` AS
SELECT * FROM `YOUR_PROJECT_ID.curated.orders$20260115`;

-- Restore a partition from a backup
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders$20260115` AS
SELECT * FROM `YOUR_PROJECT_ID.backup.orders_20260115`;

-- Swap a partition atomically (zero-downtime refresh)
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.staging.orders_new$20260115` AS
SELECT * FROM `YOUR_PROJECT_ID.curated.orders$20260115`;

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders$20260115` AS
SELECT * FROM `YOUR_PROJECT_ID.staging.orders_new$20260115`;

-- ---------------------------------------------------------------------
-- 8. The 10,000 partition limit — how to stay under it
-- ---------------------------------------------------------------------

-- Daily partitions for 10 years = 3650, safe.
-- Hourly partitions for 10 years = 87,600, too many.
-- Use daily partitioning + a clustered hour column instead:
ALTER TABLE `YOUR_PROJECT_ID.curated.events_hourly`
  SET OPTIONS (
    partition_expiration_days = 90,
    labels = [("tier", "silver")]
  );

-- Count the partitions you have
SELECT
  COUNT(*) AS partition_count
FROM `YOUR_PROJECT_ID.curated.orders.__PARTITIONS__`;

-- ---------------------------------------------------------------------
-- 9. Partitioning best-practice checklist in SQL
-- ---------------------------------------------------------------------

-- Always filter the partition column directly (no functions on it)
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = DATE '2026-01-15';   -- ✅ prunes

-- ❌ This does NOT prune:
-- SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders`
-- WHERE DATE_ADD(order_date, INTERVAL 0 DAY) = DATE '2026-01-15';

-- Use half-open ranges for the best pruning
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date >= DATE '2026-01-01'
  AND order_date <  DATE '2026-02-01';   -- ✅ optimal
