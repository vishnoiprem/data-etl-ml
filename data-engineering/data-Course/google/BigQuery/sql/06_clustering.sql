-- =====================================================================
-- 06_clustering.sql
-- Course: BigQuery for Big Data Engineers
-- Covers: Chapters 31 (clustering), 32 (partition vs cluster)
--
-- Usage:
--   bq query --use_legacy_sql=false --dry_run < 06_clustering.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. A clustered table
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_clustered` (
  order_id     STRING    NOT NULL,
  customer_id  STRING    NOT NULL,
  order_date   DATE      NOT NULL,
  order_ts     TIMESTAMP,
  total_amount NUMERIC,
  status       STRING,
  region       STRING,
  channel      STRING
)
PARTITION BY order_date
CLUSTER BY customer_id, status, region
OPTIONS(
  description = "Partitioned by date, clustered by customer, status, region",
  partition_expiration_days = 730,
  labels = [("tier", "curated"), ("owner", "data-eng")]
);

-- ---------------------------------------------------------------------
-- 2. Inspect the clustering
-- ---------------------------------------------------------------------

SELECT
  table_name,
  clustering_fields,
  partitioning_type,
  partitioning_field,
  is_partitioned
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.TABLES
WHERE table_name = 'orders_clustered' AND table_schema = 'curated';

-- ---------------------------------------------------------------------
-- 3. Clustered queries — the filters that benefit
-- ---------------------------------------------------------------------

-- Filters on the FIRST clustering column benefit most
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders_clustered`
WHERE order_date = DATE '2026-01-15'
  AND customer_id = 'c0042';

-- Filters on a later clustering column benefit less
SELECT COUNT(*)
FROM `YOUR_PROJECT_ID.curated.orders_clustered`
WHERE order_date = DATE '2026-01-15'
  AND region = 'EMEA';

-- Clustering columns used as equality filters AND range filters
SELECT
  customer_id,
  SUM(total_amount) AS revenue
FROM `YOUR_PROJECT_ID.curated.orders_clustered`
WHERE order_date BETWEEN DATE '2026-01-01' AND DATE '2026-01-31'
  AND customer_id = 'c0042'
  AND status = 'complete'
GROUP BY customer_id;

-- ---------------------------------------------------------------------
-- 4. Adding clustering to an existing table
-- ---------------------------------------------------------------------

ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
  SET OPTIONS (
    clustering_fields = ['customer_id', 'channel']
  );

-- Remove clustering
ALTER TABLE `YOUR_PROJECT_ID.curated.orders`
  SET OPTIONS (clustering_fields = NULL);

-- ---------------------------------------------------------------------
-- 5. Clustering vs partitioning — a worked comparison
-- ---------------------------------------------------------------------

-- Partitioning: coarse, date-based, limits + expirations
SELECT
  'partitioned' AS strategy,
  COUNT(*) AS total_rows
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date = DATE '2026-01-15';

-- Clustering: fine, column-value-based, no row limits
SELECT
  'clustered' AS strategy,
  COUNT(*) AS total_rows
FROM `YOUR_PROJECT_ID.curated.orders_clustered`
WHERE order_date = DATE '2026-01-15'
  AND customer_id = 'c0042';

-- Both together
SELECT
  'partition + cluster' AS strategy,
  COUNT(*) AS total_rows
FROM `YOUR_PROJECT_ID.curated.orders_clustered`
WHERE order_date = DATE '2026-01-15'
  AND customer_id = 'c0042';

-- ---------------------------------------------------------------------
-- 6. The clustering benefit metric (from the execution details)
-- ---------------------------------------------------------------------

-- In the console, the execution details panel shows:
--   "Clustering: 100%"  -> every block was filtered by the clustering key
--   "Clustering: 0%"    -> no benefit
--
-- Query it from INFORMATION_SCHEMA for a fleet-wide view:
SELECT
  job_id,
  total_bytes_billed,
  ROUND(total_bytes_billed / POWER(1024, 4) * 6.25, 4) AS est_cost_usd,
  creation_time
FROM `YOUR_PROJECT_ID`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
  AND total_bytes_billed > 0
ORDER BY total_bytes_billed DESC
LIMIT 20;

-- ---------------------------------------------------------------------
-- 7. Choosing clustering columns
-- ---------------------------------------------------------------------

-- Rank your columns by (filter frequency x selectivity)
-- High frequency + high selectivity = best first clustering column
WITH filter_stats AS (
  SELECT
    'customer_id' AS column_name, 850 AS filter_count, 0.02 AS selectivity
  UNION ALL SELECT 'status', 620, 0.08
  UNION ALL SELECT 'region', 540, 0.15
  UNION ALL SELECT 'channel', 210, 0.35
)
SELECT
  column_name,
  filter_count,
  selectivity,
  ROUND(filter_count * (1 - selectivity), 2) AS rows_skipped,
  ROW_NUMBER() OVER (ORDER BY filter_count * (1 - selectivity) DESC) AS recommended_order
FROM filter_stats;

-- ---------------------------------------------------------------------
-- 8. Clustering limitations and gotchas
-- ---------------------------------------------------------------------

-- Maximum 4 clustering columns
-- ALTER TABLE `t` SET OPTIONS (clustering_fields = ['a','b','c','d']);  -- ✅
-- ALTER TABLE `t` SET OPTIONS (clustering_fields = ['a','b','c','d','e']); -- ❌

-- Clustering does NOT apply to:
--   * External tables
--   * Views
--   * Materialized views (MVs have their own clustering)

-- Clustering has a 5-20% storage overhead (extra sort keys)

-- Re-clustering is automatic and happens in the background over
-- the last ~10 GB of the table, so a new clustering spec is not
-- applied instantly.

-- ---------------------------------------------------------------------
-- 9. Partition vs cluster — decision table
-- ---------------------------------------------------------------------

-- Use PARTITIONING when:
--   * You filter by a time range in almost every query
--   * You want automatic expiration of old data
--   * You want to reduce the number of tables/views you maintain
--
-- Use CLUSTERING when:
--   * You filter by the same 2-4 columns repeatedly
--   * The filter is not a time range (e.g. customer_id, status)
--   * The table is larger than ~1 GB
--
-- Use BOTH when:
--   * Time-based retention AND high-frequency column filters
--
-- Recommended order: cluster on the columns you filter on MOST,
-- not the ones with the highest cardinality. Order matters more
-- than cardinality.
