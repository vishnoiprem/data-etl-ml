-- ============================================================================
-- 20_extra_topics / create_stream.sql
-- ----------------------------------------------------------------------------
-- A stream on a table tracks row-level changes (INSERT / UPDATE / DELETE)
-- since the stream was last consumed.  Pair it with a TASK to build a
-- CDC pipeline in pure SQL.
--
-- Lecture reference: "Streams: change tracking" (Section 20, L04)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. The base table (already created in section 4) ──────────────────
--    Re-created defensively so the demo is self-contained.
CREATE OR REPLACE TABLE ORDERS_RAW (
    order_id     NUMBER,
    customer_id  NUMBER,
    order_date   DATE,
    total_amount NUMBER(18, 2)
);
INSERT INTO ORDERS_RAW VALUES
    (1, 100, '2026-10-10', 49.99),
    (2, 200, '2026-10-10', 79.99);

-- ── 2. Create a stream on it ──────────────────────────────────────────
--    APPEND_ONLY = TRUE → only INSERTs are tracked (cheaper, no METADATA$ROW_UPDATE).
CREATE OR REPLACE STREAM S_ORDERS_RAW
    ON TABLE ORDERS_RAW
    APPEND_ONLY = TRUE;

-- Stream is empty before any new changes.
SELECT SYSTEM$STREAM_HAS_DATA('S_ORDERS_RAW') AS has_data,
       COUNT(*)                                AS cdc_rows
FROM   S_ORDERS_RAW;

-- ── 3. Mutate the base table — stream picks it up ────────────────────
INSERT INTO ORDERS_RAW VALUES
    (3, 300, '2026-10-10', 19.99),
    (4, 400, '2026-10-10', 29.99);

SELECT SYSTEM$STREAM_HAS_DATA('S_ORDERS_RAW') AS has_data_after,
       METADATA$ACTION, METADATA$ISUPDATE, METADATA$ROW_ID, order_id
FROM   S_ORDERS_RAW
ORDER  BY order_id;

-- ── 4. Consume the stream into a target table (typical CDC pattern) ───
CREATE OR REPLACE TABLE ORDERS_LANDING (
    order_id     NUMBER,
    customer_id  NUMBER,
    order_date   DATE,
    total_amount NUMBER(18, 2),
    landed_at    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- DML on a stream consumes it (offsets advance).
INSERT INTO ORDERS_LANDING (order_id, customer_id, order_date, total_amount)
SELECT order_id, customer_id, order_date, total_amount
FROM   S_ORDERS_RAW;

SELECT * FROM ORDERS_LANDING ORDER BY order_id;

-- ── 5. After consumption the stream is empty again ────────────────────
SELECT COUNT(*) AS cdc_rows_after_consume FROM S_ORDERS_RAW;
