# Setup Guide

> Everything in this course runs **locally with no GCP account, no credentials, and no bill**.
> The cloud sections are optional — read them when you want to deploy.

---

## The 5-minute path (no GCP required)

This is the path the course assumes. Everything in it works offline after
the first install.

```bash
cd data-engineering/data-Course/google/Dataflow

python3 -m venv .venv
source .venv/bin/activate

pip install -r project/requirements.txt

# Generate the deterministic dataset
python resources/sample_data.py --output-dir ./sample_data

# Run the batch pipeline
python project/batch_pipeline.py --input ./sample_data/orders.csv --output ./out/summary

# Run the streaming pipeline
python project/streaming_pipeline.py --input ./sample_data/events.ndjson --output ./out/streaming --window-seconds 3600
```

Expected batch output:

```csv
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

### Python version

Apache Beam supports **Python 3.9–3.13**. The course was developed and
tested on **Python 3.13**. Check yours:

```bash
python3 --version
```

> **Why this matters.** Beam's type inference, `from __future__ import
> annotations` behaviour, and several dependency pins differ across
> Python versions. On 3.13 you may need `--no-build-isolation` for some
> transitive dependencies; if `pip install apache-beam[gcp]` fails to
> build a wheel, try `pip install apache-beam` first (the plain wheel has
> fewer binary dependencies).

---

## Installing the course tools

```bash
pip install -r project/requirements.txt
```

That installs:

| Package | Why |
|---|---|
| `apache-beam` | the SDK every chapter uses |
| `apache-beam[gcp]` extras | only needed for `DataflowRunner` and `WriteToBigQuery` |
| `google-cloud-storage` | GCS I/O |
| `google-cloud-pubsub` | streaming I/O |
| `pytest` | the test suites |

### The optional extras

Beam's extras are additive and each pulls a heavy transitive dependency
tree. Install only what you need:

```bash
pip install "apache-beam[gcp]"        # Dataflow runner, BigQuery, GCS
pip install "apache-beam[dataframe]"  # Beam SQL / DataFrames API
pip install "apache-beam[avro]"       # Avro sources and sinks
```

---

## Setting up a GCP project (optional)

Read this section when you want to actually deploy to Dataflow.

### 1. Create the project

```bash
gcloud projects create YOUR_PROJECT_ID --name="Dataflow Course"
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable the APIs

Dataflow needs a surprising number of them. Enabling them one at a time
is a common source of the "permission denied" error that shows up two
hours into a job.

```bash
gcloud services enable \
    dataflow.googleapis.com \
    compute.googleapis.com \
    storage.googleapis.com \
    bigquery.googleapis.com \
    pubsub.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com
```

> **Also enable the Dataflow API in the console.** `gcloud services enable`
> covers the service, but the first Dataflow job in a brand-new project
> sometimes still fails until you open
> **APIs & Services → Dataflow API → Enable**. This is a known papercut.

### 3. Enable billing

```bash
gcloud billing projects link YOUR_PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

Billing is required even for jobs that cost nothing. Set a budget alert
at $1 so an accidental `DataflowRunner` on a large input cannot surprise
you.

### 4. Create a bucket

```bash
gcloud storage buckets create gs://YOUR_BUCKET --location=us-central1 --uniform-bucket-level-access
```

Region matters. **A bucket in `us-central1` and a Dataflow job in
`europe-west1` means every byte crosses the continent twice.** Pick one
region for the bucket, the job and the BigQuery dataset and keep them
aligned.

### 5. The three service identities

This is where most Dataflow permission errors live. Dataflow uses
**three distinct identities**, and confusing them is the single most
common cause of a job that fails to start.

| Identity | What it does | Needs |
|---|---|---|
| **Your account** | submits the job | `roles/dataflow.developer` (or owner) |
| **Dataflow service agent** | creates workers, reads/writes GCS | `roles/dataflow.serviceAgent` |
| **Worker service account** | the identity the workers themselves run as | `roles/dataflow.worker` |

The **Dataflow service agent** is created automatically the first time a
job runs, but it needs the right roles *before* that first job — and
creating it by hand is more reliable than letting Dataflow create it.

```bash
# The service agent, named service-<PROJECT_NUMBER>@gcp-sa-dataflow.iam.gserviceaccount.com
export PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')
export SERVICE_ACCOUNT="service-${PROJECT_NUMBER}@gcp-sa-dataflow.iam.gserviceaccount.com"

gcloud iam service-accounts create dataflow-worker \
    --display-name="Dataflow Worker"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/dataflow.serviceAgent"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/storage.objectAdmin"

export WORKER_SA="dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${WORKER_SA}" \
    --role="roles/dataflow.worker"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${WORKER_SA}" \
    --role="roles/storage.objectAdmin"

gcloud iam service-accounts keys create ./dataflow-worker-key.json \
    --iam-account="${WORKER_SA}"
```

### 6. Authenticate

```bash
gcloud auth application-default login
```

This writes Application Default Credentials that the Beam SDK reads.
Then set the environment:

```bash
export PROJECT_ID=YOUR_PROJECT_ID
export REGION=us-central1
export BUCKET=gs://YOUR_BUCKET
export TEMP_LOCATION=gs://YOUR_BUCKET/dataflow/temp
export STAGING_LOCATION=gs://YOUR_BUCKET/dataflow/staging
export SERVICE_ACCOUNT_EMAIL=${WORKER_SA}
```

> **Never run a job with a user key file.** A user service account with
> `roles/owner` running as a Dataflow worker is the single most common
> way a course project ends up as a security incident. Use the dedicated
> worker service account above.

---

## The `.env` file

The course reads configuration from the **repository root `.env`** — one
file configures every project in the repo.

```bash
# at the repo root, not the course directory
cat >> /path/to/data-etl-ml/.env <<'EOF'
PROJECT_ID=YOUR_PROJECT_ID
REGION=us-central1
BUCKET=gs://YOUR_BUCKET
TEMP_LOCATION=gs://YOUR_BUCKET/dataflow/temp
STAGING_LOCATION=gs://YOUR_BUCKET/dataflow/staging
SERVICE_ACCOUNT_EMAIL=dataflow-worker@YOUR_PROJECT_ID.iam.gserviceaccount.com
EOF
```

Recognised variables:

| Variable | Purpose |
|---|---|
| `BEAM_RUNNER` | the runner (default `BundleBasedDirectRunner`) |
| `PROJECT_ID` | the GCP project |
| `REGION` | the Dataflow region (default `us-central1`) |
| `TEMP_LOCATION` | the Dataflow temp path |
| `STAGING_LOCATION` | the Dataflow staging path |
| `SERVICE_ACCOUNT_EMAIL` | the worker service account |
| `SUBNETWORK` | the subnetwork for private-IP jobs |

> **A note on `.env` being a directory.** In this repository `data-etl-ml/.env`
> is a *virtualenv directory*, not a dotenv file. The loaders detect this
> and fall back to the process environment rather than crashing. If you
> want dotenv-style configuration, point at a different file with
> `load_dotenv(path)` or set the variables in your shell.

---

## Choosing a runner

```bash
python project/batch_pipeline.py --runner BundleBasedDirectRunner   # default
python project/batch_pipeline.py --runner DirectRunner               # Prism, faster
python project/batch_pipeline.py --runner DataflowRunner             # needs GCP
```

| Runner | Needs GCP | Supports full trigger set | Use for |
|---|---|---|---|
| `BundleBasedDirectRunner` | no | yes | **the course default** |
| `DirectRunner` (Prism) | no | no — panics on `AfterWatermark` | fast local iteration on batch |
| `DataflowRunner` | yes | yes | deployment |

The Prism runner (`DirectRunner` in Beam 2.60+) is a Go-based rewrite and
is genuinely faster, but it does not yet implement every trigger and
windowing combination. In particular it panics on `AfterWatermark` and on
the `+inf` watermark evaluation that `TestPipeline` performs. The course
therefore defaults to `BundleBasedDirectRunner`, and the streaming
pipeline explicitly documents the limitation.

---

## Verifying the install

```bash
# The SDK imports
python -c "import apache_beam; print(apache_beam.__version__)"

# The environment summary
python resources/beam_client.py

# The pure logic — 51 tests, no Beam required
python3 -m pytest project/tests/test_transforms.py -q

# Everything
python3 -m pytest project/tests/ -q

# The course linter
python resources/audit_course.py

# The course structural tests
python resources/test_course.py
```

---

## Troubleshooting

### `apache-beam` will not install

The `gcp` extra pulls a large binary dependency tree. Install the plain
wheel first and add extras only when you need them:

```bash
pip install apache-beam
pip install "apache-beam[gcp]" --no-build-isolation
```

### `DefaultCredentialsError: Could not automatically determine credentials`

You are running a `DataflowRunner` job without credentials. Either run
the local runner, or:

```bash
gcloud auth application-default login
```

### `RuntimeError: Transform name is already used`

Two transforms in the same pipeline share a label. Beam's message does
not say which ones. The course linter catches this statically:

```bash
python resources/audit_course.py
```

### `ValueError: accumulation_mode must be provided for non-trivial triggers`

`AfterCount` and `AfterWatermark` need an explicit accumulation mode:

```python
beam.WindowInto(
    FixedWindows(60),
    trigger=AfterWatermark(),
    accumulation_mode=AccumulationMode.ACCUMULATING,
)
```

### `ValueError: Unsafe trigger: AfterCount(100) may lose data`

Beam refuses triggers it cannot prove are safe unless you opt in with
`--allow_unsafe_triggers`. The streaming pipeline detects this and falls
back to zero allowed lateness with a warning rather than failing.

### `panic in ElementManager.Bundles watermark evaluation goroutine`

The Prism runner and `AfterWatermark` do not mix. Use
`BundleBasedDirectRunner`.

### The job fails with a 403 on `storage.objects.get`

The Dataflow service agent is missing `roles/storage.objectAdmin`. See
[step 5](#5-the-three-service-identities) — and note that adding the
role *after* the service agent was created still requires removing and
re-adding it, because Dataflow caches the policy at creation time.
