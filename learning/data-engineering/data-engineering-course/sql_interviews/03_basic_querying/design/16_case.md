# Lesson 16 — CASE Expressions

> **Goal:** if/then/else logic inside a query.

---

## The two forms

### Simple CASE

```sql
SELECT name,
       CASE department_id
         WHEN 1 THEN 'Engineering'
         WHEN 2 THEN 'Sales'
         WHEN 3 THEN 'Marketing'
         ELSE 'Other'
       END AS department_name
FROM   Employee;
```

Tests one expression against a list of values. Equivalent to
a chain of `=`. NULL on the left matches nothing; NULL in
the WHEN list matches nothing.

### Searched CASE

```sql
SELECT name,
       CASE
         WHEN salary > 200000 THEN 'Executive'
         WHEN salary > 100000 THEN 'Senior'
         WHEN salary > 50000  THEN 'Mid'
         ELSE 'Junior'
       END AS band
FROM   Employee;
```

Each WHEN has its own boolean predicate. The first one that
matches wins. More flexible than the simple form.

**Prefer the searched form.** It handles more cases (range
checks, NULLs, multiple columns) and is what you'll see in
real code.

---

## CASE returns a value

`CASE` is an expression, not a statement. It returns a
single value that can be used anywhere an expression can.

```sql
SELECT
  SUM(CASE WHEN status = 'delivered' THEN total ELSE 0 END) AS delivered_revenue,
  SUM(CASE WHEN status = 'cancelled' THEN total ELSE 0 END) AS cancelled_revenue
FROM   Orders;
```

This is *conditional aggregation* — the foundation of every
"pivot" query. It turns a `GROUP BY` of one column into
many columns. M04 covers this in depth.

---

## CASE in WHERE

`CASE` is a value, not a predicate, so you can't write
`WHERE CASE WHEN ... THEN ... END`. You can write
`WHERE (CASE WHEN x THEN 1 ELSE 0 END) = 1`, but it's
clunky. Just write `WHERE x` directly.

---

## CASE in ORDER BY

You can sort by a CASE expression to get custom orderings:

```sql
SELECT * FROM Employee
ORDER BY
  CASE department_id
    WHEN 3 THEN 1   -- Engineering first
    WHEN 1 THEN 2
    WHEN 2 THEN 3
    ELSE 4
  END;
```

This is how you put a specific value at the top of a sort
without a separate rank column.

---

## NULLIF inside CASE

`NULLIF(x, y)` is `CASE WHEN x = y THEN NULL ELSE x END`. The
shorter form is sometimes easier to read.

```sql
-- Same as CASE WHEN x = 0 THEN NULL ELSE x END
SELECT NULLIF(quantity, 0) FROM OrderItem;
```

---

## COALESCE inside CASE

`COALESCE(a, b, c)` is `CASE WHEN a IS NOT NULL THEN a WHEN
b IS NOT NULL THEN b ELSE c END`. Use it whenever you want
"the first non-null value".

---

## A note on short-circuit

`CASE` evaluates WHEN clauses in order and stops at the first
match. The remaining clauses are not evaluated. This matters
when a WHEN clause has a side effect (it shouldn't, in pure
SQL, but a UDF can have one).

---

## Try it

Given `Employee(id, name, salary, department_id, hire_date)`:

1. Add a `level` column with values `'high'` if salary >
   150000, `'mid'` if salary > 80000, else `'low'`.
2. Compute the total salary for each band (high/mid/low).
3. List employees ordered by level (`high` first, then
   `mid`, then `low`) and within each level by salary desc.
