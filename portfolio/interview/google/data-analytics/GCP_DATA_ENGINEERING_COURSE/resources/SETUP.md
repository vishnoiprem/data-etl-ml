# Setup

Everything in this course runs on your laptop. The labs use a local simulation of the Google Cloud platform — no account, no credentials, no bill, no network calls.

There is an **optional** GCP path at the end for students who want to deploy the same pipeline for real. Read the cost warning before you start it.

## 📋 What You Need

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11 or newer | `python3 --version` |
| pytest | any recent | Only for the test suite |
| Jupyter | *optional* | Only for the notebooks: `jupyter`, `nbformat`, `nbclient` |
| Disk | < 50 MB | Sample data is ~1.3 MB |
| GCP account | *not required* | Only for the optional deploy path |
| `gcloud` CLI | *not required* | Only for the optional deploy path |

There are no third-party Python dependencies in the course code — it uses only the standard library. `pytest` is the only dependency the core path needs; Jupyter is optional and only for the notebooks.

## ⏱️ The 5-Minute Local Path

Run every command from the course root — the directory that contains `chapters/`, `project/` and `resources/`.

### Step 1 — Create a virtual environment

```text
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pytest
```

Expected output (the upgrade lines vary by pip version):

```text
Successfully installed pip-24.3.1
```

### Step 2 — Generate the sample data

```text
python resources/sample_data.py --output-dir ./sample_data
```

Expected output:

```text
INFO wrote sample_data/events.csv (4800 rows)
INFO wrote sample_data/events.ndjson (4800 rows)
INFO wrote sample_data/malformed_events.csv (12 lines)
INFO wrote sample_data/region_reference.ndjson (50 rows)
INFO sample data ready in /path/to/GCP_DATA_ENGINEERING_COURSE/sample_data
INFO summary: {'events': 4800, 'malformed_rows': 12, 'reference_rows': 50, 'target_date': '2026-01-15'}
```

The generator is deterministic — the same seed produces the same 4800 events every time, so the expected outputs in the chapters always match.

### Step 3 — Run the pipeline

```text
python project/local_runner.py --run
```

Expected output:

```text
organization: acme.example.com
└── folder: engineering
    └── project: GCP Data Engineering Course (gcp-de-course)
        ├── dataset: curated_us-central1  [BigQuery]
        ├── topic: events-us-central1  [Pub/Sub]
        ├── bucket: raw-events-us-central1  [Cloud Storage]
        └── serviceAccount: pipeline-sa@gcp-de-course.iam.gserviceaccount.com

▶ Running pipeline

  ingest: 4800 accepted, 0 rejected
  aggregate: 4 regions, 4800 events
  publish: 4800 messages to events-normalised
  load: partition 20260115, 4800 rows
  dedup: 4800 -> 4800 rows (0 duplicates removed)

region,event_count,revenue_eur
AMER,1238,464848.02
APAC,1159,421049.85
EMEA,1176,432544.17
LATAM,1227,445554.36

Dead-letter path
----------------
  malformed rows rejected: 12
    bad_amount               1
    bad_timestamp            1
    missing_event_id         1
    missing_user_id          1
    negative_amount          1
    unknown_channel          1
    unknown_currency         1
    unknown_event_type       1
    unknown_region           2
    wrong_field_count        2
```

The clean run rejects nothing — `events.csv` is clean. The `--run` command then merges in `sample_data/malformed_events.csv` so the dead-letter path is visible: **every reason code appears at least once**, which is what makes the failure taxonomy testable rather than a hope.

### Step 4 — Run the tests

```text
python3 -m pytest project/tests/ -q
```

Expected output:

```text
........................................................................ [ 83%]
..............                                                           [100%]
102 passed in 0.31s
```

### Step 5 — Run the linter

```text
python resources/audit_course.py
```

Expected output:

```text
Ran 1527 checks over the course.

No errors. The course is clean.
```

The linter checks that every relative link resolves, every Python snippet in every chapter parses **and executes**, every chapter has its eight required sections in order, no placeholder markers survive, the published expected outputs match what the code actually produces, and every notebook executes end-to-end.

Executing the snippets catches what parsing cannot. A missing `from dataclasses import dataclass` parses perfectly and then raises `NameError` the moment a reader runs it — exactly the kind of defect a reader would hit on a laptop, hours into a chapter.

### Step 6 — (Optional) Open the notebooks

The three notebooks explore the data, the validation taxonomy and the cost model interactively. They need Jupyter, and they run against the same sample data — no cloud account, no credentials.

```bash
pip install jupyter nbformat nbclient
jupyter lab notebooks/
```

To verify they all run without opening a browser:

```bash
python resources/execute_notebooks.py
```

Expected output:

```text
OK   01-explore-the-event-stream.ipynb: ok
OK   02-validate-and-route-to-the-dead-letter-path.ipynb: ok
OK   03-price-the-architectures.ipynb: ok

3/3 notebooks executed cleanly.
```

If `nbclient` is not installed, the linter skips the execution step and says so — it never fails a course for a missing optional dependency.

### The other commands

| Command | What it shows |
|---|---|
| `python project/local_runner.py --list` | The list of commands |
| `python project/local_runner.py --services` | The 34-service inventory table |
| `python project/local_runner.py --categories` | Services grouped into 8 categories |
| `python project/local_runner.py --regions` | The service-by-region availability matrix |
| `python project/local_runner.py --iam` | The demo IAM policy and effective-access checks |
| `python project/local_runner.py --run` | The resource tree and the pipeline log |
| `python project/local_runner.py --cost` | The monthly cost estimate for the demo project |
| `python project/local_runner.py --compare` | The same workload priced across four architectures |
| `python resources/execute_notebooks.py` | Runs every notebook end-to-end |
| `python resources/build_notebooks.py --check` | Checks the notebooks match the generated form |

## 🧪 Using the Modules Directly

Every core module is importable with the standard library alone:

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import SERVICES, REGIONS, CATEGORIES, get_service
from iam_policy import ROLES, ROLE_SUMMARY, evaluate, Principal, Binding, Policy
from cost_model import estimate, compare_architectures, STORAGE_CLASS_PRICES
from pipeline_logic import ingest_events, aggregate_events, EXPECTED_SUMMARY
from platform_sim import build_demo_project, format_resource_tree

print(f"{len(SERVICES)} services, {len(REGIONS)} regions, {len(CATEGORIES)} categories")
print(get_service("bigquery").summary)

accepted, rejected = ingest_events(open("sample_data/events.csv").read().splitlines())
summary = aggregate_events(accepted)
print(summary["AMER"]["event_count"], summary["AMER"]["revenue_eur"])
```

Expected output:

```text
34 services, 12 regions, 8 categories
Serverless, columnar analytical warehouse.
1238.0 464848.02
```

## ☁️ The Optional GCP Path

Everything above is complete on its own. This section is only for students who want to deploy the pipeline to real Google Cloud and see the console.

> **This costs money.** The free tier covers a small fraction of what a deployed pipeline needs. A naive deploy of the full pipeline in one region typically runs **$50–$400 per month**, mostly from BigQuery scans, egress and always-on streaming workers. Delete the resources when you are finished. The steps below show where the money goes.

### 1. Create a project and attach billing

```text
gcloud projects create gcp-de-course-$RANDOM --name="gcp-de-course"
gcloud billing accounts list
gcloud billing projects link gcp-de-course-$RANDOM --billing-account=YOUR_BILLING_ACCOUNT
```

A billing account is required — Google Cloud has no free tier without one. Set a budget alert the moment you link billing:

```text
gcloud billing budgets create --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="course-budget" --budget-amount=25 \
  --threshold-rule=amount=10,percent=0.5
```

Budgets alert; they do not cap spend. You still have to delete the resources.

### 2. Install and authenticate the CLI

```text
gcloud --version
gcloud auth login
gcloud config set project gcp-de-course-$RANDOM
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
```

`gcloud auth login` opens a browser. The alternative for a headless machine is a service account key — but do not commit that key to a repository, and prefer `gcloud auth application-default login` for libraries.

### 3. Enable APIs — only what your module needs

Enabling an API is free, but the service behind it is not. Enable the smallest set for the chapter you are working on:

| Module | `gcloud services enable` |
|---|---|
| Cloud Storage | `storage.googleapis.com` |
| BigQuery | `bigquery.googleapis.com` |
| Pub/Sub | `pubsub.googleapis.com` |
| Dataflow | `dataflow.googleapis.com` |
| Dataproc | `dataproc.googleapis.com` |
| Cloud Composer | `composer.googleapis.com` |
| Cloud Run | `run.googleapis.com` |
| Cloud Run functions | `cloudfunctions.googleapis.com` |
| Cloud SQL | `sqladmin.googleapis.com` |
| Cloud Spanner | `spanner.googleapis.com` |
| Bigtable | `bigtableadmin.googleapis.com` |
| Dataplex | `dataplex.googleapis.com` |
| Data Catalog | `datacatalog.googleapis.com` |
| Sensitive Data Protection | `dlp.googleapis.com` |
| Datastream | `datastream.googleapis.com` |
| Storage Transfer Service | `storagetransfer.googleapis.com` |
| BigQuery Data Transfer Service | `bigquerydatatransfer.googleapis.com` |
| Database Migration Service | `databasemigration.googleapis.com` |
| Dataform | `dataform.googleapis.com` |
| Looker Studio | `bigquery.googleapis.com` (shared) |
| Vertex AI | `aiplatform.googleapis.com` |
| Cloud Scheduler | `cloudscheduler.googleapis.com` |
| Cloud Logging | `logging.googleapis.com` |
| Cloud Monitoring | `monitoring.googleapis.com` |

Enable a set in one command:

```text
gcloud services enable storage.googleapis.com bigquery.googleapis.com pubsub.googleapis.com
```

### 4. Deploy the pipeline, piece by piece

```text
# Bucket for raw events
gsutil mb -l us-central1 -b on gcp-de-course-$RANDOM-raw-events

# Topic and subscription
gcloud pubsub topics create events-us-central1 --region=us-central1
gcloud pubsub subscriptions create events-us-central1-sub \
  --topic=events-us-central1 --region=us-central1

# Upload the sample data
gsutil cp sample_data/events.csv gs://gcp-de-course-$RANDOM-raw-events/

# BigQuery dataset, partitioned by event date
bq mk --location=us-central1 --time_partitioning_field=event_date gcp-de-course-$RANDOM:curated
```

### 5. Free-tier caveats

| Free tier | Allowance | Realistic for this course |
|---|---|---|
| Cloud Storage | 5 GB-month | Covers the sample data easily |
| Network egress | 1 GB/month | The first cross-region copy can blow this |
| BigQuery on-demand | 1 TB scanned/month | One careless `SELECT *` on a 10 TB table is 60× over |
| Compute Engine | 0.25 vCPU-hour (f1-micro) | Roughly 15 minutes — effectively nothing |
| Cloud Run | 2M requests, 180k CPU-seconds | Comfortable for a demo API |
| Cloud Run functions | 2M invocations | Comfortable for a demo |
| Pub/Sub | 10 GB/month | Comfortable for 4800 messages |

Everything above the free tier bills at list price. See [CHEATSHEET.md](CHEATSHEET.md) for the formulas.

### 6. Clean up

```text
gcloud projects delete gcp-de-course-$RANDOM --quiet
```

Deleting the project removes the resources and stops the billing. Wait a few minutes for the deletion to propagate, then check the billing console — some charges, notably BigQuery and egress, arrive with a delay.

## 🔧 Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `sample data not found at .../sample_data/events.csv` | The generator has not been run | `python resources/sample_data.py --output-dir ./sample_data` |
| `ModuleNotFoundError: No module named 'service_catalog'` | Running from the wrong directory | `cd` to the course root, the one containing `project/` |
| `ModuleNotFoundError: No module named 'pytest'` | pytest is not installed in the active environment | `source .venv/bin/activate && python -m pip install pytest` |
| `python: command not found` | macOS ships `python3`, not `python` | Use `python3` everywhere, or activate the venv so `python` points at 3.11+ |
| `SyntaxError` on a f-string in the console | The shell is mangling `{}` | Use single quotes, or write the snippet to a file first |
| `Permission denied (publickey)` on `gcloud auth login` | SSH key not registered | `gcloud auth login --no-launch-browser` and paste the URL, or use `--update-keys` |
| `gcloud: command not found` | The Cloud SDK is not installed | Install it, or skip the optional GCP path — the course is complete without it |
| `ERROR: (gcloud.billing) The project ... has no billing account` | Billing was never linked | `gcloud billing projects link ... --billing-account=YOUR_BILLING_ACCOUNT` |
| `ERROR: BigQuery: Exceeded rate limits` | Too many queries at once | Add a reservation, or lower the concurrency in the job |
| `ERROR: Could not create the service account` | The API is not enabled | `gcloud services enable iam.googleapis.com` |
| The linter reports a broken link | A file was renamed or moved | The message names the file and the target — recreate the path or update the link |
| The linter reports a snippet does not parse | A fenced block tagged `python` has a typo | The message names the snippet index in that file |
| `--run` shows no rejects | Expected — `events.csv` has no bad rows | The 12 malformed rows live in `sample_data/malformed_events.csv`; `--run` merges them in and prints the dead-letter breakdown |

## ✅ Verification Checklist

Work down the list. Every item must pass before you start chapter 1.

| # | Check | Command | Expected |
|---|---|---|---|
| 1 | Python version | `python3 --version` | `Python 3.11` or newer |
| 2 | Virtual environment active | `python -c "import sys; print(sys.prefix)"` | The path ends in `.venv` |
| 3 | Sample data exists | `ls sample_data/` | `events.csv`, `events.ndjson`, `malformed_events.csv`, `region_reference.ndjson`, `summary.json` |
| 4 | Row count is right | `wc -l sample_data/events.csv` | `4801` (4800 rows + header) |
| 5 | Pipeline runs | `python project/local_runner.py --run` | `4800 accepted`, 4 regions, `malformed rows rejected: 12` |
| 6 | Totals match | `python project/local_runner.py --run` | AMER 1238 / 464848.02, APAC 1159 / 421049.85, EMEA 1176 / 432544.17, LATAM 1227 / 445554.36 |
| 7 | Tests pass | `python3 -m pytest project/tests/ -q` | `102 passed` |
| 8 | Linter clean | `python resources/audit_course.py` | `No errors. The course is clean.` |
| 9 | Service inventory renders | `python project/local_runner.py --services` | A table of 34 services |
| 10 | Region matrix renders | `python project/local_runner.py --regions` | 34 rows × 12 regions |
| 11 | IAM evaluation works | `python project/local_runner.py --iam` | 7 access checks with ✓ and ✗ marks |
| 12 | Cost estimate renders | `python project/local_runner.py --cost` | `TOTAL $3.3844` |
| 13 | Notebooks run | `python resources/execute_notebooks.py` | `3/3 notebooks executed cleanly.` *(skip if Jupyter is not installed)* |

If all thirteen pass, you are ready. If step 5 or 6 fails, re-run step 3 — a stale or truncated `events.csv` is the usual cause.

## 📚 Where To Go Next

| Document | Use it for |
|---|---|
| [CHEATSHEET.md](CHEATSHEET.md) | Command reference, cost formulas, decision tables |
| [GLOSSARY.md](GLOSSARY.md) | Every term the course defines |
| [FAQ.md](FAQ.md) | The questions students actually ask |
| [../CURRICULUM.md](../CURRICULUM.md) | The 34-chapter plan |
| [../chapters/01-introduction-to-cloud-computing.md](../chapters/01-introduction-to-cloud-computing.md) | Where the course starts |
| [../interview/README.md](../interview/README.md) | The interview question bank |
