# Lesson 04 — SELECT, FROM, WHERE: The Basics

> **Goal:** the skeleton of every SQL query.

---

## The skeleton

```sql
SELECT <columns>
FROM   <table>
WHERE  <predicate>;
```

Three clauses. Every query in this track (and in your career)
is some elaboration of this shape.

- `SELECT` — which columns to return.
- `FROM` — where the rows come from.
- `WHERE` — which rows to keep.

That's the whole thing. Everything else (`JOIN`, `GROUP BY`,
window functions) is an elaboration.

---

## SELECT

A comma-separated list of expressions. Each expression becomes
a column in the output.

```sql
SELECT 1, 2 + 3, 'hello';
```

Returns one row: `1, 5, 'hello'`. The expressions don't have to
reference any column.

`SELECT *` returns every column. It's fine in a quick REPL
session. In interview answers and production code, **name the
columns explicitly** — your future self (and the interviewer)
will thank you.

### Aliases

You can rename a column with `AS`:

```sql
SELECT salary * 12 AS annual_salary
FROM   Employee;
```

The keyword `AS` is optional in most dialects. `salary * 12
annual_salary` also works. Prefer the explicit `AS`.

---

## FROM

A comma-separated list of tables. Almost always one table or
one table with joins.

```sql
SELECT id, name
FROM   Employee;
```

You can alias tables too:

```sql
SELECT e.id, e.name
FROM   Employee AS e;
```

Table aliases are conventional in any non-trivial query. They
make joins readable and they let you reference the same table
twice (self-join) without ambiguity.

---

## WHERE

A boolean predicate. Rows that evaluate to TRUE are kept; rows
that evaluate to FALSE or UNKNOWN are dropped.

```sql
SELECT id, name
FROM   Employee
WHERE  department_id = 5
  AND  salary > 100000;
```

The supported operators are roughly:

- Comparison: `=`, `<>`, `<`, `>`, `<=`, `>=`
- Logical: `AND`, `OR`, `NOT`
- Pattern: `LIKE`, `IN`, `BETWEEN`
- NULL: `IS NULL`, `IS NOT NULL`

`NOT` has higher precedence than `AND`, which has higher
precedence than `OR`. When in doubt, parenthesize.

---

## A note on three-valued logic

SQL has three truth values: TRUE, FALSE, UNKNOWN. A row is
returned by `WHERE` only if the predicate is TRUE. If the
predicate involves a NULL, the result is UNKNOWN and the row
is dropped.

This bites people who write `WHERE salary = NULL` and wonder
why nothing returns. The right test is `WHERE salary IS NULL`.
Lesson 11 covers this in detail.

---

## Sample query

```sql
SELECT id, name, salary
FROM   Employee
WHERE  department_id = 3
  AND  salary >= 50000;
```

---

## Try it

Given a table `Product(id, name, category, price, in_stock)`,
write a query that returns the id, name, and price of every
in-stock product in the `'electronics'` category, ordered by
price descending.

Write it from memory. Check by running it against a seeded
`QueryRunner`.
