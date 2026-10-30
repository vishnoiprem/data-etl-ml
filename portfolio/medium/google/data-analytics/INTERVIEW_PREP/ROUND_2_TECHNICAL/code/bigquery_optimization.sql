-- BigQuery Optimization SQL Examples
-- Interview-ready patterns for partitioning, clustering, materialized views, and query optimization

-- =============================================================================
-- 1. TABLE CREATION WITH PARTITIONING & CLUSTERING
-- =============================================================================

-- Partition by DATE, Cluster by high-cardinality filter columns (max 4)
CREATE OR REPLACE TABLE `project.dataset.orders_partitioned_clustered`
PARTITION BY DATE(order_timestamp)
CLUSTER BY customer_id, region, status, channel
OPTIONS (
  description = "Orders table partitioned by date, clustered by customer/region/status",
  labels = [("environment", "prod"), ("owner", "data-engineering")],
  require_partition_filter = TRUE  -- Forces partition pruning, prevents full scans
) AS
SELECT * FROM `project.dataset.orders_raw`;

-- =============================================================================
-- 2. PARTITION PRUNING - GOOD vs BAD PATTERNS
-- =============================================================================

-- ✅ GOOD: Direct partition column filter - enables partition pruning
SELECT customer_id, SUM(amount) as total_revenue
FROM `project.dataset.orders_partitioned_clustered`
WHERE DATE(order_timestamp) >= '2024-01-01'
  AND DATE(order_timestamp) < '2024-02-01'
GROUP BY customer_id;

-- ✅ GOOD: Partition filter with clustering column filter
SELECT customer_id, region, COUNT(*) as order_count
FROM `project.dataset.orders_partitioned_clustered`
WHERE DATE(order_timestamp) = '2024-01-15'
  AND customer_id IN ('cust_123', 'cust_456', 'cust_789')
GROUP BY customer_id, region;

-- ❌ BAD: Function on partition column - PREVENTS partition pruning
SELECT customer_id, SUM(amount)
FROM `project.dataset.orders_partitioned_clustered`
WHERE EXTRACT(YEAR FROM order_timestamp) = 2024  -- Full scan!
GROUP BY customer_id;

-- ❌ BAD: Non-deterministic function - PREVENTS caching + partition pruning
SELECT customer_id, SUM(amount)
FROM `project.dataset.orders_partitioned_clustered`
WHERE DATE(order_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)  -- Full scan!
GROUP BY customer_id;

-- ✅ GOOD: Deterministic partition filter with parameter
DECLARE start_date DATE DEFAULT '2024-01-01';
DECLARE end_date DATE DEFAULT '2024-01-31';
SELECT customer_id, SUM(amount)
FROM `project.dataset.orders_partitioned_clustered`
WHERE DATE(order_timestamp) BETWEEN start_date AND end_date
GROUP BY customer_id;

-- =============================================================================
-- 3. CLUSTERING OPTIMIZATION
-- =============================================================================

-- Clustering works best with:
-- 1. High cardinality columns (customer_id, session_id, user_id)
-- 2. Columns used in FILTER clauses
-- 3. Columns used in JOIN keys
-- 4. Max 4 clustering columns

-- Example: Customer 360 table
CREATE OR REPLACE TABLE `project.dataset.customer_360`
PARTITION BY DATE(last_activity_ts)
CLUSTER BY customer_id, tier, region, segment
OPTIONS (require_partition_filter = TRUE) AS
SELECT * FROM `project.dataset.customer_raw`;

-- Query leveraging clustering
SELECT customer_id, tier, COUNT(*) as events
FROM `project.dataset.customer_360`
WHERE DATE(last_activity_ts) >= '2024-01-01'
  AND customer_id = 'cust_12345'  -- Clustering filter - block pruning
GROUP BY customer_id, tier;

-- =============================================================================
-- 4. MATERIALIZED VIEWS FOR PRE-AGGREGATION
-- =============================================================================

-- Create materialized view for daily customer metrics
-- Auto-refreshes, query rewrite enabled by default
CREATE MATERIALIZED VIEW `project.dataset.mv_daily_customer_metrics`
PARTITION BY event_date
CLUSTER BY customer_id, region
OPTIONS (
  enable_refresh = TRUE,
  refresh_interval_minutes = 60,
  allow_non_incremental_definition = FALSE
) AS
SELECT
  DATE(event_timestamp) as event_date,
  customer_id,
  region,
  tier,
  COUNT(*) as event_count,
  SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as purchase_count,
  SUM(CASE WHEN event_type = 'purchase' THEN amount ELSE 0 END) as revenue,
  COUNT(DISTINCT session_id) as session_count,
  MIN(event_timestamp) as first_event_ts,
  MAX(event_timestamp) as last_event_ts
FROM `project.dataset.events_partitioned_clustered`
GROUP BY 1, 2, 3, 4;

-- Query automatically rewritten to use MV (no code changes needed!)
SELECT customer_id, SUM(revenue) as total_revenue
FROM `project.dataset.mv_daily_customer_metrics`
WHERE event_date >= '2024-01-01'
GROUP BY customer_id;

-- =============================================================================
-- 5. SEARCH OPTIMIZATION SERVICE (for point lookups)
-- =============================================================================

-- Create search index for high-cardinality point lookups
CREATE SEARCH INDEX ON `project.dataset.orders_partitioned_clustered` (customer_id);
CREATE SEARCH INDEX ON `project.dataset.orders_partitioned_clustered` (order_id);
CREATE SEARCH INDEX ON `project.dataset.events_partitioned_clustered` (user_id, session_id);

-- Query using search index (10-100x faster for point lookups)
SELECT * FROM `project.dataset.orders_partitioned_clustered`
WHERE customer_id = 'cust_12345';  -- Uses search index

SELECT * FROM `project.dataset.events_partitioned_clustered`
WHERE user_id = 'user_abc' AND session_id = 'sess_xyz';  -- Uses search index

-- =============================================================================
-- 6. QUERY OPTIMIZATION PATTERNS
-- =============================================================================

-- ✅ Column pruning - only select needed columns
SELECT customer_id, amount, order_timestamp
FROM `project.dataset.orders_partitioned_clustered`
WHERE DATE(order_timestamp) = '2024-01-15';

-- ❌ SELECT * - reads all columns
SELECT * FROM `project.dataset.orders_partitioned_clustered`
WHERE DATE(order_timestamp) = '2024-01-15';

-- ✅ Use INT64 for joins instead of STRING when possible
-- Cast in upstream pipeline, not in query

-- ✅ Filter early with WHERE before JOIN
SELECT o.customer_id, o.amount, c.tier
FROM `project.dataset.orders_partitioned_clustered` o
JOIN `project.dataset.customers` c
  ON o.customer_id = c.customer_id
WHERE DATE(o.order_timestamp) = '2024-01-15'  -- Filter first!
  AND c.tier = 'gold';

-- ❌ JOIN first, then filter - processes more data
SELECT o.customer_id, o.amount, c.tier
FROM `project.dataset.orders_partitioned_clustered` o
JOIN `project.dataset.customers` c
  ON o.customer_id = c.customer_id
WHERE c.tier = 'gold'
  AND DATE(o.order_timestamp) = '2024-01-15';

-- =============================================================================
-- 7. SKEW HANDLING (Hot Keys)
-- =============================================================================

-- Problem: customer_id = 'NULL' or 'unknown' has 40% of data
-- Solution 1: Salting for NULL keys
CREATE OR REPLACE TABLE `project.dataset.orders_salted` AS
SELECT
  *,
  CASE
    WHEN customer_id IS NULL OR customer_id = 'unknown'
    THEN CONCAT('salt_', CAST(RAND() * 100 AS INT64))
    ELSE customer_id
  END as salted_customer_id
FROM `project.dataset.orders_raw`;

-- Solution 2: Separate NULL handling in query
SELECT
  COALESCE(NULLIF(customer_id, 'unknown'), 'NULL_CUSTOMER') as clean_customer_id,
  SUM(amount) as revenue
FROM `project.dataset.orders_partitioned_clustered`
WHERE DATE(order_timestamp) >= '2024-01-01'
GROUP BY clean_customer_id;

-- =============================================================================
-- 8. BI ENGINE ACCELERATION
-- =============================================================================

-- Reserve BI Engine capacity (done via Console or API)
-- Minimum 50GB, maximum 5TB per project
-- Check what queries are accelerated:

SELECT
  query,
  acceleration_status,
  bytes_billed,
  slot_ms,
  bi_engine_statistics
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE
  creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
  AND acceleration_status = 'FULL'
ORDER BY slot_ms DESC;

-- =============================================================================
-- 9. SLOT MONITORING & COST ANALYSIS
-- =============================================================================

-- Daily slot utilization and cost
SELECT
  DATE(creation_time) as query_date,
  COUNT(*) as query_count,
  SUM(total_slot_ms) / 1000 / 3600 as total_slot_hours,
  SUM(bytes_billed) / POW(10, 12) as tb_scanned,
  SUM(bytes_billed) / POW(10, 12) * 6.25 as on_demand_cost_usd,
  AVG(total_slot_ms) / 1000 as avg_slot_seconds
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE
  creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND job_type = 'QUERY'
  AND state = 'DONE'
GROUP BY query_date
ORDER BY query_date DESC;

-- Top expensive queries
SELECT
  job_id,
  user_email,
  query,
  total_slot_ms / 1000 / 3600 as slot_hours,
  bytes_billed / POW(10, 12) as tb_scanned,
  bytes_billed / POW(10, 12) * 6.25 as estimated_cost_usd,
  creation_time
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE
  creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND job_type = 'QUERY'
  AND state = 'DONE'
ORDER BY bytes_billed DESC
LIMIT 20;

-- =============================================================================
-- 10. QUERY PLAN ANALYSIS (EXPLAIN)
-- =============================================================================

-- Get query execution plan
EXPLAIN
SELECT customer_id, SUM(amount) as revenue
FROM `project.dataset.orders_partitioned_clustered`
WHERE DATE(order_timestamp) >= '2024-01-01'
GROUP BY customer_id;

-- Key operators to look for:
-- SCAN: Reading table (check partition pruning)
-- FILTER: WHERE clause pushdown
-- AGGREGATE: GROUP BY (consider MV)
-- JOIN: JOIN type (BROADCAST vs SHUFFLE)
-- SHUFFLE: Data redistribution (check clustering alignment)
-- BROADCAST: Small table to all slots (good if <10MB)

-- =============================================================================
-- 11. CACHING OPTIMIZATION
-- =============================================================================

-- ✅ Cacheable: Deterministic, no non-deterministic functions
SELECT customer_id, COUNT(*)
FROM `project.dataset.orders_partitioned_clustered`
WHERE DATE(order_timestamp) >= '2024-01-01'
GROUP BY customer_id;

-- ❌ Not cacheable: Non-deterministic functions
SELECT customer_id, COUNT(*)
FROM `project.dataset.orders_partitioned_clustered`
WHERE DATE(order_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY customer_id;

-- ✅ Cacheable with parameters (parameterized queries)
DECLARE start_date DATE DEFAULT '2024-01-01';
SELECT customer_id, COUNT(*)
FROM `project.dataset.orders_partitioned_clustered`
WHERE DATE(order_timestamp) >= start_date
GROUP BY customer_id;

-- =============================================================================
-- 12. RESERVATION & EDITION COST OPTIMIZATION
-- =============================================================================

-- Check current reservation usage
SELECT
  reservation_id,
  project_id,
  SUM(total_slot_ms) / 1000 / 3600 as slot_hours_used,
  SUM(bytes_billed) / POW(10, 12) as tb_scanned
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT j
JOIN `region-us`.INFORMATION_SCHEMA.RESERVATION_TIMELINE r
  ON j.project_id = r.project_id
WHERE j.creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
GROUP BY reservation_id, project_id;

-- Edition comparison (run in each edition project)
-- Standard: $0.04/slot/hr on-demand
-- Enterprise: $0.06/slot/hr on-demand + CMEK, VPC-SC, 99.99% SLA
-- Editions (Standard/Enterprise): Committed use discounts 30-50%

-- =============================================================================
-- 13. REAL-WORLD OPTIMIZATION CASE: 2TB → 90GB (95% reduction)
-- =============================================================================

-- BEFORE: Full scan, no partitioning, no clustering
-- Cost: $14.38 | Time: 45 min | Bytes: 2.3 TB
SELECT customer_id, COUNT(*) as orders, SUM(amount) as revenue
FROM `project.dataset.orders_raw`
WHERE order_timestamp >= '2024-01-01'
GROUP BY customer_id;

-- AFTER: Partitioned + Clustered + Materialized View
-- Cost: $0.29 | Time: 8 sec | Bytes: 47 GB

-- Step 1: Create optimized table
CREATE OR REPLACE TABLE `project.dataset.orders_optimized`
PARTITION BY DATE(order_timestamp)
CLUSTER BY customer_id, region
OPTIONS (require_partition_filter = TRUE) AS
SELECT * FROM `project.dataset.orders_raw`;

-- Step 2: Create materialized view for daily aggregates
CREATE MATERIALIZED VIEW `project.dataset.mv_daily_customer_revenue`
PARTITION BY event_date
CLUSTER BY customer_id, region
OPTIONS (enable_refresh = TRUE, refresh_interval_minutes = 60) AS
SELECT
  DATE(order_timestamp) as event_date,
  customer_id,
  region,
  COUNT(*) as orders,
  SUM(amount) as revenue
FROM `project.dataset.orders_optimized`
GROUP BY 1, 2, 3;

-- Step 3: Query rewritten to use MV automatically
SELECT customer_id, SUM(revenue) as total_revenue
FROM `project.dataset.mv_daily_customer_revenue`
WHERE event_date >= '2024-01-01'
GROUP BY customer_id;

-- =============================================================================
-- 14. ADVANCED: RECURSIVE CTE FOR HIERARCHICAL DATA
-- =============================================================================

-- Employee hierarchy / category tree
WITH RECURSIVE category_tree AS (
  -- Base case: root categories
  SELECT category_id, category_name, parent_category_id, 0 as level
  FROM `project.dataset.categories`
  WHERE parent_category_id IS NULL

  UNION ALL

  -- Recursive case: children
  SELECT c.category_id, c.category_name, c.parent_category_id, ct.level + 1
  FROM `project.dataset.categories` c
  JOIN category_tree ct ON c.parent_category_id = ct.category_id
  WHERE ct.level < 10  -- Prevent infinite recursion
)
SELECT * FROM category_tree ORDER BY level, category_name;

-- =============================================================================
-- 15. PERFORMANCE TUNING CHECKLIST (COPY FOR INTERVIEW)
-- =============================================================================

/*
BIGQUERY OPTIMIZATION CHECKLIST (MEMORIZE):

□ 1. PARTITION PRUNING
   WHERE event_date >= '2024-01-01'          ✅ GOOD
   WHERE DATE(event_ts) >= '2024-01-01'      ❌ BAD - function on column
   WHERE event_date = CURRENT_DATE()         ❌ BAD - non-deterministic

□ 2. CLUSTERING (Max 4 columns, high cardinality first)
   CLUSTER BY customer_id, region, product_category, channel
   → Enables block pruning + sort optimization

□ 3. COLUMN PRUNING
   SELECT col1, col2 NOT SELECT *

□ 4. MATERIALIZED VIEWS
   Pre-aggregate frequent GROUP BYs (auto-refresh)

□ 5. BI ENGINE
   Reserve 50-100GB for sub-second dashboard queries

□ 6. SLOT ESTIMATION
   Check "slot_ms" in INFORMATION_SCHEMA.JOBS_BY_PROJECT

□ 7. QUERY PLAN
   Look for "Broadcast" joins → consider clustering both sides

□ 8. CACHING
   Deterministic UDFs, no NOW()/RAND() → 100% cache hits

□ 9. RESERVATIONS
   Baseline + Flex for burst, Edition commitment for 30-50% discount

□ 10. SEARCH OPTIMIZATION
   For point lookups on high-cardinality columns (user_id, session_id)
*/

-- =============================================================================
-- END OF BIGQUERY OPTIMIZATION EXAMPLES
-- =============================================================================