# Lesson 02 — How to Answer SQL Interview Questions

> **Goal:** a repeatable 5-step framework for turning an
> interview prompt into a correct, defensible SQL query.

---

## The framework

Every SQL interview question is the same problem at heart:
**translate a question written in English into a query that
returns the right shape of answer.** Whether the question is
"second highest salary" or "median salary by department", the
five steps are the same.

### Step 1 — Clarify the grain

Before you write a query, answer this out loud:
*"What does one row of my output represent?"*

- "Top 3 employees by department" → one row per (department,
  employee) within the top 3.
- "Top 3 employees" → one row per employee (across the whole
  company), top 3 by some metric.
- "Second highest salary" → one row, the salary value, or
  possibly an empty result if the table has fewer than two
  rows.

If you can't state the grain, you don't yet understand the
question. Most wrong interview answers are wrong because the
candidate never pinned down the grain.

### Step 2 — Identify the columns and the predicates

List, in plain English:

- **Output columns.** What does the result need to show?
- **Filter columns.** What rows are included?
- **Group-by columns.** What is the level of aggregation?
- **Ordering.** Tie-breakers matter. (See `ORDER BY salary DESC,
  id ASC`.)

### Step 3 — Sketch the pattern, not the syntax

Pick one of the canonical patterns:

| Pattern | When to use it |
|---|---|
| `JOIN` + `GROUP BY` | "Total / count / average of X by Y". |
| `ROW_NUMBER` / `RANK` | "Top N per group", "Nth highest". |
| Self-join | "Pairs of rows in the same table" (consecutive, prev/next). |
| Anti-join (`NOT IN`, `NOT EXISTS`, `LEFT JOIN ... IS NULL`) | "Customers who never ordered", "employees without a manager". |
| `LAG` / `LEAD` | "Compare this row to the previous / next row". |
| Recursive CTE | "Tree traversal", "running total that resets". |
| Conditional aggregation | "Pivot", "pct of rows that satisfy X". |

Sketching the pattern first stops you from writing a query
that *works* for the wrong reason.

### Step 4 — Write the query

Now actually write it. A few habits:

- **Use CTEs liberally.** A 3-CTE query reads better than one
  query with three nested subqueries.
- **Avoid `SELECT *`** in interview answers — name the columns
  you want.
- **Type your NULLs.** If a column is nullable, decide whether
  you want to keep or filter the NULLs. Be explicit.

### Step 5 — Verify with a small example

Walk through the query against the sample data. For each row
of input, predict which output row (if any) it produces. If
your prediction disagrees with what the query does, you have
a bug. This step is what separates people who ace SQL screens
from people who don't.

### Step 6 (interview only) — Explain the trade-offs

If there's time, call out the alternative you didn't take and
why. *"I used a window function rather than a self-join because
the window version is O(n) while the self-join is O(n²)."*
Interviewers notice.

---

## A worked example

> *"Find the second-highest distinct salary in the Employee
> table."*

**Step 1 — Grain.** One row. One value: the salary.
**Step 2 — Columns.** Salary.
**Step 3 — Pattern.** Nth-highest → `DENSE_RANK` or `LIMIT
1 OFFSET 1` after sorting.
**Step 4 — Query.**

```sql
SELECT MAX(salary) AS second_highest
FROM (
  SELECT DISTINCT salary
  FROM Employee
  ORDER BY salary DESC
  LIMIT 1 OFFSET 1
);
```

**Step 5 — Verify.** If salaries are 100, 200, 200, 300, the
distinct list is 100, 200, 300. `LIMIT 1 OFFSET 1` returns 200.
Correct.
**Step 6 — Trade-off.** Alternatively, `DENSE_RANK() = 2` would
return all rows tied at the second-highest value. The right
choice depends on whether the interviewer wants "the second
distinct value" (limit/offset) or "everyone whose salary is
second-highest" (DENSE_RANK).

---

## Common mistakes

1. **Jumping to code.** If you write a query before knowing the
   grain, you will almost always have to rewrite it.
2. **Forgetting ties.** The question says "top 3" — do you mean
   exactly 3 employees, or everyone tied at the 3rd rank? In
   real interviews this matters.
3. **Mixing WHERE and HAVING.** Filters on the row go in WHERE;
   filters on the group go in HAVING.
4. **Not handling NULLs.** If the column is nullable, the
   *absence* of a row is data. Decide what to do with it.

---

## Try it

Take this prompt:

> *"Find the names of customers who have placed at least 3
> orders."*

Spend 5 minutes running the framework. Don't write SQL yet.
State the grain, the columns, the pattern, and the trade-offs.
Then write the query in your head and check it against the
framework. This is the muscle you build in M07–M09.
