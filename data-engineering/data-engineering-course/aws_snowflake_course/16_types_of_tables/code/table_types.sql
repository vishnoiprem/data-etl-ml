-- ============================================================================
-- 16_types_of_tables / table_types.sql
-- ----------------------------------------------------------------------------
-- PERMANENT vs TRANSIENT vs TEMPORARY.  Only PERMANENT tables are
-- included in Snowflake's Fail-Safe.  TEMPORARY tables die at session end.
--
-- Lecture reference: "Permanent, Transient, Temporary" (Section 16, L01)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. PERMANENT — default; Fail-Safe 7 days after Time Travel ─────────
CREATE OR REPLACE PERMANENT TABLE ORDERS_PERM (
    order_id NUMBER,
    total    NUMBER(18, 2)
)
DATA_RETENTION_TIME_IN_DAYS = 1;     -- 1 day Time Travel + 7 days Fail-Safe
COMMENT = 'Production orders table — must survive outages';

-- ── 2. TRANSIENT — no Fail-Safe, only Time Travel (1 day std edition) ──
CREATE OR REPLACE TRANSIENT TABLE ORDERS_TXN (
    order_id NUMBER,
    total    NUMBER(18, 2)
)
DATA_RETENTION_TIME_IN_DAYS = 1
COMMENT = 'Staging / dev table — cheaper, no Fail-Safe';

-- ── 3. TEMPORARY — exists only for the lifetime of the session ────────
CREATE OR REPLACE TEMPORARY TABLE ORDERS_TMP (
    order_id NUMBER,
    total    NUMBER(18, 2)
)
COMMENT = 'Scratch table for the running session';

-- ── 4. Show their type / retention for sanity ─────────────────────────
SHOW TABLES LIKE 'ORDERS_%';

-- ── 5. Insert some rows and snapshot ───────────────────────────────────
INSERT INTO ORDERS_PERM VALUES (1, 10), (2, 20);
INSERT INTO ORDERS_TXN  VALUES (1, 10), (2, 20);
INSERT INTO ORDERS_TMP  VALUES (1, 10), (2, 20);

SELECT 'PERM'  AS kind, COUNT(*) AS rows FROM ORDERS_PERM
UNION ALL
SELECT 'TXN'   AS kind, COUNT(*) AS rows FROM ORDERS_TXN
UNION ALL
SELECT 'TMP'   AS kind, COUNT(*) AS rows FROM ORDERS_TMP;

-- ── 6. Convert PERMANENT → TRANSIENT (lowers storage cost) ────────────
--    The reverse (TRANSIENT → PERMANENT) is NOT supported — must clone.
ALTER TABLE ORDERS_PERM SET TRANSIENT;

SHOW TABLES LIKE 'ORDERS_PERM';

-- ── 7. Drop them all cleanly ──────────────────────────────────────────
DROP TABLE ORDERS_TMP;
DROP TABLE ORDERS_TXN;
DROP TABLE ORDERS_PERM;
