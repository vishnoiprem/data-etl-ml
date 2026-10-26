# Lesson 39 — Frame Clauses: ROWS BETWEEN, RANGE BETWEEN

> **Goal:** running totals, moving averages, and other
> "neighborhood" computations.

---

## The idea

A window function has a `PARTITION BY` (which rows are in
the window) and an `ORDER BY` (how they're ordered within
the window). The **frame clause** defines which rows in the
ordered partition are *visible* to the function for each
output row.

```sql
SUM(salary) OVER (
  PARTITION BY department_id
  ORDER BY hire_date
  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

This is a running total: for each row, sum the salaries
from the start of the partition up to and including the
current row.

---

## ROWS vs RANGE

- `ROWS` — counts physical rows. The frame is "the previous
  N rows and the current row".
- `RANGE` — counts by value of the ORDER BY expression.
  The frame is "rows whose ORDER BY value is within N units
  of the current value".

For unique orderings (like `id`), they're the same. For
non-unique orderings (like `hire_date` where multiple
employees share a date), they differ.

```sql
-- ROWS: 3 rows back, current row, 1 row forward
ROWS BETWEEN 3 PRECEDING AND 1 FOLLOWING

-- RANGE: rows within 3 days back, 1 day forward
RANGE BETWEEN INTERVAL '3 days' PRECEDING AND INTERVAL '1 day' FOLLOWING
```

For most interview questions, `ROWS` is what you want.

---

## The default frame

If you don't specify a frame, the default depends on the
function:

- For ranking functions (`ROW_NUMBER`, `RANK`, `DENSE_RANK`,
  `NTILE`): the frame is the entire partition. No frame
  clause needed.
- For aggregates (`SUM`, `AVG`, `MIN`, `MAX`) and offset
  functions (`LAG`, `LEAD`, `FIRST_VALUE`, `LAST_VALUE`):
  the default frame is `RANGE BETWEEN UNBOUNDED PRECEDING
  AND CURRENT ROW` (with `ORDER BY`) or the entire partition
  (without `ORDER BY`).

This is why `LAST_VALUE` doesn't behave as expected without
a frame clause — the default frame is "up to the current
row", not "the whole partition".

---

## Common frame patterns

### 1. Running total

```sql
SUM(salary) OVER (ORDER BY id ROWS BETWEEN UNBOUNDED PRECEDING
                                  AND CURRENT ROW)
```

Equivalent shorthand (default frame with ORDER BY):

```sql
SUM(salary) OVER (ORDER BY id)
```

### 2. 7-day moving average

```sql
AVG(salary) OVER (ORDER BY hire_date
                  ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
```

The current row plus the 6 rows before it. For daily data,
this is a 7-day moving average.

### 3. Centered moving average

```sql
AVG(salary) OVER (ORDER BY hire_date
                  ROWS BETWEEN 3 PRECEDING AND 3 FOLLOWING)
```

The 3 rows before, the current, and the 3 rows after.
Smoother than a trailing window, but uses future data.

### 4. Cumulative from the start

```sql
SUM(salary) OVER (
  ORDER BY id
  ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
)
```

Sum of *all* rows in the partition (not running). With
`ORDER BY` but no `PARTITION BY`, this is the company-wide
total. Each row has the same value.

### 5. Per-partition running total

```sql
SUM(salary) OVER (PARTITION BY department_id
                  ORDER BY hire_date
                  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
```

For each row, the cumulative salary spend in the employee's
department up to and including their hire date.

---

## The shorthand

The most common frame has a shorthand:

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

is the default when you have `ORDER BY` and no explicit
frame. So:

```sql
-- These are equivalent
SUM(x) OVER (ORDER BY id)
SUM(x) OVER (ORDER BY id
             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
```

For moving averages, no shorthand exists — you must write
the frame explicitly.

---

## LAST_VALUE and the frame

`LAST_VALUE` is the most common frame-clause gotcha.

```sql
-- WRONG: returns the current row's value (frame is "up to current")
LAST_VALUE(salary) OVER (PARTITION BY department_id
                        ORDER BY hire_date)

-- RIGHT: returns the highest salary in the partition
LAST_VALUE(salary) OVER (PARTITION BY department_id
                        ORDER BY hire_date
                        ROWS BETWEEN UNBOUNDED PRECEDING
                                 AND UNBOUNDED FOLLOWING)
```

`FIRST_VALUE` doesn't have this problem because the default
frame includes the first row. But `LAST_VALUE` needs the
frame extended to the end of the partition.

---

## A worked example: monthly cumulative revenue

```sql
SELECT
  DATE_TRUNC('month', order_date) AS month,
  SUM(total)                       AS monthly_revenue,
  SUM(SUM(total)) OVER (ORDER BY DATE_TRUNC('month', order_date)
                        ROWS BETWEEN UNBOUNDED PRECEDING
                                 AND CURRENT ROW) AS cumulative_revenue
FROM   Orders
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month;
```

The inner `SUM(total)` is a per-month aggregate. The outer
`SUM(...) OVER (...)` is a window function applied to the
*aggregated* rows. This is the "running total" pattern.

---

## A worked example: 3-month moving average of orders

```sql
SELECT
  DATE_TRUNC('month', order_date) AS month,
  COUNT(*)                        AS n_orders,
  AVG(COUNT(*)) OVER (ORDER BY DATE_TRUNC('month', order_date)
                      ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS ma3
FROM   Orders
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month;
```

For each month, the average of `n_orders` over the current
month and the 2 months before. The nested aggregate (count
per month, then average of those) is a common pattern.

---

## Try it

Given `Orders(id, customer_id, order_date, total)`:

1. Compute a per-customer running total of `total` ordered
   by `order_date`. Use `SUM` + frame clause.
2. Compute a 3-row moving average of order total per
   customer.
3. For each order, find the maximum order total over all of
   the customer's orders. Use `MAX(...) OVER (...)` with
   the right frame clause.
