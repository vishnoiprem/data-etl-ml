-- ============================================================================
-- 20_extra_topics / create_task.sql
-- ----------------------------------------------------------------------------
-- A scheduled task that aggregates orders every hour.  This is the
-- "scheduled transformation" building block for any cron-style pipeline.
-- Tasks require a dedicated warehouse to run.
--
-- Lecture reference: "Tasks: scheduled SQL" (Section 20, L03)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. The aggregated target table ─────────────────────────────────────
CREATE OR REPLACE TABLE ORDERS_HOURLY_AGG (
    hour_bucket  TIMESTAMP_NTZ,
    order_count  NUMBER,
    total_amount NUMBER(18, 2)
);

-- ── 2. The task that does the work ────────────────────────────────────
--    CRON is in UTC.  Every hour at minute 5.
CREATE OR REPLACE TASK T_ORDERS_HOURLY_AGG
    WAREHOUSE = COMPUTE_WH
    SCHEDULE  = 'USING CRON 5 * * * * UTC'
AS
INSERT INTO ORDERS_HOURLY_AGG (hour_bucket, order_count, total_amount)
SELECT DATE_TRUNC('hour', order_date),
       COUNT(*),
       SUM(total_amount)
FROM   ORDERS_RAW
WHERE  order_date >= DATEADD('hour', -1, CURRENT_TIMESTAMP())
GROUP  BY 1;

-- ── 3. Inspect the task ───────────────────────────────────────────────
SHOW TASKS LIKE 'T_ORDERS_HOURLY_AGG';
DESC TASK T_ORDERS_HOURLY_AGG;

-- ── 4. Tasks start in SUSPENDED state — resume explicitly ────────────
ALTER TASK T_ORDERS_HOURLY_AGG RESUME;

-- ── 5. Trigger a one-off execution to verify the SQL works ────────────
EXECUTE TASK T_ORDERS_HOURLY_AGG;

SELECT * FROM ORDERS_HOURLY_AGG ORDER BY hour_bucket DESC LIMIT 5;

-- ── 6. Suspend again when you are done debugging ──────────────────────
ALTER TASK T_ORDERS_HOURLY_AGG SUSPEND;
