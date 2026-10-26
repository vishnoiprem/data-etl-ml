# Lesson 28 — INNER JOIN — Row-by-Row Match

> **Goal:** the default join, in depth.

---

## What INNER JOIN does

For every row in the left table, find every row in the
right table that satisfies the join predicate. If at least
one right row matches, the left row is paired with each
match. If no right row matches, the left row is dropped.

The result is a flat table where each row is a (left row,
right row) pair.

```sql
SELECT e.id, e.name, d.department_name
FROM   Employee   AS e
INNER JOIN Department AS d ON e.department_id = d.id;
```

The `INNER` keyword is optional. `JOIN` and `INNER JOIN`
are synonyms.

---

## The Venn diagram

```
   ┌─────────┐         ┌─────────┐
   │Employee │         │Department│
   │         │         │         │
   │   ┌─────┴─────┐   │         │
   │   │  match    │   │         │
   │   │  (INNER)  │   │         │
   │   └─────┬─────┘   │         │
   │         │         │         │
   └─────────┘         └─────────┘
```

The intersection is the INNER JOIN result. Rows in only one
table are excluded.

---

## The join predicate

The `ON` clause is a boolean expression. The most common
form is `left.col = right.col` (an *equi-join*), but any
predicate is allowed:

```sql
-- Equi-join (most common)
ON e.department_id = d.id

-- Range join (e.g. valid_from <= event_date < valid_to)
ON e.id = h.employee_id AND h.start_date <= e.event_date
                       AND e.event_date <  h.end_date

-- Non-equi-join (rare; e.g. between)
ON e.salary BETWEEN b.min_salary AND b.max_salary
```

Range joins are common in SCD Type 2 fact tables: a fact row
joins to the dimension row that was current at the time of
the event.

---

## Multiple rows on the right

If a left row matches multiple right rows, the left row is
*duplicated* in the output. One row becomes N rows.

```sql
-- One employee, two managers (data error) -> 2 result rows
SELECT e.id, m.name
FROM   Employee e
JOIN   Manager  m ON m.department_id = e.department_id;
```

This is a common source of "why is my COUNT(*) wrong?"
bugs. The right side had duplicates you didn't expect.

The fix is usually to add another condition to the ON
clause to make the match unique, or to use an aggregate
before joining.

---

## INNER JOIN with WHERE

```sql
SELECT e.id, e.name, d.department_name
FROM   Employee   e
JOIN   Department d ON e.department_id = d.id
WHERE  d.location = 'NY';
```

`WHERE` is applied after the join. Equivalent to writing
the location filter in the ON clause, but more readable.

With INNER JOIN, the ON predicate and the WHERE predicate
are logically interchangeable. With OUTER JOIN, they are
not. Lesson 29.

---

## Composite join keys

A join can use multiple columns. The predicate is just an
AND of comparisons.

```sql
SELECT *
FROM   OrderItem oi
JOIN   Inventory  i ON oi.product_id = i.product_id
                   AND oi.warehouse  = i.warehouse;
```

This is the "composite key" pattern. Common when the natural
key of a table is multiple columns.

---

## USING clause

When the join columns have the same name in both tables,
`USING (col)` is shorthand for `ON a.col = b.col`:

```sql
-- These are equivalent:
SELECT * FROM Employee e JOIN Department d ON e.dept_id = d.dept_id;
SELECT * FROM Employee e JOIN Department d USING (dept_id);
```

`USING` is supported by PostgreSQL, MySQL, SQLite, Oracle.
Not supported by SQL Server (use ON).

After `USING (dept_id)`, the result has a single `dept_id`
column instead of two. This is sometimes the desired
behavior, sometimes surprising.

---

## Try it

Given `Employee(id, name, department_id)` and
`Department(id, name, location)`:

1. INNER JOIN: list every employee with their department
   name. Sort by employee name.
2. Same as 1, but only employees in NY-located departments.
3. Same as 1, but also include the manager's name. Add a
   third table `Manager(id, department_id, name)` and join
   on `department_id`.
