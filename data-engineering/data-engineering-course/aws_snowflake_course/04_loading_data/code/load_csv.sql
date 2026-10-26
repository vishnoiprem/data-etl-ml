-- ============================================================================
-- 04_loading_data / load_csv.sql
-- ----------------------------------------------------------------------------
-- Bulk-load a CSV from the user's local @~ stage into a typed table.
-- The file is uploaded with PUT via the SnowSQL CLI before running this.
--
-- Workflow:
--   1. PUT file:///tmp/orders.csv @~/%GETTING_STARTED/orders/  (in SnowSQL)
--   2. Run this script in a worksheet.
--
-- Lecture reference: "Bulk loading with COPY INTO" (Section 4, L02)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. File format for delimited CSV with header row ────────────────────
CREATE OR REPLACE FILE FORMAT CSV_FF
    TYPE                       = CSV
    FIELD_DELIMITER            = ','
    RECORD_DELIMITER           = '\n'
    SKIP_HEADER                = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    TRIM_SPACE                 = TRUE
    NULL_IF                    = ('\\N', 'NULL', '')
    COMPRESSION               = AUTO
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;

-- ── 2. Target table (typed, not VARIANT) ─────────────────────────────────
CREATE OR REPLACE TABLE ORDERS_RAW (
    order_id        NUMBER(38, 0)   NOT NULL,
    customer_id     NUMBER(38, 0),
    order_date      DATE,
    order_status    VARCHAR(20),
    total_amount    NUMBER(18, 2),
    currency        VARCHAR(3)
)
DATA_RETENTION_TIME_IN_DAYS = 1;            -- minimum to keep Time Travel cheap

-- ── 3. Internal stage scoped to the user (PUT uploads here) ─────────────
--    We do not CREATE the @~ stage; it is implicit per user.
--    We do create a named internal stage for clarity.
CREATE OR REPLACE STAGE INTERNAL_LOAD_STAGE
    FILE_FORMAT = CSV_FF
    COMMENT     = 'Internal stage for demo bulk loads';

-- ── 4. List what is on the stage (helpful before COPY) ──────────────────
LIST @INTERNAL_LOAD_STAGE;

-- ── 5. COPY INTO with ON_ERROR = ABORT_STATEMENT (default) ──────────────
COPY INTO ORDERS_RAW
FROM   @INTERNAL_LOAD_STAGE/orders.csv
FILE_FORMAT = (FORMAT_NAME = CSV_FF)
ON_ERROR    = ABORT_STATEMENT
PURGE       = FALSE;            -- keep the file for re-runs / debugging

-- ── 6. Quick sanity check ───────────────────────────────────────────────
SELECT COUNT(*)                AS rows_loaded,
       MIN(order_date)         AS first_order,
       MAX(order_date)         AS last_order,
       SUM(total_amount)       AS gross_total
FROM   ORDERS_RAW;

-- ── 7. Per-file audit trail (forensic detail) ───────────────────────────
SELECT file_name, file_row_number, status, error_count, first_error
FROM   TABLE(VALIDATE(ORDERS_RAW, JOB_QUERY_ID => LAST_QUERY_ID()))
ORDER  BY file_name, file_row_number;
