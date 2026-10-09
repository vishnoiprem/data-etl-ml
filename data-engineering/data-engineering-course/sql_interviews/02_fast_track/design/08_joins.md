# Lesson 08 — INNER JOIN, LEFT JOIN, RIGHT JOIN, FULL JOIN

> **Goal:** the four cardinal joins, in one lesson.

---

## The mental model

A `JOIN` combines rows from two tables based on a predicate.
For every row in the left table, the database engine looks
for matching rows in the right table, and combines them.

The four cardinal joins differ in *what they do when no match
is found*.

| Join | Left row has no match in right | Right row has no match in left |
|---|---|---|
| `INNER JOIN` | Drop the left row. | Drop the right row. |
| `LEFT JOIN` | Keep the left row, NULL-fill the right. | Drop the right row. |
| `RIGHT JOIN` | Drop the left row. | Keep the right row, NULL-fill the left. |
| `FULL JOIN` | Keep the left row, NULL-fill the right. | Keep the right row, NULL-fill the left. |

SQLite does not support `RIGHT JOIN` or `FULL JOIN` natively
(as of version 3.45). You can emulate them by swapping the
left and right tables. Lesson 35 covers `NATURAL JOIN` and
other join styles.

---

## INNER JOIN

The default join. Returns only rows where the join predicate
matches on both sides.

```sql
SELECT e.id, e.name, d.department_name
FROM   Employee   e
JOIN   Department d ON e.department_id = d.id;
```

Every employee gets matched to their department. Employees
without a department (NULL or non-existent ID) are dropped.
Departments without employees are dropped.

The word `INNER` is optional. `JOIN` and `INNER JOIN` are
synonyms.

### Cross join

A `JOIN` with no `ON` clause is a *cross join* — every row in
A is paired with every row in B. The result has `|A| × |B|`
rows. Rarely what you want; occasionally exactly what you
want (e.g. building a date × product grid).

---

## LEFT JOIN

Keeps every row from the left table, even if there's no
match. Unmatched right columns are NULL.

```sql
SELECT e.id, e.name, d.department_name
FROM   Employee   e
LEFT JOIN Department d ON e.department_id = d.id;
```

Now employees without a department still appear, with
`department_name = NULL`. This is the join you reach for when
the question is "include everyone, even if they don't have a
...".

The classic anti-join pattern is a `LEFT JOIN ... WHERE
right.key IS NULL`:

```sql
-- Customers who never placed an order
SELECT c.id, c.name
FROM   Customer c
LEFT JOIN Orders o ON o.customer_id = c.id
WHERE  o.id IS NULL;
```

This is one of three ways to write an anti-join; Lesson 31
covers all three.

---

## RIGHT JOIN

The mirror image of LEFT JOIN. It keeps every row from the
right table, NULL-filling the left.

```sql
SELECT e.id, e.name, d.department_name
FROM   Employee   e
RIGHT JOIN Department d ON e.department_id = d.id;
```

Same result as `LEFT JOIN` with the tables swapped. Most
people prefer `LEFT JOIN` for readability — the "big" table
goes on the left and the "lookup" goes on the right. Stylistic
preference, not a rule.

---

## FULL JOIN

Keeps every row from both sides. Unmatched columns are NULL.

```sql
SELECT e.id, e.name, d.department_name
FROM   Employee   e
FULL JOIN Department d ON e.department_id = d.id;
```

This is the union of LEFT JOIN and RIGHT JOIN, de-duplicated.
Useful for "show me everything, even orphaned rows on either
side" — e.g. an audit of referential integrity.

SQLite doesn't support it. To emulate in SQLite:

```sql
SELECT * FROM Employee e LEFT JOIN Department d ON ...
UNION
SELECT * FROM Employee e RIGHT JOIN Department d ON ...;  -- swapped
```

The `UNION` de-duplicates. (Lesson 17 covers set operations.)

---

## ON vs WHERE

With INNER JOIN, the `ON` clause and the `WHERE` clause are
often interchangeable. With LEFT JOIN they are not.

```sql
-- A: filters in ON
SELECT e.id, d.department_name
FROM   Employee e
LEFT JOIN Department d ON e.department_id = d.id
                       AND d.is_active = 1;

-- B: filters in WHERE
SELECT e.id, d.department_name
FROM   Employee e
LEFT JOIN Department d ON e.department_id = d.id
WHERE  d.is_active = 1;
```

Query A keeps every employee. For employees whose department
is inactive, `department_name` is NULL. For employees whose
department is active, it's the name.

Query B first does the LEFT JOIN, then *drops* employees whose
department is inactive (because `d.is_active` is NULL, not 1,
so the WHERE fails). So query B returns only employees with
an active department — the same as an INNER JOIN.

This is the most common join bug in real SQL code. Remember:
`ON` is a *join predicate*; `WHERE` is a *row filter*. They
behave differently when NULLs are involved.

---

## Try it

Given `Employee(id, name, department_id)` and
`Department(id, name, location)`:

1. List every employee's name and their department name. Use
   INNER JOIN.
2. List every employee's name and their department name. If
   the employee has no department, show "Unassigned" in the
   department column. Use LEFT JOIN and COALESCE.
3. Find every department, including departments with no
   employees. Show the department name and (if present) the
   employee name. Use RIGHT JOIN — or LEFT JOIN with the
   tables swapped.
