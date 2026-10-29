# Lesson 3 — AI Query Optimization

> **Type:** Article · Module 2 · AI for SQL & Analytics
> Using AI as a reading assistant for EXPLAIN plans, query profiles, and cluster configs.

---

## The role of AI in query optimisation

Query optimisation is **80% pattern recognition** (you've seen this anti-pattern 100 times) and **20% measurement** (this specific dataset, this specific cluster). AI is great at the first and blind to the second.

```
   ┌──────────────────────────────────────────────────────────┐
   │  WHERE AI HELPS IN QUERY OPTIMISATION                    │
   │                                                          │
   │   ✅ Reading EXPLAIN plans, naming the anti-pattern       │
   │   ✅ Suggesting common fixes (predicate pushdown,         │
   │      join reordering, partition pruning)                  │
   │   ✅ Generating "what changed" diffs between plans       │
   │   ✅ Hypothesis generation for slow queries               │
   │                                                          │
   │   ❌ Knowing whether a fix is actually faster             │
   │   ❌ Estimating cost on your specific cluster             │
   │   ❌ Optimising without data distribution context        │
   └──────────────────────────────────────────────────────────┘
```

**The rule:** AI hypothesises, you measure. AI proposes fixes, you EXPLAIN ANALYZE before and after.

---

## The workflow

```
   slow query
       │
       ▼
   ┌────────────┐
   │  EXPLAIN   │  (or Snowflake QUERY HISTORY, BigQuery plan)
   │  ANALYZE   │
   └─────┬──────┘
         ▼
   ┌────────────┐     paste plan + table stats
   │  AI reads  │──────────────────────────────┐
   │  the plan  │                              │
   └─────┬──────┘                              │
         ▼                                     │
   ┌────────────┐                              │
   │  AI names  │  "data skew on user_id,      │
   │  the cause │   partition pruning missed,  │◄──── AI does this
   │            │   broadcast join too large"  │
   └─────┬──────┘                              │
         ▼                                     │
   ┌────────────┐                              │
   │  AI proposes│ "skew hint, filter before   │
   │  2-3 fixes  │  join, repartition"         │◄──── AI does this
   └─────┬──────┘                              │
         ▼                                     │
   ┌────────────┐                              │
   │  YOU apply │ measure before/after         │
   │  & measure │ keep what works              │◄──── YOU do this
   └────────────┘                              │
```

---

## The 10 most common SQL anti-patterns (AI recognises these)

1. **SELECT \*** — pulls columns you don't need, breaks partition pruning
2. **Functions on filtered columns** — `WHERE DATE(order_at) = ...` prevents partition pruning
3. **Implicit type casts** — `WHERE user_id = 123` (int vs string)
4. **Cartesian joins** — missing JOIN condition
5. **Correlated subqueries** — should be a window function or join
6. **NOT IN with NULLs** — silently returns empty result
7. **OR on different columns** — defeats indexes
8. **UNION instead of UNION ALL** — extra dedup cost
9. **Large broadcast joins** — driver OOM
10. **Skewed joins** — one key dominates a partition

For each, AI can usually name the anti-pattern from the plan. The fix is yours.

---

## The prompt — "explain this query profile"

```text
ROLE: senior query-tuning engineer on {Snowflake | BigQuery | Databricks}.

CONTEXT:
- this query used to run in 30s, now runs in 8 minutes
- it scans table X with 200M rows
- cluster/partition keys: {list}
- AQE enabled: yes/no
- the failure started after {event}

TASK:
Given the EXPLAIN ANALYZE output below, in order:
1. Name the top 3 anti-patterns you see.
2. For each, the specific change that would address it.
3. The single change most likely to fix the worst bottleneck.
4. Anything that needs data-distribution info you don't have.

[PASTE EXPLAIN ANALYZE]

CONSTRAINTS:
- cite the plan line that suggests each anti-pattern
- do not speculate beyond the plan

FORMAT: numbered list, ranked by impact
```

---

## Case study — slow dbt model

```sql
-- before (slow)
SELECT
  user_id,
  DATE_TRUNC(created_at, MONTH) AS month,
  COUNT(*) AS order_count
FROM fct_orders
WHERE DATE_TRUNC(created_at, MONTH) >= '2024-01-01'
GROUP BY 1, 2
```

```sql
-- after (AI-suggested)
SELECT
  user_id,
  DATE_TRUNC(created_at, MONTH) AS month,
  COUNT(*) AS order_count
FROM fct_orders
WHERE created_at >= '2024-01-01'           -- removed function from filter
GROUP BY 1, 2
```

The fix: **don't put a function on the column you're filtering on**. The function prevents partition pruning. AI spots this in seconds. Without AI, you might miss it for days.

---

## AI for index / cluster-key recommendations

AI can suggest indexes / clustering keys, but **always validate with EXPLAIN**:

```sql
-- AI suggests: "cluster fct_orders by (user_id, created_at)"
-- You check:
EXPLAIN SELECT ... WHERE user_id = ? AND created_at > ?;
-- If cluster pruning applies, ship. If not, iterate.
```

AI is decent at naming candidate keys. It's bad at knowing whether they'll actually be used.

---

## What AI cannot optimise

- **Cardinality estimation** without column statistics
- **Cost-based decisions** without a real plan
- **Caching strategy** — that's infra, not SQL
- **Warehouse sizing** — that's capacity, not the query
- **Cross-system data movement** — that's architecture

If your "slow query" is actually "the wrong architecture," no SQL optimisation will save you.

---

## What Comes Next

> Lesson 4 — **Data Exploration & Profiling** — using AI to accelerate the first 30 minutes with a new dataset: schema inference, distribution analysis, anomaly detection.
