# 1.1 — What Is Dataform and Why It Exists

> **Section 1 · Foundations · Lecture 1.1 · 12:40**

## 🎯 What you will learn

- The problem Dataform solves: SQL pipelines that break silently and can't be tested
- What Dataform actually is under the hood — a SQL compiler, not a scheduler
- How it differs from dbt, and when to pick which
- Where Dataform sits in the GCP ecosystem alongside BigQuery, Dataproc, and Composer
- The core mental model: **declare a graph, get a correct DAG**

---

## 🧠 Concept

### The problem: a folder of SQL scripts

Most data teams start exactly like this:

```
scripts/
  01_extract_orders.sql
  02_clean_orders.sql
  03_aggregate_daily.sql
  04_build_dashboard.sql
  run.sh          # psql -f 01... && psql -f 02... && ...
```

This works. It also breaks constantly, in ways that are painful to diagnose:

| Failure | Why it happens | How long it takes to find |
|---------|----------------|---------------------------|
| `02_clean_orders.sql` runs before `01_extract_orders.sql` | The dependency is encoded in a filename, not in the data | Hours |
| Someone edits `03` but forgets `04`, so the dashboard is stale | No dependency graph, no invalidation | Until someone notices a wrong number |
| A table is dropped and `01` recreates it with the wrong schema | No schema contract, no test | Until a downstream query fails |
| The pipeline runs twice and double-counts | No idempotency strategy | Until the numbers look wrong |
| "Did this pipeline run last night?" | No run metadata, no lineage | Unanswerable |

Every one of these is a **missing dependency graph**.

### What Dataform is

Dataform is a **declarative SQL compiler**. You write SQL files that declare models, their
dependencies, their materialization strategy, and their tests. Dataform parses them, builds a
dependency graph, resolves `ref()` and `source()` calls to concrete table names, injects the
materialization logic, and outputs a single executable SQL script — plus a DAG describing what
runs in what order.

```
        Your SQLX files              Dataform compiler              Output
   ┌──────────────────────┐      ┌─────────────────────┐      ┌────────────────┐
   │ definitions/         │      │  parse              │      │ run.sql        │
   │   stg_orders.sqlx    │ ───▶ │  build DAG          │ ───▶ │ run.json (DAG) │
   │   fct_orders.sqlx    │      │  resolve refs       │      │ manifest.json  │
   │   sources/           │      │  inject strategy    │      │ schema.json    │
   │     orders.sqlx      │      │  validate           │      │ metadata.json  │
   └──────────────────────┘      └─────────────────────┘      └────────────────┘
                                    ▲
                                    │
                             BigQuery executes
                             the compiled SQL
```

Three things follow from this:

1. **The compiler is the safety net.** You cannot reference a table that does not exist, because
   `ref('stg_orders')` is checked at compile time, and so is `source('raw', 'orders')`.
2. **The DAG is the scheduler's input.** Dependency order is derived, not declared in a fragile
   shell script.
3. **The compilation output is portable.** `run.sql` is just SQL. You can run it with `bq query`,
   inspect it, diff it, or run it somewhere else.

### What Dataform is NOT

⚠️ **Dataform does not schedule anything by itself.** This is the single most common
misunderstanding. Dataform compiles. Something else *runs*:

- **Dataform Cloud** (Google's managed service) — has built-in scheduling
- **Cloud Composer** — an Airflow DAG calls `dataform run` on a schedule
- **GitHub Actions / Cloud Build** — CI/CD pipeline triggers the compilation
- **Your laptop** — `dataform compile` for local development

Everything in this course that involves execution will use one of these explicitly.

### Dataform vs dbt

Both solve the same core problem. The differences are real and worth understanding:

| Dimension | Dataform | dbt |
|-----------|----------|-----|
| Parent company | Google (acquired Fivetran 2023) | dbt Labs |
| Language | **SQLX** — SQL with JSX-style templating | **Jinja** in pure `.sql` files |
| Local development | `dataform core` (local emulator, BigQuery emulator) | `dbt compile`/`dbt run` locally |
| Full local run against BigQuery | **Yes** — `dataform run` hits real BigQuery | Yes — `dbt run` |
| Emulator for tests | Yes — BigQuery emulator | Yes — adapter plugins |
| Native GCP integration | **Deep** — Cloud Composer, IAM, BigQuery, Dataproc | Via plugins (e.g. `dbt-bigquery`) |
| CI/CD | Google Cloud Build / GitHub Actions native | Requires `dbt deps` + profiles + adapter install |
| Incremental models | Built-in `incremental()` config, `is_incremental()` | Built-in `is_incremental()` macro |
| Table operations | **Built-in** — pre/post hooks, table ops, assertions | Hooks via macros |
| Tests | Built-in, with `severity` and `config` blocks | Built-in + packages from dbt Hub |
| Open source | Core open source; Cloud is proprietary | Fully open source |
| Managed cloud offering | Dataform Cloud | dbt Cloud |

💡 **Why pick Dataform?** If your stack is GCP-native, Dataform gives you the tightest
integration — Composer orchestration, IAM, BigQuery's native table operations, and a local
emulator that runs real BigQuery SQL without a bill. The SQLX language is also more legible than
Jinja to people who write SQL for a living.

**You should still learn dbt's concepts** — incremental strategies, staging/intermediate/final
layers, tests, seeds, snapshots — because they transfer directly, and many teams run both.

### Where Dataform sits in GCP

```
                    ┌──────────────────────┐
                    │   Git / GitHub       │
                    └──────────┬───────────┘
                               │ push
                    ┌──────────▼───────────┐
                    │   Dataform           │   ← compiles SQLX → run.sql + DAG
                    │   (workspace)        │
                    └──────────┬───────────┘
                               │ run.sql
              ┌────────────────┴────────────────┐
              │                                 │
   ┌──────────▼───────────┐         ┌───────────▼────────────┐
   │  Cloud Composer     │         │  Cloud Build / GH     │
   │  (Airflow DAG)      │         │  Actions (CI/CD)      │
   │  ← schedule lives   │         │  ← CI/CD lives         │
   └──────────┬───────────┘         └───────────┬────────────┘
              │                                 │
              └────────────────┬────────────────┘
                               │ BigQuery SQL
                    ┌──────────▼───────────┐
                    │  BigQuery            │
                    │  tables + lineage    │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Looker / Looker     │
                    │  Studio              │
                    └──────────────────────┘
```

BigQuery has its own **native lineage** (in the console and via `INFORMATION_SCHEMA`), but
Dataform adds the *build-time* lineage: which model failed, which models are downstream of the
broken one, and what needs re-running.

### The core mental model

Everything in Dataform reduces to one idea:

> **Declare the graph. The compiler derives the execution plan.**

Concretely, a model declaration has four parts:

1. **A name** — the filename becomes the model name (`stg_orders.sqlx` → `stg_orders`)
2. **A materialization** — table, view, incremental, or ephemeral
3. **Inputs** — `ref()` for other models, `source()` for external tables
4. **Logic** — the SQL that produces the output

```
┌────────────────────────────────────────────────────────────────┐
│  stg_orders.sqlx                                               │
│                                                                │
│  config { type: "table" }        ← materialization            │
│                                                                │
│  SELECT ...                      ← logic                      │
│  FROM ${source("raw", "orders")} ← external input             │
│  WHERE ...                                                 │
│                                                                │
│  This model has no model inputs.                               │
│  It reads raw.orders.                                          │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  fct_orders.sqlx                                               │
│                                                                │
│  config { type: "table" }                                    │
│                                                                │
│  SELECT ...                      ← logic                      │
│  FROM ${ref("stg_orders")}       ← model input (creates edge)│
│                                                                │
│  This model depends on stg_orders.                             │
│  Dataform will run stg_orders first.                           │
└────────────────────────────────────────────────────────────────┘
```

That `ref()` call is the whole point. It is simultaneously:
- A dependency declaration (Dataform orders the DAG)
- A name resolution (it becomes the real table name, including project/dataset)
- A type check (Dataform knows the referenced model's schema)
- An invalidation trigger (change `stg_orders` → `fct_orders` is marked stale)

### Why this matters for BigQuery specifically

BigQuery's serverless model means **no cluster to tune**, but it does *not* mean no engineering
discipline. On BigQuery, the expensive mistakes are:

- Scanning a full table when a partition filter was available
- Running a model twice and appending twice
- Refactoring a table without knowing 40 downstream queries reference it
- A `MERGE` that produces duplicates because the source had late-arriving rows

Dataform addresses the last three directly (dependency graph, invalidation, idempotent
materialization strategies) and helps with the first (via `partitionBy` config and dry-run
estimation).

💡 **The single most valuable thing Dataform gives a BigQuery team is safe refactoring.** Rename a
column, run `dataform compile`, and the compiler tells you which models break — before you break
them.

---

## 🛠️ Hands-On: Install and Verify

```bash
# Install the Dataform CLI
npm install -g @dataform/cli

# Check the version
dataform --version

# Where is it?
which dataform
```

```bash
# Create your first workspace locally (no GCP account needed to start)
dataform create --project-name=dataform-course --project-dir=./dataform-course

cd dataform-course

# Generate the default example project
dataform generate-workflow-script
```

The generated workspace looks like this:

```
dataform-course/
├── dataform.json              # project config
├── package.json
├── definitions/
│   ├── sources/
│   │   └── example_source.sqlx
│   └── example/
│       ├── definitions.sqlx
│       └── example.sqlx
├── workflows/
│   └── example.json
└── .gitignore
```

```bash
# Compile — this is the core loop. It resolves refs and builds the DAG.
dataform compile

# The compiled artifacts land in .dataform/
ls -la .dataform/
#   run.json         ← the DAG: nodes, dependencies, operations
#   run.sql          ← the compiled SQL
#   metadata.json    ← table metadata
#   schema.json      ← per-model schema (when using schema blocks)
```

💡 **Make `dataform compile` your first line of defense.** It is fast (seconds), free, and catches
broken references, duplicate model names, invalid configs, and cyclic dependencies — all before a
single query runs.

### Inspect the compiled output

```bash
# The compiled SQL — this is what BigQuery actually executes
cat .dataform/run.sql | head -60

# The DAG — inspect this when you need to understand execution order
cat .dataform/run.json | python3 -m json.tool | head -40
```

```bash
# Check what a single model compiled to
dataform compile --nodes stg_orders
```

---

## 🔑 Key Takeaways

- Dataform is a **SQL compiler**. It produces `run.sql` and a DAG. Something else executes it.
- The core value is the **dependency graph**: `ref()` declares an edge, and the compiler derives
  execution order, invalidation, and type information from it.
- `ref()` is four things at once: dependency, name resolution, type check, invalidation trigger.
- **Dataform does not schedule.** Use Dataform Cloud, Cloud Composer, Cloud Build, or GitHub
  Actions.
- Dataform vs dbt is a language and ecosystem choice (SQLX vs Jinja, GCP-native vs
  open-source-plus-plugins). The core concepts transfer directly.
- **Always compile before you run.** It is free, fast, and catches most mistakes.
- BigQuery's serverless model removes cluster tuning, not engineering discipline. Dataform
  addresses safe refactoring, idempotency, and invalidation — the BigQuery-specific failure modes.
- `dataform compile --nodes <model>` is a fast way to inspect one model's compiled SQL.

---

## 📚 Practice Exercises

1. **The folder-of-scripts audit.** Find a team (yours or a public one) that orchestrates BigQuery
   with shell scripts. List every failure mode that a dependency graph would prevent. Rank them by
   how much time each costs per incident.

2. **Ref() decomposition.** For the model `fct_orders` that reads `ref("stg_orders")`, write down
   the four distinct things that one `ref()` call communicates to the compiler. Then explain what
   would break if you replaced it with a hardcoded table name.

3. **Dataform vs dbt decision.** You are joining a team that already uses dbt on BigQuery, and
   leadership wants to standardize on Google Cloud tooling. Write a one-page recommendation.
   Your answer must name at least three concrete migration costs and one concrete benefit.

4. **Compile archaeology.** Create the default Dataform workspace, compile it, and answer: (a)
   how many models were compiled? (b) what does the DAG look like? (c) what happens to the DAG if
   you add a model that reads `fct_orders`? (d) what is in `run.sql` that is not in your source
   `.sqlx` files, and why?

---

## 📖 Further Reading

- Dataform overview — https://cloud.google.com/dataform/docs/overview
- Dataform SQLX reference — https://cloud.google.com/dataform/docs/reference/sqlx
- Dataform core concepts — https://cloud.google.com/dataform/docs/concepts/overview
- Dataform vs dbt — https://cloud.google.com/dataform/docs/comparison/dataform-and-dbt
- BigQuery best practices — https://cloud.google.com/bigquery/docs/best-practices
