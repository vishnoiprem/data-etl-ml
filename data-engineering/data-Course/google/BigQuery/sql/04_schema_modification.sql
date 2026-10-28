-- =====================================================================
-- 04_schema_modification.sql
-- Course: BigQuery for Big Data Engineers
-- Covers: Chapters 18 (auto-detection), 19 (schema design),
--         22 (modifying schema), 23 (restore deleted data)
--
-- Usage:
--   bq query --use_legacy_sql=false --dry_run < 04_schema_modification.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Auto-detection — see what BigQuery infers
-- ---------------------------------------------------------------------

-- With autodetect, the first 100 rows decide the schema
-- (demonstrated with a VALUES clause so it is self-contained)
SELECT
  column_name,
  data_type,
  is_nullable
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.COLUMNS
WHERE table_name = 'events' AND table_schema = 'staging'
ORDER BY ordinal_position;

-- ---------------------------------------------------------------------
-- 2. Relaxing a schema during a load
-- ---------------------------------------------------------------------

-- (Load-time flags; shown here for reference. Applied with bq load or
--  the Python LoadJobConfig.)
--
--   --schema_update_options=ALLOW_FIELD_ADDITION
--   --schema_update_options=ALLOW_FIELD_RELAXATION
--   --ignore_unknown_values
--   --ignore_unknown_values=__NULL__ / __UNKNOWN__ / __EXTRA__ / __FORBIDDEN__

-- ---------------------------------------------------------------------
-- 3. The manual, safe way: add fields before loading them
-- ---------------------------------------------------------------------

ALTER TABLE `YOUR_PROJECT_ID.staging.events`
  ADD COLUMN IF NOT EXISTS source_channel STRING;

ALTER TABLE `YOUR_PROJECT_ID.staging.events`
  ADD COLUMN IF NOT EXISTS revenue NUMERIC;

-- Relax a REQUIRED field so incoming nulls do not fail the load
ALTER TABLE `YOUR_PROJECT_ID.staging.events`
  ALTER COLUMN user_id DROP NOT NULL;

-- ---------------------------------------------------------------------
-- 4. A schema-guard: reject rows that do not match expectations
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.staging.events_validated` AS
SELECT
  event_id,
  user_id,
  event_type,
  event_date,
  props,
  source_channel,
  revenue,
  CASE
    WHEN event_id IS NULL             THEN 'MISSING_EVENT_ID'
    WHEN event_type IS NULL           THEN 'MISSING_EVENT_TYPE'
    WHEN event_date IS NULL           THEN 'MISSING_EVENT_DATE'
    WHEN event_date > CURRENT_DATE()  THEN 'FUTURE_DATE'
    WHEN revenue < 0                  THEN 'NEGATIVE_REVENUE'
    ELSE 'OK'
  END AS quality_flag
FROM `YOUR_PROJECT_ID.staging.events`;

-- Keep only the good rows
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.staging.events_clean` AS
SELECT * EXCEPT(quality_flag)
FROM `YOUR_PROJECT_ID.staging.events_validated`
WHERE quality_flag = 'OK';

-- The rejects
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.staging.events_rejects` AS
SELECT * FROM `YOUR_PROJECT_ID.staging.events_validated`
WHERE quality_flag != 'OK';

-- A quality summary
SELECT
  quality_flag,
  COUNT(*) AS row_count,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM `YOUR_PROJECT_ID.staging.events_validated`
GROUP BY quality_flag
ORDER BY row_count DESC;

-- ---------------------------------------------------------------------
-- 5. Flexible column names — make the schema forgiving
-- ---------------------------------------------------------------------

-- BigQuery supports flexible column names for JSON-like data
-- Create a table with a JSON column and let the keys land as columns
SELECT
  JSON_VALUE(data, '$.order_id') AS order_id,
  JSON_VALUE(data, '$.customer.name') AS customer_name,
  JSON_VALUE(data, '$.amount') AS amount
FROM `YOUR_PROJECT_ID.raw.events_json`
LIMIT 100;

-- ---------------------------------------------------------------------
-- 6. Type coercion and quality
-- ---------------------------------------------------------------------

-- Coerce messy strings to typed values
SELECT
  order_id,
  SAFE_CAST(TRIM(order_id) AS STRING) AS clean_order_id,
  SAFE_CAST(REPLACE(total_amount, ',', '') AS NUMERIC) AS amount,
  SAFE_CAST(order_date AS DATE) AS order_dt,
  REGEXP_REPLACE(TRIM(email), r'\s+', '') AS clean_email
FROM `YOUR_PROJECT_ID.staging.raw_orders`
LIMIT 1000;

-- Detect duplicates
SELECT
  order_id,
  COUNT(*) AS occurrences,
  MIN(ingested_at) AS first_seen,
  MAX(ingested_at) AS last_seen
FROM `YOUR_PROJECT_ID.staging.events`
GROUP BY order_id
HAVING COUNT(*) > 1
ORDER BY occurrences DESC
LIMIT 100;

-- Deduplicate, keeping the most recent version of each row
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.staging.events_deduped` AS
SELECT * EXCEPT(row_num)
FROM (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY event_id
      ORDER BY ingested_at DESC
    ) AS row_num
  FROM `YOUR_PROJECT_ID.staging.events`
)
WHERE row_num = 1;

-- ---------------------------------------------------------------------
-- 7. Time travel — read the table as it was
-- ---------------------------------------------------------------------

-- The table as it was 3 hours ago
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders`
  FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 HOUR);

-- The table as it was yesterday
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders`
  FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY);

-- Create a snapshot for a point in time
CREATE OR REPLACE SNAPSHOT TABLE `YOUR_PROJECT_ID.backup.orders_snapshot` AS
SELECT * FROM `YOUR_PROJECT_ID.curated.orders`
  FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR);

-- ---------------------------------------------------------------------
-- 8. Undelete a dropped table
-- ---------------------------------------------------------------------

-- 1. Find the table's creation time (must be within 30 days)
SELECT
  table_name,
  type,
  creation_time,
  expiration_time
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.TABLES
WHERE table_name = 'orders' AND table_schema = 'curated'
ORDER BY creation_time DESC;

-- 2. Undelete (set expiration_time to NULL)
--    CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders`
--    COPY `YOUR_PROJECT_ID.curated.orders`
--    OPTIONS(expiration_timestamp = NULL);

-- 3. Copy the data back if the table is gone
--    CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders` AS
--    SELECT * FROM `YOUR_PROJECT_ID.curated.orders`
--      FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR);

-- ---------------------------------------------------------------------
-- 9. Time travel on a view
-- ---------------------------------------------------------------------

-- Views can be time-travelled too
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.v_active_orders`
  FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR);
