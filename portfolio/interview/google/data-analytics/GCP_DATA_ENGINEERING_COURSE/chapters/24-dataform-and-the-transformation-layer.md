# 5.5 — Dataform and the Transformation Layer

> **Section 5 · Processing & Orchestration · Lecture 5.5 · 8:00**

## 🎯 What you will learn

- Why transformation logic belongs in version-controlled SQL rather than in job code
- The transformation-layer taxonomy: raw, staging, intermediate, and mart
- Dataform's core objects: repositories, workspaces, tables, and connections
- The SQLX language: `config`, `ref`, `source`, `declare`, `is_incremental`, and variables
- Model types: view, table, incremental, and when each is right
- Incremental strategies: `insert_overwrite`, `merge`, and `unique_key`
- The compilation model and the SQL that actually runs
- Data quality tests: `unique`, `not_null`, `relationships`, `accepted_values`, and custom assertions
- The dependency graph, lineage, and incremental lineage
- Scheduling workflow executions
- How Dataform compares to dbt, and when you do not need either

---

## 🧠 Concept

### Why transformation logic should be SQL in version control

Consider the three places a transformation can live.

**In job code.** A Spark job, a Dataflow pipeline, or a shell script contains the logic. The logic is tested by running the job, reviewed by reading code, and versioned in the repository that holds the job. The problems:

- The logic is entangled with execution. You cannot easily ask "what would this transformation produce for yesterday's data?" without running it.
- Reviewing a change means reading imperative code and mentally simulating it.
- The logic is often duplicated between a batch job and a streaming job, and the copies drift.
- There is no cheap way to answer "which tables depend on this source?"

**In a spreadsheet.** Better for exploration, worse for production. No atomicity, no schema, no dependency tracking, no testing.

**In SQL, in version control, compiled by a tool.** The logic becomes a set of named models. A tool parses them, resolves their dependencies, generates concrete SQL per target, runs tests, and records lineage. You can review a diff that reads like SQL, and the tool can answer the dependency questions.

That third option is the transformation layer, and Dataform is Google Cloud's implementation of it.

### The layers

A well-shaped warehouse has a recognisable stack of layers. The naming varies, but the responsibilities do not:

| Layer | Contains | Schema | Write pattern |
|---|---|---|---|
| **Raw / Landing** | Exactly what arrived, plus ingestion metadata | Fixed by the source, or schemaless | Append only |
| **Staging / Intermediate** | Parsed, typed, deduplicated, still one-to-one with raw | Normalised and enforced | Append, usually partitioned by event date |
| **Mart / Consumption** | Joined, aggregated, business-meaningful | Denormalised and stable | Rebuild or incremental |
| **Serving** | Tables optimised for a specific consumer | Consumer-specific | Varies |

Two rules make the stack work:

1. **Each layer is derived only from the layer above.** A staging model reads raw. A mart reads staging. If a mart reads raw, the staging layer is doing nothing and you have a traceability problem.
2. **Raw is immutable.** Never transform a raw table in place. If the source system is wrong, you fix the pipeline that loads it, and the fix replays.

Dataform enforces rule 1 mechanically: `ref()` is the only way to reference another model, and the tool builds the graph from those references.

### Dataform's core objects

**Repository.** A Git repository holding your SQLX files. It is the unit of version control for your transformation logic. Dataform clones it, parses it, compiles it, and writes the results to a workspace.

**Workspace.** The compiled output: the generated SQL for every model, the dependency graph, the test results, and the metadata. It corresponds to a GCP project and a dataset.

**Connection.** A named connection to a data source — BigQuery, Cloud Storage, PostgreSQL, and others. Declared in the repository, referenced by `source()`. A connection lets you write source declarations that are portable across environments.

**Table.** The compiled model: its SQL, its dependencies, its tests, and its materialisation configuration. Dataform calls the compiled model a table even when it materialises as a view.

**Workflow execution.** An invocation of the compiled repository against a workspace. It compiles, runs the selected models, and runs their tests. This is the unit of "run the transformations".

The layering of these objects is what makes the tool useful: **repository → workspace → execution**. The repository holds logic, the workspace holds compiled state, the execution performs work.

### The SQLX language

SQLX is SQL with a small declarative layer bolted on. A file is one model.

```sql
config {
  type: "table",
  schema: "staging",
  description: "Validated, normalised events",
  tags: ["events", "daily"],
  dependencies: ["raw_events"],
  uniqueKey: "event_id",
  partitionBy: "event_date",
  bigquery: {
    partitionExpirationDays: 30,
    requirePartitionFilter: true,
    clusterBy: ["region", "event_type"]
  }
}

SELECT
  event_id,
  user_id,
  event_ts,
  DATE(event_ts) AS event_date,
  region,
  channel,
  currency,
  amount,
  amount * rate AS amount_eur
FROM ${ref("raw_events")}
WHERE amount IS NOT NULL
  AND amount >= 0
```

#### `config`

The `config` block declares metadata and materialisation behaviour. The keys that matter most:

- `type` — `view`, `table`, or `incremental`.
- `schema` — the BigQuery dataset the model lives in.
- `description` — the documentation that shows up in the Dataform UI and in Data Catalog. Write it.
- `tags` — how you filter models.
- `dependencies` — models this model depends on that are not visible via `ref()` or `source()`, for example because the dependency is applied through a UDF or a view created outside Dataform.
- `uniqueKey` — the column (or columns) that uniquely identifies a row. Required for `merge` incremental strategy.
- `partitionBy` — the partition expression.
- `bigquery.requirePartitionFilter` — require that queries against this table specify a partition filter. This is a cost control and it is worth enabling on any large table.
- `bigquery.partitionExpirationDays` — how long partitions are kept. This is how you bound storage cost and it is the single most effective cost lever in a warehouse.

#### `ref` and `source`

`ref("model_name")` references another model **in the same repository**. The tool resolves it to the model's actual table name in the target dataset, including any schema override. You never hard-code a table name; that is what makes the same repository deployable to a dev and a prod dataset.

`source("connection_name", "table_name")` references an **external** table — one that is not defined in this repository. It compiles to a fully qualified reference to the external table.

```sql
SELECT * FROM ${source("prod_db", "customers")}
```

`source` has two important properties:

- You declare the schema of the source once, in a separate `.sqlx` file with `config { type: "declaration" }`, and then reference it.
- You can declare **data tests** on the source, so you can assert that the upstream table still has the shape you expect.

The distinction between `ref` and `source` is the distinction between *models you own* and *models you consume*. Only `ref` dependencies are yours to rebuild.

#### `declare` and variables

`declare` sets a variable in the compilation scope:

```sql
declare {
  target_date: "20260115",
  min_amount: 0,
}

SELECT COUNT(*) AS n
FROM ${ref("stg_events")}
WHERE event_date = "${target_date}"
  AND amount >= ${min_amount}
```

Variables are substituted at **compile time**. The generated SQL contains the literal value, not a variable reference. This matters: compile-time substitution means the SQL that runs is fully self-describing, which is exactly what you want for a lineage record and for debugging. It also means a variable cannot be used to inject a table name at runtime.

#### `is_incremental`

Inside a model of type `incremental`, `is_incremental` is a boolean that is true when the model is running in an incremental (as opposed to a full refresh) execution.

```sql
config {
  type: "incremental",
  schema: "intermediate",
  uniqueKey: "event_id",
  partitionBy: "event_date"
}

SELECT
  event_id,
  user_id,
  event_ts,
  event_date,
  region,
  amount_eur
FROM ${ref("stg_events")}
WHERE
  ${is_incremental(
    `event_date` >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
  )}
```

When the model runs as a full refresh, the condition is `TRUE` and everything is rebuilt. When it runs incrementally, only recent partitions are considered. The `is_incremental` guard is what makes the same SQL serve both modes.

**The critical detail:** the incremental filter must select a **superset** of the rows that actually changed. Using `CURRENT_DATE()` alone is a bug, because a row that arrives late — with an old event date — would never be picked up. The three-day lookback is the standard mitigation.

### Model types

#### View

```sql
config {
  type: "view",
  schema: "marts"
}
```

A view is a stored query. Nothing is materialised; the transformation runs every time the view is queried.

- **Good for:** transformation logic that is cheap to recompute, marts over small tables, and reference models that other models build on.
- **Bad for:** anything expensive. A view over a 10 TB table with a join is charged every time it is queried, and the cost is invisible until the bill arrives.
- **Bad for:** anything with a slowly-changing dimension join that requires a window function over a large table.

Views are the default for correctness and the wrong default for cost. Use them where the recompute is trivial.

#### Table

```sql
config {
  type: "table",
  schema: "intermediate"
}
```

A full rebuild every execution: `CREATE OR REPLACE TABLE`. The output is deterministic, the cost is proportional to the full input, and there are no incremental semantics to reason about.

- **Good for:** intermediate layers whose inputs are not reliably append-only, and any model you need to rebuild deterministically.
- **Bad for:** models over large inputs on a frequent schedule, where a full rebuild is both slow and expensive.

#### Incremental

```sql
config {
  type: "incremental",
  schema: "marts",
  uniqueKey: "event_id",
  partitionBy: "event_date"
}
```

Only the changed rows are processed, and the output is updated in place.

- **Good for:** large tables with an append-only source, where the input grows and the historical data does not change.
- **Requirements, all of them:** the source is append-only, `uniqueKey` identifies a row, and the incremental filter covers the changed rows.

### Incremental strategies

Dataform supports two strategies for incremental models.

#### `insert_overwrite`

```sql
config {
  type: "incremental",
  schema: "intermediate",
  partitionBy: "event_date"
}
```

On an incremental run, Dataform computes the **partitions that the model's rows touch** and replaces exactly those partitions with the newly computed rows. Everything else is left alone.

This is the strategy to prefer when the model is partitioned by a column derivable from the data and the rows for a given partition are complete once written.

**Requirements:** the partition column must be derivable from the query's output, and the rows for a partition must not depend on rows from other partitions. If a partition's contents depend on a global aggregate, `insert_overwrite` will write a partial partition that looks complete.

**Cost characteristic:** a full refresh touches every partition. An incremental run touches only the partitions in the filtered range. This is the "smart" default for partitioned incremental models.

#### `merge`

```sql
config {
  type: "incremental",
  schema: "marts",
  uniqueKey: ["event_id", "event_date"],
  mergeIncrementalStrategy: "MERGE"
}
```

The new rows are merged into the target on the `uniqueKey`: matching keys are updated, non-matching keys are inserted, and — importantly — **rows not present in the source are deleted** if the merge configuration says so.

`merge` is the right strategy when:

- The model is not partitioned, or the changes touch arbitrary rows.
- A row can be *corrected* in place (a late-arriving refund that changes yesterday's revenue).
- You need upsert semantics rather than partition replacement.

`merge` requires a `uniqueKey`. Without one, the merge is nondeterministic and Dataform will refuse to compile it. It is also more expensive than `insert_overwrite` because it must read the target and write matched rows.

**Choosing between them:**

| | `insert_overwrite` | `merge` |
|---|---|---|
| Unit of change | Partition | Row |
| Requires a partition column | Yes | No |
| Requires a unique key | No | Yes |
| Handles corrections to old rows | Only if the partition is recomputed | Yes |
| Cost | Lower | Higher |
| Complexity | Simple | More to reason about |

### The compilation model

This is the part that makes Dataform more than a task runner.

When you open a repository, Dataform **compiles** it:

1. It parses every `.sqlx` file.
2. It extracts the `config` block and the SQL body.
3. It resolves `ref()` and `source()` into concrete table references.
4. It resolves variables.
5. It applies the `is_incremental` logic based on the execution mode.
6. It produces, for every model, a set of concrete SQL statements — a `create view`, a `create or replace table`, an `insert`/`merge`, plus `delete` statements for partitions outside the incremental range.

Then it builds the **dependency graph** from the `ref()` edges and produces a topological order.

What you get is that the tool knows, before running anything:

- The exact SQL that will execute.
- Which models must run before which.
- Which models are affected by a change to one source.
- Which tests belong to which model.

That last point is what makes incremental execution safe: when you run an incremental workflow for a single date, Dataform knows which downstream models need to be recomputed for that date and schedules them in dependency order.

You can inspect all of this before running anything, in the Dataform UI's compilation output, or from the CLI:

```bash
gcloud dataform repositories list --project=my-project --location=us-central1
gcloud dataform repositories compile --project=my-project \
  --location=us-central1 \
  --repository=analytics \
  --workspace=analytics-prod
```

### Data quality tests

Tests are declared in the `config` block of a model, or in a separate `.sqlx` file that depends on the model.

```sql
config {
  type: "table",
  schema: "marts",
  tests: [
    unique {
      columns: ["event_id"]
    },
    not_null {
      columns: ["event_id", "user_id", "event_date", "amount_eur"]
    },
    relationships {
      columns: ["region"],
      to: ref("dim_region"),
      field: "region_code"
    },
    accepted_values {
      columns: ["region"]
      values: ["AMER", "APAC", "EMEA", "LATAM"]
    },
    accepted_values {
      columns: ["channel"]
      values: ["web", "mobile", "store"]
    }
  ]
}
```

The built-in test types:

- **`unique`** — the values in the column (or column combination) are distinct. The single most valuable test in a warehouse, because it is what makes a `merge` incremental strategy possible.
- **`not_null`** — the column has no null values.
- **`relationships`** — every value in the column exists in the referenced model's column. This is the foreign key test. It catches the join that silently drops rows because of a typo in a dimension key.
- **`accepted_values`** — the column's value is in a given set. This encodes your business vocabulary in code.
- **`custom`** — a SQL expression that must return no rows.

```sql
config {
  type: "table",
  schema: "marts",
  tests: [
    custom {
      name: "no_negative_revenue"
      description: "Revenue must never be negative"
      sql: "SELECT * FROM ${self()} WHERE revenue_eur < 0"
    }
  ]
}
```

`${self()}` refers to the model under test. A custom test is a query that returns rows when the assertion fails. Keep them cheap — they run on every execution.

**The test philosophy that matters:** tests are not a safety net you deploy at the end. They are the *executable specification* of a model. A model with `not_null` on its key columns and `relationships` to its dimensions is a model whose contract is written down. A model without tests is a model whose contract is in someone's head.

**Where tests belong.** Test the models, not the raw tables. A `not_null` test on a raw table that legitimately contains nulls is a test that fails every day and teaches people to ignore failures.

### The dependency graph and lineage

Dataform maintains two related graphs.

The **dependency graph** comes from `ref()` and `source()` edges. It is the execution order. When you run a workflow, Dataform executes models in topological order.

**Column-level lineage** comes from Data Catalog and BigQuery. Dataform publishes the compiled SQL's lineage into Data Catalog, so you can ask "which tables are affected if I change this column" and "which dashboards read this table". This is the part you did not get by writing SQL in a job, and it is the reason to run the transformation layer through a tool rather than ad hoc.

**Incremental lineage** is the extension that makes the tool more than a scheduler. When you run an incremental workflow for a single partition, Dataform computes the models affected by that partition and executes only those. It uses the partition columns declared in `config` and the `is_incremental` filters to work out the affected set.

This is the feature that makes a large warehouse tractable. Without it, every daily run rebuilds everything.

### Scheduling workflow executions

A workflow execution is triggered in three ways.

**On a schedule**, using Cloud Scheduler to invoke the Dataform API. This is the standard production pattern:

```bash
gcloud dataform workflows invoke \
  --project=my-project \
  --location=us-central1 \
  --repository=analytics \
  --workflow=analytics-prod \
  --invocation-time=2026-01-15T00:00:00Z
```

The recommended approach is a Cloud Scheduler job with an HTTP target calling `dataform.googleapis.com/v1/projects/.../workflowExecutions`, with the schedule set so that the invocation time corresponds to the data interval you want to process.

**On a Cloud Storage or Pub/Sub event**, using an Eventarc trigger. This is the right pattern for event-driven data: a file lands, the workflow runs for that file's date.

**Manually**, from the Dataform UI or the CLI, for a backfill.

For a Composer-based orchestration, you would call `gcloud dataform workflows invoke` from a `BashOperator` with the logical date as the invocation time. This composes cleanly: Airflow owns the schedule and the retries, Dataform owns the transformation graph.

**Invocation time is the logical date.** `invocation-time=2026-01-15T00:00:00Z` means "process the data interval ending at 2026-01-15". Getting this wrong is the classic off-by-one.

### Dataform versus dbt

This comparison matters because many teams arrive at Dataform already using dbt, or vice versa.

| Aspect | Dataform | dbt |
|---|---|---|
| Where it runs | Managed GCP service; compilation and execution in Google's control | Your own infrastructure (Cloud Run, ECS, Kubernetes) |
| Target | BigQuery primarily; other BigQuery-adjacent targets | BigQuery, Snowflake, Redshift, Databricks, Postgres, and others |
| Transformation language | SQLX: SQL plus a config block | Jinja-templated SQL plus a YAML schema file |
| Configuration location | Inside the SQL file | Separate YAML files per model |
| Compilation | Server-side, visible in the UI before execution | Local `dbt compile` or in Cloud Build |
| Testing | Built into `config`; custom SQL assertions | `dbt test`; generic and singular tests |
| Docs | Generated in the UI and Data Catalog | `dbt docs generate` produces a static site |
| Lineage | Published to Data Catalog with column-level lineage | Emits lineage artefacts; BigQuery-specific lineage needs extra work |
| Incremental execution | Built in, partition-aware | Built in via `incremental` materialisations |
| Openness | Proprietary service | Open source, runs anywhere |

**The honest comparison.** Dataform's advantages on GCP are real: the compilation is server-side, so you can see exactly what will run before it runs; the generated SQL is visible and reviewable; lineage integration with Data Catalog is first-class; and there is no infrastructure to operate. dbt's advantages are portability and ecosystem: it runs on any warehouse, the community knowledge is larger, and the YAML-plus-Jinja approach is more familiar.

**My view:** if your warehouse is BigQuery and you are on GCP, Dataform is the lower-friction choice. If you need multi-warehouse portability, or you have a team already fluent in dbt, dbt is the better investment. Running both in one organisation is a mistake — the transformation layer should have exactly one owner, or the models will drift.

### When you do not need either

This is the most important section in the chapter.

**You do not need a transformation layer when:**

- **There are fewer than about ten models.** A handful of views in BigQuery, versioned in a repository and applied with `bq query`, is enough. The overhead of a transformation tool — compilation, a config file per model, a deployment workflow, a permissions model — is not amortised yet.
- **The transformations are one-liners.** A view that selects three columns from one table does not need a tool.
- **The source is already a clean, well-documented table** in a warehouse that someone else governs.
- **You are prototyping.** Build it in a notebook, and only move it into a transformation layer when it is stable and someone else depends on it.

**You need a transformation layer when** several of these are true:

- More than about ten models, or more than one team writes them.
- A model's SQL is referenced by other models — the dependency graph is doing real work.
- The same transformation runs in more than one environment.
- You need to answer "what breaks if I change this table?"
- You need tests, because a silent correctness failure in a mart is expensive.
- The models need lineage for governance, cataloguing, or impact analysis.
- The layer is incremental, because rebuilding everything daily is not affordable.

The progression most teams follow is: notebook → hand-written SQL → SQL in a repository → a transformation tool. Each step is triggered by a specific pain, not by fashion. If you have not hit the pain, the tool is overhead.

---

## 🛠️ Hands-On

### Exercise 1: model the transformation layers over the course pipeline

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, aggregate_events, render_summary_csv

# The layer model, expressed in the course pipeline:
#
#   raw_events          -> the CSV exactly as it arrived
#   stg_events          -> validated, normalised rows
#   int_events_daily    -> one row per (event_date, region)
#   mart_region_revenue -> the revenue summary analysts query

with open("sample_data/events.csv", encoding="utf-8") as handle:
    raw_lines = handle.read().splitlines()

accepted, rejected = ingest_events(raw_lines)

stg = accepted
daily = {}
for row in accepted:
    key = (str(row["event_dt"])[:10], row["region"])
    stats = daily.setdefault(key, {"event_count": 0, "revenue_eur": 0.0})
    stats["event_count"] += 1
    stats["revenue_eur"] += float(row["amount_eur"])

mart = aggregate_events(accepted)

print("raw rows:            ", len(raw_lines))
print("stg rows:            ", len(stg))
print("int rows:            ", len(daily))
print("mart rows:           ", len(mart))
print()
print(render_summary_csv(mart))
```

Output:

```text
raw rows:            4801
stg rows:            4800
int rows:            96
mart rows:           4

region,event_count,revenue_eur
AMER,1238,464848.02
APAC,1159,421049.85
EMEA,1176,432544.17
LATAM,1227,445554.36
```

The row counts shrink at each layer: 4801 raw lines (including the header), 4800 staged rows, 96 daily rows, 4 mart rows. Each layer is a materialisation boundary, and the cost of each boundary is a decision you make deliberately.

### Exercise 2: the four built-in tests, applied to the course data

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, aggregate_events

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, _ = ingest_events(handle.read().splitlines())

# unique on event_id
ids = [row["event_id"] for row in accepted]
unique_ok = len(ids) == len(set(ids))

# not_null on the key columns
nulls = {
    column: sum(1 for row in accepted if row.get(column) in (None, ""))
    for column in ("event_id", "user_id", "event_dt", "region", "amount_eur")
}

# relationships: region must exist in the dimension
DIM_REGIONS = {"AMER", "APAC", "EMEA", "LATAM"}
orphan = {row["region"] for row in accepted} - DIM_REGIONS

# accepted_values on region
bad_regions = orphan

summary = aggregate_events(accepted)
zero_rows = [r for r, v in summary.items() if int(v["event_count"]) == 0]

print("unique(event_id):        ", "PASS" if unique_ok else "FAIL")
print("not_null(key columns):   ", "PASS" if not any(nulls.values()) else f"FAIL {nulls}")
print("relationships(region):   ", "PASS" if not orphan else f"FAIL {orphan}")
print("accepted_values(region): ", "PASS" if not bad_regions else f"FAIL {bad_regions}")
print("custom(no empty mart):   ", "PASS" if not zero_rows else f"FAIL {zero_rows}")
```

Output:

```text
unique(event_id):         PASS
not_null(key columns):    PASS
relationships(region):    PASS
accepted_values(region):  PASS
custom(no empty mart):    PASS
```

### Exercise 3: choose the incremental strategy

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    ingest_events,
    partition_for_date,
    partition_for_event,
    filter_rows_for_partition,
    deduplicate,
)

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, _ = ingest_events(handle.read().splitlines())

partition = partition_for_date("2026-01-15")

# insert_overwrite: the unit of change is the partition. We only need to
# know which partition to replace.
overwrite_rows = filter_rows_for_partition(accepted, partition)
print("insert_overwrite:")
print("  unit of change:  partition")
print("  partition:       ", partition)
print("  rows written:    ", len(overwrite_rows))

# merge: the unit of change is the row. We need a key that identifies a
# row uniquely, and we need to handle the case where a row is corrected.
ids = [row["event_id"] for row in accepted]
print()
print("merge:")
print("  unit of change:  row")
print("  unique key:       event_id")
print("  key is unique:   ", len(ids) == len(set(ids)))
print("  rows to merge:   ", len(deduplicate(accepted, partition=partition)))
```

Output:

```text
insert_overwrite:
  unit of change:  partition
  partition:       20260115
  rows written:    4800

merge:
  unit of change:  row
  unique key:       event_id
  key is unique:    True
  rows to merge:    4800
```

The distinction: `insert_overwrite` needs a partition column and no key; `merge` needs a key and no partition column. A model that is partitioned *and* has corrections to old rows needs both, which means `merge` with partition-aware incremental execution.

### Exercise 4: the incremental filter and the late-arrival bug

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, partition_for_event

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, _ = ingest_events(handle.read().splitlines())

# A naive incremental filter uses only "today".
naive = "event_date = CURRENT_DATE()"

# The correct filter includes a lookback so that late rows, which carry
# an older event_date, are still picked up.
lookback = "event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)"

print("naive filter:   ", naive)
print("  -> a row that arrives late with an older event_date is NEVER")
print("     picked up. The row silently disappears from the model.")
print()
print("lookback filter:", lookback)
print("  -> any row whose event_date falls inside the lookback window is")
print("     recomputed, including rows that arrived after the fact.")
print()

# Show that a late row carries an older partition.
late_row = dict(accepted[0])
late_row["event_ts"] = "2026-01-10T09:15:00+00:00"
late_row["event_dt"] = "2026-01-10T09:15:00+00:00"
print("late row partition:", partition_for_event(late_row["event_dt"]))
print("today's partition: ", partition_for_event(accepted[0]["event_dt"]))
```

Output:

```text
late row partition: 20260110
today's partition:  20260115
```

A late row belongs to a five-day-old partition. With a naive `CURRENT_DATE()` filter, the incremental run never looks at that partition, so the row is never merged in. It is a silent data-loss bug that produces no error, only wrong revenue. The three-day lookback is the mitigation, and the lookback length must exceed your observed lateness distribution.

### Exercise 5: the dependency graph from `ref()` calls

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, aggregate_events

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, _ = ingest_events(handle.read().splitlines())

# The graph Dataform would build from ref() edges:
graph = {
    "raw_events": [],
    "stg_events": ["raw_events"],
    "stg_currency_rates": [],
    "int_events_daily": ["stg_events", "stg_currency_rates"],
    "mart_region_revenue": ["int_events_daily"],
    "mart_channel_summary": ["int_events_daily"],
}

# Topological order, the execution sequence.
remaining = dict(graph)
order = []
while remaining:
    ready = [name for name, deps in remaining.items()
             if all(dep in order for dep in deps)]
    if not ready:
        raise RuntimeError("cycle detected")
    ready.sort()
    order.extend(ready)
    for name in ready:
        del remaining[name]

print("execution order:")
for index, name in enumerate(order, start=1):
    deps = graph[name]
    print(f"  {index}. {name:22s} <- {', '.join(deps) if deps else '(source)'}")

# A change to raw_events affects everything downstream.
downstream = set()
frontier = {"raw_events"}
while frontier:
    current = frontier.pop()
    for name, deps in graph.items():
        if current in deps and name not in downstream:
            downstream.add(name)
            frontier.add(name)

print()
print("models affected by a change to raw_events:", len(downstream) + 1)
print("  ", sorted(downstream | {"raw_events"}))
```

Output:

```text
execution order:
  1. raw_events            <- (source)
  2. stg_currency_rates    <- (source)
  3. stg_events            <- raw_events
  4. int_events_daily      <- stg_events, stg_currency_rates
  5. mart_channel_summary  <- int_events_daily
  6. mart_region_revenue   <- int_events_daily

models affected by a change to raw_events: 4
   ['int_events_daily', 'mart_channel_summary', 'mart_region_revenue', 'stg_events']
```

Notice that `mart_channel_summary` and `mart_region_revenue` are siblings: they share a parent but not an edge. Changing one does not require rebuilding the other. That is the value of a dependency graph — impact analysis that a pile of shell scripts cannot give you.

### Exercise 6: the generated SQL for an incremental model

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import partition_for_date

logical_date = "2026-01-15"
partition = partition_for_date(logical_date)

full_refresh = f"""
DELETE FROM `my-project.analytics.int_events_daily` WHERE TRUE;
INSERT INTO `my-project.analytics.int_events_daily`
  (event_id, user_id, event_date, region, amount_eur)
SELECT event_id, user_id, event_date, region, amount_eur
FROM `my-project.analytics.stg_events`
WHERE TRUE;
"""

incremental = f"""
DELETE FROM `my-project.analytics.int_events_daily`
WHERE event_date = DATE('{logical_date}');
INSERT INTO `my-project.analytics.int_events_daily`
  (event_id, user_id, event_date, region, amount_eur)
SELECT event_id, user_id, event_date, region, amount_eur
FROM `my-project.analytics.stg_events`
WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY);
"""

print("=== FULL REFRESH ===")
print(full_refresh.strip())
print()
print("=== INCREMENTAL ===")
print(incremental.strip())
```

The full refresh deletes everything and rebuilds. The incremental deletes only the affected partitions and recomputes only the lookback window. Note that the `is_incremental` guard has already been resolved at compile time — the generated SQL contains a literal `WHERE TRUE` in one mode and a real filter in the other.

---

## 🛠️ Common Errors and Fixes

### 1. `Compilation error: Could not resolve reference to dataset 'analytics.stg_events'`

```text
DataformCompilationError: Compilation error: Could not resolve reference to
dataset 'analytics.stg_events'. Referenced by model 'int_events_daily'.
```

**Cause.** The `ref()` name does not match any model in the repository — usually a typo, a rename that was not propagated, or a model that was deleted but is still referenced.

**Fix.** Check the model list in the Dataform UI's compile output, and grep the repository for the stale reference:

```bash
grep -rn 'ref("stg_events")' --include=*.sqlx .
```

Also check that the `.sqlx` file is actually in the repository and that its filename is unique. Dataform identifies models by their filename (with the `.sqlx` suffix stripped), not by any name inside the file, so `stg_events.sqlx` defines the model `stg_events`.

### 2. `Compilation error: Column 'stg_events.amount' not found`

```text
DataformCompilationError: Compilation error: Column 'stg_events.event_id'
not found in table 'analytics.stg_events'.
```

**Cause.** The referenced model's schema does not include the column you selected. Dataform compiles against the schema in the `config` block of the referenced model (or, for `source()` declarations, against the declared source schema).

**Fix.** Check the referenced model's `schema` declaration in its `config` block and add the column, or correct the column name in the dependent model. If the column was recently added upstream, update the source declaration:

```sql
config {
  type: "declaration",
  database: "prod_db",
  schema: "public",
  name: "events"
}

columns: [
  { name: "event_id", type: "STRING" },
  { name: "amount", type: "NUMERIC" }
]
```

### 3. `Error: Model 'stg_events' has no unique key but uses the merge strategy`

```text
DataformCompilationError: Model 'stg_events' is incremental with the 'merge'
strategy but does not declare a 'uniqueKey'.
```

**Cause.** The model is `type: "incremental"` with `mergeIncrementalStrategy: "MERGE"` but has no `uniqueKey` in its config. The merge has nothing to match on, so the behaviour would be nondeterministic.

**Fix.** Add the key, and verify it is genuinely unique with a test:

```sql
config {
  type: "incremental",
  schema: "marts",
  uniqueKey: "event_id",
  mergeIncrementalStrategy: "MERGE",
  tests: [ unique { columns: ["event_id"] } ]
}
```

If the key is a composite, use a list: `uniqueKey: ["event_id", "event_date"]`. If the model genuinely has no natural key, use `insert_overwrite` on a partition instead.

### 4. `Error: Invocation time is not a valid date` or `Invalid argument: Workflow execution already exists`

```text
google.api_core.exceptions.BadRequest: 400 Invalid value for
'invocationTime': 'yesterday'.
```

**Cause.** The `--invocation-time` flag requires an RFC 3339 timestamp, not a relative expression. A separate and more dangerous variant: the same invocation time was already used, so the workflow refuses to run again — which is a **feature**, protecting against accidental double-processing of a date.

**Fix.** Use an absolute timestamp in the correct format:

```bash
gcloud dataform workflows invoke \
  --project=my-project \
  --location=us-central1 \
  --repository=analytics \
  --workflow=analytics-prod \
  --invocation-time=2026-01-15T00:00:00Z
```

For a backfill, invoke once per date. The duplicate-invocation guard means a retry with the same timestamp fails loudly, which is exactly what you want.

### 5. `BigQuery error: Partition filter required for query` on a table you did not write

```text
400 Bad Request: Partition filter required for query on table
my-project.analytics.events
```

**Cause.** The model has `bigquery.requirePartitionFilter: true`, and a query against it — from a dashboard, a notebook, or another model — did not filter by the partition column. The error is raised by BigQuery, not Dataform, so it surfaces at query time rather than compile time.

**Fix.** Add the partition predicate to the querying SQL:

```sql
SELECT * FROM `my-project.analytics.events`
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-15'
```

This error is a feature, not a nuisance. It is the mechanism that prevents an accidental 2 TB scan of a 2 TB table, and it is the single highest-value line of configuration in a BigQuery warehouse.

### 6. Test failures that nobody reads

```text
Test unique_on_event_id failed for model 'stg_events'.
2 rows failed.
```

**Cause.** Either a genuine data-quality regression, or a test that is too strict for the data's actual shape — for example, a `unique` test on a column that is only unique within a partition, not globally.

**Fix.** Decide which it is, deliberately:

- **Genuine regression.** Fix the upstream model. Do not weaken the test to make it pass; that converts a detected bug into a hidden one.
- **Too strict.** Make the test match the grain of the model. If the grain is "one row per event per partition", the test should be a composite:

```sql
tests: [
  unique { columns: ["event_date", "event_id"] }
]
```

Then fix the operational problem: **a test that fails every day is a test people learn to ignore**, and one ignored test teaches people to ignore all of them. Alert on test failures, and treat a permanently red test as an outage of your data contract.

---

## 💡 Production Notes

- **Put a `description` in every model's `config`.** It is the first thing an engineer sees in the Dataform UI and in Data Catalog. A model with no description is a model nobody dares to change.
- **Set `bigquery.requirePartitionFilter` on every large table.** It is the cheapest cost control available and it turns a potential 2 TB scan into a 20 GB one.
- **Set `partitionExpirationDays` deliberately.** Storage cost is unbounded by default, and old partitions are almost never read. Thirty days on staging, a year on marts, is a reasonable starting point.
- **Use a lookback window on every incremental model.** The window must exceed your observed late-arrival distribution. Measure it; do not guess. Three days is a common default, but your data may be slower.
- **Never hard-code a table name.** Use `ref()` for models you own and `source()` for tables you consume. Hard-coded names break environment promotion and silently break lineage.
- **Keep the raw layer immutable.** If the raw data needs fixing, fix the ingestion and replay. Editing raw in place destroys the audit trail.
- **Test models, not raw.** Assert the contract you actually depend on. Enforce `unique` on every key used by a `merge`, and `relationships` to every dimension you join.
- **Compile before you run.** The compiled SQL in the UI is the exact statement that will execute. Reviewing it is the cheapest code review you will ever do.
- **Schedule workflow invocations with Cloud Scheduler, and pass the data interval as the invocation time.** Then the orchestrator owns the schedule and Dataform owns the graph, and neither has to know about the other's internals.
- **Use tags.** `tags: ["daily", "events"]` makes it possible to run a subset of models, which is how you get a fast path for a hot fix.

---

## 🔑 Key Takeaways

- The transformation layer exists so that logic becomes declarative SQL, reviewable as a diff, testable, and analysable for dependencies and impact.
- Dataform's objects layer cleanly: repository (logic) → workspace (compiled state) → table (model) → workflow execution (a run).
- SQLX adds a small declarative layer: `config` for metadata and materialisation, `ref()` for models you own, `source()` for tables you consume, `declare` for compile-time variables, and `is_incremental` for the incremental guard.
- Three model types with distinct economics: views recompute on every read, tables rebuild on every run, incremental models update only what changed.
- Two incremental strategies: `insert_overwrite` works at partition granularity and needs no key; `merge` works at row granularity, needs a `uniqueKey`, and handles corrections to old rows.
- The incremental filter must cover a superset of the changed rows. `CURRENT_DATE()` alone silently loses late-arriving data; a lookback window is the fix, and its length must be measured, not guessed.
- Compilation is the core mechanic: Dataform resolves references and variables at compile time, producing the exact SQL that will run, the execution order, and the affected set for an incremental run.
- Tests are the executable specification of a model. `unique`, `not_null`, `relationships`, `accepted_values`, and custom SQL assertions catch the failures that silently corrupt a mart.
- Dataform versus dbt: Dataform wins on server-side compilation, visible generated SQL, and Data Catalog lineage; dbt wins on portability and ecosystem. Running both in one organisation is a mistake.
- You do not need a transformation layer until the dependency graph, the tests, or the incremental execution earn their keep. Below roughly ten models, plain versioned SQL applied with `bq query` is the right answer.

---

## 📚 Practice Exercises

1. **Design the layers.** Write out the model names, types, and `ref()` dependencies for the course pipeline across raw, staging, intermediate, and mart. State which model is incremental, which strategy it uses, and why.
2. **Write the SQLX.** Write the complete `.sqlx` file for the staging model over the course events: the `config` block with `type`, `schema`, `description`, `tags`, `partitionBy`, and the built-in tests for `unique`, `not_null`, `relationships`, and `accepted_values`.
3. **Prove the incremental filter bug.** Use `partition_for_event` to demonstrate that an event with an old timestamp would be skipped by a `CURRENT_DATE()` filter. Then quantify the lookback window you would set if your observed lateness distribution had a 99th percentile of 6 hours.
4. **Compare strategies.** Build the same model twice: once with `insert_overwrite` on a partition column and once with `merge` on `event_id`. Use `filter_rows_for_partition` and `deduplicate` to show what each strategy writes, and explain when a late-arriving correction to a five-day-old partition is handled correctly by each.
5. **Compute the impact set.** Extend the dependency graph from Exercise 5 to ten models. Write a function that, given a changed model, returns every model that must be rebuilt. Verify it against the graph and state which models are safe to skip.
6. **Write the custom assertions.** Write three custom SQL assertions for the course pipeline: no negative revenue in the mart, every mart row's event count is positive, and the mart total event count equals the staging row count. Explain why the third is the most valuable of the three.
7. **Compare Dataform and dbt concretely.** For your own organisation, list the BigQuery features you rely on (partition requirements, JSON handling, scheduled queries, Data Catalog lineage, slot reservations). For each, say whether dbt on Cloud Run could do it, and at what operational cost.
8. **Argue for or against a transformation layer.** Using the course project, count the models, the cross-model dependencies, the tests you would write, and the incremental opportunities. Then write a one-page recommendation: adopt a transformation layer now, or wait and what specifically would change your mind.

---

## 📖 Further Reading

- [Dataform Documentation](https://cloud.google.com/dataform/docs)
- [Dataform: Overview of the Dataform Workflow](https://cloud.google.com/dataform/docs/workflow-overview)
- [Dataform: Write SQL for Dataform](https://cloud.google.com/dataform/docs/reference/dataform-sql)
- [Dataform: Data Quality Tests](https://cloud.google.com/dataform/docs/data-quality-tests)
- [Dataform: Incremental Tables](https://cloud.google.com/dataform/docs/incremental-tables)
- [BigQuery: Partitioned Tables](https://cloud.google.com/bigquery/docs/partitioned-tables)
- [dbt Documentation: Introduction](https://docs.getdbt.com/docs/introduction)
