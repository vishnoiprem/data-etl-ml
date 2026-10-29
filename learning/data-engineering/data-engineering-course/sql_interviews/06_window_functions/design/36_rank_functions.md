# Lesson 36 — ROW_NUMBER, RANK, DENSE_RANK

> **Goal:** the three ranking functions, in depth.

---

## The shape

```sql
SELECT
  <column>,
  ROW_NUMBER() OVER (ORDER BY <col>) AS rn,
  RANK()       OVER (ORDER BY <col>) AS rk,
  DENSE_RANK() OVER (ORDER BY <col>) AS drk
FROM   <table>;
```

Three functions, same syntax, different behaviors on ties.

---

## A concrete example

Input:

| id | name | salary |
|---|---|---|
| 1 | Alice | 100 |
| 2 | Bob | 200 |
| 3 | Carol | 200 |
| 4 | Dan | 300 |
| 5 | Eve | 300 |

Output of:

```sql
SELECT id, name, salary,
       ROW_NUMBER() OVER (ORDER BY salary DESC) AS rn,
       RANK()       OVER (ORDER BY salary DESC) AS rk,
       DENSE_RANK() OVER (ORDER BY salary DESC) AS drk
FROM   Employee;
```

| id | name | salary | rn | rk | drk |
|---|---|---|---|---|---|
| 4 | Dan | 300 | 1 | 1 | 1 |
| 5 | Eve | 300 | 2 | 1 | 1 |
| 2 | Bob | 200 | 3 | 3 | 2 |
| 3 | Carol | 200 | 4 | 3 | 2 |
| 1 | Alice | 100 | 5 | 5 | 3 |

- `ROW_NUMBER` is 1, 2, 3, 4, 5. No ties; arbitrary order
  for tied rows.
- `RANK` is 1, 1, 3, 3, 5. Ties get the same rank, with a
  gap.
- `DENSE_RANK` is 1, 1, 2, 2, 3. Ties get the same rank,
  no gap.

---

## The choice

| Question | Use |
|---|---|
| "Exactly N rows" | `ROW_NUMBER` |
| "All rows tied for rank N" | `RANK` |
| "All rows whose value is in the top N distinct values" | `DENSE_RANK` |

For "top 3 employees by salary per department":

```sql
-- "exactly 3 employees per department" → ROW_NUMBER
ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC) <= 3

-- "all employees whose salary is in the top 3 distinct
--  salaries per department" → DENSE_RANK
DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) <= 3
```

If there are ties at rank 3, `ROW_NUMBER` picks 3, `DENSE_RANK`
keeps everyone tied at rank 3 (and possibly 4, 5, ...). The
right choice depends on what the question means.

---

## PARTITION BY

`PARTITION BY` splits the rows into independent windows. The
ranking restarts at 1 for each partition.

```sql
SELECT
  name,
  department_id,
  salary,
  DENSE_RANK() OVER (PARTITION BY department_id
                     ORDER BY salary DESC) AS dept_rank
FROM   Employee;
```

Within each department, the salaries are ranked 1, 2, 3
starting from the highest. Different departments can have
the same `dept_rank` because the windows are independent.

This is the "top N per group" pattern. It is the single
most common window-function use in interviews.

---

## Top N per group

The classic:

```sql
WITH ranked AS (
  SELECT
    name, department_id, salary,
    DENSE_RANK() OVER (PARTITION BY department_id
                       ORDER BY salary DESC) AS rk
  FROM   Employee
)
SELECT name, department_id, salary
FROM   ranked
WHERE  rk <= 3
ORDER BY department_id, rk;
```

Returns the top 3 salaries (with ties) per department.

A common variation: "top 3 employees per department, with
no ties, one row per employee":

```sql
WITH ranked AS (
  SELECT
    name, department_id, salary, id,
    ROW_NUMBER() OVER (PARTITION BY department_id
                       ORDER BY salary DESC, id) AS rn
  FROM   Employee
)
SELECT name, department_id, salary
FROM   ranked
WHERE  rn <= 3
ORDER BY department_id, rn;
```

The `, id` in the ORDER BY is the tie-breaker that makes
the result deterministic. Without it, two interviews with
the same data could return different rows.

---

## The "second highest" pattern

```sql
SELECT MAX(salary) AS second_highest
FROM   (
  SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rk
  FROM   Employee
) sub
WHERE  rk = 2;
```

This returns the second distinct salary value. To get all
rows tied at the second-highest value:

```sql
SELECT name, salary
FROM   (
  SELECT name, salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rk
  FROM   Employee
) sub
WHERE  rk = 2;
```

---

## Nth highest in each group

```sql
-- Nth highest salary per department
WITH ranked AS (
  SELECT
    name, department_id, salary,
    DENSE_RANK() OVER (PARTITION BY department_id
                       ORDER BY salary DESC) AS rk
  FROM   Employee
)
SELECT name, department_id, salary
FROM   ranked
WHERE  rk = :N;
```

Replace `:N` with a parameter. If no employee has rank N in
a department, that department has no row in the result. This
is the "nth highest per group" pattern.

---

## Try it

Given `Employee(id, name, salary, department_id, hire_date)`:

1. Rank every employee by salary descending, company-wide.
   Use all three functions and see the difference.
2. For each department, find the top 2 employees by salary
   (with ties).
3. Find the employee with the second-highest salary in
   each department.
