# Lesson 11 — NULL Handling: COALESCE, NULLIF, IS NULL

> **Goal:** treat NULL as a first-class value, not as zero
> or empty string.

---

## What NULL means

`NULL` means **unknown**. Not zero, not empty string, not
"no value". The salary of an employee is NULL when we don't
know it. Treating NULL as 0 turns an unknown into a known,
which is a data error.

This is the most common source of bugs in interview SQL.
`WHERE salary = 0` will not find employees with unknown
salary. `WHERE salary = NULL` will never return rows, in any
SQL dialect. The correct test is `WHERE salary IS NULL`.

---

## IS NULL and IS NOT NULL

```sql
SELECT id, name FROM Employee WHERE manager_id IS NULL;
SELECT id, name FROM Employee WHERE manager_id IS NOT NULL;
```

These are the only correct ways to test for NULL. Avoid:

- `WHERE manager_id = NULL` — always FALSE.
- `WHERE manager_id <> NULL` — always FALSE.
- `WHERE NOT (manager_id = NULL)` — also always FALSE (because
  the inner expression is FALSE, and NOT FALSE is TRUE — but
  the result is filtered for `manager_id = NULL` which is
  FALSE, so the row is dropped).

The last one is the trap. Three-valued logic is sneaky.

---

## COALESCE

`COALESCE(a, b, c, ...)` returns the first non-NULL argument.
The "if null, then ..." operator.

```sql
SELECT name, COALESCE(salary, 0) AS salary
FROM   Employee;
```

`COALESCE(salary, 0)` is a synonym for `ISNULL(salary, 0)`
in SQL Server / MySQL. Standard SQL is `COALESCE`.

The most common pattern:

```sql
SELECT
  COUNT(*)                       AS total,
  COUNT(COALESCE(phone, ''))     AS with_phone,
  SUM(COALESCE(salary, 0))       AS total_salary
FROM   Employee;
```

`COALESCE(salary, 0)` turns unknown salaries into 0 so they
contribute to the sum. Whether that's the right thing depends
on the question. Often it isn't — be careful.

---

## NULLIF

`NULLIF(a, b)` returns NULL if `a = b`, else returns `a`. The
"if equal, then NULL" operator.

```sql
SELECT NULLIF(status, 'cancelled') FROM Orders;
```

Replaces 'cancelled' with NULL. Useful in conditional
aggregation:

```sql
SELECT
  COUNT(*) AS total,
  COUNT(NULLIF(status, 'cancelled')) AS non_cancelled
FROM   Orders;
```

The classic interview use case: counting "rows where X is
true" without a CASE expression.

```sql
COUNT(NULLIF(x, 0))       -- counts rows where x != 0
SUM(NULLIF(x, 0))         -- sums x over rows where x != 0
```

---

## Three-valued logic

`WHERE` evaluates to TRUE, FALSE, or UNKNOWN. Rows are
returned only if the predicate is TRUE.

| A | B | A AND B | A OR B | NOT A |
|---|---|---|---|---|
| T | T | T | T | F |
| T | F | F | T | F |
| T | U | U | T | F |
| F | T | F | T | T |
| F | F | F | F | T |
| F | U | F | U | T |
| U | T | U | T | U |
| U | F | F | U | U |
| U | U | U | U | U |

(T = TRUE, F = FALSE, U = UNKNOWN.)

The takeaway: **a NULL in the predicate makes the predicate
UNKNOWN, which drops the row**. So `WHERE salary > 0` drops
employees with NULL salary. This is usually what you want, but
sometimes you want to keep them. Be explicit.

---

## Aggregation recap

Aggregates skip NULLs by default:

- `COUNT(*)` — counts every row, NULLs included.
- `COUNT(x)` — counts non-NULL `x`.
- `SUM(x)` — sums non-NULL `x`; NULL if all NULL.
- `AVG(x)` — averages non-NULL `x`; NULL if all NULL.
- `MIN(x)` / `MAX(x)` — ignores NULLs; NULL if all NULL.

This is why `AVG(salary)` differs from `SUM(salary) /
COUNT(*)`. The first excludes NULL salaries from the
denominator; the second includes them.

---

## Try it

Given `Orders(id, customer_id, total, status, order_date)`:

1. Count the orders that are not yet shipped. Treat `NULL`
   status as "not shipped".
2. Compute total revenue, treating NULL totals as 0. (You
   decide if this is what you want. The exercise is to write
   it both ways and compare.)
3. Find the orders whose total is NULL or zero. Use
   `NULLIF` and a single predicate.
