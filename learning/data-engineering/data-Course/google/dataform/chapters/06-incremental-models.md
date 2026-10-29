# 2.2 — Incremental Models

> **Section 2 · Modeling · Lecture 2.2 · 22:10**

## 🎯 What you will learn

- How `incremental` models differ from full-rebuild tables, and the two strategies Dataform generates
- The `merge` strategy (`uniqueKey` → `MERGE`) vs the `insert` strategy (no `uniqueKey` → `INSERT`)
- What `self()` actually returns, and why using it in a `WHERE` clause is safe
- The late-arriving data problem and how to choose a lookback window
- Why idempotency makes a lookback window safe to re-process
- The danger of `DELETE` + `INSERT` on a partitioned table
- `partitionBy`, `partition_expiration_days`, and how assertions guard incremental runs

---

## 🧠 Concept

### Why incremental exists

A full-rebuild table re-scans its entire source and rewrites its entire output, every run. For a
table that grows without bound, that cost grows with the table — and eventually the daily rebuild
costs more than the compute it produces.

An incremental model asks a different question: **"what changed since last time?"**

```
FULL REBUILD (type: "table")
  Run 1:  scan 1 TB  →  write 100 GB
  Run 4:  scan 4 TB  →  write 400 GB      ← source grows, cost grows

INCREMENTAL (type: "incremental")
  Run 1:  scan 1 TB   →  write 100 GB     (initial load)
  Run 2+: scan 180 GB →  merge 18 GB      ← only the new slice; cost stays flat
```

### The two strategies

Dataform generates **one of two statements** for an incremental model, decided by whether you set
`uniqueKey` — or stated explicitly with `incrementalStrategy`.

| | `merge` strategy | `insert` strategy |
|---|---|---|
| Triggered by | `uniqueKey` set, or `incrementalStrategy: "MERGE"` | No `uniqueKey`, and no `incrementalStrategy` |
| Generated SQL | `MERGE target AS D USING source AS S ON ...` | `INSERT INTO target (cols) SELECT ...` |
| Existing key | `WHEN MATCHED THEN UPDATE` | Row appended (duplicate) |
| New key | `WHEN NOT MATCHED THEN INSERT` | Row appended |
| Idempotent? | **Yes** | **No** — reruns duplicate rows |
| Correct for updates | Yes (late data, corrections) | No |
| Key must be unique | Yes | No |

💡 **Dataform exposes the strategy explicitly.** The `incrementalStrategy` config key takes
`"MERGE"` or `"INSERT_OVERWRITE"`:

| `incrementalStrategy` | Behavior |
|---|---|
| `"MERGE"` | Matches rows on `uniqueKey` — update existing, insert new. **Requires `uniqueKey`.** |
| `"INSERT_OVERWRITE"` | Replaces whole partitions present in the new data. **Requires `partitionBy`.** |
| *(unset)* | Defaults to `MERGE` if `uniqueKey` is configured, append otherwise |

```sqlx
config {
  type: "incremental",
  uniqueKey: ["id"]
  // incrementalStrategy is inferred as MERGE from uniqueKey
}
```

⚠️ **The compiler enforces both requirements.** `MERGE` without a `uniqueKey`, or
`INSERT_OVERWRITE` without a `partitionBy`, is a compile error — not a runtime surprise.

```
MERGE (with uniqueKey)
  MERGE `prod.fct_sales` AS D
  USING (SELECT ... FROM src WHERE updated_at > (SELECT MAX(updated_at) FROM `prod.fct_sales`)) AS S
  ON D.id = S.id
  WHEN MATCHED THEN UPDATE SET D.amount = S.amount, D.updated_at = S.updated_at
  WHEN NOT MATCHED THEN INSERT (id, amount, updated_at) VALUES (S.id, S.amount, S.updated_at);

INSERT (no uniqueKey)
  INSERT INTO `prod.fct_sales` (id, amount, updated_at)
  SELECT ... FROM src WHERE updated_at > (SELECT MAX(updated_at) FROM `prod.fct_sales`);
```

⚠️ **An `INSERT`-based incremental is not idempotent.** If the pipeline runs twice — a retry, a
backfill, a manual re-run — you get duplicate rows. That is why `uniqueKey` is not optional
decoration: it is what makes the model safely re-runnable.

💡 **Default to `merge`.** Only use `insert` when rows are strictly append-only (a raw event log
where no row is ever updated) and you control the run schedule tightly enough to guarantee no
double-runs.

### `incremental()` and the `when()` idiom

The subtlety with an incremental model is that its SQL must work **twice**: once for the initial
load, and once for every subsequent run. The filter that restricts to "new data" must be
**inactive** on the first run — otherwise the table would only ever contain the last slice.

Dataform exposes this with the `incremental()` helper, combined with `when(cond, trueCase, falseCase?)`:

| Helper | Returns |
|---|---|
| `incremental()` | `true` when the model already exists (not the first run) |

⚠️ **There is no `is_incremental()` in Dataform** — that's the dbt spelling. Dataform's helper is
`incremental()`, used as `${when(incremental(), "...")}`.

The canonical idiom combines them with `when()`:

```sqlx
config {
  type: "incremental",
  uniqueKey: ["id"]
}

SELECT
  id,
  customer_id,
  amount,
  updated_at
FROM ${ref("raw_orders")}
WHERE
  ${when(incremental(), "updated_at > (SELECT MAX(updated_at) FROM ${self()})")}
```

`${when(condition, trueValue, falseValue)}` emits the `trueValue` string when `condition` is
true, and the `falseValue` (or nothing) when it is false. So the compiled SQL is:

```sql
-- FIRST RUN (table does not exist → incremental() is false)
-- The entire WHERE clause disappears. The table gets a full load.
SELECT id, customer_id, amount, updated_at FROM `raw.orders`;

-- SUBSEQUENT RUNS (table exists → incremental() is true)
-- The predicate is injected, restricting to rows newer than the table's max.
SELECT id, customer_id, amount, updated_at FROM `raw.orders`
WHERE updated_at > (SELECT MAX(updated_at) FROM `prod.fct_orders`);
```

This is why the `when()` wrapper matters: **a bare `WHERE updated_at > (SELECT MAX(...) FROM
${self()})` would fail on the first run** because `self()` points at a table that doesn't exist
yet.

### What `self()` returns, and why it's safe

`${self()}` resolves to the **fully-qualified name of the model being defined**. For a model
named `fct_orders` in project `my-project` and dataset `analytics`:

```
${self()}  →  `my-project.analytics.fct_orders`
```

Inside the model's own SQL, it refers to the table as it exists *right now* — the output of the
previous run.

**Why is using `self()` in a `WHERE` clause safe?**

1. **It only executes on incremental runs.** The `when()` guard means the predicate is absent on
   the first run, so `self()` never references a non-existent table.
2. **It reads a consistent snapshot.** BigQuery evaluates the subquery against the table's state
   at query start, and the `MERGE` that follows uses that same snapshot.
3. **It's a read of the target, not a write.** The subquery is evaluated once as part of the
   source query feeding the `MERGE`; it doesn't race with the merge itself.
4. **It's deterministic within a run.** Two identical runs against an unchanged source produce
   the same watermark.

⚠️ **The real danger is not `self()` — it's a source with no monotonic `updated_at`.** If
`updated_at` can go *backwards* (a backfill sets an old timestamp), `MAX(updated_at)` may exceed
the timestamp of rows you haven't processed yet, and those rows will never be picked up.

⚠️ **`MAX()` also misses ties.** If 500 rows share the exact same `updated_at` as the current
maximum, and only some were processed, the next run's `> MAX(...)` skips the rest. This is the
classic "watermark boundary bug" — and the reason the lookback window below exists.

### The alternative: an explicit watermark

The `MAX(updated_at)` approach derives the watermark from the data itself. The alternative is to
**store the watermark explicitly**, either in `vars` or in a dedicated table.

```sqlx
// definitions/marts/fct_orders.sqlx
config {
  type: "incremental",
  uniqueKey: ["id"]
}

SELECT id, customer_id, amount, updated_at
FROM ${ref("raw_orders")}
WHERE updated_at > ${vars("last_run_ts")}
```

```json
// definitions/vars.sqlx
vars {
  last_run_ts: "TIMESTAMP('2024-06-01 00:00:00')"
}
```

**A dedicated `last_run` table** is the more robust version:

```sqlx
// definitions/marts/fct_orders.sqlx
config { type: "incremental", uniqueKey: ["id"] }

SELECT id, customer_id, amount, updated_at
FROM ${ref("raw_orders")}
WHERE updated_at > (SELECT last_watermark FROM ${ref("ops_last_run")})
```

```sqlx
// definitions/operations/ops_last_run.sqlx
config { type: "table" }

SELECT
  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY) AS last_watermark,
  CURRENT_TIMESTAMP()                                 AS recorded_at
```

| Watermark approach | Pros | Cons |
|---|---|---|
| `MAX(updated_at)` from `self()` | Zero extra infrastructure; self-maintaining | Ties can drop rows; needs monotonic source timestamps |
| `vars` value | Simple; version-controlled | Must be bumped out-of-band; drifts from reality |
| `last_run` table | Explicit and auditable | Extra model to maintain; must be updated with the merge |

💡 **The `vars` approach is brittle in production** because a value committed to git is a value
someone has to remember to bump. The `self()` approach is self-maintaining. The `last_run` table
is the best of both, at the cost of complexity — reserve it for pipelines where you need to resume
from a specific point or where the source timestamp is not monotonic.

### The late-arriving data problem

Real-world event streams are not ordered. An event that happened at 10:00 may not arrive in the
raw table until 10:30 — or until the next day.

```
  10:00  event A arrives   ─┐
  10:05  event B arrives    │  Run at 11:00 → MAX(updated_at) = 10:30
  10:30  event C arrives   ─┘  All three processed ✓

  14:00  Run at 15:00. MAX(updated_at) = 10:30.
         Event D arrives with updated_at = 10:15  ← LATE, and OLDER than the watermark!
         Condition: updated_at > 10:30  →  FALSE
         → Event D is NEVER processed. ⚠️ SILENT DATA LOSS
```

This is the single most common failure mode of incremental pipelines, and it is **silent** — the
pipeline succeeds, the table looks healthy, and rows are quietly missing.

### The lookback window

The fix is to **re-read a window of already-processed data** and let the `MERGE` handle the
duplicates:

```sqlx
config { type: "incremental", uniqueKey: ["id"] }

SELECT id, customer_id, amount, updated_at
FROM ${ref("raw_orders")}
WHERE
  ${when(
    incremental(),
    "updated_at > (SELECT MAX(updated_at) - INTERVAL 7 DAY FROM ${self()})"
  )}
```

**Why this is safe — the idempotency argument.** The lookback window *will* re-process rows that
were already handled. That's fine, because the `MERGE` matches on `uniqueKey`: matched rows are
**updated**, not inserted, so the final state is identical to processing each row exactly once.
Re-processing is **idempotent** — correctness is preserved; only a little extra compute is spent.

⚠️ **This only works with `merge`.** With an `insert`-based incremental, the lookback window
would duplicate every row in the window on every run. **Lookback + insert = guaranteed duplicate
rows.**

💡 **The lookback window must be at least as long as your maximum lateness.** If events can be
up to 3 days late, the window must be ≥ 3 days, plus a safety margin. If you're not sure, use 7.

### The late data / correctness window trade-off

| Lookback window | Rows/run | Cost | Risk of missing late data | Duplicate risk |
|---|---|---|---|---|
| 0 (pure watermark) | Minimum | Cheapest | **High** — late rows lost forever | None |
| 1 day | 1× daily | Low | Moderate | Low |
| **7 days** | 7× daily | Moderate | **Low** — covers a week of lateness | Low |
| 30 days | 30× daily | Expensive | Very low | Low |
| 90 days | 90× daily | Very expensive | Near zero | Low |

⚠️ **A longer window is not free.** The cost of the lookback scales with the window. If daily
volume is 180 GB, a 7-day window means ~1.26 TB scanned per run — most of which produces rows
that already exist and get no-op updated.

💡 **Balance the two sides against the facts you actually have:** measure your source's lateness
distribution (compare `event_time` to `arrival_time` in your raw table) and set the window to the
99th percentile plus margin. If you don't have that data, start with 7 days and add an assertion
that watches for suspiciously old rows.

### Idempotency: the property that makes everything safe

**Idempotent** = applying the operation N times has the same effect as applying it once.

| Operation | Idempotent? | Notes |
|---|---|---|
| `CREATE OR REPLACE TABLE` | Yes | Atomic swap; result is a pure function of the SQL |
| `MERGE` on a unique key | **Yes** | Matched → update to same values; unmatched → insert once |
| `INSERT` | **No** | Each run appends again |
| `DELETE` + `INSERT` | Yes, but expensive | See below |

Idempotency is what lets you safely retry a failed job, safely re-run a backfill, and safely use a
lookback window. It is the property that separates a pipeline you can operate from one you fear.

### The danger of `DELETE` + `INSERT` incremental

There's a tempting pattern for partitioned incremental models: delete the partitions you're about
to rewrite, then insert fresh. It looks clean:

```sql
-- ⚠️ THIS PATTERN IS DANGEROUS ON A PARTITIONED TABLE
DELETE FROM `prod.fct_sales`
WHERE sale_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);

INSERT INTO `prod.fct_sales` (sale_date, order_id, amount)
SELECT sale_date, order_id, amount
FROM src
WHERE sale_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);
```

The problem: **`DELETE` on a partitioned BigQuery table does not just remove rows.** It
**rewrites the entire table's metadata and rewrites every partition that remains.** BigQuery
charges you for the bytes of the partitions affected, and the deletion itself is a full
metadata operation.

```
Table: 365 daily partitions, 12 months of history
DELETE ... WHERE sale_date >= (today - 30 days)
  → touches 30 partitions, but BigQuery rewrites the *entire table's* partition metadata
  → every remaining partition's metadata is regenerated, then the INSERT re-adds 30 partitions

Cost: metadata rewrite (all 365 partitions) + 30 partitions re-written
      vs. MERGE with uniqueKey → only the affected rows are touched
```

⚠️ **On a large partitioned table, `DELETE` + `INSERT` can cost more than the full rebuild it was
meant to avoid.** And it destroys the table's history if the INSERT then fails — you've deleted
30 days of data and replaced it with nothing.

💡 **Use `MERGE` with a `uniqueKey`.** It achieves the same "overwrite" semantics without the
partition rewrite, and it doesn't destroy history on failure. `DELETE` + `INSERT` is acceptable
only on a small, non-partitioned table.

💡 **Better still: use the built-in `INSERT_OVERWRITE` incremental strategy.** Dataform exposes
an explicit strategy, so you never have to hand-write the `DELETE`:

```sqlx
config {
  type: "incremental",
  incrementalStrategy: "INSERT_OVERWRITE",
  bigquery: {
    partitionBy: "DATE(order_date)",
    updatePartitionFilter: "order_date = @order_date"
  }
}
```

⚠️ **`INSERT_OVERWRITE` requires `partitionBy`** — the compiler errors without it. It replaces
whole partitions present in the new data, so it gives you partition-replace semantics without
the hand-written `DELETE` and its metadata-rewrite cost.

### `partitionBy` and expiration on incremental models

```sqlx
config {
  type: "incremental",
  uniqueKey: ["id"],
  partition_expiration_days: 90,
  require_partition_filter: true,
  bigquery: {
    partitionBy: "DATE(order_date)"
  }
}
```

| Config | Scope | Effect |
|---|---|---|
| `partition_expiration_days` | **Model config** (`.sqlx`) | BigQuery drops the partition N days after the data in it was last modified |
| `require_partition_filter` | **Model config** (`.sqlx`) | BigQuery rejects queries against the table without a partition filter |
| `update_partition_filter` | **Model config** (`.sqlx`) | The filter that selects which partitions an incremental run replaces |
| `incremental_predicates` | **Model config** (`.sqlx`) | Extra SQL predicates applied when incremental updates run |
| `labels` | **Model config** (`.sqlx`) | BigQuery table labels (billing attribution, governance) |
| `defaultAssertionDataset` | **`workflow_settings.yaml`** | The dataset where failing assertion rows are recorded (default `dataform_assertions`) |
| `defaultLocation` | **`workflow_settings.yaml`** | Location for datasets the project creates |
| `defaultProject` / `defaultDataset` | **`workflow_settings.yaml`** | Default target project and dataset |

⚠️ **There is no `table_expiration_days` model config, and no `bigquery` section in
`dataform.json`.** Partition expiration is a **model-level** config in the `.sqlx` file. The
workspace-level settings live in `workflow_settings.yaml` (or `dataform.json` in older CLI
versions), whose real keys are `defaultProject`, `defaultDataset`, `defaultLocation`,
`defaultAssertionDataset`, `namePrefix`, `projectSuffix`, `datasetSuffix`, and `vars`.

```yaml
# workflow_settings.yaml
defaultProject: my-project
defaultDataset: analytics
defaultLocation: US
defaultAssertionDataset: analytics_assertions
vars:
  last_run_ts: "TIMESTAMP('2024-06-01 00:00:00')"
```

💡 **`defaultAssertionDataset` is how assertion failures get recorded in BigQuery.** When an
assertion fails, Dataform writes the failing rows into this dataset so you can inspect them —
much better than just an error message.

💡 **`require_partition_filter` is a cost-control circuit breaker.** It makes BigQuery reject any
query against your table that doesn't filter on the partition column — so a stray `SELECT *` in a
BI tool can't quietly scan a terabyte.


### Assertions on incremental models

An incremental model needs *different* assertions than a full-rebuild model, because "the row
count should be 5000" is meaningless for a table that accumulates.

```sqlx
config {
  type: "incremental",
  uniqueKey: ["id"],
  assertions: {
    rowCount: { when: "incremental()", else: true },
    nonNull: ["id", "order_date"],
    uniqueKey: ["id"]
  }
}
```

| Assertion | What it checks on an incremental model |
|---|---|
| `rowCount: { when: "incremental()", else: true }` | On incremental runs, `true` means "row count > 0" (a run that added zero rows is suspicious). On the first (full) run, `else: true` applies |
| `nonNull: ["id", "order_date"]` | No nulls in `id` or `order_date` — catches null-key rows that break the `MERGE` |
| `uniqueKey: ["id"]` | `id` is genuinely unique — catches duplicate keys that make `MERGE` nondeterministic |

⚠️ **The `rowCount` assertion on an incremental model needs the `when`/`else` form.** A literal
`rowCount: true` would compare against a fixed expected count, which only makes sense for a
full-rebuild model.

💡 **Assert `nonNull` on the partition column and the `uniqueKey` columns specifically.** Those
are the fields where a null or duplicate causes a `MERGE` to fail or misbehave — and where the
failure is expensive to diagnose after the fact.

### Incremental run cost vs full rebuild

Concrete numbers for the daily sales fact table:

```
Source: raw.sales, 1.2 TB total, ~180 GB/day of new rows
Target: prod.fct_sales, 365 days retained, ~109 GB total

FULL REBUILD (type: "table")
  Scanned/run: 1.2 TB     Written/run: 109 GB   Billed/day: 1.31 TB
  Time to first row: ~11 min (full build before any data lands)   Idempotent: Yes

INCREMENTAL (uniqueKey: ["id"])
  Scanned/run: 180 GB     Written/run: 18 GB     Billed/day: 198 GB
  Time to first row: ~45 sec                      Idempotent: Yes (MERGE)

INCREMENTAL with 7-day lookback
  Scanned/run: 1.26 TB    Written/run: 18 GB     Billed/day: 1.28 TB
  ← 16% MORE than a full rebuild!   Late-data safety: ✓
```

⚠️ **Notice the last row.** With a 7-day lookback on a high-volume source, an incremental model
can cost *more* than a full rebuild, because the lookback re-reads data it will mostly discard.
That's an argument for measuring your actual lateness distribution and tuning the window — and for
making sure the source is partition-filtered so the lookback doesn't scan the whole source.

💡 **A 1-day lookback on this table gives 360 GB/day scanned** — 3.3× cheaper than a full rebuild
and still catches a day of late data. That is often the right operating point.

### Pre-hooks for insert-based incremental

If you *must* use an `insert`-based incremental (append-only source, strictly controlled
schedule), you can delete the affected partitions first with a **pre-hook**:

```sqlx
config {
  type: "incremental",
  bigquery: {
    partitionBy: "DATE(order_date)",
    },
pre_operations: [
    {
      "SELECT": "DELETE FROM ${self()} WHERE order_date = @partition_date"
    }
  ]
}
```

💡 **Pre-hooks run before the model's own SQL.** Dataform also supports `post_operations` for
anything that should run after.

⚠️ **But the metadata-rewrite cost still applies.** A pre-hook `DELETE` on a partitioned table
touches the whole table's metadata. Use it only where that cost is acceptable, and always prefer
`MERGE` when you have a reliable unique key.

---

## 🛠️ Hands-On: Build an Incremental Orders Model

### Step 1 — Declare the source and build the staging model

⚠️ **Dataform has no `source()` function** — a source is a `type: "declaration"` file, referenced
downstream with `ref()`:

```sqlx
// definitions/sources/raw_orders.sqlx
config {
  type: "declaration",
  database: "my-project",
  schema: "raw",
  name: "orders",
  description: "Raw orders table owned by the source system"
}
```

```sqlx
// definitions/staging/stg_orders.sqlx
config {
  type: "table",
  partitionBy: "DATE(order_date)"
}

SELECT
  id                   AS order_id,
  customer_id,
  amount               AS order_amount,
  'complete'           AS order_status,
  TIMESTAMP(order_ts)  AS updated_at,
  DATE(order_ts)       AS order_date
FROM ${ref("raw_orders")}
WHERE order_status != 'cancelled'
```

### Step 2 — The incremental fact model

```sqlx
// definitions/marts/fct_orders.sqlx
config {
  type: "incremental",
  uniqueKey: ["order_id"],
  bigquery: {
    partitionBy: "DATE(order_date)",
    },
partition_expiration_days: 90,
  assertions: {
    rowCount: { when: "incremental()", else: true },
    nonNull: ["order_id", "order_date"],
    uniqueKey: ["order_id"]
  }
}

SELECT
  order_id,
  customer_id,
  order_amount,
  order_date,
  updated_at
FROM ${ref("stg_orders")}
WHERE
  ${when(
    incremental(),
    "updated_at > (SELECT MAX(updated_at) - INTERVAL 7 DAY FROM ${self()})"
  )}
```

### Step 3 — Compile and read the generated SQL

```bash
dataform compile
grep -A 25 "fct_orders" .dataform/run.sql | head -45
```

```
MERGE `my-project.analytics.fct_orders` AS D
USING (
  SELECT order_id, customer_id, order_amount, order_date, updated_at
  FROM `my-project.analytics.stg_orders`
  WHERE updated_at > (SELECT MAX(updated_at) - INTERVAL 7 DAY FROM `my-project.analytics.fct_orders`)
) AS S
ON D.order_id = S.order_id
WHEN MATCHED THEN UPDATE SET
  D.customer_id = S.customer_id,
  D.order_amount = S.order_amount,
  D.order_date = S.order_date,
  D.updated_at = S.updated_at
WHEN NOT MATCHED THEN INSERT (order_id, customer_id, order_amount, order_date, updated_at)
VALUES (S.order_id, S.customer_id, S.order_amount, S.order_date, S.updated_at);
```

### Step 4 — Run it twice and prove idempotency

```bash
# First run: full load
dataform run --nodes fct_orders
bq query --use_legacy_sql=false   'SELECT COUNT(*) AS rows, COUNT(DISTINCT order_id) AS distinct_ids
   FROM `my-project.analytics.fct_orders`'
```

```
+------+--------------+------------+
| rows | distinct_ids | updated_at |
+------+--------------+------------+
| 5000 |        5000 | ...        |
+------+--------------+------------+
```

```bash
# Second run with no source changes: the MERGE reprocesses the lookback window,
# but every row matches → no duplicates
dataform run --nodes fct_orders
bq query --use_legacy_sql=false   'SELECT COUNT(*) AS rows FROM `my-project.analytics.fct_orders`'
```

```
+------+
| rows |
+------+
| 5000 |   ← unchanged. The MERGE was idempotent.
+------+
```

### Step 5 — Simulate a late-arriving row

```bash
# A row that arrives now but has an OLD timestamp (late data)
bq query --use_legacy_sql=false   'INSERT INTO `my-project.raw.orders`
   (id, customer_id, amount, order_ts, order_status)
   VALUES (99999, 42, 75.50, TIMESTAMP("2024-05-20 08:00:00"), "complete")'
```

```bash
# Without a lookback window it would NEVER be picked up.
# With the 7-day window it is merged in.
dataform run --nodes fct_orders

bq query --use_legacy_sql=false   'SELECT order_id, order_date FROM `my-project.analytics.fct_orders` WHERE order_id = 99999'
```

```
+----------+------------+
| order_id | order_date |
+----------+------------+
| 99999    | 2024-05-20 |
+----------+------------+
```

### Step 6 — Inspect the schema of the `self()` reference

```bash
bq query --use_legacy_sql=false   'SELECT column_name, data_type, is_nullable
   FROM `my-project.analytics.INFORMATION_SCHEMA.COLUMNS`
   WHERE table_name = "fct_orders"
   ORDER BY ordinal_position'
```

```
+-------------------+-----------+--------------+
| column_name       | data_type | is_nullable |
+-------------------+-----------+--------------+
| order_id          | INT64     | YES         |
| customer_id       | INT64     | YES         |
| order_amount      | FLOAT64   | YES         |
| order_date        | DATE      | YES         |
| updated_at        | TIMESTAMP | YES         |
+-------------------+-----------+--------------+
```

The `self()` subquery `(SELECT MAX(updated_at) FROM ...)` reads the `updated_at` column of this
same table — the previous run's output. Note `is_nullable` is `YES` here because `nonNull`
assertions run *after* the table is built, not as table constraints.

### Step 7 — Trigger an assertion failure

```bash
# Insert a duplicate order_id into the source
bq query --use_legacy_sql=false   'INSERT INTO `my-project.raw.orders`
   (id, customer_id, amount, order_ts, order_status)
   VALUES (99999, 42, 10.00, TIMESTAMP("2024-05-21 08:00:00"), "complete")'
```

```bash
dataform run --nodes fct_orders
```

```
ERROR: Assertion failed: uniqueKey
  Duplicate value found in column order_id: 99999
  Checked 5000 rows, found 1 duplicate.
```

The pipeline **failed loudly** instead of silently writing a bad row. That's the `uniqueKey`
assertion doing its job.

---

## 🔑 Key Takeaways

- An incremental model answers "what changed since last time?" — its cost stays flat as the table grows, while a full rebuild's cost grows linearly.
- Dataform generates a **`MERGE`** when `uniqueKey` is set, and an **`INSERT`** when it isn't. The `MERGE` path is idempotent; the `INSERT` path duplicates rows on re-run.
- `${when(incremental(), "...")}` emits the predicate only on incremental runs. Without it, a bare `self()` subquery would fail on the first run when the table doesn't exist.
- `${self()}` resolves to the model's own fully-qualified name — the output of the previous run. It's safe to read because the `when()` guard prevents it from executing before the table exists.
- The `MAX(updated_at)` watermark is simple but has a **tie bug**: rows sharing the exact max timestamp can be skipped forever.
- The **late-arriving data problem** is the silent killer of incremental pipelines — a row that arrives with a timestamp older than the watermark is never processed.
- The fix is a **lookback window** (`updated_at > MAX(updated_at) - INTERVAL 7 DAY`). It's safe because `MERGE` on `uniqueKey` makes re-processing idempotent.
- **Lookback + insert = guaranteed duplicates.** The lookback window depends on `merge`.
- A longer lookback is not free — on a 180 GB/day source, a 7-day window costs 1.28 TB/day, which can exceed a full rebuild.
- `DELETE` + `INSERT` on a partitioned BigQuery table rewrites the **entire table's partition metadata** and can cost more than a full rebuild — and destroys history if the insert fails.
- `partition_expiration_days` and `require_partition_filter` are **model-level** configs; workspace defaults like `defaultAssertionDataset` and `defaultLocation` live in **`workflow_settings.yaml`**. There is no `bigquery` section in `dataform.json` and no `table_expiration_days` model config.
- Incremental models need **different assertions**: `rowCount: { when: "incremental()", else: true }`, plus `nonNull` on the partition and key columns and `uniqueKey` for uniqueness.
- `defaultAssertionDataset` (default `dataform_assertions`) records assertion failures as rows in BigQuery so you can inspect what actually broke.
- A pre-hook `DELETE` before an append-based incremental is possible, but the metadata cost remains — prefer `MERGE`, or the built-in `incrementalStrategy: "INSERT_OVERWRITE"` (which requires `partitionBy`).

---

## 📚 Practice Exercises

1. **Watermark bug hunt.** Write an incremental model using the bare `MAX(updated_at)` watermark.
   Then seed your source with 10 rows that share the exact same `updated_at` timestamp, run the
   model, add one more row with that same timestamp, and run again. Show from the row counts which
   rows were missed. Then fix it with a lookback window and re-run to prove the rows are picked up.
   Explain precisely why the `>` comparison (rather than `>=`) causes this.

2. **Cost comparison, measured.** Build three versions of the same daily aggregate: a full-rebuild
   `table`, an `incremental` with no lookback, and an `incremental` with a 7-day lookback. Run each
   twice and record the actual `totalBytesProcessed` from the dry run and the wall-clock time.
   Produce a table of cost-per-day for each. Then vary the lookback to 1, 3, 7, and 30 days and
   plot the cost curve. Where does incremental stop being cheaper than a full rebuild in your data?

3. **Merge vs insert.** Create an incremental model with `uniqueKey` and a copy without it. Run the
   `insert` version twice and show the row count doubling. Then explain what would have to be true
   about your source for the `insert` strategy to be safe — and write down the operational
   controls (run triggers, retry policy, backfill procedure) that would make it acceptable.

4. **Expiration design.** Using `partition_expiration_days` and `require_partition_filter`,
   design a retention policy for a 3-year clickstream fact table that keeps 90 days of daily
   partitions and monthly partitions for the full 3 years. Write the `workflow_settings.yaml` and
   the model config. Then explain what BigQuery charges for and what it does *not* charge for when
   a partition expires, and how expired-partition billing differs between on-demand and capacity
   pricing.

---

## 📖 Further Reading

- Dataform incremental model configs — https://cloud.google.com/dataform/docs/reference/workflow-configuration
- Dataform SQLX reference (`incremental`, `self`, `when`) — https://cloud.google.com/dataform/docs/reference/sqlx
- BigQuery incremental load patterns — https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-csv
- BigQuery MERGE statement — https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax#merge_statement
- BigQuery partition expiration — https://cloud.google.com/bigquery/docs/partitioned-tables#partition-expiration
- BigQuery deleting table data — https://cloud.google.com/bigquery/docs/managing-tables#delete-data
- BigQuery storage costs and pricing — https://cloud.google.com/bigquery/pricing
