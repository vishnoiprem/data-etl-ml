-- sql_interviews/09_hard_practice/code/solutions.sql
-- Solutions to the 14 M09 (Hard) practice problems.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>

-- Problem 85: Median Finder per Group
-- Per department, the median salary. SQLite has no
-- percentile, so use the ROW_NUMBER + FLOOR/CEIL trick.
WITH ranked AS (
  SELECT departmentId, salary,
         ROW_NUMBER() OVER (PARTITION BY departmentId ORDER BY salary) AS rn,
         COUNT(*)    OVER (PARTITION BY departmentId)                  AS n
  FROM   Employee6
)
SELECT departmentId,
       CAST(SUM(salary) AS REAL) / COUNT(*) AS median_salary
FROM   ranked
WHERE  rn IN (CAST((n + 1) / 2.0 AS INT), CAST((n + 2) / 2.0 AS INT))
GROUP BY departmentId
ORDER BY departmentId;

-- Problem 86: Cumulative Sum with Reset
-- A running sum that resets to 0 every 'reset' event.
-- Implementation: assign a "segment" id by counting how
-- many resets preceded this row, then aggregate per
-- segment.
WITH segments AS (
  SELECT id, val, kind,
         SUM(CASE WHEN kind = 'reset' THEN 1 ELSE 0 END)
           OVER (ORDER BY id ROWS BETWEEN UNBOUNDED PRECEDING
                                    AND CURRENT ROW) AS segment
  FROM   Events
)
SELECT id, kind, val,
       SUM(val) OVER (PARTITION BY segment
                      ORDER BY id
                      ROWS BETWEEN UNBOUNDED PRECEDING
                               AND CURRENT ROW) AS running_sum
FROM   segments
ORDER BY id;

-- Problem 87: Tournament Winners
-- For each group, the top scorer. Ties broken by player_id.
SELECT player_id, group_id, score
FROM   (
  SELECT player_id, group_id, score,
         ROW_NUMBER() OVER (PARTITION BY group_id
                            ORDER BY score DESC, player_id) AS rn
  FROM   Tournament
)
WHERE  rn = 1
ORDER BY group_id;

-- Problem 88: Department Salary Ranking w/ Tie-Breaking
-- Per dept, the top earner. Ties preserved (DENSE_RANK).
SELECT departmentId, name, salary
FROM   (
  SELECT departmentId, name, salary,
         DENSE_RANK() OVER (PARTITION BY departmentId
                            ORDER BY salary DESC) AS rk
  FROM   Employee7
)
WHERE  rk = 1
ORDER BY departmentId, name;

-- Problem 89: Stock Price Analysis
-- The maximum profit for each stock if you buy at one
-- price and sell at a strictly later price. Equivalent
-- to max(price - min_so_far) for each prefix.
WITH prefix_min AS (
  SELECT stock_id, ts, price,
         MIN(price) OVER (PARTITION BY stock_id
                          ORDER BY ts
                          ROWS BETWEEN UNBOUNDED PRECEDING
                                   AND 1 PRECEDING) AS min_before
  FROM   StockPrice
)
SELECT stock_id, MAX(price - min_before) AS max_profit
FROM   prefix_min
GROUP BY stock_id;

-- Problem 90: Employee Bonus Calculation
-- For each employee, their bonus. Treat NULL bonus as 0.
SELECT id, name,
       COALESCE(bonus, 0)        AS bonus,
       salary + COALESCE(bonus, 0) AS total_comp
FROM   Employee8
ORDER BY id;

-- Problem 91: Consecutive Available Seats
-- Consecutive seat_ids where both seats are free.
SELECT DISTINCT a.seat_id
FROM   Seats a
JOIN   Seats b ON b.seat_id = a.seat_id + 1
WHERE  a.free = 1 AND b.free = 1
ORDER BY a.seat_id;

-- Problem 92: Rank Scores
-- Dense rank by score descending. No gaps on ties.
SELECT score,
       DENSE_RANK() OVER (ORDER BY score DESC) AS "rank"
FROM   Scores
ORDER BY "rank", score DESC;

-- Problem 93: Department Salary Stats
-- Per dept: avg, max, min, count.
SELECT d.id, d.name,
       COUNT(e.id)         AS n_employees,
       AVG(e.salary)       AS avg_salary,
       MAX(e.salary)       AS max_salary,
       MIN(e.salary)       AS min_salary
FROM   Department5 d
LEFT JOIN Employee9  e ON e.departmentId = d.id
GROUP BY d.id, d.name
ORDER BY d.id;

-- Problem 94: Trip Cancellation Rate by Day
-- Per day, the cancellation rate. Cancellation = status
-- starts with 'cancelled'.
SELECT request_at AS Day,
       ROUND(
         CAST(SUM(CASE WHEN status LIKE 'cancelled%' THEN 1 ELSE 0 END) AS REAL)
         / COUNT(*),
         2
       ) AS "Cancellation Rate"
FROM   Trips2
GROUP BY request_at
ORDER BY request_at;

-- Problem 95: Market Analysis II
-- For each buyer, the number of items sold to them where
-- the item brand matches a brand of an item the buyer
-- themselves sold.
WITH buyer_brands AS (
  -- For each buyer, the set of item brands they have sold.
  SELECT DISTINCT o.seller_id AS user_id, i.item_brand
  FROM   Orders3 o
  JOIN   Items   i ON i.item_id = o.item_id
)
SELECT u.user_id AS buyer_id, u.name AS buyer_name,
       SUM(CASE WHEN EXISTS (
                SELECT 1 FROM buyer_brands bb
                WHERE bb.user_id = u.user_id
                  AND bb.item_brand = i.item_brand
              ) THEN 1 ELSE 0 END) AS same_brand_purchases
FROM   Users3 u
LEFT JOIN Orders3 o ON o.buyer_id = u.user_id
LEFT JOIN Items   i ON i.item_id  = o.item_id
GROUP BY u.user_id, u.name
ORDER BY u.user_id;

-- Problem 96: Sales Analysis by Year
-- Year-over-year growth per product. Compare each year's
-- total to the previous year's.
SELECT s1.product_id, s1.sale_date, s1.amount,
       s2.amount AS prev_year_amount,
       s1.amount - COALESCE(s2.amount, 0) AS yoy_growth
FROM   Sales3 s1
LEFT JOIN Sales3 s2
  ON  s1.product_id = s2.product_id
  AND CAST(SUBSTR(s1.sale_date, 1, 4) AS INT) =
      CAST(SUBSTR(s2.sale_date, 1, 4) AS INT) + 1
ORDER BY s1.product_id, s1.sale_date;

-- Problem 97: Number of Transactions per Visit
-- For each (user, visit_date), the number of transactions.
-- Visits with 0 transactions get 0.
SELECT v.user_id, v.visit_date, COUNT(t.id) AS n_transactions
FROM   Visits v
LEFT JOIN Transactions t ON t.user_id = v.user_id
                        AND t.visit_date = v.visit_date
GROUP BY v.user_id, v.visit_date
ORDER BY v.user_id, v.visit_date;

-- Problem 98: Last Person to Fit in the Bus
-- A bus has capacity 1000. People board in 'turn' order.
-- The last person who still fits is the answer.
SELECT name
FROM   (
  SELECT name, turn, weight,
         SUM(weight) OVER (ORDER BY turn
                           ROWS BETWEEN UNBOUNDED PRECEDING
                                    AND CURRENT ROW) AS cumulative
  FROM   Bus
)
WHERE  cumulative <= 1000
ORDER BY turn DESC
LIMIT 1;
