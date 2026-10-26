# Lesson 09 — Window Functions: ROW_NUMBER, RANK, DENSE_RANK

> **Goal:** the single most important SQL feature for
> interviews. After this lesson you can solve "top N per
> group" in one pass.

---

## The idea

An aggregate function (`SUM`, `COUNT`, `AVG`) collapses many
rows into one. A **window function** computes a value *for
each row* based on a set of related rows (the *window*), but
keeps every row in the output.

```sql
SELECT name, department_id, salary,
       RANK() OVER (PARTITION BY department_id
                    ORDER BY salary DESC) AS rk
FROM   Employee;
```

The output has one row per employee (the original row is
kept). The `rk` column is the rank of the employee within
their department, by salary descending.

---

## ROW_NUMBER, RANK, DENSE_RANK

The three ranking functions differ in how they handle ties.

| Function | Ties | Gaps? |
|---|---|---|
| `ROW_NUMBER()` | Arbitrary unique value. | No — 1,2,3,4,5 always. |
| `RANK()` | Same rank for tied rows. | Yes — 1,2,2,4,5. |
| `DENSE_RANK()` | Same rank for tied rows. | No — 1,2,2,3,4. |

If two employees tie for the highest salary in a department:

- `ROW_NUMBER` picks one of them as #1 and the other as #2.
  Arbitrary.
- `RANK` calls them both #1, then the next person is #3.
- `DENSE_RANK` calls them both #1, then the next person is #2.

The choice of function depends on the question:

- "Top 3 distinct salaries" → `DENSE_RANK` ≤ 3
- "Top 3 by salary, no ties" → `ROW_NUMBER` ≤ 3
- "Highest earner per department, with ties" → `RANK` = 1

---

## Top N per group

The canonical "top N per group" pattern. It uses a window
function to rank within a group, then filters to the top N.

```sql
WITH ranked AS (
  SELECT name, department_id, salary,
         DENSE_RANK() OVER (PARTITION BY department_id
                            ORDER BY salary DESC) AS rk
  FROM   Employee
)
SELECT name, department_id, salary
FROM   ranked
WHERE  rk <= 3;
```

This is the pattern for *every* "top N per group" question.
Memorize it. M07-M09 contain 8+ variations of this exact
shape.

### The decision: ROW_NUMBER vs DENSE_RANK

If the question is "exactly N people" → `ROW_NUMBER` ≤ N.
If the question is "everyone earning a salary in the top N
distinct salaries" → `DENSE_RANK` ≤ N.
If the question is "everyone ranked N or better" → `RANK` ≤ N.

In practice, the interviewer will say "top 3" and the
correct answer is whichever preserves ties naturally. Ask
if it's ambiguous.

---

## The OVER clause

Every window function call is followed by an `OVER` clause.
The OVER clause has three optional parts:

```sql
<function> OVER (
  [PARTITION BY <exprs>]
  [ORDER BY <exprs>]
  [<frame clause>]
)
```

- `PARTITION BY` — split the rows into windows. Without it,
  the window is the entire input.
- `ORDER BY` — order the rows *within* the window. Required
  for ranking functions; optional for others.
- Frame clause — see Lesson 39. Used for running totals and
  moving averages.

You can have `ORDER BY` inside a window function *and* a
separate `ORDER BY` at the query level. They are different:
the inner one controls ranking; the outer one sorts the
final output.

```sql
SELECT name, department_id, salary,
       RANK() OVER (PARTITION BY department_id
                    ORDER BY salary DESC) AS rk
FROM   Employee
ORDER BY department_id, rk;
```

---

## Common interview answers using window functions

- "Top N per group" → `DENSE_RANK` (or `ROW_NUMBER`) in a
  CTE, then filter.
- "Nth highest" → `DENSE_RANK = N`.
- "Cumulative sum" → `SUM(...) OVER (ORDER BY ...)` with a
  frame clause. Lesson 39.
- "Compare to previous row" → `LAG` / `LEAD`. Lesson 37.
- "First / last value in a group" → `FIRST_VALUE` /
  `LAST_VALUE`. Lesson 37.

---

## A note on determinism

Window functions without an `ORDER BY` for ranking are
non-deterministic. `ROW_NUMBER() OVER (PARTITION BY
department_id)` with no `ORDER BY` returns a number from 1
to N per department, but which row gets which number is
undefined. Always include `ORDER BY` in the window spec for
ranking.

If the ordering column has ties, the ranking is also
non-deterministic across the tied rows. Add a tie-breaker
(`id`, `created_at`, anything monotonic).

---

## Try it

Given `Employee(id, name, salary, department_id, hire_date)`:

1. Return every employee's name, salary, and their rank
   within their department by salary descending. Use
   `DENSE_RANK`.
2. Return the top 2 employees by salary per department.
   Show their name, department, and salary.
3. Same as 2, but include ties — if two employees tie for
   rank 2, include both. Use `RANK` instead of `DENSE_RANK`.
