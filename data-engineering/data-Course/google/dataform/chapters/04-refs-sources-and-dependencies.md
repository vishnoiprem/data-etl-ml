# 1.4 — Refs, Sources & the Dependency Graph

> **Section 1 · Foundations · Lecture 1.4 · 15:20**

## 🎯 What you will learn

- How `ref()` resolves a name to a fully-qualified relation, step by step
- The precedence rules between `dataform.json` defaults, per-model `config`, and `ref()` overrides
- How the `sources/` folder is discovered, and what the file name vs the argument means
- Freshness configuration: `loaded_at_field` + `freshness` on a source
- How the DAG is built, and how to read `.dataform/run.json` to inspect it
- Topological ordering, cycles, and how the compiler reports a missing `ref()`
- `include`/`exclude`, `disabled` models, `protected` models, and cross-project refs
- `action_selector`, `actions: ["run"]` vs `["build"]` vs `["test"]`, and ephemeral models in the graph

---

## 🧠 Concept

### How a `ref()` resolves

`ref("stg_orders")` looks up a model **by name** — the filename without the `.sqlx` extension —
and returns its fully-qualified relation. The resolution is a strict sequence:

```
  ref("stg_orders")
        │
        ▼
 ① FIND THE MODEL — look for stg_orders.sqlx anywhere under definitions/
        │    (excluding definitions/sources/, which holds sources)
        ▼
 ② APPLY THE TARGET SCHEMA — first match wins:
      a. the schema in the ref() call:  ref("x", { schema: "other" })
      b. the model's own config { schema: "..." }
      c. dataform.json → warehouse.schema
      d. dataform.json → defaultDataset
        │
        ▼
 ③ APPLY THE TARGET DATABASE — same precedence:
      a. ref("x", { database: "other-project" })
      b. the model's own config { database: "..." }
      c. dataform.json → warehouse.database
      d. dataform.json → defaultProject
        │
        ▼
 ④ RETURN THE QUALIFIED NAME → `my-project.analytics.stg_orders`
```

The result is substituted into your SQL as a literal, and **a DAG edge is created** from
`stg_orders` to the model that called `ref()`.

### The precedence table

This is the single most useful thing to internalize:

| Priority | Source | Example |
|----------|--------|---------|
| 1 (highest) | The `ref()` call itself | `ref("stg_orders", { schema: "other_schema" })` |
| 2 | The model's own `config` block | `config { schema: "staging" }` |
| 3 | `dataform.json` → `warehouse` | `warehouse.schema`, `warehouse.database` |
| 4 (lowest) | `dataform.json` → `default*` | `defaultDataset`, `defaultProject` |

💡 **A per-model `config { schema: ... }` affects where that model is *written*.** A
`ref("x", { schema: "..." })` affects where `x` is *read from*. They are different things, and
mixing them up is the classic "why is my table in the wrong dataset" bug.

### `ref()` with a custom schema

```sqlx
config { type: "view" }

SELECT *
FROM ${ref("stg_orders", { schema: "raw_staging" })}
```

This reads `my-project.raw_staging.stg_orders` while still declaring a dependency on the
`stg_orders` **model**. Use it when the same logical model exists materialized in several
datasets — e.g. a `stg_orders` model built into both `analytics` and `sandbox`, and one
particular consumer needs the sandbox copy.

```sqlx
// Cross-project reference
FROM ${ref("stg_orders", { database: "other-project", schema: "staging" })}
```

⚠️ **A `ref()` override does not create a new model.** It still points at the same node in the
DAG. If `stg_orders` lives in `analytics` but you reference it with `{ schema: "raw_staging" }`,
Dataform will still build `analytics.stg_orders` and then your query will read
`raw_staging.stg_orders` — which may not exist. The override is for *reading* an already-
materialized variant, not for redirecting the build.

### Cross-schema and cross-project refs

The normal case: models in a different dataset within the same project.

```sqlx
config {
  type: "table",
  schema: "marts"
}

SELECT *
FROM ${ref("stg_orders")}          // → my-project.analytics.stg_orders
```

The `config { schema: "marts" }` says *write me to* `marts`. The `ref()` says *read from*
`analytics`. Both are correct, and the compiled SQL reflects both.

For a genuinely different project:

```sqlx
FROM ${ref("shared_dim_customer", { database: "shared-analytics-prod", schema: "dims" })}
```

⚠️ **Cross-project refs require IAM.** The identity running the pipeline needs
`roles/bigquery.dataViewer` (or `dataEditor`) on the other project, and — for Dataform Cloud —
the workspace's service account must have it too. This is the most common cause of a
"permission denied" that only appears in production, because local development runs under your
own user account.

### The `sources/` folder and how Dataform discovers sources

Sources live in `definitions/sources/`. Dataform scans that folder and treats each file as a
**source definition**.

```
definitions/sources/
├── raw_orders.sqlx        ← source name: "raw_orders"
├── raw_customers.sqlx     ← source name: "raw_customers"
└── crm_contacts.sqlx      ← source name: "crm_contacts"
```

Each file declares one or more tables:

```sqlx
// definitions/sources/raw_orders.sqlx

config {
  type: "declarative",
  database: "source-project",
  schema: "raw",
  description: "Raw orders landing table"
}

source("raw_orders", "orders")
```

```
┌────────────────────────────────────────────────────────────────┐
│  FILE: definitions/sources/raw_orders.sqlx                    │
│                                                                │
│  source("raw_orders", "orders")                               │
│         │             │                                       │
│         │             └── "orders"  = the TABLE name           │
│         └── "raw_orders"  = the SOURCE name (= file name)     │
│                                                                │
│  Models reference it as: ${source("raw_orders", "orders")}    │
│     → source-project.raw.orders                               │
└────────────────────────────────────────────────────────────────┘
```

> **The file name is the source name. The argument in `source()` is the table name.**

So `definitions/sources/raw_orders.sqlx` containing `source("raw_orders", "orders")` creates a
source named `raw_orders` with a table named `orders`.

⚠️ **A `source()` file that declares no table, or a `source()` call whose first argument does
not match the file name, is a compile error.** The compiler will not guess.

⚠️ **Sources do not create tables and do not appear in the DAG as buildable nodes.** They are
leaves — the entry points where external data enters your graph. There is nothing to build, so
there is nothing to order.

### Source config — `type`, `loaded_at_field`, and `freshness`

```sqlx
// definitions/sources/raw_orders.sqlx

config {
  type: "declarative",
  database: "source-project",
  schema: "raw",
  description: "Raw orders landing table, written by the operational system",
  loaded_at_field: "_loaded_at",
  freshness: {
    errorAfter: "48h",
    warnAfter: "24h"
  }
}

source("raw_orders", "orders")
```

| Field | Effect |
|-------|--------|
| `type: "declarative"` | Marks this as a source (not a model). |
| `database` / `schema` | Where the external table lives. |
| `description` | Surfaced in the catalog and lineage. |
| `loaded_at_field` | Column holding the load timestamp. |
| `freshness.errorAfter` | Age at which the source is considered **failed**. |
| `freshness.warnAfter` | Age at which the source is considered **stale**. |

💡 **Freshness is the closest thing Dataform has to an SLA on an external feed.** With
`loaded_at_field: "_loaded_at"` and `freshness: { errorAfter: "48h", warnAfter: "24h" }`,
Dataform checks the source's load timestamp on every run: older than 24 hours is a warning,
older than 48 hours is an error that fails the build.

This catches the failure mode nothing else catches: **the upstream job silently stopped.** Your
pipeline keeps running green against three-day-old data, and nobody notices until someone asks
why the numbers look stale.

### How the DAG is built

The compiler does this, in order:

```
   ① PARSE every .sqlx file under definitions/
        ▼
   ② EXTRACT the config block → a target per model
        ▼
   ③ SCAN the SQL body for ref() and source() calls
        ├─► ref("x")         → edge: x  ──►  this model
        └─► source("s","t")  → no edge (sources are leaves)
        ▼
   ④ ADD explicit config { dependencies: [...] } edges
        ▼
   ⑤ TOPOLOGICALLY SORT the graph → execution order
        ▼
   ⑥ RESOLVE each ref() to a fully-qualified relation name
        ▼
   ⑦ GENERATE the compiled SQL + the DAG (.dataform/run.json)
```

### Reading `.dataform/run.json`

```json
{
  "targets": [
    { "name": "stg_orders",
      "relation": "my-project.analytics.stg_orders",
      "type": "table",
      "fileName": "definitions/stg/stg_orders.sqlx" },
    { "name": "fct_orders",
      "relation": "my-project.analytics.fct_orders",
      "type": "incremental",
      "fileName": "definitions/marts/fct_orders.sqlx" }
  ],
  "dag": {
    "stg_orders": {
      "relations": ["my-project.analytics.stg_orders"]
    },
    "fct_orders": {
      "relations": ["my-project.analytics.fct_orders"],
      "dependencies": [
        { "target": { "name": "stg_orders",
                      "relation": "my-project.analytics.stg_orders" } }
      ]
    }
  },
  "operations": [ ... ],
  "tests": [ ... ]
}
```

`dag.<model>.dependencies` is the list you care about — it is the model's upstream nodes,
derived from the SQL.

Key fields:

| Field | What it tells you |
|-------|-------------------|
| `targets` | Every model, with its resolved relation, type, and source file. |
| `dag.<model>.relations` | The relations a model produces. |
| `dag.<model>.dependencies` | The upstream nodes it depends on. **This is your dependency list.** |
| `operations` | The ordered list of actions to execute. |
| `tests` | Unit tests and assertions attached to the graph. |

```bash
# Pretty-print the DAG
python3 -m json.tool .dataform/run.json | head -60
```

### Topological ordering

A DAG has a **topological sort**: an ordering of the nodes such that every node comes *after*
all of its dependencies. There may be several valid orderings — the compiler picks one.

```
    stg_orders ──┐
                 ├──▶ fct_orders
    stg_cust  ───┘

    stg_cust  ──┐
                ├──▶ dim_customers ──▶ fct_cust
    stg_ord  ───┘
```

Because `stg_orders` and `stg_customers` are independent, they may run in parallel. Dataform
exploits this — `dataform run` executes independent nodes concurrently, which is where the
BigQuery slot-time savings come from.

⚠️ **The compiler cannot invent a dependency from shared tables.** If two models read the same
`source()` and you assume one must run first, you are wrong — they are independent by
definition.

### Cycles — and how the compiler reports them

A cycle is impossible to order: A needs B, B needs C, C needs A. Dataform rejects it at
compile time.

```
    stg_a ──▶ stg_b ──▶ stg_c ──▶ stg_a
      ▲                            │
      └────────────────────────────┘
```

The error names the models involved in the cycle. The fix is to break the loop — usually by
extracting the shared logic into a third model that both depend on:

```
    stg_a ──▶ stg_b ──┐
                      ├──▶ stg_shared ──▶ stg_c
    stg_d ──▶ stg_e ──┘
```

⚠️ **A cycle is almost always a design smell, not a typo.** It usually means two models are
doing each other's jobs — and in BigQuery, a self-referencing table is usually better expressed
with `self()` than with a cycle.

### A worked compile error — a missing ref

Create a model that references something that does not exist:

```sqlx
// definitions/marts/fct_orders.sqlx

config { type: "table" }

SELECT *
FROM ${ref("stg_orderz")}
```

```bash
dataform compile
```

The compiler fails with an error like:

```text
Error: Compilation failed
  Target 'fct_orders' is invalid:
    1:6: Unable to resolve reference to 'stg_orderz'.
    Compiled SQL cannot be determined until the reference is resolved.
    Check that the model 'stg_orderz' exists in the project and that
    the file name matches the model name.
```

Three things to notice:

1. **The error names the model and the missing reference.** You do not have to hunt for it.
2. **Nothing was written to BigQuery.** The compiler stopped before any query ran.
3. **The error is a compile error, not a runtime error.** The "table does not exist" failure mode
   from Chapter 1.1 cannot happen here.

Fix it — create `definitions/stg/stg_orderz.sqlx`, or correct the typo to `ref("stg_orders")`.
Then `dataform compile; echo $?` returns `0`.

⚠️ **The same error appears for an undefined `source()`.** `source("raw_oders", "orders")` with
no matching file in `definitions/sources/` fails identically.

### The DAG before and after a dependency

**Before** — `fct_orders` reads only `stg_orders`:

```
       ┌──────────────┐
       │  stg_orders  │
       └──────┬───────┘
              │ ref("stg_orders")
       ┌──────▼───────┐
       │  fct_orders  │
       └──────────────┘

  run.json dag:
    stg_orders: { relations: [...] }
    fct_orders: { relations: [...], dependencies: [] }
```

**After** — you add `dim_customers` and reference it:

```sqlx
SELECT o.order_id, o.customer_id, c.segment
FROM ${ref("stg_orders")} o
JOIN ${ref("dim_customers")} c ON o.customer_id = c.customer_id
```

```
       ┌──────────────┐                    ┌────────────────┐
       │  stg_orders  │                    │ dim_customers  │
       └──────┬───────┘                    └────────┬───────┘
              │                    ref()            │
       ┌──────▼──────────────────────────────┐      │
       │           fct_orders                │◀─────┘
       └─────────────────────────────────────┘

  run.json dag:
    stg_orders:    { relations: [...] }
    dim_customers: { relations: [...], dependencies: [stg_customers] }
    fct_orders:    { relations: [...], dependencies: [stg_orders, dim_customers] }
```

The `dependencies` array for `fct_orders` now has two entries. That single line is the entire
value proposition of Dataform: **the dependency graph is derived from the SQL, not maintained
separately.**

### `dependencies` — edges the SQL does not imply

```sqlx
config {
  type: "table",
  dependencies: ["stg_cleanup_audit"]
}
```

Use it for ordering dependencies, not data dependencies:

- A model must run *after* a cleanup/audit model finishes
- A model must not run concurrently with another model (e.g. both write the same partition)
- A model must run after a `DELETE` operation on another model

⚠️ **`dependencies` does not make data available.** If model A reads model B's table, you must
use `ref("B")`. Adding `dependencies: ["B"]` without a `ref()` gives you ordering but no
readability — and the compiler will still complain about an unresolved table name.

### `include` / `exclude`

```sqlx
config {
  type: "table",
  include: ["definitions/stg/*.sqlx"],
  exclude: ["definitions/stg/stg_temp.sqlx"]
}
```

These control which files contribute to the model's compilation — used when you build a model
from a shared template or want to exclude a file from a specific compiled target.

### `disabled` models

```sqlx
config {
  type: "table",
  disabled: true
}
```

The model is **compiled but not executed**. It stays in the DAG so that anything referencing it
still resolves, but `dataform run` will not build it.

⚠️ **A `disabled` model is not deleted.** If it already produced a table, the table stays in
BigQuery with stale data. Downstream models that read it will keep working — with stale data.
`disabled` is for pausing a model, not for removing one.

### `protected` models

```sqlx
config {
  type: "table",
  protected: true
}
```

Dataform refuses to run destructive operations against the relation — no overwrite, no drop —
without an explicit override. It is the "do not accidentally destroy my mart" switch.

### Ephemeral models and the graph

An `ephemeral` model is a node in the DAG that produces **no relation**. It is inlined into its
dependents as a CTE.

```
    WITH a materialized model:
    ┌──────────────┐
    │ stg_orders   │
    └──────┬───────┘
    ┌──────▼───────┐
    │ fct_orders   │        ← one physical table
    └──────────────┘

    WITH an ephemeral model in between:
    ┌──────────────┐
    │ stg_orders   │
    └──────┬───────┘
    ┌──────▼───────┐     ┌────────────────┐
    │ int_enriched │────▶│ → CTE inside   │
    │ (ephemeral)  │     │   fct_orders   │
    └──────────────┘     └────────────────┘
```

⚠️ **An ephemeral model shared by two materialized models is inlined into both** — the CTE is
duplicated, and the upstream work is done twice. If you want the work done once, make it a
`view` or a `table`.

### `action_selector` and `actions`

In `workflows/*.json`, `actionSelector` picks *which* actions a workflow covers, and `actions`
gives the per-action detail.

```json
{
  "workflows": [
    {
      "name": "orders",
      "tags": ["daily"],
      "actionSelector": ["orders"],
      "actions": [
        { "name": "fct_orders", "tags": ["daily"], "disabled": false }
      ]
    }
  ]
}
```

The three action types:

| Action | What it does |
|--------|--------------|
| `build` | Creates or replaces the target relation. The DDL. |
| `run` | Executes the model's query. |
| `test` | Runs the unit tests and assertions attached to the model. |

```bash
# Build only — create the table, don't populate it
dataform run --actions build

# Run only — populate, don't create/replace
dataform run --actions run

# Test only — assertions and unit tests, no data written
dataform run --actions test

# All three
dataform run --actions build,run,test
```

💡 **`--actions test` is a cheap CI gate.** It validates your data quality rules without
touching the production tables — ideal as a pull-request check.

### Compiling a subgraph

```bash
# Compile one model and its upstream dependencies
dataform compile --nodes fct_orders

# Compile several
dataform compile --nodes stg_orders,fct_orders

# Include downstream models too
dataform run --nodes fct_orders --include-dependents
```

💡 **This is your inner-loop command.** While iterating on one model, `--nodes` means you
compile and run one thing instead of the whole warehouse.

---

## 🛠️ Hands-On: Trace a Dependency Graph

### Step 1 — Build a three-model chain

`definitions/sources/raw_orders.sqlx`:

```sqlx
config {
  type: "declarative",
  database: "source-project",
  schema: "raw",
  description: "Raw orders landing table",
  loaded_at_field: "_loaded_at",
  freshness: { errorAfter: "48h", warnAfter: "24h" }
}

source("raw_orders", "orders")
```

`definitions/stg/stg_orders.sqlx`:

```sqlx
config { type: "table", description: "Staged orders" }

SELECT order_id, customer_id, order_date, total_amount
FROM ${source("raw_orders", "orders")}
```

`definitions/marts/fct_orders.sqlx` — same shape, but reading the model:

```sqlx
config { type: "table", description: "Order fact table" }

SELECT o.order_id, o.customer_id, o.order_date, o.total_amount
FROM ${ref("stg_orders")} o
```

### Step 2 — Compile and read the DAG

```bash
dataform compile

python3 -c "
import json
d = json.load(open('.dataform/run.json'))
for name, node in d['dag'].items():
    deps = [x['target']['name'] for x in node.get('dependencies', [])]
    print(f'{name} <- {deps}')
"
```

Expected output:

```text
stg_orders <- []
fct_orders <- ['stg_orders']
```

### Step 3 — Trigger the missing-ref error

Temporarily break the reference:

```sqlx
FROM ${ref("stg_orderz")}
```

```bash
dataform compile
```

Record the exact error text. Now fix it and confirm the compile returns to `0`.

### Step 4 — Add a second dependency and watch the graph change

```sqlx
SELECT o.order_id, o.customer_id, o.total_amount, c.segment
FROM ${ref("stg_orders")} o
JOIN ${ref("dim_customers")} c ON o.customer_id = c.customer_id
```

```bash
dataform compile
```

Re-run the DAG dump from Step 2. Now `fct_orders <- ['stg_orders', 'dim_customers']`.

### Step 5 — Use a cross-schema reference

```sqlx
config {
  type: "view",
  schema: "marts"
}

SELECT o.order_id, o.total_amount
FROM ${ref("stg_orders")} o
JOIN ${ref("dim_customers", { schema: "dims" })} c
    ON o.customer_id = c.customer_id
```

```bash
dataform compile
grep -o "dims\.dim_customers\|analytics\.dim_customers" .dataform/run.sql | sort -u
```

### Step 6 — Compile a subgraph

```bash
dataform compile --nodes fct_orders
dataform run --nodes fct_orders --dry-run
```

Compare the action list against `dataform run --dry-run` for the whole project. The subgraph
should contain only `fct_orders` and its upstream dependencies.

### Step 7 — Test the action types

```bash
dataform run --actions test --dry-run
dataform run --actions build --dry-run
dataform run --actions run --dry-run
```

### Step 8 — Disable a model and observe

```sqlx
config {
  type: "table",
  disabled: true
}
```

```bash
dataform run --dry-run
```

The model no longer appears as an action to execute, but it still resolves in the DAG.

---

## 🔑 Key Takeaways

- `ref()` resolves in four steps: find the model by filename → apply the schema → apply the database → return the qualified name.
- Precedence, highest first: the `ref()` call's own override → the model's `config` → `dataform.json` `warehouse` → `dataform.json` `default*`.
- `config { schema: "x" }` controls where a model is **written**; `ref("y", { schema: "x" })` controls where `y` is **read from**. Different things.
- The `sources/` folder rule: **file name = source name, `source()` argument = table name.** A mismatch is a compile error.
- Source config needs `type: "declarative"`. `loaded_at_field` + `freshness` (`warnAfter` / `errorAfter`) gives you staleness monitoring on external feeds.
- Sources are leaves — they have no buildable node and produce no DAG edges.
- The DAG is built by: parse → extract config → scan for `ref()`/`source()` → add `dependencies` edges → topological sort → resolve names → emit `run.sql` and `run.json`.
- Read `run.json`'s `dag.<model>.dependencies` to see a model's upstream nodes. `targets` is the full model inventory.
- Independent models run in parallel — that is where BigQuery slot-time savings come from.
- A **cycle is a compile error**, and it almost always means a design problem, not a typo.
- A **missing `ref()` is a compile error** naming the model and the missing reference. Nothing is written to BigQuery.
- `dependencies` is for *ordering* edges the SQL does not imply. It does not make data readable — that needs `ref()`.
- `disabled` compiles but does not execute, and does **not** delete an existing table. `protected` blocks destructive operations.
- An ephemeral model produces no relation; if two materialized models share it, the CTE is duplicated and the work is done twice.
- `actions` are `build` (DDL), `run` (execute the query), and `test` (unit tests and assertions). `--actions test` is a cheap CI gate.

---

## 📚 Practice Exercises

1. **Resolution truth table.** For a model `fct_orders` with `config { schema: "marts" }` calling `ref("stg_orders")`, where `stg_orders` has `config { schema: "staging" }` and `dataform.json` has `defaultDataset: "analytics"` and `warehouse.schema: "analytics"` — work out the fully-qualified relation for each of the four resolution steps. Then repeat with `ref("stg_orders", { schema: "raw_staging" })` and explain exactly which table gets written and which gets read.

2. **Broken graph, then fix.** Create four models that form a cycle (`a → b → c → d → a`). Record the compiler's error message verbatim. Then refactor: extract the shared logic into a fifth model so the cycle becomes a diamond. Re-derive the DAG and confirm the compile succeeds. Explain why a cycle in a BigQuery pipeline is a modelling smell rather than a scheduling problem.

3. **Source naming trap.** Write a source file `definitions/sources/orders.sqlx` containing `source("raw_orders", "orders")`. Compile and record the error. Then fix it two different ways — rename the file, and rename the argument — and explain the difference in what each fix means for downstream models.

4. **Freshness monitor.** Add `loaded_at_field` and `freshness` to two sources: one that loads hourly and one that loads daily. Set `warnAfter`/`errorAfter` appropriately for each. Write the exact queries you would run to check whether the source has actually been updated, and explain how Dataform's freshness check would have caught a silent upstream failure that your query would have missed.

5. **Subgraph surgery.** Build a project with 12 models. Use `dataform compile --nodes` and `--include-dependents` to compile three different subgraphs, and record the action count each time. Then use `--actions build`, `--actions run`, and `--actions test` separately and explain what each produces. Finally, design a `workflows/` file with two workflows (an hourly `stg` one and a nightly `marts` one) and show how the compiled action lists differ.

---

## 📖 Further Reading

- Dataform `ref()` and `source()` — https://cloud.google.com/dataform/docs/reference/sqlx-ref-and-source
- Dataform dependency graph — https://cloud.google.com/dataform/docs/concepts/dependency-graph
- Dataform configuration reference — https://cloud.google.com/dataform/docs/reference/config
- Dataform `dataform.json` reference — https://cloud.google.com/dataform/docs/reference/dataform-json
- Dataform assertions — https://cloud.google.com/dataform/docs/tests/assertions
- Dataform unit tests — https://cloud.google.com/dataform/docs/tests/unit-tests
- Dataform CLI reference — https://cloud.google.com/dataform/docs/reference/cli
- BigQuery IAM roles — https://cloud.google.com/bigquery/docs/access-control
