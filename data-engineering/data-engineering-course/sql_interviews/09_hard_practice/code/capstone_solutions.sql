-- sql_interviews/code/capstone_solutions.sql
-- Reference answers to the 5 capstone questions.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
--
-- These are one valid answer per question. Many
-- alternatives exist; the comments call out the most
-- important variations.

-- ============================================================
-- Question 1: Top 3 spenders per country
-- ============================================================
-- Approach: DENSE_RANK partitioned by country, ordered by
-- total spend descending. Filter to rank <= 3. Ties
-- preserved.

WITH spend AS (
  SELECT c.id, c.name, c.country, COALESCE(SUM(o.total), 0) AS total_spend
  FROM   Customers c
  LEFT JOIN Orders   o ON o.customer_id = c.id
  GROUP BY c.id, c.name, c.country
),
ranked AS (
  SELECT id, name, country, total_spend,
         DENSE_RANK() OVER (PARTITION BY country
                            ORDER BY total_spend DESC) AS rk
  FROM   spend
)
SELECT country, name, total_spend
FROM   ranked
WHERE  rk <= 3
ORDER BY country, total_spend DESC, name;

-- ============================================================
-- Question 2: Month-over-month revenue growth
-- ============================================================
-- Approach: aggregate revenue per month, then LAG the
-- previous month, then compute the percentage growth.

WITH monthly AS (
  SELECT
    CAST(SUBSTR(order_date, 1, 7) AS TEXT) AS month,
    SUM(total)                            AS revenue
  FROM   Orders
  GROUP BY CAST(SUBSTR(order_date, 1, 7) AS TEXT)
),
with_lag AS (
  SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS prev_revenue
  FROM   monthly
)
SELECT
  month,
  revenue,
  prev_revenue,
  CASE
    WHEN prev_revenue IS NULL OR prev_revenue = 0 THEN NULL
    ELSE ROUND((revenue - prev_revenue) * 100.0 / prev_revenue, 2)
  END AS pct_growth
FROM   with_lag
ORDER BY month;

-- ============================================================
-- Question 3: Users active 7 consecutive days
-- ============================================================
-- Approach: the classic "gaps and islands" pattern. Tag
-- each row with its row number in the (user, date) order;
-- the (date - row_number) stays constant inside a run.
-- Group by (user, run_key) and count.

WITH user_dates AS (
  SELECT DISTINCT user_id, login_date FROM Logins
),
runs AS (
  SELECT
    user_id,
    login_date,
    DATE(login_date, '-' ||
         CAST(ROW_NUMBER() OVER (PARTITION BY user_id
                                 ORDER BY login_date) - 1 AS TEXT) ||
         ' days') AS run_key
  FROM   user_dates
)
SELECT user_id
FROM   runs
GROUP BY user_id, run_key
HAVING COUNT(*) >= 7
ORDER BY user_id;

-- ============================================================
-- Question 4: Pivoted cohort revenue
-- ============================================================
-- Approach: compute signup year (year of first order) per
-- customer. Then aggregate revenue by (signup_year,
-- order_year) and pivot with conditional aggregation.

WITH first_order AS (
  SELECT customer_id, MIN(order_date) AS first_date
  FROM   Orders
  GROUP BY customer_id
),
cohort_orders AS (
  SELECT
    CAST(SUBSTR(fo.first_date, 1, 4) AS INT)  AS signup_year,
    CAST(SUBSTR(o.order_date, 1, 4) AS INT)  AS order_year,
    o.total
  FROM   Orders       o
  JOIN   first_order  fo ON fo.customer_id = o.customer_id
)
SELECT
  signup_year,
  SUM(CASE WHEN order_year = 2022 THEN total ELSE 0 END) AS y2022,
  SUM(CASE WHEN order_year = 2023 THEN total ELSE 0 END) AS y2023,
  SUM(CASE WHEN order_year = 2024 THEN total ELSE 0 END) AS y2024
FROM   cohort_orders
GROUP BY signup_year
ORDER BY signup_year;

-- ============================================================
-- Question 5: Anti-join, three forms
-- ============================================================
-- Each of these returns customers with no delivered
-- orders. The first is unsafe when customer_id can be
-- NULL; the others are NULL-safe.

-- Form 1: NOT IN
-- BUG when customer_id can be NULL: a single NULL kills
-- the result. We filter out NULLs in the subquery to make
-- it safe.
SELECT id, name FROM Customers
WHERE  id NOT IN (
  SELECT customer_id FROM Orders
  WHERE  status = 'delivered' AND customer_id IS NOT NULL
);

-- Form 2: NOT EXISTS (NULL-safe, recommended)
SELECT id, name FROM Customers c
WHERE  NOT EXISTS (
  SELECT 1 FROM Orders o
  WHERE  o.customer_id = c.id AND o.status = 'delivered'
);

-- Form 3: LEFT JOIN ... IS NULL (NULL-safe, less idiomatic)
SELECT c.id, c.name
FROM   Customers c
LEFT JOIN Orders o ON o.customer_id = c.id
                  AND o.status = 'delivered'
WHERE  o.id IS NULL;
