# 16 — Aggregations, Joins, Window Functions

> **Lesson 16 of 30 — Transformation**

The three SQL patterns every analyst needs. This lesson is a
catalog with worked examples — the kind of thing you can come
back to the day before the interview.

---

## 1. Aggregations: `GROUP BY` + `HAVING`

The basic pattern:

```sql
SELECT
  country,
  COUNT(*) AS user_count,
  AVG(EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM signup_date)) AS avg_tenure_years
FROM users
GROUP BY country
HAVING COUNT(*) > 100
ORDER BY user_count DESC;
```

The senior moves:
- `GROUP BY 1, 2` is fine for ad-hoc queries; spell out the
  column names in production code.
- `HAVING` filters *after* aggregation; `WHERE` filters *before*.
- Always `ORDER BY` a deterministic column when you `LIMIT`.

---

## 2. Joins: the five types

| Join | Returns |
|---|---|
| `INNER JOIN` | Rows that match in both sides |
| `LEFT JOIN` | All rows from left, matched or NULL on right |
| `RIGHT JOIN` | All rows from right, matched or NULL on left |
| `FULL OUTER JOIN` | All rows from both, NULL where no match |
| `CROSS JOIN` | Cartesian product (every row × every row) |

The senior default: `LEFT JOIN` is the workhorse. `INNER JOIN` for
strict relationships. Avoid `RIGHT JOIN` (write it as `LEFT JOIN`
with the tables swapped). Avoid `CROSS JOIN` unless you really
mean it.

```sql
SELECT
  o.order_id,
  o.total,
  u.email
FROM orders o
LEFT JOIN users u ON o.user_id = u.user_id;
```

---

## 3. Self joins and anti joins

A *self join* joins a table to itself. Used for hierarchies:

```sql
SELECT
  e.employee_id,
  e.name,
  m.name AS manager_name
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.employee_id;
```

An *anti join* returns rows that *don't* match:

```sql
-- Find users who have never placed an order
SELECT u.user_id, u.email
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE o.order_id IS NULL;
```

Or in modern SQL:

```sql
SELECT u.user_id, u.email
FROM users u
WHERE NOT EXISTS (
  SELECT 1 FROM orders o WHERE o.user_id = u.user_id
);
```

The senior move: know both forms. `NOT EXISTS` is often faster on
large tables because the planner can short-circuit.

---

## 4. Window functions: the most powerful SQL feature

A window function computes a value *across a set of rows* without
collapsing them. The result has the same number of rows as the
input.

```sql
SELECT
  user_id,
  order_date,
  total,
  -- Running total per user
  SUM(total) OVER (
    PARTITION BY user_id
    ORDER BY order_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS running_total,
  -- Rank per user
  RANK() OVER (
    PARTITION BY user_id
    ORDER BY total DESC
  ) AS order_rank,
  -- Previous order's total
  LAG(total) OVER (
    PARTITION BY user_id
    ORDER BY order_date
  ) AS prev_total
FROM orders;
```

The senior move: name the three window function patterns:
*running totals* (`SUM OVER ORDER BY`), *rankings* (`RANK`,
`DENSE_RANK`, `ROW_NUMBER`), and *lag/lead* (`LAG`, `LEAD`).

---

## 5. `ROW_NUMBER` vs `RANK` vs `DENSE_RANK`

| Function | Ties get... |
|---|---|
| `ROW_NUMBER()` | Distinct ranks (1, 2, 3, 4 — even for ties) |
| `RANK()` | Same rank, then skip (1, 1, 3, 4) |
| `DENSE_RANK()` | Same rank, no skip (1, 1, 2, 3) |

The senior default: `ROW_NUMBER` when you need a strict order
("the most recent order per user"). `RANK` when ties matter
("the top 3 scores"). `DENSE_RANK` when you want dense
ordering ("the top 3 distinct scores").

```sql
-- The "most recent order per user" pattern
SELECT *
FROM (
  SELECT
    o.*,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY order_date DESC) AS rn
  FROM orders o
) ranked
WHERE rn = 1;
```

---

## 6. `LAG` and `LEAD`: the time-series pattern

`LAG` looks at the previous row. `LEAD` looks at the next.

```sql
-- The "days since last order" pattern
SELECT
  user_id,
  order_date,
  LAG(order_date) OVER (PARTITION BY user_id ORDER BY order_date) AS prev_order,
  JULIANDAY(order_date) - JULIANDAY(LAG(order_date) OVER (
    PARTITION BY user_id ORDER BY order_date
  )) AS days_since_last_order
FROM orders;
```

The senior move: this is the *canonical* churn / reactivation
analysis. "Days since last order" is a primary input to almost
every retention model.

---

## 7. CTEs vs subqueries

Use CTEs (`WITH`) for readability. Use subqueries when the
planner benefits.

```sql
-- CTE: readable
WITH order_totals AS (
  SELECT user_id, SUM(total) AS lifetime_value
  FROM orders
  WHERE status IN ('paid', 'shipped', 'delivered')
  GROUP BY user_id
)
SELECT
  u.user_id,
  u.email,
  COALESCE(ot.lifetime_value, 0) AS ltv
FROM users u
LEFT JOIN order_totals ot ON u.user_id = ot.user_id;
```

The senior move: every multi-step query is a CTE. Subqueries only
when the planner needs them.

---

## 8. The interview answer

> "I reach for three SQL patterns: `GROUP BY` + `HAVING` for
> aggregations, `LEFT JOIN` for enrichment, and window functions
> for time-series. The window functions I use most are
> `ROW_NUMBER` for strict ordering, `RANK` / `DENSE_RANK` for
> top-N, and `LAG` / `LEAD` for time-since-event. I prefer CTEs
> over nested subqueries for readability, and I always name the
> window's `PARTITION BY` and `ORDER BY` explicitly so the
> planner knows what to do."

That single paragraph covers: aggregation pattern, join default,
three window function categories, CTE preference, planner
hygiene. Senior answer in 30 seconds.

---

## Try it

Pick a real query from your most recent pipeline. Rewrite it with
CTEs and window functions. If you can't rewrite it, the original
is doing more work than it should — or it's a case where SQL
isn't the right tool.
