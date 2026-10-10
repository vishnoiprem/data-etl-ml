# 43 — Query Rewrites

> **Lesson 43 of 43 — Query Performance & Optimization**

The fourth and final lever: the rewrite. The plan is good,
the indexes are right, the joins are ordered — but the query
itself can still be slow because of how it's written. The
senior move is having ten rewrites in your back pocket, each
with a one-sentence "before" and "after."

---

## 1. Subquery → JOIN

The single most common rewrite. A correlated subquery
re-executes for every row in the outer query; a JOIN
materializes once.

```sql
-- SLOW: correlated subquery, executes per user
SELECT u.id, u.email,
       (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS n
FROM users u;

-- FAST: aggregate-then-join, executes once
SELECT u.id, u.email, COALESCE(o.n, 0) AS n
FROM users u
LEFT JOIN (
  SELECT user_id, COUNT(*) AS n
  FROM orders
  GROUP BY user_id
) o ON o.user_id = u.id;
```

**The win:** O(N × M) becomes O(N + M) for the join side.

---

## 2. NOT EXISTS vs NOT IN vs LEFT JOIN

The anti-join has three spellings, and only one is right.

```sql
-- SLOW + WRONG: NULL handling
SELECT u.*
FROM users u
WHERE u.id NOT IN (SELECT user_id FROM orders);
-- If ANY user_id in orders is NULL, this returns ZERO rows.

-- CORRECT + FAST: NOT EXISTS
SELECT u.*
FROM users u
WHERE NOT EXISTS (
  SELECT 1 FROM orders o WHERE o.user_id = u.id
);

-- CORRECT + FAST: LEFT JOIN ... IS NULL
SELECT u.*
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE o.user_id IS NULL;
```

**The senior move:** "I'd never use `NOT IN` with a
subquery. `NOT EXISTS` and `LEFT JOIN ... IS NULL` both
handle NULLs correctly, and the optimizer treats them
identically. I'd pick `NOT EXISTS` for readability."

---

## 3. UNION vs UNION ALL

`UNION` sorts and deduplicates the entire result; `UNION ALL`
just concatenates. The sort is O(N log N) and the dedup is
expensive.

```sql
-- SLOW: sorts and dedupes 1M + 1M rows
SELECT id, name FROM users_us
UNION
SELECT id, name FROM users_eu;

-- FAST: just concatenates
SELECT id, name FROM users_us
UNION ALL
SELECT id, name FROM users_eu;
```

**The rule:** Use `UNION ALL` unless you specifically need
to dedupe. The dedupe is rarely what you want — and if it
is, you should do it explicitly with `GROUP BY` so the
intent is clear.

**The senior move:** "I'd grep for `UNION` in the codebase
and replace every occurrence with `UNION ALL` unless the
caller explicitly needs the dedup."

---

## 4. EXISTS vs IN

For semi-joins (do any matches exist?), `EXISTS` short-
circuits; `IN` materializes the subquery.

```sql
-- SLOW on large subquery: materializes all rows
SELECT u.*
FROM users u
WHERE u.id IN (SELECT user_id FROM orders);

-- FAST: short-circuits per user
SELECT u.*
FROM users u
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);
```

The difference is small in modern optimizers but can be
significant when the subquery is large.

**The senior move:** "I'd use `EXISTS` for semi-joins, `IN`
for literal lists. The two are not interchangeable when
NULLs are involved."

---

## 5. Derived table → CTE (and when CTE is slower)

CTEs are cleaner; derived tables are sometimes faster.

```sql
-- CTE (cleaner, but Postgres ≤ 11 inlined; ≥ 12 may not)
WITH active_users AS (
  SELECT id, email
  FROM users
  WHERE last_seen > NOW() - INTERVAL '30 days'
)
SELECT au.email, COUNT(o.id)
FROM active_users au
JOIN orders o ON o.user_id = au.id
GROUP BY au.email;

-- Equivalent derived table
SELECT au.email, COUNT(o.id)
FROM (
  SELECT id, email
  FROM users
  WHERE last_seen > NOW() - INTERVAL '30 days'
) au
JOIN orders o ON o.user_id = au.id
GROUP BY au.email;
```

**Postgres 12+** has *optimization fences* on CTEs. A CTE
referenced more than once is materialized to disk (the
`MATERIALIZED` keyword forces this even when referenced
once). If your CTE is huge and referenced once, a derived
table may be faster.

**The senior move:** "I'd start with a CTE for readability.
If `EXPLAIN ANALYZE` shows the CTE is being materialized
unnecessarily, I'd convert to a derived table, or add the
`NOT MATERIALIZED` hint (Postgres 12+)."

---

## 6. DISTINCT alternatives

`SELECT DISTINCT` is a sort-and-dedup. If you're using it to
"remove duplicates from a join", the real fix is the join.

```sql
-- SLOW: DISTINCT to dedup a one-to-many join
SELECT DISTINCT u.id, u.email
FROM users u
JOIN orders o ON o.user_id = u.id;

-- FAST: EXISTS (no join, no dedup)
SELECT u.id, u.email
FROM users u
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);

-- OR: GROUP BY (uses hash aggregate, often faster than sort dedup)
SELECT u.id, u.email
FROM users u
JOIN orders o ON o.user_id = u.id
GROUP BY u.id, u.email;
```

**The senior move:** "I'd never use `DISTINCT` to clean up
a join. The join is wrong, not the data. Either switch to
`EXISTS` (no rows from the orders side) or `GROUP BY` (if
you need aggregates)."

---

## 7. SELECT *

Pulling every column forces the engine to read every column
from the heap, even if the index already has what you need.

```sql
-- SLOW: can't use index-only scan
SELECT * FROM orders WHERE user_id = 42;

-- FAST: index-only scan if you have a covering index
SELECT id, status, created_at
FROM orders
WHERE user_id = 42;
-- + covering index
CREATE INDEX idx_orders_user_covering
  ON orders(user_id) INCLUDE (status, created_at);
```

The win is twofold: smaller network payload, and the
opportunity for an index-only scan.

**The senior move:** "I'd ban `SELECT *` in production
code. Always name the columns. The cost is invisibly paid
in network, in disk I/O, and in lost index-only scan
opportunities."

---

## 8. The CASE WHEN chain

Sometimes a chain of `CASE WHEN` is hiding an `OR` that
defeats an index.

```sql
-- SLOW: OR on different columns defeats indexes
SELECT *
FROM orders
WHERE status = 'paid' OR user_id = 42;

-- FAST: UNION ALL of two indexed queries
SELECT * FROM orders WHERE status = 'paid'
UNION ALL
SELECT * FROM orders WHERE user_id = 42 AND status != 'paid';
-- (or just: WHERE user_id = 42)
```

The second form lets each branch use its own index. The
first forces a single scan with an `OR` filter that most
optimizers can't push into an index.

**The senior move:** "I'd rewrite `OR` on different columns
as `UNION ALL` of two indexed queries."

---

## 9. The date_trunc trick

`date_trunc('day', ts)` on every row in a `GROUP BY` is
expensive — it's a function call per row.

```sql
-- SLOW: function call per row, no index can help
SELECT DATE_TRUNC('day', created_at) AS day, COUNT(*)
FROM orders
GROUP BY 1;

-- FAST: range scan on the underlying column
SELECT created_at::date AS day, COUNT(*)
FROM orders
WHERE created_at >= '2026-01-01' AND created_at < '2026-02-01'
GROUP BY 1;
```

Or, even better: a functional index.

```sql
CREATE INDEX idx_orders_day ON orders(DATE_TRUNC('day', created_at));
```

**The senior move:** "I'd push the date filter into the
`WHERE` clause as a range on the underlying column. That
lets the index do its job. The `date_trunc` only happens
in the projection, after the filter."

---

## 10. The LATERAL JOIN

The "for each row in the outer, run this query" pattern.
Useful for top-N per group.

```sql
-- SLOW: window function over the whole table
SELECT *
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
  FROM orders
) t
WHERE rn <= 3;

-- FAST: LATERAL join with LIMIT 3
SELECT u.id, o.*
FROM users u
CROSS JOIN LATERAL (
  SELECT *
  FROM orders o
  WHERE o.user_id = u.id
  ORDER BY o.created_at DESC
  LIMIT 3
) o;
```

The LATERAL form lets the inner query use the index on
`user_id` to seek directly, fetching only 3 rows per
outer row. The window function must rank all rows first.

**The senior move:** "For top-N per group on a large table,
I'd use `LATERAL` with `LIMIT N`, not `ROW_NUMBER()`. The
index seek per outer row is dramatically faster."

---

## 11. The interview answer

> "Ten rewrites I use: subquery to JOIN for correlated
> subqueries; `NOT EXISTS` over `NOT IN` to handle NULLs
> correctly; `UNION ALL` over `UNION` unless dedup is
> needed; `EXISTS` over `IN` for semi-joins on large
> subqueries; derived table over CTE when the CTE would
> be materialized; `EXISTS` or `GROUP BY` over `DISTINCT`
> to dedup a join; explicit columns over `SELECT *` to
> allow index-only scans; `UNION ALL` over `OR` to let
> each branch use its own index; range filters over
> `date_trunc` to keep the index useful; `LATERAL` with
> `LIMIT N` over window functions for top-N per group."

That single paragraph is the cheat sheet. Senior answer in
45 seconds.

---

## Try it

Pick any slow query. Apply one of the ten rewrites.
Rerun `EXPLAIN ANALYZE`. Confirm the new plan is faster
*and* doing less work. That's the rewrite loop — and it's
the answer to "rewrite this query to make it faster."

*Author: Prem Vishnoi <pvishnoi@avilx.com>*
