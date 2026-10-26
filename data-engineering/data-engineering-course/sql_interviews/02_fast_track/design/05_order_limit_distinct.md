# Lesson 05 — ORDER BY, LIMIT, DISTINCT

> **Goal:** sort, truncate, and dedupe the output of a query.

---

## ORDER BY

`ORDER BY` sorts the result set. The default is ascending; you
can write `ASC` or `DESC` explicitly.

```sql
SELECT id, name, salary
FROM   Employee
ORDER BY salary DESC, id ASC;
```

**Tie-breakers matter.** If two employees have the same
salary, the query above orders them by `id` ascending. Always
include a tie-breaker — a stable order makes your results
reproducible, which is critical in tests.

`ORDER BY` can reference:

- Column names from `SELECT`.
- Aliases declared in `SELECT`.
- The ordinal position of the column in the `SELECT` list
  (e.g. `ORDER BY 1`).
- Expressions that aren't even in the `SELECT`.

The last one is occasionally useful. Most of the time, name
the column.

### NULL ordering

`NULL` is "less than" every value in ascending order and
"greater than" every value in descending order in most
databases. SQLite follows this. Be careful: `ORDER BY x ASC`
puts NULLs first. If you want NULLs last, write
`ORDER BY x ASC NULLS LAST` (PostgreSQL) or use a
workaround like `ORDER BY x IS NULL, x ASC` (SQLite).

---

## LIMIT

`LIMIT n` returns the first `n` rows of the query. Combine
with `ORDER BY` to get "the top N".

```sql
SELECT id, name, salary
FROM   Employee
ORDER BY salary DESC
LIMIT  10;
```

For "skip the first M, then take N", use `OFFSET`:

```sql
SELECT id, name, salary
FROM   Employee
ORDER BY salary DESC
LIMIT  10 OFFSET 10;   -- rows 11..20
```

**Beware the offset trap.** `OFFSET` scans and discards the
first M rows. For `OFFSET 1_000_000` the engine has to read
a million rows just to throw them away. For paginated APIs
prefer *keyset pagination* (`WHERE id > last_seen_id`).

### FETCH FIRST (ANSI)

The standard syntax is `OFFSET ... ROWS FETCH FIRST ...
ROWS ONLY`. SQLite doesn't support this; PostgreSQL does;
Snowflake does. The MySQL-style `LIMIT N OFFSET M` is more
portable in practice.

---

## DISTINCT

`SELECT DISTINCT` removes duplicate rows from the output.
It's a deduplicator over the entire SELECT list, not a single
column.

```sql
SELECT DISTINCT department_id
FROM   Employee;
```

Returns the set of distinct department IDs.

`COUNT(DISTINCT column)` counts distinct non-NULL values of
that column. The classic interview question: *"How many
unique customers placed an order last month?"*

```sql
SELECT COUNT(DISTINCT customer_id)
FROM   Orders
WHERE  order_date >= '2024-01-01';
```

`SELECT DISTINCT *` is rare but valid. It returns every
distinct row of the table. Useful as a quick dedup.

`DISTINCT` on multiple columns: `DISTINCT (a, b)` keeps rows
with distinct combinations of `a` and `b`. In SQLite the
parens are optional; in standard SQL they're required.

---

## When ORDER BY + LIMIT can lie

The pattern "order by X, limit 1" is the canonical "find the
X" — but only if there's a meaningful tie-breaker. If two
employees have the same salary and you want "the highest
earner", `ORDER BY salary DESC LIMIT 1` will return one of
them arbitrarily. Use `ROW_NUMBER` or a subquery with `MAX()`
to make the answer deterministic.

---

## Try it

Given `Product(id, name, category, price, in_stock)`, write
three queries:

1. Top 5 most expensive products, with their name and price.
2. The distinct set of categories in the table.
3. The 3rd through 5th most expensive products.

Write them from memory.
