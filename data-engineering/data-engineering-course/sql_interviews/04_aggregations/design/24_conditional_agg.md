# Lesson 24 — Conditional Aggregation with CASE Inside Aggregates

> **Goal:** turn a GROUP BY of one column into many
> computed columns. The pivot query.

---

## The pattern

```sql
SELECT
  department_id,
  COUNT(*)                                    AS n,
  SUM(CASE WHEN hire_date >= '2023-01-01' THEN 1 ELSE 0 END) AS recent_hires,
  SUM(CASE WHEN salary > 100000 THEN salary ELSE 0 END)      AS high_earner_payroll
FROM   Employee
GROUP BY department_id;
```

Each CASE inside the aggregate produces a 0/1 (or zero/value)
contribution. `SUM` collapses the contributions. The result
is one row per department with the computed columns.

This is the foundation of every "pivot" query. It's how you
turn rows into columns without a PIVOT keyword.

---

## Three ways to count conditionally

```sql
-- 1. SUM(CASE)
SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END)

-- 2. COUNT(CASE)  -- counts non-NULL CASE results
COUNT(CASE WHEN status = 'delivered' THEN 1 END)

-- 3. FILTER (PostgreSQL, standard SQL)
COUNT(*) FILTER (WHERE status = 'delivered')
```

The first is the most portable. The second is shorter when
the condition is a single column check. The third is
PostgreSQL-specific (and Snowflake, BigQuery) but reads
beautifully. SQLite does not support FILTER.

For boolean aggregations (true/false columns), the
shortest form is `SUM(bool_col)` or `COUNT(*) FILTER (WHERE
bool_col)`.

---

## NULLIF inside aggregates

A common pattern for "count where x is not the sentinel":

```sql
COUNT(NULLIF(status, 'cancelled'))
```

`NULLIF(status, 'cancelled')` returns NULL when status is
'cancelled', and the status otherwise. `COUNT` ignores NULL,
so this counts the non-cancelled orders. Less verbose than
the CASE form.

```sql
SUM(NULLIF(quantity, 0))  -- sums quantity, treating 0 as NULL (skipped)
```

---

## Pivot: rows to columns

The "pivot" pattern is conditional aggregation with one
column per distinct value of the dimension:

```sql
SELECT
  customer_id,
  SUM(CASE WHEN EXTRACT(YEAR FROM order_date) = 2022 THEN total ELSE 0 END) AS y2022,
  SUM(CASE WHEN EXTRACT(YEAR FROM order_date) = 2023 THEN total ELSE 0 END) AS y2023,
  SUM(CASE WHEN EXTRACT(YEAR FROM order_date) = 2024 THEN total ELSE 0 END) AS y2024
FROM   Orders
GROUP BY customer_id;
```

This produces a row per customer with one column per year.
It's the query behind every cohort-revenue dashboard.

The hardcoded year columns are a code smell — the query
breaks when 2025 arrives. In production you'd generate the
columns dynamically with dbt or a templating engine. For
interviews, the hardcoded form is the expected answer.

---

## Multi-level aggregation

A pivot of a pivot:

```sql
WITH per_user_per_day AS (
  SELECT user_id, DATE(event_date) AS d, COUNT(*) AS n
  FROM   events
  GROUP BY user_id, DATE(event_date)
)
SELECT
  d,
  COUNT(DISTINCT user_id)                  AS dau,
  SUM(CASE WHEN n >= 10 THEN 1 ELSE 0 END) AS power_users,
  SUM(CASE WHEN n = 1  THEN 1 ELSE 0 END) AS one_event_users
FROM   per_user_per_day
GROUP BY d;
```

Step 1: per-user-per-day event counts. Step 2: per-day
buckets of "power user", "one event", "DAU". The first CTE
materializes the intermediate state; the outer query does
the final aggregation.

---

## Try it

Given `Orders(id, customer_id, total, status, order_date)`:

1. For each customer, return `n_total`, `n_delivered`,
   `n_cancelled`, `n_other` in one row.
2. For each month in 2024, return `revenue_delivered`,
   `revenue_cancelled`, `n_orders`.
3. For each customer, return `first_order_date`,
   `last_order_date`, and `n_orders`. Hint: use
   `MIN`/`MAX` in aggregates.
