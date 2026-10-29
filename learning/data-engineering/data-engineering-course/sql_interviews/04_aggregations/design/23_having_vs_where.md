# Lesson 23 — HAVING vs WHERE

> **Goal:** filters before vs after aggregation.

---

## The distinction

- `WHERE` filters **rows** before grouping.
- `HAVING` filters **groups** after aggregation.

This is the only difference. The syntax is otherwise similar.

```sql
-- WHERE: keep only high-salary employees before counting
SELECT department_id, COUNT(*) AS n
FROM   Employee
WHERE  salary > 80000
GROUP BY department_id;

-- HAVING: count everyone, then drop small departments
SELECT department_id, COUNT(*) AS n
FROM   Employee
GROUP BY department_id
HAVING COUNT(*) > 5;
```

Both return similar shapes; the row set being aggregated is
different.

---

## The compiler error

```sql
SELECT department_id, COUNT(*) AS n
FROM   Employee
WHERE  COUNT(*) > 5                -- SYNTAX ERROR
GROUP BY department_id;
```

`COUNT(*)` doesn't exist yet at the WHERE stage (the rows
haven't been grouped). The compiler rejects this. The fix is
`HAVING COUNT(*) > 5`.

---

## When to use each

| Predicate | Use |
|---|---|
| Per-row filter (e.g. `salary > X`) | `WHERE` |
| Filter on an aggregate (e.g. `COUNT(*) > 5`) | `HAVING` |
| Filter on a column not in SELECT | `WHERE` (the column is a row attribute) |
| Filter on a column alias from SELECT | `HAVING` (the alias is computed during SELECT) |

### Always prefer WHERE for row filters

If the filter can be expressed in WHERE, put it there. The
engine evaluates WHERE before grouping, so the GROUP BY has
fewer rows to process. This is faster.

```sql
-- Slower: filter in HAVING
SELECT department_id, AVG(salary) AS avg_sal
FROM   Employee
GROUP BY department_id
HAVING MAX(hire_date) >= '2023-01-01';

-- Faster: filter in WHERE
SELECT department_id, AVG(salary) AS avg_sal
FROM   Employee
WHERE  hire_date >= '2023-01-01'
GROUP BY department_id;
```

Both return the same shape; the second is faster because it
groups fewer rows. The first is correct only if the intent
is "departments where the latest hire is in 2023"; the
second is "departments where the average salary (of recent
hires) is ...". The semantic difference is real.

---

## Combining WHERE and HAVING

```sql
SELECT department_id, COUNT(*) AS n
FROM   Employee
WHERE  hire_date >= '2023-01-01'        -- row filter
GROUP BY department_id
HAVING COUNT(*) > 3;                    -- group filter
```

The order in the SQL doesn't matter for correctness; the
engine always evaluates WHERE → GROUP BY → HAVING. But the
order in the source code matters for readability. Put WHERE
first, then GROUP BY, then HAVING.

---

## HAVING without GROUP BY

If you write `HAVING` without `GROUP BY`, the entire input
is one group. This is occasionally useful:

```sql
SELECT COUNT(*) AS n
FROM   Orders
HAVING COUNT(*) > 1000;
```

Returns either one row (if there are > 1000 orders) or zero
rows (if there are ≤ 1000). It's a "do we have enough data"
check.

---

## A common pattern: the count-and-filter

```sql
SELECT department_id, COUNT(*) AS n
FROM   Employee
GROUP BY department_id
HAVING COUNT(*) BETWEEN 5 AND 20;
```

Find departments of moderate size. Note that `BETWEEN` works
in HAVING just like in WHERE.

---

## Try it

Given `Orders(id, customer_id, total, status, order_date)`:

1. Find customers whose lifetime spend is over $1,000, using
   `SUM` in HAVING.
2. Find months where the total revenue was over $10,000,
   but only counting `delivered` orders. Put the status
   filter in WHERE.
3. Find the top 3 customers by total spend. Use `ORDER BY`
   + `LIMIT` (not HAVING).
