-- Problem 3 — Customers buying 3+ books on BOTH first and last day, excluding one-tx customers
-- Difficulty: Medium | Round: Screening | Pattern: per-day aggregation + HAVING + EXCEPT-style exclusion

-- Goal
-- ----
-- Find customers such that:
--   * They have >= 3 books on their FIRST purchase date
--   * AND >= 3 books on their LAST purchase date
--   * AND they have more than one transaction row overall
--
-- "Excluding those with only one transaction" — interpret as: more than
-- one row in transactions. (Some interviews phrase it as "more than one
-- distinct transaction id", which is the same thing in this dataset.)

-- Interview script
-- ----------------
-- "I need per-customer aggregates of book counts on two specific dates.
--  The first date is min(purchase_date); the last date is max(purchase_date).
--  I'll compute three columns: count_on_first, count_on_last, total_tx.
--  Then HAVING on all three. The exclusion of 'only one transaction' is
--  a HAVING count(*) > 1. Cleanest form: aggregate once per customer."

-- Solution
-- --------
WITH per_customer AS (
    SELECT
        customer_id,
        COUNT(*) AS total_tx,
        SUM(CASE WHEN purchase_date = first_day THEN 1 ELSE 0 END) AS books_on_first_day,
        SUM(CASE WHEN purchase_date = last_day  THEN 1 ELSE 0 END) AS books_on_last_day
    FROM (
        SELECT
            customer_id,
            purchase_date,
            MIN(purchase_date) OVER (PARTITION BY customer_id) AS first_day,
            MAX(purchase_date) OVER (PARTITION BY customer_id) AS last_day
        FROM transactions
    )
    GROUP BY customer_id
)
SELECT customer_id
FROM per_customer
WHERE total_tx > 1
  AND books_on_first_day >= 3
  AND books_on_last_day  >= 3
ORDER BY customer_id;

-- Expected output (against schema.sql sample data)
-- ------------------------------------------------
-- Priya (1003): 3 books on first/last day (which happen to be the same
--   day, 2024-02-10), 3 transactions total.
-- Rosa  (1005): 4 books on 2024-04-15 (first), 4 books on 2024-11-30 (last).
-- Sam   (1006): 3 books on first/last day (2024-04-12).
-- Uma   (1008): 3 books on first/last day (2024-06-15).
-- All four qualify because their first and last dates happen to coincide
-- (one-day-only buyers), and they have > 1 transaction.
--
-- Talk-track follow-ups
-- ---------------------
-- "What if first_day == last_day?"
--   -> Then books_on_first_day == books_on_last_day, and the customer
--      trivially qualifies if it's >= 3 — but they would only have ONE
--      transaction date, so total_tx > 1 would catch them out anyway.
--      Mention this in the interview; it shows you thought about it.
-- "Why use window functions inside a CTE?"
--   -> To compute first_day / last_day once per customer without
--      self-joining transactions. Easier to read than two correlated
--      subqueries.
