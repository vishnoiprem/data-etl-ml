# Lesson 21 — COUNT vs COUNT(DISTINCT)

> **Goal:** understand the three flavors of COUNT and when
> each is the right answer.

---

## The three

```sql
SELECT
  COUNT(*)                       AS row_count,    -- every row
  COUNT(column)                  AS non_null_count, -- non-NULL values
  COUNT(DISTINCT column)         AS distinct_count -- distinct non-NULL
FROM   Employee;
```

| Function | Counts |
|---|---|
| `COUNT(*)` | Every row in the input, including rows where every column is NULL. |
| `COUNT(x)` | Rows where `x` is not NULL. |
| `COUNT(DISTINCT x)` | Distinct non-NULL values of `x`. |

The result of `COUNT(*)` is always the row count. The other
two depend on the column.

---

## When each is right

**`COUNT(*)`** — when you want the number of rows. "How many
orders did we get in 2024?" `SELECT COUNT(*) FROM Orders
WHERE order_date BETWEEN ...`.

**`COUNT(column)`** — when you want the number of rows where
that column is populated. "How many employees have a known
salary?" `SELECT COUNT(salary) FROM Employee`. (Yes, you
could write `WHERE salary IS NOT NULL` and `COUNT(*)`, but
`COUNT(salary)` is one line.)

**`COUNT(DISTINCT column)`** — when you want the number of
unique non-NULL values. "How many unique customers placed an
order last month?" `SELECT COUNT(DISTINCT customer_id) FROM
Orders WHERE ...`.

---

## COUNT(DISTINCT) across multiple columns

PostgreSQL, MySQL 8+, Snowflake, BigQuery, and SQLite
support `COUNT(DISTINCT col1, col2, ...)` — distinct
*combinations* of the listed columns.

```sql
SELECT COUNT(DISTINCT customer_id, order_date) AS customer_dates
FROM   Orders;
```

This counts unique (customer, date) pairs. Two orders by the
same customer on the same day count as one.

In some databases (notably older MySQL) you have to use a
subquery:

```sql
SELECT COUNT(*) FROM (
  SELECT DISTINCT customer_id, order_date FROM Orders
) sub;
```

---

## Performance

`COUNT(*)` is the fastest — the engine knows the row count
from the table metadata (or close to it).

`COUNT(column)` requires checking each row for non-NULL.
Index-only scans can speed this up if the column is indexed.

`COUNT(DISTINCT column)` is the most expensive — the engine
has to dedup. For very large tables, an approximate
`COUNT(DISTINCT ...)` (HyperLogLog) is sometimes acceptable
and orders of magnitude faster. PostgreSQL doesn't have
this; BigQuery does (`APPROX_COUNT_DISTINCT`); Elasticsearch
has `cardinality` aggregation.

---

## The interview trap

A common interview question:

> "How many customers have placed an order?"

The wrong answer is `COUNT(*) FROM Orders` — that counts
orders, not customers. The right answer is
`COUNT(DISTINCT customer_id) FROM Orders`.

---

## A second trap

> "How many customers have placed an order, and what is the
> total number of orders?"

```sql
SELECT
  COUNT(DISTINCT customer_id) AS n_customers,
  COUNT(*)                    AS n_orders
FROM   Orders;
```

Both numbers from the same query. Don't write two.

---

## A third trap

> "How many distinct customers have placed an order in each
> of the last 3 months?"

```sql
SELECT
  DATE_TRUNC('month', order_date) AS month,
  COUNT(DISTINCT customer_id)     AS n_customers
FROM   Orders
WHERE  order_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '3 months')
GROUP BY DATE_TRUNC('month', order_date);
```

This is a real production query. Note that `COUNT(DISTINCT
customer_id)` here counts distinct customers *within each
month*, not across the whole period. The `GROUP BY` makes
the difference.

---

## Try it

Given `Orders(id, customer_id, total, status, order_date)`:

1. How many distinct customers have ever placed an order?
2. How many distinct (customer, day) pairs are in the
   table?
3. For each month in 2024, how many distinct customers
   placed an order?
