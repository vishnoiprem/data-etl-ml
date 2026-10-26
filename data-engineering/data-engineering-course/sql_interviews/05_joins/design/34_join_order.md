# Lesson 34 — Join Order and the Optimizer

> **Goal:** know what the query engine is allowed to
> reorder, and what it must preserve.

---

## The rules of reorderability

A SQL optimizer is free to reorder joins **as long as the
result is the same**. Different join types have different
rules.

| Join | Reorderable? |
|---|---|
| `INNER JOIN` | Yes, mostly. The engine can pick any join order. |
| `LEFT OUTER JOIN` | Limited. Must preserve left-to-right dependencies. |
| `RIGHT OUTER JOIN` | Limited. Must preserve right-to-left dependencies. |
| `FULL OUTER JOIN` | Not reorderable in general. |
| `CROSS JOIN` | Yes, but rarely reorders. |

The reason: INNER JOIN is *associative* and *commutative*:
`(A INNER JOIN B) INNER JOIN C` is the same as `A INNER
JOIN (B INNER JOIN C)` is the same as `A INNER JOIN C
INNER JOIN B`. OUTER JOINs don't have these properties (in
general), so the engine can't freely reorder them.

---

## What the optimizer does

Given a query with N tables, the engine must pick:

1. **Join order.** Which two tables to join first, then
   which, etc. The number of possible orderings is N! — for
   N=10, that's 3.6 million. The optimizer uses dynamic
   programming to find a good order in a few milliseconds.
2. **Join algorithm.** For each pair, nested-loop, hash, or
   merge join. Each has trade-offs.
3. **Index usage.** For each predicate, use an index or
   scan the table.

You can see the choices in the `EXPLAIN` output. SQLite:
`EXPLAIN QUERY PLAN`. PostgreSQL: `EXPLAIN (ANALYZE, BUFFERS)`.

---

## How to read an EXPLAIN plan

A simplified example:

```
SCAN TABLE Orders
SEARCH TABLE Customer USING INDEX idx_customer_id (id=?)
```

Reading: "Scan the Orders table. For each row, look up the
matching Customer using the index on `id`." This is a
nested-loop join with Orders as the outer.

Cost: the optimizer assigns a cost to each operation. The
total cost of the plan is the sum. You want the lowest-cost
plan. SQLite's `EXPLAIN QUERY PLAN` shows the chosen
strategy.

```sql
EXPLAIN QUERY PLAN
SELECT o.id, c.name
FROM   Orders o
JOIN   Customer c ON c.id = o.customer_id;
```

Look for:
- `SCAN TABLE` — full table scan (often bad for large
  tables; sometimes unavoidable).
- `SEARCH TABLE ... USING INDEX` — index lookup (usually
  good).
- `USE TEMP B-TREE FOR ORDER BY` — sort happens in memory
  (fine for small, bad for large).
- `USE TEMP B-TREE FOR GROUP BY` — hash aggregate (good).

---

## When the optimizer gets it wrong

1. **Stale statistics.** If the table has grown 10x since
   the last `ANALYZE`, the optimizer may pick a bad plan.
   Run `ANALYZE` periodically (PostgreSQL: `VACUUM ANALYZE`).
2. **Wrong indexes.** Missing index on the join column. Add
   one.
3. **Functions on indexed columns.** `WHERE DATE(order_date)
   = ...` prevents the engine from using the index on
   `order_date`. Rewrite as `WHERE order_date >= ... AND
   order_date < ...`.
4. **OR across columns.** `WHERE a = 1 OR b = 2` is hard
   for the optimizer. Use `UNION` of two `WHERE`s:

   ```sql
   SELECT * FROM t WHERE a = 1
   UNION ALL
   SELECT * FROM t WHERE b = 2;
   ```

5. **Implicit type casts.** `WHERE id = '123'` (string) when
   `id` is an integer forces a cast. Index may be unusable.
   Match types exactly.

---

## How to influence the optimizer

### 1. Add the right indexes

The single biggest win. Index every column you filter or
join on, in the order you use it.

```sql
CREATE INDEX idx_orders_customer ON Orders(customer_id);
```

Composite index for multi-column predicates:

```sql
CREATE INDEX idx_orders_status_date ON Orders(status, order_date);
```

### 2. Use the right join order

You can't directly tell the optimizer what to do, but you
can hint it with CTEs. Materializing a subquery first via
a CTE tells the engine "compute this once, then join to it":

```sql
WITH filtered_orders AS (
  SELECT * FROM Orders WHERE order_date >= '2024-01-01'
)
SELECT *
FROM   filtered_orders o
JOIN   Customer c ON c.id = o.customer_id;
```

(Some engines inline CTEs by default. PostgreSQL 12+ does
inline by default. To force materialization in PostgreSQL,
use `WITH ... AS MATERIALIZED`.)

### 3. Use the right join type

If you don't need unmatched rows, use INNER JOIN. The
optimizer has more freedom with INNER JOINs and usually
picks a better plan.

### 4. Avoid `SELECT *`

It can prevent the optimizer from using an index-only scan
(where the engine reads only the index, not the table).

---

## Interview expectations

For data engineering interviews, you should:

1. Know what `EXPLAIN` is and what it shows.
2. Recognize `SCAN` (bad) vs `SEARCH USING INDEX` (good).
3. Know that JOINs can be reordered and the engine picks
   the order.
4. Know that LEFT JOIN can't be reordered past a downstream
   filter.

You don't need to be a query-tuning expert. That's a
specialty; you're expected to recognize obvious problems
("why is this slow?") and propose fixes ("add an index",
"rewrite the WHERE", "materialize as a CTE").

---

## Try it

For a query joining `Orders` (1M rows) and `Customer` (10K
rows):

1. Predict which side the engine will choose as the outer
   of the nested loop. (Hint: smaller side as inner.)
2. Run `EXPLAIN QUERY PLAN` and check.
3. Add an index on `Orders.customer_id` and re-run
   `EXPLAIN`. Does the plan change?
