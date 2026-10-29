# 2.1 — Model Types & Materialization Strategies

> **Section 2 · Modeling · Lecture 2.1 · 18:25**

## 🎯 What you will learn

- The four `config { type: ... }` values — `table`, `view`, `incremental`, `ephemeral` — and the exact SQL each compiles to
- What each strategy costs in bytes scanned, storage, and query latency
- How `CREATE OR REPLACE TABLE` gives you atomic swaps in BigQuery
- Why views can silently become a performance trap when partition filters don't push down
- How `partitionBy`, `clusterBy`, `uniqueKey`, `labels`, and `transitive` shape the physical table
- The staging → intermediate → mart layering convention and why the boundaries exist

---

## 🧠 Concept

### The one decision that drives everything downstream

Every Dataform model starts with a question: **should this be a stored thing, or a computed
thing?** That answer determines whether BigQuery stores bytes, whether downstream models
re-compute the logic, how a failure behaves, and what the model costs every single day.

In Dataform you answer it with `config { type: "..." }`. There are exactly four values, and each
compiles to a different shape of SQL:

```
   table       → CREATE OR REPLACE TABLE         stored, full rewrite every run
   view        → CREATE OR REPLACE VIEW          definition only; re-computed per query
   incremental → CREATE OR REPLACE TABLE + MERGE  stored; only new rows processed
   ephemeral   → (nothing!)                      inlined as a CTE in every downstream model
```

### `type: "table"` → `CREATE OR REPLACE TABLE`

The default. Dataform compiles your `SELECT` into a statement that creates or replaces a physical
BigQuery table:

```sql
CREATE OR REPLACE TABLE `my-project.analytics.stg_orders` (...)
PARTITION BY DATE(updated_at)
CLUSTER BY customer_id
AS
SELECT id, customer_id, amount, updated_at
FROM `my-project.raw.orders`
WHERE updated_at >= '2024-01-01';
```

**Cost profile:** you're billed for bytes scanned during the query plus bytes written into the
table (active logical storage). A full rebuild re-scans the entire source and rewrites the entire
destination every run.

**When to use it:** the model is a final artifact a dashboard reads; the output is small enough
that a full rebuild is cheap; you need a stable, independently-queryable object for audit.

💡 **Rule of thumb:** if the output table is under a few GB and the source scan is cheap, a plain
`table` is the right answer. Most "we need incremental" anxiety in a young pipeline is premature
optimization.

### `type: "view"` → `CREATE OR REPLACE VIEW`

A view stores only the **query definition**. No data, no rows.

```sql
CREATE OR REPLACE VIEW `my-project.analytics.v_daily_sales` AS
SELECT
  DATE_TRUNC(order_ts, DAY) AS sale_date,
  SUM(amount)              AS total_amount,
  COUNT(*)                 AS order_count
FROM `my-project.analytics.stg_orders`
GROUP BY 1;
```

**Cost profile:** a view is **free to create** (it stores nothing) but **not free to read**. Every
query against it re-executes the underlying query and you are billed for those bytes — read
amplification.

| | Table | View |
|---|---|---|
| Bytes **scanned** on read | No (already materialized) | **Yes** — logic runs every time |
| Bytes **stored** for the result | Yes (active logical storage) | No |
| Latency / re-computation | ~instant read, never recomputed | Read + compute the whole query, every time |

```
TABLE:  read fct_sales     →    12 MB scanned,   1 ms
VIEW:   read v_daily_sales →  4.7 GB scanned, 900 ms   (it re-aggregates stg_orders)
```

**When to use it:** the definition is cheap to recompute and you want a live alias; you want a
**logical layer** in the DAG — a named, dependency-tracked concept — without physical storage; the
output is a thin wrapper (filter, rename, small join).

**The classic view performance trap.** Views lose their partitioning advantage if the partition
filter cannot be pushed down.

```
Scenario A — filter on the partition column, expressed in the view:
  CREATE OR REPLACE VIEW v_sales AS
    SELECT * FROM fct_sales WHERE sale_date >= '2024-01-01';

  Query: SELECT * FROM v_sales WHERE sale_date = '2024-06-01';
  → BigQuery pushes BOTH predicates down to fct_sales
  → Partition pruning works → only 1 day scanned. Cost: 3 MB.


Scenario B — filter that hides the partition column behind an expression:
  CREATE OR REPLACE VIEW v_sales AS
    SELECT DATE_ADD(sale_date, INTERVAL 1 DAY) AS sale_date FROM fct_sales;

  Query: SELECT * FROM v_sales WHERE sale_date = '2024-06-01';
  → The predicate applies to sale_date + 1 day, not to the stored sale_date
  → No partition pruning → full table scan. Cost: 4.7 GB.
```

⚠️ **A partition filter wrapped in an expression (a function call, a cast, a join to a
non-partitioned lookup, an `OR` between two different partition columns) frequently defeats
partition pruning.** Verify with `EXPLAIN`, or check `totalBytesProcessed` in a dry run.

💡 **Treat a view as a *query*, not a *table*.** The moment a view is on a hot dashboard path or
sits over a partitioned table with a non-pushable filter, materialize it.

### `type: "ephemeral"` → not materialized at all

The one people misunderstand most. An `ephemeral` model is **never compiled into a table or
view**. Its SQL is **inlined as a CTE** into every downstream model that references it.

```sqlx
// definitions/marts/int__customer_labels.sqlx
config { type: "ephemeral" }

SELECT customer_id,
       CASE WHEN lifetime_value > 10000 THEN 'platinum'
            WHEN lifetime_value > 1000  THEN 'gold'
            ELSE 'standard' END AS segment
FROM ${ref("stg_customers")}
```

A downstream model references it with `JOIN ${ref("int__customer_labels")}`. Dataform compiles
both models into a single statement:

```sql
CREATE OR REPLACE TABLE `my-project.analytics.fct_orders` AS
WITH
  int__customer_labels AS (
    -- ⚠️ the ephemeral model's SQL was INLINED here
    SELECT customer_id,
           CASE WHEN lifetime_value > 10000 THEN 'platinum'
                WHEN lifetime_value > 1000  THEN 'gold'
                ELSE 'standard' END AS segment
    FROM `my-project.analytics.stg_customers`
  )
SELECT o.id, c.segment
FROM `my-project.analytics.stg_orders` AS o
JOIN int__customer_labels AS c USING (customer_id);
```

**Cost profile:** zero storage, zero table-creation cost — but note carefully:

| Scenario | Ephemeral | Table |
|---|---|---|
| Storage | None | Active logical storage billed |
| `stg_customers` scanned | Once per downstream query that inlines it | Once per rebuild |
| 5 downstream models | scanned 5× | scanned 1×, then 5 cheap reads |
| 50 downstream models | scanned 50× | scanned 1× |
| Compiled SQL size | Grows with every dependent | Constant |

⚠️ **The trap:** because the ephemeral model is inlined into *each* downstream model separately,
the compiled SQL grows linearly with the number of dependents. A wide ephemeral CTE referenced by
20 models is re-computed 20 times and bloats `run.sql`.

**When to use it:** small dimension lookups (a static mapping table, a currency-code list, a
status decoder); logic reused a *handful* of times where the source is cheap to scan; a "macro"
you want to version-control but not materialize.

**When it hurts:** a wide, expensive CTE referenced by many models; a model whose source is large
(ephemeral forces a re-scan of the base table, not a read of a small pre-aggregated table);
anything you need to query independently.

💡 **The decision rule:** if a source table is scanned more than ~3 times across the DAG because
of an ephemeral model, materialize it. Ephemeral is for *cheap* and *narrow*, not for *shared*.

### `type: "incremental"` → `CREATE OR REPLACE TABLE` + `MERGE`

The most complex strategy, and the subject of the next chapter. In short: the table is created if
it doesn't exist, and on subsequent runs only *new or changed* rows are merged in.

```sql
-- First run: table doesn't exist → plain CREATE TABLE AS
CREATE OR REPLACE TABLE `my-project.analytics.fct_sales` AS SELECT ... WHERE ...;

-- Subsequent runs: table exists → MERGE
MERGE `my-project.analytics.fct_sales` AS D
USING (SELECT ... WHERE updated_at > (SELECT MAX(updated_at) FROM `my-project.analytics.fct_sales`)) AS S
ON D.id = S.id
WHEN MATCHED THEN UPDATE SET ...
WHEN NOT MATCHED THEN INSERT (...) VALUES (...);
```

**Cost profile:** on a steady-state daily run you scan only the *new* slice of the source — often
10× to 1000× less bytes scanned per run.

**When to use it:** the table grows unboundedly (fact tables, event logs, append-only history); the
source is expensive to re-scan; the table is queried often. **Full treatment in Lecture 2.2.**

### Cost comparison — the same daily sales aggregate, four ways

Assume `raw.sales` holds **1.2 TB** compressed (~180 GB/day of new rows), the daily aggregate
produces **~4,000 rows / ~300 KB**, the view runs **60 times/day**, and 30 days are retained.

```
┌─────────────┬──────────────────┬──────────────────┬────────────┬──────────────┐
│ Strategy    │ Scanned/run      │ Scanned/day      │ Storage    │ Freshness    │
├─────────────┼──────────────────┼──────────────────┼────────────┼──────────────┤
│ table       │ 1.2 TB           │ 1.2 TB           │ ~9 MB      │ stale until │
│             │                  │                  │ (30d×300KB)│ run ends     │
├─────────────┼──────────────────┼──────────────────┼────────────┼──────────────┤
│ view        │ 1.2 TB (on read) │ 1.2 TB × 60 =    │ 0          │ always live  │
│             │                  │ 72 TB            │            │              │
├─────────────┼──────────────────┼──────────────────┼────────────┼──────────────┤
│ incremental │ 180 GB           │ 180 GB           │ ~9 MB      │ updated on   │
│             │ (+4.7 GB MERGE)  │                  │            │ run          │
├─────────────┼──────────────────┼──────────────────┼────────────┼──────────────┤
│ ephemeral   │ 1.2 TB inlined   │ depends on       │ 0          │ always live  │
│ (nonsensical│ into every       │ downstream       │            │              │
│  here)      │ dependent)       │ query            │            │              │
└─────────────┴──────────────────┴──────────────────┴────────────┴──────────────┘
```

⚠️ **The view's 72 TB/day figure is the number to remember.** A view is not "free storage" — it is
"you re-pay for the computation on every single read." Materializing that view into a `table`
turns 72 TB/day of scanning into 1.2 TB/day plus a trivial 9 MB read. That is the whole argument.

💡 **A view is only cheaper than a table when reads are rare AND the source is small.** If
`reads-per-day × source-size > rebuild-cost`, materialize.

### `CREATE OR REPLACE TABLE` is atomic

A `table` model never exposes a half-built result to a reader.

```
   Time ──────────────────────────────────────────────────────────────▶

   t0:  Table fct_sales exists with 4000 rows (version A)
   t1:  dataform runs the CREATE OR REPLACE TABLE ...
   t2:  BigQuery builds the new table (version B) — in a staging area
   t3:  Build succeeds
   t4:  ATOMIC SWAP: fct_sales now points to version B
   t5:  Old version A dropped (recoverable ~7 days via time travel / snapshot)

   A reader at any moment sees EITHER version A OR version B.
   A reader NEVER sees "3,200 of 4,000 rows".
```

If the build fails at t3 (type error, OOM), the table is **untouched** — the original still holds
yesterday's data and the pipeline fails loudly. No truncation, no empty table.

⚠️ **The important caveat:** atomicity does **not** mean cheapness. BigQuery still has to *build*
the entire replacement table before the swap. A 1 TB `CREATE OR REPLACE TABLE` costs the full
write, full scan, and full recompute every run. Atomic ≠ incremental.

💡 **This is also why `CREATE OR REPLACE TABLE` is safe for concurrent readers.** A BI tool polling
`fct_sales` every minute sees a consistent snapshot at every instant, never a torn read.

### Physical table config: partitioning, clustering, keys, labels

Beyond `type`, the `config` block shapes the physical table.

#### `partitionBy`

```sqlx
config { type: "table", partitionBy: { ts: "DATE(ts)" } }
```

`partitionBy` accepts a map of `column -> partition expression`:

| Expression | Partitioning | Typical use |
|---|---|---|
| `DATE(ts)` | Day-level | Event/fact tables with a timestamp |
| `DATE_TRUNC(ts, MONTH)` | Month-level | Monthly aggregates, wide event tables |
| `DATE_TRUNC(ts, YEAR)` | Year-level | Very large archive tables |
| `TIMESTAMP_TRUNC(ts, DAY)` | Timestamp (millisecond) | High-precision event logs |
| `DATE(ts, 'UTC')` | Day-level with timezone | Cross-timezone reporting |

```sqlx
// Month-partitioned fact table
config {
  type: "incremental",
  partitionBy: { order_date: "DATE(order_date)" },
  uniqueKey: "id"
}
```

💡 **Partition by the column your queries filter on most often.** Partitioning by a column nobody
filters on is pure overhead.

⚠️ **Partitioning does not reduce storage bytes** — it reduces *bytes scanned* by enabling pruning.
A partitioned 1 TB table still costs 1 TB of storage.

#### `clusterBy`

```sqlx
config {
  type: "table",
  partitionBy: { sale_date: "DATE(sale_date)" },
  clusterBy: ["customer_id", "region"]
}
```

Clustering sorts data within each partition by the given columns. BigQuery's clustering is "loose"
— it doesn't guarantee full ordering, but it co-locates matching values, letting BigQuery apply
**cluster filters** to skip blocks.

| | Partitioning | Clustering |
|---|---|---|
| Granularity | One partition = one discrete value | Sorting keys within a partition |
| Max columns | 1 | Up to 4 |
| Pruning | Partition filter | Block-level cluster filter |
| Best for | Date-based facts | High-cardinality dimensions (customer_id) |

💡 **Partition + cluster is the standard fact-table pattern:** partition by date for time-range
pruning, cluster by the dimension you'll join and filter on.

#### `uniqueKey`

```sqlx
config { type: "incremental", uniqueKey: "id" }
```

`uniqueKey` names the column (or comma-separated columns) that uniquely identifies a row. For
incremental models it **switches the generated statement from `INSERT` to `MERGE`**, and it is what
makes the merge idempotent. Composite keys use a comma-separated string:

```sqlx
config { type: "incremental", uniqueKey: "store_id,transaction_id" }
```

⚠️ **`uniqueKey` must actually be unique in the source.** If it isn't, the `MERGE` may error
("MERGE statement matched multiple rows") or produce nondeterministic results. Dataform's
`uniqueKey` assertion (Lecture 2.3) exists to catch this.

#### `labels`

```sqlx
config {
  type: "table",
  labels: { team: "analytics", domain: "sales", tier: "gold", cost_center: "CC-4417" }
}
```

Labels propagate to BigQuery as table labels, driving **billing attribution** (per-label slot
pricing) and **dataset-level governance**. 💡 Label every table at creation — retroactive
labelling is painful.

#### `transitive`

```sqlx
config { type: "table", transitive: true }
```

By default `transitive: false` means only **direct** dependencies matter for invalidation. Setting
`transitive: true` makes Dataform rebuild the model when **any** transitive dependency changes:

```
  stg_orders ──▶ int__enriched ──▶ fct_sales

  transitive: false → stg_orders changes?  NO
  transitive: true  → stg_orders changes?  YES
```

💡 **Use `transitive: true` sparingly.** It maximizes freshness but multiplies rebuild cost across
the DAG. Right for small, high-value aggregates; wasteful for large ones.

### The staging → intermediate → mart convention

Teams past a handful of models converge on three layers. Each layer has **exactly one job**, and
the layer boundary is where that job ends.

```
   RAW / SOURCE          External systems. No logic. No renames. Read-only.
   raw.orders            Owned by the source team.
        │ source()
        ▼
   STAGING (stg_*)       ONE JOB: clean and conform.
                         • canonical renaming • correct casts
                         • drop unwanted columns • de-duplicate identical rows
                         • NO business logic, NO joins, NO aggregation
   stg_orders, stg_customers, stg_products
        │ ref()
        ▼
   INTERMEDIATE (int_*)  ONE JOB: reshape and combine.
                         • join staging models • dedupe on a business key
                         • business rules • fan out / explode / enrich
   int__customer_labels, int__order_items_enriched
        │ ref()
        ▼
   MART (fct_*, dim_*)   ONE JOB: present for consumption.
                         • aggregate to the dashboard's grain
                         • star-schema naming • final metric definition
   fct_sales, dim_customers, agg_daily_revenue
```

**Why the boundaries exist:**

| Boundary reason | Explanation |
|---|---|
| **Debuggability** | A wrong number in a mart → check intermediate → check staging → check raw. Each layer is a place the bug can *live*. |
| **Reuse** | `stg_customers` is cleaned once and reused by 12 models; cleaning logic lives in one place. |
| **Cost control** | Staging reads raw once/day. Intermediate joins cleaned data (cheap), not raw (expensive). |
| **Blast radius** | A staging change invalidates everything downstream — you *want* to know that. |
| **Parallelism** | Independent models within a layer run concurrently; flat staging layers maximize it. |
| **Ownership** | Raw = source team. Staging = platform team. Marts = analytics team. |

⚠️ **The most common layering violation:** putting business logic in staging (e.g. computing
`lifetime_value` in `stg_customers`). Staging must stay a faithful, lossless representation of
the source, or you cannot rebuild the mart from raw without silently inheriting old logic.

💡 **A layer boundary is also a contract.** If `stg_orders` guarantees "one row per order id,
`amount` is a non-null float64, timestamps are UTC", downstream models can rely on those guarantees
without re-checking. Write them down as assertions (Lecture 2.3).

## 🛠️ Hands-On: Compare the Four Types

### Step 1 — Four models, four types

All four read the same cleaned source and produce the same daily aggregate.

```sqlx
// definitions/staging/stg_orders.sqlx
config {
  type: "table",
  partitionBy: { order_date: "DATE(order_date)" },
  clusterBy: ["customer_id"],
  labels: { team: "analytics", layer: "staging" }
}

SELECT
  id                   AS order_id,
  customer_id,
  amount               AS order_amount,
  'complete'           AS order_status,
  TIMESTAMP(order_ts)  AS updated_at,
  DATE(order_ts)       AS order_date
FROM ${source("raw", "orders")}
WHERE order_status != 'cancelled'
```

```sqlx
// definitions/marts/v_daily_sales.sqlx      ← type: "view"
config { type: "view" }

SELECT order_date AS sale_date,
       COUNT(DISTINCT order_id) AS order_count,
       SUM(order_amount)        AS total_amount
FROM ${ref("stg_orders")}
GROUP BY order_date
```

```sqlx
// definitions/marts/tbl_daily_sales.sqlx    ← type: "table"
config { type: "table", partitionBy: { sale_date: "DATE(sale_date)" } }

SELECT order_date AS sale_date,
       COUNT(DISTINCT order_id) AS order_count,
       SUM(order_amount)        AS total_amount
FROM ${ref("stg_orders")}
GROUP BY order_date
```

```sqlx
// definitions/marts/inc_daily_sales.sqlx    ← type: "incremental"
// same SELECT body as tbl_daily_sales, different config
config {
  type: "incremental",
  uniqueKey: "sale_date",
  partitionBy: { sale_date: "DATE(sale_date)" }
}

SELECT order_date AS sale_date,
       COUNT(DISTINCT order_id) AS order_count,
       SUM(order_amount)        AS total_amount
FROM ${ref("stg_orders")}
GROUP BY order_date
```

### Step 2 — Compile and inspect what each type produced

```bash
dataform compile

grep -A 12 "stg_orders"      .dataform/run.sql | head -30
grep -A 20 "inc_daily_sales" .dataform/run.sql | head -40
```

```
stg_orders      → CREATE OR REPLACE TABLE ... PARTITION BY DATE(order_date) CLUSTER BY customer_id
v_daily_sales   → CREATE OR REPLACE VIEW ...
tbl_daily_sales → CREATE OR REPLACE TABLE ... PARTITION BY DATE(sale_date)
inc_daily_sales → CREATE TABLE IF NOT EXISTS ... ; MERGE ... ON D.sale_date = S.sale_date
```

### Step 3 — Measure the cost of each

```bash
bq query --use_legacy_sql=false --dry_run --format=json \
  'SELECT * FROM `my-project.analytics.v_daily_sales` WHERE sale_date = "2024-06-01"' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('bytes:', d['statistics']['query']['totalBytesProcessed'])"

bq query --use_legacy_sql=false --dry_run --format=json \
  'SELECT * FROM `my-project.analytics.tbl_daily_sales` WHERE sale_date = "2024-06-01"' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('bytes:', d['statistics']['query']['totalBytesProcessed'])"
```

```
view  read  → bytes: 4949931520     (~4.9 GB — it re-aggregates stg_orders)
table read → bytes: 311296          (~304 KB — it reads one partition)
```

That ~16,000× difference is the entire materialization argument, in one number.

### Step 4 — Verify the ephemeral inlining

```sqlx
// definitions/marts/int__customer_labels.sqlx
config { type: "ephemeral" }

SELECT customer_id,
       CASE WHEN total_spend > 5000 THEN 'platinum'
            WHEN total_spend > 500  THEN 'gold'
            ELSE 'standard' END AS segment
FROM ${ref("stg_orders")}
GROUP BY customer_id, total_spend
```

A second model (`fct_customer_orders`) joins it with
`LEFT JOIN ${ref("int__customer_labels")} AS l USING (customer_id)`.

```bash
dataform compile
grep -B2 -A 14 "int__customer_labels AS" .dataform/run.sql
```

```
WITH
  int__customer_labels AS (
    SELECT customer_id,
           CASE WHEN total_spend > 5000 THEN 'platinum'
                WHEN total_spend > 500  THEN 'gold'
                ELSE 'standard' END AS segment
    FROM `my-project.analytics.stg_orders`
    GROUP BY customer_id, total_spend
  )
SELECT ...
```

No `CREATE TABLE` anywhere for that model. Add a third downstream model that also refs it,
recompile, and watch the CTE appear a second time in a different statement.

### Step 5 — Confirm atomicity

```bash
# Introduce a deliberate type error in stg_orders, then:
dataform run --nodes stg_orders
```

```
ERROR: Value of type STRING cannot be assigned to INT64 field updated_at
```

```bash
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `my-project.analytics.stg_orders`'
```

```
+----------+
| count    |
+----------+
| 5000     |   ← still the previous version. No truncation, no empty table.
+----------+
```

---

## 🔑 Key Takeaways

- The four types are `table`, `view`, `incremental`, `ephemeral` — the choice drives cost, freshness, and failure behavior.
- `table` → `CREATE OR REPLACE TABLE`: stored, full rebuild every run, cheapest to read.
- `view` → `CREATE OR REPLACE VIEW`: stores nothing, but **re-runs the whole query and re-bills the bytes on every read**. A view read 60×/day over a 1.2 TB source costs 72 TB/day of scanning.
- `ephemeral` → **not materialized at all**; inlined as a CTE into every downstream model. Zero storage, but the computation is duplicated per dependent and the compiled SQL grows.
- `incremental` → `CREATE OR REPLACE TABLE` + `MERGE` (with `uniqueKey`) or `INSERT` (without). Covered fully in Lecture 2.2.
- `CREATE OR REPLACE TABLE` is **atomic** in BigQuery: readers see the old table or the new one, never a partial write. But atomic ≠ cheap — the full rebuild still happens.
- Partitioning reduces **bytes scanned**, not storage. `partitionBy` takes BigQuery partition expressions: `DATE(ts)`, `DATE_TRUNC(ts, MONTH)`, `TIMESTAMP_TRUNC(ts, DAY)`.
- `clusterBy` (up to 4 columns) sorts within a partition for block-level pruning — use it for the high-cardinality dimension you join on.
- `uniqueKey` both enables the `MERGE` path and declares row identity. It must actually be unique.
- `labels` drive billing attribution and governance; `transitive: true` rebuilds on any transitive change — powerful, but it multiplies rebuild cost.
- **Layer boundaries exist so each layer has one job**: staging cleans, intermediate reshapes, marts present. Debuggability, reuse, and cost control all follow from that.
- Default to `table`. Use `view` only when reads are rare and the source is small; use `ephemeral` only for small, cheap lookups reused a handful of times.

---

## 📚 Practice Exercises

1. **Materialization audit.** Take a real project (or a public BigQuery dataset) and classify
   every model as table / view / incremental / ephemeral. For each `view`, compute
   `reads_per_day × source_bytes_scanned` versus the cost of materializing. Produce a one-page
   recommendation with the top three changes ranked by dollars saved.

2. **The ephemeral decision.** Write two versions of the same 12-column customer enrichment CTE
   — one `ephemeral`, one `table` — plus **three** downstream models that reference it. Compile
   both, and report: (a) how many times does the CTE appear in each `run.sql`? (b) how many bytes
   are scanned at run time in each design? (c) at what number of downstream models does ephemeral
   become more expensive than the table version?

3. **Partition pruning detective.** Create a partitioned `stg_orders` table, then write two views
   over it: one that filters on the partition column directly, one that wraps it in
   `DATE_ADD(order_date, INTERVAL 1 DAY)`. Use `EXPLAIN` on both and identify which one loses
   partition pruning. Explain *why* in terms of predicate pushdown, and describe the two other
   view shapes that commonly defeat pruning (one join shape, one `OR` shape).

4. **Atomicity proof.** Write a `table` model, run it successfully, then introduce an error that
   fails *after* the SELECT begins (e.g. a `CAST` that overflows on one row). Run it and query the
   table. Prove the previous version survived intact with no partial rows exposed. Then explain
   why `MERGE`-based incremental models behave *differently* on failure (and what that means for a
   `DELETE`+`INSERT` incremental).

---

## 📖 Further Reading

- Dataform SQLX reference — https://cloud.google.com/dataform/docs/reference/sqlx
- Dataform configuration reference — https://cloud.google.com/dataform/docs/reference/workflow-configuration
- BigQuery partitioned tables — https://cloud.google.com/bigquery/docs/partitioned-tables
- BigQuery clustering — https://cloud.google.com/bigquery/docs/clustered-tables
- BigQuery views and materialized views — https://cloud.google.com/bigquery/docs/views-intro
- BigQuery best practices — https://cloud.google.com/bigquery/docs/best-practices
- BigQuery cost optimization — https://cloud.google.com/bigquery/docs/best-practices-cost-optimization
