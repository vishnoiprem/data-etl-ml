# 1.3 — The SQLX Language & Core Concepts

> **Section 1 · Foundations · Lecture 1.3 · 16:05**

## 🎯 What you will learn

- What SQLX actually is: SQL + JSX-style expressions + a config block
- The file structure — `config` block first, then the SQL
- Every field in the `config` block, and what each one changes about the compiled output
- `ref()`, `resolve()`, `self()`, `when()`, and `incremental()` — the context methods
- Data source declarations, custom SQL operations, and assertions
- How SQLX compares to plain SQL and to dbt's Jinja

---

## 🧠 Concept

### What SQLX is

SQLX is a **superset of SQL**. It is SQL, plus two additions:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  1. A CONFIG BLOCK      config { type: "table", ... }                   │
│     → declarative metadata: materialization, partitioning, assertions   │
├──────────────────────────────────────────────────────────────────────────┤
│  2. SQLX EXPRESSIONS   ${ref("stg_orders")}                            │
│     → JSX-style interpolation of compiler-resolved values               │
└──────────────────────────────────────────────────────────────────────────┘
```

Everything in a `.sqlx` file is one of those two things. The SQL part is ordinary SQL that
BigQuery executes. The config block is metadata the compiler reads. The expressions are
placeholders the compiler substitutes.

SQLX files can also contain JavaScript blocks (`js { ... }`) for local constants and functions.

### The file structure

The `config` block comes first, and the compiler enforces it:

```
definitions/stg_orders.sqlx

┌─────────────────────────────────────────────────────────────┐
│ ① config { ... }        ← FIRST. Declarative metadata.      │
├─────────────────────────────────────────────────────────────┤
│ ② SELECT ...            ← the SQL body                     │
└─────────────────────────────────────────────────────────────┘
```

```sqlx
config {
  type: "table",
  description: "Staged orders"
}

SELECT *
FROM ${ref("orders")}
```

⚠️ **The `config` block must come first.** Putting SQL before `config` is a compile error, and
there can be only one `config` block per file.

### The `config` block — full reference

The core config interface, `ITableConfig`, extends `IActionConfig`, `IDependenciesConfig`,
`IDocumentableConfig`, `INamedConfig`, and `ITargetableConfig`:

| Field | Type | Purpose |
|-------|------|---------|
| `type` | string | **Required.** `table`, `view`, or `incremental`. |
| `name` | string | Action name. Defaults to the filename without the extension. |
| `schema` | string | Override the target BigQuery dataset for this action. |
| `database` | string | Override the target GCP project for this action. |
| `description` | string | Human description, surfaced in the catalog and lineage. |
| `columns` | object | Per-column descriptions, display names, tags, BigQuery policy tags. |
| `uniqueKey` | string[] | Column(s) that uniquely identify a row. Used for merge criteria. |
| `partitionBy` | string | Partition expression, e.g. `"DATE(order_date)"`. Also settable as `bigquery.partitionBy`. |
| `clusterBy` | string[] | Clustering column(s). |
| `labels` | object | BigQuery table labels (key → value). |
| `tags` | string[] | Dataform tags for action selection. |
| `disabled` | boolean | If true, the action is not run — but can still be depended upon. |
| `protected` | boolean | **Incremental only.** Running the action ignores `full-refresh`. |
| `dependencies` | string[] | Extra DAG edges to actions not referenced in the SQL. |
| `hermetic` | boolean | Whether all dependencies are explicitly declared. |
| `dependOnDependencyAssertions` | boolean | Whether this action also depends on its dependencies' assertions. |
| `assertions` | object | Automatic assertions generated for this action. |
| `materialized` | boolean | **View only.** Create a BigQuery materialized view. |
| `onSchemaChange` | string | **Incremental only.** `IGNORE`, `FAIL`, `EXTEND`, or `SYNCHRONIZE`. |
| `bigquery` | object | BigQuery-specific warehouse options. |
| `preserveGovernanceControls` | boolean | Re-apply BigQuery policies and governance tags on recreation. |

#### `type` — the three materializations

There are exactly **three** types:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ type: "table"        → CREATE OR REPLACE TABLE. Full rebuild every run.│
│   Use for: staging layers, aggregates that must be exactly right.      │
├──────────────────────────────────────────────────────────────────────────┤
│ type: "view"         → CREATE OR REPLACE VIEW. No data stored.         │
│   Use for: thin transformations, dimension lookups, dashboards.         │
│   + `materialized: true` creates a BigQuery materialized view.          │
├──────────────────────────────────────────────────────────────────────────┤
│ type: "incremental"  → MERGE into an existing table. Only changed rows  │
│   are written. Requires uniqueKey and a WHERE clause.                  │
│   Use for: large, append-mostly fact tables.                           │
└──────────────────────────────────────────────────────────────────────────┘
```

⚠️ **`table` rebuilds the whole thing every run.** On a 2-billion-row table that is a full scan
and a full rewrite — every time. `incremental` exists to avoid exactly that.

⚠️ **An `incremental` table must include a WHERE clause.** This is a hard requirement, not a
style guideline — it is what makes the incremental run bounded.

#### `uniqueKey` — the merge criterion

```sqlx
config {
  type: "incremental",
  uniqueKey: ["order_id"]
}
```

Records with matching unique key(s) are **updated** instead of new rows being inserted. It is a
list, even when there is only one column.

#### `hermetic`

```sqlx
config {
  type: "table",
  hermetic: true
}
```

Declares whether the action is hermetic — that is, whether **all of its dependencies are
explicitly declared**. If the action depends on data from a source that is not declared as a
dependency, set `hermetic` to `false`. Otherwise, set it to `true`.

💡 **Set `hermetic: true` and the compiler enforces it.** An undeclared table reference in a
hermetic action is a compile error, not a silent bug. This is the cheapest guard against
introducing a dependency the graph does not know about.

#### `protected`

```sqlx
config {
  type: "incremental",
  protected: true
}
```

⚠️ **`protected` is only allowed for the `incremental` type.** When set to true, running the
action ignores the `full-refresh` option. This is useful for tables built from transient data,
to verify that historical data is never lost.

#### `onSchemaChange` — what happens when the schema drifts

Only valid for `incremental` tables. Dataform checks the `SELECT` query to determine if columns
were added or removed, then performs the action you specify:

| Value | Behavior |
|-------|----------|
| `IGNORE` (default) | Ignores added columns; errors on missing columns. |
| `FAIL` | Stops the action if any schema change is detected. |
| `EXTEND` | Adds new columns with `NULL` for previous records; errors on removed columns. |
| `SYNCHRONIZE` | Adds new columns and removes columns no longer in the query. **Cannot be undone.** |

⚠️ **`SYNCHRONIZE` can lose data.** Removing a column from the query drops it from the table
and all its historical values. Use `EXTEND` unless you are certain.

#### `assertions` in config

```sqlx
config {
  type: "table",
  assertions: {
    nonNull: ["order_id", "customer_id"],
    uniqueKey: ["order_id"],
    uniqueKeys: [["order_id"], ["order_id", "line_number"]],
    rowConditions: ["total_amount >= 0"]
  }
}
```

| Assertion | Meaning |
|-----------|---------|
| `nonNull` | Column(s) which can never be `NULL`. |
| `uniqueKey` | Column(s) constituting the unique key index. |
| `uniqueKeys` | Combinations of columns, each of which is a unique key. |
| `rowConditions` | General conditions that must hold true for all rows. |

When configured, the relevant assertions are **automatically created and run as a dependency**
of the table.

#### `bigquery` specific options

```sqlx
config {
  type: "table",
  bigquery: {
    partitionBy: "order_date",
    partitionExpirationDays: 90,
    clusterBy: ["customer_id"],
    updatePartitionFilter: "TRUE",
    requirePartitionFilter: true,
    labels: { team: "analytics", tier: "gold" },
    additionalOptions: { "option-name": '"value"' }
  }
}
```

`requirePartitionFilter: true` makes BigQuery **reject queries** that scan the table without a
partition filter — a cost guardrail at the database level, not just a convention.

`additionalOptions` passes options straight through to the BigQuery API. String values must be
double-quoted inside the string: `'"string-value"'`.

### `ref()` — the core of the language

`ref()` is the single most important function in Dataform. It does four things at once:

```
        ref("stg_orders")
                 │
    ┌────────────┼────────────────────────────────────────┐
    │            │                                        │
    ▼            ▼                                        ▼
 1. RESOLVES   2. CREATES                              3. ENABLES
 the name      a DAG edge                               4. INVALIDATES
    │            │                                        │
    ▼            ▼                                        ▼
"my-project.  stg_orders runs                      fct_orders is
analytics.    BEFORE fct_orders                      marked stale
stg_orders"                                           when stg_orders
                                                      changes
```

The `${...}` wrapper is JSX-style interpolation: the expression is evaluated at compile time and
the result is substituted into the SQL text as a literal.

⚠️ **`ref()` resolves to a fully-qualified relation, not a CTE.** `FROM ${ref("stg_orders")}`
compiles to `FROM \`my-project.analytics.stg_orders\``. There is no join, no subquery, no
materialization — it is a straight reference to the upstream table.

#### The `ref()` call forms

```sqlx
${ref("name")}                                       // name only
${ref("schema", "name")}                             // schema + name
${ref("database", "schema", "name")}                 // full path
${ref({ name: "name", schema: "schema", database: "database" })}  // object form
```

- With **one** value, the default database and schema are used, and the value is the `name`.
- With **two** values, the default database is used and the values are `schema` and `name`.
- With **three** values, they are `database`, `schema`, and `name`.
- The **object form** `{ name, schema, database }` is the most readable, and it is the form to
  reach for when you need to override the schema.

```sqlx
// Read from a different dataset
FROM ${ref({ name: "stg_orders", schema: "raw_staging" })}
```

⚠️ **The override order matters when you mix forms.** `ref("schema", "name")` is positional;
`ref({ name: ..., schema: ... })` is named. Passing `ref("name", { schema: "other" })` — a name
followed by an options object — is **not** a documented call form. Use the object form
`ref({ name: "name", schema: "other" })` or the positional form `ref("schema", "name")`.

### `resolve()` — resolving without a dependency

`resolve()` works like `ref()`, but **instead of adding a dependency**, it resolves the provided
reference so it can be used in SQL.

```sqlx
config { type: "view" }

SELECT *
FROM ${resolve("stg_orders")}
```

💡 **Use `resolve()` when you need the table name but not the ordering.** For example, in a
`UNION ALL` branch you want to read the current state of a table without forcing a rebuild, or
when you need the qualified name as a string literal rather than in a FROM clause.

### `self()` — referencing your own table

`self()` is equivalent to `resolve(name())`. It returns a valid SQL string referencing the table
produced by this action.

```sqlx
config {
  type: "incremental",
  uniqueKey: ["order_id"]
}

SELECT
    o.order_id,
    o.customer_id,
    o.total_amount,
    COALESCE(c.segment, 'unknown') AS segment
FROM ${ref("orders")} o
LEFT JOIN ${self()} c
    ON o.order_id = c.order_id
```

💡 **`self()` in a join is how you enrich with your own historical state** — cumulative
measures, slowly-changing dimensions, last-known values.

It also works in `post_operations` to grant access on the table you just built:

```sqlx
config { type: "table" }

SELECT * FROM ${ref("orders")}

post_operations {
  GRANT `roles/bigquery.dataViewer`
  ON TABLE ${self()}
  TO "group:analytics@company.com"
}
```

### `when()` — conditional SQL

```sqlx
when(cond: boolean, trueCase: string, falseCase: string) => string
```

Shorthand for an `if` condition — equivalent to `cond ? trueCase : falseCase`. **`falseCase` is
optional and defaults to an empty string.**

```sqlx
config { type: "view" }

SELECT ${when(
  dataform.projectConfig.vars.myVariableName === "myVariableValue",
  "myVariableName is set to myVariableValue!",
  "myVariableName is not set to myVariableValue!"
)}
```

### `incremental()` — is this an incremental run?

```sqlx
incremental() => boolean
```

Returns `true` when the current context indicates that the table will be built incrementally. On
the first run, or a full refresh, it returns `false`.

The standard Dataform incremental idiom combines it with `when()`:

```sqlx
config {
  type: "incremental",
  uniqueKey: ["order_id"]
}

SELECT order_id, customer_id, order_date, total_amount
FROM ${ref("orders")}
WHERE ${when(incremental(), "order_date > @last_run", "TRUE")}
```

This reads as: *on an incremental run, filter to rows after the last run; on a full rebuild,
take everything.*

### Data source declarations

A declaration tells Dataform about an existing table it does not create.

```sqlx
// definitions/sources/raw_orders.sqlx

config {
  type: "declaration",
  database: "source-project",
  schema: "raw",
  name: "orders"
}
```

You declare one source per SQLX file. Reference it with `ref("orders")` — it behaves like any
other action for dependency purposes.

For multiple declarations, use a JavaScript file:

```javascript
// definitions/declarations.js

declare({ database: "source-project", schema: "raw", name: "orders" });
declare({ database: "source-project", schema: "raw", name: "customers" });
```

### Custom SQL operations

`type: "operations"` lets you run arbitrary BigQuery SQL that Dataform passes through
unmodified.

```sqlx
// definitions/cleanup.sqlx

config { type: "operations" }

DELETE FROM dataset.table WHERE country = 'GB';
DELETE FROM dataset.table WHERE country = 'FR';
```

BigQuery runs all the operations in a file in the same context, and creates the run SQL by
joining them with a semicolon.

To create a table that other actions can reference, set `hasOutput: true` and use `self()` in
the `CREATE`:

```sqlx
config {
  type: "operations",
  hasOutput: true
}

CREATE OR REPLACE TABLE ${self()} AS (SELECT 1 AS test)
```

⚠️ **When `hasOutput` is true, the operation's name must match the output table's name.** That
is how Dataform knows what relation the operation produced.

### Assertions

Assertions are data quality test queries. Dataform runs them every time it updates your
workflow, and alerts you if any fail.

```sqlx
// definitions/assertions.sqlx

config { type: "assertion" }

SELECT *
FROM ${ref("fct_orders")}
WHERE order_id IS NULL OR customer_id IS NULL
```

A `type: "assertion"` file can be set as a dependency and as a dependent by declaring
`dependencies` in the `config` block.

💡 **Assertions are how you turn a silent data-quality problem into a failed build.** A model
that produces null keys should fail loudly, not quietly write bad data into a dashboard.

### JavaScript blocks and `includes/`

You can add JavaScript to a SQLX file inline or in a `js` block:

```sqlx
config { type: "view" }

js {
  const columnName = "foo";
}

SELECT
  1 AS ${columnName},
  ${bar(1)} AS two
```

For code shared across a **single file**, use a `js` block. For code shared across the whole
repository, use `includes/`:

```javascript
// includes/constants.js
const launch_date = "11.11.2011";
module.exports = { launch_date };
```

For code shared across **multiple repositories**, create or import a package.

### SQLX vs plain SQL vs dbt Jinja

| Dimension | SQLX | Plain `.sql` | dbt (Jinja) |
|-----------|------|--------------|--------------|
| Templating style | JSX-style `${expression}` | None | Jinja `{{ expression }}` / `{% statement %}` |
| Materialization | Built into `config` | You write the DDL yourself | Macros (`materialization` blocks) |
| Dependency declaration | `ref()` | None — external orchestration | `ref()` |
| Test framework | `type: "assertion"` files + `config.assertions` | You write and run them | `schema.yml` or `dbt tests` |
| Config | `workflow_settings.yaml` + per-file `config` | N/A | `dbt_project.yml` + model `config` |
| Incremental | `incremental()` context method | Manual `MERGE` | `is_incremental()` macro |
| Errors on bad ref | Compile-time, always | Runtime | Compile-time, usually |
| Verbosity | Moderate | None | High — Jinja blocks are dense |
| Portability | Dataform only | Universal | dbt only |

⚠️ **Plain SQL has no dependency awareness at all.** You can write `FROM orders` and the system
has no idea `orders` is produced by another script. That is exactly the failure mode from
Chapter 1.1 — a folder of scripts with encoded-by-filename ordering.

💡 **SQLX is roughly halfway between plain SQL and dbt Jinja in terms of ceremony.** The `config`
block is a formal declaration; the `${}` interpolation is familiar to anyone who has written
React; and tests live next to the code they test.

---

## 🛠️ Hands-On: One File Per Action Type

Create these files under `definitions/`, then run `dataform compile` after each.

### Step 1 — Declare the source

`definitions/sources/raw_orders.sqlx`:

```sqlx
config {
  type: "declaration",
  database: "source-project",
  schema: "raw",
  name: "orders"
}
```

### Step 2 — A `view` action

`definitions/dim_customers.sqlx`:

```sqlx
config {
  type: "view",
  description: "Customer dimension, one row per customer",
  columns: {
    customer_id: { description: "Surrogate key" },
    segment: { description: "Marketing segment" }
  }
}

SELECT
    customer_id,
    customer_name,
    COALESCE(segment, 'unknown') AS segment,
    created_at
FROM ${ref("stg_customers")}
```

### Step 3 — A `table` action

`definitions/stg_orders.sqlx`:

```sqlx
config {
  type: "table",
  description: "Staged orders, deduplicated",
  tags: ["daily"],
  partitionBy: "DATE(order_date)",
  clusterBy: ["customer_id"]
}

SELECT order_id, customer_id, order_date, total_amount
FROM ${ref("orders")}
QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY _loaded_at DESC) = 1
```

### Step 4 — An `incremental` action

`definitions/fct_orders.sqlx`:

```sqlx
config {
  type: "incremental",
  description: "Order fact table, incrementally maintained",
  uniqueKey: ["order_id"],
  partitionBy: "DATE(order_date)",
  clusterBy: ["customer_id"],
  protected: true
}

SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    o.total_amount,
    COALESCE(c.segment, 'unknown') AS segment
FROM ${ref("orders")} o
LEFT JOIN ${self()} c
    ON o.order_id = c.order_id
WHERE ${when(incremental(), "o.order_date > @last_run", "TRUE")}
```

### Step 5 — A custom operation

`definitions/cleanup.sqlx`:

```sqlx
config { type: "operations" }

DELETE FROM `my-project.analytics.stg_orders`
WHERE order_date < DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY);
```

### Step 6 — An assertion

`definitions/assertions.sqlx`:

```sqlx
config { type: "assertion" }

SELECT *
FROM ${ref("fct_orders")}
WHERE order_id IS NULL
```

### Step 7 — Compile and run

```bash
# Compile — catches config errors, missing refs, bad types
dataform compile

# Run the assertions
dataform test

# Compile just one action and its dependencies
dataform compile --nodes fct_orders

# Inspect the compiled SQL for the incremental action — note the MERGE
grep -A 20 "fct_orders" .dataform/run.sql | head -40
```

### Step 8 — Exercise `resolve()` and `when()`

Add a var to `workflow_settings.yaml` — `vars: { region: 'us-east1', minAmount: '10.0' }` —
then use them:

```sqlx
config { type: "view" }

SELECT *
FROM ${ref("stg_orders")}
WHERE region = '${dataform.projectConfig.vars.region}'
  AND total_amount >= ${dataform.projectConfig.vars.minAmount}
```

```bash
dataform compile --vars '{"region": "eu-west1"}'
grep "eu-west1" .dataform/run.sql    # confirms the override reached the SQL
```

### Step 9 — Try the object form of `ref()`

```sqlx
FROM ${ref({ name: "stg_orders", schema: "raw_staging" })}
```

```bash
dataform compile
grep -o "raw_staging\.stg_orders\|analytics\.stg_orders" .dataform/run.sql | sort -u
```

---

## 🔑 Key Takeaways

- SQLX = SQL + `${}` expressions + a `config` block. The `config` block must come first.
- There are exactly three types: `table`, `view`, `incremental`. `table` rebuilds fully, `incremental` merges, `view` stores nothing.
- An `incremental` table **must** have a WHERE clause, and `uniqueKey` is a list — `["order_id"]`, not `"order_id"`.
- `ref()` is four things at once: name resolution, a DAG edge, schema awareness, and an invalidation trigger.
- `ref()` call forms: `ref("name")`, `ref("schema", "name")`, `ref("database", "schema", "name")`, or `ref({ name, schema, database })`. A name followed by an options object is **not** a documented form.
- `resolve()` resolves a reference **without** adding a dependency; `self()` is equivalent to `resolve(name())`.
- `when(cond, trueCase, falseCase)` — `falseCase` is optional and defaults to `""`.
- `incremental()` returns a boolean: true only when the table is being built incrementally. The standard idiom is `WHERE ${when(incremental(), "order_date > @last_run", "TRUE")}`.
- `hermetic: true` means all dependencies are explicitly declared — the compiler enforces it.
- `protected` is **incremental only**; it makes the action ignore `full-refresh`.
- `onSchemaChange` accepts `IGNORE`, `FAIL`, `EXTEND`, `SYNCHRONIZE`. `SYNCHRONIZE` can lose data.
- `config.assertions` supports `nonNull`, `uniqueKey`, `uniqueKeys`, and `rowConditions` — **not** `rowCount`.
- Data source declarations are `type: "declaration"` files in `definitions/`. There is no special `sources/` folder.
- Custom SQL uses `type: "operations"`, with `hasOutput: true` when other actions must reference the output.
- Assertions are `type: "assertion"` files, and Dataform runs them on every workflow update.

---

## 📚 Practice Exercises

1. **Type selection audit.** You have five actions: a customer dimension joined into 40 dashboards, a 3-billion-row click stream, a small currency lookup, a reusable cleansed-orders CTE used by two marts, and a daily aggregate. Assign a `type` to each and justify it. Then find the one that would be most expensive if you got it wrong, and estimate the cost difference.

2. **Config block archaeology.** Take a plain SQL file that creates a partitioned, clustered table with a `CREATE OR REPLACE` and a `DELETE` afterwards. Rewrite it as SQLX. Identify every piece of SQL you moved into `config`, every piece you moved into a `type: "operations"` file, and explain what the compiler now knows that it did not before.

3. **Build an action zoo.** Create one action of each of the three types, plus a declaration, an operation, and an assertion. Compile, then inspect `.dataform/run.sql` and write down the exact SQL Dataform generated for each. Then explain why a declaration produces no statement of its own.

4. **`ref()` form drill.** Write the same cross-schema reference four ways: `ref("name")`, `ref("schema", "name")`, `ref("database", "schema", "name")`, and `ref({ name, schema, database })`. Compile each and verify the compiled SQL resolves to the relation you expect. Then try `ref("name", { schema: "other" })` and record the error — explain why the object form is the one to reach for.

5. **Hermeticity experiment.** Set `hermetic: true` on an action, then add an undocumented table reference. Compile and record the error. Then find a real dependency edge you had forgotten and add it as a declaration plus a `ref()`. Explain why `dependencies` is the right tool for an ordering dependency but not for a data dependency.

---

## 📖 Further Reading

- Dataform core reference — https://cloud.google.com/dataform/docs/reference/dataform-core-reference
- Declare data sources — https://cloud.google.com/dataform/docs/declare-source
- Declare dependencies — https://cloud.google.com/dataform/docs/dependencies
- Add custom SQL operations — https://cloud.google.com/dataform/docs/custom-sql
- JavaScript in Dataform — https://cloud.google.com/dataform/docs/javascript-in-dataform
- Dataform assertions — https://cloud.google.com/dataform/docs/assertions
- Configure additional actions — https://cloud.google.com/dataform/docs/configure-additional-actions
- Dataform overview — https://cloud.google.com/dataform/docs/overview
- SQL workflows in Dataform — https://cloud.google.com/dataform/docs/sql-workflows
