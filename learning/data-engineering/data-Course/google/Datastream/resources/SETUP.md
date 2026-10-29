# Setup Guide

> Everything in this course runs **locally with no GCP account, no credentials, and no bill**.
> The cloud sections are optional — read them when you want to deploy.

---

## The 5-minute path (no GCP required)

This is the path the course assumes. Everything in it works offline after the
first install.

```bash
cd data-engineering/data-Course/google/Datastream

python3 -m venv .venv
source .venv/bin/activate

pip install -r project/requirements.txt

# Generate the deterministic dataset
python resources/sample_data.py --output-dir ./sample_data

# Run the CDC replay — no cloud, no credentials
python project/cdc_pipeline.py \
    --input ./sample_data/changes.ndjson \
    --output ./out/customers \
    --merge-keys customer_id

# Run the Kafka-side ingest against the same messages (dry run: no database)
python project/kafka_to_gcp.py \
    --messages ./sample_data/transactions.ndjson \
    --dry-run
```

Expected CDC replay summary:

```text
  CDC replay summary
  ----------------------------------------------------
    events read          : 377
    rows in table        : 186
    changes applied      : 374
    events skipped       : 8
    skip reasons:
      delete_of_absent_row      : 2
      duplicate_insert          : 5
      missing_merge_key         : 1
```

Expected Kafka replay summary:

```text
  Kafka → GCP replay summary
  ----------------------------------------------------
    messages read    : 500
    ingested         : 500
    rejected         : 0
```

### Python version

**3.10–3.13.** The course was developed and tested on **Python 3.13**. Check
yours:

```bash
python3 --version
```

> **Why this matters.** The merge logic in `project/cdc.py` uses
> `from __future__ import annotations` and PEP 604 unions in annotations.
> On 3.9 the `X | None` syntax in *annotations* still works (because of the
> future import) but not in runtime expressions like `isinstance(x, int | str)`.

---

## Installing the course tools

```bash
pip install -r project/requirements.txt
```

That installs:

| Package | Why |
|---|---|
| `google-cloud-bigquery` | reading the destination in the BigQuery chapters |
| `google-cloud-secretmanager` | the Secret Manager chapter and the Kafka path |
| `psycopg2-binary` | the Cloud SQL / PostgreSQL path |
| `pytest` | the test suites |

### The optional extras

The core pipeline is **pure standard library** — `project/cdc.py` imports
nothing outside the stdlib. That is deliberate: the merge semantics are the
hard part, and they must be testable without a network.

```bash
pip install google-cloud-datastream-types   # typed stream configs
pip install google-cloud-bigquery-storage    # the bqstorage API
```

---

## Running the tests

```bash
pytest project/tests -q
```

Expected:

```text
82 passed, 1 skipped
```

The one skip is the Secret Manager test, which requires the SDK and
credentials to be installed. Everything else — the merge semantics, the
Kafka parsing, the SQL generation, the parameterisation guarantee — runs
offline.

---

## Running the notebooks

```bash
pip install jupyter nbclient nbformat ipykernel

jupyter lab
```

Or, headless, to confirm every notebook executes end to end:

```bash
python resources/build_notebooks.py --check   # the sources are in sync
python resources/run_notebooks.py              # execute every notebook
```

The notebooks are **generated** from `resources/notebook_0*.py` so that the
course linter can parse every code cell. Edit the builder, not the `.ipynb`.

---

## Running the linter

```bash
python resources/audit_course.py
```

It checks that every notebook parses, every Python snippet in every chapter
is valid Python, every referenced GCP SDK attribute actually exists, every
relative link resolves, and no unresolved marker or placeholder text is left
behind in a code block.

Expected output:

```text
ERRORS:   0
WARNINGS: 0
INFO:     ...
```

---

---

## Setting up a GCP project (optional)

Read this section when you want to actually deploy.

### 1. Create the project

```bash
gcloud projects create YOUR_PROJECT_ID --name="Datastream Course"
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable the APIs

```bash
gcloud services enable \
    datastream.googleapis.com \
    bigquery.googleapis.com \
    secretmanager.googleapis.com \
    run.googleapis.com \
    cloudfunctions.googleapis.com \
    sqladmin.googleapis.com \
    compute.googleapis.com
```

### 3. Enable billing

```bash
gcloud billing accounts list
gcloud billing projects link YOUR_PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

> Datastream and BigQuery both bill by volume. A forgotten stream left
> running against a chatty table is a real invoice. Set a budget alert
> before you create the stream, not after.

### 4. Create the Datastream service account

```bash
gcloud iam service-accounts create datastream-sa \
    --display-name="Datastream service account"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:datastream-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastream.serviceAgent"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:datastream-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:datastream-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastream.reader"
```

### 5. Create the network config and IP allocation

```bash
gcloud datastream network-configs create network-config \
    --location=us-central1 \
    --network="projects/YOUR_PROJECT_ID/global/networks/default"

gcloud datastream network-configs ip-pools create ip-pool \
    --location=us-central1 \
    --network-config=network-config \
    --ip-address=10.0.0.2/28 \
    --name="ip-pool"
```

> **The IP allocation's address is not the Datastream service's outbound
> IP.** Your source database's firewall must allow the *allocation*. This
> is the most common first-run failure, and it presents as a **timeout**,
> not a refusal.

### 6. Prepare the source

**MySQL:**

```sql
SHOW VARIABLES LIKE 'binlog_format';      -- ROW
SHOW VARIABLES LIKE 'binlog_row_image';   -- FULL

CREATE USER 'datastream_user'@'%' IDENTIFIED BY '...';
GRANT SELECT, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'datastream_user'@'%';
```

**Postgres:**

```sql
ALTER SYSTEM SET wal_level = logical;
SELECT pg_reload_conf();

CREATE USER datastream_user WITH REPLICATION;
GRANT pg_read_all_data TO datastream_user;
GRANT USAGE ON SCHEMA public TO datastream_user;
```

### 7. Create the source config, destination config, and stream

The Terraform in `project/terraform/` does exactly this. Or by hand:

```bash
gcloud datastream source-configs create mysql-source \
    --location=us-central1 \
    --source-config-type=mysql-source \
    --mysql-source-config="host=10.0.0.3,port=3306,username=datastream_user,password=...,network=ip-pool"

gcloud datastream destination-configs create bigquery-destination \
    --location=us-central1 \
    --destination-config-type=bigquery-destination \
    --bigquery-destination-config="datasetId=datastream"

gcloud datastream streams create my-stream \
    --location=us-central1 \
    --source-config=mysql-source \
    --destination-config=bigquery-destination \
    --display-name="Customers CDC" \
    --backfill-all
```

### 8. Apply the destination schema

```bash
bq query --use_legacy_sql=false < sql/create_customers.sql
```

> The destination table must exist and must be **empty** before the backfill
> runs. If the stream starts against a table with rows in it, you get
> duplicates that no merge can resolve.

---

## The Kafka path (optional)

### Confluent Cloud

1. Create a cluster and a Kafka topic.
2. **Set retention on the topic.** The default is unbounded, and unbounded
   retention on a high-volume topic is an unbounded bill.
3. Create a Kafka Connect cluster and add the **Google Cloud Functions
   sink connector**.
4. Point it at your topic, your Cloud Run function's URL, and the auth
   credentials.

### The Cloud Run function

```bash
gcloud functions deploy ingest-transaction \
    --gen2 \
    --runtime python312 \
    --region us-central1 \
    --source project/ \
    --entry-point handle_event \
    --trigger-http \
    --no-allow-unauthenticated \
    --set-env-vars="INSTANCE_CONNECTION_NAME=YOUR_PROJECT:us-central1:INSTANCE,DB_NAME=transactions" \
    --set-secrets="DB_PASSWORD=db-password:latest" \
    --min-instances 1
```

> `--min-instances` keeps the instance warm. It costs money continuously, and
> it is a deliberate trade: you are paying for warm capacity to meet a
> latency SLA. Without it, a cold start lands on a real message and the
> consumer's offset does not advance until the function returns.

### The database password

```bash
echo -n 'the-password' | gcloud secrets create db-password --data-file=-
gcloud secrets versions add db-password --data-file=-
```

> **Never** use `--set-env-vars` for the password itself, and never put it
> in the source or in a `Dockerfile` `ENV` line. `--set-secrets` mounts it
> at runtime; `--set-env-vars` writes it into the function's configuration,
> where anyone with IAM access can read it.

---

## Terraform (optional)

```bash
cd project/terraform

terraform init
terraform plan -var="project_id=YOUR_PROJECT_ID" \
               -var="region=us-central1" \
               -var="mysql_host=10.0.0.3" \
               -var="mysql_username=datastream_user" \
               -var="mysql_password=..." \
               -var="merge_keys=[\"customer_id\"]"

terraform apply
```

The `mysql_password` is a sensitive variable — mark it `sensitive = true` in
`variables.tf` and never commit a `terraform.tfvars` containing it.

---

---

## Troubleshooting the setup

| Symptom | Cause | Fix |
|---|---|---|
| The stream stays `READY` but nothing arrives | The replication user's password expired | `SHOW GRANTS FOR 'datastream_user'@'%'` |
| The connection **times out** | The firewall does not allow the IP allocation | Open the allocation's address, not the service's outbound IP |
| The connection is **refused** | Wrong host, wrong port, or nothing listening | Check the connection profile |
| `Too many table update operations` | The merge exceeds BigQuery's per-table DML quota | Batch the changes; cluster on the merge key |
| Duplicates in the destination | The merge key is not unique, or the backfill ran into a non-empty table | Fix the merge key; drop, recreate, re-backfill |
| `NOT MATCHED BY SOURCE` empties the table | A synchronised merge on a stream | Remove the clause; use explicit delete events |
| The function returns 500 for a malformed payload | The status code is inverted | 4xx for permanent failures, 5xx for transient ones |
| `psycopg2.errors.UniqueViolation` on every message | A redelivery, and the constraint is doing its job | Catch it and treat it as success |

---

## Where to go next

- The chapters — [../chapters/](../chapters/)
- The interview bank — [../interview/](../interview/)
- The one-page reference — [CHEATSHEET.md](CHEATSHEET.md)
- The questions students actually ask — [FAQ.md](FAQ.md)
