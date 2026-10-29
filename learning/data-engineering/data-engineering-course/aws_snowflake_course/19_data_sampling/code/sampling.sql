-- ============================================================================
-- 19_data_sampling / sampling.sql
-- ----------------------------------------------------------------------------
-- TABLESAMPLE (row-level) and SAMPLE (block-level) — both reduce the rows
-- scanned while keeping statistics representative.  TABLESAMPLE is the
-- deterministic Bernoulli approach; SAMPLE is the system-friendly block one.
--
-- Lecture reference: "Data sampling" (Section 19, L01)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. Build a 1M-row orders table for sampling demos ─────────────────
CREATE OR REPLACE TABLE BIG_ORDERS (
    order_id     NUMBER,
    customer_id  NUMBER,
    total_amount NUMBER(18, 2)
);
INSERT INTO BIG_ORDERS
SELECT SEQ8(),
       UNIFORM(1, 100000, RANDOM()),
       UNIFORM(1000, 99999, RANDOM()) / 100.0
FROM   TABLE(GENERATOR(ROWCOUNT => 1000000));

SELECT COUNT(*) AS source_rows FROM BIG_ORDERS;

-- ── 2. BERNOULLI — each row kept with given probability (10%) ──────────
SELECT COUNT(*) AS sample_rows
FROM   BIG_ORDERS TABLESAMPLE BERNOULLI (10);

-- ── 3. SYSTEM — block-level sampling (faster, less precise) ──────────
SELECT COUNT(*) AS sample_rows
FROM   BIG_ORDERS TABLESAMPLE SYSTEM (5);

-- ── 4. SAMPLE ROWS — exact N rows (latency friendly) ──────────────────
SELECT *
FROM   BIG_ORDERS SAMPLE (1000 ROWS)
ORDER  BY order_id
LIMIT  10;

-- ── 5. Sampling with a deterministic seed (repeatable) ────────────────
SELECT COUNT(*) AS sample_rows
FROM   BIG_ORDERS SAMPLE BERNOULLI (10) SEED (42);

-- ── 6. Compare aggregates: full scan vs sample scan ───────────────────
WITH sample_stats AS (
    SELECT AVG(total_amount) AS avg_amt, STDDEV(total_amount) AS std_amt
    FROM   BIG_ORDERS TABLESAMPLE BERNOULLI (5)
)
SELECT (SELECT AVG(total_amount) FROM BIG_ORDERS) AS full_avg,
       s.avg_amt                                  AS sample_avg,
       100 * (s.avg_amt - (SELECT AVG(total_amount) FROM BIG_ORDERS))
              / (SELECT AVG(total_amount) FROM BIG_ORDERS) AS pct_diff
FROM   sample_stats s;
