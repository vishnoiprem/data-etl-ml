-- ============================================================================
-- 05_copy_options / copy_options.sql
-- ----------------------------------------------------------------------------
-- Demonstrate every important COPY INTO option: ON_ERROR, FORCE, SIZE_LIMIT,
-- TRUNCATECOLUMNS, RETURN_FAILED_ONLY.  Each COPY is a separate run so we
-- can compare audit outputs.
--
-- Lecture reference: "COPY INTO options deep dive" (Section 5, L01)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 0. Reuse the same file format & table from the previous demo ────────
--    Re-create the file format defensively in case the script is run alone.
CREATE OR REPLACE FILE FORMAT CSV_FF
    TYPE = CSV
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    TRIM_SPACE = TRUE
    NULL_IF = ('\\N', 'NULL', '');

CREATE OR REPLACE STAGE COPY_DEMO_STAGE FILE_FORMAT = CSV_FF;

CREATE OR REPLACE TABLE COPY_DEMO_RAW (
    id      NUMBER,
    label   VARCHAR(10),                -- intentionally short
    amount  NUMBER(10, 2)
);

-- ── 1. ON_ERROR = ABORT_STATEMENT (default) ─────────────────────────────
--    A single bad row aborts the whole load.
COPY INTO COPY_DEMO_RAW FROM @COPY_DEMO_STAGE/clean.csv
    ON_ERROR = ABORT_STATEMENT;

-- ── 2. ON_ERROR = CONTINUE ──────────────────────────────────────────────
--    Bad rows are skipped but the rest are loaded.  Error count is in the
--    COPY result.
COPY INTO COPY_DEMO_RAW FROM @COPY_DEMO_STAGE/messy.csv
    ON_ERROR = CONTINUE;

-- ── 3. ON_ERROR = SKIP_FILE ─────────────────────────────────────────────
--    The whole file is skipped if any row fails.  Useful for partitioned
--    drops where partial loads are meaningless.
COPY INTO COPY_DEMO_RAW FROM @COPY_DEMO_STAGE/partition_2026_10.csv
    ON_ERROR = SKIP_FILE;

-- ── 4. FORCE = TRUE — re-load a file even if it was already loaded ──────
--    Normally Snowflake skips a file that was already loaded successfully
--    in the last 64 days.  FORCE bypasses that de-duplication.
TRUNCATE TABLE COPY_DEMO_RAW;
COPY INTO COPY_DEMO_RAW FROM @COPY_DEMO_STAGE/clean.csv
    ON_ERROR = CONTINUE
    FORCE    = TRUE;

-- ── 5. SIZE_LIMIT — cap bytes loaded (useful for incremental sampling) ───
COPY INTO COPY_DEMO_RAW FROM @COPY_DEMO_STAGE/clean.csv
    ON_ERROR  = CONTINUE
    SIZE_LIMIT = 1_000_000;             -- 1 MB cap

-- ── 6. TRUNCATECOLUMNS — silently truncate strings that overflow ────────
--    Without this, a 200-char value into VARCHAR(10) would fail the row.
COPY INTO COPY_DEMO_RAW FROM @COPY_DEMO_STAGE/long_labels.csv
    ON_ERROR          = CONTINUE
    TRUNCATECOLUMNS   = TRUE;

-- ── 7. RETURN_FAILED_ONLY — return ONLY the rows that errored ───────────
--    Combine with VALIDATE() to build a remediation workflow.
COPY INTO COPY_DEMO_RAW FROM @COPY_DEMO_STAGE/messy.csv
    ON_ERROR           = CONTINUE
    RETURN_FAILED_ONLY = TRUE;

-- ── 8. Audit the previous copy ──────────────────────────────────────────
SELECT file_name, file_row_number, status, error_count, first_error
FROM   TABLE(VALIDATE(COPY_DEMO_RAW, JOB_QUERY_ID => LAST_QUERY_ID()));
