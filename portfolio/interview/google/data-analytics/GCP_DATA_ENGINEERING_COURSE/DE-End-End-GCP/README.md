# Data Engineering on GCP — End-to-End Course

A hands-on GCP data engineering course. Twelve chapters that build one
retail analytics platform, end to end: a GCS data lake, a Cloud SQL
operational database with secrets, a BigQuery warehouse, Spark on Dataproc,
Spark on Databricks, and the same daily-product-revenue pipeline
orchestrated three different ways.

Every module runs against real GCP services with real commands. The datasets
are in `data/`. The notebooks are in `notebooks/`. The deployable code is in
`apps/`.

---

## Before you start

You need:

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.9+ | `python3 --version` (Windows: `py -3 --version`) |
| A GCP project | with billing attached | Google Cloud has no free tier without one |
| `gcloud` CLI | current | [Install guide](https://cloud.google.com/sdk/docs/install) — **or skip it and use Cloud Shell** |
| VS Code | current | See [chapter 03](03%20Setup%20Local%20Environment%20using%20VS%20Code.md) |
| SQL | working knowledge | The course is query-heavy from chapter 5 onward |

> **No `gcloud` installed?** Use **Cloud Shell** — a browser terminal with
> `gcloud`, `kubectl`, `docker` and `git` already present, authenticated
> through your browser session. Open the console and click the **>_** icon,
> or go to <https://shell.cloud.google.com>. Every `gcloud` command in this
> course runs there unchanged.
>
> Two caveats: the VM is **discarded after 40 minutes of inactivity** (a
> session is capped at 12 hours), and your `$HOME` **persists** (5 GB), so
> cloned datasets survive between sessions. Full walkthrough in
> [chapter 01](01%20Getting%20Started%20with%20Data%20Engineering%20on%20GCP.md).

**Start here:** [03 Setup Local Environment using VS Code](03%20Setup%20Local%20Environment%20using%20VS%20Code.md)
— it covers Windows and Mac, the virtual environment split, and `gcloud`
in the integrated terminal.

Then verify your setup:

```shell
python tools/check_environment.py
```

It checks Python, the virtualenv, dependencies, `gcloud`, your default
project, and the data. Every failure comes with the fix. It resolves the
course root from its own location, so you can run it from anywhere.

---

## The chapter map

| # | Chapter | What you build | Evidence in this repo |
|---|---|---|---|
| 01 | [Getting Started with Data Engineering on GCP](01%20Getting%20Started%20with%20Data%20Engineering%20on%20GCP.md) | GCP account, project, SDK, and **Cloud Shell** as the no-install alternative | — |
| 02 | [Setting up Data Lake using GCS](02%20Setting%20up%20Data%20Lake%20using%20GCS.md) | The lake, bucket layout, file management | `notebooks/03 …/`, `data/retail_db*` |
| 03 | [Setup Local Environment using VS Code](03%20Setup%20Local%20Environment%20using%20VS%20Code.md) | Your local dev environment | `tools/check_environment.py` |
| 04 | [Setup Postgres Database using Cloud SQL](04%20Setup%20Postgres%20Database%20using%20GCP%20Cloud%20SQL.md) | Operational DB + Secret Manager | `notebooks/04 …/`, `data/retail_db/*.sql` |
| 05 | [Data Warehouse using Google BigQuery](05%20Data%20Warehouse%20using%20Google%20Big%20Query.md) | The warehouse, dims and facts | `notebooks/05 …/`, `scripts/05 …/` |
| 06 | [Data Processing using Google Cloud Functions](06%20Data%20Processing%20using%20Google%20Cloud%20Functions.md) | An event-driven file converter | `apps/cloud_function/`, `apps/file_format_converter/` |
| 07 | [Big Data Processing using Google Dataproc](07%20Big%20Data%20Processing%20using%20Google%20Dataproc.md) | Spark on Dataproc | `notebooks/07 …/` |
| 08 | [Big Data Processing using Databricks on GCP](08%20Big%20Data%20Processing%20using%20Databricks%20on%20GCP.md) | Spark on Databricks, cluster + UC | `notebooks/09 …/`, `notebooks/10 …/` |
| 09 | [Integration of Dataproc and Google BigQuery](09%20Integration%20of%20Dataproc%20and%20Google%20BigQuery.md) | Spark ↔ BigQuery connector | `notebooks/11 …/` |
| 10 | *ELT Pipelines using Dataproc* | The pipeline, as a workflow template | `notebooks/08 …/`, `scripts/daily_product_revenue/` |
| 11 | *ELT Pipelines using Databricks* | The pipeline, as a Databricks Job | `notebooks/10 …/`, `apps/databricks_jobs/` |
| 12 | [Data Pipeline Orchestration using Cloud Composer](12%20Data%20Pipeline%20Orchestration%20using%20Google%20Cloud%20Composer.md) | The pipeline, as an Airflow DAG | `apps/airflow_dags/` |
| 13 | [Choosing between Dataproc, Databricks and Composer](13 Choosing between Dataproc, Databricks and Composer.md) | The argument for which to pick | — |

Chapters 10 and 11 have no `.md` file yet — their material is in the
notebooks and scripts listed above.

> **Read chapter 13.** It is the payoff for the whole course: it compares
> the three implementations of the same pipeline and argues which one to
> ship.

---

## The three implementations

The course builds the **same daily product revenue pipeline** three ways,
so the choice between them is made from experience rather than opinion.

| | Dataproc + Dataproc Workflows | Databricks + Workflows | Composer (Airflow) |
|---|---|---|---|
| Where the graph lives | A workflow template | A Databricks Job | The DAG |
| Reviewable in git | Yes | Yes — `apps/databricks_jobs/*.json` | Yes — the DAG is Python |
| Orchestrates non-Spark steps | No | Mostly | Yes |
| Backfill | Basic | Good | Yes |
| Non-engineer can rerun | No | Yes | No |

---

## Layout

```text
.
├── 01 … 13 *.md              the chapters
├── apps/
│   ├── airflow_dags/          5 Airflow DAGs
│   ├── cloud_function/        the file converter function
│   ├── databricks_jobs/       Jobs API 2.2 job definitions
│   ├── daily_product_revenue_bq/  the BigQuery variant of the pipeline
│   └── file_format_converter/     the standalone converter
├── data/                      the datasets (see below)
├── notebooks/                 19 notebooks across 9 module directories
├── scripts/
│   ├── 05 Data Warehouse …/   BigQuery SQL
│   └── daily_product_revenue/ the pipeline's SQL scripts
└── tools/
    └── check_environment.py   the setup verification script
```

---

## The datasets

Everything runs on real data, in `data/`.

| Directory | Contents | Used by |
|---|---|---|
| `retail_db/` | Orders, order_items, customers, products, categories, departments (CSV) | The daily product revenue pipeline, on every engine |
| `retail_db_header/` | Same, with headers | Header-aware loading exercises |
| `retail_db_json/` | Same, as JSON | The file format converter |
| `hr_db/` | Employees, departments, jobs, locations, countries, regions | Cloud SQL and BigQuery exercises |
| `nyse/`, `nyse_all/` | NYSE daily prices, 1997–2017 | Partitioning and window-function exercises |
| `lca/` | Life-cycle assessment financials, FY2010–2013 | Aggregations |
| `electionresults/` | `ls2014.tsv` | Tabular parsing |
| `cards/` | Playing-card text and archives | Archive/format exercises |

`data/retail_db/schemas.json` carries the column definitions and their
positions — the File Format Converter reads it to derive the schema
instead of hardcoding it.

---

## Running the pipeline

The daily product revenue pipeline, end to end:

```shell
# 1. The SQL that converts CSV to Parquet and computes revenue
#    scripts/daily_product_revenue/file_format_converter.sql
#    scripts/daily_product_revenue/compute_daily_product_revenue.sql
#    scripts/daily_product_revenue/cleanup.sql
#    scripts/daily_product_revenue/unittest.sql

# 2. As a Dataproc workflow template
#    notebooks/08 …/Managing Dataproc Workflows using gcloud.ipynb

# 3. As a Databricks Job
databricks jobs create --json-file apps/databricks_jobs/daily_product_revenue_job.json

# 4. As an Airflow DAG
#    apps/airflow_dags/daily_product_revenue_jobs.py
```

Deploying the Airflow DAGs to Composer:

```shell
gcloud composer environments create analytics-pipelines \
  --location=us-central1 \
  --environment-size=ENVIRONMENT_SIZE_SMALL

gcloud composer dags import analytics-pipelines \
  --location=us-central1 \
  --dag-id=daily_product_revenue_jobs_dag \
  --source=apps/airflow_dags/daily_product_revenue_jobs.py
```

The DAGs read their configuration from Airflow Variables, so set them
before triggering a run:

```shell
airflow variables set project_id YOUR_PROJECT_ID
airflow variables set region us-central1
airflow variables set bucket_name YOUR_BUCKET
airflow variables set cluster_name YOUR_CLUSTER
```

---

## Prerequisites per module

| Module | Needs |
|---|---|
| 02 — Data Lake | A GCS bucket |
| 04 — Cloud SQL | Cloud SQL admin API, billing enabled, a Cloud SQL instance |
| 05 — BigQuery | BigQuery API, a dataset |
| 06 — Cloud Functions | Cloud Functions API, a deployable source zip |
| 07 — Dataproc | Dataproc API, and a GCP service account with the right roles |
| 08 — Databricks | A Databricks workspace (via GCP Marketplace) and a cluster |
| 09 — Dataproc ↔ BigQuery | The BigQuery Spark connector JAR |
| 12 — Composer | Composer API, and an Airflow DAGs bucket |

Enable the APIs in one pass:

```shell
gcloud services enable \
  storage.googleapis.com \
  sqladmin.googleapis.com \
  bigquery.googleapis.com \
  dataproc.googleapis.com \
  composer.googleapis.com \
  secretmanager.googleapis.com \
  cloudfunctions.googleapis.com \
  cloudresourcemanager.googleapis.com
```

---

## Cost

This course creates billable resources. Before you start:

```shell
# A hard ceiling
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="gcp-de-course" \
  --budget-amount=25 \
  --threshold-rule=amount=10,percent=0.5
```

The largest single risk is a Dataproc cluster left running. It bills by
the hour, including while you sleep. Terminate it when the module ends:

```shell
gcloud dataproc clusters delete YOUR_CLUSTER --region=us-central1 --quiet
```

And delete the project when you are completely done:

```shell
gcloud projects delete YOUR_PROJECT_ID --quiet
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `gcloud: command not found` in VS Code only | Restart VS Code — the terminal has a stale `PATH` |
| `gcloud: command not found` everywhere | Reinstall, or add the SDK `bin` to your shell profile |
| `running scripts is disabled` (Windows) | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `DefaultCredentialsError` in a notebook | `gcloud auth application-default login` |
| DAG task fails on a missing Variable | `airflow variables set <name> <value>` — see above |
| Spark job cannot reach the bucket | The cluster's service account needs `roles/storage.objectViewer` |
| BigQuery write denied from Spark | The service account needs `roles/bigquery.dataEditor` |
| `databricks fs` not found | Expected on GCP — use `gsutil` for DBFS file management |

---

## Related material

| Path | What it is |
|---|---|
| `../chapters/` | The refactored platform course — 34 chapters on the breadth of GCP |
| `../project/` | A pure-Python simulation of the platform, with 102 tests |
| `../interview/` | A certification-style question bank |
| `../CURRICULUM_COVERAGE.md` | (in this directory) — the item-by-item gap analysis for this course |

The two corpora are complementary. **This directory** is the hands-on
build. **`../chapters/`** is the conceptual depth. An interview answer
should cite the build for "I have done it" and the chapters for "I know
why".
