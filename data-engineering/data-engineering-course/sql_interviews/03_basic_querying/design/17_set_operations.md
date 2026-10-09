# Lesson 17 — UNION, INTERSECT, EXCEPT

> **Goal:** combine two queries that have the same shape
> into a single result.

---

## The three operators

| Operator | What it does |
|---|---|
| `UNION` | All rows from both queries, de-duplicated. |
| `UNION ALL` | All rows from both queries, with duplicates. |
| `INTERSECT` | Rows that appear in both queries. |
| `EXCEPT` | Rows from the first query that are not in the second. |

(MySQL does not support `INTERSECT` or `EXCEPT` as of
version 8. SQLite supports all four.)

The two queries must have the **same number of columns** and
**compatible types** in each position. The result column
names come from the first query.

---

## UNION ALL

The most useful of the set operations. Concatenates the
results of two queries.

```sql
SELECT id, name, 'employee' AS kind FROM Employee
UNION ALL
SELECT id, name, 'customer' AS kind FROM Customer;
```

Returns every employee and every customer, with a `kind`
column to distinguish them. `UNION ALL` is what you want
when you've partitioned data across tables or want to
combine two periods.

`UNION ALL` is fast (no dedup). `UNION` requires a sort or
hash to dedup, which can be expensive.

---

## UNION

Same as `UNION ALL` but removes duplicates. Use only when
you genuinely want distinct rows.

```sql
-- Customers who are also employees (by name)
SELECT name FROM Customer
UNION
SELECT name FROM Employee;
```

This deduplicates by all columns. Two employees with the
same name collapse to one row. (Usually you want a more
explicit join here.)

---

## INTERSECT

Rows that appear in *both* queries. Useful for "in both
tables" without an explicit join.

```sql
-- Customers who placed an order
SELECT id FROM Customer
INTERSECT
SELECT customer_id FROM Orders;
```

The same result can be had with `WHERE EXISTS` or with
`INNER JOIN DISTINCT`. `INTERSECT` is sometimes the
clearest.

---

## EXCEPT

Rows from the first query that are *not* in the second.
Useful for "in A but not in B" without an anti-join.

```sql
-- Customers who have not placed an order
SELECT id FROM Customer
EXCEPT
SELECT customer_id FROM Orders;
```

Same as `NOT IN` or `NOT EXISTS` or `LEFT JOIN ... IS NULL`.
M05 covers all three ways to write an anti-join.

---

## When to use set operations vs joins

Set operations treat the input as *sets of rows* and combine
them. Joins treat the input as *collections of rows with
relationships* and enrich each row with columns from the
other table.

Use set operations when:

- The two queries have the same shape (same columns, same
  types).
- You want to combine or filter the row sets without
  per-row matching.
- You're doing "append" logic (UNION ALL) or "diff" logic
  (EXCEPT).

Use joins when:

- You want to combine columns from two tables into one row.
- The relationship is N:1 (e.g. employee to department).
- You're doing anything more complex than append/diff.

---

## Performance

`UNION ALL` is essentially free — the engine just concatenates
the result sets. `UNION`, `INTERSECT`, and `EXCEPT` require
deduplication, which the engine does via sort or hash. For
millions of rows, prefer `UNION ALL` with a follow-up
`GROUP BY` or `DISTINCT` if you can isolate the dedup to a
single column.

---

## Try it

Given two tables `Employee_2023(id, name, dept)` and
`Employee_2024(id, name, dept)`:

1. List every employee who appears in both years.
2. List every employee who appears in 2023 but not 2024.
3. List every employee (across both years), with a `year`
   column showing which year(s) they appear in. Use UNION
   ALL.
