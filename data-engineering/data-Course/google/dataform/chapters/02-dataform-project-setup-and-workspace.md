# 1.2 — Project Setup & Workspace Anatomy

> **Section 1 · Foundations · Lecture 1.2 · 14:20**

## 🎯 What you will learn

- How to install the Dataform CLI and authenticate it against your GCP project
- The two deployment models: Dataform Cloud (managed) vs self-hosted (Composer / Cloud Build / GitHub Actions)
- How to create a workspace and what `dataform init` actually generates
- Every file in a Dataform project and what it does — `dataform.json`, `package.json`, `definitions/`, `workflows/`, `.dataform/`
- The full `dataform.json` reference: `defaultProject`, `defaultDataset`, `defaultLocation`, `vars`, `warehouse`, `schema` (deprecated)
- Compilation flags (`--json`, `--nodes`, `--vars`, `--schema`, `--project-dir`) and local development with `dataform core`, the BigQuery emulator, and `dataform run`

---

## 🧠 Concept

### What "setup" actually involves

Dataform has no servers, no agents, and no control plane in the CLI. Setup is three separate
things, and it helps to keep them apart:

| Step | Command | Purpose |
|------|---------|---------|
| 1. The tool | `npm install -g @dataform/cli` | A Node.js binary. Nothing GCP-specific yet. |
| 2. The credentials | `gcloud auth application-default login` | Lets the CLI resolve real BigQuery schemas and run jobs. |
| 3. The workspace | `dataform create` / `dataform init` | A directory with `dataform.json` + `definitions/` + `workflows/`. |

You can do steps 1 and 3 with no GCP account at all, and compile — that is deliberately how
you learn the language. Steps that need real BigQuery require step 2.

### The two deployment models

This is the first decision, and it determines everything else about how you operate.

```
   git push
      │
      ├───────────────────────────────┬────────────────────────────────┐
      ▼                               ▼                                │
┌───────────────────┐   ┌───────────────────────────────┐              │
│ A. DATAFORM CLOUD │   │ B. SELF-HOSTED (your CI/CD)  │              │
│                   │   │                               │              │
│ Cloud Build       │   │ Cloud Build / GH Actions      │              │
│   ↓               │   │   npm i -g @dataform/cli     │              │
│ Dataform         │   │   dataform compile            │              │
│ workspace        │   │   dataform run                │              │
│ (managed)        │   │                               │              │
│   ├→ Dataform UI │   │ + Cloud Composer:             │              │
│   │   (history,  │   │   Airflow DAG calls           │              │
│   │    lineage)  │   │   `dataform run`              │              │
│   ├→ .dataform/  │   └───────────────┬───────────────┘              │
│   │   run.sql+DAG│                   │                              │
│   └→ scheduler   │                   │                              │
└─────────┬─────────┘                   │                              │
          │                             │                              │
          └──────────────┬──────────────┘                              │
                         ▼                                             │
                      BigQuery ◄───────────────────────────────────────┘
```

| Dimension | Dataform Cloud | Self-hosted (Composer / Cloud Build) |
|-----------|----------------|--------------------------------------|
| Where compilation happens | Google-managed, in your project | Your CI runner / Composer worker |
| Scheduling | Built in (cron, Cloud Scheduler, API) | You build it (Composer DAG or cron) |
| Build history UI | Rich: per-action history, lineage graph, error messages | Only what your CI retains (log artifacts) |
| Lineage in UI | Yes | No — build a viewer or use BigQuery lineage |
| Tests | Managed, zero setup | You run one (or use the BigQuery emulator) |
| Versioning / branches | Managed git integration | Your git, your rules |
| Cost | Workspace pricing | Compute + BigQuery only |
| Vendor lock-in | Higher | Lower — `run.sql` is portable SQL |
| Best for | Teams wanting a UI, lineage, and managed schedules | Platform teams, CI/CD-native shops |

⚠️ **Dataform Cloud is a Google Cloud feature.** The `@dataform/core` package is open source and
the CLI runs anywhere Node.js runs, but the managed UI, workspace registration, and the
built-in scheduler are Cloud-only.

💡 **The compiled artifact is identical in both models.** `dataform compile` produces the same
`run.sql` and the same DAG. Cloud adds UI, scheduling, and lineage around that artifact;
self-hosted gives you control. The SQLX files do not change when you migrate.

### The anatomy of a workspace

```
my-workspace/
├── dataform.json          ← PROJECT CONFIG (the most important file)
├── package.json           ← npm manifest: pins the @dataform/core version
├── .gitignore             ← excludes .dataform/, node_modules/
│
├── definitions/           ← your SQLX models live here
│   ├── sources/           ← EXTERNAL TABLES (source() declarations)
│   │   ├── raw_orders.sqlx
│   │   └── raw_customers.sqlx
│   ├── stg/               ← convention: staging layer
│   ├── int/               ← convention: intermediate layer
│   └── marts/             ← convention: presentation layer
│
├── workflows/             ← workflow definitions (action lists, scheduling)
│   └── orders.json
│
└── .dataform/             ← COMPILED OUTPUT (git-ignored, regenerate freely)
    ├── run.json           ← the DAG: targets, dependencies, operations
    ├── run.sql            ← the compiled SQL BigQuery executes
    ├── metadata.json      ← table metadata (descriptions, columns, labels)
    └── schema.json        ← inferred/asserted schemas per model
```

| Path | Purpose | Edit it? |
|------|---------|----------|
| `definitions/` | The models. SQLX files. | **Yes — this is your code.** |
| `workflows/` | Named groups of actions ("run the orders DAG"). | Yes |
| `.dataform/` | Compiler output. | **No — never edit, never commit.** |
| `dataform.json` | Project-wide config. | Yes |
| `package.json` | npm manifest; pins the `@dataform/core` compiler version. | Rarely |

⚠️ **Never commit `.dataform/`.** It is derived, it is large, and it will produce noisy diffs. The
default `.gitignore` handles it — but if you see it staged, something is wrong with your
`.gitignore`.

### `dataform.json` — the full reference

This is the file that decides where your tables land. A fully annotated version:

```json
{
  "defaultProject": "my-gcp-project",
  "defaultDataset": "analytics",
  "defaultLocation": "US",

  "defaultAssertionDataset": "analytics_assertions",

  "vars": {
    "startDate": "2024-01-01",
    "endDate": "2024-12-31",
    "minOrderValue": 50.0,
    "sourceProject": "raw-data-project",
    "sourceDataset": "raw"
  },

  "warehouse": {
    "database": "my-gcp-project",
    "schema": "analytics",
    "location": "US",
    "assertDataset": "analytics_assertions"
  },

  "workflowSettings": {
    "defaultProject": "my-gcp-project",
    "defaultDataset": "analytics",
    "defaultLocation": "US",
    "assertionSchema": "analytics_assertions"
  },

  "dataformCoreVersion": "^3.0.0"
}
```

| Field | Type | Meaning |
|-------|------|---------|
| `defaultProject` | string | GCP project that owns the target tables. |
| `defaultDataset` | string | Default BigQuery dataset. **Every model lands here unless overridden.** |
| `defaultLocation` | string | BigQuery location (`US`, `EU`, `US-CENTRAL1`, …). All tables in one project should share a location. |
| `defaultAssertionDataset` | string | Dataset where assertion tables are written. Separate from data so failures are easy to spot. |
| `vars` | object | Compile-time variables, resolved with `resolve("name")`. |
| `warehouse` | object | The target warehouse: `database`, `schema`, `location`, `assertDataset`. |
| `warehouse.database` | string | GCP project of the target. Differs from `defaultProject` only for cross-project output. |
| `warehouse.schema` | string | Dataset the models write to. |
| `warehouse.location` | string | BigQuery location. |
| `warehouse.assertDataset` | string | Dataset for assertion/result tables. |
| `schema` | object | **Deprecated** — superseded by `warehouse`. |
| `workflowSettings` | object | Defaults applied to generated workflows. |
| `dataformCoreVersion` | string | Pins the `@dataform/core` version used to compile. |

⚠️ **The top-level `schema` key is deprecated.** Older Dataform versions used
`"schema": { "database": ..., "schema": ..., "location": ... }` to configure the target
warehouse. The modern equivalent is the **`warehouse`** object. Dataform still tolerates the old
shape for backwards compatibility, but new projects should use `warehouse`.

💡 **`warehouse` vs `defaultProject`/`defaultDataset`:** they overlap confusingly. The `default*`
keys set the *logical* target; `warehouse` sets the *physical* one. In practice you set them to
the same values. If you want models written into a different project than the one you deploy
from, `warehouse.database` is the knob.

### `vars` — compile-time constants

`vars` are **not** BigQuery variables, not runtime parameters, and not environment variables.
They are substituted into your SQLX at compile time, and read with `resolve("name")`.

```json
{ "vars": { "startDate": "2024-01-01", "minOrderValue": 50.0,
            "regions": ["us-east1", "us-west1"] } }
```

```sqlx
config { type: "view" }

SELECT *
FROM ${source("raw", "orders")}
WHERE order_date BETWEEN '${resolve("startDate")}' AND '${resolve("endDate")}'
  AND total_amount >= ${resolve("minOrderValue")}
```

Nested vars resolve to objects and arrays, so `resolve("regions")` gives you
`["us-east1","us-west1"]`.

💡 **Use `vars` for things that change between environments** — dataset names, date windows,
feature flags. Do **not** use them to pass secrets; there is no secret store in `dataform.json`,
and it is committed to git.

### `definitions/` and the `sources/` convention

Dataform discovers models by walking the `definitions/` directory. The **filename becomes the
model name**, with the `.sqlx` extension stripped:

```
definitions/marts/fct_orders.sqlx   →  model name: fct_orders
definitions/stg/stg_orders.sqlx     →  model name: stg_orders
```

Subdirectories are purely conventional — `stg/`, `int/`, `marts/` are the community-standard
layering, and they make `include`/`exclude` patterns easy later. But Dataform itself does not
care about folder names; only the filename matters.

The `definitions/sources/` folder is special. Files there declare **external tables** that
Dataform does not create:

```
definitions/sources/raw_orders.sqlx

config {
  type: "declarative",
  database: "source-project",
  schema: "raw",
  description: "Raw orders landing table, written by the operational system"
}

source("raw_orders", "orders")
```

Here the **file name** (`raw_orders`) is the *source name*, and the argument inside
`source("raw_orders", "orders")` is the *table name*. Models reference it as
`${source("raw_orders", "orders")}`.

### `workflows/`

A workflow is a **named set of actions** — a subset of the DAG you can build, run, or test
independently.

```json
{ "workflows": [ { "name": "orders", "tags": ["daily"], "actionSelector": ["orders"] } ] }
```

The `actionSelector` is a list of *selectors*; each can be a model name, a tag, or a workflow
name. `dataform run --workflows orders` runs only matching actions.

⚠️ **`workflows/` is optional.** Many teams just run `dataform run` (everything) plus `--nodes`
for targeted rebuilds. Use workflows when you need distinct schedules — e.g. an hourly `stg`
workflow and a nightly `marts` workflow.

### The `.dataform/` output directory

Compilation writes a self-contained bundle:

```
.dataform/
├── run.json          ← the DAG
├── run.sql           ← compiled SQL
├── metadata.json     ← table metadata (descriptions, columns, labels)
├── schema.json       ← inferred / asserted schemas
└── README.md         ← generated docs
```

`run.json` is the one you will inspect most, because it is the machine-readable execution plan:

```json
{
  "targets": [
    { "name": "fct_orders",
      "database": "my-gcp-project",
      "schema": "analytics",
      "type": "table",
      "relation": "my-gcp-project.analytics.fct_orders",
      "fileName": "definitions/marts/fct_orders.sqlx" }
  ],
  "dag": {
    "stg_orders": { "relations": ["my-gcp-project.analytics.stg_orders"] },
    "fct_orders": { "relations": ["my-gcp-project.analytics.fct_orders"] }
  },
  "operations": [
    { "metadata": { "target": { "name": "fct_orders" } }, "hasOutput": true }
  ],
  "tests": [],
  "metadata": { "projectId": "my-gcp-project", "defaultDataset": "analytics" }
}
```

`targets` is the inventory of models. `dag` maps each model to the relations it produces.
`operations` is the ordered list of things to do. `tests` holds the unit test and assertion
definitions.

💡 **`run.json` is the machine-readable execution plan.** When a run fails, this file tells you
what was supposed to happen and in what order — and it is the first thing to inspect when a
model you did not expect ran, or one you expected did not.

### `package.json` and `.gitignore`

`package.json` exists for one reason: **pinning the compiler version**.

```json
{
  "name": "my-workspace",
  "version": "1.0.0",
  "private": true,
  "dependencies": { "@dataform/core": "3.0.0" },
  "scripts": { "compile": "dataform compile", "test": "dataform test" }
}
```

💡 **Pin `@dataform/core` exactly, not with a caret.** A caret lets a fresh `npm install` pull a
newer compiler and change your compiled SQL without any commit on your side. Exact pinning makes
your builds reproducible.

The generated `.gitignore` excludes the compiler output and dependencies:

```gitignore
.dataform/
node_modules/
```

Add `.env` if you keep local credentials.

### `dataform init` and its flags

`dataform init` generates a workspace *in place*; `dataform create` (from Chapter 1) also
registers a managed workspace in Dataform Cloud.

```bash
dataform init \
  --project-name=my-workspace \
  --project-dir=./my-workspace \
  --dataform-json=dataform.json \
  --dataform-project-dir=definitions \
  --location=US
```

| Flag | Meaning |
|------|---------|
| `--project-name` | Workspace name. Must be globally unique for Dataform Cloud workspaces. |
| `--project-dir` | Directory to create the workspace in. |
| `--dataform-json` | Path to a `dataform.json` to seed the workspace with. |
| `--dataform-project-dir` | Name of the definitions folder. Default `definitions`. |
| `--location` | BigQuery location. Default `US`. |
| `--no-example` | Skip the example models. |

💡 **Use `init`, not `create`, for local development.** `create` tries to register a managed
workspace in Dataform Cloud, which needs the Dataform API enabled on your project. `init` is
offline and instant.

### Compilation targets and flags

```bash
dataform compile --nodes fct_orders
dataform compile --vars '{"startDate": "2025-01-01"}'
dataform compile --project-dir definitions
dataform compile --dataform-json ./config/prod.dataform.json
```

| Flag | Purpose |
|------|---------|
| `--json` | Output directory for the compiled bundle. Default `.dataform`. |
| `--nodes` | Comma-separated model names to compile. Dependencies are pulled in automatically. |
| `--vars` | JSON object of var overrides, merged over `dataform.json`. |
| `--schema` | Legacy target-dataset override. Superseded by `warehouse` / `defaultDataset`. |
| `--project-dir` | Directory containing `definitions/`. |
| `--dataform-json` | Path to an alternative `dataform.json`. |
| `--actions` | Which action types to compile: `build`, `run`, `test`. |
| `--dry-run` | Compile and print the actions without executing. |

⚠️ **`--schema` is the legacy way to point compilation at a different dataset.** New projects
should change `defaultDataset` in `dataform.json` or pass `--vars` instead, because `--schema`
does not update `warehouse` and can leave the two disagreeing.

### Local development: `dataform core`, the emulator, and auth

`dataform core` starts a **local Dataform Core server** — the same compiler Dataform Cloud
runs, wrapped in an HTTP API. Tools like the VS Code extension use it to compile your project
without touching GCP.

```bash
dataform core                              # foreground server
dataform compile --project-dir definitions # in another terminal
```

For running SQL **without touching real BigQuery**, use the **BigQuery emulator**:

```bash
docker run -p 9050:9050 -e BIGQUERY_EMULATOR_HOST=localhost:9050 \
  gcr.io/cloud-bigquery/bqemu:latest
export BIGQUERY_EMULATOR_HOST=localhost:9050
dataform test --project-dir definitions
```

⚠️ **The emulator is not BigQuery.** It implements enough of the API for Dataform's unit tests,
but not every function, DDL statement, or BigQuery-specific feature. Treat emulator passes as a
fast first gate, never as proof.

Authentication for local runs: `gcloud auth application-default login` (recommended) or
`export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json` (what CI uses). You need
`roles/bigquery.jobUser`, `roles/bigquery.dataEditor`, and `roles/bigquery.user` on the target
project, plus `roles/dataform.editor` for Cloud workspaces.

⚠️ **Do not check in service account JSON keys.** In Cloud, prefer Workload Identity / service
account impersonation so no key material exists in the repo at all.

### `dataform run`

`dataform run` compiles and then **executes** the resulting SQL against BigQuery.

```bash
# Run everything
dataform run

# Run one model and everything it depends on
dataform run --nodes fct_orders

# Run with var overrides
dataform run --nodes fct_orders --vars '{"startDate": "2025-01-01"}'

# Compile only — print the actions without executing (free, safe)
dataform run --dry-run

# Choose action types
dataform run --actions run          # only execute actions, no assertions
dataform run --actions build        # only build (create/replace) actions
dataform run --actions test         # only run tests
```

| Flag | Meaning |
|------|---------|
| `--dry-run` | Compile, print what *would* run, execute nothing. **Always try this first.** |
| `--actions` | `build`, `run`, `test`, or a comma-separated list. |
| `--nodes` | Restrict to these models (plus dependencies). |
| `--vars` | Var overrides for this execution. |
| `--include-dependents` | Include downstream models of the selected nodes. |
| `--full-refresh` | For incremental models, force a complete rebuild. |

💡 **The local dev loop is three commands:** `dataform compile` (catch errors, ~2s, free) →
`dataform run --dry-run` (see exactly what will execute) → `dataform run` (execute).

---

## 🛠️ Hands-On: Build Your First Workspace

### Step 1 — Install and authenticate

```bash
npm install -g @dataform/cli
dataform --version
gcloud auth application-default login
gcloud config set project my-gcp-project
```

### Step 2 — Create the workspace

```bash
mkdir -p ~/dataform-workspace && cd ~/dataform-workspace

dataform init \
  --project-name=dataform-course \
  --project-dir=. \
  --dataform-json=dataform.json \
  --dataform-project-dir=definitions \
  --location=US \
  --no-example
```

### Step 3 — Write `dataform.json`

```json
{
  "defaultProject": "my-gcp-project",
  "defaultDataset": "analytics",
  "defaultLocation": "US",
  "defaultAssertionDataset": "analytics_assertions",

  "vars": {
    "startDate": "2024-01-01",
    "endDate": "2024-12-31",
    "minOrderValue": 50.0,
    "sourceProject": "raw-data-project",
    "sourceDataset": "raw"
  },

  "warehouse": {
    "database": "my-gcp-project",
    "schema": "analytics",
    "location": "US",
    "assertDataset": "analytics_assertions"
  },

  "dataformCoreVersion": "3.0.0"
}
```

### Step 4 — Write a source declaration

`definitions/sources/raw_orders.sqlx`:

```sqlx
config {
  type: "declarative",
  database: ${dataform.projectConfig.vars.sourceProject},
  schema: ${dataform.projectConfig.vars.sourceDataset},
  description: "Raw orders landing table",
  loaded_at_field: "_loaded_at",
  freshness: { errorAfter: "48h", warnAfter: "24h" }
}

source("raw_orders", "orders")
```

### Step 5 — Write a model

`definitions/stg/stg_orders.sqlx`:

```sqlx
config {
  type: "table",
  description: "Staged orders, one row per order, deduplicated"
}

SELECT order_id, customer_id, order_date, total_amount, _loaded_at
FROM ${source("raw_orders", "orders")}
WHERE order_date BETWEEN '${resolve("startDate")}' AND '${resolve("endDate")}'
  AND total_amount >= ${resolve("minOrderValue")}
QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY _loaded_at DESC) = 1
```

### Step 6 — Compile and inspect

```bash
dataform compile
ls -la .dataform/          # run.json  run.sql  metadata.json  schema.json

# List the compiled targets
python3 -c "
import json
d = json.load(open('.dataform/run.json'))
for t in d['targets']:
    print(t['name'], '->', t['relation'])
"
```

Expected output:

```text
stg_orders -> my-gcp-project.analytics.stg_orders
```

### Step 7 — Dry run, then run

```bash
dataform run --dry-run              # see what would happen — no query executes
dataform run --nodes stg_orders     # actually run it

# Verify in BigQuery
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `my-gcp-project.analytics.stg_orders`'
```

### Step 8 — Override vars without editing files

```bash
dataform compile --vars '{"startDate": "2025-06-01", "endDate": "2025-06-30"}'
grep -c "2025-06-01" .dataform/run.sql   # confirm the override reached the SQL
```

### Step 9 — Add a `workflows/` file

`workflows/orders.json`:

```json
{ "workflows": [ { "name": "orders", "tags": ["daily"], "actionSelector": ["orders"] } ] }
```

```bash
dataform compile
dataform run --actions run --workflows orders --dry-run
```

### Step 10 — Wire it into CI

In GitHub Actions, the job is: check out → install Node 20 → `npm install -g @dataform/cli` →
authenticate to GCP with `google-github-actions/auth@v2` (Workload Identity Federation) →
`dataform compile`.

💡 **Use Workload Identity Federation, not a service account key.** The key never exists in the
repo, and the same pattern works in Cloud Build.

---

## 🔑 Key Takeaways

- Setup is three separable things: the CLI, the credentials, and the workspace.
- Dataform Cloud vs self-hosted is a decision about *orchestration and UI*, not about SQLX. The compiled `run.sql` is identical.
- The workspace has four moving parts: `dataform.json` (config), `definitions/` (your models), `workflows/` (named action groups), `.dataform/` (generated output — never commit it).
- `warehouse` is the modern target config (`database` / `schema` / `location` / `assertDataset`). The top-level `schema` key is **deprecated**.
- `vars` are compile-time constants, read with `resolve("name")`, overridable with `--vars`. Not runtime parameters, and not a secret store.
- The `definitions/sources/` folder holds `source()` declarations: the **file name is the source name**, the argument inside `source()` is the table name. Folder names like `stg/`/`int/`/`marts/` are convention only — the filename is what becomes the model name.
- `dataform core` gives you a local compiler server; the BigQuery emulator gives you a local test target — but it is *not* BigQuery.
- The local loop is `compile` → `run --dry-run` → `run`. Compile is free and catches most errors.
- `dataform run --nodes <model>` rebuilds one model and its upstream dependencies; `--full-refresh` overrides incremental logic.

---

## 📚 Practice Exercises

1. **Workspace teardown and rebuild.** Create a workspace with `dataform init`, delete `.dataform/` entirely, and rebuild with `dataform compile`. Confirm the `run.json` is identical. Explain why committing `.dataform/` is a mistake in terms of diff noise, merge conflicts, and trust.

2. **`dataform.json` archaeology.** Take the deprecated top-level `schema` block from an old tutorial and convert it to `warehouse`. Then write a `dataform.json` for a project where models live in `analytics` but assertions live in `analytics_assertions`, and vars set a date window and a source dataset. Prove it works by compiling with `--vars` overrides and grepping the compiled SQL.

3. **Deployment model decision memo.** Write a one-page comparison of Dataform Cloud vs Cloud Composer orchestration for a team of 12 data engineers. Cover: build history visibility, debugging a failed 3am run, branching strategy, cost at 100 models and 500 daily runs, and lock-in. Recommend one, and name the condition under which you would switch.

4. **Local loop under failure.** Add a model that references a non-existent model via `ref("does_not_exist")`. Run `dataform compile` and record the exact error. Then run `dataform run --dry-run` and record the difference. Finally, fix it and show the working compile. Explain why the compile-time check is more valuable than the run-time failure.

5. **Emulator limitations.** Run the BigQuery emulator and write a query using a feature you suspect it will not support (a window function, a `PIVOT`, a BigQuery-specific function). Document what happens, and explain why a green local suite does not guarantee a green production run.

---

## 📖 Further Reading

- Dataform overview — https://cloud.google.com/dataform/docs/overview
- Dataform core concepts — https://cloud.google.com/dataform/docs/concepts/overview
- Dataform `dataform.json` reference — https://cloud.google.com/dataform/docs/reference/dataform-json
- Dataform CLI reference — https://cloud.google.com/dataform/docs/reference/cli
- Dataform local development — https://cloud.google.com/dataform/docs/local-development
- Dataform Dataform Core open source — https://github.com/dataform-co/dataform
- BigQuery emulator — https://cloud.google.com/bigquery/docs/emulator
- Cloud Build — https://cloud.google.com/build/docs
