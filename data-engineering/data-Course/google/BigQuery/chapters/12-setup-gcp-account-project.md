# 2.5 — Setup: GCP Account, Project & Billing

> **Section 2 · BigQuery Fundamentals · Lectures 2.5–2.7 · 4:35 + 0:45 + 0:14**

## 🎯 What you will learn

- Set up a GCP project correctly from the start (IAM, APIs, billing)
- Enable the APIs you need
- Configure budget alerts so you never get a surprise bill
- Authenticate via the CLI, the SDK, and service accounts

---

## 🧠 Concept

> **Important note:** You must have a **billing-enabled GCP project** to query BigQuery. The free
> tier requires billing to be linked, even though you will not be charged beyond the free limits.

### The resource hierarchy

```
Organization (optional)
└── Folders (optional)
    └── Projects  ← BigQuery datasets and tables live here
        ├── Datasets
        │   └── Tables
        └── Service Accounts / IAM bindings
```

**Everything in BigQuery belongs to a project.** Billing is attached to the project (or to a folder
for consolidated billing). This is the first decision that matters, because it determines who can
see your data and which bill it lands on.

### IAM roles for BigQuery

| Role | Grants | Who needs it |
|------|--------|--------------|
| `roles/bigquery.dataViewer` | Read data & metadata | Analysts, BI tools |
| `roles/bigquery.dataEditor` | Read + write data | Data engineers |
| `roles/bigquery.dataOwner` | + create/delete datasets & tables | Leads, admins |
| `roles/bigquery.jobUser` | Run jobs (needed for query-only users) | Analysts |
| `roles/bigquery.admin` | Full admin | Platform admins |
| `roles/bigquery.metadataViewer` | View metadata only | Catalog integrations |
| `roles/storage.admin` | Manage GCS buckets | Data engineers (if using external tables) |

💡 **Least privilege for a BI analyst:**

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="group:analysts@yourcompany.com" \
    --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="group:analysts@yourcompany.com" \
    --role="roles/bigquery.dataViewer"
```

Note the split: `jobUser` lets them *run* queries; `dataViewer` lets them *see* results. A user
without `dataViewer` can still run queries but cannot read the output tables — useful for a
"compute only" service account.

---

## 🛠️ Hands-On Setup

### 1. Create the project

```bash
# Set your preferred project name and region
export PROJECT_ID="bq-course-$(date +%s)"
export REGION="us-central1"

# Create it
gcloud projects create "$PROJECT_ID" \
    --name="BigQuery Course" \
    --description="Hands-on BigQuery course workspace"

# Set it as the active project
gcloud config set project "$PROJECT_ID"
```

### 2. Link billing

```bash
# List available billing accounts
gcloud billing accounts list

# Link one to the project
gcloud billing projects link "$PROJECT_ID" \
    --billing-account="XXXXXX-XXXXXX-XXXXXX"
```

### 3. Enable the APIs

```bash
gcloud services enable \
    bigquery.googleapis.com \
    storage.googleapis.com \
    cloudbilling.googleapis.com \
    iam.googleapis.com \
    cloudresourcemanager.googleapis.com
```

### 4. Set a budget alert (do this BEFORE running anything)

```bash
gcloud billing budgets create \
    --billing-account="XXXXXX-XXXXXX-XXXXXX" \
    --display-name="BigQuery Course Budget" \
    --budget-amount=100 \
    --budget-display-name="BigQuery Course Budget" \
    --threshold-rules="0.5,0.9,1.0" \
    --threshold-actions="stop-spend"
```

💡 **Always set `--threshold-actions="stop-spend"`** during development. A runaway query — a
cartesian join between two 10 TB tables — can burn hundreds of dollars in minutes. The default
email-only alerts are too slow.

### 5. Authenticate

```bash
# User credentials (for interactive development)
gcloud auth login
gcloud auth application-default login

# Verify
gcloud auth list
gcloud config list
```

### 6. Create a service account for the SDK

```bash
gcloud iam service-accounts create bq-course-sa \
    --display-name="BigQuery Course Service Account"

# Scope it to the project only
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:bq-course-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataOwner"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:bq-course-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Download the key — never commit this
gcloud iam service-accounts keys create ./bq-course-sa-key.json \
    --iam-account="bq-course-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Point the SDK at it
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/bq-course-sa-key.json"
```

⚠️ **Never commit service account keys.** Add to `.gitignore`:
```
bq-course-sa-key.json
*.key.json
```

### 7. Set default location and other project settings

```sql
-- Create the working dataset
CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.analytics`
OPTIONS (
  location = 'US',
  description = 'Analytics dataset',
  labels = [('env', 'dev'), ('course', 'bigquery')]
);

-- Confirm everything works
SELECT
    CURRENT_PROJECT()  AS project,
    CURRENT_DATETIME()  AS now_utc,
    CURRENT_REGION()    AS region;
```

### 8. Guard every query with a byte cap

```bash
# The CLI equivalent of maximum_bytes_billed
bq query --use_legacy_sql=false --max_bytes_billed=1000000000 '
  SELECT COUNT(*) FROM `YOUR_PROJECT_ID.analytics.orders`'
```

```python
from google.cloud import bigquery

config = bigquery.QueryJobConfig()
config.maximum_bytes_billed = 1_000_000_000   # 1 GB

client = bigquery.Client()
job = client.query("SELECT COUNT(*) FROM `p.analytics.orders`", job_config=config)
print(job.result())
```

💡 **Set this as your default.** It is the single most effective protection against a runaway bill.

---

## 🔑 Key Takeaways

- Billing must be linked even for free-tier use.
- Everything belongs to a project — project choice determines data access and which bill it lands on.
- Split `jobUser` from `dataViewer` for least-privilege BI access.
- **Set a budget with `stop-spend` before running anything.**
- Set `maximum_bytes_billed` on every query during development.
- Service account keys must never be committed.

---

## 📚 Practice Exercises

1. **IAM design.** A team has: 5 data engineers, 30 analysts, 2 admins, and 1 BI service account.
   Write the exact `gcloud projects add-iam-policy-binding` commands for each group.

2. **Budget response.** You get an email at 50% of budget. A dashboard is responsible for $40 of the
   $50. Write the query to identify the top-10 expensive queries in the project.

3. **Failure mode.** Your teammate accidentally committed `bq-course-sa-key.json` to a public repo.
   Write the exact remediation steps, in order.

4. **Region choice.** Your users are in London and Mumbai. Your data source is in `europe-west2`.
   Compare: `EU` multi-region vs `europe-west2` regional vs `asia-south1`. Which minimizes cost
   and latency?

---

## 📖 Further Reading

- BigQuery IAM roles — https://cloud.google.com/bigquery/docs/access-control
- Setting up billing — https://cloud.google.com/billing/docs/how-to/modify-project
- Budget alerts — https://cloud.google.com/billing/docs/how-to/budgets
