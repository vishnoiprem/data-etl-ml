# 40 — Reading EXPLAIN / EXPLAIN ANALYZE Plans

> **Lesson 40 of 43 — Query Performance & Optimization**

Every SQL performance question starts the same way: someone says
"this query is slow," and you say "let me see the plan." The
interviewer will judge you on whether you can read the plan,
name the operators, spot the red flags, and propose a fix. This
lesson is the first half of that.

---

## 1. The two commands

```sql
-- The plan only (no execution)
EXPLAIN SELECT ...;

-- The plan AND actual runtime statistics
EXPLAIN ANALYZE SELECT ...;
```

`EXPLAIN` is safe to run anywhere — it doesn't execute the
query. `EXPLAIN ANALYZE` *does* execute it, so never run it
against a write statement (`INSERT`, `UPDATE`, `DELETE`)
without wrapping in a transaction you can roll back. The
interviewer's trap question: "Is EXPLAIN ANALYZE safe on a
DELETE?" Answer: "No — it executes the DELETE. I'd wrap in
`BEGIN; EXPLAIN ANALYZE ...; ROLLBACK;`."

---

## 2. The plan tree

The output of `EXPLAIN` is a tree of *operators*. Each row is
one node. The rightmost indent is the leaf (the scan), and
each level above is a parent (the join, the aggregate, the
sort). Read the plan **bottom-up, right-to-left**: start at
the leaves (where the rows come from) and walk up to the root
(where the result is produced).

```
Limit  (cost=... rows=10)
  ->  Sort  (cost=... rows=1000)
        Sort Key: order_date DESC
        ->  Hash Join  (cost=... rows=1000)
              Hash Cond: (o.user_id = u.id)
              ->  Seq Scan on orders o  (cost=... rows=1000000)
              ->  Hash  (cost=... rows=50000)
                    ->  Seq Scan on users u  (cost=... rows=50000)
```

Read this as: "We scanned all 1M orders and all 50K users into
hash tables, joined them, sorted by date, and limited to 10.
The big cost is the two sequential scans."

---

## 3. The operators you must know

| Operator | What it does | When the optimizer picks it |
|---|---|---|
| **Seq Scan** | Reads every row in the table, top to bottom. | Small tables, no useful index, low selectivity filter. |
| **Index Scan** | Walks the index in order, then fetches matching rows from the heap. | Selective filter on an indexed column. |
| **Index Only Scan** | Walks the index and answers the query without touching the heap. | All needed columns are in the index (covering). |
| **Bitmap Index Scan** | Builds an in-memory bitmap of pages matching each predicate, ANDs/ORs them, then fetches. | Multiple indexed predicates, moderate selectivity. |
| **Hash Join** | Builds a hash table on the smaller side, probes with the larger side. | Equi-joins with no useful sort order. |
| **Nested Loop** | For each row in the outer, scan the inner. | Small outer, indexed inner. |
| **Merge Join** | Both sides sorted on the join key, walk in parallel. | Both inputs already sorted, or with an index on the join key. |
| **Sort** | Sort the input. | ORDER BY, GROUP BY (sometimes), merge join input. |
| **Aggregate** | Hash-based or sort-based grouping. | GROUP BY, DISTINCT. |
| **Materialize** | Cache a subquery to disk/memory. | Subquery reused multiple times. |
| **Gather / Gather Merge** | Merge results from parallel workers. | Parallel query. |

The senior move: name these unprompted and explain when each
wins. "Hash join is best for large equi-joins; nested loop is
best for a small outer with an indexed inner; merge join is
best when both sides are pre-sorted."

---

## 4. The five red flags

A plan with any of these is a slow query. Spot them in
interviews and you've answered half the question.

| Red flag | What it means | The fix |
|---|---|---|
| **Seq Scan on a large table** | Postgres gave up on the index. | Add or fix the index; check the predicate is sargable. |
| **Nested Loop with many rows** | Wrong join algorithm for the cardinality. | Encourage hash join with `SET enable_nestloop = off` to confirm; or rewrite. |
| **Sort spilling to disk** | `work_mem` too small. | Increase `work_mem` for the session, or remove the sort. |
| **Hash table spilling to disk** | `work_mem` too small for the build side. | Increase `work_mem` or reduce the build side (filter earlier). |
| **Missing index on a join key** | Hash join on unindexed columns. | Add an index on the join key on at least the inner side. |

Bonus red flag: a row count estimate that is wildly off. If
the planner thinks the join produces 10 rows and it actually
produces 10M, every cost number above it is wrong. Run
`ANALYZE` to refresh statistics.

---

## 5. Reading a Postgres plan — worked example #1

```sql
SELECT u.email, COUNT(o.id) AS orders
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE u.signup_date >= '2026-01-01'
  AND o.status = 'paid'
GROUP BY u.email
ORDER BY orders DESC
LIMIT 10;
```

```
Limit  (cost=4250.31..4250.33 rows=10 width=39) (actual time=182.034..182.036 rows=10 loops=1)
  ->  Sort  (cost=4250.31..4250.34 rows=12 width=39) (actual time=182.033..182.034 rows=10 loops=1)
        Sort Key: (count(o.id)) DESC
        Sort Method: top-N heapsort  Memory: 25kB
        ->  HashAggregate  (cost=4249.99..4250.12 rows=12 width=39) (actual time=181.928..181.991 rows=20 loops=1)
              Group Key: u.email
              ->  Hash Join  (cost=1245.00..4100.00 rows=30000 width=31) (actual time=12.345..178.456 rows=28654 loops=1)
                    Hash Cond: (o.user_id = u.id)
                    ->  Seq Scan on orders o  (cost=0.00..2500.00 rows=200000 width=8) (actual time=0.012..45.123 rows=199876 loops=1)
                          Filter: (status = 'paid'::text)
                          Rows Removed by Filter: 800124
                    ->  Hash  (cost=1100.00..1100.00 rows=11600 width=31) (actual time=11.987..11.987 rows=11500 loops=1)
                          Buckets: 16384  Batches: 1  Memory Usage: 700kB
                          ->  Seq Scan on users u  (cost=0.00..1100.00 rows=11600 width=31) (actual time=0.008..8.456 rows=11500 loops=1)
                                Filter: (signup_date >= '2026-01-01'::date)
                                Rows Removed by Filter: 38500
Planning Time: 1.234 ms
Execution Time: 182.123 ms
```

**Reading it:** Two sequential scans (orders and users), hash
join on `user_id`, hash aggregate by `email`, top-N sort. The
bulk of the time is the `orders` seq scan — 200K rows scanned
to find 200K paid orders. That's 100% selectivity, so the
filter isn't helping.

**The fix:** Add a partial index on the paid subset:

```sql
CREATE INDEX idx_orders_paid_user
  ON orders(user_id) WHERE status = 'paid';
```

Now the hash join can probe the index instead of scanning all
1M rows. The plan would show `Index Scan` on the orders side
and execution time would drop to single-digit ms.

---

## 6. Reading a MySQL plan — worked example #2

MySQL's `EXPLAIN` is a table, not a tree. Read the columns
left-to-right, top-to-bottom:

```sql
EXPLAIN SELECT u.email, COUNT(o.id)
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE o.status = 'paid'
GROUP BY u.email;
```

| id | select_type | table | type | possible_keys | key | rows | Extra |
|---|---|---|---|---|---|---|---|
| 1 | SIMPLE | o | ALL | NULL | NULL | 1000000 | Using where; Using temporary; Using filesort |
| 1 | SIMPLE | u | eq_ref | PRIMARY | PRIMARY | 1 | NULL |

**Reading it:** `type=ALL` on `o` is a full table scan — red
flag #1. `Using filesort` and `Using temporary` are
MySQL-speak for sort spilling — red flag #3. The fix: add an
index on `orders(user_id, status)` so MySQL can use it for
both the join and the filter.

For more detail, use `EXPLAIN FORMAT=JSON` or `EXPLAIN
ANALYZE` (MySQL 8.0+). JSON output gives the same cost /
row-estimate picture as Postgres.

---

## 7. Reading a Snowflake plan — worked example #3

Snowflake's plan is a DAG in the *Query Profile* UI. Each
node is an operator; the arrows are data flow. The columns
that matter: **% of total time**, **rows produced**, **bytes
spilled to remote storage**.

```
[SEQ: orders]   ->  [JOIN: hash]  ->  [AGG: hash]  ->  [SORT]  ->  [RESULT]
[SEQ: users]    -/
```

If the `JOIN: hash` node shows `Bytes spilled: 2.3 GB`,
that's a partition-pruning or filter-pushdown problem. If the
`SEQ: orders` node shows `Partitions scanned: 1024 /
scanned: 1024`, no pruning happened.

**The fix:** Add a clustering key (`CLUSTER BY (user_id)`)
and filter on it; or push the date filter into the source
query so only relevant micro-partitions are scanned.

---

## 8. Reading a BigQuery plan — worked example #4

BigQuery returns a JSON plan via `bq query --explain`. The
top-level stages are read from the leaves up:

```json
{
  "queryId": "abc123",
  "stages": [
    {"name": "S00: Scan users",  "recordsRead": 50000,   "bytesRead": "5 MB"},
    {"name": "S01: Scan orders", "recordsRead": 1000000, "bytesRead": "200 MB"},
    {"name": "S02: Join",        "recordsRead": 1000000, "joinType": "HASH"},
    {"name": "S03: Aggregate",   "recordsRead": 50000},
    {"name": "S04: Sort + Limit","recordsRead": 10}
  ]
}
```

The big number is `S01: 200 MB`. BigQuery charges by bytes
scanned. If you only need paid orders, partition by `status`
or add a `_PARTITIONTIME` filter to cut bytes by 5-10x.

---

## 9. The "estimated vs actual" check

Every Postgres `EXPLAIN ANALYZE` line has two numbers:
`rows=1000` (estimated) and `actual rows=10000` (measured).
If the ratio is 10x or more, the planner is making decisions
on bad data. Run `ANALYZE table_name` to refresh
statistics, or `ALTER TABLE ... SET STATISTICS 1000` for a
specific column.

**Interview red flag:** "I see a `Hash Join` with estimated
100 rows but actual 10 million. What's going on?" Answer: the
planner chose hash join because it thought the build side was
small. With 10M rows, hash join is fine, but the choice
should have been re-evaluated. Either way, `ANALYZE` first.

---

## 10. The interview answer

> "First I'd run `EXPLAIN ANALYZE` to see the plan and the
> actual row counts. I'm looking for five red flags: a
> sequential scan on a large table, a nested loop with many
> rows, a sort or hash table spilling to disk, a join key
> without an index, and a row count estimate that's wildly
> off. Once I see the bottleneck — usually one of those five —
> I fix it with the corresponding lever: add the missing
> index, rewrite the join order, increase `work_mem`, or push
> the filter down. After the fix I rerun `EXPLAIN ANALYZE`
> and confirm the new plan is doing what I expected."

That single paragraph covers: how to read plans, the five red
flags, the four fixes, the verification loop. Senior answer
in 30 seconds.

---

## Try it

Pick any query you've written recently. Run `EXPLAIN
ANALYZE` against it. Identify the slowest node. Find a red
flag. Propose a fix. Apply it. Rerun. That's the loop — and
it's the answer to "this query is slow, how do you fix it?"

*Author: Prem Vishnoi <prem.vishnoi@example.com>*
