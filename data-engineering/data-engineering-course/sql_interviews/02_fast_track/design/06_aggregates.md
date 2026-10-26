# Lesson 06 — Aggregates: COUNT, SUM, AVG, MIN, MAX

> **Goal:** the five built-in reducers and how they handle NULLs.

---

## The five

| Function | What it returns |
|---|---|
| `COUNT(expr)` | Number of rows where `expr` is non-NULL. |
| `SUM(expr)` | Sum of `expr` over all rows. NULLs ignored. |
| `AVG(expr)` | Arithmetic mean of `expr` over non-NULL rows. |
| `MIN(expr)` | Smallest value. |
| `MAX(expr)` | Largest value. |

A query with no `GROUP BY` that uses an aggregate returns
**one row** — the aggregate over the entire input.

```sql
SELECT COUNT(*)        AS n_employees,
       SUM(salary)     AS total_salary,
       AVG(salary)     AS avg_salary,
       MIN(salary)     AS min_salary,
       MAX(salary)     AS max_salary
FROM   Employee;
```

This is the "summary statistics" query. It is the foundation
of every dashboard.

---

## NULL handling

Aggregates skip NULLs, with one important exception: `COUNT(*)`.

- `COUNT(*)` — counts every row in the input, including rows
  where every column is NULL.
- `COUNT(column)` — counts non-NULL values of `column`.
- `SUM(column)` — sums non-NULL values; returns NULL if all
  values are NULL.
- `AVG(column)` — averages non-NULL values; returns NULL if
  all values are NULL.

Two consequences worth knowing:

1. `COUNT(*) <> COUNT(column)` when `column` has any NULLs.
   `COUNT(*)` is always the row count. `COUNT(column)` is the
   non-NULL count of that column.
2. `AVG(x)` is `SUM(x) / COUNT(x)`, *not* `SUM(x) / COUNT(*)`.
   If you want the average over all rows, you need to
   `COALESCE(x, 0)` first.

The classic interview gotcha: *"What's the average salary of
everyone, including the ones with NULL salary?"* The honest
answer is "NULL salaries aren't salaries; we can't include
them in the average without inventing a value."

---

## COUNT(*) vs COUNT(1)

They are the same. `COUNT(*)` and `COUNT(1)` both count every
row in the group. Some engines optimize `COUNT(1)` slightly
differently, but the result is identical and the performance
difference is negligible in modern databases.

`COUNT(DISTINCT column)` counts distinct non-NULL values.
This is the one you reach for when the question is "how many
unique X".

```sql
SELECT COUNT(DISTINCT customer_id) AS unique_customers
FROM   Orders;
```

---

## Multiple aggregates

You can list as many aggregates as you want in the same
SELECT. They all see the same input (the rows in the FROM /
WHERE).

```sql
SELECT department_id,
       COUNT(*)        AS n,
       AVG(salary)     AS avg_salary,
       MAX(salary)     AS top_salary
FROM   Employee
GROUP BY department_id;
```

This is the basic "stats by group" shape. The next lesson
covers `GROUP BY` and `HAVING` in detail.

---

## What NULLs mean in MIN / MAX

`MIN` and `MAX` ignore NULLs entirely. If every value is NULL,
they return NULL. To make `MIN` return 0 instead of NULL when
all values are NULL, wrap it: `COALESCE(MIN(x), 0)`.

---

## Try it

Given `Orders(id, customer_id, total, status, order_date)`,
write three queries:

1. The total revenue (sum of `total`) across all orders.
2. The number of distinct customers who have at least one
   `status = 'delivered'` order.
3. The average order total, ignoring NULL totals.

Then think: *if `total` were nullable, would query 3 give the
right answer?* If not, what would you change?
