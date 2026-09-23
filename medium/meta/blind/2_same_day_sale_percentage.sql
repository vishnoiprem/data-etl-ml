-- Problem 2 — Percentage of sales completed on the same day the customer registered
-- Difficulty: Easy | Round: Screening | Pattern: SUM(CASE WHEN ...) + percentage

-- Goal
-- ----
-- Compute: (sales where transaction.purchase_date == customer.registered_on)
--          divided by total sales, as a percentage.

-- Interview script
-- ----------------
-- "I need numerator and denominator. Both are counts of transactions.
--  Numerator is a conditional count, so I'll use SUM(CASE WHEN ... THEN 1
--  ELSE 0 END). Denominator is COUNT(*). I'll guard against div-by-zero
--  with NULLIF. I'll round to 2 decimals because percentages of
--  transactions are usually reported that way."

-- Solution
-- --------
WITH transaction_with_reg AS (
    SELECT
        t.transaction_id,
        t.purchase_date,
        c.registered_on,
        CASE
            WHEN t.purchase_date = c.registered_on THEN 1
            ELSE 0
        END AS is_same_day
    FROM transactions AS t
    JOIN customers    AS c ON c.customer_id = t.customer_id
)
SELECT
    100.0 * SUM(is_same_day) / NULLIF(COUNT(*), 0) AS same_day_pct
FROM transaction_with_reg;

-- Expected output (against schema.sql sample data)
-- ------------------------------------------------
-- Numerator: Oscar's 2 same-day + Priya's 3 + Sam's 3 + Tariq's 1 = 9
-- Total transactions: 28
-- 100.0 * 9 / 28 = 32.142857... -> 32.14

-- Talk-track follow-ups
-- ---------------------
-- "Why NULLIF(COUNT(*), 0)?"
--   -> Division by zero returns NULL in SQL; I prefer a clean NULL
--      result over a runtime error so the query stays runnable.
-- "Could you also return total_sales and same_day_sales as columns?"
--   -> Yes — add them to the SELECT.
