# 41 — Index Strategy

> **Lesson 41 of 43 — Query Performance & Optimization**

The second lever after reading the plan: choosing the right
indexes. Most "slow query" tickets are solved by adding one
well-chosen index or dropping one bad one. The senior move is
knowing the five index types, knowing when each wins, and
knowing the two anti-patterns (index-everything and
low-cardinality-on-leading-column).

---

## 1. The five index types you must know

| Type | Best for | Pros | Cons |
|---|---|---|---|
| **B-tree** (default in Postgres / MySQL) | Range scans, equality, ORDER BY, `LIKE 'foo%'`. | General-purpose; supports `<`, `>`, `BETWEEN`, `IS NULL`. | Useless for `ILIKE '%foo%'` (leading wildcard). |
| **Hash** | Equality only (`=`). | Slightly smaller than B-tree. | No range scans; only equality. Postgres-only, rarely worth it. |
| **Bitmap** | Multiple predicates, low cardinality, read-only / analytical. | AND/OR multiple indexes cheaply. | Slow to update; not great for high-write OLTP. |
| **Partial** | Hot subset of rows (e.g., `WHERE status = 'pending'`). | 10-100x smaller than full index; faster. | Only one predicate; you must match the predicate exactly. |
| **Covering** (include columns) | Query reads only a few columns, all of which fit in the index. | Index-only scan; no heap touch. | Index size grows with included columns. |

Composite indexes (multi-column) are B-trees with multiple
sort keys. Their order is the entire game.

---

## 2. B-tree internals in 30 seconds

A B-tree is a balanced tree where every node is a sorted page
of keys with child pointers. Lookups are O(log n). Range
scans are O(log n + k) where k is the number of matching
rows. Inserts and deletes are O(log n) with occasional
splits.

The key implication: **a B-tree is sorted on its leading
column**. If the index is `(a, b)`, you can use it for
queries on `a`, on `a AND b`, but *not* on `b` alone.

```sql
CREATE INDEX idx_orders_user ON orders(user_id, created_at);

-- Can use the index:
SELECT * FROM orders WHERE user_id = 42;
SELECT * FROM orders WHERE user_id = 42 AND created_at > '2026-01-01';
SELECT * FROM orders ORDER BY user_id, created_at LIMIT 10;

-- CANNOT use the index (no leading-column predicate):
SELECT * FROM orders WHERE created_at > '2026-01-01';
```

---

## 3. Composite index column ordering

The single most-asked interview question in this module: "I
have a slow query that filters on `user_id` and `event_type`
and sorts by `ts`. What index do you add?"

The answer depends on the **cardinality** of each column and
the **query pattern**:

1. **Equality columns first**, in any order, highest
   selectivity first.
2. **Range column next**, in the exact order the query needs
   it sorted.
3. **Include covering columns** at the end (in `INCLUDE`).

| Query | Best index | Why |
|---|---|---|
| `WHERE a = 1 AND b = 2` | `(a, b)` or `(b, a)` | Both are equality; either works. |
| `WHERE a = 1 AND b > 5` | `(a, b)` | Equality first, range second. `(b, a)` can't seek on `a`. |
| `WHERE a = 1 ORDER BY b` | `(a, b)` | The index is already sorted on `(a, b)`. |
| `WHERE a = 1 GROUP BY b` | `(a, b)` | Same as above. |
| `WHERE a > 1 AND b = 5` | `(b, a)` | Range on leading column kills ordering; equality on `b` first lets it seek. |

**The rule of thumb:** "Equality, then range, then sort, then
include."

---

## 4. The "index everything" anti-pattern

The mistake: adding an index to every column that appears in
a `WHERE` clause.

```sql
-- BAD
CREATE INDEX idx_a ON t(a);
CREATE INDEX idx_b ON t(b);
CREATE INDEX idx_c ON t(c);
CREATE INDEX idx_d ON t(d);
```

Why it's bad:

- **Write amplification.** Every `INSERT` updates every
  index. Five indexes on a hot table can double write
  throughput requirements.
- **Cache pressure.** Indexes live in the buffer pool (or
  `shared_buffers` in Postgres). Too many indexes means
  the working set doesn't fit and the cache thrashes.
- **Planner confusion.** Postgres can pick a worse index
  because it has too many choices.

**The senior move:** "I'd start with no indexes and add them
based on actual slow queries, not anticipated ones. Every
index is a write-time cost I'm buying for a read-time
benefit. I'd want a workload-driven reason."

---

## 5. The "filter by low-cardinality column" mistake

The mistake: putting a low-cardinality column first in a
composite index.

```sql
-- 99% of rows have status = 'paid'. Index leads with status.
CREATE INDEX idx_orders_status_user ON orders(status, user_id);

-- Query: WHERE user_id = 42
-- This CANNOT use the index efficiently. The index is sorted
-- by status, so to find user_id = 42 the engine scans
-- almost the entire index.
```

**Why it's bad:** A B-tree on a column with N distinct values
splits the data into N sorted groups. If N=2 and the values
are 99%/1%, the engine has to scan ~50% of the index to find
the matching group. You might as well seq scan.

**The fix:** Put the high-cardinality column first.

```sql
-- Good: high-cardinality first
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
```

**The exception — partial indexes:** A low-cardinality column
*as the predicate* of a partial index is great:

```sql
-- The 1% of unpaid orders — small, fast index.
CREATE INDEX idx_orders_unpaid ON orders(user_id)
  WHERE status IN ('pending', 'failed');
```

---

## 6. When to drop an index

The senior move: "An unused index is worse than no index at
all. I'd drop indexes that no query is using."

In Postgres:

```sql
SELECT schemaname, relname, indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

`idx_scan = 0` for a long time = safe to drop. The senior
move: name this query unprompted.

Other reasons to drop an index:

- **It's been replaced** by a better composite.
- **It's on a column that's no longer queried** (e.g., after
  a schema change).
- **It's a duplicate** with a different name (common after
  migrations).
- **The table is write-heavy and the index is rarely read** —
  the cost outweighs the benefit.

---

## 7. Covering indexes (the index-only scan trick)

A *covering* index includes all the columns the query
needs, so the engine can answer the query from the index
alone without touching the heap.

```sql
-- Query
SELECT user_id, status, created_at
FROM orders
WHERE user_id = 42;

-- Covering index — includes created_at so the heap isn't touched
CREATE INDEX idx_orders_user_covering
  ON orders(user_id) INCLUDE (status, created_at);
```

The plan goes from `Index Scan` (index walk + heap fetch per
row) to `Index Only Scan` (no heap touch). On a wide table
this is a 5-10x speedup.

**The senior move:** "For a hot query that reads a few
columns, I'd add a covering index with the leading equality
column and the rest in `INCLUDE`."

---

## 8. Worked example — events table

Setup: a slow query on `events(user_id, event_type, ts)`.

```sql
-- The slow query
SELECT user_id, event_type, COUNT(*)
FROM events
WHERE user_id IN (1, 2, 3, 4, 5)
  AND event_type = 'click'
  AND ts >= NOW() - INTERVAL '7 days'
GROUP BY user_id, event_type;
```

**Option A: equality + range, no covering.**

```sql
CREATE INDEX idx_events_user_type_ts
  ON events(user_id, event_type, ts);
```

Good if you also need to `ORDER BY ts` or fetch other
columns. The leading columns are equality (`user_id IN` is
treated as 5 equality lookups), then `event_type` is also
equality, then `ts` is range.

**Option B: partial + covering.**

```sql
CREATE INDEX idx_events_recent_clicks
  ON events(user_id)
  INCLUDE (event_type, ts)
  WHERE event_type = 'click' AND ts >= NOW() - INTERVAL '30 days';
```

Tighter, smaller, faster — but only useful for the 30-day
window. The 7-day query re-validates the predicate and uses
the index. After 30 days the partial index has no rows and
stops being useful; you'd need to refresh or rebuild.

**Option C: separate indexes + bitmap scan.**

```sql
CREATE INDEX idx_events_user ON events(user_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_ts ON events(ts);
```

Postgres combines them with a BitmapAnd. Useful if you have
many queries with different filter combinations; bad if you
have one hot query (single composite is faster).

**Tradeoff summary:**

| Option | Best when | Cost |
|---|---|---|
| A: composite | Single hot query pattern; need ORDER BY. | Writes pay 3-key index update. |
| B: partial + covering | Read-mostly table; bounded time window. | Becomes useless past 30 days. |
| C: separate + bitmap | Many ad-hoc filter combos. | Slow per-query vs composite. |

The senior answer: "I'd start with A, monitor with
`pg_stat_user_indexes`, and only switch to B if A's write
amplification is a problem."

---

## 9. Indexing for ORDER BY and GROUP BY

The under-appreciated win: an index on `(a, b)` lets Postgres
*skip* the sort if the query has `ORDER BY a, b`.

```sql
CREATE INDEX idx_orders_user_created
  ON orders(user_id, created_at);

-- The plan: Index Scan, no Sort node.
SELECT * FROM orders
WHERE user_id = 42
ORDER BY created_at DESC
LIMIT 10;
```

The plan shows `Index Scan` walking the index in reverse
order. No sort, no temp file, no `work_mem` pressure.

**The senior move:** "When the query has both a `WHERE` and
an `ORDER BY`, the index should match the order in the
query — equality columns first, then the sort columns."

---

## 10. The interview answer

> "I'd start with the actual slow query and the actual
> `EXPLAIN ANALYZE` plan. The fix is usually one of three
> things: a missing composite index on the equality +
> range columns, a covering index with `INCLUDE` to make
> the query an index-only scan, or a partial index on the
> hot subset of rows. I'd avoid the two anti-patterns:
> adding an index to every column, and leading with a
> low-cardinality column. I'd also drop indexes that no
> query is using — every index is a write-time cost I'm
> buying for a read-time benefit. After adding the index
> I'd rerun `EXPLAIN ANALYZE` and confirm the new plan
> uses it."

That single paragraph covers: the read-first approach, the
three index patterns, the two anti-patterns, the drop rule,
and the verification loop. Senior answer in 30 seconds.

---

## Try it

Pick your slowest query. Find the `WHERE` and `ORDER BY`
columns. Apply the rule: equality, then range, then sort,
then include. Add the index. Rerun `EXPLAIN ANALYZE`. Watch
the operator change from `Seq Scan` to `Index Scan` or
`Index Only Scan`. That's the win.

*Author: Prem Vishnoi <pvishnoi@avilx.com>*
