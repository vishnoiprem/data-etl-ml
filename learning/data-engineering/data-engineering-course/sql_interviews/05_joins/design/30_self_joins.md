# Lesson 30 — Self-Joins

> **Goal:** join a table to itself.

---

## When to self-join

A self-join is when both sides of the join are the same
table. It expresses a relationship *between rows of the
same table*.

Common cases:

- **Hierarchies.** An employee has a manager (also an
  employee). Find manager names.
- **Sequences.** A row references the previous row
  (`prev_id`, `next_id`). Walk the chain.
- **Pairs.** Find all pairs of rows that share a property
  (same department, same day, same price).
- **Consecutive.** Find rows that follow each other in time
  (e.g. "rising temperature" — Lesson 51).

---

## The syntax

You must use two different aliases for the same table:

```sql
SELECT e.id, e.name, m.name AS manager_name
FROM   Employee e
LEFT JOIN Employee m ON e.manager_id = m.id;
```

`e` is "the employee", `m` is "the manager of the employee".
The join condition `e.manager_id = m.id` says: find the
manager row whose `id` matches the employee's `manager_id`.

The same table appears twice in the FROM clause, with two
different aliases. The engine doesn't care; it sees two
inputs.

---

## The classic: the org chart

```sql
WITH RECURSIVE org AS (
  -- Anchor: the CEO (no manager)
  SELECT id, name, manager_id, 0 AS depth, name AS path
  FROM   Employee
  WHERE  manager_id IS NULL

  UNION ALL

  -- Recursive: an employee whose manager is already in the org
  SELECT e.id, e.name, e.manager_id, o.depth + 1,
         o.path || ' > ' || e.name
  FROM   Employee e
  JOIN   org o ON e.manager_id = o.id
)
SELECT * FROM org;
```

This is a *recursive* self-join, walking the manager
hierarchy from the CEO down. M08 has a worked example
("Tree Node" — Lesson 75).

---

## Pairs

```sql
-- Pairs of employees in the same department
SELECT a.name AS emp1, b.name AS emp2
FROM   Employee a
JOIN   Employee b ON a.department_id = b.department_id
                 AND a.id < b.id;
```

`a.id < b.id` is the trick: it ensures each pair appears
once (not twice — `a, b` and `b, a` are the same pair) and
excludes self-pairs (`a.id = b.id`).

This is the "find all pairs" pattern. M08 has multiple
exercises on it.

---

## Consecutive rows

```sql
-- Consecutive days with rising temperature
SELECT w1.id
FROM   Weather w1
JOIN   Weather w2 ON w2.record_date = DATE(w1.record_date, '+1 day')
WHERE  w2.temperature > w1.temperature;
```

The self-join matches a row with the row from "tomorrow"
(or any other "next" relation). The WHERE filters to the
ones where the comparison holds.

The pattern can also be written with `LAG`:

```sql
SELECT id
FROM   (
  SELECT id, record_date, temperature,
         LAG(temperature) OVER (ORDER BY record_date) AS prev_temp,
         LAG(record_date) OVER (ORDER BY record_date) AS prev_date
  FROM   Weather
)
WHERE  temperature > prev_temp
  AND  record_date = DATE(prev_date, '+1 day');
```

The window-function form is usually clearer. The
self-join form is the one most candidates reach for first.

---

## Why self-joins are tricky

The biggest mistake: forgetting the alias. `SELECT * FROM
Employee JOIN Employee ON ...` is a syntax error (ambiguous
column references).

The second-biggest mistake: producing duplicate pairs. If
your predicate is `a.department_id = b.department_id` and
nothing else, you get `(a, b)` and `(b, a)` for every pair,
plus `(a, a)` for every row. Add `a.id < b.id` (or
`a.id <> b.id` if you want both orderings).

The third-biggest mistake: cross-product explosion. If the
table has 1,000 rows and you self-join with no WHERE, you
get 1,000,000 rows. The fix is the same: a strong join
predicate.

---

## Try it

Given `Employee(id, name, manager_id, department_id)`:

1. List every employee and their manager's name. (Use LEFT
   JOIN to include employees without managers.)
2. Find every pair of employees who share a manager.
3. Find the employees who are exactly two levels below the
   CEO. (Hint: a CTE with two joins.)
