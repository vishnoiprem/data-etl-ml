# Lesson 13 — Filtering with WHERE, IN, BETWEEN, LIKE

> **Goal:** the four filter patterns you'll use in 90% of
> queries.

---

## Comparison operators

`=`, `<>`, `<`, `>`, `<=`, `>=`. Standard SQL. Nothing
surprising.

The one gotcha is `<>`. It's the standard "not equal".
Some dialects also accept `!=` (MySQL, SQLite). Prefer `<>`.

---

## AND / OR / NOT

Combine predicates with `AND` (both true), `OR` (either
true), `NOT` (negate).

```sql
SELECT * FROM Employee
WHERE  department_id = 3
   AND salary > 50000
   AND NOT (name LIKE 'A%');
```

**Precedence:** `NOT` > `AND` > `OR`. When in doubt,
parenthesize.

```sql
-- Ambiguous: NOT binds to 'salary > 50000', not the whole OR
WHERE NOT department_id = 3 OR salary > 50000

-- Clear: explicit grouping
WHERE NOT (department_id = 3 OR salary > 50000)
```

---

## IN

Tests whether a value is in a list. Equivalent to a chain of
`=` joined with `OR`, but more readable.

```sql
SELECT * FROM Employee
WHERE  department_id IN (1, 3, 7);
```

`NOT IN` is the negation. With a NULL in the list, `NOT IN`
returns no rows (because the comparison is UNKNOWN for NULL).
This is a famous bug — see Lesson 31.

The list can also be a subquery:

```sql
SELECT * FROM Employee
WHERE  department_id IN (
  SELECT id FROM Department WHERE location = 'NY'
);
```

---

## BETWEEN

Inclusive range test. `BETWEEN a AND b` means `x >= a AND x <= b`.
Both ends are inclusive.

```sql
SELECT * FROM Orders
WHERE  order_date BETWEEN '2024-01-01' AND '2024-12-31';
```

The `BETWEEN` is inclusive on both sides, so this captures
all of 2024. With dates, watch for time-of-day: a TIMESTAMP
of `'2024-12-31 23:59:59'` is included, but `'2024-12-31
00:00:00'` is also included. The boundary semantics depend
on whether the column is a DATE or a TIMESTAMP.

`BETWEEN` is *not* restricted to numbers. It works on strings
(alphabetical range), dates, and any orderable type.

---

## LIKE

Pattern matching on strings. Two wildcards:

- `%` — zero or more characters.
- `_` — exactly one character.

```sql
SELECT * FROM Customer
WHERE  email LIKE '%@gmail.com';

SELECT * FROM Product
WHERE  name LIKE 'Pro%';      -- starts with 'Pro'

SELECT * FROM Product
WHERE  name LIKE '_____';     -- exactly 5 characters

SELECT * FROM Product
WHERE  name LIKE 'P_o%';      -- P, any char, o, anything
```

`LIKE` is case-sensitive in PostgreSQL, case-insensitive in
MySQL and SQLite. To make it case-insensitive in PostgreSQL,
use `ILIKE`.

To match the literal `%` or `_`, escape with `\`:
`name LIKE '50\%' ESCAPE '\'`. Or use the standard
`LIKE '50\%' ESCAPE '\'` form.

For more complex patterns, use a regular expression. Most
databases have a `REGEXP` operator or `~` (PostgreSQL).
SQLite has none — install the `regexp` extension or fall back
to multiple `LIKE`s.

### NOT LIKE

Negation. Same wildcards, opposite meaning.

```sql
SELECT * FROM Customer WHERE email NOT LIKE '%@example.com';
```

---

## Combining the four

A real WHERE clause stacks all of these:

```sql
SELECT id, name, salary
FROM   Employee
WHERE  department_id IN (1, 3, 5)
  AND  salary BETWEEN 60000 AND 120000
  AND  name LIKE 'A%'
  AND  manager_id IS NOT NULL;
```

The order of the predicates doesn't affect correctness, but
**put the most selective predicate first** as a habit. The
query optimizer usually reorders, but if it doesn't, putting
the most selective first is a small win.

---

## Performance note

`LIKE 'foo%'` (anchored at the start) can use an index. `LIKE
'%foo'` (anchored at the end) cannot. If you have a lot of
rows and you're searching for a suffix pattern, consider a
full-text index instead.

`IN` with a long literal list (e.g. 10,000 IDs) is usually
rewritten as a join for performance. Modern engines do this
automatically.

---

## Try it

Given `Customer(id, name, email, country, signup_date)`:

1. Find customers whose email ends with `@gmail.com` and who
   signed up in 2024.
2. Find customers in the US, UK, or DE whose name starts
   with a vowel.
3. Find customers whose signup date is in the first or
   last quarter of 2023.
