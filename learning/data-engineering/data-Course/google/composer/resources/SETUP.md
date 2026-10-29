# Setup — Google Cloud Composer Course

Two paths. **Path A takes five minutes and needs no cloud account at all** — it is
enough for every chapter, every notebook and every test in this course. Path B is for
when you actually want to deploy to Composer.

---

## Path A — Local (5 minutes, no bill)

### 1. Use the project virtualenv

This repository already has a virtualenv at the repo root with everything the course
needs:

```bash
cd data-engineering/data-Course/google/composer
source ../../../../.env/bin/activate

python --version
# Python 3.13.16
```

If that path does not exist, create your own:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r project/requirements.txt
```

The only hard requirement is **Jinja2** — the course's templating model uses it.
`pandas` and `matplotlib` are used by two notebooks; `pytest` runs the tests.

```bash
pip install jinja2 pandas matplotlib pytest
```

> **Airflow is deliberately NOT installed.** The whole point of this course is to
> learn Airflow without a local install that will not match Composer's version. If
> you install Airflow, the test suite still passes — it just gains a few extra tests
> that parse the DAG files. See [the Airflow section](#optional-install-airflow) below.

### 2. Generate the sample dataset

```bash
python resources/sample_data.py --output-dir ./sample_data
```

Expected output:

```text
INFO wrote sample_data/orders.csv (5000 rows)
INFO wrote sample_data/orders.ndjson (5000 rows)
INFO wrote sample_data/malformed_orders.csv (9 lines)
INFO wrote sample_data/product_reference.ndjson (50 rows)
INFO sample data ready in .../composer/sample_data
```

The dataset is **seeded**, so every run produces byte-identical output. The expected
results printed throughout the course stay correct no matter when you run them.

### 3. Run a pipeline

```bash
python project/local_runner.py --list
python project/local_runner.py --dag etl_to_gcs
```

Expected output:

```text
▶ Running etl_to_gcs @ 2026-01-15

  Run summary for etl_to_gcs @ 2026-01-15
  ----------------------------------------------------
    ✓ read_orders            success
    ✓ transform_orders       success
    ✓ aggregate              success
    ✓ write_summary          success

  ✓ etl_to_gcs succeeded

region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

### 4. Run the tests

```bash
python -m pytest project/tests/ -q
# 130 passed, 10 skipped in 0.35s
```

The 10 skips are tests that require Airflow to be installed.

### 5. Verify the notebooks

```bash
python resources/check_notebooks.py
# All 10 notebooks passed.
```

This **executes every code cell in every notebook**, in order. If a notebook would
fail on your laptop, it fails here first — which is much cheaper than finding out
halfway through a chapter.

---

## Path B — Deploy to Cloud Composer

Everything below is optional. You need it only when you want a real Composer
environment.

### Prerequisites

| Requirement | Notes |
|---|---|
| A GCP project | With billing enabled |
| The **Cloud Composer API** | `composer.googleapis.com` |
| The **Cloud Storage API** | For the DAG bucket |
| The **Cloud SQL Admin API** | For the metadata database |
| Permission to create a Composer environment | Typically Owner or Editor on the project |

Enable the APIs:

```bash
gcloud services enable \
  composer.googleapis.com \
  storage.googleapis.com \
  sqladmin.googleapis.com \
  cloudresourcemanager.googleapis.com
```

### 1. Create a DAG bucket

```bash
PROJECT_ID=YOUR_PROJECT_ID
REGION=us-central1
BUCKET=gs://${PROJECT_ID}-composer-dags

gcloud storage buckets create gs://${PROJECT_ID}-composer-dags \
  --location=${REGION} \
  --uniform-bucket-level-access
```

### 2. Create the environment

```bash
gcloud composer environments create composer-course \
  --location=${REGION} \
  --environment-size=SMALL \
  --image-version=composer-2.9.7-airflow-2.9.3 \
  --dag-bucket=${BUCKET} \
  --description="Composer course environment"
```

The environment takes **5–10 minutes** to provision. It creates a GKE cluster, a
Cloud SQL instance for the metadata database, and a web server.

### 3. Upload the DAGs

```bash
gcloud storage cp --recursive project/dags/* gs://${PROJECT_ID}-composer-dags/
```

Composer parses new files within **1–2 minutes**. Check the DAG list in the UI
(Composer → DAGs).

### 4. Configure Variables and Connections

In the Composer UI under **Admin → Variables** and **Admin → Connections**, set:

| Type | Name | Value |
|---|---|---|
| Variable | `gcp_project_id` | `YOUR_PROJECT_ID` |
| Variable | `source_bucket` | `gs://your-source-bucket` |
| Variable | `target_bucket` | `gs://your-target-bucket` |
| Variable | `bq_dataset` | `analytics` |
| Variable | `bq_table` | `orders_enriched` |
| Variable | `full_load_threshold` | `1000000` |
| Connection | `gcp_default` | The BigQuery connection Composer provides |

> **Never put a password in a Variable.** Variables are visible in the UI to anyone
> with Variable read access, and are stored unencrypted in the metadata database.
> Use a Connection — Airflow encrypts the `password` field.

### 5. Trigger a run

```bash
gcloud composer environments run composer-course \
  --location=${REGION} \
  --dag etl_orders_to_bigquery
```

Or use the **▶ Run** button in the UI, which also lets you pass `params`.

### 6. Clean up — do not skip this

A Composer environment bills **continuously**, whether or not any DAG runs. Delete it
when you are finished:

```bash
gcloud composer environments delete composer-course \
  --location=${REGION}
```

> **What survives the delete?** The DAG bucket does — it is yours, not Composer's.
> A Composer-managed Cloud SQL instance may also survive depending on the Composer
> version. Check the Cloud SQL console. The failure story is real: an environment
> left running for a month costs several hundred dollars, and nobody notices because
> there is no usage to look at.

Set a budget alert as a backstop:

```bash
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="Composer guardrail" \
  --budget-amount=100 \
  --threshold-rules="percentage=0.5, spend_basis=currentMonth"
```

---

## Optional: Install Airflow

If you want to parse the DAG files locally, install Airflow in a **separate**
virtualenv — never in the course venv, or the pure-logic tests will pick up the
wrong environment.

```bash
python3 -m venv .venv-airflow
source .venv-airflow/bin/activate
pip install "apache-airflow==2.9.3" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.11.txt"
```

With Airflow installed, the test suite gains 10 extra tests that parse the DAG
files and check their structure.

> **Pin the version to your Composer's version.** Airflow's own docs are explicit
> that Airflow is not a library with a stable API — the DAG import API can change
> between minor versions. A DAG that parses on 2.9 may fail on 2.10.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'jinja2'`

```bash
pip install jinja2
```

### `ModuleNotFoundError: No module named 'pipeline_logic'`

The `core/` directory must be on `sys.path`. The notebooks handle this with a
preamble; in a script, do it explicitly:

```python
import sys
sys.path.insert(0, "project/core")
```

### `FileNotFoundError: sample_data/orders.csv`

```bash
python resources/sample_data.py --output-dir ./sample_data
```

### The notebooks fail on `COURSE_ROOT`

The path preamble walks up two levels to find `project/`. If you launched Jupyter
from an unexpected directory, open it from the course root:

```bash
cd data-engineering/data-Course/google/composer
jupyter lab
```

### `DagNotFound: DAG: [etl_orders_to_bigquery] not found`

In Composer, the DAG file must be in the `dags/` bucket **and** the environment
must have finished parsing it. Wait 1–2 minutes after upload, then hard-refresh
the DAG list. If it still fails, check the DAG import errors in the UI.

### The local runner reports `upstream_failed`

That is correct behaviour, not a bug: an upstream task failed, so this one could
not run. Read the failure from the upstream task in the run summary.

### `pytest` finds no tests

Run it from the course root:

```bash
python -m pytest project/tests/ -q
```
