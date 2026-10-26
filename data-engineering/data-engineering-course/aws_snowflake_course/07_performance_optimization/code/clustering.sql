-- ============================================================================
-- 07_performance_optimization / clustering.sql
-- ----------------------------------------------------------------------------
-- Define a clustering key, re-cluster a large table, and inspect the
-- clustering ratio with SYSTEM$CLUSTERING_INFORMATION.
--
-- Lecture reference: "Clustering keys & automatic clustering" (Section 7, L02)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. A medium-size table to cluster ───────────────────────────────────
CREATE OR REPLACE TABLE ORDERS_LARGE (
    order_id     NUMBER(38, 0),
    customer_id  NUMBER(38, 0),
    order_date   DATE,
    region       VARCHAR(20),
    total_amount NUMBER(18, 2)
);

-- Seed it with 1M rows of synthetic data spread across 5 years.
INSERT INTO ORDERS_LARGE
SELECT
    SEQ8()                                                    AS order_id,
    UNIFORM(1, 100000, RANDOM())                              AS customer_id,
    DATEADD('day', UNIFORM(0, 1825, RANDOM()), '2020-01-01') AS order_date,
    ARRAY_CONSTRUCT('NA','EU','APAC','LATAM','MEA')[UNIFORM(0,4,RANDOM())] AS region,
    UNIFORM(1000, 99999, RANDOM()) / 100.0                    AS total_amount
FROM   TABLE(GENERATOR(ROWCOUNT => 1000000));

-- ── 2. Cluster the table on (order_date, region) ────────────────────────
--    ALTER TABLE ... CLUSTER BY is idempotent.
ALTER TABLE ORDERS_LARGE CLUSTER BY (order_date, region);

-- ── 3. Inspect the clustering ratio before any maintenance ─────────────
SELECT SYSTEM$CLUSTERING_INFORMATION(
    'ORDERS_LARGE',
    '(order_date, region)',
    10  -- average number of micro-partitions per clustering group
) AS clustering_info;

-- ── 4. Show partitions and their min/max (proves the sort is happening) ─
SELECT partition,
       min(order_date)  AS min_d,
       max(order_date)  AS max_d,
       min(region)      AS min_r,
       max(region)      AS max_r,
       row_count        AS rows
FROM   TABLE(INFORMATION_SCHEMA.AUTOMATIC_CLUSTERING_HISTORY(
              TABLE_NAME => 'ORDERS_LARGE', DATE_RANGE_START => '2020-01-01'))
GROUP  BY 1
ORDER  BY 1
LIMIT  20;

-- ── 5. Recreate a clustered clone (zero copy!) for "development" ───────
CREATE OR REPLACE TABLE ORDERS_LARGE_DEV CLONE ORDERS_LARGE;
SELECT COUNT(*) AS dev_rows FROM ORDERS_LARGE_DEV;

-- ── 6. Drop a clustering key (back to automatic) ────────────────────────
ALTER TABLE ORDERS_LARGE DROP CLUSTERING KEY;
