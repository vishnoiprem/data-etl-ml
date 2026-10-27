-- =====================================================================
-- 02_tables_and_schemas.sql
-- Course: BigQuery for Big Data Engineers
-- Covers: Chapters 14 (create a table), 19 (schema design),
--         20 (nested & repeated), 22 (modifying schema)
--
-- Usage:
--   bq query --use_legacy_sql=false --dry_run < 02_tables_and_schemas.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. A flat table
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders` (
  order_id     STRING    NOT NULL,
  customer_id  STRING    NOT NULL,
  order_ts     TIMESTAMP NOT NULL,
  order_date   DATE      NOT NULL,
  total_amount NUMERIC   NOT NULL,
  status       STRING    NOT NULL,
  is_completed BOOLEAN,
  source_system STRING   DEFAULT 'app',
  ingested_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
OPTIONS(
  description = "Conformed orders",
  labels = [("tier", "silver"), ("owner", "data-eng")]
);

-- ---------------------------------------------------------------------
-- 2. A table with a nested RECORD and a REPEATED field
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_nested` (
  order_id   STRING    NOT NULL,
  order_date DATE      NOT NULL,
  customer   STRUCT<
    customer_id STRING,
    name       STRING,
    email      STRING,
    address    STRUCT<
      city    STRING,
      country STRING,
      postcode STRING
    >
  >,
  line_items ARRAY<STRUCT<
    product_id STRING,
    quantity   INT64,
    unit_price NUMERIC,
    discount   NUMERIC
  >>,
  metadata   JSON,
  tags       ARRAY<STRING>
)
OPTIONS(
  description = "Orders with nested and repeated columns"
);

-- ---------------------------------------------------------------------
-- 3. A table with a JSON column and a GEOGRAPHY column
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.stores` (
  store_id   STRING NOT NULL,
  store_name STRING,
  location   GEOGRAPHY,
  attributes JSON,
  opened_at  DATE
);

-- ---------------------------------------------------------------------
-- 4. Create a table from a query (CTAS) — the most common pattern
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_enriched` AS
SELECT
  o.order_id,
  o.customer_id,
  o.order_date,
  o.total_amount,
  c.customer_name,
  c.segment,
  ROUND(o.total_amount * COALESCE(fx.rate_to_eur, 1.0), 2) AS amount_eur
FROM `YOUR_PROJECT_ID.curated.orders` AS o
LEFT JOIN `YOUR_PROJECT_ID.curated.customers` AS c
  ON o.customer_id = c.customer_id
LEFT JOIN `YOUR_PROJECT_ID.raw.fx_rates` AS fx
  ON fx.rate_date = o.order_date
  AND fx.currency = 'EUR'
WHERE o.order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY);

-- ---------------------------------------------------------------------
-- 5. Modify a table's schema
-- ---------------------------------------------------------------------

-- Add a column (rewrite on large tables — prefer CTAS for big changes)
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
  ADD COLUMN source_channel STRING DEFAULT 'unknown';

-- Add a nested column
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
  ADD COLUMN shipping STRUCT<city STRING, country STRING>;

-- Drop a column
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
  DROP COLUMN source_channel;

-- Set a column description
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
  ALTER COLUMN total_amount SET OPTIONS (description = "Order total in local currency");

-- Set column policy tags (for sensitive data)
-- ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
--   ALTER COLUMN customer_id SET OPTIONS (
--     policy_tags = ['projects/YOUR_PROJECT_ID/locations/us/taxonomies/1/policyTags/10']
--   );

-- Set the table description and labels
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
  SET OPTIONS (
    description = "Conformed orders from all sources",
    labels = [("tier", "silver"), ("owner", "data-eng"), ("reviewed", "2026-10")]
  );

-- ---------------------------------------------------------------------
-- 6. Schema relaxation — the supported way to evolve a schema
-- ---------------------------------------------------------------------

-- Create a table that allows adding fields and relaxing types
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.staging.events` (
  event_id   STRING    NOT NULL,
  user_id    STRING,
  event_type STRING,
  event_date DATE,
  props      JSON
)
OPTIONS(
  description = "Event schema designed for relaxation"
);

-- RELAX a required field to nullable
ALTER TABLE `YOUR_PROJECT_ID.staging.events`
  ALTER COLUMN user_id DROP NOT NULL;

-- ADD a new field
ALTER TABLE `YOUR_PROJECT_ID.staging.events`
  ADD COLUMN source_channel STRING;

-- ---------------------------------------------------------------------
-- 7. Inspect the schema
-- ---------------------------------------------------------------------

SELECT
  column_name,
  ordinal_position,
  data_type,
  is_nullable,
  description
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.COLUMNS
WHERE table_name = 'orders' AND table_schema = 'curated'
ORDER BY ordinal_position;

-- ---------------------------------------------------------------------
-- 8. Nested data queries
-- ---------------------------------------------------------------------

-- Access a nested field
SELECT
  order_id,
  customer.customer_id,
  customer.address.country
FROM `YOUR_PROJECT_ID.curated.orders_nested`
LIMIT 10;

-- Unnest an array of structs
SELECT
  order_id,
  item.product_id,
  item.quantity,
  item.unit_price * item.quantity AS line_total
FROM `YOUR_PROJECT_ID.curated.orders_nested`,
UNNEST(line_items) AS item
WHERE order_date = DATE '2026-01-15';

-- Flatten an array of scalars
SELECT order_id, tag
FROM `YOUR_PROJECT_ID.curated.orders_nested`,
UNNEST(tags) AS tag;

-- Extract from a JSON column
SELECT
  order_id,
  JSON_VALUE(metadata, '$.channel') AS channel,
  JSON_QUERY(metadata, '$.items') AS items
FROM `YOUR_PROJECT_ID.curated.orders_nested`;

-- ---------------------------------------------------------------------
-- 9. Safe casting — never let a bad row kill the query
-- ---------------------------------------------------------------------

SELECT
  order_id,
  SAFE_CAST(total_amount AS NUMERIC) AS amount_numeric,
  SAFE_CAST(order_ts AS TIMESTAMP) AS ts,
  CASE
    WHEN total_amount IS NULL THEN 'MISSING'
    WHEN SAFE_CAST(total_amount AS NUMERIC) IS NULL THEN 'UNPARSEABLE'
    ELSE 'OK'
  END AS quality_flag
FROM `YOUR_PROJECT_ID.staging.raw_orders`
LIMIT 1000;
