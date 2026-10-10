# 42 — Join Optimization

> **Lesson 42 of 43 — Query Performance & Optimization**

The third lever: how joins are ordered and which algorithm
the engine picks. The senior move is knowing the three
algorithms (nested loop, hash, merge), the small/large
heuristic, and the three most common join bugs (different
types, function on the join key, implicit cross joins).

---

## 1. The three join algorithms

| Algorithm | Best when | Cost |
|---|---|---|
| **Nested Loop** | Small outer, indexed inner, low selectivity. | O(outer × log(inner)) with index. O(outer × inner) without. |
| **Hash Join** | Large equi-join, no useful sort order, enough `work_mem`. | O(outer + inner) build + probe. |
| **Merge Join** | Both inputs already sorted on the join key. | O(outer + inner) walk. |

**The senior move:** Name all three unprompted and explain
when each wins. "Nested loop for a small outer with an
indexed inner; hash join for a large equi-join; merge join
when both sides are pre-sorted on the join key."

The optimizer picks based on row count estimates, indexes,
and `work_mem`. If it picks wrong, you can hint it
(`SET enable_nestloop = off`) to confirm — but the real fix
is to change the schema, the query, or the statistics.

---

## 2. The small/large heuristic

In a nested-loop join, the **outer** is scanned once, and the
**inner** is scanned once per outer row. So the smaller
table should be the outer.

```sql
-- BAD: 1M users outer, 10 orders inner, 10M probes
SELECT *
FROM users u
JOIN orders o ON o.user_id = u.id;

-- SAME PLAN — Postgres usually reorders correctly.
-- But the principle: small outer, large inner, indexed
-- inner on the join key.
```

The optimizer usually gets this right. But there are two
cases where it doesn't:

1. The statistics are stale (`ANALYZE` fixes this).
2. You use a `LEFT JOIN` with a non-equi predicate, which
   constrains the optimizer's reordering.

**The senior move:** "If the optimizer picks the wrong join
order, I'd `ANALYZE` the tables first. If it's still wrong,
I'd consider rewriting as a CTE to force a different
materialization point, but only as a last resort."

---

## 3. Broadcast vs shuffle (distributed engines)

In Snowflake, BigQuery, Spark, and Redshift, joins happen
across nodes. The two strategies are:

| Strategy | What it does | Best when |
|---|---|---|
| **Broadcast (replicated) join** | Copy the small side to every node. | Small side fits in memory (e.g., < 10 MB). |
| **Shuffle (partitioned) join** | Re-partition both sides on the join key. | Both sides are large. |

The heuristic: if one side is small enough to broadcast,
broadcast it. Otherwise, shuffle both sides on the join key.

In BigQuery:

```sql
-- BigQuery auto-broadcasts if the smaller side is small.
-- The plan will show "BROADCAST" or "HASH" join.
-- To force: use @@join_method hint (BigQuery 2024+).
```

In Snowflake:

```sql
-- Check the Query Profile. If a large join shows high
-- "Bytes spilled" or "Partitions scanned", it's shuffling.
-- Pre-cluster both tables on the join key.
ALTER TABLE orders CLUSTER BY (user_id);
```

The senior move: "For a distributed join, if one side is
small, I'd broadcast it. If both are large, I'd cluster both
sides on the join key so the shuffle is cheap."

---

## 4. The "join on different types" bug

The classic silent performance killer. Postgres won't warn
you; MySQL might. Snowflake and BigQuery error out.

```sql
-- users.id is INT
-- orders.user_id is BIGINT

-- Looks fine, runs fine, but the index on orders(user_id)
-- is USELESS here. Postgres does an implicit cast and
-- can't use the index.
SELECT *
FROM users u
JOIN orders o ON o.user_id = u.id;
```

The plan: `Seq Scan on orders` even though there's an index
on `user_id`. Why? The cast to BIGINT forces a per-row
computation that defeats the index.

**The fix:** Match the types.

```sql
ALTER TABLE users ALTER COLUMN id TYPE BIGINT;
-- Or: cast in the query
SELECT *
FROM users u
JOIN orders o ON o.user_id = u.id::INT;
```

**The senior move:** "I'd check the types on the join keys
*first* before adding an index. Adding an index to a join
key with a type mismatch is wasted work."

---

## 5. The "join on a function" anti-pattern

The same problem, different cause. Wrapping the join key in
a function makes the index useless.

```sql
-- The index on orders(user_id) can't be used because the
-- join is on LOWER(u.email), not u.id.
SELECT *
FROM users u
JOIN orders o ON o.user_id = LOWER(u.email);

-- The fix: make the function deterministic, or pre-compute.
```

Or:

```sql
-- The index on events(ts) can't be used because the join
-- is on DATE_TRUNC('day', ts), not ts.
SELECT *
FROM events e
JOIN daily_aggregates d ON d.day = DATE_TRUNC('day', e.ts);
```

**The fix:** Add a functional index, or pre-compute the
column, or change the join key.

```sql
-- Functional index (Postgres)
CREATE INDEX idx_events_day ON events(DATE_TRUNC('day', ts));

-- Or: add a generated column
ALTER TABLE events ADD COLUMN event_day DATE
  GENERATED ALWAYS AS (DATE_TRUNC('day', ts)) STORED;
CREATE INDEX idx_events_event_day ON events(event_day);
```

**The senior move:** "I'd never wrap a join key in a
function. If the business really wants to join on the
transformed value, I'd add a functional index or a
generated column."

---

## 6. The implicit cross-join bug

A `WHERE` clause with multiple unrelated conditions can turn
a join into a cross join by accident.

```sql
-- INTENT: orders with their users.
-- ACTUAL: every order paired with every user where
-- u.signup_date < o.created_at. That's a cross join
-- filtered by date.
SELECT *
FROM users u, orders o
WHERE u.signup_date < o.created_at;
```

**The fix:** Use explicit `JOIN` syntax with a proper
predicate.

```sql
SELECT *
FROM users u
JOIN orders o ON o.user_id = u.id;
```

**The senior move:** "I'd ban comma-join syntax in code
review. Always use explicit `JOIN ... ON`. The cost of
implicit cross joins is too high."

---

## 7. Worked example #1 — slow orders-by-user

```sql
-- Slow: 30 seconds
SELECT u.email, COUNT(o.id) AS n
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE o.status = 'paid'
GROUP BY u.email
ORDER BY n DESC
LIMIT 10;
```

Plan:

```
Limit
  -> Sort
    -> HashAggregate
      -> Hash Join
        -> Seq Scan on users u
        -> Hash
          -> Seq Scan on orders o
            Filter: status = 'paid'
```

Two seq scans. The fix: indexes.

```sql
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
CREATE INDEX idx_orders_paid_user ON orders(user_id)
  WHERE status = 'paid';  -- if 90% are 'paid', this is small
```

After the indexes, the plan shows `Index Scan` on orders
and execution drops to < 100 ms.

---

## 8. Worked example #2 — join on a function

```sql
-- Slow: 8 seconds
SELECT u.email, COUNT(*) AS n
FROM users u
JOIN events e ON e.user_id = LOWER(u.email)
WHERE e.event_type = 'click'
GROUP BY u.email
ORDER BY n DESC
LIMIT 100;
```

Plan: `Hash Join` with `Hash Cond: (e.user_id = (lower(u.email)))`.
The lower() function defeats any index on `e.user_id`.

**The fix:**

```sql
-- Pre-compute email_lower on users
ALTER TABLE users ADD COLUMN email_lower TEXT
  GENERATED ALWAYS AS (LOWER(email)) STORED;
CREATE INDEX idx_users_email_lower ON users(email_lower);

-- Add index on events
CREATE INDEX idx_events_user_type ON events(user_id, event_type);

-- Rewrite the query to use the pre-computed column
SELECT u.email, COUNT(*) AS n
FROM users u
JOIN events e ON e.user_id = u.email_lower
WHERE e.event_type = 'click'
GROUP BY u.email
ORDER BY n DESC
LIMIT 100;
```

Execution drops from 8 s to 80 ms.

---

## 9. Worked example #3 — Snowflake shuffle

```sql
-- Slow: 5 minutes
SELECT o.user_id, SUM(o.amount)
FROM orders o
JOIN users u ON u.id = o.user_id
WHERE u.country = 'US'
GROUP BY o.user_id;
```

Query Profile shows 2.3 GB spilled at the join, with both
sides shuffling on `user_id`.

**The fix:** Pre-cluster both tables on the join key.

```sql
ALTER TABLE orders CLUSTER BY (user_id);
ALTER TABLE users CLUSTER BY (id, country);
```

After clustering, the join is local: each node's slice of
`orders` joins against the same node's slice of `users`. No
shuffle, no spill. Execution drops from 5 min to 30 s.

**The senior move:** "If the join key matches the cluster
key, the shuffle is free. I'd always check that the cluster
keys align before a large join."

---

## 10. The interview answer

> "Three algorithms: nested loop for a small outer with an
> indexed inner, hash join for a large equi-join, merge
> join when both sides are pre-sorted. The small/large
> heuristic: smaller table on the outer side, larger on
> the inner, with the inner indexed on the join key. In
> distributed engines, broadcast the small side or
> pre-cluster both sides on the join key to avoid
> shuffling. The three common bugs: joining on different
> types (kills the index), joining on a function
> (defeats the index), and using comma-join syntax
> (produces an implicit cross join). I'd fix the types,
> pre-compute the function, and rewrite as explicit
> `JOIN ... ON`."

That single paragraph covers: three algorithms, the
heuristic, the distributed case, and the three bugs.
Senior answer in 30 seconds.

---

## Try it

Pick a slow join. Run `EXPLAIN ANALYZE`. Check three things:
the join algorithm, the join key types, and whether the
join key is wrapped in a function. Fix any of the three.
Rerun. Watch the plan change.

*Author: Prem Vishnoi <prem.vishnoi@example.com>*
