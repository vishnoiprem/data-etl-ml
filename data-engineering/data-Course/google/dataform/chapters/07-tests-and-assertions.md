# 2.3 — Tests, Assertions & Data Quality

> **Section 2 · Modeling · Lecture 2.3 · 20:35**

## 🎯 What you will learn

- The two quality mechanisms in Dataform: **assertions** (guard the build) and **tests** (guard the logic)
- The real built-in assertion types — `uniqueKey`, `uniqueKeys`, `nonNull`, `rowConditions` — and exactly what each compiles to
- Why there is **no** built-in `relationships` or `rowCount` assertion, and how to write those yourself
- The `assert()` action as the mechanism for custom, relationship-style checks
- How to write tests with `input` / `expect`, and how `dataform test` runs them
- The `dataform_assertions` dataset — where failures are recorded in BigQuery
- A worked quality-gate model set covering five distinct checks

---

## 🧠 Concept

### Two mechanisms, two jobs

Dataform gives you two ways to check quality, and they run at different times against different
things.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ASSERTIONS                          Separate queries, run as a          │
│                                      dependency of the model.            │
│                                      Run against the BUILT table.       │
│                                                                         │
│  SELECT * FROM fct_orders WHERE amount < 0;                            │
│  → if it returns ANY rows, the assertion FAILS                         │
│                                                                         │
│  → "Does the table I just built contain bad rows?"                     │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  TESTS                              Separate queries, run independently.  │
│                                      Compare a model's output to a      │
│                                      known expected result.             │
│                                                                         │
│  config { type: "test" }                                               │
│  input "foo" { SELECT 1 AS bar }                                       │
│  SELECT 1 AS bar                                                       │
│                                                                         │
│  → "Does my transformation logic do what I think it does?"             │
└─────────────────────────────────────────────────────────────────────────┘
```

**The governing philosophy:**

| | Assertions | Tests |
|---|---|---|
| **Guard** | The **build** | The **logic** |
| **When** | After the model is built, as a dependency of it | Separately, on demand or in CI |
| **What they check** | The actual output table | The transformation against known inputs |
| **On failure** | The model is marked failed; downstream models don't run | The test fails |
| **Who runs them** | The scheduler / `dataform run` | The developer / `dataform test` |
| **Cost** | A separate query against the built table | A separate query against fixtures |

💡 **Assertions guard the build; tests guard the logic.** A pipeline can have perfect assertions
and still contain wrong logic — the assertions would happily pass a table of `amount * 2` when it
should be `amount * 3`. Tests catch that before the model ever touches production data.

### The `assertions` config block

The built-in assertions are configured inside the model's `config` block:

```sqlx
config {
  type: "incremental",
  uniqueKey: ["id"],
  assertions: {
    uniqueKey: ["id"],
    nonNull: ["id", "event_date"],
    rowConditions: ["amount >= 0", "status IN ('new', 'paid', 'shipped')"]
  }
}
```

Dataform turns each of these into a separate **assertion action** that depends on the model:

```
  fct_orders (table)
      │
      ├──▶ fct_orders_assertions_uniqueKey      (runs after fct_orders)
      ├──▶ fct_orders_assertions_rowConditions  (runs after fct_orders)
      └──▶ (nonNull is folded into rowConditions)
```

### The four real built-in assertions

⚠️ **These are the only built-in assertion types in Dataform: `uniqueKey`, `uniqueKeys`,
`nonNull`, and `rowConditions`.** There is **no** built-in `relationships` assertion and **no**
built-in `rowCount` assertion. If you write either name in the `assertions` config, the compiler
rejects it. Relationship checks and row-count checks must be written by hand.

| Assertion | Config value | What it checks | Failure meaning |
|---|---|---|---|
| `uniqueKey` | `["col_a"]` or `"col_a"` | The column(s) are unique | Duplicate keys — breaks `MERGE`, double-counts downstream |
| `uniqueKeys` | `[["a", "b"], ["c"]]` | Each listed *combination* is unique | Duplicate composite keys |
| `nonNull` | `["col_a", "col_b"]` | The listed columns contain no NULLs | Missing keys, null dimensions, incomplete joins |
| `rowConditions` | `["pred1", "pred2"]` | Every row satisfies each predicate | Business-rule violations |

#### `uniqueKey` and `uniqueKeys`

```sqlx
config {
  type: "incremental",
  uniqueKey: ["id"],
  assertions: {
    uniqueKey: ["id"]
  }
}
```

`uniqueKey` checks that the listed column(s) are unique — the same property the `MERGE` depends on.
Note this is separate from the `uniqueKey` *config* key: the config key tells Dataform **how to
build** the model; the assertion tells Dataform **to verify** the property.

The compiled SQL:

```sql
SELECT
  *
FROM (
  SELECT
    id,
    COUNT(1) AS index_row_count
  FROM `my-project.analytics.fct_orders`
  GROUP BY id
  ) AS data
WHERE index_row_count > 1
```

If that query returns any rows, there are duplicates.

`uniqueKeys` handles **multiple** composite keys at once:

```sqlx
config {
  assertions: {
    uniqueKeys: [["val1", "val2"], ["val2"]]
  }
}
```

That asserts two things: the combination `(val1, val2)` is unique, **and** `val2` on its own is
unique. (The two cannot be set together — `uniqueKey` and `uniqueKeys` are mutually exclusive.)

💡 **`uniqueKeys` is the right choice for a table with more than one natural key.** A dimension
might be unique on `customer_id` *and* on `email`; `uniqueKeys` checks both in one assertion.

#### `nonNull`

```sqlx
config {
  assertions: {
    nonNull: ["id", "event_date", "customer_id"]
  }
}
```

⚠️ **`nonNull` is not a separate assertion — it is rewritten into a `rowConditions` assertion.**
Dataform converts each column into the predicate `<column> IS NOT NULL` and merges it with any
`rowConditions` you supplied. The compiled SQL looks like:

```sql
SELECT
  'id IS NOT NULL' AS failing_row_condition,
  *
FROM `my-project.analytics.fct_orders`
WHERE NOT (id IS NOT NULL)
```

💡 **Always assert `nonNull` on your `uniqueKey` columns and your partition column.** A NULL in a
`uniqueKey` column makes the `MERGE` behave unpredictably; a NULL in the partition column sends
that row to the `__NULL__` partition, where it will never be pruned.

#### `rowConditions`

`rowConditions` is the general-purpose built-in — a list of SQL predicates that **every row** must
satisfy.

```sqlx
config {
  assertions: {
    rowConditions: [
      "amount >= 0",
      "status IN ('new', 'paid', 'shipped')",
      "order_date <= CURRENT_DATE()"
    ]
  }
}
```

Each predicate becomes its own `SELECT` branch, unioned together:

```sql
SELECT 'amount >= 0' AS failing_row_condition, *
FROM `my-project.analytics.fct_orders`
WHERE NOT (amount >= 0)
UNION ALL
SELECT 'status IN (''new'', ''paid'', ''shipped'')' AS failing_row_condition, *
FROM `my-project.analytics.fct_orders`
WHERE NOT (status IN ('new', 'paid', 'shipped'))
```

💡 **`rowConditions` is how you express business rules.** It covers validity checks that
`nonNull` can't: non-negative amounts, a closed set of status values, dates that aren't in the
future.

⚠️ **`rowConditions` predicates are per-row, not aggregate.** You cannot write `COUNT(*) > 0`
here — a per-row predicate like that is true for zero rows and therefore always passes. Aggregate
checks need a different mechanism.

### What there is **no** built-in `rowCount` assertion

⚠️ **There is no built-in `rowCount` assertion.** If you need "the table is not empty" or "the
row count grew", you write it yourself.

**"The table is not empty"** — write it as a `rowConditions`? No: an empty table trivially
satisfies every per-row predicate, so `rowConditions` cannot express it. Use a **custom assertion
action** instead:

```sqlx
// definitions/assertions/fct_orders_not_empty.sqlx
config {
  type: "assertion",
  dependencies: ["fct_orders"]
}

SELECT *
FROM `my-project.analytics.fct_orders`
LIMIT 1
```

An assertion query that **returns rows** fails. `LIMIT 1` on an empty table returns nothing, so
the assertion passes; on a non-empty table it returns a row, so the assertion fails.

**"The row count grew since the last run"** — a custom assertion with a subquery:

```sqlx
// definitions/assertions/fct_orders_row_count.sqlx
config {
  type: "assertion",
  dependencies: ["fct_orders"]
}

SELECT *
FROM (
  SELECT COUNT(*) AS n FROM `my-project.analytics.fct_orders`
) AS counts
WHERE n = 0
```

💡 **This is the standard workaround people reach for when they expect a `rowCount` assertion.**
Note the important difference in shape: the built-in `rowConditions` assertion tests *rows*;
your custom assertion tests a *scalar query result*.

### There is no built-in `relationships` assertion

⚠️ **Dataform has no built-in `relationships` assertion.** (dbt does — one of the most common
sources of confusion when moving between the two tools.) Relationship and foreign-key checks must
be written explicitly, either as a `rowConditions` assertion or as a custom assertion action.

**As a `rowConditions` assertion** — express the orphan check as a per-row predicate:

```sqlx
config {
  type: "table",
  assertions: {
    rowConditions: [
      "customer_id IN (SELECT customer_id FROM ${ref('dim_customers')})"
    ]
  }
}
```

⚠️ **This works, but it is expensive.** The subquery is re-evaluated for every row of the model,
and it references `dim_customers` inside a per-row predicate — a correlated subquery over the
whole table. On a large fact table this is a serious scan.

**As a custom assertion action** — the recommended form, because the query runs once:

```sqlx
// definitions/assertions/fct_orders_relationship_customers.sqlx
config {
  type: "assertion",
  dependencies: ["fct_orders", "dim_customers"]
}

SELECT o.order_id, o.customer_id
FROM `my-project.analytics.fct_orders` AS o
LEFT JOIN `my-project.analytics.dim_customers` AS c
  ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
```

That query returns the orphan rows. If it returns any, the assertion fails — and the failing rows
tell you *exactly* which orders are broken, which is far more useful than a count.

💡 **Prefer the custom assertion action for relationship checks.** It runs as one join, it
returns the offending rows for inspection, and it doesn't scale with the size of the fact table
the way a correlated per-row predicate does.

### `assert()` — the assertion action

The `assertion` action type is the general mechanism behind every custom check:

```sqlx
// definitions/assertions/custom_check.sqlx
config {
  type: "assertion",
  dependencies: ["fct_orders"]
}

SELECT *
FROM `my-project.analytics.fct_orders`
WHERE amount < 0
```

| Config field | Purpose |
|---|---|
| `type: "assertion"` | Marks this file as an assertion, not a table |
| `dependencies` | The model(s) this assertion checks — creates the DAG edge |
| `disabled` | Set to `true` to turn the assertion off without deleting it |

**The rule that makes assertions work: an assertion query that returns rows FAILS.** This is
inverted from most people's first instinct, so write it down:

```
  SELECT * FROM t WHERE bad        →  returns rows  →  assertion FAILS
  SELECT * FROM t WHERE good       →  returns rows  →  assertion FAILS  ← counterintuitive!
  SELECT 1 FROM t WHERE bad LIMIT 1 →  returns 0 rows →  assertion PASSES
```

💡 **The `LIMIT 1` trick makes every check fast.** An assertion doesn't need all the bad rows to
fail the build — it needs one. `LIMIT 1` lets BigQuery stop after the first violation, which can
turn an expensive scan into a cheap one.

⚠️ **To assert something must NOT exist, query for the rows that shouldn't be there.** The
assertion fails when it finds them. Invert your thinking from "the check must pass" to "the query
must return nothing."

### The `dataform_assertions` dataset

When an assertion fails, Dataform records the failing rows in a dedicated BigQuery dataset. By
default that dataset is named **`dataform_assertions`**, and it can be overridden with
`defaultAssertionDataset` in `workflow_settings.yaml` (or `--assertion-schema` on the CLI).

```sqlx
// workflow_settings.yaml
defaultAssertionDataset: analytics_assertions
```

```bash
# Inspect what failed
bq query --use_legacy_sql=false \
  'SELECT * FROM `my-project.dataform_assertions.fct_orders_assertions_uniqueKey` LIMIT 10'
```

💡 **This is the single most useful thing about Dataform's assertions.** A failed assertion doesn't
just say "something is wrong" — it hands you the exact rows that are wrong, queryable in BigQuery.
That turns a vague failure into a five-minute fix.

### Writing tests

Tests verify that a model produces a known result from known inputs.

```sqlx
// definitions/tests/fct_orders.sqlx
config {
  type: "test"
}

input "stg_orders" {
  SELECT
    1 AS order_id, 10 AS customer_id, 100.0 AS order_amount, 'complete' AS order_status
  UNION ALL
  SELECT
    2 AS order_id, 20 AS customer_id, 50.0 AS order_amount, 'cancelled' AS order_status
}

SELECT
  order_id,
  customer_id,
  order_amount
FROM ${ref("stg_orders")}
WHERE order_status = 'complete'
```

**The block structure:**

| Block | Purpose |
|---|---|
| `config { type: "test" }` | Marks the file as a test rather than a table |
| `input "name" { ... }` | A fixture — a named query whose result is materialized and substituted for `ref("name")` |
| The body query | The model's logic under test, referencing the fixtures via `ref()` |

```
  input "stg_orders" { ... }
       └── the INPUT fixture, materialized as a temporary table

  ${ref("stg_orders")}
       └── inside the test, resolves to the FIXTURE, not to the real table

  The body query
       └── the model's logic, run against the fixtures
```

💡 **The `input` blocks are what make a test hermetic.** Your real `stg_orders` table is never
read. You can test a model whose source doesn't exist yet, whose source is enormous, or whose
source is currently broken.

**The comparison.** The test compares the model's output to the `expect` query:

```sqlx
// definitions/tests/fct_orders.sqlx
config {
  type: "test"
}

input "stg_orders" {
  SELECT 1 AS order_id, 10 AS customer_id, 100.0 AS order_amount, 'complete' AS order_status
  UNION ALL
  SELECT 2 AS order_id, 20 AS customer_id, 50.0 AS order_amount, 'cancelled' AS order_status
}

SELECT order_id, customer_id, order_amount
FROM ${ref("stg_orders")}
WHERE order_status = 'complete'
```

The expected result is defined by the `expect` query in the JavaScript API:

```js
// definitions/tests/fct_orders.js
test("fct_orders")
  .input("stg_orders", `SELECT 1 AS order_id, 10 AS customer_id, 100.0 AS order_amount, 'complete' AS order_status
                        UNION ALL
                        SELECT 2 AS order_id, 20 AS customer_id, 50.0 AS order_amount, 'cancelled' AS order_status`)
  .expect(`SELECT 1 AS order_id, 10 AS customer_id, 100.0 AS order_amount`);
```

The `.expect()` query is the ground truth. Dataform runs both queries and compares the results.

### Running tests

```bash
# Compile everything — free, and catches broken references
dataform compile

# Run all tests
dataform test

# Run tests for specific nodes
dataform test --nodes fct_orders

# Run against the local BigQuery emulator (free, no GCP project needed)
dataform core
```

| Command | What it does |
|---|---|
| `dataform compile` | Compiles models and tests; produces `run.sql` and the DAG. Free |
| `dataform test` | Executes the tests against BigQuery (or the emulator) |
| `dataform test --nodes <name>` | Runs only the named nodes |
| `dataform core` | Starts the local Dataform core with the BigQuery emulator |

💡 **The emulator is the right place to iterate.** You can break and fix a model dozens of times
at zero cost. Run against real BigQuery only in CI, before merge.

⚠️ **Each test is a real BigQuery query.** Tests aren't free — a test with a `CROSS JOIN` over a
million rows costs real money. Keep fixtures tiny.

### The cost of quality checks

| Mechanism | BigQuery cost | Notes |
|---|---|---|
| **Built-in assertions** | One query per assertion, against the built table | Usually cheap relative to the build; `rowConditions` with correlated subqueries can be expensive |
| **Custom assertions** | One query per assertion | Usually one scan — but they run for *every* build |
| **Tests** | One query per test, against fixtures | Fixture size is the only thing that matters |

💡 **Assertions run on every pipeline build, so their cost is recurring.** A `rowConditions`
assertion with a correlated subquery over a 10 GB fact table, evaluated on every daily run, is a
real line item. Prefer the custom assertion action — it joins once instead of per-row.

### Test types and what each catches

| Check | Mechanism | Catches | Misses |
|---|---|---|---|
| `uniqueKey` | Built-in assertion | Duplicate keys that break `MERGE` and double-count | Cross-column uniqueness |
| `uniqueKeys` | Built-in assertion | Multiple composite keys not unique | — |
| `nonNull` | Built-in assertion | Missing keys, incomplete joins, null dimensions | Wrong values |
| `rowConditions` | Built-in assertion | Business-rule violations (negative amounts, bad enum values) | Aggregate checks; empty tables |
| Relationship / FK | Custom assertion action | Orphan rows | Cycles, cardinality violations |
| Row count | Custom assertion action | Empty tables; "the run added nothing" | Wrong-but-nonempty counts |
| Unit test | `type: "test"` | Wrong filter logic, wrong join condition, wrong aggregation | Anything requiring real data volume |

### Data quality dimensions

| Dimension | The question | Typical check |
|---|---|---|
| **Completeness** | Is anything missing? | `nonNull`, row-count assertion, coverage vs. source |
| **Uniqueness** | Is each row identified once? | `uniqueKey` / `uniqueKeys` |
| **Validity** | Do values obey their domain? | `rowConditions` |
| **Consistency** | Do two systems agree? | Cross-source reconciliation (a custom assertion or a dedicated model) |
| **Timeliness** | Is the data recent enough? | Row-count assertion on an incremental + a freshness monitor |
| **Accuracy** | Does it reflect reality? | Tests, business review, sampling |

💡 **Assertions map onto completeness, uniqueness, and validity.** Consistency, timeliness, and
accuracy need different techniques — reconciliation queries, freshness monitors, and business
review. Don't assume a green assertion suite means the data is correct.

### A worked quality-gate model set

```sqlx
// definitions/staging/stg_orders.sqlx
config {
  type: "table",
  partitionBy: { order_date: "DATE(order_date)" },
  assertions: {
    uniqueKey: ["order_id"],
    nonNull: ["order_id", "customer_id", "order_date"],
    rowConditions: ["order_amount >= 0"]
  }
}

SELECT
  id AS order_id, customer_id, amount AS order_amount,
  'complete' AS order_status,
  TIMESTAMP(order_ts) AS updated_at, DATE(order_ts) AS order_date
FROM ${ref("raw_orders")}
WHERE order_status != 'cancelled'
```

```sqlx
// definitions/marts/fct_orders.sqlx
config {
  type: "incremental",
  uniqueKey: ["order_id"],
  partitionBy: { order_date: "DATE(order_date)" },
  assertions: {
    uniqueKey: ["order_id"],
    nonNull: ["order_id", "order_date"],
    rowConditions: ["order_amount >= 0"]
  }
}

SELECT order_id, customer_id, order_amount, order_date, updated_at
FROM ${ref("stg_orders")}
WHERE
  ${when(
    incremental(),
    "updated_at > (SELECT MAX(updated_at) - INTERVAL 7 DAY FROM ${self()})"
  )}
```

**Four built-in assertions, plus two custom ones:**

```sqlx
// definitions/assertions/fct_orders_not_empty.sqlx
config {
  type: "assertion",
  dependencies: ["fct_orders"]
}

SELECT * FROM `my-project.analytics.fct_orders` LIMIT 1
```

```sqlx
// definitions/assertions/fct_orders_relationship_customers.sqlx
config {
  type: "assertion",
  dependencies: ["fct_orders", "dim_customers"]
}

SELECT o.order_id, o.customer_id
FROM `my-project.analytics.fct_orders` AS o
LEFT JOIN `my-project.analytics.dim_customers` AS c
  ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
```

**Six checks, six mechanisms:**

| # | Check | Mechanism | Guards against |
|---|---|---|---|
| 1 | `uniqueKey: ["order_id"]` | Built-in | Duplicate orders; broken `MERGE` |
| 2 | `nonNull: ["order_id", "customer_id", "order_date"]` | Built-in | Missing keys; null join keys |
| 3 | `rowConditions: ["order_amount >= 0"]` | Built-in | Negative amounts (business validity) |
| 4 | `fct_orders_not_empty` | Custom assertion | An empty table slipping through |
| 5 | `fct_orders_relationship_customers` | Custom assertion | Orphan orders (referential integrity) |
| 6 | A `type: "test"` file | Test | Wrong filter / join / aggregation logic |

💡 **The relationship check and the row-count check are both custom assertion actions** because
Dataform has no built-in `relationships` or `rowCount` assertion. This is the single most common
source of confusion for people coming from dbt, where both exist.

---

## 🛠️ Hands-On: Build and Run the Quality Gate

### Step 1 — A model with built-in assertions

(For the source declaration, see Lecture 2.2 — Dataform declares sources with
`type: "declaration"` and references them with `ref()`.)


```sqlx
// definitions/marts/fct_orders.sqlx
config {
  type: "incremental",
  uniqueKey: ["order_id"],
  partitionBy: { order_date: "DATE(order_date)" },
  assertions: {
    uniqueKey: ["order_id"],
    nonNull: ["order_id", "order_date"],
    rowConditions: ["order_amount >= 0"]
  }
}

SELECT order_id, customer_id, order_amount, order_date, updated_at
FROM ${ref("stg_orders")}
WHERE
  ${when(
    incremental(),
    "updated_at > (SELECT MAX(updated_at) - INTERVAL 7 DAY FROM ${self()})"
  )}
```

### Step 2 — Compile and read the generated assertions

```bash
dataform compile
```

The compiled graph contains **separate assertion actions**, not inline `ASSERT` statements:

```bash
# List the assertion nodes in the DAG
python3 -c "
import json
g = json.load(open('.dataform/run.json'))
for a in g.get('assertions', []):
    print(a['target']['name'])
"
```

```
fct_orders_assertions_uniqueKey
fct_orders_assertions_rowConditions
```

### Step 3 — Read the compiled assertion SQL

```bash
python3 -c "
import json
g = json.load(open('.dataform/run.json'))
for a in g.get('assertions', []):
    print('---', a['target']['name'], '---')
    print(a['query'])
"
```

```
--- fct_orders_assertions_uniqueKey ---
SELECT
  *
FROM (
  SELECT
    order_id,
    COUNT(1) AS index_row_count
  FROM `my-project.analytics.fct_orders`
  GROUP BY order_id
  ) AS data
WHERE index_row_count > 1

--- fct_orders_assertions_rowConditions ---
SELECT
  'order_amount >= 0' AS failing_row_condition,
  *
FROM `my-project.analytics.fct_orders`
WHERE NOT (order_amount >= 0)
```

Note that `nonNull` was folded into the `rowConditions` assertion, exactly as the implementation
does — there's no separate `nonNull` assertion node.

### Step 4 — Write a custom assertion

```sqlx
// definitions/assertions/fct_orders_not_empty.sqlx
config {
  type: "assertion",
  dependencies: ["fct_orders"]
}

SELECT * FROM `my-project.analytics.fct_orders` LIMIT 1
```

```bash
dataform compile
dataform run --nodes fct_orders_not_empty
```

### Step 5 — Trigger an assertion failure

```bash
# Insert a duplicate order_id into the source
bq query --use_legacy_sql=false \
  'INSERT INTO `my-project.raw.orders`
   (id, customer_id, amount, order_ts, order_status)
   VALUES (99999, 42, 10.00, TIMESTAMP("2024-05-21 08:00:00"), "complete")'
```

```bash
dataform run --nodes fct_orders
```

```
ERROR: Assertion failed: fct_orders_assertions_uniqueKey
  Query returned 1 row(s).
```

### Step 6 — Inspect the failing rows

```bash
bq query --use_legacy_sql=false \
  'SELECT * FROM `my-project.dataform_assertions.fct_orders_assertions_uniqueKey` LIMIT 10'
```

```
+----------+-------------+------------+
| order_id | index_row_count | ...    |
+----------+-------------+------------+
| 99999    |             2 | ...    |
+----------+-------------+------------+
```

The exact duplicate row is now queryable. That's the payoff of the assertions dataset.

### Step 7 — Write a test

```sqlx
// definitions/tests/fct_orders.sqlx
config {
  type: "test"
}

input "stg_orders" {
  SELECT 1 AS order_id, 10 AS customer_id, 100.0 AS order_amount, 'complete' AS order_status
  UNION ALL
  SELECT 2 AS order_id, 20 AS customer_id, 50.0 AS order_amount, 'cancelled' AS order_status
}

SELECT order_id, customer_id, order_amount
FROM ${ref("stg_orders")}
WHERE order_status = 'complete'
```

```js
// definitions/tests/fct_orders.js
test("fct_orders")
  .input("stg_orders", `SELECT 1 AS order_id, 10 AS customer_id, 100.0 AS order_amount, 'complete' AS order_status
                        UNION ALL
                        SELECT 2 AS order_id, 20 AS customer_id, 50.0 AS order_amount, 'cancelled' AS order_status`)
  .expect(`SELECT 1 AS order_id, 10 AS customer_id, 100.0 AS order_amount`);
```

### Step 8 — Run the test, then break it

```bash
dataform test --nodes fct_orders
```

```
Running 1 test...
  ✓ fct_orders
PASSED
```

```sqlx
// Change the filter to include cancelled orders
WHERE order_status IN ('complete', 'cancelled')
```

```bash
dataform test --nodes fct_orders
```

```
Running 1 test...
  ✗ fct_orders
    Expected 1 row(s), got 2 row(s).
FAILED
```

⚠️ **This is exactly what you want.** The test failed because your logic changed — and it failed
*before* the model touched production data.

### Step 9 — Run everything against the emulator (free)

```bash
dataform core
```

```bash
# In another terminal
dataform test --nodes fct_orders
```

💡 **Break and fix the model dozens of times at zero cost** on the emulator. Run against real
BigQuery only in CI, before merge.

---

## 🔑 Key Takeaways

- Dataform has **two** quality mechanisms: **assertions** (guard the build) and **tests** (guard the logic).
- The four real built-in assertions are **`uniqueKey`, `uniqueKeys`, `nonNull`, `rowConditions`**. There is **no** built-in `relationships` and **no** built-in `rowCount`.
- `nonNull` is not a separate assertion — Dataform **rewrites each column into a `rowConditions` predicate** (`col IS NOT NULL`) and merges it with your own conditions.
- `rowConditions` compiles to one `SELECT ... WHERE NOT (predicate)` branch per condition, unioned together, with the failing predicate named in `failing_row_condition`.
- `uniqueKey` compiles to a `GROUP BY ... HAVING COUNT(1) > 1` probe. `uniqueKeys` takes a **list of lists** to check several composite keys at once — and is mutually exclusive with `uniqueKey`.
- **`rowConditions` predicates are per-row.** An aggregate check like `COUNT(*) > 0` can't be expressed there — write a custom assertion instead.
- **A custom assertion is a file with `config { type: "assertion", dependencies: [...] }`** whose query returns the violating rows. The rule: **an assertion query that returns rows FAILS.**
- Use `LIMIT 1` in an assertion when you only need to know *whether* something is wrong — it lets BigQuery stop at the first violation.
- Relationship checks are best as a **custom assertion action** (one join, returns the offending rows) rather than a `rowConditions` predicate (correlated subquery, expensive, scales with table size).
- Failed assertion rows are recorded in the **`dataform_assertions`** dataset (override with `defaultAssertionDataset`), so you can query exactly what broke.
- Tests use `config { type: "test" }` with `input` blocks as fixtures, and compare against an `expect` query. `dataform test` runs them; `dataform test --nodes <name>` selects specific ones.
- **Tests are hermetic** — fixtures replace `ref()` calls, so your real tables are never read.
- **Each test and each assertion is a real BigQuery query.** Keep fixtures to a handful of rows.
- Assertions map to completeness, uniqueness, and validity. Consistency, timeliness, and accuracy need other techniques.

---

## 📚 Practice Exercises

1. **Build the missing assertions.** Take an incremental orders fact with `stg_orders` and
   `dim_customers`. Write (a) a custom assertion that fails if the table is empty, and (b) a
   custom assertion that fails if any order references a missing customer. Prove each works by
   seeding bad data and showing the run fails. Then show the failing rows in the
   `dataform_assertions` dataset. Finally, rewrite (b) as a `rowConditions` predicate and measure
   the difference in `totalBytesProcessed` between the two forms — explain why the custom
   assertion is cheaper as the table grows.

2. **Write the test suite.** For a model that joins `stg_orders` to `dim_customers` and aggregates
   daily revenue, write three tests: one verifying the join excludes cancelled orders, one
   verifying null `customer_id` rows are dropped, and one verifying the revenue aggregate.
   For each, state precisely which bug it would catch. Then write the "mutant" version of the
   model for one test (e.g. change `>` to `>=`) and show the test failing.

3. **Assertion cost audit.** Take a fact table with ten `rowConditions` assertions. Run
   `dataform run` and record the total bytes processed by the assertions alone. Then convert each
   to a custom assertion action and re-measure. Write a short policy for your team: when do you
   prefer a built-in assertion, and when do you pay for a custom one?

4. **Quality dimensions audit.** For your own project, build a table mapping each of the six data
   quality dimensions (completeness, uniqueness, validity, consistency, timeliness, accuracy) to
   the specific check you would implement, and mark which ones your current assertions and tests
   already cover. Identify the two gaps and write the SQL — not necessarily Dataform code — that
   would close them. For timeliness, specify exactly how you'd measure and alert on data freshness.

---

## 📖 Further Reading

- Dataform overview — https://cloud.google.com/dataform/docs/overview
- Dataform data quality (assertions and tests) — https://cloud.google.com/dataform/docs/build-data-quality
- BigQuery partitioned tables and clustering — https://cloud.google.com/bigquery/docs/partitioned-tables
- BigQuery storage costs and pricing — https://cloud.google.com/bigquery/pricing
- Dataform open-source core (assertion implementation) — https://github.com/dataform-co/dataform
