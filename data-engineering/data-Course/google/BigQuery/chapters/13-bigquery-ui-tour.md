# 2.6 — BigQuery UI Tour

> **Section 2 · BigQuery Fundamentals · Lecture 2.6 · 12:57**

## 🎯 What you will learn

- Every panel in the BigQuery console and what it tells you
- How to read the query execution details — this is where optimization happens
- Query history, saved queries, and scheduled queries from the UI
- Keyboard shortcuts and workflow tips that save hours

---

## 🧠 Concept

The BigQuery console is the single most under-used BigQuery feature. Most engineers use it as a
SQL editor and ignore the diagnostic panels that show them *why* a query was slow or expensive.
Learning to read them is the difference between guessing and engineering.

### Console layout

```
┌──────────────────────────────────────────────────────────────────────────┐
│  BigQuery ▾ Project ▾ |  RESOURCES │ WORKBENCH │ DATA            [Search]│
├───────────────────┬──────────────────────────────────────────────────────┤
│  RESOURCES        │  Query editor                                        │
│                   │  ┌────────────────────────────────────────────────┐  │
│  ▾ your_project   │  │ SELECT * FROM `p.dataset.table` WHERE ...      │  │
│    ▾ analytics    │  │                                                 │  │
│      ▸ customers  │  └────────────────────────────────────────────────┘  │
│      ▸ orders     │  [Run ▾] [Schedule] [Save] [Share] [Format] [⋮]     │
│    ▸ staging      ├──────────────────────────────────────────────────────┤
│    ▾ raw          │  Results (3 tabs)                                    │
│      ▸ events     │  [Results] [Chart] [Job details] [Preview]           │
│  ▸ public data    │  ┌────────────────────────────────────────────────┐  │
│                   │  │ row  col1  col2  col3                          │  │
│  [CREATE DATASET] │  │ 1    ...   ...   ...                          │  │
│                   │  └────────────────────────────────────────────────┘  │
│                   ├──────────────────────────────────────────────────────┤
│                   │  Query plan: [GRAPH] [EXECUTION DETAILS]            │
│                   │  ┌────────────────────────────────────────────────┐  │
│                   │  │  S00  Input  →  S01  Filter  →  S02  Output   │  │
│                   │  └────────────────────────────────────────────────┘  │
└───────────────────┴──────────────────────────────────────────────────────┘
```

### The Resources panel

The left panel is the **catalog browser**. It shows your project's datasets and tables, plus
public datasets. Key interactions:

- **Click a table** → opens a tab with Schema, Details, Sharing, and Preview tabs
- **Schema tab** → column names, types, descriptions, modes (NULLABLE / REQUIRED / REPEATED),
  policy tags. This is where you design schemas.
- **Details tab** → table size, row count, partition count, clustering columns, creation time,
  last modified, expiration time, encryption, labels. This is where you audit.
- **Sharing tab** → who can access it. Also where authorized views live.
- **Preview tab** → sample rows without running a query.

💡 **The Details tab is your monitoring dashboard.** Partition count, clustering columns, and
table size should be part of your regular review. A table with 10,000 partitions and no clustering
is a warning sign.

### The query editor

- **Run** button has three modes worth knowing:
  - `Run` — execute now
  - `Dry run` — validate + estimate bytes without executing (free, no cost)
  - `Run` with **destination table** — write results to a table
- **Format** button → auto-formats SQL (shortcut `Shift+Cmd+F` / `Ctrl+Shift+F`)
- **Save** → save the query to the project's saved queries
- **Share** → share a link; the recipient gets read access to the query text (and can run it if
  they have `jobUser`)
- **⋮ (kebab)** → job settings, maximum bytes billed, use legacy SQL toggle, random shuffle,
  flatten results, etc.

💡 **Always use Dry run first.** It costs nothing, takes a second, and tells you exactly how many
bytes the query will scan. This single habit prevents most runaway bills.

### The four result tabs

**1. Results** — the data grid. Header shows row count and elapsed time.

**2. Chart** — auto-visualization of the result set. Useful for quick sanity checks, but do not
rely on it for anything serious.

**3. Job details** — the diagnostic tab. This is where you learn *why* something happened:

```
Job ID:              bquxjob_abc123
Location:            US
Created:             2 minutes ago
State:               DONE
Total bytes processed: 1.23 GB
Slot time:           12.4 s
```

**4. Preview** — schema and a sample of rows from the result, without materializing the full grid.

### Query plan — the two views

**GRAPH** shows the stage DAG:

```
┌──────────┐      ┌──────────┐      ┌──────────┐
│ S00      │      │ S01      │      │ S02      │
│ Input    │─────▶│ Filter   │─────▶│ Output   │
│ 1.2 GB   │      │ 8.4 MB   │      │ 120 rows │
└──────────┘      └──────────┘      └──────────┘
```

Each stage shows **bytes in → bytes out** and **rows**. This is how you see where data volume
explodes.

**EXECUTION DETAILS** shows the per-stage timeline:

```
S00: Input                                    ████████████  0.8s   1.2 GB
S01: Filter                                   ██          0.1s   8.4 MB
S02: Output                                   █           0.05s  120 rows
```

💡 **What to look for:**
- A long flat bar on the **first** stage → the scan is the bottleneck (partition/cluster pruning)
- One stage dramatically larger in bytes than the input → a shuffle (join or group by)
- A gap between stages → waiting for resources (capacity problem, not a query problem)
- Many small stages → query is doing too much

---

## 🛠️ Hands-On: Reading a Slow Query

### Step 1 — Run the query with dry run first

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS lifetime_value
FROM `YOUR_PROJECT_ID.analytics.orders`
WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY customer_id
ORDER BY lifetime_value DESC;
```

### Step 2 — Check the Execution Details

Record: total bytes processed, slot time, and the per-stage timings.

### Step 3 — Diagnose

| Observation | Diagnosis | Fix |
|-------------|-----------|-----|
| Bytes >> table size | No partition pruning | Add a partition filter |
| Bytes high for a small table | No clustering / `SELECT *` | Add clustering, project columns |
| Shuffle stage dominates | High-cardinality `GROUP BY` | Pre-aggregate, cluster on the key |
| Long wait before first stage | Slot exhaustion | Buy capacity or reduce concurrency |
| Output stage slow | Huge result set | Add `LIMIT`, aggregate earlier |

### Step 4 — Fix and compare

```sql
-- Optimized: clustered table + partition filter + explicit columns
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS lifetime_value
FROM `YOUR_PROJECT_ID.analytics.orders`
WHERE order_date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) AND CURRENT_DATE()
GROUP BY customer_id
ORDER BY lifetime_value DESC;
```

### Step 5 — Verify with the job history

```sql
SELECT
    job_id,
    creation_time,
    ROUND((total_bytes_processed / POW(1024, 3)), 2) AS mb_processed,
    ROUND(total_slot_ms / 1000, 2) AS slot_seconds,
    SUBSTR(query, 1, 80) AS query_head
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE job_type = 'QUERY'
ORDER BY creation_time DESC
LIMIT 10;
```

💡 **Build this habit:** after every non-trivial query, check `total_bytes_processed` against
your expectation. Over time this trains an intuition for what a query *should* cost.

---

## 💡 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl + Enter` | Run query |
| `Cmd/Ctrl + Shift + Enter` | Dry run |
| `Cmd/Ctrl + Shift + F` | Format SQL |
| `Cmd/Ctrl + K` | Open the command palette |
| `Cmd/Ctrl + Alt + M` | Toggle multi-statement editor |

### The multi-statement editor

Enable via **⋮ → Multi-statement mode**. This lets you script a whole pipeline in one job:

```sql
CREATE TEMP TABLE stg_orders AS
SELECT * FROM `YOUR_PROJECT_ID.analytics.orders`
WHERE order_date = CURRENT_DATE();

CREATE TEMP TABLE stg_customers AS
SELECT * FROM `YOUR_PROJECT_ID.analytics.customers`;

MERGE `YOUR_PROJECT_ID.curated.fact_orders` t
USING stg_orders s
ON t.order_id = s.order_id
WHEN MATCHED THEN UPDATE SET
    total_amount = s.total_amount,
    updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT (order_id, customer_id, order_date, total_amount)
VALUES (s.order_id, s.customer_id, s.order_date, s.total_amount);
```

💡 **Multi-statement scripts are the cleanest way to write a BigQuery-native pipeline.** Each
statement runs as a sequential sub-job; if one fails, the whole script fails. This is the standard
pattern for Composer DAGs that only need BigQuery.

---

## 🔑 Key Takeaways

- The console has four panels: Resources, query editor, results, query plan. All four matter.
- **Job details** (bytes processed, slot time) and **Query plan** (graph + execution details) are
  the diagnostic tools you should always open.
- **Always dry run** — free, instant, and shows exact bytes.
- The **Details tab** of any table is your monitoring dashboard (partitions, clustering, size).
- Multi-statement mode enables clean BigQuery-native pipelines.
- Build the habit of checking `total_bytes_processed` after every query.

---

## 📚 Practice Exercises

1. **Diagnosis drill.** Run a deliberately bad query (full scan + `SELECT *` + high-cardinality
   `GROUP BY`) and write a full diagnosis from the execution details: which stage dominates, why,
   and the specific fix.

2. **Console tour.** Document every tab on a table's detail page and what you would use each for
   during a production incident.

3. **Multi-statement script.** Write a single multi-statement SQL script that: stages today's
   orders, merges them into a fact table, updates a summary table, and creates a view. Use
   `DECLARE` for a shared variable.

4. **Cost habit.** Write a small script that, after any query, prints bytes processed and estimated
   cost from `INFORMATION_SCHEMA.JOBS`. Turn it into a reusable snippet.

---

## 📖 Further Reading

- BigQuery console docs — https://cloud.google.com/bigquery/docs/console
- Reading execution plans — https://cloud.google.com/bigquery/docs/query-plan
- BigQuery best practices — https://cloud.google.com/bigquery/docs/best-practices
