-- Problem 7 — Sum of total orders and count of unique customers from a transaction table
-- Difficulty: Easy | Round: Screening | Pattern: SUM + COUNT(DISTINCT), CTE to be explicit

-- Goal
-- ----
-- Two scalars (or one row with two columns):
--   * total_orders  = COUNT(*)
--   * unique_customers = COUNT(DISTINCT customer_id)

-- Interview script
-- ----------------
-- "Two simple aggregates on the same table. I'll wrap them in a CTE so
--  the SELECT at the bottom is a single, named pass over the data. The
--  interviewer said 'don't be afraid to use CTEs' — I'll use one here
--  to demonstrate the habit."

-- Solution (CTE version — preferred for onsite clarity)
-- --------
WITH order_metrics AS (
    SELECT
        COUNT(*)              AS total_orders,
        COUNT(DISTINCT customer_id) AS unique_customers
    FROM transactions
)
SELECT * FROM order_metrics;

-- Expected output (against schema.sql sample data)
-- ------------------------------------------------
-- total_orders   = 28
-- unique_customers = 8

-- Talk-track follow-ups
-- ---------------------
-- "What if I want this by month?"
--   -> GROUP BY strftime('%Y-%m', purchase_date) — or DATE_TRUNC('month', ...)
--      in Postgres.
-- "What if I want rolling 7-day unique customers?"
--   -> Window function with a date range; more advanced but worth naming.

-- Talk-track follow-ups
-- ---------------------
-- "What if I want this by month?"
--   -> GROUP BY strftime('%Y-%m', purchase_date) — or DATE_TRUNC('month', ...)
--      in Postgres.
-- "What if I want rolling 7-day unique customers?"
--   -> Window function with a date range; more advanced but worth naming.
