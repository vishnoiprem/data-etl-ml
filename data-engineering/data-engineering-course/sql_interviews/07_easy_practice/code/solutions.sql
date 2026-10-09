-- sql_interviews/07_easy_practice/code/solutions.sql
-- Solutions to the 14 M07 (Easy) practice problems.
-- Author: Prem Vishnoi <prem.vishnoi@example.com>
--
-- Each solution is named with a comment so the test file can
-- extract it with a regex and run it as a standalone query.
-- Convention:
--
--   -- Problem 40: Top Earning Employees
--   SELECT ...
--
-- The test file looks for the line `-- Problem N:` and grabs
-- everything until the next `-- Problem M:` (or EOF).

-- Problem 40: Top Earning Employees
-- Return the highest-paid employee per department, with
-- ties preserved (DENSE_RANK = 1 per department).
SELECT name, salary, departmentId
FROM   (
  SELECT name, salary, departmentId,
         DENSE_RANK() OVER (PARTITION BY departmentId
                            ORDER BY salary DESC) AS rk
  FROM   Employee
)
WHERE  rk = 1
ORDER BY departmentId, salary DESC, name;

-- Problem 41: Employee Earnings (running totals)
-- For each employee, return their running total of salary
-- ordered by hire date.
SELECT id, name, hireDate, salary,
       SUM(salary) OVER (PARTITION BY id
                         ORDER BY hireDate
                         ROWS BETWEEN UNBOUNDED PRECEDING
                                  AND CURRENT ROW) AS running_salary
FROM   Employee
ORDER BY id, hireDate;

-- Problem 42: Remove Duplicate Emails
-- A single DELETE statement that removes all but the
-- smallest id for each email. Returns the surviving rows.
-- (Tests run this as a data-mutating query and then SELECT.)
DELETE FROM Person
WHERE  id NOT IN (
  SELECT min_id FROM (
    SELECT MIN(id) AS min_id FROM Person GROUP BY email
  )
);

-- Problem 43: Top Salaries by Department
-- Top 3 employees by salary per department, with ties
-- preserved (DENSE_RANK <= 3).
SELECT name, salary, departmentId
FROM   (
  SELECT name, salary, departmentId,
         DENSE_RANK() OVER (PARTITION BY departmentId
                            ORDER BY salary DESC) AS rk
  FROM   Employee
)
WHERE  rk <= 3
ORDER BY departmentId, rk, name;

-- Problem 44: Instagram Likes
-- Users who have at least 2 posts with more than 100 likes.
-- Uses GROUP BY + HAVING. We synthesize "users with >=2
-- such posts" from the InstagramPost table.
SELECT userId
FROM   InstagramPost
WHERE  likes > 100
GROUP BY userId
HAVING COUNT(*) >= 2
ORDER BY userId;

-- Problem 45: Monthly Post Success Analysis
-- For each user, the number of posts per month and the
-- total likes, with success rate = likes / count.
SELECT userId,
       SUBSTR(postDate, 1, 7) AS month,
       COUNT(*)               AS n_posts,
       SUM(likes)             AS total_likes,
       CAST(SUM(likes) AS REAL) / COUNT(*) AS avg_likes_per_post
FROM   InstagramPost
GROUP BY userId, SUBSTR(postDate, 1, 7)
ORDER BY userId, month;

-- Problem 46: Calculate Test Scores
-- For each student, compute their average score. NULL
-- scores are ignored. Use COALESCE so students with no
-- scores show 0 (rather than NULL).
SELECT student,
       AVG(score)             AS avg_score,
       COALESCE(AVG(score), 0) AS avg_score_or_zero,
       SUM(CASE WHEN score IS NULL THEN 1 ELSE 0 END) AS n_null
FROM   TestScore
GROUP BY student
ORDER BY student;

-- Problem 47: Customer Lifetime Value
-- For each customer, their total spend, number of orders,
-- and average order value. Filter to delivered only.
SELECT c.id, c.name,
       COALESCE(SUM(o.total), 0)    AS lifetime_value,
       COUNT(o.id)                  AS n_orders,
       COALESCE(AVG(o.total), 0)    AS avg_order_value
FROM   Customer c
LEFT JOIN Orders o ON o.customerId = c.id
                  AND o.status     = 'delivered'
GROUP BY c.id, c.name
ORDER BY lifetime_value DESC, c.name;

-- Problem 48: Second Highest Salary
-- The second distinct highest salary. NULL if there is no
-- second distinct value.
SELECT MAX(salary) AS second_highest_salary
FROM   (
  SELECT salary,
         DENSE_RANK() OVER (ORDER BY salary DESC) AS rk
  FROM   Employee
)
WHERE  rk = 2;

-- Problem 49: Customers Who Never Order
-- Customers with no orders. Using NOT IN. We use a
-- subquery that filters out NULL customer IDs to make
-- NOT IN safe.
SELECT id, name
FROM   Customer
WHERE  id NOT IN (
  SELECT customerId FROM Orders WHERE customerId IS NOT NULL
)
ORDER BY id;

-- Problem 50: Department Highest Salary
-- The top earner per department. Equivalent to Problem 40
-- but with the department name joined in.
SELECT d.name AS department,
       e.name AS employee,
       e.salary
FROM   (
  SELECT name, salary, departmentId,
         DENSE_RANK() OVER (PARTITION BY departmentId
                            ORDER BY salary DESC) AS rk
  FROM   Employee
) e
JOIN   Department d ON d.id = e.departmentId
WHERE  e.rk = 1
ORDER BY d.name, e.salary DESC, e.name;

-- Problem 51: Rising Temperature
-- Days where the temperature was higher than the previous
-- day. Using LAG.
SELECT id
FROM   (
  SELECT id, recordDate, temperature,
         LAG(temperature) OVER (ORDER BY recordDate) AS prev_temp
  FROM   Weather
)
WHERE  temperature > prev_temp
ORDER BY id;

-- Problem 52: Classes More Than 5 Students
-- Classes with 5 or more distinct students. GROUP BY +
-- HAVING.
SELECT class
FROM   Course
GROUP BY class
HAVING COUNT(DISTINCT student) >= 5
ORDER BY class;

-- Problem 53: Big Countries
-- Countries with population > 25M or area > 3M. A big
-- country is one whose size or population exceeds a
-- threshold. UNION ALL of the two conditions.
SELECT name, population, area
FROM   Country
WHERE  population > 25000000
   OR  area > 3000000
ORDER BY name;
