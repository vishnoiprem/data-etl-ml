-- =====================================================================
-- 08_views_and_materialized_views.sql
-- Course: BigQuery for Big Data Engineers
-- Covers: Chapters 35 (views), 36 (materialized views)
--
-- Usage:
--   bq query --use_legacy_sql=false --dry_run < 08_views_and_materialized_views.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. A logical view
-- ---------------------------------------------------------------------

CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.curated.v_active_orders` AS
SELECT
  order_id,
  customer_id,
  order_date,
  total_amount,
  region
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE status = 'active';

-- A view is expanded at query time — the base table is still scanned
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.v_active_orders`
WHERE order_date = DATE '2026-01-15';

-- View metadata
SELECT
  table_name,
  view_definition,
  base_tables
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.VIEWS
WHERE table_schema = 'curated';

-- ---------------------------------------------------------------------
-- 2. A view over a join
-- ---------------------------------------------------------------------

CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.curated.v_orders_with_customer` AS
SELECT
  o.order_id,
  o.order_date,
  o.total_amount,
  o.status,
  c.customer_name,
  c.segment,
  c.country
FROM `YOUR_PROJECT_ID.curated.orders` AS o
LEFT JOIN `YOUR_PROJECT_ID.curated.customers` AS c
  ON o.customer_id = c.customer_id;

-- ---------------------------------------------------------------------
-- 3. An authorized view — row-level security
-- ---------------------------------------------------------------------

-- The view runs with the view owner's permissions and adds a filter.
-- Only rows matching the predicate are visible to the consumer.
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.curated.v_emea_orders` AS
SELECT *
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE region = 'EMEA';

-- Grant a user access to the view ONLY (not the base table)
-- GRANT `roles/bigquery.dataViewer` ON VIEW `YOUR_PROJECT_ID.curated.v_emea_orders`
-- TO "user:analyst@yourcompany.com";

-- A view that uses the caller's identity
-- CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.curated.v_my_rows` AS
-- SELECT * FROM `YOUR_PROJECT_ID.curated.orders`
-- WHERE customer_id = SESSION_USER();

-- ---------------------------------------------------------------------
-- 4. A parameterized view
-- ---------------------------------------------------------------------

CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.curated.v_recent_orders` AS
SELECT
  order_id,
  order_date,
  total_amount
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);

-- ---------------------------------------------------------------------
-- 5. A materialized view
-- ---------------------------------------------------------------------

CREATE MATERIALIZED VIEW `YOUR_PROJECT_ID.mart.mv_daily_revenue`
PARTITION BY order_date
CLUSTER BY region
OPTIONS(
  description = "Daily revenue by region",
  enable_refresh = TRUE,
  max_staleness = INTERVAL 1 HOUR,
  labels = [("tier", "gold"), ("owner", "analytics-eng")]
) AS
SELECT
  order_date,
  region,
  COUNT(*) AS order_count,
  COUNT(DISTINCT customer_id) AS customer_count,
  SUM(total_amount) AS revenue,
  SAFE_DIVIDE(SUM(total_amount), COUNT(*)) AS aov
FROM `YOUR_PROJECT_ID.curated.orders`
GROUP BY order_date, region;

-- Query the MV — it reads the pre-aggregated rows, not the base table
SELECT
  order_date,
  region,
  revenue
FROM `YOUR_PROJECT_ID.mart.mv_daily_revenue`
WHERE order_date = DATE '2026-01-15'
ORDER BY revenue DESC;

-- ---------------------------------------------------------------------
-- 6. MV metadata and refresh
-- ---------------------------------------------------------------------

SELECT
  table_name,
  table_type,
  creation_time,
  last_modified_time,
  refresh_interval_minutes,
  max_staleness,
  base_tables
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.TABLE_STORAGE
WHERE table_schema = 'mart'
  AND table_type = 'MATERIALIZED_VIEW';

SELECT
  table_name,
  refresh_interval_minutes,
  max_staleness,
  last_refresh_time,
  creation_time
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.MATERIALIZED_VIEWS
WHERE table_schema = 'mart';

-- Manual refresh
CALL bq.refresh_materialized_view('YOUR_PROJECT_ID.mart.mv_daily_revenue');

-- ---------------------------------------------------------------------
-- 7. The MV + view pattern — getting around the single-base-table rule
-- ---------------------------------------------------------------------

-- Step 1: a view that does the join
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.mart.v_orders_with_region` AS
SELECT
  o.order_id,
  o.order_date,
  o.total_amount,
  o.customer_id,
  r.region_name,
  r.country
FROM `YOUR_PROJECT_ID.curated.orders` AS o
JOIN `YOUR_PROJECT_ID.curated.regions` AS r
  ON o.region = r.region_id;

-- Step 2: an MV over the view (the view counts as one base table)
CREATE MATERIALIZED VIEW `YOUR_PROJECT_ID.mart.mv_revenue_by_country` AS
SELECT
  order_date,
  country,
  SUM(total_amount) AS revenue,
  COUNT(*) AS order_count
FROM `YOUR_PROJECT_ID.mart.v_orders_with_region`
GROUP BY order_date, country;

-- ---------------------------------------------------------------------
-- 8. Incremental refresh — refresh only what changed
-- ---------------------------------------------------------------------

-- Refresh only the last 3 days (much cheaper than a full refresh)
CALL bq.refresh_materialized_view(
  'YOUR_PROJECT_ID.mart.mv_daily_revenue',
  INTERVAL 3 DAY
);

-- ---------------------------------------------------------------------
-- 9. MV limitations
-- ---------------------------------------------------------------------
--
-- * Exactly ONE base table (a view counts as one)
-- * No subqueries
-- * Cannot GROUP BY an aggregate
-- * No JOIN directly (use the MV + view pattern)
-- * Cannot reference a parameterized view
-- * No GROUP BY on expressions involving aggregates
-- * The base table's partition filter is inherited
-- * MVs cost storage, and each refresh is billed

-- ---------------------------------------------------------------------
-- 10. Views vs MVs — when to use which
-- ---------------------------------------------------------------------
--
-- VIEW:
--   * Zero storage cost
--   * Always fresh (reads the base table at query time)
--   * Costs the same as querying the base table
--   * Use for: joins, row-level security, reusable logic
--
-- MATERIALIZED VIEW:
--   * Costs storage
--   * May be stale (up to max_staleness)
--   * Much cheaper to query (pre-aggregated)
--   * Use for: dashboards, repeated aggregations, expensive filters

-- ---------------------------------------------------------------------
-- 11. Snapshots — a point-in-time copy of a table
-- ---------------------------------------------------------------------

CREATE OR REPLACE SNAPSHOT TABLE `YOUR_PROJECT_ID.backup.orders_snapshot` AS
SELECT *
FROM `YOUR_PROJECT_ID.curated.orders`
FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR);

-- Query a snapshot like a normal table
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.backup.orders_snapshot`;

-- A snapshot is a full copy — it costs storage immediately
SELECT
  table_name,
  size_bytes,
  creation_time
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.TABLES
WHERE table_schema = 'backup';

-- ---------------------------------------------------------------------
-- 12. A complete serving layer
-- ---------------------------------------------------------------------

-- The logical layer
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.mart.v_daily_revenue` AS
SELECT
  order_date,
  region,
  channel,
  COUNT(*) AS order_count,
  SUM(total_amount) AS revenue
FROM `YOUR_PROJECT_ID.curated.orders`
GROUP BY order_date, region, channel;

-- The physical layer
CREATE MATERIALIZED VIEW `YOUR_PROJECT_ID.mart.mv_daily_revenue` AS
SELECT
  order_date,
  region,
  channel,
  COUNT(*) AS order_count,
  SUM(total_amount) AS revenue
FROM `YOUR_PROJECT_ID.curated.orders`
GROUP BY order_date, region, channel;

-- Compare the cost of querying the view vs the MV
SELECT
  'view' AS source,
  SUM(total_bytes_billed) AS total_bytes,
  ROUND(SUM(total_bytes_billed) / POWER(1024, 4) * 6.25, 4) AS est_cost_usd
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE statement_type LIKE '%v_daily_revenue%'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
UNION ALL
SELECT
  'mv' AS source,
  SUM(total_bytes_billed),
  ROUND(SUM(total_bytes_billed) / POWER(1024, 4) * 6.25, 4)
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE statement_type LIKE '%mv_daily_revenue%'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY);
