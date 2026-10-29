# 4.2 — Reading the Execution Plan in the UI

> **Section 4 · Query Execution Plan · Lecture 4.2 · 5:50**

## 🎯 What you will learn

- Every field in the Query plan panel and what it means
- How to read the GRAPH and EXECUTION DETAILS views
- A repeatable diagnosis workflow
- The metrics that tell you *what* to fix

---

## 🧠 Concept

The Query plan panel is where optimization becomes empirical rather than guesswork. This lesson
is a practical guide to reading it.

### The Query plan panel

```
┌────────────────────────────────────────────────────────────────┐
│ Query plan:  [GRAPH] [EXECUTION DETAILS]                        │
├────────────────────────────────────────────────────────────────┤
│  S00: Input                          [Table scan: 1.2 GB]       │
│  ├─ 0.42s  ████████████                                            │
│  ├─ bytes: 1.2 GB in → 1.2 GB out                                │
│  └─ rows: 50,000,000 → 12,000,000                                 │
│       └─ S01: Filter (order_date >= ...)                         │
│            ├─ 0.08s  ██                                            │
│            ├─ bytes: 1.2 GB → 240 MB                             │
│            └─ rows: 12,000,000 → 12,000,000                       │
│                 └─ S02: Output                                     │
│                      ├─ 0.01s  ▌                                  │
│                      └─ rows: 12,000,000                          │
└────────────────────────────────────────────────────────────────┘
```

### The fields

| Field | Meaning | What to look for |
|-------|---------|-------------------|
| **Stage ID** | `S00`, `S01`... Execution order | Stages run in dependency order |
| **Stage name** | `Input`, `Filter`, `Join`, `Aggregate`, `Output` | Where the work happens |
| **Elapsed time** | Wall time for the stage | The longest bar is usually the bottleneck |
| **Wait time** | Time queued for slots | ⚠️ High wait = capacity problem |
| **Active time** | Time actually computing | High active = query problem |
| **Bytes in / out** | Data volume at stage boundaries | A sudden drop = a filter working |
| **Rows in / out** | Row counts | A big drop = selectivity |
| **Workers** | Parallel tasks | Low worker count = small query |
| **Slot ms** | CPU time consumed | The real cost driver for capacity pricing |

---

## 🧠 GRAPH view

The GRAPH view shows the stage DAG. Read it top-to-bottom.

```
              ┌──────────────┐
              │ S00: Input   │  2.0 GB
              │  Scan        │
              └──────┬───────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   ┌──────────────┐      ┌──────────────┐
   │ S01: Filter  │      │ S01: Filter  │   1.0 GB each
   └──────┬───────┘      └──────┬───────┘
          │                     │
          └──────────┬──────────┘
                     ▼
              ┌──────────────┐
              │ S02: Join    │   1.8 GB  ← SHUFFLE
              └──────┬───────┘
                     ▼
              ┌──────────────┐
              │ S03: Output  │   50 MB
              └──────────────┘
```

### What to look for in the GRAPH

1. **Width of the fan-out** — how many parallel branches. More branches = more parallelism.
2. **Where bytes expand** — a stage whose output bytes exceed its input bytes means a
   *denormalization* or a *cross join* has occurred.
3. **Fan-in points** — where many branches converge. That is a shuffle, and it is expensive.
4. **A single narrow stage at the end** — the final aggregation. If it is long, the `GROUP BY` is
   the problem.

💡 **The "bytes expand" pattern is the signature of a cross join or a many-to-many join.**
If output bytes are much larger than input bytes at a stage, you have multiplied your data.

---

## 🧠 EXECUTION DETAILS view

A per-stage timeline, which is where wait-vs-active becomes visible.

```
S00: Input
   ├─ Shuffle  █
   ├─ Read     ██
   ├─ Wait     ████████████     ← 4.2s waiting for slots
   └─ Active   █
```

| Bar | Meaning | Action |
|-----|---------|--------|
| **Read** | Reading from storage | Optimize with pruning |
| **Shuffle** | Moving data between workers | Reduce the join/aggregate |
| **Wait** | Queued for resources | **Buy capacity** or reduce concurrency |
| **Active** | Computing | Optimize the query |

💡 **The rule of thumb:** if `Wait` is more than 20% of a stage's time, **do not optimize the
query** — you have a capacity problem. Optimizing the SQL will not help a query that is queued
behind 200 other jobs.

---

## 🛠️ A Repeatable Diagnosis Workflow

```
Step 1: Dry run
        └─▶ How many bytes will this scan? Is that proportional to the table size?

Step 2: Run and open Job details
        └─▶ total_bytes_processed, total_slot_ms

Step 3: Open Query plan → GRAPH
        └─▶ Where does the data expand? Where are the fan-in points?

Step 4: Open Query plan → EXECUTION DETAILS
        └─▶ For the longest stage: is it Wait or Active?

Step 5: Diagnose
        ├─ Bytes >> table size      → no pruning (partition/cluster)
        ├─ Data expands mid-plan    → cross join / join explosion
        ├─ Long fan-in              → shuffle (join/aggregate)
        ├─ Long wait                → capacity problem
        └─ Long active on scan      → too much data, needs pruning
```

### Worked example

```
Symptom:  A dashboard query takes 90 seconds and costs $3.20.

Step 1 (dry run):  estimated 1.2 TB scanned. Table is 1.5 TB.
                   → 80% of the table is being read. Something is not pruning.

Step 2 (job details): 1.18 TB processed, 340 slot-seconds.

Step 3 (graph): S00 Input 1.2 GB → S01 Filter 1.1 GB → S02 Join 2.3 GB (!)
                 → Data nearly doubled at the join. Join explosion.

Step 4 (execution details): S02 Join — 55s Active (not Wait).
                            S00 Scan — 12s Active.

Step 5 (diagnosis): TWO problems.
     (a) The WHERE clause is not on the partition column → no partition pruning.
     (b) The join is one-to-many, multiplying rows 2×, and the GROUP BY
         then shuffles the doubled set.
```

The fix:

```sql
-- ❌ Before
SELECT c.segment, SUM(o.total_amount) AS revenue
FROM `YOUR_PROJECT_ID.curated.orders` o
JOIN `YOUR_PROJECT_ID.curated.customers` c USING (customer_id)
WHERE o.order_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY c.segment;

-- ✅ After
SELECT c.segment, SUM(o.total_amount) AS revenue
FROM `YOUR_PROJECT_ID.curated.orders` o
JOIN `YOUR_PROJECT_ID.curated.customers` c USING (customer_id)
WHERE o.order_date >= DATE_SUB(CURRENT_CURRENT_DATE(), INTERVAL 30 DAY)  -- partition column!
GROUP BY c.segment;
```

💡 **The 30-second fix that matters most:** filter on the **partition column**, not on a
timestamp that merely contains the date. `order_ts >= TIMESTAMP(...)` cannot prune an
`order_date`-partitioned table. `order_date >= DATE(...)` can.

---

## 🛠️ Hands-On: Build a Plan-Reading Habit

### 1. Create a test bed

```sql
-- A table big enough to show meaningful differences
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_test`
PARTITION BY order_date
CLUSTER BY customer_id
AS
SELECT
    DATE_ADD(DATE '2026-01-01', INTERVAL INT(div(ROW_NUMBER() OVER (), 1000)) DAY) AS order_date,
    CONCAT('cust_', LPAD(CAST(div(ROW_NUMBER() OVER (), 500) AS STRING), 6, '0')) AS customer_id,
    CAST(ROW_NUMBER() OVER () AS INT64) AS order_id,
    ROUND(RAND() * 500, 2) AS total_amount,
    status
FROM UNNEST(GENERATE_ARRAY(1, 1000000)) AS n;
```

### 2. Run the four variants and compare

```sql
-- V1: no filter, SELECT *
SELECT * FROM `YOUR_PROJECT_ID.curated.orders_test` LIMIT 10;

-- V2: filter on partition column, SELECT *
SELECT * FROM `YOUR_PROJECT_ID.curated.orders_test`
WHERE order_date = DATE '2026-06-15' LIMIT 10;

-- V3: filter on partition column, narrow projection
SELECT order_id FROM `YOUR_PROJECT_ID.curated.orders_test`
WHERE order_date = DATE '2026-06-15' LIMIT 10;

-- V4: cluster filter as well
SELECT order_id FROM `YOUR_PROJECT_ID.curated.orders_test`
WHERE order_date = DATE '2026-06-15' AND customer_id = 'cust_000042';
```

### 3. Compare the plans

```sql
SELECT
    job_id,
    ROUND((total_bytes_processed / POW(1024, 3)), 1) AS mb_processed,
    ROUND(total_slot_ms / 1000, 2) AS slot_seconds,
    REGEXP_EXTRACT(query, r'V(\d)') AS variant,
    SUBSTR(query, 1, 60) AS query_head
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE query LIKE '%orders_test%'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY creation_time DESC;
```

Expected pattern:

| Variant | Bytes | Why |
|---------|-------|-----|
| V1 | ~Full table | `SELECT *`, no pruning |
| V2 | ~1 partition | Partition pruning works; but all columns read |
| V3 | ~1 partition, 1 column | Column pruning too |
| V4 | ~1 partition + few blocks | Cluster pruning too |

---

## 💡 Production Notes

- **Save the plan.** When you diagnose a query, note the stage-level bytes. Over time you build
  an intuition for "a 1 TB scan should show ~1 TB at S00."
- **`total_bytes_billed` vs `total_bytes_processed`**: billed is what you pay for, processed is
  what was read. They differ when the cache is involved.
- **A query with `total_bytes_processed = 0`** is a cache hit or a metadata-only operation.
- **Look at "workers" per stage.** A stage with 1 worker on a large table means the scan was not
  parallelized — usually because the filter was so selective that BigQuery only needed one.
- **Multi-statement scripts show per-statement plans.** Look at the sub-query stage breakdown in
  the EXECUTION DETAILS view.

---

## 🔑 Key Takeaways

- Read the plan: **stage names, bytes in/out, rows in/out, elapsed, wait vs active**.
- **Data expanding mid-plan** = a join explosion or cross join.
- **Fan-in points = shuffles** = the expensive part.
- **Wait > 20% of stage time = capacity problem**, not a query problem. Do not optimize the SQL.
- The highest-value fix is usually: **filter on the partition column** + **project only the
  columns you need**.
- Build a repeatable workflow: dry run → job details → graph → execution details → diagnosis.

---

## 📚 Practice Exercises

1. **Diagnosis drill.** Take a deliberately bad query and produce a full diagnosis in the format
   of the workflow above: symptom → dry run → job details → graph finding → execution detail
   finding → two root causes → fixed query → measured improvement.

2. **Plan reading practice.** For each stage description, identify the likely problem:
   - "S00: 1.4 GB in, 1.4 GB out, 0.3s"
   - "S01: 1.4 GB in, 90 MB out, 0.1s"
   - "S02: 1.4 GB in, 1.4 GB out, 45s active, 2s wait"
   - "S03: 0.02s wait, 0.01s active, 12s total"

3. **Capacity vs query.** A team says "our queries are slow." Write the queries and procedure that
   distinguish a capacity problem from a query problem. What is the threshold?

4. **Fix verification.** Take a query that costs $5 and reduce it below $0.50. Record the plan
   before and after, and explain every byte of the difference.

---

## 📖 Further Reading

- Reading query plans — https://cloud.google.com/bigquery/docs/query-plan
- Query plan examples — https://cloud.google.com/bigquery/docs/query-plan-examples
- Troubleshooting slow queries — https://cloud.google.com/bigquery/docs/troubleshoot-slow-queries
