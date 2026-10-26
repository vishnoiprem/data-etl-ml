# Lesson 29 — LEFT JOIN — Keep All Left Rows

> **Goal:** the "include everything from the left" join.

---

## What LEFT JOIN does

For every row in the left table, find every row in the
right table that satisfies the join predicate. If at least
one right row matches, the left row is paired with each
match. If no right row matches, the left row is paired with
a single row of NULLs.

The result has at least one row per left row. Right rows
that don't match any left row are dropped.

```sql
SELECT e.id, e.name, d.department_name
FROM   Employee e
LEFT JOIN Department d ON e.department_id = d.id;
```

An employee without a department still appears, with
`department_name = NULL`.

---

## The Venn diagram

```
   ┌─────────┐         ┌─────────┐
   │Employee │─────────│Department│
   │         │   LEFT  │         │
   │   ┌─────┴─────┐   │         │
   │   │  match    │   │         │
   │   │  (INNER)  │   │         │
   │   └─────┬─────┘   │         │
   │         │         │         │
   └─────────┘         └─────────┘
```

Everything in `Employee` is kept. Only the part of
`Department` that intersects with `Employee` appears.

---

## When to use LEFT JOIN

Use LEFT JOIN when the question is "include everything on
the left, even if there's no match on the right":

- Employees and their departments (include employees with
  no department).
- Customers and their orders (include customers who haven't
  ordered).
- Products and their reviews (include products with no
  reviews).
- Sales reps and their quotas (include reps without quotas).

If the question is "only those with a match", use INNER JOIN.

---

## ON vs WHERE — the difference

This is the most important lesson in M05. With OUTER JOIN,
the ON predicate and the WHERE predicate are **not
interchangeable**.

```sql
-- Query A: filter in ON
SELECT e.id, d.department_name
FROM   Employee e
LEFT JOIN Department d ON e.department_id = d.id
                       AND d.location = 'NY';

-- Query B: filter in WHERE
SELECT e.id, d.department_name
FROM   Employee e
LEFT JOIN Department d ON e.department_id = d.id
WHERE  d.location = 'NY';
```

**Query A:** Every employee is kept. For employees in an
NY-located department, `department_name` is the name. For
everyone else, `department_name` is NULL.

**Query B:** First we LEFT JOIN, then we drop any row where
`d.location` is not 'NY' (which includes the rows where
the join didn't match, since `d.location` is NULL for them).
So Query B returns only employees in NY-located departments.
**Same as INNER JOIN.**

The semantic difference: the WHERE filter is applied to the
*output* of the join, while the ON filter is applied
*during* the join. With an outer join, this matters.

**Rule of thumb:** if you're using LEFT JOIN and want to
keep the "no match" rows, put the filter in ON. If you want
to drop them after the join, put the filter in WHERE.

---

## Common LEFT JOIN patterns

### 1. The "include orphans"

```sql
SELECT c.id, c.name, COUNT(o.id) AS n_orders
FROM   Customer c
LEFT JOIN Orders o ON o.customer_id = c.id
GROUP BY c.id, c.name;
```

Customers with no orders get `n_orders = 0`. The LEFT JOIN
preserves them; `COUNT(o.id)` (not `COUNT(*)`) excludes the
NULL-padded rows.

### 2. The "default value" pattern

```sql
SELECT e.id, e.name,
       COALESCE(d.department_name, 'Unassigned') AS department_name
FROM   Employee e
LEFT JOIN Department d ON e.department_id = d.id;
```

`COALESCE` swaps the NULL for a human-readable string. Common
in reports where "Unassigned" is more useful than blank.

### 3. The anti-join (preview)

```sql
SELECT c.id, c.name
FROM   Customer c
LEFT JOIN Orders o ON o.customer_id = c.id
WHERE  o.id IS NULL;
```

This is the LEFT JOIN anti-join. Lesson 31 covers all three
forms.

---

## Multiple LEFT JOINs

```sql
SELECT
  e.id, e.name,
  d.department_name,
  m.name AS manager_name
FROM   Employee e
LEFT JOIN Department d ON e.department_id = d.id
LEFT JOIN Employee    m ON e.manager_id    = m.id;
```

This is "give me the employee, their department, and their
manager — if any of these are missing, NULL them out". A
common pattern in HR / org-chart queries.

Each LEFT JOIN is independent. An employee with no manager
and no department gets one row with both `department_name`
and `manager_name` as NULL.

---

## Try it

Given `Customer(id, name)` and `Orders(id, customer_id,
total, status)`:

1. List every customer with the count of their orders,
   including customers with zero orders.
2. List every customer with their total spend, or 0 if they
   haven't ordered. Use `COALESCE`.
3. List every customer with the count of their *delivered*
   orders. Use `LEFT JOIN ... ON ... AND status = 'delivered'`
   in the ON clause (so customers with no delivered orders
   still appear).
