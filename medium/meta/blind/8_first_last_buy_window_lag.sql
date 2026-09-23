-- Problem 8 — Days between each customer's first and last book purchase (using LAG)
-- Difficulty: Medium | Round: Onsite | Pattern: Window function LAG + CTE
--
-- Goal
-- ----
-- For each customer who has 2+ purchases, compute the number of days
-- between their first and last purchase. Order customers by that span
-- descending. This is the kind of question you see on StrataScratch
-- under "Meta".

-- Interview script
-- ----------------
-- "The onsite question expects window functions and CTEs. I want
--  first_purchase_date and last_purchase_date per customer. LAG wouldn't
--  help here — I'll use MIN and MAX as window aggregates. Then subtract
--  in the outer query. Writing it as two CTEs makes the steps explicit:
--  1) per-customer dates, 2) span, 3) filter and order."

-- Solution
-- --------
WITH customer_dates AS (
    SELECT
        customer_id,
        MIN(purchase_date) AS first_purchase,
        MAX(purchase_date) AS last_purchase,
        COUNT(*)           AS purchase_count
    FROM transactions
    GROUP BY customer_id
),
customer_span AS (
    SELECT
        customer_id,
        purchase_count,
        CAST(julianday(last_purchase) - julianday(first_purchase) AS INTEGER) AS days_between
    FROM customer_dates
)
SELECT customer_id, purchase_count, days_between
FROM customer_span
WHERE purchase_count > 1
ORDER BY days_between DESC, customer_id ASC;

-- Expected output (against schema.sql sample data)
-- ------------------------------------------------
-- Customer 1001 (Nina):    2024-03-01 -> 2024-12-01 = 275 days, 4 txs
-- Customer 1002 (Oscar):   2024-02-01 -> 2024-08-15 = 196 days, 3 txs
-- Customer 1004 (Quentin): 2024-03-15 -> 2024-09-10 = 179 days, 3 txs
-- Customer 1005 (Rosa):    2024-04-15 -> 2024-11-30 = 229 days, 8 txs
--
-- (1001, 4, 275)
-- (1002, 3, 196)
-- (1004, 3, 179)
-- (1005, 8, 229)
-- (sorted DESC: 1001 first, 1005 second, 1002 third, 1004 last)

-- Talk-track follow-ups
-- ---------------------
-- "What does LAG have to do with this?"
--   -> LAG is the right call when you want the PREVIOUS row's value
--      (e.g., days since last purchase per transaction). For first/last
--      boundaries, MIN/MAX are correct. Mentioning both shows range.
-- "How would you do this in Postgres?"
--   -> DATE_PART('day', last - first) or (last::date - first::date).
