# Lesson 22 — SUM, AVG with GROUP BY

> **Goal:** the basic "stats by group" shape that underpins
> every dashboard.

---

## The shape

```sql
SELECT <grouping columns>,
       <aggregates>
FROM   <table>
WHERE  <row filter>
GROUP BY <grouping columns>
HAVING <group filter>
ORDER BY <sort>;
```

That's the whole thing. Every analytics query in a data
warehouse is some elaboration of this shape.

---

## The rules

1. Every column in `SELECT` that is not an aggregate must
   appear in `GROUP BY`. (The engine enforces this.)
2. `WHERE` filters rows *before* grouping. Use it for
   per-row predicates.
3. `HAVING` filters groups *after* aggregation. Use it for
   per-group predicates.
4. `ORDER BY` sorts the final result.

---

## Examples

**Total revenue per month:**

```sql
SELECT
  DATE_TRUNC('month', order_date) AS month,
  SUM(total)                      AS revenue,
  COUNT(*)                        AS n_orders
FROM   Orders
WHERE  status = 'delivered'
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month;
```

**Average salary per department, only departments with avg
salary > 80,000:**

```sql
SELECT
  department_id,
  AVG(salary) AS avg_salary,
  COUNT(*)    AS n
FROM   Employee
GROUP BY department_id
HAVING AVG(salary) > 80000
ORDER BY avg_salary DESC;
```

**Total quantity sold per (product, month):**

```sql
SELECT
  product_id,
  DATE_TRUNC('month', order_date) AS month,
  SUM(quantity)                   AS qty,
  SUM(quantity * unit_price)      AS revenue
FROM   OrderItem
GROUP BY product_id, DATE_TRUNC('month', order_date)
ORDER BY product_id, month;
```

---

## Two-level aggregation

A common pattern: aggregate once at a fine grain, then
aggregate again at a coarser grain.

```sql
WITH per_customer AS (
  SELECT customer_id, SUM(total) AS lifetime_value
  FROM   Orders
  GROUP BY customer_id
)
SELECT
  AVG(lifetime_value) AS avg_ltv,
  MIN(lifetime_value) AS min_ltv,
  MAX(lifetime_value) AS max_ltv,
  COUNT(*)            AS n_customers
FROM   per_customer;
```

The CTE computes per-customer LTV. The outer query
aggregates again over the customers. This is the canonical
"lifetime value" query. (M07 contains a hard version of it.)

---

## Ordering of columns in the result

The columns appear in the order you write them in the
SELECT. Grouping columns usually come first, then the
aggregates. Within the aggregates, the convention is
"row count, then sums, then averages, then min/max". The
exact order doesn't matter for correctness; it matters for
readability.

```sql
SELECT
  department_id,
  COUNT(*)    AS n,
  SUM(salary) AS total_salary,
  AVG(salary) AS avg_salary,
  MIN(salary) AS min_salary,
  MAX(salary) AS max_salary
FROM   Employee
GROUP BY department_id;
```

---

## NULL handling in aggregates

Aggregates skip NULLs:

- `SUM(x)` — sum of non-NULL `x`; NULL if all NULL.
- `AVG(x)` — average of non-NULL `x`; NULL if all NULL.
- `MIN(x)` / `MAX(x)` — non-NULL extremes; NULL if all NULL.
- `COUNT(x)` — count of non-NULL `x`; 0 if all NULL.
- `COUNT(*)` — total row count, including NULL-only rows.

To make a NULL aggregate return 0, wrap in `COALESCE`:

```sql
SELECT COALESCE(SUM(salary), 0) FROM Employee;
```

---

## Try it

Given `Orders(id, customer_id, total, status, order_date)`:

1. Total revenue per `status`, sorted by revenue desc.
2. Average order total per customer, only for customers
   with at least 5 orders. Use `HAVING`.
3. Number of distinct customers per month, plus the total
   number of orders per month, in one query.
