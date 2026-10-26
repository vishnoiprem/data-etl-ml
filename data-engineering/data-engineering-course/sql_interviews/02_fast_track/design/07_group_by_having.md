# Lesson 07 — GROUP BY and HAVING

> **Goal:** aggregate *per group*, then filter the groups.

---

## GROUP BY

`GROUP BY` partitions the input into buckets, one per
distinct value of the grouping expression. Each aggregate then
runs *per bucket*. The result has one row per bucket.

```sql
SELECT department_id, COUNT(*) AS n
FROM   Employee
GROUP BY department_id;
```

One row per department. `COUNT(*)` is the row count of that
department's bucket.

### The SELECT/GROUP BY rule

Every column in the SELECT list that is *not* an aggregate
must appear in the GROUP BY clause. That's the rule. The
database engine will reject any query that breaks it.

```sql
-- WRONG: name is not aggregated and not in GROUP BY
SELECT department_id, name, COUNT(*)
FROM   Employee
GROUP BY department_id;
```

This raises an error in strict mode (PostgreSQL, SQL Server).
MySQL historically allowed it with a non-deterministic choice
of `name`. Don't rely on that — write the GROUP BY correctly.

### Multiple grouping columns

```sql
SELECT department_id, job_title, AVG(salary) AS avg_sal
FROM   Employee
GROUP BY department_id, job_title;
```

One row per (department, job_title) combination. Useful for
"pivot-style" summaries.

### Grouping by an expression

You can group by an expression, not just a column:

```sql
SELECT EXTRACT(YEAR FROM order_date) AS yr, COUNT(*) AS n
FROM   Orders
GROUP BY EXTRACT(YEAR FROM order_date);
```

Some databases (PostgreSQL, Snowflake, BigQuery) let you
reference the SELECT alias instead: `GROUP BY yr`. SQLite
does not — you have to repeat the expression.

---

## HAVING

`WHERE` filters rows *before* aggregation. `HAVING` filters
groups *after* aggregation. That's the only difference.

```sql
SELECT department_id, COUNT(*) AS n
FROM   Employee
GROUP BY department_id
HAVING COUNT(*) > 5;
```

This returns only departments with more than 5 employees.

### Common mistake: putting aggregates in WHERE

```sql
-- WRONG: aggregates are not allowed in WHERE
SELECT department_id, COUNT(*)
FROM   Employee
WHERE  COUNT(*) > 5
GROUP BY department_id;
```

This is a syntax error. The fix is `HAVING COUNT(*) > 5`.

### When to use WHERE vs HAVING

If the predicate references an aggregate, it must go in
HAVING. If it doesn't, it can go in either — but **put it in
WHERE if you can**, because WHERE is evaluated before grouping
and so has less work to do.

```sql
-- Faster: filter in WHERE before grouping
SELECT department_id, AVG(salary) AS avg_sal
FROM   Employee
WHERE  hire_date >= '2023-01-01'
GROUP BY department_id
HAVING AVG(salary) > 80000;
```

The `hire_date >= ...` filter would also work in HAVING
(referencing `MAX(hire_date)`), but it's clearer and faster
in WHERE.

---

## The order of clauses

The clauses are evaluated in this order, conceptually:

1. `FROM` — choose the source rows.
2. `WHERE` — drop rows.
3. `GROUP BY` — partition into groups.
4. `HAVING` — drop groups.
5. `SELECT` — compute expressions.
6. `ORDER BY` — sort.
7. `LIMIT` / `OFFSET` — truncate.

`SELECT` is the fifth step, not the first. This is why you
can't reference a SELECT alias in the same query's WHERE or
GROUP BY (in most databases). Use a CTE if you need a
named expression visible to WHERE.

---

## Try it

Given `Orders(id, customer_id, total, status, order_date)`:

1. Find the number of orders per `customer_id`, only for
   customers with at least 3 orders, ordered by count desc.
2. Find the total revenue per month in 2024, only for months
   with revenue over $10,000.
3. Find the average order total per `status`, only including
   statuses with at least 10 orders.
