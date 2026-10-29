# Course Setup Guide

> Everything you need before starting the Dataproc + PySpark course.

---

## 📋 Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.9+ (3.11 recommended) | `python3 --version` |
| Google Cloud SDK | latest | `gcloud --version` |
| A GCP project | with billing enabled | `gcloud projects list` |
| Dataproc API | enabled | `gcloud services list --enabled` |
| Cloud Storage API | enabled | same |
| BigQuery API | enabled | same |
| A VPC network | with Private Google Access | — |
| gcloud auth | an active account | `gcloud auth list` |

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

Verify:

```bash
gcloud --version
```

---

## 2. Authenticate

```bash
# Log in with your Google account
gcloud auth login

# Set your defaults
gcloud config set project YOUR_PROJECT_ID
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a

# Verify
gcloud config list
gcloud auth list
```

💡 **Pick a region deliberately.** A Dataproc cluster's region determines where the
master, workers, **and** the cluster's staging bucket live. Moving it later means
recreating everything. `us-central1` has the widest machine-type availability;
`europe-west1` is closer if you are in Europe and your data has residency
requirements.

---

## 3. Enable the required APIs

```bash
gcloud services enable \
  dataproc.googleapis.com \
  storage.googleapis.com \
  bigquery.googleapis.com \
  bigquerystorage.googleapis.com \
  cloudresourcemanager.googleapis.com \
  composer.googleapis.com \
  compute.googleapis.com
```

Verify:

```bash
gcloud services list --enabled | grep -E "dataproc|storage|bigquery|resourcemanager|composer"
```

⚠️ **Composer is only needed for the orchestration chapter.** You do not need to
create a Composer environment to complete the core course. Enable it anyway — the
API enablement is free, and only the environment costs money.

---

## 4. Set up a Python environment

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-Course/google/dataproc

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r resources/requirements.txt
```

Verify:

```bash
python -c "import pyspark, pandas, google.cloud.bigquery; print(pyspark.__version__)"
```

---

## 5. Create a service account

You need **two** identities, and they have different jobs:

| Identity | Runs as | Needs |
|----------|---------|-------|
| **Cluster SA** (`dataproc-cluster-sa`) | The cluster's VMs — your Spark code | `roles/dataproc.worker`, bucket access, BigQuery access |
| **Pipeline SA** (`dataproc-pipeline-sa`) | CI/CD jobs that submit work | `roles/dataproc.editor`, `roles/bigquery.jobUser` |

💡 **Why two?** The cluster SA is the identity your Spark executors use when they
read GCS and write BigQuery. The pipeline SA is the identity that *creates clusters
and submits jobs*. Mixing them means a compromised data-plane credential can
create more clusters — a cost attack.

```bash
PROJECT_ID=YOUR_PROJECT_ID

# The cluster's VM identity
gcloud iam service-accounts create dataproc-cluster-sa \
  --display-name="Dataproc Cluster Service Account" \
  --project=$PROJECT_ID

# The pipeline identity
gcloud iam service-accounts create dataproc-pipeline-sa \
  --display-name="Dataproc Pipeline Service Account" \
  --project=$PROJECT_ID
```

### 5.1 The real IAM role names

⚠️ **`roles/dataproc.developer` does not exist.** You will see it in older blog
posts, in AI-generated answers, and in interview questions. The actual
predefined Dataproc roles are:

| Role | Grants | Give it to |
|------|--------|------------|
| `roles/dataproc.admin` | Full control of Dataproc resources | Platform admins only |
| `roles/dataproc.editor` | View + manage clusters, jobs, operations | The pipeline SA, and engineers who create clusters |
| `roles/dataproc.viewer` | Read-only access to clusters, jobs, operations | Analysts, dashboards |
| `roles/dataproc.worker` | Worker / data-plane access | **The cluster's VM service account** |
| `roles/dataproc.serverlessEditor` | Manage serverless batches and sessions | Serverless users |
| `roles/dataproc.serverlessViewer` | Read-only serverless access | Observability |

⚠️ **There is no `roles/dataproc.clusterUser` either.** The granular permission
that plays that role is `dataproc.clusters.use` — it lets a principal run jobs on
a cluster without letting them create or delete it. `roles/dataproc.editor`
includes it.

The other roles this course uses:

| Role | Grants |
|------|--------|
| `roles/storage.objectAdmin` | Full control of objects in a bucket |
| `roles/storage.objectViewer` | Read objects in a bucket |
| `roles/storage.legacyBucketReader` | List buckets (needed by some tools) |
| `roles/bigquery.jobUser` | Run jobs (queries, loads) — without it you get `403 Access Denied` on any query |
| `roles/bigquery.dataEditor` | Read + write table data |
| `roles/bigquery.dataViewer` | Read table data |
| `roles/iam.serviceAccountUser` | **Act as** a service account — required to create a cluster with that SA |

### 5.2 Grant the cluster service account its roles

```bash
PROJECT_ID=YOUR_PROJECT_ID
CLUSTER_SA="dataproc-cluster-sa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLUSTER_SA}" \
  --role="roles/dataproc.worker"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLUSTER_SA}" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLUSTER_SA}" \
  --role="roles/bigquery.dataEditor"
```

### 5.3 Grant the pipeline service account its roles

```bash
PROJECT_ID=YOUR_PROJECT_ID
PIPELINE_SA="dataproc-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PIPELINE_SA}" \
  --role="roles/dataproc.editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PIPELINE_SA}" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PIPELINE_SA}" \
  --role="roles/bigquery.dataEditor"
```

### 5.4 Allow your user to act as the cluster service account

```bash
PROJECT_ID=YOUR_PROJECT_ID
CLUSTER_SA="dataproc-cluster-sa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts add-iam-policy-binding $CLUSTER_SA \
  --member="user:YOUR_EMAIL@example.com" \
  --role="roles/iam.serviceAccountUser" \
  --project=$PROJECT_ID
```

⚠️ **This step is the one that bites.** To create a cluster, the caller must be
able to *act as* the cluster's VM service account. Forget it and you get a
permission error that mentions nothing about Dataproc:

```
PERMISSION_DENIED: User ... does not have permission to use service account
```

### 5.5 Bucket-scoped access (least privilege)

Grant the storage role **on the bucket**, not on the project. A project-level
`roles/storage.objectAdmin` gives the SA write access to every bucket in the
project — including your other projects' buckets if they share the project.

```bash
PROJECT_ID=YOUR_PROJECT_ID
CLUSTER_SA="dataproc-cluster-sa@${PROJECT_ID}.iam.gserviceaccount.com"
BUCKET="gs://${PROJECT_ID}-dataproc-data"

gcloud storage buckets add-iam-policy-binding $BUCKET \
  --member="serviceAccount:${CLUSTER_SA}" \
  --role="roles/storage.objectAdmin"

# Read-only on the raw landing zone
gcloud storage buckets add-iam-policy-binding gs://${PROJECT_ID}-dataproc-raw \
  --member="serviceAccount:${CLUSTER_SA}" \
  --role="roles/storage.objectViewer"
```

⚠️ **Never download a service-account key to your laptop.** For local
development, use impersonation:

```bash
gcloud auth application-default login \
  --impersonate-service-account=dataproc-pipeline-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

---

## 6. Create the Cloud Storage buckets

```bash
PROJECT_ID=YOUR_PROJECT_ID

# The main data lake
gcloud storage buckets create gs://${PROJECT_ID}-dataproc-data \
  --location=us-central1 \
  --uniform-bucket-level-access

# The raw landing zone (append-only)
gcloud storage buckets create gs://${PROJECT_ID}-dataproc-raw \
  --location=us-central1 \
  --uniform-bucket-level-access

# The quarantine area
gcloud storage buckets create gs://${PROJECT_ID}-dataproc-quarantine \
  --location=us-central1 \
  --uniform-bucket-level-access

# A TEMPORARY bucket for BigQuery load-job staging
gcloud storage buckets create gs://${PROJECT_ID}-bq-staging \
  --location=us-central1 \
  --uniform-bucket-level-access \
  --lifecycle-configuration=temp-bucket-lifecycle.json
```

💡 **Why a separate temporary bucket for BigQuery loads?** The BigQuery
connector writes Parquet to GCS, then issues a LOAD job pointing at those
files. The files are intermediate, not data. Putting them in a dedicated bucket
with a lifecycle rule that deletes them after 1 day means:
- They never get mixed up with your real data.
- They are cleaned up automatically, so storage does not creep up.
- You can give the pipeline SA write access to the staging bucket only.

The lifecycle file (`temp-bucket-lifecycle.json`):

```json
[
  {
    "action": { "type": "Delete" },
    "condition": { "age": 1 }
  }
]
```

⚠️ **Do not use the cluster's auto-created staging bucket for BigQuery loads.**
Dataproc creates one per cluster, it is deleted with the cluster, and its IAM
bindings are managed by Dataproc. Point the connector at your own bucket.

Folder layout:

```
gs://YOUR_PROJECT_ID-dataproc-raw/
├── pos/                 # inbound POS extracts
├── claims/              # inbound claims NDJSON
├── product_master/      # dimension source
└── provider_master/     # dimension source

gs://YOUR_PROJECT_ID-dataproc-data/
├── silver/              # conformed dimensions
├── gold/                # facts
├── mart/                # serving tables
└── checkpoints/         # Spark checkpoint output

gs://YOUR_PROJECT_ID-dataproc-quarantine/
├── sales/
└── claims/

gs://YOUR_PROJECT_ID-bq-staging/
└── (transient — deleted by the lifecycle rule)
```

---

## 7. Create your first cluster

⚠️ **COST WARNING — read this before you run the next command.**

A Dataproc cluster bills **from the moment it exists until it is deleted**,
whether or not a job is running. A 3-worker `n2-standard-4` cluster costs roughly
$3–4 per hour. Leaving one running over a weekend costs $50+. There is no
"pause" — a stopped cluster still bills for its disks.

**Three ways to never get a surprise bill:**

1. **Always set `--delete-max-idle`.** A cluster with no activity for 30 minutes
   deletes itself.
2. **Always set `--delete-max-age`.** A cluster older than 8 hours deletes itself.
3. **Create a temporary cluster per job** and let it self-destruct.

```bash
gcloud dataproc clusters create course-dev \
  --region=us-central1 \
  --image-version=2.2-debian12 \
  --master-machine-type=n2-standard-4 \
  --worker-machine-type=n2-standard-4 \
  --num-workers=2 \
  --num-secondary-workers=1 \
  --secondary-worker-type=spot \
  --service-account=dataproc-cluster-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --delete-max-idle=30m \
  --delete-max-age=8h \
  --labels=env=dev,course=dataproc,owner=student
```

⚠️ **Always set `--scopes=https://www.googleapis.com/auth/cloud-platform`.**
The default Compute Engine scope list is the legacy one and does **not** include
BigQuery or Cloud Storage write access. A job that works perfectly in Jupyter
fails on submission. This is the single most common "works locally, fails in
the cluster" bug in Dataproc.

⚠️ **Always pin `--image-version`.** Without it, gcloud uses the current
default image, which Google changes as new images reach GA. This course uses
**`2.2-debian12`** (Spark 3.5.3, supported until 2027-03-31) throughout.

---

## 8. Set a budget alert

Budgets do **not** cap your spending. They only send you an email. They are
still the single most effective safety net, because they tell you about the
cluster you forgot.

```bash
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT_ID \
  --display-name="Dataproc course budget" \
  --budget-amount=50 \
  --budget-threshold-type=0.5,0.9,1.0 \
  --threshold-rules="firebase:project=YOUR_PROJECT_ID:channel=email,amount=0.5,recipient=email@example.com" \
  --threshold-rules="firebase:project=YOUR_PROJECT_ID:channel=email,amount=0.9,recipient=email@example.com" \
  --threshold-rules="firebase:project=YOUR_PROJECT_ID:channel=email,amount=1.0,recipient=email@example.com"
```

Verify billing is enabled:

```bash
gcloud billing projects describe YOUR_PROJECT_ID
```

---

## 9. Create the BigQuery datasets

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-Course/google/dataproc

# Substitute your project ID first
sed -i '' 's/YOUR_PROJECT_ID/my-real-project/g' sql/*.sql

bq query --use_legacy_sql=false --dry_run < sql/01_bigquery_setup.sql
bq query --use_legacy_sql=false < sql/01_bigquery_setup.sql
bq query --use_legacy_sql=false < sql/02_dimensions.sql
bq query --use_legacy_sql=false < sql/03_fact_tables.sql
```

---

## 10. Generate and upload the sample data

```bash
# Locally
python resources/sample_data.py --output-dir=./sample_data --seed=42

# To GCS
gcloud storage cp -r sample_data/* gs://YOUR_PROJECT_ID-dataproc-raw/
```

---

## 🔐 Environment variables

Create a `.env` file (and add it to `.gitignore`):

```bash
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GCP_REGION=us-central1
GCP_ZONE=us-central1-a
DATAPROC_CLUSTER=course-dev
GCS_RAW_BUCKET=YOUR_PROJECT_ID-dataproc-raw
GCS_DATA_BUCKET=YOUR_PROJECT_ID-dataproc-data
GCS_QUARANTINE_BUCKET=YOUR_PROJECT_ID-dataproc-quarantine
GCS_BQ_STAGING_BUCKET=YOUR_PROJECT_ID-bq-staging
BQ_LOCATION=US
ENV=dev
```

---

## 🐍 Notebooks

```bash
jupyter lab notebooks/
```

The notebooks import the helper module from `resources/`. Either add that
directory to your `PYTHONPATH`, or copy the module into the notebook directory:

```bash
cp resources/spark_helpers.py notebooks/
```

---

## ✅ Verify everything

Run this checklist top to bottom. Each command should succeed.

```bash
PROJECT_ID=YOUR_PROJECT_ID

# 1. Auth and project
gcloud auth list --filter=status:ACTIVE --format="value(account)"
gcloud config get-value project

# 2. APIs enabled
gcloud services list --enabled --format="value(config.name)" | grep -E "dataproc|storage.googleapis.com|bigquery"

# 3. Billing
gcloud billing projects describe $PROJECT_ID | grep billingEnabled

# 4. Service accounts
gcloud iam service-accounts list --project=$PROJECT_ID

# 5. Role bindings on the cluster SA
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:dataproc-cluster-sa" \
  --format="value(bindings.role)"

# 6. Buckets
gcloud storage ls

# 7. BigQuery datasets
bq ls --project_id=$PROJECT_ID

# 8. Cluster is RUNNING
gcloud dataproc clusters list --region=us-central1 \
  --format="table(name,status,config.workerConfig.numInstances)"

# 9. Submit a trivial job
gcloud dataproc jobs submit pyspark --cluster=course-dev -- \
  -c "spark=spark.executor.memory=1g" \
  -c "spark=spark.executor.cores=1" \
  -c "spark=spark.executor.instances=2" \
  -c "spark=spark.yarn.maxAppAttempts=1" \
  -c "spark=spark.submit.deployMode=client" \
  "print('hello from dataproc')"
```

### Checklist

- [ ] `gcloud auth list` shows an active account
- [ ] `gcloud config get-value project` returns your project
- [ ] All required APIs are enabled
- [ ] Billing is enabled on the project
- [ ] `dataproc-cluster-sa` exists and has `roles/dataproc.worker`
- [ ] `dataproc-pipeline-sa` exists and has `roles/dataproc.editor`
- [ ] Your user has `roles/iam.serviceAccountUser` on the cluster SA
- [ ] Four buckets exist, with the staging bucket's lifecycle rule
- [ ] The seven BigQuery datasets exist
- [ ] The sample data is in the raw bucket
- [ ] A cluster reaches `RUNNING` state
- [ ] A test job completes with state `DONE`
- [ ] A budget alert is configured
- [ ] You know how to delete the cluster (below)

### The one command you must always remember

```bash
gcloud dataproc clusters delete course-dev --region=us-central1
```

---

## 🆘 Troubleshooting

| Problem | Fix |
|---------|-----|
| `PERMISSION_DENIED: ... does not have permission to use service account` | Grant `roles/iam.serviceAccountUser` on the cluster SA to yourself (step 5.4) |
| `PERMISSION_DENIED: ... dataproc.clusters.create` | Grant `roles/dataproc.editor` to your user or the pipeline SA |
| `Access Denied: BigQuery: User ... does not have permission to run a job` | Grant `roles/bigquery.jobUser` |
| `google.api_core.exceptions.Forbidden: 403 ... storage.buckets.get` | Grant `roles/storage.objectViewer` on the bucket |
| Job fails with `403 ... BigQuery Storage Write API` | Add `--scopes=https://www.googleapis.com/auth/cloud-platform` |
| `gcloud: command not found` | Add the SDK's `bin` to your `PATH` |
| `AccessDeniedException: Vertex ... does not have ...` on cluster create | The API is not enabled; run step 3 |
| Cluster creation fails after 10 minutes | Check `gcloud dataproc operations list` — usually a quota or a network route issue |
| `DEFAULT_NOT_FOUND: Table ... not found` | The dataset/region is wrong; check `bq ls` |
| Python `ImportError: pandas` in Jupyter | `pip install pandas pyarrow` then restart the kernel |
| `spark.driver.memory` OOM | The driver runs on the master; do not `collect()` large results |
| `JobStatus.state` is `SUCCEEDED` | It is not — the API states are `DONE` and `ERROR` |

---

## 📖 Next steps

- Chapter `02-dataproc-cluster-creation-and-management.md` — clusters in depth
- Chapter `03-submitting-jobs-to-dataproc.md` — running your first job
- `sql/01_bigquery_setup.sql` — the BigQuery side of the setup
- `resources/CHEATSHEET.md` — the command reference
- `resources/FAQ.md` — the questions students actually ask
