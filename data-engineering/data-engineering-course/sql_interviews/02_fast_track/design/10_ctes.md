# Lesson 10 — CTEs (WITH clause)

> **Goal:** name a subquery so the rest of the query can read
> it like a table.

---

## Syntax

A CTE (Common Table Expression) is a named subquery defined
at the top of a query:

```sql
WITH high_earners AS (
  SELECT id, name, salary, department_id
  FROM   Employee
  WHERE  salary > 100000
)
SELECT d.department_name, COUNT(*) AS n
FROM   high_earners h
JOIN   Department d ON h.department_id = d.id
GROUP BY d.department_name;
```

`high_earners` is computed once, then joined. The outer query
treats it like a table.

CTEs were added to the SQL standard in 1999 and are now
supported by every major engine (PostgreSQL, MySQL 8+,
SQLite 3.8.3+, SQL Server, Snowflake, BigQuery, Oracle 11g+,
Databricks).

---

## Why use CTEs

Three reasons:

1. **Readability.** A query that uses three subqueries can be
   unreadable when written inline. Three named CTEs read like
   steps in a recipe.

2. **Reuse within a query.** A CTE can be referenced multiple
   times in the main query. A subquery has to be repeated.

3. **Recursion.** Recursive CTEs (Lesson 36 and the medium
   practice module) are how you traverse trees, generate
   sequences, and solve iterative problems in SQL.

CTEs do **not** necessarily perform better than subqueries.
In some engines a CTE is inlined like a subquery; in others
it's materialized once. Don't optimize for performance when
choosing between a CTE and a subquery — optimize for clarity.

---

## Multiple CTEs

Chain them with commas:

```sql
WITH
  base AS (
    SELECT * FROM events WHERE event_type = 'click'
  ),
  per_user AS (
    SELECT user_id, COUNT(*) AS n FROM base GROUP BY user_id
  ),
  top_users AS (
    SELECT user_id FROM per_user WHERE n > 100
  )
SELECT u.email
FROM   top_users t
JOIN   users u ON u.id = t.user_id;
```

The chain reads top-to-bottom. Each CTE sees the previous
ones. This is the closest SQL gets to a function call with a
named argument.

---

## CTEs vs subqueries

```sql
-- Subquery form
SELECT d.department_name, n
FROM   (
  SELECT department_id, COUNT(*) AS n
  FROM   Employee
  WHERE  salary > 100000
  GROUP BY department_id
) h
JOIN   Department d ON d.id = h.department_id;

-- CTE form (same query)
WITH h AS (
  SELECT department_id, COUNT(*) AS n
  FROM   Employee
  WHERE  salary > 100000
  GROUP BY department_id
)
SELECT d.department_name, n
FROM   h
JOIN   Department d ON d.id = h.department_id;
```

They produce the same result. The CTE form is easier to read
and easier to debug. Use the CTE form unless you have a
specific reason not to.

### When subqueries are better

- **Correlated subqueries for `EXISTS` / `NOT EXISTS`.** These
  are sometimes clearer as a subquery in the WHERE clause.

  ```sql
  -- Customers who have at least one order
  SELECT id, name FROM Customer c
  WHERE EXISTS (SELECT 1 FROM Orders o WHERE o.customer_id = c.id);
  ```

- **Scalar subqueries in the SELECT list.** A single value
  pulled from another table.

  ```sql
  SELECT e.name,
         (SELECT MAX(salary) FROM Employee
          WHERE department_id = e.department_id) AS dept_max
  FROM   Employee e;
  ```

  This is sometimes more compact than a window function,
  though slower.

---

## Materialization hint (PostgreSQL)

PostgreSQL has an optimization fence: a CTE is normally
*not* inlined into the outer query. You can override this
with `WITH ... AS MATERIALIZED` or `AS NOT MATERIALIZED`.
SQLite does not have this; CTEs are inlined when possible.

This is rarely a thing you need to know for interviews. It
matters in production query tuning.

---

## Try it

Rewrite each of the following as a CTE-based query:

1. Find the names of customers who have placed at least 3
   orders, with the count.
2. Find the top-earning department (by total salary) and its
   total.
3. Find every employee whose salary is above the company-wide
   average.

In each case, name the intermediate steps. The goal is to
make the query read like English.
