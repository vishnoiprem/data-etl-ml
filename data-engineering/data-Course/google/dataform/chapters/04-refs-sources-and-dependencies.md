# 1.4 — Refs, Sources & the Dependency Graph

> **Section 1 · Foundations · Lecture 1.4 · 15:20**

## 🎯 What you will learn

- How `ref()` resolves a name to a fully-qualified relation, step by step
- The precedence rules between project settings, per-action `config`, and `ref()` overrides
- How Dataform discovers declarations, and what the `type: "declaration"` config means
- How the dependency graph is built, and how to read `.dataform/run.json` to inspect it
- Topological ordering, cycles, and how the compiler reports a missing `ref()`
- `dependencies` for non-SQL dependencies; `disabled` and `protected` actions
- Cross-schema and cross-project refs; `action_selector` and the `actions` types

---

## 🧠 Concept

### How a `ref()` resolves

`ref()` looks up an action **by name** — the filename without the extension — and returns its
fully-qualified relation. The resolution is a strict sequence:

```
  ref("stg_orders")
        │
        ▼
 ① FIND THE ACTION
   Look for stg_orders.sqlx (or stg_orders.js) under definitions/
   The name is the filename without its extension.
        │
        ▼
 ② APPLY THE TARGET SCHEMA
   Which dataset? Resolution order (first match wins):
      a. the schema in the ref() call itself
         ref({ name: "stg_orders", schema: "other_schema" })
      b. the action's own config { schema: "..." }
      c. workflow_settings.yaml → defaultDataset
        │
        ▼
 ③ APPLY THE TARGET DATABASE
   Same precedence:
      a. ref({ name: "stg_orders", database: "other-project" })
      b. the action's own config { database: "..." }
      c. workflow_settings.yaml → defaultProject
        │
        ▼
 ④ RETURN THE QUALIFIED NAME
   `my-project.analytics.stg_orders`
```

The result is substituted into your SQL as a literal, and **a DAG edge is created** from
`stg_orders` to the action that called `ref()`.

### The precedence table

This is the single most useful thing to internalize:

| Priority | Source | Example |
|----------|--------|---------|
| 1 (highest) | The `ref()` call itself | `ref({ name: "stg_orders", schema: "other_schema" })` |
| 2 | The action's own `config` block | `config { schema: "staging" }` |
| 3 (lowest) | `workflow_settings.yaml` | `defaultDataset`, `defaultProject` |

💡 **A per-action `config { schema: ... }` affects where that action is *written*.** A
`ref({ schema: ... })` affects where the referenced action is *read from*. They are different
things, and mixing them up is the classic "why is my table in the wrong dataset" bug.

### The `ref()` call forms

```sqlx
${ref("name")}                                       // name only
${ref("schema", "name")}                             // schema + name
${ref("database", "schema", "name")}                 // full path
${ref({ name: "name", schema: "schema", database: "database" })}  // object form
```

- With **one** value, the default database and schema are used; the value is the `name`.
- With **two** values, the default database is used; the values are `schema` and `name`.
- With **three** values, they are `database`, `schema`, and `name`.
- The **object form** is the most readable and is the one to reach for when you need to override
  the schema.

⚠️ **`ref("name", { schema: "other" })` is not a documented call form.** The documented forms are
the positional ones and the object form. Use `ref({ name: "name", schema: "other" })`.

### Cross-schema and cross-project refs

The normal case: actions in a different dataset within the same project.

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
FROM ${ref({ name: "shared_dim_customer",
             database: "shared-analytics-prod",
             schema: "dims" })}
```

⚠️ **Cross-project refs require IAM.** The identity running the pipeline needs
`roles/bigquery.dataViewer` (or `dataEditor`) on the other project, and — for Dataform Cloud —
the workspace's service account must have it too. This is the most common cause of a
"permission denied" that only appears in production, because local development runs under your
own user account.

### Data source declarations

A **declaration** tells Dataform about a table that already exists and that Dataform does not
create.

```sqlx
// definitions/sources/raw_orders.sqlx

config {
  type: "declaration",
  database: "source-project",
  schema: "raw",
  name: "orders"
}
```

```
┌──────────────────────────────────────────────────────────────────┐
│  FILE: definitions/sources/raw_orders.sqlx                       │
│                                                                  │
│  config { type: "declaration", ... }                             │
│         │             │             │                           │
│         │             │             └── "orders" = the NAME     │
│         │             └── "raw" = the SCHEMA (dataset)           │
│         └── "source-project" = the DATABASE (project)           │
│                                                                  │
│  Models reference it as: ${ref("orders")}                       │
│     → source-project.raw.orders                                 │
└──────────────────────────────────────────────────────────────────┘
```

💡 **The declaration's `name` is the action name.** It is what other actions reference. The
`database` and `schema` tell Dataform where the physical table lives — and they can differ from
your project's defaults, which is exactly how you point at an upstream or shared dataset.

⚠️ **A declaration produces no build step.** There is nothing to compile and nothing to create.
But it *is* a real node in the graph: `ref("orders")` creates a normal DAG edge, and Dataform
will not try to build `source-project.raw.orders`.

For multiple declarations, use a JavaScript file:

```javascript
// definitions/declarations.js

declare({ database: "source-project", schema: "raw", name: "orders" });
declare({ database: "source-project", schema: "raw", name: "customers" });
```

### How the dependency graph is built

The compiler does this, in order:

```
   ① PARSE every .sqlx and .js file under definitions/
        ▼
   ② EXTRACT the config block → an action per file
        ▼
   ③ SCAN the SQL body for ref() calls
        │
        └─► ref("x")  → edge: x  ──►  this action
        ▼
   ④ ADD explicit config { dependencies: [...] } edges
        ▼
   ⑤ TOPOLOGICALLY SORT the graph → execution order
        ▼
   ⑥ RESOLVE each ref() to a fully-qualified relation name
        ▼
   ⑦ GENERATE the compiled SQL + the graph (.dataform/run.json)
```

💡 **`resolve()` deliberately does not create an edge.** That is its whole difference from
`ref()`. Use `ref()` when you need ordering; use `resolve()` when you only need the name.

### Reading `.dataform/run.json`

```json
{
  "targets": [
    { "name": "stg_orders",
      "relation": "my-project.analytics.stg_orders",
      "type": "table",
      "fileName": "definitions/stg_orders.sqlx" },
    { "name": "fct_orders",
      "relation": "my-project.analytics.fct_orders",
      "type": "incremental",
      "fileName": "definitions/fct_orders.sqlx" }
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

| Field | What it tells you |
|-------|-------------------|
| `targets` | Every action, with its resolved relation, type, and source file. |
| `dag.<action>.relations` | The relations an action produces. |
| `dag.<action>.dependencies` | The upstream nodes it depends on. **This is your dependency list.** |
| `operations` | The ordered list of actions to execute. |
| `tests` | Assertions attached to the graph. |

```bash
# Pretty-print the graph
python3 -m json.tool .dataform/run.json | head -60

# List every action and its dependencies
python3 -c "
import json
d = json.load(open('.dataform/run.json'))
for name, node in d['dag'].items():
    deps = [x['target']['name'] for x in node.get('dependencies', [])]
    print(f'{name} <- {deps}')
"
```

💡 **In Dataform Cloud, the same information is visual.** The **Compiled graph** tab shows your
workflow as an interactive DAG, filterable by name, tag, and type (assertion, declaration,
incremental table, operation, table, view). Clicking an action shows its full name, type,
dependencies, and dependents. The `run.json` file is the local equivalent of that view.

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
exploits this — independent nodes execute concurrently, which is where the BigQuery slot-time
savings come from.

⚠️ **The compiler cannot invent a dependency from shared tables.** If two actions read the same
declaration and you assume one must run first, you are wrong — they are independent by
definition.

### Cycles — and how the compiler reports them

A cycle is impossible to order: A needs B, B needs C, C needs A. Dataform rejects it at
compile time.

```
    stg_a ──▶ stg_b ──▶ stg_c ──▶ stg_a
      ▲                            │
      └────────────────────────────┘
```

The error names the actions involved in the cycle. The fix is to break the loop — usually by
extracting the shared logic into a third action that both depend on:

```
    stg_a ──▶ stg_b ──┐
                      ├──▶ stg_shared ──▶ stg_c
    stg_d ──▶ stg_e ──┘
```

⚠️ **A cycle is almost always a design smell, not a typo.** It usually means two actions are
doing each other's jobs — and in BigQuery, a self-referencing table is usually better expressed
with `self()` than with a cycle.

### A worked compile error — a missing ref

Create an action that references something that does not exist:

```sqlx
// definitions/fct_orders.sqlx

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
    Check that the action 'stg_orderz' exists in the project and that
    the file name matches the action name.
```

Three things to notice:

1. **The error names the action and the missing reference.** You do not have to hunt for it.
2. **Nothing was written to BigQuery.** The compiler stopped before any query ran.
3. **The error is a compile error, not a runtime error.** The "table does not exist" failure mode
   from Chapter 1.1 cannot happen here.

Fix it — create `definitions/stg_orderz.sqlx`, or correct the typo to `ref("stg_orders")`. Then
`dataform compile; echo $?` returns `0`.

### The graph before and after a dependency

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

- An action must run *after* a cleanup/audit action finishes
- An action must not run concurrently with another action (e.g. both write the same partition)
- An action must run after a custom operation on another action

💡 **There are two ways to declare a dependency.** Either reference it as an argument of `ref()`
in a `SELECT` statement, or declare a list of `dependencies` in the `config` block. The `config`
block form is for dependencies that are not referenced in the SQL statement but still need to run
before the action.

⚠️ **`dependencies` does not make data available.** If action A reads action B's table, you must
use `ref("B")`. Adding `dependencies: ["B"]` without a `ref()` gives you ordering but no
readability — and the compiler will still complain about an unresolved table name.

### `disabled` actions

```sqlx
config {
  type: "table",
  disabled: true
}
```

If set to true, the action is **not run**. The action can still be depended upon — useful for
temporarily turning off broken actions without breaking everything downstream.

⚠️ **A `disabled` action is not deleted.** If it already produced a table, the table stays in
BigQuery with stale data. Downstream actions that read it will keep working — with stale data.
`disabled` is for pausing an action, not for removing one.

### `protected` actions

```sqlx
config {
  type: "incremental",
  protected: true
}
```

⚠️ **`protected` is only allowed for the `incremental` type.** When set to true, running the
action ignores the `full-refresh` option. This is useful for tables built from transient data,
to verify that historical data is never lost.

### `action_selector` and `actions`

Actions are grouped and selected by **tag**. A `tag` is a list of strings in an action's `config`
block, and it is how you select a subset of the graph to build, run, or test.

```sqlx
config {
  type: "table",
  tags: ["daily", "marts"]
}
```

The three action types:

| Action | What it does |
|--------|--------------|
| `build` | Creates or replaces the target relation. The DDL. |
| `run` | Executes the action's query. |
| `test` | Runs the assertions attached to the action. |

```bash
# Build only — create the relation, don't populate it
dataform run --actions build

# Run only — populate, don't create/replace
dataform run --actions run

# Test only — assertions, no data written
dataform run --actions test

# All three
dataform run --actions build,run,test
```

💡 **`--actions test` is a cheap CI gate.** It validates your data quality rules without
touching the production tables — ideal as a pull-request check.

### Compiling a subgraph

```bash
# Compile one action and its upstream dependencies
dataform compile --nodes fct_orders

# Compile several
dataform compile --nodes stg_orders,fct_orders

# Include downstream actions too
dataform run --nodes fct_orders --include-dependents
```

💡 **This is your inner-loop command.** While iterating on one action, `--nodes` means you
compile and run one thing instead of the whole warehouse.

---

## 🛠️ Hands-On: Trace a Dependency Graph

### Step 1 — Build a three-action chain

`definitions/sources/raw_orders.sqlx`:

```sqlx
config {
  type: "declaration",
  database: "source-project",
  schema: "raw",
  name: "orders"
}
```

`definitions/stg_orders.sqlx`:

```sqlx
config { type: "table", description: "Staged orders" }

SELECT order_id, customer_id, order_date, total_amount
FROM ${ref("orders")}
```

`definitions/fct_orders.sqlx`:

```sqlx
config { type: "table", description: "Order fact table" }

SELECT o.order_id, o.customer_id, o.order_date, o.total_amount
FROM ${ref("stg_orders")} o
```

### Step 2 — Compile and read the graph

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

Re-run the graph dump from Step 2. Now `fct_orders <- ['stg_orders', 'dim_customers']`.

### Step 5 — Use a cross-schema reference

```sqlx
config {
  type: "view",
  schema: "marts"
}

SELECT o.order_id, o.total_amount
FROM ${ref("stg_orders")} o
JOIN ${ref({ name: "dim_customers", schema: "dims" })} c
    ON o.customer_id = c.customer_id
```

```bash
dataform compile
grep -o "dims\.dim_customers\|analytics\.dim_customers" .dataform/run.sql | sort -u
```

### Step 6 — Declare an ordering dependency

```sqlx
config {
  type: "table",
  dependencies: ["stg_orders"]
}
```

```bash
dataform compile
```

Note the edge appears in `dag` even though the SQL does not reference `stg_orders`.

### Step 7 — Compile a subgraph

```bash
dataform compile --nodes fct_orders
dataform run --nodes fct_orders --dry-run
```

Compare the action list against `dataform run --dry-run` for the whole project. The subgraph
should contain only `fct_orders` and its upstream dependencies.

### Step 8 — Test the action types

```bash
dataform run --actions test --dry-run
dataform run --actions build --dry-run
dataform run --actions run --dry-run
```

### Step 9 — Disable an action and observe

```sqlx
config {
  type: "table",
  disabled: true
}
```

```bash
dataform run --dry-run
```

The action no longer appears as an action to execute, but it still resolves in the graph.

---

## 🔑 Key Takeaways

- `ref()` resolves in four steps: find the action by filename → apply the schema → apply the database → return the qualified name.
- Precedence, highest first: the `ref()` call's own override → the action's `config` → `workflow_settings.yaml` defaults.
- `config { schema: "x" }` controls where an action is **written**; `ref({ schema: "x" })` controls where the referenced action is **read from**. Different things.
- The documented `ref()` forms are positional (`ref("name")`, `ref("schema","name")`, `ref("database","schema","name")`) and the object form `ref({ name, schema, database })`. A name followed by an options object is **not** documented.
- Declarations live in `definitions/` like any other file — `type: "declaration"`, with `name`, `schema`, and `database`. There is no special `sources/` folder.
- A declaration produces no build step, but it is a real graph node: `ref()` on one creates a normal DAG edge.
- `resolve()` resolves a reference **without** adding a dependency. That is the whole difference from `ref()`.
- The graph is built by: parse → extract config → scan for `ref()` → add `dependencies` edges → topological sort → resolve names → emit `run.sql` and `run.json`.
- Read `run.json`'s `dag.<action>.dependencies` to see upstream nodes. In Dataform Cloud, the **Compiled graph** tab is the visual equivalent.
- Independent actions run in parallel — that is where BigQuery slot-time savings come from.
- A **cycle is a compile error**, and it almost always means a design problem, not a typo.
- A **missing `ref()` is a compile error** naming the action and the missing reference. Nothing is written to BigQuery.
- There are two ways to declare a dependency: `ref()` in a `SELECT`, or `dependencies` in the `config` block for ordering-only edges.
- `disabled` means the action is not run but **can still be depended upon** — and does **not** delete an existing table. `protected` is **incremental only** and makes the action ignore `full-refresh`.
- Actions are `build` (DDL), `run` (execute the query), and `test` (assertions). `--actions test` is a cheap CI gate.

---

## 📚 Practice Exercises

1. **Resolution truth table.** For an action `fct_orders` with `config { schema: "marts" }` calling `ref("stg_orders")`, where `stg_orders` has `config { schema: "staging" }` and `workflow_settings.yaml` has `defaultDataset: "analytics"` — work out the fully-qualified relation for each of the four resolution steps. Then repeat with `ref({ name: "stg_orders", schema: "raw_staging" })` and explain exactly which table gets written and which gets read.

2. **Broken graph, then fix.** Create four actions that form a cycle (`a → b → c → d → a`). Record the compiler's error message verbatim. Then refactor: extract the shared logic into a fifth action so the cycle becomes a diamond. Re-derive the graph and confirm the compile succeeds. Explain why a cycle in a BigQuery pipeline is a modelling smell rather than a scheduling problem.

3. **Declaration naming trap.** Create `definitions/sources/raw_orders.sqlx` with `config { type: "declaration", database: "source-project", schema: "raw", name: "orders" }`. Now try to add a *second* declaration to the same file by appending another `config { ... }` block — compile and record what happens. Then move the second declaration into a JavaScript file (`definitions/declarations.js`) using `declare({...})` and confirm it compiles. Explain why multiple declarations belong in a `.js` file rather than a `.sqlx` file.

4. **Freshness is not free — design the equivalent.** Dataform Cloud does not ship a built-in `freshness` block on declarations. Design the equivalent yourself: write a custom SQL operation that reads the source's load timestamp and raises a failure when it is too old. Show how you would wire it into the graph as a dependency of every action that reads that source, and explain how you would surface the failure.

5. **Subgraph surgery.** Build a project with 12 actions. Use `dataform compile --nodes` and `--include-dependents` to compile three different subgraphs, and record the action count each time. Then use `--actions build`, `--actions run`, and `--actions test` separately and explain what each produces. Finally, tag your actions (`daily`, `hourly`, `marts`) and show how tagging lets you select a subset.

---

## 📖 Further Reading

- Dataform core reference — https://cloud.google.com/dataform/docs/reference/dataform-core-reference
- Declare dependencies — https://cloud.google.com/dataform/docs/dependencies
- Declare data sources — https://cloud.google.com/dataform/docs/declare-source
- Create a development workspace — https://cloud.google.com/dataform/docs/create-workspace
- Configure compilation — https://cloud.google.com/dataform/docs/configure-compilation
- Add custom SQL operations — https://cloud.google.com/dataform/docs/custom-sql
- Dataform assertions — https://cloud.google.com/dataform/docs/assertions
- Using the Dataform CLI — https://cloud.google.com/dataform/docs/use-dataform-cli
