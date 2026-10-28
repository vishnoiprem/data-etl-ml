# Course Setup Guide

> Everything you need before starting the BigQuery course.

---

## 📋 Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.9+ (3.11 recommended) | `python3 --version` |
| Google Cloud SDK | latest | `gcloud --version` |
| A GCP project | with billing enabled | — |
| BigQuery API | enabled | — |

---

## 1. Install the Google Cloud SDK

```bash
# macOS (Homebrew)
brew install --cask google-cloud-sdk

# macOS (installer script)
curl https://sdk.cloud.google.com | bash
source "$HOME/google-cloud-sdk/path.zsh.sh"

# Linux
curl https://sdk.cloud.google.com | bash
source "$HOME/google-cloud-sdk/path.bash.inc"
```

---

## 2. Authenticate

```bash
# Log in
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID
gcloud config set compute/region europe-west1

# Verify
gcloud config list
```

---

## 3. Enable the required APIs

```bash
gcloud services enable \
  bigquery.googleapis.com \
  bigquerystorage.googleapis.com \
  storage.googleapis.com \
  pubsub.googleapis.com \
  dataflow.googleapis.com \
  composer.googleapis.com \
  cloudscheduler.googleapis.com
```

---

## 4. Set up a Python environment

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-Course/google/BigQuery

python3 -m venv .venv
source .venv/bin/activate

pip install -r resources/requirements.txt
```

---

## 5. Create a service account (for CI and production)

```bash
gcloud iam service-accounts create bq-pipeline \
  --display-name="BigQuery Pipeline Service Account"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:bq-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:bq-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:bq-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:bq-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:bq-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/pubsub.subscriber"
```

**Never commit the key file.** For local development, use impersonation instead:

```bash
gcloud auth application-default login \
  --impersonate-service-account=bq-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

---

## 6. Create the Cloud Storage bucket

```bash
gcloud storage buckets create gs://YOUR_PROJECT_ID-bq-course \
  --location=europe-west1 \
  --uniform-bucket-level-access
```

Folder layout:

```
gs://YOUR_PROJECT_ID-bq-course/
├── staging/          # inbound files (CSV, NDJSON, Parquet)
│   ├── pos/
│   └── parquet/
├── raw/              # landing zone copies
├── exports/          # EXPORT DATA targets
├── beam/
│   ├── tmp/
│   ├── staging/
│   └── bq_tmp/
└── logs/
```

---

## 7. Run the setup SQL

```bash
bq query --use_legacy_sql=false < sql/01_setup_and_datasets.sql
bq query --use_legacy_sql=false < sql/02_tables_and_schemas.sql
```

---

## 8. Verify everything

```python
python - <<'PY'
from google.cloud import bigquery

client = bigquery.Client()
print("Project:", client.project)

rows = client.query(
    """
    SELECT dataset_id, location
    FROM `region-us`.INFORMATION_SCHEMA.SCHEMATA
    WHERE dataset_id IN ('raw','staging','curated','mart','sandbox')
    ORDER BY dataset_id
    """
).result()

for r in rows:
    print(f"  {r.dataset_id:12} {r.location}")
PY
```

---

## 9. Load the sample data

```bash
# Generate and upload the sample data
python resources/sample_data.py

# Load it
bq load --use_legacy_sql=false \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --replace \
  YOUR_PROJECT_ID:curated.orders \
  gs://YOUR_PROJECT_ID-bq-course/staging/orders_2026-01-15.csv
```

---

## 🔐 Environment variables

Create a `.env` file (and add it to `.gitignore`):

```bash
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
BQ_LOCATION=US
BQ_MAX_BYTES_BILLED=10737418240
ENV=dev
GCS_BUCKET=YOUR_PROJECT_ID-bq-course
```

---

## 🐍 Notebooks

```bash
jupyter lab notebooks/
```

Notebooks use the Python client. The first notebook sets up a shared client module
in the notebook directory:

```bash
cp resources/bq_client.py notebooks/bq_client.py
```

---

## ✅ Checklist

- [ ] `gcloud auth list` shows an active account
- [ ] `gcloud config get-value project` returns your project
- [ ] BigQuery API is enabled
- [ ] `bq ls` returns without error
- [ ] `python -c "import google.cloud.bigquery"` succeeds
- [ ] The bucket exists
- [ ] The datasets exist
- [ ] The sample data loads

---

## 🆘 Troubleshooting

| Problem | Fix |
|---------|-----|
| `DefaultCredentialsError` | `gcloud auth application-default login` |
| `403 Permission denied` on a query | Grant `roles/bigquery.jobUser` and `roles/bigquery.dataViewer` |
| `404 Not found: Dataset` | Wrong project — check `client.project` |
| `bq: command not found` | Add the SDK's `bin` to your `PATH` |
| `AccessDeniedException: ... does not have storage.buckets.get` | Grant `roles/storage.objectViewer` |
| Billing not enabled | Enable billing in the GCP console — BigQuery will not run without it |
| `pandas` import fails in Jupyter | `pip install pandas pyarrow db-dtypes` then restart the kernel |

---

## 📖 Next steps

- Chapter `42-python-setup.md` — the client setup in detail
- Chapter `45-python-query-tables.md` — your first queries
- `notebooks/01-setup-and-authentication.ipynb` — hands-on setup
