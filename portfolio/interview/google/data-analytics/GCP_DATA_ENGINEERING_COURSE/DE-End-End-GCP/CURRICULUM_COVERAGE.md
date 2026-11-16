# Curriculum Coverage — 11-Item GCP Data Engineer Track

> **Status:** verified 2026-11-15 by direct inspection of every file in this
> directory. This is a gap analysis, not a rewrite of the course.
>
> **Scope:** maps the 11-item target curriculum onto the assets that exist in
> `DE-End-End-GCP/`. It answers one question per item: *can you point an
> interviewer at a file that proves you did this?*

---

## How to read the verdicts

| Verdict | Meaning |
|---|---|
| **BUILT** | A runnable artifact exists — commands, notebooks, DAGs, or app code. An interviewer can open the file. |
| **PARTIAL** | The concept is present but the evidence is thin, GUI-driven, or missing a key piece. |
| **GAP** | Nothing exists at the artifact level. |

**Never claim more than the verdict.** `PARTIAL` on an item means the
interviewer can see the shape but not the build.

---

## The summary table

| # | Curriculum item | Verdict | Primary evidence | Gap severity |
|---|---|---|---|---|
| 1 | Setup Environment on Windows and Mac using VS Code | **BUILT** | `03 Setup Local Environment using VS Code.md`, `tools/check_environment.py` | Low ✅ *was PARTIAL* |
| 2 | Build Data Lake using Google Cloud Storage | **BUILT** | `02 Setting up Data Lake using GCS.md`, 4 notebooks, `data/retail_db*` | Low |
| 3 | Cloud SQL Database and GCP Secrets | **BUILT** | `04 Setup Postgres…md`, 3 notebooks incl. Secret Manager, `data/retail_db/*.sql` | Low |
| 4 | Build Data Warehouse using Google BigQuery | **BUILT** | `05 Data Warehouse using Google Big Query.md`, 3 notebooks, 4 SQL scripts | Low |
| 5 | Big Data Processing using GCP Dataproc | **BUILT** | `07 …Dataproc.md`, `notebooks/07 …/Notes.md` | Low |
| 6 | ELT Pipelines using Dataproc Jobs and Workflows | **BUILT** | `notebooks/08 …/Managing Dataproc Workflows using gcloud.ipynb` (33 cells), `apps/airflow_dags/daily_product_revenue_jobs.py` | Low–Med (no `.md` chapter) |
| 7 | Big Data Processing using Databricks on GCP | **BUILT** | `08 …Databricks on GCP.md` (now +cluster +UC), `notebooks/09 …` | Low ✅ *was PARTIAL* |
| 8 | ELT Pipelines using Databricks Jobs and Workflows | **BUILT** | `notebooks/10 …/ELT Data Pipeline for Daily Product Revenue.dbc` (20 KB), `apps/databricks_jobs/daily_product_revenue_job.json` | Low–Med ✅ *was PARTIAL* |
| 9 | Integration of Spark on Dataproc and BigQuery | **BUILT** | `09 Integration of Dataproc and Google BigQuery.md` (connector JARs + `format('bigquery')`), 4 notebooks | Low |
| 10 | Add PySpark Application with BigQuery Connector to the Pipeline | **BUILT** | `notebooks/11 …/10 Data Pipeline using Spark on Dataproc and BigQuery.ipynb` | Low–Med |
| 11 | ELT Pipelines using GCP Cloud Composer (Airflow) | **BUILT** | `12 …Cloud Composer.md`, 5 DAGs in `apps/airflow_dags/` | Low–Med (no `.md` chapter for 03) |

**Verdict: 11 BUILT, 0 PARTIAL** (was 8 BUILT / 3 PARTIAL). The three gaps
that mattered — the VS Code setup and the two Databricks items — are now
closed. The remaining "Low–Med" notes are narrative gaps, not evidence
gaps: items 6, 8 and 11 are fully built but their `.md` chapters do not
tell the story of what was built.

---

## Item-by-item detail

### Item 1 — Setup Environment on Windows and Mac using VS Code · **PARTIAL**

**What exists**
- `01 Getting Started with Data Engineering on GCP.md` — prerequisites,
  GCP signup, and SDK setup via `gcloud init` / `gsutil list`. Nothing on
  VS Code, nothing OS-specific.
- `07 Big Data Processing using Google Dataproc.md:51-56` — four bullets on
  "Remote Development using VS Code on Dataproc" (cluster + static IP,
  Remote Development Extension Pack, remote connection, clone repo).
- The curriculum's own CURRICULUM.md lists "Setup Remote Development
  Environment using VS Code" under the Dataproc module — so VS Code was
  always a *Dataproc remote-dev* topic, never a local-environment topic.

**What is missing**
- Local VS Code install and setup for **both** Windows and Mac.
- Recommended extension list (Python, Pylance, Jupyter, Cloud Code, GitLens).
- Workspace layout — what folders the learner opens, and why.
- The **venv activation split**: `source .venv/bin/activate` (macOS zsh) vs
  `.venv\Scripts\Activate.ps1` (Windows PowerShell). This is the single most
  common first-hour failure for a Windows learner and it appears nowhere.
- `gcloud` on PATH inside the VS Code integrated terminal, and the
  PowerShell execution-policy problem that blocks it.
- Line-ending / `PYTHONPATH` / `.env` differences between the two OSes.
- There is no `.vscode/` directory, no `settings.json` / `tasks.json` /
  `launch.json`, and no devcontainer in this course.

**Severity: High.** This is item 1 of the curriculum — the first thing a
reader hits — and it currently teaches `gcloud init` while claiming to be
"Getting Started". The VS Code content that does exist is 4 bullets for
remote development, which is a different skill.

---

### Item 2 — Build Data Lake using Google Cloud Storage · **BUILT**

`02 Setting up Data Lake using GCS.md` (112 lines) covers bucket setup, the
GCS web UI, `gsutil`, dataset management, and the Python/ Pandas paths.

**Notebooks:** `08 Manage Files in GCS using Python.ipynb`,
`09 Project to Upload Files to GCS using Python.ipynb`,
`10 Overview of processing data in GCS using Pandas.ipynb`,
`11 Project to Upload Files to GCS using Pandas.ipynb`.

**Datasets present:** `data/retail_db` (CSV + JSON + header variants),
`data/hr_db`, `data/nyse`, `data/nyse_all`, `data/lca`,
`data/electionresults`, `data/cards`. This is enough to build a real
multi-zone lake.

**Minor gap:** no `archive` tier in the bucket layout, and the commands use
legacy `gsutil` rather than `gcloud storage` (see *Cross-cutting findings*).

---

### Item 3 — Cloud SQL Database and GCP Secrets · **BUILT**

`04 Setup Postgres Database using GCP Cloud SQL.md` (183 lines) — the
strongest chapter in the original corpus. Covers Cloud SQL overview, network
configuration, local PostgreSQL install, `psql` CLI, pgAdmin, database
creation, and table setup + data load.

**Secrets are genuinely covered**, which is better than the refactored
course (whose chapter set has no Secret Manager material at all):
- `04 …md:139-170` — create secret, access via CLI, and a Python SDK snippet
  using `secretmanager.SecretManagerServiceClient()` and
  `access_secret_version`, explicitly framed as replacing a hardcoded password.
- `notebooks/04 …/10 Manage Database Credentials using GCP Secret Manager.ipynb`

**Datasets:** `data/hr/hr_mysql.sql`, `data/retail_db/create_db_tables_pg.sql`,
`data/retail_db/load_db_tables_pg.sql`.

**Minor gap:** chapter 03 of the original course ("Getting Started with GCP
Secrets Manager") exists **only** as curriculum bullets in `CURRICULUM.md` —
no `.md`, no notebook dir. Its content is folded into chapter 04.

---

### Item 4 — Build Data Warehouse using Google BigQuery · **BUILT**

`05 Data Warehouse using Google Big Query.md` (285 lines) — the largest
chapter. Public datasets, retail database setup, table load, daily product
revenue, dimensions and facts, cumulative aggregations and ranking.

**Notebooks:** `05 Load Data into an Empty Table in Google BigQuery.ipynb`,
`15 Python Pandas Integration with Google BigQuery.ipynb`,
`16 Integration of BigQuery with Cloud SQL.ipynb`.

**Scripts:** `02 CRUD Operations…sql`, `11 Basic SQL Queries…sql`,
`12 Cumulative Aggregations…sql`, `13 Ranking…sql`,
`16 Integration of BigQuery with Cloud SQL.sql`.

**Minor gap:** no partitioning or clustering as a taught topic here — the
refactored `chapters/13-…` and `14-…` cover those better.

---

### Item 5 — Big Data Processing using GCP Dataproc · **BUILT**

`07 Big Data Processing using Google Dataproc.md` (272 lines) — single-node
Hadoop/Spark cluster, remote development, dataset review, Spark SQL and
PySpark execution, Spark UI review.

`notebooks/07 Big Data Processing using Google Dataproc/Notes.md` is a
placeholder — no notebook in this directory. This is the one chapter whose
notebook dir is empty.

---

### Item 6 — ELT Pipelines using Dataproc Jobs and Workflows · **BUILT**

This is the item most at risk of being assumed missing — it is **not**.
There is no `.md` chapter numbered 10, but the artifacts are complete:

- `notebooks/08 ELT Data Pipelines using Dataproc on GCP/Managing Dataproc Workflows using gcloud.ipynb` — **33 cells**, the workflow-template build.
- `notebooks/08 …/Run and Validate ELT Data Pipeline using Dataproc.ipynb` — 15 cells.
- `apps/airflow_dags/daily_product_revenue_jobs.py` — a real Airflow DAG
  using `DataprocSubmitSparkSqlJobOperator` and
  `DataprocSubmitPySparkJobOperator`, with task dependencies.
- `apps/airflow_dags/daily_product_revenue_wf.py` and
  `daily_product_revenue_vars_wf.py` — DAGs using
  `DataprocInstantiateWorkflowTemplateOperator` against the workflow
  template `wf-daily-product-revenue-bq`.
- `scripts/daily_product_revenue/` — `cleanup.sql`, `file_format_converter.sql`,
  `compute_daily_product_revenue.sql`, `unittest.sql`.

**Gap:** no `.md` chapter, so the *narrative* (why a workflow template beats
four chained operators, when to use the Workflows API vs the Airflow
operator) is never told. The interview answer has to supply it verbally.

---

### Item 7 — Big Data Processing using Databricks on GCP · **PARTIAL**

`08 Big Data Processing using Databricks on GCP.md` (168 lines) — signing up
via GCP Marketplace, workspace creation, overview, Databricks CLI, DBFS
limitations, copying retail data to DBFS, Spark SQL and PySpark examples,
workflows, Spark UI troubleshooting.

**Notebook:** `notebooks/09 …/06 Copy Data Sets to DBFS using gsutil Commands.ipynb`.

**What is missing**
- **No cluster creation.** The chapter never shows creating a Databricks
  cluster, node types, or runtime version. "Big Data Processing using
  Databricks" without a cluster is the weakest part of this item.
- **No Unity Catalog** — zero mentions in the corpus.
- **No Databricks-vs-Dataproc argument.** The item is explicitly paired
  with items 5–6, so the comparison is the point. It is nowhere made.
- The chapter says "A dbc archive will be provided under the notebooks
  repository" — it *is* provided (see item 8), so this line resolves, but
  the chapter never tells the reader where.
- The `databricks fs` CLI limitation on GCP is stated but never worked around.

**Severity: High.** This is one half of the deliberate Dataproc-vs-Databricks
pairing that makes items 5–8 worth building. Half the argument is missing.

---

### Item 8 — ELT Pipelines using Databricks Jobs and Workflows · **PARTIAL**

**What exists**
- `notebooks/10 ELT Data Pipelines using Databricks on GCP/ELT Data Pipeline for Daily Product Revenue.dbc` — a **20 KB** Databricks archive containing the modularised
  notebooks (file-format converter for orders and order_items, daily product
  revenue, validator). This is the real build.
- `notebooks/10 …/06 Copy Data Sets to DBFS using gsutil Commands.ipynb`.
- Chapter prose for workflows, task dependencies, task-level vs job-level
  parameters, per-task clusters, run modes (Run now / with parameters /
  schedule), and Spark UI troubleshooting.

**What is missing**
- **GUI-only.** Task creation is described as click-instructions
  (`08 …md:144-150`). There is **no exportable job definition** — no Jobs
  API 2.2 JSON, no `databricks jobs create`, no YAML bundle, no Terraform.
  An interviewer cannot see a definition.
- **`dbutils.notebook.task.reparameterize` is never mentioned** — and the
  chapter claims task-level and job-level parameter passing without ever
  showing a parameter read. The `.dbc` may contain it; the teaching never
  does.

  > **Correction (2026-11-15):** `dbutils.notebook.task.reparameterize`
  > is **not a real Databricks API**. The correct one is
  > `dbutils.jobs.taskValues` (`.set(key=, value=)` and
  > `.get(taskKey=, key=, default=, debugValue=)`, Python-only). Chapter 08
  > now teaches the real API. This matters for the interview — citing the
  > non-existent one is an immediate wrong answer.
- **Delta Live Tables / Lakeflow: zero mentions.**
- **No comparison against Composer.** Item 8 is item 11's mirror; the
  corpus never puts them side by side.

  > **Closed 2026-11-15:** `13 Choosing between Dataproc, Databricks and
  > Composer.md` now makes that comparison explicitly, and
  > `apps/databricks_jobs/daily_product_revenue_job.json` exports the Job
  > definition as reviewable JSON.

**Severity: High.** The `.dbc` is a strong artifact, but "build the pipeline
on Databricks Jobs *versus* Airflow" is the interview question this
curriculum is built to answer, and only the Databricks side is teachable
from these files.

---

### Item 9 — Integration of Spark on GCP Dataproc and Google BigQuery · **BUILT**

`09 Integration of Dataproc and Google BigQuery.md` (207 lines) covers the
BigQuery Spark connector properly:

- `29` — `pyspark --jars gs://spark-lib/bigquery/spark-bigquery-with-dependencies_2.12-0.26.0.jar`
- `39`, `85` — `format('bigquery')` reads and writes in Spark SQL
- `118`, `128`, `149`, `178` — the `--jars` flag wired into `gcloud dataproc jobs submit pyspark`
- `161` — the JAR path stated as the reference
- Python client integration via `google.cloud.bigquery`

**Notebooks:** `03 Validate Google BigQuery Integration with Python on Dataproc.ipynb`,
`04 Validate Google BigQuery Integration with Pyspark.ipynb`,
`07 Develop Logic to Save Result to BigQuery Table.ipynb`,
`10 Data Pipeline using Spark on Dataproc and BigQuery.ipynb`.

**Gap:** the connector is pinned to `0.26.0` (2021-era). Fine for a course,
but if an interviewer asks about current versions, know it is dated.

---

### Item 10 — Add PySpark Application with BigQuery Connector to the Pipeline · **BUILT**

`notebooks/11 Integration of Dataproc and Google BigQuery/10 Data Pipeline using Spark on Dataproc and BigQuery.ipynb`
is the end-to-end PySpark → BigQuery pipeline, and
`07 Develop Logic to Save Result to BigQuery Table.ipynb` is the
save-to-table logic.

**Gap:** the notebook is the pipeline, but nothing in the `.md` files
narrates it. Item 10 is an *additive* step in the curriculum — the pipeline
already existed, and the connector was added to it. That framing is lost.

---

### Item 11 — Build ELT Pipelines using GCP Cloud Composer (Airflow) · **BUILT**

`12 Data Pipeline Orchestration using Google Cloud Composer.md` (129 lines).

**DAGs in `apps/airflow_dags/`** — five real, importable Airflow DAGs:

| File | What it demonstrates |
|---|---|
| `daily_product_revenue_jobs.py` | `DataprocSubmitSparkSqlJobOperator` + `DataprocSubmitPySparkJobOperator`, task dependencies, Airflow `Variable` lookup |
| `daily_product_revenue_wf.py` | `DataprocInstantiateWorkflowTemplateOperator` → `wf-daily-product-revenue-bq` |
| `daily_product_revenue_vars_wf.py` | Same, with parameters sourced from Airflow Variables |
| `spark_sql_demo.py` | Minimal Spark SQL job operator |
| `tutorial_dag.py` | `BashOperator` with `t1 >> t2` |

**Gap:** no `.md` chapter for curriculum item 03 ("Getting Started with GCP
Secrets Manager") — but more importantly, the Composer chapter is the
shortest of the orchestration material and never explicitly compares
Composer to Dataproc Workflows (items 6 vs 11) or to Databricks Jobs
(item 8).

---

## Cross-cutting findings

These affect several items at once and are worth fixing before item-level work.

### 1. Chapter numbering has three gaps — `01, 02, 04, 05, 06, 07, 08, 09, 12`

The original course's module numbers are `01, 02, 04, 05, 06, 07, 08, 09, 12`.
**03, 10, 11 have no `.md` chapter**, yet all three have notebook/script
directories:

| Missing chapter | Orphaned assets |
|---|---|
| 03 — Getting Started with GCP Secrets Manager | content folded into ch04; `notebooks/04 …/10 Manage Database Credentials using GCP Secret Manager.ipynb` |
| 10 — ELT Data Pipelines using Dataproc on GCP | `notebooks/08 ELT Data Pipelines using Dataproc on GCP/` (2 notebooks, 48 cells) |
| 11 — ELT Data Pipelines using Databricks on GCP | `notebooks/10 ELT Data Pipelines using Databricks on GCP/` (notebook + 20 KB `.dbc`) |

Items 6, 8, and 11 are all "BUILT" *because of notebooks*, not because of
chapters. A reader working strictly top-to-bottom through the `.md` files
never reaches them.

### 2. Legacy `gsutil` throughout, while the refactored course teaches `gcloud storage`

Every storage command here uses `gsutil` (`gsutil mb`, `gsutil cp`,
`gsutil ls`). The refactored `chapters/06-cloud-storage.md` deliberately
teaches `gcloud storage buckets create` and calls the `gsutil` style
legacy. A learner moving between the two corpora hits a contradiction.

**Recommendation:** keep `gsutil` in the original course (it is historically
accurate and the commands still work), but add a one-line note in
`CURRICULUM.md` or a README explaining that `gcloud storage` is the
current form and where the refactored course teaches it.

### 3. No onboarding scaffolding in this directory

`DE-End-End-GCP/` has **no README, no SETUP, no `.vscode/`, no
requirements pinning, no test harness**. The refactored course has all of
these (`README.md`, `resources/SETUP.md`, 102 passing tests).

### 4. Hardcoded project IDs in the DAGs

- `daily_product_revenue_wf.py:10` — `project_id = "tidy-fort-361710"`
- `spark_sql_demo.py:7` — `project_id = "itversity-rnd"`
- `spark_sql_demo.py:22,24` — `project_id='itversity-rnd'`, `cluster_name='aidataprocdev'`

`daily_product_revenue_jobs.py` and `daily_product_revenue_vars_wf.py` do it
correctly via `Variable.get('project_id')`. Two of five DAGs are clean;
three leak the instructor's project IDs.

### 5. Git state

All files in this directory are **staged but not committed** (git status
shows `A` for every file). The mtimes are Oct 2022 but the files entered
the working tree on 2026-11-15.

---

## Priority order for closing gaps

Ranked by interview value per unit of effort.

| Priority | Work | Item | Effort | Status |
|---|---|---|---|---|
| **1** | Write the VS Code setup guide: Windows + Mac, venv split, extensions, `gcloud` in the integrated terminal | 1 | Medium | ✅ **Done** — `03 Setup Local Environment using VS Code.md` + `tools/check_environment.py` |
| **2** | Add a Databricks-vs-Dataproc comparison chapter (storage, orchestration, cost, when to pick which) | 7, 8, 11 | Medium | ✅ **Done** — `13 Choosing between Dataproc, Databricks and Composer.md` |
| **3** | Show Databricks cluster creation + Unity Catalog in ch08 | 7 | Small | ✅ **Done** — cluster table, SA roles, lifecycle, Unity Catalog setup added to ch08 |
| **4** | Write the three missing `.md` chapters (03 Secrets, 10 Dataproc ELT, 11 Databricks ELT) | 6, 8 | Medium | 🟡 Partly done — item 1's chapter added as `03`; 10 and 11 still open |
| **5** | Export a Databricks job definition (Jobs API 2.2 JSON) for the daily-product-revenue workflow | 8 | Small | ✅ **Done** — `apps/databricks_jobs/daily_product_revenue_job.json`, 6 tasks, verified against the `.dbc` |
| **6** | Parameterise the hardcoded project IDs in the three DAGs | 11 | Trivial | ✅ **Done** — `daily_product_revenue_wf.py`, `spark_sql_demo.py` now use `Variable.get()` |
| **7** | Add a `README.md` + `SETUP.md` to this directory | All | Small | ✅ **Done** — `README.md` (chapter map, dataset inventory, cost controls, troubleshooting, per-module prerequisites). A separate `SETUP.md` is still open; the setup content lives in chapter 03 |
| **8** | Add `dbutils.jobs.taskValues` and a DLT/Lakeflow note | 8 | Small | 🟡 Partly done — `dbutils.jobs.taskValues` taught in ch08; DLT/Lakeflow still open |

**Highest value per effort: #1, #3, #6.** #1 fixes the weakest item in the
curriculum; #3 is a handful of commands in an existing chapter; #6 is three
lines and removes a leak of the instructor's project IDs from a portfolio
artifact.

**Highest value overall: #2.** Items 5–6 and 7–8 are a deliberate mirror
pairing. The interview payoff is the *argument* between the two stacks, and
the corpus currently supports only one side of it.

---

## What has been added (2026-11-15)

| File | Purpose |
|---|---|
| `03 Setup Local Environment using VS Code.md` | Closes curriculum item 1. Windows/macOS split, venv activation per shell, PowerShell execution policy, extensions, workspace layout, `.vscode/settings.json` + `tasks.json`, troubleshooting table, and a runnable verification step. |
| `tools/check_environment.py` | Executable environment check backing the new chapter. Verifies Python version, virtualenv, dependencies, gcloud install/auth/project, repo layout, sample data. Exits non-zero with an actionable message per failure. |
| `13 Choosing between Dataproc, Databricks and Composer.md` | Closes the comparison gap across items 5–6, 7–8, 11. Two-axis framework (runtime ownership vs pipeline-metadata ownership), the three-way case study using this repo's own artifacts, a decision procedure, and a recommended stack. |
| `apps/databricks_jobs/daily_product_revenue_job.json` | Exportable Jobs API 2.2 definition for the daily-product-revenue workflow. 6 tasks, job-level parameters, job cluster with a GCP service account, `concurrency: 1`. Every notebook path verified against the `.dbc`. |
| `README.md` | Onboarding for this directory: prerequisites, the chapter map, the dataset inventory, how to run the pipeline on each of the three engines, per-module API prerequisites, cost controls, and troubleshooting. |
| `CURRICULUM_COVERAGE.md` | This document. |

---

## Cloud Shell — added 2026-11-16

Cloud Shell was the one platform tool with a **factual error** in the course
and no hands-on treatment in the build track. Both are now fixed.

### The error, corrected

`chapters/02-regions-zones-and-resource-hierarchy.md` claimed Cloud Shell
was "ephemeral (5 hours idle by default)". The official docs say otherwise:

| Claim | Course said | Official |
|---|---|---|
| Idle timeout | 5 hours | **40 minutes** — the VM terminates |
| Session cap | not stated | **12 hours** |
| Weekly quota | not stated | **50 hours** |
| Home directory | "5 GB, in the home region of your Cloud Shell configuration" | 5 GB at `$HOME`, per user, shared across projects; the VM region is assigned automatically and is **not** user-selectable |
| Home directory deletion | not stated | After **120 days** without access |

Corrected in chapter 02, and the corrected numbers are now stated in
`resources/CHEATSHEET.md` (§ Cloud Shell), `resources/SETUP.md`, and the
`DE-End-End-GCP` chapter 01 and README.

### What was added

| File | Change |
|---|---|
| `DE-End-End-GCP/01 Getting Started with Data Engineering on GCP.md` | A full **Alternative — Google Cloud Shell** section: when to use it, when *not* to, launching it, verifying the session, the persistent `$HOME`, the `$HOME/.customize_environment` boot script, ephemeral mode, files in/out, the editor and Web Preview, and the browser-authentication trap |
| `resources/SETUP.md` | A **"Or skip the install entirely — use Cloud Shell"** subsection under the CLI install step, so a learner without the SDK is not blocked |
| `resources/CHEATSHEET.md` | A **§ Cloud Shell** reference block — limits table, in-session commands, persistent customisation, ephemeral mode, the authentication trap |
| `DE-End-End-GCP/README.md` | The `gcloud` CLI requirement now points at Cloud Shell as the no-install alternative, with the two caveats stated inline |

**Why it matters for the interview:** Cloud Shell is a natural RRK answer to
"how do you work on GCP without putting credentials on a laptop" — and the
40-minute idle timeout is the kind of specific number that separates
someone who has actually used it from someone who has read the landing
page.

**Chapter 08 changes:** added a Databricks cluster creation section (cluster
type/runtime/node type table, dedicated service account with scoped IAM
roles, verification, job-cluster-vs-all-purpose lifecycle), a Unity Catalog
section (metastore on GCS, workspace assignment, what it buys over GCS
IAM), a task-parameters section teaching the real
`dbutils.jobs.taskValues` API, and a job-definition-as-code section with
the CLI commands and the task graph.

**DAG changes:** `apps/airflow_dags/daily_product_revenue_wf.py` and
`apps/airflow_dags/spark_sql_demo.py` no longer hardcode the instructor's
project IDs (`tidy-fort-361710`, `itversity-rnd`, `aidataprocdev`). Both now
read `project_id`, `region` and `cluster_name` from Airflow Variables, matching
the pattern already used in `daily_product_revenue_jobs.py`. All five DAGs
parse cleanly (verified with `ast.parse`).

**Chapter numbering note:** the new local-setup chapter was numbered `03`
because that slot was free — but the original curriculum's `03` was
"Getting Started with GCP Secrets Manager", whose content is folded into
chapter 04. Chapter `10` (Dataproc ELT) and `11` (Databricks ELT) remain
without a `.md` companion, and the numbering now has two distinct gaps. If
the chapters are renumbered into a continuous sequence, that will resolve
both.
