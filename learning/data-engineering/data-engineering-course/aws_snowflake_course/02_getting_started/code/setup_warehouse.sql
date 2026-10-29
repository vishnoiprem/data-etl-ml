-- ============================================================================
-- 02_getting_started / setup_warehouse.sql
-- ----------------------------------------------------------------------------
-- Idempotently create a small virtual warehouse and grant it to a default
-- role.  Re-running this script is safe; it does not duplicate resources.
--
-- Lecture reference: "Your first warehouse" (Section 2, L03)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

-- Use a dedicated database/schema so demo objects do not pollute ACCOUNTADMIN.
CREATE DATABASE IF NOT EXISTS SNOWFLAKE_DEMO;
USE DATABASE SNOWFLAKE_DEMO;

CREATE SCHEMA IF NOT EXISTS GETTING_STARTED;
USE SCHEMA GETTING_STARTED;

-- The main warehouse: X-Small, scaling policy ECONOMY, auto-suspend after
-- 60 seconds of inactivity.  AUTO_SUSPEND keeps credits cheap.
CREATE WAREHOUSE IF NOT EXISTS COMPUTE_WH
    WITH
        WAREHOUSE_SIZE        = 'XSMALL'
        AUTO_SUSPEND          = 60
        AUTO_RESUME           = TRUE
        INITIALLY_SUSPENDED   = TRUE
        MIN_CLUSTER_COUNT     = 1
        MAX_CLUSTER_COUNT     = 1
        SCALING_POLICY        = 'ECONOMY'
        COMMENT               = 'Default demo warehouse for the masterclass';

-- A second warehouse with MAX_CLUSTER_COUNT > 1 to allow scale-out demos.
CREATE WAREHOUSE IF NOT EXISTS COMPUTE_WH_MULTI
    WITH
        WAREHOUSE_SIZE        = 'XSMALL'
        AUTO_SUSPEND          = 60
        AUTO_RESUME           = TRUE
        INITIALLY_SUSPENDED   = TRUE
        MIN_CLUSTER_COUNT     = 1
        MAX_CLUSTER_COUNT     = 4
        SCALING_POLICY        = 'ECONOMY'
        COMMENT               = 'Scale-out demo warehouse (1..4 clusters)';

-- Grant USAGE to SYSADMIN so any role that inherits it can use the warehouse.
GRANT USAGE ON WAREHOUSE COMPUTE_WH        TO ROLE SYSADMIN;
GRANT USAGE ON WAREHOUSE COMPUTE_WH_MULTI  TO ROLE SYSADMIN;

-- Confirm the warehouse was created with the expected shape.
SHOW WAREHOUSES LIKE 'COMPUTE_WH%';

-- Quick smoke test: resume, run a trivial query, suspend.
ALTER WAREHOUSE COMPUTE_WH RESUME;
SELECT 'warehouse is alive' AS STATUS, CURRENT_WAREHOUSE() AS WH, CURRENT_VERSION() AS VERSION;
ALTER WAREHOUSE COMPUTE_WH SUSPEND;
