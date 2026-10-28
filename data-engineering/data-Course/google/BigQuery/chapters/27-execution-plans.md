# 4.1 — How BigQuery Creates an Execution Plan

> **Section 4 · Query Execution Plan · Lectures 4.1–4.2 · 8:10 + 5:50**

## 🎯 What you will learn

- The six phases from SQL text to executed plan
- How the optimizer rewrites your query
- Pushdown, join reordering, and why they matter
- What "shuffle" means and how to spot it in the plan

---

## 🧠 Concept

BigQuery does not execute your SQL literally. A **query optimizer** rewrites it into a physical
execution plan that is usually quite different from what you wrote. Understanding the rewrite is
what lets you predict cost.

### The six phases

```
 SQL text
   │
   ▼
┌────────────────────────────────────────────────────────────┐
│ 1. PARSE & BIND                                            │
│    SQL → AST; resolve table/column names against catalog  │
│    Output: logical plan                                    │
└──────────────────────┬─────────────────────────────────────┘
                       ▼
┌────────────────────────────────────────────────────────────┐
│ 2. LOGICAL OPTIMIZATION                                    │
│    • Rewrite predicates into canonical form                │
│    • Resolve views and CTEs                                │
│    • Apply policy tags / RLS filters                      │
│    Output: optimized logical plan                          │
└──────────────────────┬─────────────────────────────────────┘
                       ▼
┌────────────────────────────────────────────────────────────┐
│ 3. PHYSICAL PLANNING                                       │
│    • Choose join algorithms (hash, broadcast, merge)       │
│    • Choose scan strategies (partition/cluster pruning)    │
│    • Assign operators to stages                            │
│    Output: stage DAG                                       │
└──────────────────────┬─────────────────────────────────────┘
                       ▼
┌────────────────────────────────────────────────────────────┐
│ 4. SCHEDULING                                             │
│    • Reserve slots                                         │
│    • Wait for capacity                                     │
│    Output: slot allocation                                 │
└──────────────────────┬─────────────────────────────────────┘
                       ▼
┌────────────────────────────────────────────────────────────┐
│ 5. EXECUTION                                              │
│    • Stages run in dependency order                        │
│    • Each stage uses N slots with M parallel tasks         │
│    • Shuffles between stages                               │
└──────────────────────┬─────────────────────────────────────┘
                       ▼
┌────────────────────────────────────────────────────────────┐
│ 6. RESULT MATERIALIZATION                                  │
│    • Write to destination table or stream to client        │
└────────────────────────────────────────────────────────────┘
```

---

## 🧠 Logical optimization — the rewrites that change your bill

### Predicate pushdown

The single most important rewrite. A filter placed as early as possible eliminates data before it
is read or moved.

```sql
-- You wrote this
SELECT customer_id, SUM(total_amount)
FROM orders
JOIN customers USING (customer_id)
WHERE order_date >= '2026-01-01'
GROUP BY customer_id;

-- It becomes this internally
SELECT customer_id, SUM(total_amount)
FROM (SELECT * FROM orders WHERE order_date >= '2026-01-01')  -- pushed into the scan
JOIN customers USING (customer_id)
GROUP BY customer_id;
```

💡 **The pushdown filter reaches the scan stage**, where it triggers **partition pruning** and
**block pruning**. This is why adding a partition filter to a query can cut its cost by 100×.

### Column pruning

```sql
-- You wrote this
SELECT * FROM orders WHERE order_date >= '2026-01-01';

-- It becomes this
SELECT order_id, customer_id, order_date, total_amount, status  -- only what you need
FROM orders WHERE order_date >= '2026-01-01';
```

The optimizer tracks which columns are actually referenced and never fetches the others.

### Join reordering

```sql
-- You wrote this
SELECT * FROM a JOIN b ON a.id = b.id JOIN c ON b.id = c.id;

-- The optimizer reorders to minimize the shuffle:
SELECT * FROM a JOIN c ON a.id = c.id JOIN b ON b.id = c.id;
```

BigQuery picks the join order that minimizes the amount of data shuffled. It may also convert a
`LEFT JOIN` to an `INNER JOIN` when a `WHERE` clause on the right table's columns makes the outer
rows impossible.

### Aggregation optimization

BigQuery rewrites `GROUP BY` into a **two-phase aggregation**:

```
Phase 1 (parallel, per worker):  partial GROUP BY → many small groups
Phase 2 (shuffle + merge):        merge partial groups → final groups
```

This is why a high-cardinality `GROUP BY` is expensive — the shuffle has to move millions of
partial groups.

### Constant folding and predicate simplification

```sql
WHERE 1=1                    -- removed
WHERE order_date > '2026-01-01' AND '2026-01-01' < '2026-06-01'
     -- simplified to a range, which prunes partitions better
```

💡 **A `BETWEEN` on a partition column prunes better than two `>=`/`<=` predicates**, because the
optimizer can turn it into a contiguous partition range.

---

## 🧠 Physical planning — join algorithms

| Algorithm | When the optimizer picks it | Shuffle? |
|-----------|---------------------------|----------|
| **Hash join** (default) | Larger tables, `=` join keys | Yes — both sides |
| **Broadcast hash join** | One side is small (< ~10 MB) | No — small side copied to all workers |
| **Merge join** | Both sides sorted on the join key | Yes, but sorted |

💡 **Broadcast joins are the cheapest joins.** If one side of your join is small enough to fit in
memory, BigQuery replicates it to every worker instead of shuffling both sides. Making a lookup
table small and pre-aggregating is often the highest-leverage optimization available.

### How to encourage a broadcast join

```sql
-- Pre-aggregate the large side down to a small lookup
WITH small_dim AS (
    SELECT customer_id, customer_name, segment
    FROM `YOUR_PROJECT_ID.curated.customers`
    WHERE segment = 'enterprise'      -- small result set
)
SELECT ...
FROM `YOUR_PROJECT_ID.curated.orders` o
JOIN small_dim USING (customer_id);
```

---

## 🧠 Shuffles

A **shuffle** is a data movement between stages. Shuffles are where the money goes.

```
Stage 1: Scan           [2 TB in]  →  [1.8 TB out]
                ⬇ SHUFFLE (network transfer, hash-partitioned)
Stage 2: Join           [1.8 TB in] →  [1.2 TB out]
                ⬇ SHUFFLE
Stage 3: Aggregate      [1.2 TB in] →  [50 MB out]
```

### What causes a shuffle

| Operation | Shuffle? |
|-----------|----------|
| `JOIN` on a large table | ✅ Yes — both sides hash-partitioned on the join key |
| `GROUP BY` | ✅ Yes — partial aggregates must be merged |
| `DISTINCT` | ✅ Yes — must be deduplicated globally |
| `ORDER BY` | ✅ Yes — global sort |
| `UNION ALL` | ✅ Yes — rows are redistributed |
| `WHERE` filter | ❌ No — stays in the scan stage |
| `SELECT` projection | ❌ No |
| `LIMIT` | ❌ No (usually) |

💡 **Rule of thumb: if the operation needs to see all rows together, it shuffles.** Filters and
projections do not.

### Reducing shuffles

1. **Pre-aggregate before joining** — aggregate the big side first
2. **Cluster on the join key** — reduces the data that must be shuffled
3. **Broadcast a small side** — avoid a shuffle entirely
4. **Avoid `ORDER BY` on large results** — sort only the final, small output
5. **Replace `UNION ALL` of many tables with a single partitioned table**

---

## 🛠️ Hands-On: Read a Real Execution Plan

### 1. Get the plan via dry run

```bash
bq query --dry_run --use_legacy_sql=false '
  SELECT
    c.region,
    COUNT(*) AS orders,
    SUM(o.total_amount) AS revenue
  FROM `YOUR_PROJECT_ID.curated.orders` o
  JOIN `YOUR_PROJECT_ID.curated.customers` c USING (customer_id)
  WHERE o.order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  GROUP BY c.region'
```

### 2. Read the plan in the console

Go to **Query plan → GRAPH**. You will see the stage DAG. For each stage, note:

- **Input bytes** and **output bytes**
- **Rows in / rows out**
- **Wait time vs active time** — wait time means slot contention

### 3. Find the shuffle

```sql
-- ❌ Expensive: shuffle + broadcast check
SELECT
    c.region,
    COUNT(*) AS orders,
    SUM(o.total_amount) AS revenue
FROM `YOUR_PROJECT_ID.curated.orders` o
JOIN `YOUR_PROJECT_ID.curated.customers` c USING (customer_id)
WHERE o.order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY c.region;
```

```sql
-- ✅ Optimized: pre-aggregate, then join a small table
WITH order_totals AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(total_amount) AS revenue
    FROM `YOUR_PROJECT_ID.curated.orders`
    WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    GROUP BY customer_id
)
SELECT
    c.region,
    SUM(t.order_count) AS orders,
    SUM(t.revenue) AS revenue
FROM order_totals t
JOIN `YOUR_PROJECT_ID.curated.customers` c USING (customer_id)
GROUP BY c.region;
```

### 4. Measure the difference

```sql
SELECT
    job_id,
    ROUND((total_bytes_processed / POW(1024, 4)) * 6.25, 4) AS est_cost_usd,
    ROUND(total_slot_ms / 1000, 2) AS slot_seconds,
    ROUND((total_bytes_billed / POW(1024, 3)), 2) AS mb_billed
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE job_type = 'QUERY'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY creation_time DESC;
```

### 5. Watch slot contention

```sql
-- Is the project running out of slots?
SELECT
    ROUND(SUM(total_slot_ms) / 1000 / 3600, 2) AS slot_hours_24h,
    COUNT(*) AS job_count,
    COUNTIF(state = 'ERROR') AS failed_jobs,
    COUNTIF(error_result.reason = 'resourcesExceeded') AS quota_failures
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY job_type;
```

---

## 💡 Production Notes

- **`SELECT *` prevents column pruning** because the optimizer cannot know what you will use
  downstream of a `UNION` or a view.
- **A `WHERE` on a joined table's columns converts `LEFT JOIN` to `INNER JOIN`** — sometimes
  silently changing your result semantics. Check the plan when row counts surprise you.
- **`ORDER BY` on a large result is a full sort.** Sort the final aggregated output, never the
  raw scan.
- **Long "wait time" on stage 1 means slot exhaustion**, not a bad query. Buy capacity.
- **`DISTINCT` is a shuffle.** `SELECT DISTINCT` on a large table is expensive; consider
  `GROUP BY` with a pre-aggregated input, or a different data model.

---

## 🔑 Key Takeaways

- Six phases: parse → logical optimize → physical plan → schedule → execute → materialize.
- **Predicate pushdown** is the rewrite that matters most — it enables partition and block pruning.
- The optimizer also does column pruning, join reordering, aggregation rewriting, and predicate
  simplification.
- **A shuffle happens whenever an operation must see all rows together** — joins, `GROUP BY`,
  `DISTINCT`, `ORDER BY`, `UNION ALL`.
- **Broadcast joins** (small side) avoid a shuffle entirely — pre-aggregate to enable them.
- Distinguish **wait time** (capacity problem) from **active time** (query problem).

---

## 📚 Practice Exercises

1. **Plan analysis.** Write a query with 3 joins and a `GROUP BY`. Predict the stage DAG, identify
   every shuffle, and explain which stage dominates. Then verify against the console.

2. **Rewrite drill.** Rewrite each query to reduce shuffles:
   - `SELECT DISTINCT customer_id FROM orders`
   - `SELECT * FROM big_a UNION ALL SELECT * FROM big_b`
   - `SELECT c.name FROM customers c JOIN orders o USING (customer_id) ORDER BY o.total_amount`
   Explain what you changed and why.

3. **Broadcast join.** Design a schema and query that guarantees a broadcast join for a
   100 TB fact table. Measure the actual bytes processed with and without the optimization.

4. **Wait vs active.** Find 10 queries in the last week with the highest wait-to-active ratio.
   What do they tell you about your project's capacity configuration?

5. **Optimizer trap.** Construct a query where `LEFT JOIN` is silently converted to `INNER JOIN`
   by a `WHERE` predicate. Demonstrate the row-count difference.

---

## 📖 Further Reading

- Query execution plans — https://cloud.google.com/bigquery/docs/query-plan
- Query optimizer — https://cloud.google.com/bigquery/docs/query-optimization
- BigQuery best practices — https://cloud.google.com/bigquery/docs/best-practices
