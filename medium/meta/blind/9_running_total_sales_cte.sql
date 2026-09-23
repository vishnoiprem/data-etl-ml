-- Problem 9 — Running total of sales by date, with a 7-day rolling count of customers
-- Difficulty: Medium-Hard | Round: Onsite | Pattern: Window function SUM OVER + CTE

-- Goal
-- ----
-- For each calendar day with transactions, return:
--   * purchase_date
--   * daily_sales (SUM of amount that day)
--   * running_total_sales (cumulative SUM to date)
--   * rolling_7d_unique_customers (distinct customer count over the last 7 days)

-- Interview script
-- ----------------
-- "The onsite question expects at least one window function. SUM OVER
--  (ORDER BY date) gives running total trivially. The rolling distinct-
--  customer count is harder — there's no DISTINCT inside a window
--  function in standard SQL. The clean solution is: compute daily
--  unique customer counts first, then sum them with a 7-day window."

-- Solution
-- --------
WITH daily AS (
    SELECT
        purchase_date,
        SUM(amount)                       AS daily_sales,
        COUNT(DISTINCT customer_id)       AS daily_unique_customers
    FROM transactions
    GROUP BY purchase_date
),
with_running AS (
    SELECT
        purchase_date,
        daily_sales,
        daily_unique_customers,
        SUM(daily_sales) OVER (ORDER BY purchase_date
                               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total_sales,
        SUM(daily_unique_customers) OVER (ORDER BY purchase_date
                                          ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS rolling_7d_unique_customers
    FROM daily
)
SELECT
    purchase_date,
    daily_sales,
    running_total_sales,
    rolling_7d_unique_customers
FROM with_running
ORDER BY purchase_date;

-- Expected output (subset — against schema.sql sample data)
-- ----------------------------------------------------------
-- 2024-02-01 | 22.75 | 22.75  | 2 (Oscar only — distinct on this day)
-- 2024-02-10 | 35.50 | 58.25  | 3 (Priya)
-- 2024-03-01 | 22.49 | 80.74  | rolling 7 days covers ~Jan 26 .. Mar 01
-- ...
-- The windowed exact numbers depend on date distribution; the SHAPE of
-- the running_total is monotonically increasing.
--
-- Talk-track follow-ups
-- ---------------------
-- "What if dates are missing?"
--   -> Window frames respect actual rows; if 2024-02-05 has no
--      transactions, it's simply not in the table. If you need a
--      continuous date spine, build a calendar CTE first.
-- "Could you do monthly running totals instead?"
--   -> Use strftime('%Y-%m', purchase_date) for grouping; same SUM OVER.
