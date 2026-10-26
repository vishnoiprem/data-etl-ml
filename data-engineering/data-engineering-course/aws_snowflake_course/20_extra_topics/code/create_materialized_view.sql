-- ============================================================================
-- 20_extra_topics / create_materialized_view.sql
-- ----------------------------------------------------------------------------
-- A materialized view pre-computes the result and Snowflake auto-refreshes
-- it in the background.  Great for dashboards where sub-second latency
-- matters but the source data changes a few times a minute.
--
-- Lecture reference: "Materialized views" (Section 20, L05)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. Source table with realistic data ───────────────────────────────
CREATE OR REPLACE TABLE ORDERS_RAW (
    order_id     NUMBER,
    customer_id  NUMBER,
    order_date   DATE,
    region       VARCHAR(10),
    total_amount NUMBER(18, 2)
);
INSERT INTO ORDERS_RAW
SELECT SEQ8(),
       UNIFORM(1, 100000, RANDOM()),
       DATEADD('day', UNIFORM(0, 365, RANDOM()), '2025-01-01'),
       ARRAY_CONSTRUCT('NA','EU','APAC','LATAM','MEA')[UNIFORM(0,4,RANDOM())],
       UNIFORM(1000, 99999, RANDOM()) / 100.0
FROM   TABLE(GENERATOR(ROWCOUNT => 100000));

-- ── 2. The materialized view (clustered for read speed) ───────────────
CREATE OR REPLACE MATERIALIZED VIEW MV_ORDERS_BY_REGION_DAY
    CLUSTER BY (region, order_date) AS
SELECT region,
       order_date,
       COUNT(*)              AS order_count,
       SUM(total_amount)     AS gross_total,
       AVG(total_amount)     AS avg_total
FROM   ORDERS_RAW
WHERE  order_date >= '2025-01-01'
GROUP  BY region, order_date;

-- ── 3. Query the MV — same SQL, dramatically faster, paid for by Snowflake
SELECT region,
       SUM(order_count) AS orders,
       SUM(gross_total) AS gross
FROM   MV_ORDERS_BY_REGION_DAY
WHERE  order_date BETWEEN '2025-01-01' AND '2025-03-31'
GROUP  BY region
ORDER  BY gross DESC;

-- ── 4. Inspect MV state and refresh history ───────────────────────────
SHOW MATERIALIZED VIEWS LIKE 'MV_ORDERS_BY_REGION_DAY';
SELECT * FROM TABLE(INFORMATION_SCHEMA.MATERIALIZED_VIEW_REFRESH_HISTORY(
              MATERIALIZED_VIEW_NAME => 'MV_ORDERS_BY_REGION_DAY'))
ORDER  BY refresh_start_time DESC
LIMIT  5;
