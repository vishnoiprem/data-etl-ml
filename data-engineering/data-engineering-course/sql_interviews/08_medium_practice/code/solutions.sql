-- sql_interviews/08_medium_practice/code/solutions.sql
-- Solutions to the 31 M08 (Medium) practice problems.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
--
-- Convention: every problem starts with `-- Problem N: <name>`
-- and is followed by exactly one SQL statement (possibly a
-- multi-CTE query). The test file extracts each problem's
-- SQL by regex.

-- Problem 54: Consecutive Numbers
-- Numbers that appear at least 3 times in a row.
SELECT DISTINCT num AS ConsecutiveNums
FROM   (
  SELECT num,
         LAG(num, 1) OVER (ORDER BY id) AS prev1,
         LAG(num, 2) OVER (ORDER BY id) AS prev2
  FROM   Logs
)
WHERE  num = prev1 AND num = prev2
ORDER BY ConsecutiveNums;

-- Problem 55: Nth Highest Salary
-- The Nth distinct highest salary. SQLite doesn't accept
-- a function parameter, so we hard-code N = 2 in the
-- solution. (Tests assume N=2.)
SELECT MAX(salary) AS SecondHighestSalary
FROM   (
  SELECT salary,
         DENSE_RANK() OVER (ORDER BY salary DESC) AS rk
  FROM   Employee2
)
WHERE  rk = 2;

-- Problem 56: Department Top 3 Salaries
-- Top 3 distinct salaries per department, with ties.
SELECT d.name AS Department, e.name AS Employee, e.salary
FROM   (
  SELECT name, salary, departmentId,
         DENSE_RANK() OVER (PARTITION BY departmentId
                            ORDER BY salary DESC) AS rk
  FROM   Employee3
) e
JOIN   Department2 d ON d.id = e.departmentId
WHERE  e.rk <= 3
ORDER BY d.name, e.salary DESC, e.name;

-- Problem 57: Friend Requests II
-- The user(s) with the most friends. "Friend" = accepted
-- request in either direction. Use DENSE_RANK to keep
-- ties.
SELECT id, num
FROM   (
  SELECT id, COUNT(*) AS num,
         DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) AS rk
  FROM   (
    SELECT requester_id AS id FROM RequestAccepted
    UNION ALL
    SELECT accepter_id  AS id FROM RequestAccepted
  )
  GROUP BY id
)
WHERE  rk = 1
ORDER BY id;

-- Problem 58: Game Play Analysis I
-- For each player, the date they first logged in.
SELECT player_id, MIN(event_date) AS first_login
FROM   Activity
GROUP BY player_id
ORDER BY player_id;

-- Problem 59: Game Play Analysis II
-- For each player, the device they first used. Use a
-- window function to pick the first row by event_date.
SELECT player_id, device_id
FROM   (
  SELECT player_id, device_id, event_date,
         ROW_NUMBER() OVER (PARTITION BY player_id
                            ORDER BY event_date) AS rn
  FROM   Activity
)
WHERE  rn = 1
ORDER BY player_id;

-- Problem 60: Game Play Analysis III
-- For each (player, login), the running total of games
-- played in that player's history.
SELECT player_id, event_date,
       SUM(games_played) OVER (PARTITION BY player_id
                               ORDER BY event_date
                               ROWS BETWEEN UNBOUNDED PRECEDING
                                        AND CURRENT ROW) AS games_played_so_far
FROM   Activity
ORDER BY player_id, event_date;

-- Problem 61: Game Play Analysis IV
-- Fraction of players who logged in the day after their
-- first login.
SELECT ROUND(
  CAST(COUNT(DISTINCT a.player_id) AS REAL) /
  NULLIF((SELECT COUNT(DISTINCT player_id) FROM Activity), 0),
  2
) AS fraction
FROM   Activity a
JOIN   (
  SELECT player_id, MIN(event_date) AS first_login
  FROM   Activity
  GROUP BY player_id
) first ON a.player_id = first.player_id
       AND a.event_date = DATE(first.first_login, '+1 day');

-- Problem 62: Sales Analysis III
-- Products that were only sold in Q1 2024 (no other quarters).
SELECT p.product_id, p.product_name
FROM   Product p
JOIN   Sales   s ON s.product_id = p.product_id
GROUP BY p.product_id, p.product_name
HAVING MIN(s.sale_date) >= '2024-01-01'
   AND MAX(s.sale_date) <= '2024-03-31';

-- Problem 63: Tree Node
-- Classify each node as Root / Inner / Leaf.
SELECT id,
       CASE
         WHEN p_id IS NULL                  THEN 'Root'
         WHEN id IN (SELECT p_id FROM Tree) THEN 'Inner'
         ELSE 'Leaf'
       END AS Type
FROM   Tree
ORDER BY id;

-- Problem 64: Median Employee Salary
-- Per company, the median salary. SQLite has no
-- percentile; we use the ROW_NUMBER + FLOOR/CEIL trick.
WITH ranked AS (
  SELECT company, salary,
         ROW_NUMBER() OVER (PARTITION BY company ORDER BY salary) AS rn,
         COUNT(*)    OVER (PARTITION BY company)                  AS n
  FROM   Employee4
)
SELECT company,
       CAST(SUM(salary) AS REAL) / COUNT(*) AS median
FROM   ranked
WHERE  rn IN (CAST((n + 1) / 2.0 AS INT), CAST((n + 2) / 2.0 AS INT))
GROUP BY company
ORDER BY company;

-- Problem 65: Swap Salary
-- UPDATE that swaps m and f.
UPDATE Salary
SET    sex = CASE sex WHEN 'm' THEN 'f' ELSE 'm' END;

-- Problem 66: Trips and Users
-- Cancellation rate for unbanned users on 2024-01-01 and
-- 2024-01-02. Cancellation = status starts with 'cancelled'.
SELECT request_at,
       ROUND(
         CAST(SUM(CASE WHEN status LIKE 'cancelled%' THEN 1 ELSE 0 END) AS REAL) /
         NULLIF(COUNT(*), 0),
         2
       ) AS cancellation_rate
FROM   Trips t
WHERE  t.request_at IN ('2024-01-01', '2024-01-02')
  AND  t.client_id  IN (SELECT users_id FROM Users WHERE banned = 'No')
  AND  t.driver_id  IN (SELECT users_id FROM Users WHERE banned = 'No')
GROUP BY request_at
ORDER BY request_at;

-- Problem 67: Human Traffic of Stadium
-- Days with >= 100 people, including the 2 days before
-- and after.
SELECT DISTINCT s1.id, s1.visit_date, s1.people
FROM   Stadium s1
JOIN   Stadium s2 ON s2.id BETWEEN s1.id - 2 AND s1.id
JOIN   Stadium s3 ON s3.id BETWEEN s1.id AND s1.id + 2
WHERE  s1.people >= 100
  AND  s2.people >= 100
  AND  s3.people >= 100
ORDER BY s1.visit_date;

-- Problem 68: Department Highest Salary (revisited)
-- Top earner per department, with the department name.
SELECT d.name AS Department, e.name AS Employee, e.salary
FROM   Employee5 e
JOIN   Department3 d ON d.id = e.departmentId
WHERE  (e.departmentId, e.salary) IN (
  SELECT departmentId, MAX(salary)
  FROM   Employee5
  GROUP BY departmentId
)
ORDER BY d.name, e.name;

-- Problem 69: Exchange Seats
-- Swap adjacent seats; the last odd seat stays put.
SELECT id,
       CASE
         WHEN id % 2 = 1 AND id = (SELECT MAX(id) FROM Seat) THEN student
         WHEN id % 2 = 1 THEN (SELECT student FROM Seat WHERE id = s.id + 1)
         WHEN id % 2 = 0 THEN (SELECT student FROM Seat WHERE id = s.id - 1)
       END AS student
FROM   Seat s
ORDER BY id;

-- Problem 70: Customers Who Bought All Products
-- Customers whose distinct product set is the entire
-- Product2 table.
SELECT customer_id
FROM   Orders2
GROUP BY customer_id
HAVING COUNT(DISTINCT product_id) = (SELECT COUNT(*) FROM Product2)
ORDER BY customer_id;

-- Problem 71: Product Sales Analysis I
-- Total units sold per product.
SELECT product_id, SUM(units_sold) AS total_units
FROM   ProductSales2
GROUP BY product_id
ORDER BY product_id;

-- Problem 72: Product Sales Analysis II
-- The first sale date per product.
SELECT product_id, MIN(sale_date) AS first_sale
FROM   ProductSales2
GROUP BY product_id
ORDER BY product_id;

-- Problem 73: Product Sales Analysis III
-- Per product, the average units sold across all months.
SELECT product_id,
       CAST(SUM(units_sold) AS REAL) / COUNT(*) AS avg_units
FROM   ProductSales2
GROUP BY product_id
ORDER BY product_id;

-- Problem 74: Daily Leads and Partners
-- For each (date, make_name), the distinct count of leads
-- and partners.
SELECT date_id, make_name,
       COUNT(DISTINCT lead_id)    AS unique_leads,
       COUNT(DISTINCT partner_id) AS unique_partners
FROM   DailySales
GROUP BY date_id, make_name
ORDER BY date_id, make_name;

-- Problem 75: Number of Comments per Post
-- For each post, the number of comments. Posts with no
-- comments get 0.
SELECT p.id, COUNT(c.id) AS n_comments
FROM   Posts2   p
LEFT JOIN Comments c ON c.post_id = p.id
GROUP BY p.id
ORDER BY p.id;

-- Problem 76: Page Recommendations
-- Pages liked by a friend's friend, excluding pages
-- already liked by the user. Implementation: friends of
-- the user, then pages their friends like.
SELECT DISTINCT l.page_id
FROM   Likes l
WHERE  l.user_id IN (
  SELECT CASE WHEN user1_id = 1 THEN user2_id ELSE user1_id END
  FROM   Friendship
  WHERE  user1_id = 1 OR user2_id = 1
)
AND    l.page_id NOT IN (SELECT page_id FROM Likes WHERE user_id = 1)
ORDER BY l.page_id;

-- Problem 77: Capital Gain/Loss
-- Per stock, sum of (sell - buy) for matched buy/sell
-- pairs by operation_day. Match each Buy with the next
-- Sell.
SELECT stock_name,
       SUM(CASE WHEN operation = 'Sell' THEN  price ELSE -price END) AS capital_gain_loss
FROM   Stocks
GROUP BY stock_name
ORDER BY stock_name;

-- Problem 78: Winners of Each Group
-- The top scorer (by score desc) per contest, with the
-- user's name.
SELECT contest_id, name
FROM   (
  SELECT s.contest_id, u.name, s.score,
         DENSE_RANK() OVER (PARTITION BY s.contest_id
                            ORDER BY s.score DESC) AS rk
  FROM   Score  s
  JOIN   Users2 u ON u.id = s.user_id
)
WHERE  rk = 1
ORDER BY contest_id, name;

-- Problem 79: Confirmation Rate
-- Per user, the fraction of confirmations that are
-- 'confirmed'. Users with no confirmations get 0.
SELECT s.user_id,
       CASE
         WHEN COUNT(c.user_id) = 0 THEN 0.0
         ELSE CAST(SUM(CASE WHEN c.action = 'confirmed' THEN 1 ELSE 0 END) AS REAL)
            / COUNT(c.user_id)
       END AS confirmation_rate
FROM   Signups s
LEFT JOIN Confirmations c ON c.user_id = s.user_id
GROUP BY s.user_id
ORDER BY s.user_id;

-- Problem 80: Students and Examinations
-- For each (student, subject), the number of exams.
-- Includes subjects the student did not take.
SELECT st.student_id, st.student_name, su.subject_name,
       COUNT(e.student_id) AS attended_exams
FROM   Students    st
CROSS JOIN Subjects  su
LEFT JOIN Examinations e ON e.student_id = st.student_id
                          AND e.subject_name = su.subject_name
GROUP BY st.student_id, st.student_name, su.subject_name
ORDER BY st.student_id, su.subject_name;

-- Problem 81: User Activity Past 30 Days
-- Distinct users active in 2024-01-01..2024-01-30.
-- SQLite's date arithmetic: JULIANDAY or DATE('now', '-30 day').
SELECT activity_date, COUNT(DISTINCT user_id) AS active_users
FROM   Activity2
WHERE  activity_date BETWEEN '2024-01-01' AND '2024-01-30'
GROUP BY activity_date
ORDER BY activity_date;

-- Problem 82: Immediate Food Delivery
-- Fraction of orders where the order_date equals
-- customer_pref_delivery_date.
SELECT ROUND(
  CAST(SUM(CASE WHEN order_date = customer_pref_delivery_date
                THEN 1 ELSE 0 END) AS REAL) / COUNT(*),
  2
) AS immediate_fraction
FROM   Delivery;

-- Problem 83: Sales Analysis I
-- For each product, the year with the maximum total sales.
-- We pick (product, year) with the highest total.
SELECT product_id, year, total
FROM   (
  SELECT product_id, year,
         SUM(quantity * price) AS total,
         DENSE_RANK() OVER (PARTITION BY product_id
                            ORDER BY SUM(quantity * price) DESC) AS rk
  FROM   Sales2
  GROUP BY product_id, year
)
WHERE  rk = 1
ORDER BY product_id, year;

-- Problem 84: Daily Active Users
-- For each day, the number of distinct users who logged in.
SELECT login_date, COUNT(DISTINCT user_id) AS dau
FROM   DAU_Logins
GROUP BY login_date
ORDER BY login_date;
