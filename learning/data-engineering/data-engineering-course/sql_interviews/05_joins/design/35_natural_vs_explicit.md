# Lesson 35 — Natural Joins vs Explicit Joins

> **Goal:** understand `NATURAL JOIN`, `USING`, and why
> explicit ON is usually the right choice.

---

## NATURAL JOIN

`NATURAL JOIN` joins two tables on every column that has
the same name in both.

```sql
-- These are equivalent (if both tables have `id` and `name`):
SELECT * FROM Employee NATURAL JOIN Department;
SELECT * FROM Employee JOIN Department USING (id, name);
```

That's it. The engine figures out the join columns by
matching names. If the tables have no columns in common,
`NATURAL JOIN` falls back to a CROSS JOIN. If they have
multiple columns in common, *all* of them are used.

### Why NATURAL JOIN is a code smell

```sql
-- Today
CREATE TABLE Employee (id INT, dept_id INT, name TEXT);
CREATE TABLE Department (id INT, name TEXT);

SELECT * FROM Employee NATURAL JOIN Department;
-- Joins on id AND name. Result: an employee in the right
-- department only if the department name matches the employee
-- name (which they don't). Empty result.
```

The query silently returns the wrong answer because the
schemas happened to share a column (`name`) that wasn't
intended as a join key. Add a column to either table that
happens to share a name with the other, and the query
breaks in a new and surprising way.

This is the kind of bug that takes hours to debug because
the SQL looks fine.

### When NATURAL JOIN is OK

Almost never. Some style guides ban it entirely. If you
must use it, comment the join columns explicitly so the
next reader doesn't have to guess.

---

## USING

`USING (col)` is the semi-explicit form. The column must
exist in both tables with the same name; the engine joins
on equality. The result has a single column (not two) for
the shared name.

```sql
SELECT * FROM Employee JOIN Department USING (dept_id);
```

`USING` is safer than `NATURAL JOIN` because you name the
column(s). The result is more predictable.

### When USING is OK

For ad-hoc queries in a REPL, `USING` is convenient. For
production code, prefer explicit `ON`. The reason: `USING`
hides the join predicate in the column list, and a
column-name change in either table silently breaks the
query.

---

## Explicit ON

```sql
SELECT *
FROM   Employee e
JOIN   Department d ON e.dept_id = d.id;
```

The join predicate is in the `ON` clause, visible, and
unambiguous. Two columns named `id` in the result (one from
each table) is sometimes a hassle, but it forces you to
qualify with the alias, which is good practice.

**Default to explicit ON.** It's the most readable and the
least likely to break under schema changes.

---

## Comparing the three

| Style | Pros | Cons |
|---|---|---|
| `NATURAL JOIN` | Concise. | Fragile; depends on column names. |
| `USING (col)` | Concise; names the join column. | Still name-dependent; result has one column not two. |
| `ON a.col = b.col` | Explicit, robust. | Verbose. |

---

## A common interview gotcha

> "What does `SELECT * FROM A NATURAL JOIN B` return if A
> and B have no common columns?"

Answer: a CROSS JOIN. The engine joins on zero columns,
which means every pair.

> "What if they have *two* common columns?"

Answer: a join on both. If you only meant one of them,
NATURAL JOIN gives the wrong answer.

---

## Try it

Given `Employee(id, name, dept_id)` and
`Department(id, name, location)`:

1. Write the join as `NATURAL JOIN`. Predict which columns
   it joins on.
2. Run it. Check the result.
3. Add a column to `Employee` named `location` (defaulting
   to `'remote'`). Re-run the `NATURAL JOIN`. Observe the
   breakage.
4. Rewrite using explicit `ON` and verify the result is
   unchanged.
