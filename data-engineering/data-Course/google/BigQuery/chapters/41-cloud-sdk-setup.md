# 6.1 — Cloud SDK Setup

> **Section 6 · Command Line Interface · Lecture 6.1 · 3:37**

## 🎯 What you will learn

- Install and authenticate the Google Cloud CLI
- Set up project defaults and the `bq` command specifically
- Service account authentication for automation
- Configure `bq` defaults with `.bqrc`

---

## 🧠 Concept

The `bq` command-line tool is the official BigQuery CLI. It ships with the Google Cloud SDK and
gives you full control over jobs, datasets, and tables from a terminal or a script.

### Install the Cloud SDK

```bash
# macOS (Homebrew)
brew install --cask google-cloud-sdk

# macOS (installer)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Linux
sudo apt-get install apt-transport-https python3-pip python3-venv
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Windows
# Download the installer from https://cloud.google.com/sdk/docs/install

# Verify
gcloud version
```

### Authenticate

```bash
# For interactive development — opens a browser
gcloud auth login

# Application Default Credentials (used by the Python SDK and bq)
gcloud auth application-default login

# Verify
gcloud auth list
```

### Configure the project

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud config set compute/region us-central1
gcloud config set billing/quota_project YOUR_PROJECT_ID

# Verify
gcloud config list
```

💡 **Always set a quota project explicitly** if you use a shared credentials file. Without it,
the `bq` command may pick the wrong project for quota and billing purposes.

### `bq` specific setup

```bash
# The default project for bq
bq config set project_id YOUR_PROJECT_ID

# Or simply rely on gcloud config
bq ls --project_id=YOUR_PROJECT_ID

# Set a default location for new datasets
bq config set default_dataset_location US
```

### `.bqrc` — your personal defaults

```bash
cat > ~/.bqrc <<'EOF'
--project_id=YOUR_PROJECT_ID
--max_bytes_billed=10000000000
--format=prettyjson
EOF
```

| Setting | Purpose |
|---------|---------|
| `--project_id` | Default project |
| `--max_bytes_billed` | **Safety cap on every query** |
| `--format` | Default output format |
| `--use_legacy_sql=false` | Always GoogleSQL |

💡 **`--max_bytes_billed` in `.bqrc` is the single most valuable line you can add.** It caps every
query you run from the CLI. A cartesian join will fail in seconds instead of costing hundreds.

### Service account authentication (for automation)

```bash
# Create a service account
gcloud iam service-accounts create bq-pipeline \
    --display-name="BigQuery Pipeline"

# Grant the minimal role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:bq-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

# Create and download the key
gcloud iam service-accounts keys create ./bq-pipeline-key.json \
    --iam-account="bq-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com"

export GOOGLE_APPLICATION_CREDENTIALS="$PWD/bq-pipeline-key.json"
```

⚠️ **Never commit the key file.** Add it to `.gitignore`:
```
bq-pipeline-key.json
*.key.json
```

### Service account impersonation (the safer pattern)

Instead of a key file, use impersonation:

```bash
gcloud auth application-default login \
    --impersonate-service-account=bq-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

💡 **Impersonation eliminates key files entirely.** The credentials never live on disk. This is
the modern recommended pattern for local development against production.

### In CI/CD

```yaml
# GitHub Actions
- uses: google-github-actions/auth@v2
  with:
    credentials_json: ${{ secrets.GCP_SA_KEY }}

- name: Run BigQuery query
  run: |
    bq query --use_legacy_sql=false --max_bytes_billed=1000000000 \
      'SELECT COUNT(*) FROM `proj.dataset.table`'
```

---

## 🛠️ Hands-On: Verify Your Setup

```bash
# 1. gcloud works
gcloud version

# 2. Auth is active
gcloud auth list --filter=status:ACTIVE --format="table(account)"

# 3. bq is installed
bq version

# 4. bq can see your project
bq ls --max_results=5

# 5. Run a real query
bq query --use_legacy_sql=false --dry_run \
  'SELECT COUNT(*) FROM `bigquery-public-data.samples.shakespeare`'

# 6. Your defaults are set
bq config list
```

---

## 💡 Production Notes

- **Set `--max_bytes_billed` globally.** It costs nothing and prevents the most common
  catastrophic mistake.
- **Use a dedicated service account per workload** (per pipeline, per environment). Shared
  credentials make cost attribution and revocation impossible.
- **Prefer impersonation over key files** in local development.
- **Rotate keys** if you must use them — and prefer the IAM Credentials API for machine-to-machine
  auth on GCP.
- **`bq` is scriptable.** Everything in this module is designed to be piped, looped, and run from
  CI.

---

## 🔑 Key Takeaways

- Install the Cloud SDK; `bq` ships with it.
- `gcloud auth application-default login` sets up both the CLI and the Python SDK.
- **`.bqrc` with `--max_bytes_billed` is the highest-value configuration line.**
- Use service accounts for automation; use impersonation instead of key files where possible.
- Set the quota project explicitly in shared-credential environments.

---

## 📚 Practice Exercises

1. **Environment setup.** Write a `setup.sh` script that: installs the SDK (if needed),
   authenticates, sets the project, and writes a `.bqrc` with a byte cap. Make it idempotent.

2. **Credential hygiene.** Write a script that detects whether any service account key file is
   staged for commit, and fails the build if so. Include the `git` check.

3. **Impersonation setup.** Configure local development to use impersonation instead of a key
   file. Verify that `bq` and the Python SDK both work.

4. **CI pipeline.** Write a GitHub Actions workflow that authenticates with a service account and
   runs a BigQuery DDL + query, failing the build on error.

---

## 📖 Further Reading

- Cloud SDK install — https://cloud.google.com/sdk/docs/install
- `bq` reference — https://cloud.google.com/bigquery/docs/reference/bq-cli-reference
- Service account impersonation — https://cloud.google.com/iam/docs/impersonating-service-accounts
