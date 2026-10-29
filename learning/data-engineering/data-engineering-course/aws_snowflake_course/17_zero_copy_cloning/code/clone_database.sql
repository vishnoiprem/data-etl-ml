-- ============================================================================
-- 17_zero_copy_cloning / clone_database.sql
-- ----------------------------------------------------------------------------
-- Zero-copy cloning: instant copies of databases, schemas, tables — including
-- historical states via AT (OFFSET => ...).  Storage is shared until data
-- diverges, so clones cost nothing at clone time.
--
-- Lecture reference: "Zero-copy cloning" (Section 17, L01)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. Source table with some data ────────────────────────────────────
CREATE OR REPLACE TABLE SOURCE_ORDERS (
    order_id NUMBER,
    status   VARCHAR(20),
    total    NUMBER(18, 2)
);
INSERT INTO SOURCE_ORDERS VALUES
    (1, 'PLACED',   10.00),
    (2, 'SHIPPED',  20.00),
    (3, 'DELIVERED',30.00);

-- ── 2. Plain clone — same data, no extra storage cost up front ────────
CREATE OR REPLACE TABLE DEV_ORDERS CLONE SOURCE_ORDERS;
SELECT * FROM DEV_ORDERS ORDER BY order_id;

-- ── 3. Mutate the clone — divergence starts here ──────────────────────
UPDATE DEV_ORDERS SET status = 'CANCELLED' WHERE order_id = 1;
SELECT * FROM DEV_ORDERS ORDER BY order_id;

-- ── 4. Time-travel clone — copy as it was 5 minutes ago ───────────────
CREATE OR REPLACE TABLE DEV_ORDERS_5MIN CLONE SOURCE_ORDERS AT (OFFSET => -60*5);
SELECT * FROM DEV_ORDERS_5MIN ORDER BY order_id;

-- ── 5. Schema clone (entire schema in one statement) ──────────────────
CREATE OR REPLACE SCHEMA GETTING_STARTED;
CREATE OR REPLACE SCHEMA CLONE_DEMO_SCHEMA CLONE GETTING_STARTED;
SHOW SCHEMAS LIKE 'CLONE_DEMO_SCHEMA';

-- ── 6. Database clone (e.g. promote a dev DB to a test DB) ────────────
CREATE OR REPLACE DATABASE DEV_DB CLONE SNOWFLAKE_DEMO;
SHOW DATABASES LIKE 'DEV_DB';

-- ── 7. Drop the clones to release shared storage ──────────────────────
--    (Snowflake eventually reclaims storage when ref counts go to 0.)
DROP DATABASE  DEV_DB;
DROP SCHEMA    CLONE_DEMO_SCHEMA;
DROP TABLE     DEV_ORDERS_5MIN;
DROP TABLE     DEV_ORDERS;
DROP TABLE     SOURCE_ORDERS;
