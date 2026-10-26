-- ============================================================================
-- 03_snowflake_architecture / editions_pricing.sql
-- ----------------------------------------------------------------------------
-- Explore Snowflake editions, account metadata and ACCOUNT_USAGE views.
-- This script is read-only — it does not create or modify any objects.
--
-- Lecture reference: "Editions, pricing & ACCOUNT_USAGE" (Section 3, L05)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE;
USE SCHEMA ACCOUNT_USAGE;

-- ── 1. Which edition is this account on? ─────────────────────────────────
SELECT CURRENT_ACCOUNT()        AS ACCOUNT_NAME,
       CURRENT_REGION()         AS REGION,
       CURRENT_EDITION()        AS EDITION,
       CURRENT_ACCOUNT_NAME()   AS ACCOUNT_LOCATOR;

-- ── 2. Inventory of every warehouse on the account ───────────────────────
--    SHOW is a meta-command, not a SELECT; we wrap it in a result scan.
SHOW WAREHOUSES;
SELECT "name", "state", "size", "min_cluster_count",
       "max_cluster_count", "auto_suspend", "scaling_policy"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
ORDER BY "name";

-- ── 3. Inventory of every database ───────────────────────────────────────
SHOW DATABASES;
SELECT "name", "owner", "created_on", "is_default"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
ORDER BY "name";

-- ── 4. Inventory of every table in SNOWFLAKE_DEMO ────────────────────────
USE DATABASE SNOWFLAKE_DEMO;
SHOW TABLES IN ACCOUNT;
SELECT "database_name", "schema_name", "name", "kind", "rows", "bytes"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
WHERE "database_name" = 'SNOWFLAKE_DEMO'
ORDER BY "schema_name", "name";

-- ── 5. Recent warehouse credit usage (ACCOUNT_USAGE) ─────────────────────
--    Latency can be up to ~3h, so this is for trend analysis, not live ops.
USE SCHEMA SNOWFLAKE.ACCOUNT_USAGE;
SELECT warehouse_name,
       DATE_TRUNC('day', start_time)               AS day,
       SUM(credits_used)                           AS credits
FROM   WAREHOUSE_METERING_HISTORY
WHERE  start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP  BY 1, 2
ORDER  BY 2 DESC, 1;

-- ── 6. Top 10 most expensive queries in the last 7 days ──────────────────
SELECT query_text,
       warehouse_name,
       user_name,
       total_elapsed_time / 1000.0                 AS elapsed_s,
       bytes_scanned / 1024.0 / 1024.0             AS scanned_mb,
       partitions_scanned,
       partitions_total
FROM   QUERY_HISTORY
WHERE  start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER  BY total_elapsed_time DESC
LIMIT  10;
