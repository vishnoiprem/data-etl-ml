# Lesson 37 — LAG, LEAD, FIRST_VALUE, LAST_VALUE

> **Goal:** read the previous, next, or boundary row in the
> same window.

---

## LAG and LEAD

`LAG(x)` returns the value of `x` in the *previous* row of
the window. `LEAD(x)` returns the value in the *next* row.

```sql
SELECT
  record_date,
  temperature,
  LAG(temperature)  OVER (ORDER BY record_date) AS prev_temp,
  LEAD(temperature) OVER (ORDER BY record_date) AS next_temp
FROM   Weather;
```

For the first row, `LAG` is NULL. For the last row, `LEAD`
is NULL. This is the "compare to the previous row" pattern.

### The OFFSET argument

By default, `LAG` looks 1 row back. You can pass an offset:

```sql
LAG(temperature, 2) OVER (ORDER BY record_date)  -- 2 rows back
LAG(temperature, 7) OVER (ORDER BY record_date)  -- a week back, if daily data
```

### The DEFAULT argument

If you want a default for the missing values (instead of
NULL):

```sql
LAG(temperature, 1, 0) OVER (ORDER BY record_date)  -- 0 instead of NULL
```

Useful when the LAG'd value is going into a calculation and
you don't want to deal with NULLs.

---

## LAG with PARTITION BY

```sql
SELECT
  user_id,
  order_date,
  total,
  LAG(order_date) OVER (PARTITION BY user_id
                        ORDER BY order_date) AS prev_order_date
FROM   Orders;
```

For each user, the date of their previous order. NULL for
their first order.

This is the "days since last order" pattern:

```sql
WITH orders_with_prev AS (
  SELECT
    user_id,
    order_date,
    LAG(order_date) OVER (PARTITION BY user_id
                          ORDER BY order_date) AS prev_order_date
  FROM   Orders
)
SELECT
  user_id,
  order_date,
  JULIANDAY(order_date) - JULIANDAY(prev_order_date) AS days_since_prev
FROM   orders_with_prev;
```

---

## FIRST_VALUE and LAST_VALUE

`FIRST_VALUE(x) OVER (...)` returns `x` from the first row
of the window. `LAST_VALUE(x) OVER (...)` returns `x` from
the last row.

```sql
SELECT
  name,
  department_id,
  salary,
  FIRST_VALUE(name) OVER (PARTITION BY department_id
                          ORDER BY salary DESC) AS top_earner,
  LAST_VALUE(name)  OVER (PARTITION BY department_id
                          ORDER BY salary DESC
                          ROWS BETWEEN UNBOUNDED PRECEDING
                                   AND UNBOUNDED FOLLOWING) AS lowest_earner
FROM   Employee;
```

The `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED
FOLLOWING` is required for `LAST_VALUE` to mean "the last
row of the window". Without it, the default frame is
"up to the current row", which means `LAST_VALUE` returns
the current row. Lesson 39 explains frames in detail.

`FIRST_VALUE` doesn't need the frame clause because the
default frame "from the start of the window to the current
row" includes the first row.

---

## When to use LAG vs a self-join

Both can express "compare to the previous row":

```sql
-- Window function form
SELECT
  w1.id,
  w1.temperature,
  w2.temperature AS prev_temp
FROM   Weather w1
LEFT JOIN Weather w2 ON w2.record_date = (
  SELECT MAX(record_date) FROM Weather
  WHERE  record_date < w1.record_date
);

-- LAG form (cleaner)
SELECT
  id,
  temperature,
  LAG(temperature) OVER (ORDER BY record_date) AS prev_temp
FROM   Weather;
```

The LAG form is one query, no correlated subquery, no self-
join. It's the canonical "compare rows in the same window"
pattern. Use it.

The self-join form is occasionally needed when the join
predicate isn't a simple offset (e.g. "the previous business
day", which depends on a calendar table).

---

## LAG and LEAD for sequential comparisons

The classic "consecutive numbers" question:

```sql
SELECT DISTINCT num AS ConsecutiveNums
FROM   (
  SELECT
    num,
    LAG(num, 1) OVER (ORDER BY id) AS prev1,
    LAG(num, 2) OVER (ORDER BY id) AS prev2
  FROM   Logs
)
WHERE  num = prev1 AND num = prev2;
```

Three consecutive rows with the same number. The pattern
extends: `LAG(num, k)` for k consecutive prior rows.

---

## A worked example: rising temperature

```sql
SELECT w1.id
FROM   Weather w1
WHERE  w1.temperature > (
  SELECT w2.temperature
  FROM   Weather w2
  WHERE  w2.record_date = DATE(w1.record_date, '-1 day')
);
```

Or with `LAG`:

```sql
SELECT id
FROM   (
  SELECT
    id, record_date, temperature,
    LAG(temperature) OVER (ORDER BY record_date) AS prev_temp,
    LAG(record_date) OVER (ORDER BY record_date) AS prev_date
  FROM   Weather
)
WHERE  temperature > prev_temp
  AND  record_date = DATE(prev_date, '+1 day');
```

The LAG form is more verbose here but reads more like the
"compare rows" intent. The self-join form is what most
candidates write first.

---

## Try it

Given `Orders(id, customer_id, order_date, total)`:

1. For each order, show the date of the customer's previous
   order. Use `LAG`.
2. For each customer, find the gap in days between
   consecutive orders.
3. Find every order whose total is greater than the
   customer's previous order's total.
