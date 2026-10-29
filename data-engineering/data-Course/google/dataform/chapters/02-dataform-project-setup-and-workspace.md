# 1.2 — Project Setup & Workspace Anatomy

> **Section 1 · Foundations · Lecture 1.2 · 14:20**

## 🎯 What you will learn

- Installing the Dataform CLI and authenticating it against your GCP project
- The two deployment models: Dataform Cloud (managed) vs self-hosted (Cloud Composer / Cloud Build / GitHub Actions)
- Creating a project: `dataform init`, the directory layout, and `workflow_settings.yaml`
- Every file in a Dataform project — `definitions/`, `includes/`, `workflow_settings.yaml`, `package.json`, `.gitignore`
- The full `workflow_settings.yaml` reference: `defaultProject`, `defaultDataset`, `defaultLocation`, `defaultAssertionDataset`, `vars`
- Compilation flags (`--nodes`, `--vars`, `--project-dir`, `--actions`) and the local dev loop
- `dataform core`, the BigQuery emulator, and `dataform run`

---

## 🧠 Concept

### What "setup" actually involves

Dataform has no servers, no agents, and no control plane in the CLI. Setup is three separable
things:

| Step | Command | Purpose |
|------|---------|---------|
| 1. The tool | `npm install -g @dataform/cli` | A Node.js binary. Nothing GCP-specific yet. |
| 2. The credentials | `dataform init-creds` | Writes a `.df-credentials.json` file the CLI uses to reach remote services. |
| 3. The project | `dataform init` | A directory with `definitions/`, `includes/`, and `workflow_settings.yaml`. |

⚠️ **`.df-credentials.json` contains access credentials. Never commit it.** Add it to
`.gitignore` immediately. This is the modern Dataform equivalent of the old
`GOOGLE_APPLICATION_CREDENTIALS` JSON key — and it has the same rule: keys live outside the repo.

### The two deployment models

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
│   ├→ compiled    │   └───────────────┬───────────────┘              │
│   │   graph (DAG)│                   │                              │
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
| Scheduling | Built in (release configurations, Cloud Scheduler) | You build it (Composer DAG or cron) |
| Build history UI | Rich: per-action history, compiled graph, error messages | Only what your CI retains |
| Lineage | Interactive DAG in the Compiled graph tab | No — build a viewer or use BigQuery lineage |
| Version control | Git-based, in-workspace | Your git, your rules |
| Cost | Workspace pricing | Compute + BigQuery only |
| Vendor lock-in | Higher | Lower — the compiled SQL is portable |
| Best for | Teams wanting a UI, lineage, and managed schedules | Platform teams, CI/CD-native shops |

💡 **The compiled artifact is identical in both models.** `dataform compile` produces the same
SQL and the same graph. Cloud adds UI, scheduling, and lineage around it; self-hosted gives you
control. Your SQLX files do not change when you migrate.

⚠️ **Dataform Cloud is a Google Cloud feature.** The `@dataform/core` package is open source and
the CLI runs anywhere Node.js runs, but the managed UI, workspace registration, and the built-in
scheduler are Cloud-only.

### The anatomy of a project

Dataform core 3.0.0 and later produce this structure:

```
my-project/
│
├── workflow_settings.yaml   ← the project config (project ID, dataset, location, vars)
├── package.json             ← npm manifest; pins @dataform/core, holds package deps
├── .gitignore               ← excludes .dataform/, node_modules/, .df-credentials.json
│
├── definitions/             ← your SQLX and JavaScript assets live here
│   ├── stg_orders.sqlx
│   ├── fct_orders.sqlx
│   ├── assertions.sqlx
│   └── sources.sqlx         ← data source declarations
│
├── includes/                ← reusable JS constants and functions, global to the repo
│   └── constants.js
│
└── .dataform/               ← COMPILED OUTPUT (git-ignored, regenerate freely)
    ├── run.json             ← the compiled graph: actions, dependencies
    ├── run.sql              ← the compiled SQL BigQuery executes
    ├── metadata.json        ← table metadata (descriptions, columns, labels)
    └── schema.json          ← inferred/asserted schemas per action
```

| Path | Purpose | Edit it? |
|------|---------|----------|
| `definitions/` | The assets. SQLX and JavaScript files. | **Yes — this is your code.** |
| `includes/` | Reusable JS constants and functions, repo-wide. | Yes |
| `.dataform/` | Compiler output. | **No — never edit, never commit.** |
| `workflow_settings.yaml` | Project-wide config. | Yes |
| `package.json` | npm manifest; pins `@dataform/core`, holds package deps. | Rarely |

⚠️ **Never commit `.dataform/`.** It is derived, it is large, and it produces noisy diffs. The
default `.gitignore` handles it — but if you see it staged, something is wrong.

### `workflow_settings.yaml` — the project config

This is the file that decides where your tables land. A fully annotated version:

```yaml
# The desired Dataform core version to compile against.
dataformCoreVersion: 3.0.0

# Required. The default Google Cloud project (database).
defaultProject: my-gcp-project

# Required. The default dataset (schema).
defaultDataset: analytics

# Required. The default BigQuery location.
defaultLocation: US

# Required. The default dataset (schema) for assertions.
defaultAssertionDataset: analytics_assertions

# Optional. Variables available to project code during compilation.
vars:
  startDate: '2024-01-01'
  endDate: '2024-12-31'
  minOrderValue: '50.0'
  sourceProject: raw-data-project
  sourceDataset: raw

# Optional. Suffix appended to all Google Cloud project references.
projectSuffix: ''

# Optional. Suffix appended to all dataset references.
datasetSuffix: ''

# Optional. Prefix appended to all action names.
namePrefix: ''
```

Field by field:

| Field | Type | Meaning |
|-------|------|---------|
| `dataformCoreVersion` | string | The Dataform core version to compile against. When set, `@dataform/core` installs automatically at runtime — you do not need `dataform install`. |
| `defaultProject` | string | **Required.** The Google Cloud project (database) that owns the output. |
| `defaultDataset` | string | **Required.** The BigQuery dataset (schema) the actions write to. |
| `defaultLocation` | string | **Required.** The BigQuery location — `US`, `EU`, `US-CENTRAL1`, etc. |
| `defaultAssertionDataset` | string | **Required.** The dataset where assertion tables are written. |
| `vars` | map | Compile-time variables, read via `dataform.projectConfig.vars.<name>`. |
| `projectSuffix` | string | Suffix appended to every project reference. Useful for environment isolation. |
| `datasetSuffix` | string | Suffix appended to every dataset reference. |
| `namePrefix` | string | Prefix appended to every action name. |

💡 **`projectSuffix` and `datasetSuffix` are the isolation mechanism.** Set
`datasetSuffix: _dev` and every action lands in `analytics_dev` instead of `analytics`. That
lets a development workspace and a production workspace compile from the same code without
colliding — the "isolated development environment" pattern.

⚠️ **`vars` values are strings in the YAML file.** `minOrderValue: '50.0'` is a string, not a
number. Quote any value that could be parsed as a number or boolean, or it will be coerced.

### `vars` — compile-time constants

`vars` are **not** BigQuery variables, not runtime parameters, not environment variables. They
are substituted into your code at compile time.

Read them in SQLX with `dataform.projectConfig.vars`:

```sqlx
config { type: "view" }

SELECT *
FROM ${ref("stg_orders")}
WHERE order_date BETWEEN '${dataform.projectConfig.vars.startDate}'
                    AND '${dataform.projectConfig.vars.endDate}'
```

You can also override them at compile time without editing the file:

```bash
dataform compile --vars '{"startDate": "2025-01-01"}'
```

💡 **Use `vars` for things that change between environments** — dataset names, date windows,
feature flags. Do **not** use them to pass secrets; there is no secret store here, and this file
is committed to git.

### `definitions/` — where assets live

Dataform discovers assets by walking the `definitions/` directory. The **filename becomes the
action name**, with the extension stripped:

```
definitions/stg_orders.sqlx   →  action name: stg_orders
definitions/sources.sqlx      →  action name: sources
```

Subdirectories are conventional — `stg/`, `int/`, `marts/` are the community-standard layering
and make file organization obvious. But Dataform itself does not care about folder names; only
the filename matters.

### Data source declarations

A **declaration** tells Dataform about a table that already exists and that Dataform does not
create. There is no special `sources/` folder — a declaration is just another file in
`definitions/`.

```sqlx
// definitions/sources.sqlx

config {
  type: "declaration",
  database: "source-project",
  schema: "raw",
  name: "orders"
}
```

You declare one source per SQLX file. Then reference it like any other action:

```sqlx
// definitions/stg_orders.sqlx

config { type: "table" }

SELECT *
FROM ${ref("orders")}
```

💡 **A declaration is a dependency target, not a build step.** Dataform knows `orders` lives in
`source-project.raw` and will not try to create it. But because it is a real action in the
graph, `ref("orders")` creates a DAG edge exactly like a table reference does.

For multiple declarations in one file, use JavaScript:

```javascript
// definitions/declarations.js

declare({
  database: "source-project",
  schema: "raw",
  name: "orders",
});
declare({
  database: "source-project",
  schema: "raw",
  name: "customers",
});
```

### The compiled output directory

Compilation writes a self-contained bundle into `.dataform/`:

```
.dataform/
├── run.json          ← the compiled graph
├── run.sql           ← compiled SQL
├── metadata.json     ← table metadata (descriptions, columns, labels)
├── schema.json       ← inferred / asserted schemas
└── README.md         ← generated docs
```

`run.json` is the one you will inspect most — it is the machine-readable execution plan:

```json
{
  "targets": [
    {
      "name": "stg_orders",
      "database": "my-gcp-project",
      "schema": "analytics",
      "type": "table",
      "relation": "my-gcp-project.analytics.stg_orders",
      "fileName": "definitions/stg_orders.sqlx"
    }
  ],
  "dag": {
    "stg_orders": { "relations": ["my-gcp-project.analytics.stg_orders"] },
    "fct_orders": {
      "relations": ["my-gcp-project.analytics.fct_orders"],
      "dependencies": [
        { "target": { "name": "stg_orders",
                      "relation": "my-gcp-project.analytics.stg_orders" } }
      ]
    }
  },
  "operations": [
    { "metadata": { "target": { "name": "fct_orders" } }, "hasOutput": true }
  ],
  "tests": [],
  "metadata": { "projectId": "my-gcp-project", "defaultDataset": "analytics" }
}
```

`targets` is the inventory of actions. `dag` maps each action to the relations it produces and
the actions it depends on. `operations` is the ordered list of things to do. `tests` holds the
test and assertion definitions.

### `package.json`

Minimal, and it exists for one reason: **pinning the compiler version**.

```json
{
  "name": "my-project",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "@dataform/core": "3.0.0"
  },
  "scripts": {
    "compile": "dataform compile",
    "test": "dataform test"
  }
}
```

💡 **Pin `@dataform/core` exactly, not with a caret.** A caret lets a fresh `npm install` pull a
newer compiler and change your compiled SQL without any commit on your side. Exact pinning makes
your builds reproducible.

If you set `dataformCoreVersion` in `workflow_settings.yaml`, Dataform installs
`@dataform/core` automatically at runtime and you can skip `dataform install` entirely.

### `.gitignore`

```gitignore
.dataform/
node_modules/
.df-credentials.json
```

### `dataform init` and its flags

`dataform init` generates a project in a new directory:

```bash
dataform init my-project \
  --default-database my-gcp-project \
  --default-location US
```

| Flag | Meaning |
|------|---------|
| `PROJECT_NAME` (positional) | Directory to create the project in. |
| `--default-database` | The GCP project that will own the output. |
| `--default-location` | The BigQuery location. Default `US`. |
| `--service-account` | Service account for the Dataform service agent. |

To initialize in place, run `dataform init .` inside an existing project directory.

💡 **Use `init`, not `create`, for local development.** `init` is offline and instant. The
Cloud-side workspace creation happens in the Dataform console or the API.

### Compilation flags

| Flag | Purpose |
|------|---------|
| `--nodes` | Comma-separated action names to compile. Dependencies are pulled in automatically. |
| `--vars` | JSON object of var overrides, merged over `workflow_settings.yaml`. |
| `--project-dir` | Directory containing `definitions/`. |
| `--actions` | Which action types to compile: `build`, `run`, `test`. |
| `--dry-run` | Compile and print the actions without executing. |
| `--json` | Output directory for the compiled bundle. Default `.dataform`. |

```bash
dataform compile
dataform compile --nodes fct_orders
dataform compile --vars '{"startDate": "2025-01-01"}'
dataform compile --project-dir definitions
```

### Local development: `dataform core` and the BigQuery emulator

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
```

⚠️ **The emulator is not BigQuery.** It implements enough of the API for Dataform's tests, but
not every function, DDL statement, or BigQuery-specific feature. Treat emulator passes as a fast
first gate, never as proof.

💡 **Compilation is hermetic.** Dataform compiles your code in a sandbox with no internet
access — no external API calls, no network. That is a guarantee, not a limitation: the same code
always compiles to the same SQL, which is what makes compilation results reproducible.

### `dataform run`

`dataform run` compiles and then **executes** the resulting SQL against BigQuery.

```bash
# Run everything
dataform run

# Run one action and everything it depends on
dataform run --nodes fct_orders

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
| `--nodes` | Restrict to these actions (plus dependencies). |
| `--vars` | Var overrides for this execution. |
| `--include-dependents` | Include downstream actions of the selected nodes. |
| `--full-refresh` | For incremental tables, force a complete rebuild. |

💡 **The local dev loop is three commands:** `dataform compile` (catch errors, ~2s, free) →
`dataform run --dry-run` (see exactly what will execute) → `dataform run` (execute).

---

## 🛠️ Hands-On: Build Your First Project

### Step 1 — Install and authenticate

```bash
npm install -g @dataform/cli
dataform --version

# Create the credentials file (writes .df-credentials.json)
dataform init-creds
```

### Step 2 — Create the project

```bash
dataform init my-project \
  --default-database my-gcp-project \
  --default-location US

cd my-project
```

```bash
# Add the credentials file to .gitignore — do this first
echo ".df-credentials.json" >> .gitignore
```

### Step 3 — Inspect the generated structure

```bash
ls -la
#   definitions/  includes/  workflow_settings.yaml  package.json  .gitignore
```

### Step 4 — Write `workflow_settings.yaml`

```yaml
dataformCoreVersion: 3.0.0
defaultProject: my-gcp-project
defaultDataset: analytics
defaultLocation: US
defaultAssertionDataset: analytics_assertions

vars:
  startDate: '2024-01-01'
  endDate: '2024-12-31'
  minOrderValue: '50.0'
  sourceProject: raw-data-project
  sourceDataset: raw
```

### Step 5 — Declare the source

`definitions/sources.sqlx`:

```sqlx
config {
  type: "declaration",
  database: "source-project",
  schema: "raw",
  name: "orders"
}
```

### Step 6 — Write a model

`definitions/stg_orders.sqlx`:

```sqlx
config {
  type: "table",
  description: "Staged orders, one row per order, deduplicated",
  tags: ["daily"]
}

SELECT order_id, customer_id, order_date, total_amount, _loaded_at
FROM ${ref("orders")}
WHERE order_date BETWEEN '${dataform.projectConfig.vars.startDate}'
                    AND '${dataform.projectConfig.vars.endDate}'
  AND total_amount >= ${dataform.projectConfig.vars.minOrderValue}
QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY _loaded_at DESC) = 1
```

### Step 7 — Compile and inspect

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

### Step 8 — Override vars without editing files

```bash
dataform compile --vars '{"startDate": "2025-06-01", "endDate": "2025-06-30"}'
grep -c "2025-06-01" .dataform/run.sql   # confirm the override reached the SQL
```

### Step 9 — Dry run, then run

```bash
dataform run --dry-run              # see what would happen — no query executes
dataform run --nodes stg_orders     # actually run it

# Verify in BigQuery
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `my-gcp-project.analytics.stg_orders`'
```

### Step 10 — Wire it into CI

```yaml
# .github/workflows/dataform.yml
name: dataform
on: { push: { branches: [main] } }
jobs:
  compile:
    runs-on: ubuntu-latest
    permissions: { contents: read, id-token: write }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm install -g @dataform/cli
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}
      - name: Compile
        run: dataform compile
```

💡 **Use Workload Identity Federation, not a service account key.** The key never exists in the
repo, and the same pattern works in Cloud Build.

---

## 🔑 Key Takeaways

- Setup is three separable things: the CLI, the credentials file, and the project directory.
- `.df-credentials.json` holds access credentials — **never commit it**.
- Dataform Cloud vs self-hosted is a decision about orchestration and UI, not about SQLX. The compiled output is identical.
- The project has four moving parts: `workflow_settings.yaml` (config), `definitions/` (your assets), `includes/` (reusable JS), `.dataform/` (generated output — never commit it).
- `workflow_settings.yaml` requires `defaultProject`, `defaultDataset`, `defaultLocation`, and `defaultAssertionDataset`. `vars` and the three suffix/prefix options are optional.
- `projectSuffix` / `datasetSuffix` are how you isolate dev from prod while compiling the same code.
- Declarations live in `definitions/` like any other file — there is no special `sources/` folder. `type: "declaration"` marks them.
- A declaration is a dependency target, not a build step. `ref()` on one creates a normal DAG edge.
- `dataformCoreVersion` in `workflow_settings.yaml` makes `@dataform/core` install automatically at runtime.
- Compilation is **hermetic** — sandboxed, no network, same code always compiles to the same SQL.
- `dataform core` is a local compiler server; the BigQuery emulator is a local test target — but it is *not* BigQuery.
- The local loop is `compile` → `run --dry-run` → `run`. Compile is free and catches most errors.
- `dataform run --nodes <action>` rebuilds one action and its upstream dependencies; `--full-refresh` overrides incremental logic.

---

## 📚 Practice Exercises

1. **Workspace teardown and rebuild.** Create a project with `dataform init`, delete `.dataform/` entirely, and rebuild with `dataform compile`. Confirm the `run.json` is identical. Explain why committing `.dataform/` is a mistake in terms of diff noise, merge conflicts, and trust.

2. **`workflow_settings.yaml` archaeology.** Write a settings file for a project where actions live in `analytics`, assertions live in `analytics_assertions`, a `datasetSuffix` of `_dev` isolates development, and vars set a date window and a source project. Prove it works by compiling with `--vars` overrides and grepping the compiled SQL. Then explain what changes in the compiled output when you flip `datasetSuffix` from `_dev` to empty.

3. **Deployment model decision memo.** Write a one-page comparison of Dataform Cloud vs Cloud Composer orchestration for a team of 12 data engineers. Cover: build history visibility, debugging a failed 3am run, branching strategy, cost at 100 actions and 500 daily runs, and lock-in. Recommend one, and name the condition under which you would switch.

4. **Local loop under failure.** Add an asset that references a non-existent action via `ref("does_not_exist")`. Run `dataform compile` and record the exact error. Then run `dataform run --dry-run` and record the difference. Finally, fix it and show the working compile. Explain why the compile-time check is more valuable than the run-time failure.

5. **Hermetic compilation audit.** Read the Dataform core reference on hermeticity, then find a place in your project where you read a table that is not declared via `ref()` or a declaration. Rewrite it as a declaration plus a `ref()`, and explain what the compiler can now enforce that it could not before.

---

## 📖 Further Reading

- Dataform overview — https://cloud.google.com/dataform/docs/overview
- Dataform core reference — https://cloud.google.com/dataform/docs/reference/dataform-core-reference
- Using the Dataform CLI — https://cloud.google.com/dataform/docs/use-dataform-cli
- Create a development workspace — https://cloud.google.com/dataform/docs/create-workspace
- Configure compilation — https://cloud.google.com/dataform/docs/configure-compilation
- Declare data sources — https://cloud.google.com/dataform/docs/declare-source
- Declare dependencies — https://cloud.google.com/dataform/docs/dependencies
- Dataform open source (dataform-co/dataform) — https://github.com/dataform-co/dataform
- BigQuery emulator — https://cloud.google.com/bigquery/docs/emulator
