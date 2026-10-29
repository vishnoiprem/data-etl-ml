# Lesson 31 — Anti-Joins: NOT IN, NOT EXISTS, LEFT JOIN ... IS NULL

> **Goal:** the three ways to write "in A but not in B" —
> and why they're not equivalent when NULLs are involved.

---

## The three syntactic forms

```sql
-- Form 1: NOT IN
SELECT id, name FROM Customer
WHERE  id NOT IN (SELECT customer_id FROM Orders);

-- Form 2: NOT EXISTS
SELECT id, name FROM Customer c
WHERE  NOT EXISTS (
  SELECT 1 FROM Orders o WHERE o.customer_id = c.id
);

-- Form 3: LEFT JOIN ... IS NULL
SELECT c.id, c.name
FROM   Customer c
LEFT JOIN Orders o ON o.customer_id = c.id
WHERE  o.id IS NULL;
```

All three return "customers who have no orders". When the
subquery has no NULLs, all three return the same result. When
the subquery has NULLs, they differ.

---

## The NULL trap

`NOT IN` with a NULL in the list returns **no rows**.

```sql
-- Orders table has a row with customer_id = NULL
SELECT id, name FROM Customer
WHERE  id NOT IN (SELECT customer_id FROM Orders);
-- Returns 0 rows, even if there are customers with no orders.
```

Why? `id NOT IN (1, 2, NULL)` is `id <> 1 AND id <> 2 AND
id <> NULL`. The last comparison is UNKNOWN. `AND UNKNOWN`
is UNKNOWN, so the WHERE drops every row.

`NOT EXISTS` and `LEFT JOIN ... IS NULL` are not affected.
They handle NULLs correctly:

```sql
-- Both return the right answer even with NULL customer_id
SELECT id, name FROM Customer c
WHERE  NOT EXISTS (
  SELECT 1 FROM Orders o WHERE o.customer_id = c.id
);

SELECT c.id, c.name
FROM   Customer c
LEFT JOIN Orders o ON o.customer_id = c.id
WHERE  o.id IS NULL;
```

**The interview lesson:** when the subquery could return
NULLs, prefer `NOT EXISTS` or `LEFT JOIN ... IS NULL` over
`NOT IN`.

---

## Performance

All three forms can be optimized to the same execution plan
by a smart query optimizer. In practice, `NOT EXISTS` is
the most reliably optimized form, especially in PostgreSQL
and MySQL. `LEFT JOIN ... IS NULL` is sometimes slower
because the optimizer may not recognize the anti-join
pattern.

For correctness and clarity, prefer `NOT EXISTS`. For
performance, write all three and let `EXPLAIN` decide.

---

## When NULLs are guaranteed absent

If the column in the subquery is `NOT NULL`, all three
forms are equivalent. Use whichever reads best:

```sql
-- customer_id is NOT NULL in Orders
SELECT id, name FROM Customer
WHERE  id NOT IN (SELECT customer_id FROM Orders);
```

The `NOT IN` form is the most readable when the column is
definitively non-nullable. In an interview, ask about
nullability or assume NOT NULL based on the schema.

---

## When to use each

| Form | When |
|---|---|
| `NOT IN` | Subquery column is definitely NOT NULL. Compact and readable. |
| `NOT EXISTS` | Default choice. Handles NULLs correctly, well-optimized. |
| `LEFT JOIN ... IS NULL` | When you need to inspect the joined columns anyway (e.g. for debugging). |

In production code, `NOT EXISTS` is the safest default.

---

## NOT EXISTS and correlation

`NOT EXISTS` is a *correlated* subquery: it references a
column from the outer query (`c.id`). The database engine
evaluates it for each row of the outer query.

```sql
SELECT c.id, c.name
FROM   Customer c
WHERE  NOT EXISTS (
  SELECT 1 FROM Orders o
  WHERE  o.customer_id = c.id
);
```

For each customer, the engine asks "does any order exist
with this customer_id?". If no, the customer is in the
result.

Some databases (PostgreSQL 14+, modern MySQL) optimize
`NOT EXISTS` to a hash-based anti-join, which is O(n + m)
instead of O(n × m). Older engines did a nested-loop
anti-join, which is O(n × m) in the worst case. For
interviews, don't worry about this — just write the
correlated form.

---

## A worked example

Given `Customer(id, name)` and `Orders(id, customer_id,
status)`:

> "Find customers who have no *delivered* orders."

```sql
-- NOT IN (assumes customer_id NOT NULL)
SELECT id, name FROM Customer
WHERE  id NOT IN (
  SELECT customer_id FROM Orders WHERE status = 'delivered'
);

-- NOT EXISTS (NULL-safe)
SELECT id, name FROM Customer c
WHERE  NOT EXISTS (
  SELECT 1 FROM Orders o
  WHERE  o.customer_id = c.id
    AND  o.status = 'delivered'
);

-- LEFT JOIN ... IS NULL
SELECT c.id, c.name
FROM   Customer c
LEFT JOIN Orders o ON o.customer_id = c.id
                  AND o.status = 'delivered'
WHERE  o.id IS NULL;
```

All three return the same result (assuming `customer_id` is
NOT NULL). Pick the form you can explain.

---

## Try it

Given `Employee(id, name, department_id)` and
`Project(id, name, lead_employee_id)`:

1. Find employees who are not leading any project. Use
   `NOT IN`.
2. Same, but use `NOT EXISTS`.
3. Same, but use `LEFT JOIN ... IS NULL`.

Then add a row to `Project` with `lead_employee_id = NULL`
and re-run each query. The `NOT IN` form will return no
rows; the others will still work.
