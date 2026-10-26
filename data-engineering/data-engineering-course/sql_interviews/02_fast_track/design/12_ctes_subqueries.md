# Lesson 12 — Common Table Expressions and Subqueries

> **Goal:** choose between a CTE and a subquery with
> confidence. The two are functionally equivalent in most
> cases, but stylistically different.

---

## Decision tree

```
Is the subquery recursive?
├── yes → CTE (no choice; recursive CTEs only)
└── no
    ├── Is the subquery referenced more than once?
    │   ├── yes → CTE
    │   └── no
    │       ├── Is the subquery short and obvious?
    │       │   ├── yes → subquery (inline)
    │       │   └── no  → CTE (named)
    │       └── Is the subquery correlated?
    │           ├── yes → leave as subquery in WHERE
    │           └── no  → CTE
    └── (none of the above)
```

That's the whole decision. In practice, the answer is "CTE
by default, subquery when it's small and obvious."

---

## When to use a CTE

**Recursive logic.** Recursive CTEs (the `WITH RECURSIVE`
form) walk trees, generate sequences, and explore
hierarchies. No subquery form.

```sql
WITH RECURSIVE org_chart AS (
  SELECT id, name, manager_id, 0 AS depth
  FROM   Employee
  WHERE  manager_id IS NULL
  UNION ALL
  SELECT e.id, e.name, e.manager_id, c.depth + 1
  FROM   Employee e
  JOIN   org_chart c ON e.manager_id = c.id
)
SELECT * FROM org_chart;
```

**Multi-step transformation.** A query that's actually three
or four logical steps. Each step is a CTE.

**Debuggability.** CTEs are easier to inspect. You can
`SELECT * FROM my_cte` and see the intermediate result.

---

## When to use a subquery

**Scalar subquery in the SELECT list.** A single value
pulled from another table.

```sql
SELECT e.name,
       (SELECT MAX(salary) FROM Employee
        WHERE department_id = e.department_id) AS dept_max
FROM   Employee e;
```

**EXISTS / NOT EXISTS.** Tests for the existence of a
related row. The subquery form is conventional and clear.

```sql
-- Customers who have never ordered
SELECT c.id, c.name
FROM   Customer c
WHERE  NOT EXISTS (
  SELECT 1 FROM Orders o WHERE o.customer_id = c.id
);
```

**IN / NOT IN with a small list.** Less common, but valid.

```sql
SELECT * FROM Employee
WHERE  department_id IN (1, 3, 7);
```

The list can also be a subquery:

```sql
SELECT * FROM Employee
WHERE  department_id IN (SELECT id FROM Department WHERE is_active);
```

This is sometimes clearer as a join; the choice is
stylistic.

---

## Correlated vs uncorrelated subqueries

A **correlated** subquery references a column from the outer
query. It runs once per outer row.

```sql
-- Correlated: subquery depends on e.department_id
SELECT e.name, e.salary
FROM   Employee e
WHERE  e.salary > (
  SELECT AVG(salary) FROM Employee
  WHERE  department_id = e.department_id
);
```

For each employee, the subquery computes the average salary
of their department. Then we keep the employee if their
salary is above the average. The subquery is correlated
because it references `e.department_id`.

An **uncorrelated** subquery does not reference the outer
query. It runs once.

```sql
-- Uncorrelated: subquery is the same for every row
SELECT name, salary
FROM   Employee
WHERE  salary > (SELECT AVG(salary) FROM Employee);
```

The subquery computes the company-wide average once. Then
every employee is compared against it.

In modern engines, correlated subqueries are often rewritten
as joins for performance. Don't worry about that for
interviews — focus on correctness and clarity.

---

## Inline views (subquery in FROM)

A subquery in the `FROM` clause is called an *inline view*
or *derived table*. It behaves like a table for the rest of
the query.

```sql
SELECT d.department_name, h.n
FROM   (
  SELECT department_id, COUNT(*) AS n
  FROM   Employee
  GROUP BY department_id
) h
JOIN   Department d ON d.id = h.department_id;
```

This is a CTE written inline. In most cases, prefer the CTE
form for readability.

---

## The two ways to write the same thing

The classic "second-highest salary" question has at least
six valid SQL answers. Three of them:

```sql
-- 1. Subquery in WHERE
SELECT MAX(salary) FROM Employee
WHERE  salary < (SELECT MAX(salary) FROM Employee);

-- 2. CTE + DENSE_RANK
WITH ranked AS (
  SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rk
  FROM Employee
)
SELECT salary FROM ranked WHERE rk = 2;

-- 3. LIMIT + OFFSET on distinct
SELECT DISTINCT salary FROM Employee
ORDER BY salary DESC LIMIT 1 OFFSET 1;
```

All three are correct. The differences are stylistic and
subtle (the third one returns the second distinct value;
the others return the second row, which differs if there are
ties). Interviewers may ask you to compare — practice the
"why this version over that one" explanation.

---

## Try it

Pick three of the M07 problems. Write each one twice: once
with a CTE, once with a subquery. Compare the two. Which is
clearer? Why?

If you find yourself reaching for a CTE, that's usually the
right answer.
