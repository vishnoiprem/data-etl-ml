# 2.4 — Architecture of BigQuery

> **Section 2 · BigQuery Fundamentals · Lecture 2.4 · 5:43**

## 🎯 What you will learn

- The two-layer architecture: Colossus (storage) + Dremel (compute)
- How a query actually flows through the system, step by step
- What "slots" really are and how parallelism works
- Why columnar storage + tree execution = fast queries

---

## 🧠 Concept

This is the chapter that separates people who *use* BigQuery from people who *understand* it.
Everything else in this course is an application of the ideas here.

### The two layers

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│   Web Console  │  bq CLI  │  Python/Java/Go SDK  │  JDBC/ODBC   │
└────────────────────────────┬─────────────────────────────────────┘
                             │  REST / gRPC (jobs.insert)
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                     BIGQUERY FRONT END                          │
│   • Parses & validates SQL (GoogleSQL → logical plan)          │
│   • Resolves table references against the catalog               │
│   • Applies IAM, policy tags, row-level security                │
│   • Produces an execution plan (DAG of stages)                  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
┌────────────────────────┐   ┌────────────────────────────────────┐
│  COMPUTE LAYER         │   │  STORAGE LAYER                     │
│  (Dremel / Slots)      │   │  (Colossus)                        │
│                        │   │                                    │
│  • Slots = vCPU + 4GB  │   │  • Columnar, compressed            │
│  • Distributed workers │◀──┤  • Replicated, no NameNode        │
│  • Tree execution      │   │  • Metadata in a separate catalog │
│  • Query-scoped        │   │  • Unlimited logical size         │
└────────────────────────┘   └────────────────────────────────────┘
```

### Layer 1 — Storage: Colossus

Colossus is Google's distributed, columnar storage service. It is **not** HDFS, and this matters:

| Property | Colossus | HDFS |
|----------|----------|------|
| Metadata location | Distributed, in the service | **Single NameNode in RAM** |
| File count limit | Effectively unlimited | Tens of millions (namespace size) |
| Columnar | Native | No (row-oriented blocks) |
| Compression | Per-column, type-aware | Per-block, generic |
| Durability | Replicated across regions | 3× replication within a cluster |
| Scale | Logical (PB+) | Bound by cluster config |

💡 **Key insight:** BigQuery's storage is *logical*. There is no "cluster" whose size determines how
much data you can store. A table can be 1 GB or 1 PB with the same operational profile. This is
why BigQuery doesn't need a load step to "make room."

#### How table data is laid out

A BigQuery table is stored as **column segments**. For a table with schema
`(id INT64, name STRING, amount FLOAT64, created_at TIMESTAMP)`:

```
Table
├── Column: id
│   ├── Segment 1: [page, page, page, ...]   ← compressed ints, ~1–4 bytes each
│   └── Segment 2: [...]
├── Column: name
│   ├── Segment 1: [page, page, ...]          ← dictionary-encoded, ~20 bytes each
│   └── Segment 2: [...]
├── Column: amount
│   └── ...
└── Column: created_at
    └── ...
```

Each column is compressed with a codec suited to its type:
- Integers → dictionary + bit-packing
- Strings → dictionary encoding (most strings repeat) + front-coding
- Repeated/struct fields → specialized encodings

**Consequence:** a query referencing 2 of 4 columns reads ~half the bytes. This is why
`SELECT *` is a cost bug, not a style bug.

### Layer 2 — Compute: Dremel and Slots

Dremel is BigQuery's distributed query engine. It was originally Google's internal engine for
analyzing petabytes of web crawl data — the paper that described it, *"Dremel: Interactive Analysis
of Web-Scale Datasets"*, won the 2010 ACM SIGMOD Best Paper award.

#### Slots

```
1 slot = 1 vCPU + 4 GB RAM
```

BigQuery allocates slots to a query dynamically, up to the project's maximum. A simple query might
get 10 slots; a 40 TB scan might get 2,000.

#### Dremel's Tree Execution Model

Dremel does not use the traditional Volcano iterator model. It uses **tree execution**:

```
Traditional (Volcano) — pull-based, row-at-a-time
   Scan → Filter → Project → Join → Aggregate
   Each operator calls its child for one row at a time.
   Result: enormous function-call overhead, poor cache locality.

Dremel — tree execution
   The plan is compiled into a tree of parallel stages.
   Each stage has:
     • parallel tasks (one per slot)
     • a set of cursors that pipeline results upward
   Result: operators work on batches (vectors), not individual rows.
```

The paper's key contribution for BigQuery: **tree execution** lets a single operator process
thousands of rows per call, amortizing the interpreter overhead across a batch.

#### The stages of a query

```
Stage 1: Scan         ──▶ read columns, apply partition/cluster pruning
Stage 2: Filter       ──▶ push down predicates
Stage 3: Join (hash)  ──▶ shuffle + hash table build/probe
Stage 4: Aggregate    ──▶ partial + final aggregation (two-phase)
Stage 5: Output       ──▶ write results
```

Each stage boundary is a **synchronization point** and a **data shuffle**. Joins and aggregations
are the expensive stages — they must shuffle data between workers. Scans and filters are cheap.

💡 **This is why `GROUP BY` on a huge table is expensive but a `SELECT COUNT(*)` on the same table
is cheap.** `COUNT(*)` needs only one aggregate row per worker. A `GROUP BY customer_id` produces
millions of groups that must be shuffled and merged.

#### Pushing down

The query planner pushes operations down the tree whenever it can:

```
SELECT customer_id, SUM(amount)          -- after
FROM orders                              -- table
WHERE order_date >= '2026-01-01'         -- pushed down as a filter
```

The pushed-down filter does two things:
1. **Prunes partitions** — entire partition directories are skipped, never read
2. **Prunes blocks** — within a partition, block-level metadata stats let entire blocks be skipped

Column pruning happens at the same time: only referenced columns are fetched from storage.

### The end-to-end query flow

```
1. CLIENT ──jobs.insert──▶ FRONT END
2. FRONT END
   ├─ Parse & bind SQL
   ├─ Resolve table refs → locate column metadata
   ├─ Apply security (IAM, policy tags, RLS)
   ├─ Rewrite into logical plan
   ├─ Optimize: push filters/columns, reorder joins
   └─ Generate physical plan (DAG of stages)
3. ALLOCATOR ──▶ reserve slots for the job
4. WORKERS execute stages in dependency order
   ├─ Stage A: scan (parallel across slots)
   ├─ Stage B: shuffle + join
   └─ Stage C: aggregate + write
5. RESULTS written to a temporary table (or streamed to the client)
6. JOB marked DONE; bytes_processed and slot_ms recorded
```

💡 **Why a query job has a "Job ID" and takes time to start.** Steps 1–4 are the scheduling
overhead. A query that takes 30 seconds but shows "waiting for resources" for 25 of them means
your project's slot capacity is exhausted — a capacity problem, not a query problem.

---

## 🛠️ Hands-On: Observe the Architecture

### 1. See the stages in the execution plan

```sql
-- Use the CLI's --dry_run to see bytes before running
bq query --dry_run --use_legacy_sql=false '
  SELECT customer_id, COUNT(*) AS n, SUM(amount) AS total
  FROM `YOUR_PROJECT_ID.analytics.orders`
  WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  GROUP BY customer_id'
```

### 2. Observe partition pruning in the plan

```sql
-- Force a full scan (no partition filter) — check bytes_processed
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.analytics.orders`;

-- Same table, partition-filtered — compare bytes_processed
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.analytics.orders`
WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY);
```

The difference in `total_bytes_processed` **is** the partition pruning benefit, measured.

### 3. Observe column pruning

```sql
-- Scans all columns
SELECT * FROM `YOUR_PROJECT_ID.analytics.orders` LIMIT 100;

-- Scans 1 column
SELECT order_id FROM `YOUR_PROJECT_ID.analytics.orders` LIMIT 100;
```

Compare `total_bytes_processed` between the two. The ratio should be close to the width ratio of
the schemas.

### 4. Inspect slot usage

```sql
SELECT
    job_id,
    creation_time,
    total_slot_ms,
    ROUND(total_slot_ms / 1000 / 60, 2) AS slot_minutes,
    ROUND(total_slot_ms / 1000 / 3600, 3) AS slot_hours
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE job_type = 'QUERY'
  AND state = 'DONE'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
ORDER BY total_slot_ms DESC
LIMIT 20;
```

### 5. Check project slot limits

```bash
gcloud compute regions describe us-central1 \
    --format="value(quotas)"
```

```sql
-- Jobs by slot-time — find your most expensive queries by CPU, not by bytes
SELECT
    job_id,
    user_email,
    ROUND(total_slot_ms / 1000 / 60, 1) AS slot_minutes,
    ROUND((total_bytes_processed / POW(1024, 4)) * 6.25, 2) AS est_usd,
    SUBSTR(query, 1, 120) AS query_head
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND total_slot_ms > 60000
ORDER BY total_slot_ms DESC;
```

---

## 💡 Production Notes

- **The `LIMIT` clause does not reduce bytes scanned** for most operations — BigQuery still reads
  the matching blocks. Only partition and cluster pruning reliably reduce cost.
- **`SELECT *` is a cost bug.** It forces every column to be read and decoded. Always project
  explicitly.
- **A query waiting on slots looks like a slow query.** Distinguish "waiting for resources" from
  "executing" in the UI before optimizing SQL — you may have a capacity problem, not a query
  problem.
- **Shuffles are the expensive part.** Every `JOIN` and every non-trivial `GROUP BY` shuffles.
  Reduce shuffle by pre-aggregating, using `GROUP BY` keys that cluster, and avoiding
  `ORDER BY` on huge results.
- **Reserved slots eliminate the wait.** If your queries regularly sit in "waiting for resources",
  buy capacity.

---

## 🔑 Key Takeaways

- Two layers: **Colossus** (distributed columnar storage, no NameNode) + **Dremel** (distributed
  query engine, slot-based).
- **Slots** = 1 vCPU + 4 GB, allocated dynamically per job.
- **Dremel uses tree execution** (batched, parallel stages), not Volcano's row-at-a-time iteration.
- **Storage is logical and unlimited** — no cluster sizing, no load step to "make room."
- **Bytes scanned = columns read × blocks not pruned.** Partition pruning, cluster pruning, and
  explicit column lists are the three levers.
- Joins and aggregations are expensive because they **shuffle**; scans and filters are cheap.

---

## 📚 Practice Exercises

1. **Measure column pruning.** Create a wide table (20 columns, varied types), then measure
   `total_bytes_processed` for `SELECT *` vs `SELECT` of one narrow column vs `SELECT` of one wide
   column. Explain the ratios.

2. **Slot analysis.** Run a query over 1 TB with `GROUP BY` on a high-cardinality column, then
   aggregate pre-aggregated data. Compare `total_slot_ms` and explain the shuffle cost.

3. **Stage design.** Draw the stage DAG for:
   ```sql
   SELECT c.region, SUM(o.amount)
   FROM orders o JOIN customers c USING (customer_id)
   WHERE o.order_date >= '2026-01-01'
   GROUP BY c.region
   ```
   Identify every shuffle point and predict which stage dominates runtime.

4. **Capacity vs query.** A user's dashboard query takes 45 seconds, and the UI shows "waiting for
   resources" for 40 of them. What is the actual problem, and what are two fixes (one SQL-side, one
   capacity-side)?

5. **Design a table.** Design the physical layout for a 10 PB clickstream table with columns:
   `event_id STRING, event_ts TIMESTAMP, user_id STRING, page STRING, revenue FLOAT64`.
   How would you partition it? What encoding would you expect for each column type?

---

## 📖 Further Reading

- Dremel paper (VLDB 2010) — https://research.google/pubs/pub36632/
- BigQuery architecture overview — https://cloud.google.com/bigquery/docs/introduction
- BigQuery slots and reservations — https://cloud.google.com/bigquery/docs/slots
- Colossus — https://research.google/pubs/pub42070/
