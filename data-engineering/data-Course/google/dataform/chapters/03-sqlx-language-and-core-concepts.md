# 1.3 — The SQLX Language & Core Concepts

> **Section 1 · Foundations · Lecture 1.3 · 16:05**

## 🎯 What you will learn

- What SQLX actually is: SQL + JSX-style expressions + a config block
- The three-part file structure — `config` block, then SQL, then optional `post` block
- Every field in the `config` block, and what each one changes about the compiled output
- `ref()` and `source()` in depth — how names resolve and how the DAG is built
- The helper functions: `resolve()`, `is_incremental()`, `when()`, `self()`, `publish()`, `operate()`
- Unit tests (`unitTest` blocks) and the `expect` operators
- How SQLX compares to plain SQL and to dbt's Jinja

---

## 🧠 Concept

### What SQLX is

SQLX is a **superset of SQL**. It is SQL, plus three additions:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  1. A CONFIG BLOCK      config { type: "table", ... }                   │
│     → declarative metadata: materialization, partitioning, tests        │
├──────────────────────────────────────────────────────────────────────────┤
│  2. SQLX EXPRESSIONS   ${ref("stg_orders")}                            │
│     → JSX-style interpolation of compiler-resolved values               │
├──────────────────────────────────────────────────────────────────────────┤
│  3. A POST BLOCK        post { operations { ... } }                     │
│     → optional post-execution operations (delete, update, assert, grant)│
└──────────────────────────────────────────────────────────────────────────┘
```

Everything in a `.sqlx` file is one of those three things: the SQL is ordinary SQL BigQuery
executes, the config block is metadata the compiler reads, and the expressions are placeholders
the compiler substitutes.

### The file structure

The order is fixed and the compiler enforces it:

```
definitions/stg/stg_orders.sqlx

┌─────────────────────────────────────────────────────────────┐
│ ① config { ... }        ← FIRST. Declarative metadata.      │
├─────────────────────────────────────────────────────────────┤
│ ② SELECT ...            ← the SQL body                     │
├─────────────────────────────────────────────────────────────┤
│ ③ post { ... }          ← OPTIONAL. Post-execution ops.     │
└─────────────────────────────────────────────────────────────┘
```

```sqlx
config {
  type: "table",
  description: "Staged orders"
}

SELECT *
FROM ${source("raw_orders", "orders")}

post {
  operations {
    grant {
      roles: ["roles/bigquery.dataViewer"],
      grantees: ["group:analytics@company.com"]
    }
  }
}
```

⚠️ **The `config` block must come first.** Putting SQL before `config` is a compile error. And
there can be only one `config` block per file.

### The `config` block — full reference

| Field | Type | Purpose |
|-------|------|---------|
| `type` | string | **Required.** `table`, `view`, `incremental`, or `ephemeral`. |
| `schema` | string | Override the target dataset for this model only. |
| `database` | string | Override the target project for this model only. |
| `description` | string | Human description, surfaced in the catalog and lineage UI. |
| `uniqueKey` | string \| string[] | Column(s) that uniquely identify a row. Used by incremental merge. |
| `partitionBy` | string \| object | Partition column(s) and expiration. |
| `clusterBy` | string \| string[] | Clustering column(s). |
| `labels` | object | BigQuery table labels (key → value). |
| `tags` | string \| string[] | Dataform tags for workflow/action selection. |
| `disabled` | boolean | Compile the model but do not execute it. |
| `protected` | boolean | Block destructive operations (DROP, overwrite). |
| `dependencies` | string[] | Extra DAG edges to models not referenced in SQL. |
| `hermetic` | boolean | When true, the model may only read data it declares via `ref()`/`source()`. |
| `assertions` | object | Automatic assertions generated for this model. |
| `include` / `exclude` | string[] | Files to include or exclude from the model's compilation. |
| `bigquery` | object | BigQuery-specific options (see below). |

`schema` and `database` are the per-model overrides — they take precedence over
`defaultDataset` and `defaultProject` in `dataform.json`. Chapter 1.4 covers the resolution
rules in full.

#### `type` — the four materializations

There are exactly **four** types, and choosing the wrong one is the most common early mistake.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ type: "view"         → CREATE OR REPLACE VIEW. No data stored.         │
│   Use for: thin transformations, dimension lookups, dashboards.         │
├──────────────────────────────────────────────────────────────────────────┤
│ type: "table"        → CREATE OR REPLACE TABLE. Full rebuild every run.│
│   Use for: staging layers, aggregates that must be exactly right.      │
├──────────────────────────────────────────────────────────────────────────┤
│ type: "incremental"  → MERGE into an existing table. Only changed rows  │
│   are written. Requires uniqueKey. Large, append-mostly fact tables.   │
├──────────────────────────────────────────────────────────────────────────┤
│ type: "ephemeral"    → NOT materialized. Inlined as a CTE into its     │
│   dependents. Reusable CTEs, light cleansing between two real models.  │
└──────────────────────────────────────────────────────────────────────────┘
```

⚠️ **`table` rebuilds the whole thing every run.** On a 2-billion-row table that is a full scan
and a full rewrite — every time. `incremental` exists to avoid exactly that. If you have a
`table` model that takes minutes and scans billions of bytes, it should probably be
`incremental`.

⚠️ **`ephemeral` models disappear from your catalog.** They become CTEs. You cannot query them
directly, and they do not appear as tables in BigQuery. They are still real nodes in the DAG.

#### `partitionBy` and `clusterBy`

```sqlx
config {
  type: "table",
  partitionBy: { field: "order_date", dataType: "date", expirationDays: 90 },
  clusterBy: ["customer_id", "status"]
}
```

`partitionBy` with `expirationDays` is a **cost control**: BigQuery drops partitions older than
the window. `clusterBy` improves filter pruning and join performance.

#### `hermetic`, `dependencies`, `protected`

```sqlx
config {
  type: "table",
  hermetic: true,          // may only read data declared via ref()/source()
  dependencies: ["stg_orders"],  // extra DAG edge to a model not referenced in SQL
  protected: true          // block destructive operations against the relation
}
```

`hermetic: true` makes the compiler fail if the model reads any table it did not declare via
`ref()` or `source()`. `dependencies` is for *ordering* dependencies, not data dependencies.
`protected` stops Dataform overwriting or dropping the relation without an explicit override.

💡 **Turn `hermetic: true` on for your marts layer.** It is the cheapest possible guard against
accidentally introducing a hidden dependency the DAG does not know about — this is how Dataform's
"no undeclared dependencies" guarantee is actually enforced.

#### `bigquery` specific options

```sqlx
config {
  type: "table",
  bigquery: {
    updatePartitionFilter: "TRUE",
    insertMode: "INSERT",
    partitionExpirationDays: 90,
    requirePartitionFilter: true,
    clustering: { fields: ["customer_id"] }
  }
}
```

`requirePartitionFilter: true` makes BigQuery **reject queries** that scan the table without a
partition filter — a cost guardrail at the database level, not just a convention.

#### `assertions` in config

```sqlx
config {
  type: "table",
  assertions: {
    rowCount: { min: 1 },
    nonNull: ["order_id", "customer_id"]
  }
}
```

Auto-generates assertions for every model with this config.

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

(`resolve()` returns a relation *name*, not a CTE — the compiled SQL contains a straight
`FROM \`my-project.analytics.stg_orders\``.)

```sqlx
config { type: "view" }

SELECT *
FROM ${ref("stg_orders")}
```

The `${...}` wrapper is JSX-style interpolation: the expression is evaluated at compile time and
the result is substituted into the SQL text as a literal.



### `source()` — declaring external tables

`source()` declares data that Dataform does **not** create: a table that already exists in
BigQuery, written by another system.

```
definitions/sources/raw_orders.sqlx

config {
  type: "declarative",
  database: "source-project",
  schema: "raw",
  description: "Raw orders landing table"
}

source("raw_orders", "orders")
```

The **file name** is the source name (`raw_orders`); the **argument** is the table name (`orders`).
Models then use `SELECT * FROM ${source("raw_orders", "orders")}`.

| Field | Meaning |
|-------|---------|
| `type` | Must be `"declarative"`. |
| `database` | Project the source table lives in. |
| `schema` | Dataset the source table lives in. |
| `description` | Human description. |
| `loaded_at_field` | Column holding the load timestamp. Used by freshness checks. |
| `freshness` | `{ errorAfter: "48h", warnAfter: "24h" }` — how stale is too stale. |

```sqlx
config {
  type: "declarative",
  database: "source-project",
  schema: "raw",
  loaded_at_field: "_loaded_at",
  freshness: {
    errorAfter: "48h",
    warnAfter: "24h"
  }
}

source("raw_orders", "orders")
```

💡 **`loaded_at_field` + `freshness` is how you get pipeline monitoring for free.** Dataform
checks the source's load timestamp and raises a warning or an error if the data has not arrived
on schedule. This catches "the upstream job silently stopped three days ago" — the failure mode
that is otherwise invisible until someone notices a stale dashboard.

### `resolve()` and `is_incremental()`

`resolve("name")` looks up `vars` in `dataform.json` at compile time. Nested access works too:
`resolve("featureFlags.enableNewPricing")`.

```sqlx
config { type: "view" }

SELECT *
FROM ${source("raw_orders", "orders")}
WHERE order_date >= '${resolve("startDate")}'
  AND region IN (${resolve("regions")})
```

`is_incremental()` returns `true` **only** on an incremental run of an `incremental` model. On
the first run (or a full refresh), it is `false`.

### `incremental()` and the `when()` idiom

`incremental()` is a helper that produces the WHERE clause for an incremental model. The
standard Dataform pattern builds the clause with `when()`:

```sqlx
config {
  type: "incremental",
  uniqueKey: "order_id"
}

SELECT
    order_id,
    customer_id,
    order_date,
    total_amount
FROM ${source("raw_orders", "orders")}
WHERE ${when(incremental(), "order_date > @last_run", "TRUE")}
```

This reads as: *on an incremental run, filter to rows after the last run; on a full rebuild,
take everything.* The `when()` function takes a condition and returns the true or false branch.

`when(condition, trueValue, falseValue)` — the two-argument form returns `trueValue` when the
condition holds and `""` otherwise; the three-argument form returns the false branch.

### `self()` — referencing your own table

`self()` returns the model's own fully-qualified relation name. You need it to read the
previous state of the table you are writing:

```sqlx
config {
  type: "incremental",
  uniqueKey: "order_id"
}

SELECT
    o.order_id,
    o.customer_id,
    o.total_amount,
    COALESCE(c.segment, 'unknown') AS segment
FROM ${source("raw_orders", "orders")} o
LEFT JOIN ${self()} c
    ON o.order_id = c.order_id
```

💡 **`self()` in a join is how you enrich with your own historical state** — cumulative
measures, slowly-changing dimensions, last-known values.

### `publish()` — operational metadata

`publish()` attaches metadata to the relation Dataform creates. It does not change the SQL.

```sqlx
config {
  type: "table",
  description: "Order fact table"
}

SELECT * FROM ${ref("stg_orders")}

post {
  publish({
    schema: "analytics",
    database: "my-project",
    description: "Order fact table, one row per order",
    columns: {
      order_id: { description: "Surrogate key of the order" },
      customer_id: { description: "Surrogate key of the customer" }
    },
    rowCount: 1234567,
    updatedAt: "2025-01-15T10:30:00Z"
  })
}
```

💡 **`publish()` does not change the SQL.** It is how a model tells the catalog what it contains,
which is what makes the lineage graph readable six months later. `publishWithSelector()` is the
variant that publishes metadata for a **subset** of rows — used with `operate()` operations to
publish metadata about a specific partition or slice.

### `operate()` — declarative operations

`operate()` declares things to do to the relation *after* it is built.

```sqlx
config {
  type: "table"
}

SELECT * FROM ${ref("stg_orders")}

post {
  operations {
    delete  { where: "order_date < DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)" }
    update  { where: "status = 'pending'", columns: { status: "'cancelled'" } }
    assert  { where: "order_id IS NULL", error: "Found null order_id" }
    grant   { roles: ["roles/bigquery.dataViewer"],
              grantees: ["group:analytics@company.com"] }
    revoke  { roles: ["roles/bigquery.dataOwner"],
              grantees: ["user:contractor@vendor.com"] }
  }
}
```

| Action | What it does |
|--------|--------------|
| `delete` | DELETE matching rows. |
| `update` | UPDATE matching rows, setting columns. |
| `assert` | Fail the run if any row matches. |
| `grant` | GRANT a role to a grantee. |
| `revoke` | REVOKE a role from a grantee. |

💡 **`delete` is the idiomatic way to implement retention.** Partition expiration is cheaper, but
`operate({action: "delete"})` works on any table and can be conditional.

### `unitTest` blocks — the test framework

Dataform has first-class unit tests. A `unitTest` block defines test cases for a model.

```sqlx
config {
  type: "table"
}

SELECT * FROM ${source("raw_orders", "orders")}

unitTest("stg_orders", {
  "a valid order passes": {
    ref: { stg_orders: { order_id: 1, customer_id: 10, total_amount: 25.0 } },
    rows: [
      { order_id: 1, customer_id: 10, total_amount: 25.0 }
    ],
    columns: {
      order_id: { not_null: true },
      total_amount: { not_null: true, equals: 25.0 }
    }
  }
})
```

Anatomy:

- **Test name** — the first string argument. It must be unique within the file.
- **`ref`** — the mocked inputs. `ref: { stg_orders: { ... } }` supplies rows for the `stg_orders`
  relation, so the test runs against **fake data**, not real BigQuery.
- **`rows`** — the expected output rows.
- **`columns`** — per-column expectations using `expect` operators.

| Operator | Asserts |
|----------|---------|
| `equals` / `not_equals` | The value equals (or does not equal) the expected value. |
| `not_null` | The value is not null. |
| `in_set` / `not_in_set` | The value is (or is not) one of a set of values. |
| `between` | The value falls in a range (inclusive). |
| `matches` | The value matches a regex pattern. |
| `contains` | The value contains a substring. |
| `length_equals` | The array/string length equals a number. |
| `row_count` | The number of rows equals a number. |
| `aggregate_equals` | An aggregate over the rows equals a value. |

```sqlx
unitTest("stg_orders", {
  "rejects negative amounts": {
    ref: { stg_orders: { order_id: 2, total_amount: -5.0 } },
    rows: [{ order_id: 2, total_amount: -5.0 }],
    columns: {
      total_amount: { not_in_set: [-5.0] },
      order_id: { not_null: true, in_set: [1, 2, 3] }
    }
  },
  "produces exactly one row": {
    ref: { stg_orders: { order_id: 3 } },
    rows: [{ order_id: 3 }],
    columns: { order_id: { row_count: 1 } }
  }
})
```

⚠️ **`unitTest` runs against mocked `ref` data, not real tables.** That is what makes it fast —
the test does not query BigQuery at all (against the emulator, or in Dataform Cloud's test
environment). The trade-off: you must mock *every* upstream input your model reads, or the test
fails with a missing-input error.

### `assert` blocks — standalone assertions

A `unitTest` validates a model in isolation. An `assert` validates a **data quality rule** about
a relation, and can be declared on its own or attached to a model via `config { assertions: ... }`.

```sqlx
assert {
  name: "fct_orders_has_no_orphans",
  description: "Every order must reference a known customer",
  rows: [{ order_id: "1", customer_id: "999" }],
  columns: { order_id: { not_null: true } }
}
```

💡 **Assertions are how you turn a silent data-quality problem into a failed build.** A model
that produces null keys or loses 90% of its rows should fail loudly, not quietly write bad data
into a dashboard.


### `include` / `exclude`, and reading project config

Inside a `config` block, `include` and `exclude` control which files contribute to the model:

```sqlx
config {
  type: "table",
  include: ["definitions/stg/*.sqlx"],
  exclude: ["definitions/stg/stg_orders.sqlx"]
}
```

And you can read project-level and model-level config from SQLX:

```sqlx
config { type: "view" }

SELECT *
FROM ${source("raw_orders", "orders")}
WHERE dataset = '${dataform.projectConfig.defaultDataset}'
  AND ${dataform.projectConfig.vars.filterFlag} = true
```

- `dataform.projectConfig.vars.foo` — access a var
- `dataform.projectConfig.defaultDataset` — the project config values
- `dataform.config.someConfig` — access a value from the model's own `config` block

### SQLX vs plain SQL vs dbt Jinja

| Dimension | SQLX | Plain `.sql` | dbt (Jinja) |
|-----------|------|--------------|--------------|
| Templating style | JSX-style `${expression}` | None | Jinja `{{ expression }}` / `{% statement %}` |
| Materialization | Built into `config` | You write the DDL yourself | Macros (`materialization` blocks) |
| Dependency declaration | `ref()` / `source()` | None — external orchestration | `ref()` / `source()` |
| Test framework | `unitTest` blocks + `assert` | You write and run them | `schema.yml` or `dbt tests` |
| Config | `dataform.json` + per-file `config` block | N/A | `dbt_project.yml` + model `config` |
| Incremental | `is_incremental()` + `incremental()` | Manual `MERGE` | `is_incremental()` macro |
| Errors on bad ref | Compile-time, always | Runtime | Compile-time, usually |
| Verbosity | Moderate | None | High — Jinja blocks are dense |
| Portability | Dataform only | Universal | dbt only |

⚠️ **Plain SQL has no dependency awareness at all.** You can write `FROM orders` and the system
has no idea `orders` is produced by another script. That is exactly the failure mode from
Chapter 1.1 — a folder of scripts with encoded-by-filename ordering.

💡 **SQLX is roughly halfway between plain SQL and dbt Jinja in terms of ceremony.** The `config`
block is a formal declaration; the `${}` interpolation is familiar to anyone who has written
React; and there is no separate YAML file for tests — tests live next to the code they test.

---

## 🛠️ Hands-On: One File Per Model Type

Create these files under `definitions/`, then run `dataform compile` after each.

### Step 1 — A `view` model

`definitions/marts/dim_customers.sqlx`:

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

### Step 2 — A `table` model

`definitions/stg/stg_orders.sqlx`:

```sqlx
config {
  type: "table",
  description: "Staged orders, deduplicated",
  partitionBy: { field: "order_date", dataType: "date" },
  clusterBy: ["customer_id"]
}

SELECT order_id, customer_id, order_date, total_amount
FROM ${source("raw_orders", "orders")}
QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY _loaded_at DESC) = 1
```

### Step 3 — An `incremental` model

`definitions/marts/fct_orders.sqlx`:

```sqlx
config {
  type: "incremental",
  description: "Order fact table, incrementally maintained",
  uniqueKey: "order_id",
  partitionBy: { field: "order_date", dataType: "date" },
  clusterBy: ["customer_id"],
  protected: true
}

SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    o.total_amount,
    COALESCE(c.segment, 'unknown') AS segment
FROM ${source("raw_orders", "orders")} o
LEFT JOIN ${self()} c
    ON o.order_id = c.order_id
WHERE ${when(incremental(), "o.order_date > @last_run", "TRUE")}
```

### Step 4 — An `ephemeral` model

`definitions/int/int_order_items_enriched.sqlx`:

```sqlx
config {
  type: "ephemeral",
  description: "Order items joined to order context; inlined as a CTE"
}

SELECT
    i.order_id,
    i.product_id,
    i.quantity * i.unit_price AS line_total,
    o.order_date,
    o.customer_id
FROM ${ref("stg_order_items")} i
JOIN ${ref("stg_orders")} o
    ON i.order_id = o.order_id
```

⚠️ **An `ephemeral` model cannot be referenced by anything except a `view`, `table`, or
`incremental` model that will actually materialize it.** If two materialized models reference the
same ephemeral model, it is inlined into both — which defeats the purpose and doubles the cost.

### Step 5 — A model with post-operations

`definitions/marts/fct_order_items.sqlx`:

```sqlx
config {
  type: "table",
  description: "Order line items"
}

SELECT order_id, product_id, quantity, unit_price
FROM ${ref("int_order_items_enriched")}

post {
  operations {
    delete { where: "order_id IN (SELECT order_id FROM ${source("raw_orders", "cancelled_orders")})" }
    grant  { roles: ["roles/bigquery.dataViewer"],
             grantees: ["group:analytics@company.com"] }
  }
  publish({
    description: "Order line items, published to the analytics dataset",
    rowCount: 4819203,
    updatedAt: "2025-01-15T10:30:00Z"
  })
}
```

### Step 6 — A unit test

`definitions/stg/stg_orders.sqlx` — append the test:

```sqlx
unitTest("stg_orders", {
  "keeps only the latest version of each order": {
    ref: {
      stg_orders: {
        order_id: 1,
        customer_id: 10,
        total_amount: 25.0,
        _loaded_at: "2025-01-01"
      }
    },
    rows: [{ order_id: 1, customer_id: 10, total_amount: 25.0 }],
    columns: {
      order_id: { not_null: true },
      total_amount: { equals: 25.0 }
    }
  }
})
```

### Step 7 — Compile and run the tests

```bash
# Compile — catches config errors, missing refs, bad types
dataform compile

# Run the unit tests
dataform test

# Compile just one model and its dependencies
dataform compile --nodes fct_orders

# Inspect the compiled SQL for the incremental model — note the MERGE
grep -A 20 "fct_orders" .dataform/run.sql | head -40
```

### Step 8 — Exercise `resolve()` and `when()`

Add a var to `dataform.json` — `{ "vars": { "region": "us-east1", "minAmount": 10.0 } }` —
then use it:

```sqlx
config { type: "view" }

SELECT *
FROM ${ref("stg_orders")}
WHERE region = '${resolve("region")}'
  AND total_amount >= ${resolve("minAmount")}
```

```bash
dataform compile --vars '{"region": "eu-west1"}'
grep "eu-west1" .dataform/run.sql    # confirms the override reached the SQL
```

---

## 🔑 Key Takeaways

- SQLX = SQL + `${}` expressions + a `config` block (+ optional `post` block). The `config` block must come first.
- There are exactly four types: `table`, `view`, `incremental`, `ephemeral`. `table` rebuilds fully; `incremental` merges; `ephemeral` becomes a CTE and never materializes.
- `ref()` is four things at once: name resolution, a DAG edge, schema awareness, and an invalidation trigger. It resolves to a fully-qualified relation.
- `source()` declares external tables. The **file name** is the source name; the **argument** is the table name. Source `config` needs `type: "declarative"`.
- `resolve()` reads compile-time `vars`. `when()` picks between branches. `is_incremental()` is true only on incremental runs.
- The standard incremental idiom is `WHERE ${when(incremental(), "order_date > @last_run", "TRUE")}` — a filter on incremental runs, everything on a full rebuild.
- `self()` returns your own model's relation — use it to join against the previous state of the table.
- `operate()` declares `delete`, `update`, `assert`, `grant`, `revoke` as post-execution operations.
- `publish()` attaches operational metadata to the relation; it does not change the SQL.
- `unitTest` blocks validate models against **mocked** `ref` inputs. The `expect` operators are: `equals`, `not_equals`, `not_null`, `in_set`, `not_in_set`, `between`, `matches`, `contains`, `length_equals`, `row_count`, `aggregate_equals`.
- `hermetic: true` is the cheapest guard against undeclared dependencies — turn it on for your marts layer.
- `loaded_at_field` + `freshness` on sources gives you upstream-staleness monitoring for free.

---

## 📚 Practice Exercises

1. **Type selection audit.** You have five models: a customer dimension joined into 40 dashboards, a 3-billion-row click stream, a small currency lookup, a reusable cleansed-orders CTE used by two marts, and a daily aggregate. Assign a `type` to each and justify it. Then find the one that would be most expensive if you got it wrong, and estimate the cost difference.

2. **Config block archaeology.** Take a plain SQL file that creates a partitioned, clustered table with a `CREATE OR REPLACE` and a `DELETE` afterwards. Rewrite it as SQLX. Identify every piece of SQL you moved into `config` and every piece you moved into `post { operations { ... } }`. Explain what the compiler now knows that it did not before.

3. **Build a model type zoo.** Create one model of each of the four types. Compile, then inspect `.dataform/run.sql` and write down the exact DDL Dataform generated for each — `CREATE OR REPLACE VIEW`, `CREATE OR REPLACE TABLE`, `MERGE`, and the CTE inlining. Then explain why `ephemeral` produces no statement of its own.

4. **Unit test gauntlet.** Write a `unitTest` for `stg_orders` with at least six cases, using `equals`, `not_null`, `in_set`, `not_in_set`, `between`, `matches`, `contains`, and `row_count`. Then deliberately break the model (change a filter, change a column name) and confirm each test fails for the right reason.

5. **Hermeticity experiment.** Take a model and set `hermetic: true`. Add an undocumented table reference to a table that is not declared via `ref()` or `source()`. Compile and record the error. Then find a real dependency edge you had forgotten and add it to `config { dependencies: [...] }` instead. Explain why `dependencies` is the right fix for an ordering dependency but not for a data dependency.

---

## 📖 Further Reading

- Dataform SQLX reference — https://cloud.google.com/dataform/docs/reference/sqlx
- Dataform configuration reference — https://cloud.google.com/dataform/docs/reference/config
- Dataform `ref()` and `source()` — https://cloud.google.com/dataform/docs/reference/sqlx-ref-and-source
- Dataform unit tests — https://cloud.google.com/dataform/docs/tests/unit-tests
- Dataform assertions — https://cloud.google.com/dataform/docs/tests/assertions
- Dataform operations — https://cloud.google.com/dataform/docs/reference/operations
- Dataform vs dbt — https://cloud.google.com/dataform/docs/comparison/dataform-and-dbt
