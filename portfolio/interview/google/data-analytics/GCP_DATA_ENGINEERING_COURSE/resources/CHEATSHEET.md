# Cheat Sheet

Dense reference for the whole course. Numbers are us-central1 list prices as of the course's `cost_model.py`.

## 📟 gcloud Commands

### Project and configuration

```text
gcloud config set project PROJECT_ID
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
gcloud config list
gcloud auth login
gcloud auth application-default login
gcloud projects create PROJECT_ID --name="NAME"
gcloud projects list
gcloud projects delete PROJECT_ID --quiet
gcloud projects describe PROJECT_ID
```

### Service accounts

```text
gcloud iam service-accounts create pipeline-sa --display-name="Pipeline SA"
gcloud iam service-accounts list
gcloud iam service-accounts keys list iam.gserviceaccount.com/pipeline-sa@PROJECT_ID.iam.gserviceaccount.com
gcloud iam service-accounts keys create KEY_NAME --iam-account=pipeline-sa@PROJECT_ID.iam.gserviceaccount.com
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:pipeline-sa@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/bigquery.dataEditor
gcloud projects get-iam-policy PROJECT_ID
gcloud auth print-access-token
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:pipeline-sa@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/iam.serviceAccountUser
```

### Cloud Storage

```text
gsutil mb -l us-central1 -b on gs://BUCKET
gsutil ls gs://BUCKET
gsutil cp sample_data/events.csv gs://BUCKET/
gsutil rs -r gs://SOURCE gs://DEST
gsutil rm -r gs://BUCKET
gsutil versioning set on gs://BUCKET
gsutil lifecycle set - gs://BUCKET <<< '{"rule":[{"action":{"type":"SetStorageClass","storageClass":"NEARLINE"},"condition":{"age":30}}]}'
gsutil du -sh gs://BUCKET
```

### BigQuery

```text
bq mk --location=us-central1 --time_partitioning_field=event_date PROJECT_ID:DATASET
bq ls --project_id=PROJECT_ID
bq show --format=table PROJECT_ID:DATASET.TABLE
bq query --use_legacy_sql=false --dry_run 'SELECT * FROM PROJECT_ID:DATASET.TABLE'
bq query --use_legacy_sql=false --destination_table=PROJECT_ID:DATASET.OUT 'SELECT ...'
bq mk --external --source_format=CSV PROJECT_ID:DATASET.EXTERNAL
bq load --source_format=CSV PROJECT_ID:DATASET.TABLE gs://BUCKET/data.csv
bq rm -f -t PROJECT_ID:DATASET.TABLE
bq add-iam-policy-binding --member=user:USER@DOMAIN --role=roles/bigquery.dataViewer PROJECT_ID:DATASET
```

### Pub/Sub

```text
gcloud pubsub topics create TOPIC --region=us-central1
gcloud pubsub topics list
gcloud pubsub subscriptions create SUB --topic=TOPIC --region=us-central1
gcloud pubsub subscriptions create SUB --topic=TOPIC --ack-deadline=60 --message-retention-duration=7d
gcloud pubsub subscriptions create SUB --topic=TOPIC --dead-letter-topic=DLQ --max-delivery-attempts=10
gcloud pubsub topics publish TOPIC --message="hello"
gcloud pubsub subscriptions pull SUB --max-messages=10
gcloud pubsub subscriptions ack SUB --ack-id=ACK_ID
gcloud pubsub subscriptions seek SUB --time=2026-01-15T00:00:00Z
gcloud pubsub topics delete TOPIC
```

### Dataflow

```text
gcloud dataflow jobs run JOB_NAME \
  --runner=DataflowRunner \
  --project=PROJECT_ID \
  --region=us-central1 \
  --temp_location=gs://BUCKET/tmp \
  --staging_location=gs://BUCKET/staging \
  --streaming
gcloud dataflow jobs list
gcloud dataflow jobs show JOB_ID
gcloud dataflow jobs cancel JOB_ID
gcloud dataflow jobs dump JOB_ID
```

### Dataproc

```text
gcloud dataproc clusters create CLUSTER_NAME \
  --region=us-central1 --zone=us-central1-a \
  --master-machine-type=standard \
  --worker-machine-type=standard \
  --num-workers=2 \
  --initialization-action-timeout=600
gcloud dataproc clusters list
gcloud dataproc clusters describe CLUSTER_NAME
gcloud dataproc jobs submit pyspark JOB.py --cluster=CLUSTER_NAME -- --date=2026-01-15
gcloud dataproc clusters delete CLUSTER_NAME --quiet
```

### Cloud Composer

```text
gcloud composer environments create ENV_NAME \
  --location=us-central1 \
  --image-version=composer-2
gcloud composer environments list --location=us-central1
gcloud composer environments describe ENV_NAME --location=us-central1
gcloud composer environments update ENV_NAME --location=us-central1 --python-version=3.11
gcloud composer environments delete ENV_NAME --location=us-central1 --quiet
```

### Cloud Run and Cloud Run functions

```text
gcloud run deploy SERVICE --image=IMAGE --region=us-central1 --no-allow-unauthenticated
gcloud run deploy SERVICE --image=IMAGE --region=us-central1 --service-account=pipeline-sa@PROJECT_ID.iam.gserviceaccount.com --set-env-vars ENV=us-central1
gcloud run services list --region=us-central1
gcloud run services describe SERVICE --region=us-central1
gcloud run services logs tail SERVICE --region=us-central1
gcloud run services delete SERVICE --region=us-central1

gcloud functions deploy FUNCTION \
  --gen2 --runtime=python311 --region=us-central1 \
  --source=. --entry-point=handler \
  --trigger-topic=TOPIC \
  --service-account=pipeline-sa@PROJECT_ID.iam.gserviceaccount.com
gcloud functions list
gcloud functions delete FUNCTION --region=us-central1
```

### SQL and Cloud SQL

```text
gcloud sql instances create INSTANCE --database-version=POSTGRES_15 --tier=db-f1-micro --region=us-central1
gcloud sql instances list
gcloud sql databases create DATABASE --instance=INSTANCE
gcloud sql users set-password PASSWORD --instance=INSTANCE --user=USER
gcloud sql connect INSTANCE --user=USER --database=DATABASE
gcloud sql instances patch INSTANCE --backup-start-time=02:00
gcloud sql instances delete INSTANCE
```

### Dataplex, Data Catalog, Sensitive Data Protection

```text
gcloud dataplex lakes create LAKE --location=us-central1 --display-name="Events Lake"
gcloud dataplex zones create ZONE --location=us-central1 --lake=LAKE --display-name="Raw Zone"
gcloud dataplex assets create ASSET --location=us-central1 --zone=ZONE --display-name="Raw Events"
gcloud dataplex catalog create CATALOG --location=us-central1 --display-name="Events Catalog"

gcloud data-catalog entries create --location=us-central1 \
  --entry-group=@projects/PROJECT_ID/locations/us-central1/entryGroups/@bigquery \
  --entry-id=events --entry-type=bigquery.googleapis.com/Table \
  --entry-description="Raw events"

gcloud sdp deidentify --location=us-central1 \
  --deidentify-config-file=config.json \
  --input-file=input.json \
  --output-file=output.json
```

### Datastream, Transfer, Migration, Vertex AI

```text
gcloud datastream streams create STREAM --location=us-central1 --display-name="MySQL CDC"
gcloud datastream streams list --location=us-central1

gcloud transfer jobs create S3_TO_GCS --source-s3-bucket=OLD_BUCKET \
  --destination-gcs-bucket=gs://NEW_BUCKET --schedule-frequency=24h
gcloud transfer jobs list

gcloud database migration create-target --region=us-central1 --source-type=POSTGRES
gcloud database migration create --migration-job=... --source=...

gcloud ai endpoints create ENDPOINT --region=us-central1 --display-name="Churn"
gcloud ai models list --region=us-central1
gcloud ai custom-jobs create --region=us-central1 --display-name="Training"
```

### Monitoring and logging

```text
gcloud logging read 'severity>=ERROR' --limit=50 --project=PROJECT_ID
gcloud monitoring dashboards list
gcloud monitoring alert-policies list
gcloud logging buckets list
```

## 🎯 Service Selection

| If the workload is… | Pick | Chapter |
|---|---|---|
| Analysing tabular data at petabyte scale | BigQuery | [13](../chapters/13-bigquery-platform-overview.md) |
| Open-format tables on object storage | BigLake | [15](../chapters/15-biglake-dataplex-and-data-catalog.md) |
| Landing raw files durably and cheaply | Cloud Storage | [06](../chapters/06-cloud-storage.md) |
| Relational OLTP with familiar SQL | Cloud SQL | [08](../chapters/08-cloud-sql.md) |
| Relational OLTP at global scale | Cloud Spanner | [09](../chapters/09-cloud-spanner.md) |
| Wide-column key-value at high read volume | Bigtable | [10](../chapters/10-nosql-bigtable-datastore-firestore-memorystore.md) |
| Document entities for an application | Datastore or Firestore | [10](../chapters/10-nosql-bigtable-datastore-firestore-memorystore.md) |
| Sub-millisecond cache in front of a database | Memorystore | [10](../chapters/10-nosql-bigtable-datastore-firestore-memorystore.md) |
| Decoupling producers from consumers | Pub/Sub | [17](../chapters/17-pubsub.md) |
| High-throughput streaming with a Kafka API | Kafka (Confluent Cloud) | [16](../chapters/16-kafka-and-the-streaming-model.md) |
| Change data capture from a database | Datastream | [18](../chapters/18-datastream-and-cdc.md) |
| Batch or streaming Beam pipelines | Dataflow | [22](../chapters/22-apache-beam-and-dataflow.md) |
| Spark/Hadoop/Hive jobs | Dataproc | [21](../chapters/21-apache-spark-and-dataproc.md) |
| DAG-based scheduling | Cloud Composer | [23](../chapters/23-airflow-composer-and-workflows.md) |
| Event-driven API-call orchestration | Workflows | [23](../chapters/23-airflow-composer-and-workflows.md) |
| Version-controlled SQL transformations | Dataform | [24](../chapters/24-dataform-and-the-transformation-layer.md) |
| No-code pipelines and ETL | Data Fusion | [25](../chapters/25-cloud-data-fusion.md) |
| Browser-based visual data cleaning | Dataprep | [26](../chapters/26-cloud-dataprep.md) |
| Governance, lineage and discovery | Dataplex and Data Catalog | [15](../chapters/15-biglake-dataplex-and-data-catalog.md) |
| Finding and de-identifying PII | Sensitive Data Protection | [27](../chapters/27-sensitive-data-protection.md) |
| Dashboards for business users | Looker Studio | [29](../chapters/29-looker-studio-and-bi.md) |
| Custom model training and serving | Vertex AI | [32](../chapters/32-custom-training-and-vertex-ai.md) |
| Models trained in SQL | BigQuery ML | [33](../chapters/33-bigquery-ml.md) |
| Bulk object storage migration | Storage Transfer Service | [19](../chapters/19-transfer-services-and-migration.md) |
| Moving a database to Cloud SQL | Database Migration Service | [19](../chapters/19-transfer-services-and-migration.md) |

## 🔐 IAM Roles

23 roles are modelled in `iam_policy.py`. The 23 that matter most:

| Role | Grants | Use it when |
|---|---|---|
| `roles/owner` | Everything, including granting itself | Never in production. Break-glass only. |
| `roles/editor` | Read/write most resources, not IAM | Development, and nothing else. |
| `roles/viewer` | Read-only | Exploration, monitoring, audit. |
| `roles/storage.admin` | Full bucket and object control | The pipeline service account. |
| `roles/storage.objectViewer` | Read objects | BI and analyst roles. |
| `roles/storage.objectCreator` | Write objects, not read | A write-only ingest account. |
| `roles/bigquery.dataViewer` | Read datasets and table data | Analysts and Looker. |
| `roles/bigquery.dataEditor` | Read/write datasets and tables | The transformation service account. |
| `roles/bigquery.jobUser` | Run queries without seeing data | A BI account that only needs results. |
| `roles/pubsub.editor` | Full topic and subscription control | The pipeline service account. |
| `roles/pubsub.publisher` | Publish to topics | A producer that must not subscribe. |
| `roles/pubsub.subscriber` | Consume from subscriptions | A consumer that must not publish. |
| `roles/compute.admin` | Manage VM instances | Legacy workloads only. |
| `roles/container.admin` | Manage GKE clusters | Platform teams. |
| `roles/run.admin` | Manage Cloud Run services and jobs | The deployment service account. |
| `roles/cloudfunctions.admin` | Manage Cloud Run functions | The function deployment account. |
| `roles/iam.serviceAccountUser` | `iam.serviceAccounts.actAs` | The deployer who needs to attach an SA. |
| `roles/iam.serviceAccountAdmin` | Create and manage service accounts | Platform team only. |
| `roles/resourcemanager.projectIamAdmin` | Set project IAM policy | Security team only. |
| `roles/orgpolicy.policyAdmin` | Set org policies | Security team only. |
| `roles/datacatalog.admin` | Catalog entries and tag templates | The metadata service account. |
| `roles/dlp.user` | Inspect and de-identify | The privacy pipeline. |
| `roles/aiplatform.user` | Train models, call endpoints | The ML service account. |

Principles the course enforces:

- Separate producer and consumer: `roles/pubsub.publisher` never gets `roles/pubsub.subscriber`.
- `roles/bigquery.jobUser` plus `roles/bigquery.dataViewer` beats `roles/bigquery.dataEditor` for read-only analysts.
- `roles/iam.serviceAccountUser` is separate from the SA's own roles. A deployer needs it to *attach* an SA, not to *be* it.
- Never grant `roles/owner` to a workload identity. It can grant itself `roles/owner`.

## 💰 BigQuery Cost Formulas

### On-demand vs flat-rate

| Mode | Formula | 1 TB | 10 TB | 100 TB | 1 PB |
|---|---|---|---|---|---|
| On-demand | `scanned_TB × $6.25` | $6.25 | $62.50 | $625.00 | $6,250.00 |
| Flat-rate | `slot_hours × $0.06` | $6.00 (100 slots × 1h) | $60.00 (100 slots × 10h) | $600.00 | $6,000.00 |
| Capacity | `slot_hours × $0.06` | $0.00 (no cost until provisioned) | $0.00 | $0.00 | $0.00 |

Flat-rate breaks even against on-demand at roughly **100 TB scanned per 1000 slot-hours**. Below that, on-demand wins.

The free tier gives **1 TB scanned per month**, so the first TB is always $0.00.

### Partitioning and clustering

| Table | Bytes scanned | Cost at $6.25/TB |
|---|---|---|
| Unpartitioned, `SELECT *` | 1.00 TB | $6.25 |
| Partitioned, filter on the partition column | 0.01 TB | $0.0625 |
| Partitioned + clustered + selective predicate | 0.001 TB | $0.00625 |

Partitioning with a filter that selects 1% of the data cuts the cost **100×**. This is the single biggest lever in the course:

```text
$ python project/local_runner.py --compare

Same workload, different architectures
---------------------------------------
| Architecture | Monthly cost |
|---|---|
| Streaming on Dataflow | $0.0000 |
| Spark on Dataproc | $0.0000 |
| Batch on BigQuery (partitioned) | $0.0625 |
| Batch on BigQuery (unpartitioned) | $6.2500 |
```

### Storage

| Class | Per GB-month | Retrieval per GB | Read latency | Use for |
|---|---|---|---|---|
| Standard | $0.020 | $0.00 | Instant | Active data, the default |
| Nearline | $0.010 | $0.01 | < 1 second | Read once or twice a month |
| Coldline | $0.004 | $0.02 | < 1 second | Read quarterly |
| Archive | $0.0012 | $0.05 | Hours | Read yearly or never |

Archive is 16.7× cheaper than Standard to store, but 5× more expensive to read. A 1 TB archive read costs **$50** in retrieval. Never archive and then query it interactively.

### Other services

| Service | Unit | Price |
|---|---|---|
| Cloud Storage egress | per GB | $0.12 |
| Dataflow | per vCPU-hour | $0.0595 |
| Dataproc | per vCPU-hour | $0.0476 |
| Composer | per environment-node-hour | $0.0564 |
| Pub/Sub ingest | per GB | $0.40 |
| Dataprep | per user-hour | $0.60 |
| Vertex AI training | per node-hour | $3.67 |

### Free-tier allowances

| Service | Monthly allowance |
|---|---|
| Cloud Storage | 5 GB-month |
| Network egress | 1 GB |
| BigQuery on-demand | 1 TB scanned |
| Compute Engine | 0.25 vCPU-hour |
| Cloud Run | 2,000,000 requests and 180,000 CPU-seconds |
| Cloud Run functions | 2,000,000 invocations |
| Pub/Sub | 10 GB |
| Cloud SQL | $0.30 (EUR) |

## 🧩 Partitioning and Clustering Checklist

Before running a query over a large table, work down this list.

1. **Partition by a date or timestamp column.** Ingestion time (`_PARTITIONTIME`) is the default; event date (`event_date`) is better for late-arriving data.
2. **Always filter on the partition column.** `WHERE event_date = '2026-01-15'`. An unfiltered query scans everything.
3. **Avoid `SELECT *`.** List the columns. Storage is columnar, so you pay per column read.
4. **Cluster by the filter columns.** Up to four. Order matters: most selective first.
5. **Cluster on high-cardinality columns.** `customer_id`, `event_id` — not `country`.
6. **Do not cluster on low-cardinality columns.** A boolean column gives no benefit.
7. **Keep partitions small but not tiny.** Daily partitions over 1 GB and under 1 TB each.
8. **Set partition expiration.** Partitioned tables do not expire by default; only the data does.
9. **Avoid `SELECT COUNT(*)` on partitioned tables.** It scans every partition unless filtered.
10. **Materialise views for repeated aggregations.** A view that re-reads the base table costs the same every time.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import estimated_scan_bytes, estimated_scan_tb

rows = [{"event_date": "2026-01-15"} for _ in range(4800)]
partitioned = estimated_scan_bytes(rows, partitioned=True, partition_prune_ratio=0.01)
unpartitioned = estimated_scan_bytes(rows, partitioned=False)
print(f"partitioned: {partitioned:,} bytes")
print(f"unpartitioned: {unpartitioned:,} bytes")
print(f"unpartitioned TB: {estimated_scan_tb(rows, partitioned=False):.9f}")
```

Expected output:

```text
partitioned: 1,344 bytes
unpartitioned: 134,400 bytes
unpartitioned TB: 0.000000122
```

## 📬 Pub/Sub Delivery Types

| Type | Guarantees | Duplicates | Ordering | Use it for |
|---|---|---|---|---|
| At most once | Fire and forget | No | No | Telemetry where loss is acceptable |
| At least once | The message is retried until acked | Possible | No | The default for most pipelines |
| Exactly once | No duplicates | No | No | Billing, audit logs |

Exactly-once delivery is available **only for a pull subscriber** that acknowledges the message with an exactly-once-enabled subscription. It costs more and can be slower.

Ordering is separate from delivery guarantees. Pub/Sub supports **ordered delivery** per key (for example, per `customer_id`), and it only works when every publish and consume uses the same key.

Dead-letter configuration:

```text
gcloud pubsub subscriptions create SUB \
  --topic=TOPIC \
  --dead-letter-topic=DLQ \
  --dead-letter-topic-project=PROJECT_ID \
  --max-delivery-attempts=10
```

The message moves to the DLQ after 10 failed delivery attempts. The DLQ topic needs its own subscription, or the messages sit unread.

Push vs pull:

| | Push | Pull |
|---|---|---|
| Who runs the consumer | Pub/Sub | Your service |
| Scaling | Automatic | You manage it |
| Authentication | OIDC token to your endpoint | Your own credentials |
| Cost | Per delivery attempt | Per request, more control |
| Best for | Serverless endpoints, webhooks | Long-running consumers, Dataflow, batch |

## 📅 Airflow Logical Date

Airflow's `logical_date` is the **start of the data interval**, not the run time. A DAG scheduled at `2026-01-16T00:00:00` with a daily schedule has a logical date of `2026-01-15`.

| Concept | Meaning |
|---|---|
| Logical date | The start of the interval the run covers |
| Data interval | `[logical_date, next_execution_date)` |
| Execution date | When the scheduler actually starts the task — for `2026-01-15`, that is `2026-01-16` |
| `ds` | The logical date as `YYYY-MM-DD` |
| `macros.ds_add(ds, -1)` | The previous day |
| `data_interval_start` | The left edge of the interval |
| `data_interval_end` | The right edge — exclusive |

Consequences that catch people out:

- To process **yesterday's** data at 02:00 today, use `{{ macros.ds_add(ds, -1) }}`, not `{{ ds }}`.
- A backfill re-runs the same logical date, so the code must be **idempotent**. Write to a partition, not to "the latest".
- `ds` is always UTC unless the DAG says otherwise.
- Airflow 2.2+ replaced `execution_date` with `logical_date`. The old name still works but is deprecated.

## 🌍 Service Availability by Region

The course models 12 regions:

| Region | Location |
|---|---|
| `us-central1` | Iowa |
| `us-east1` | South Carolina |
| `us-east4` | Northern Virginia |
| `us-west1` | Oregon |
| `europe-west1` | Belgium |
| `europe-west2` | London |
| `europe-west4` | Netherlands |
| `asia-south1` | Mumbai |
| `asia-southeast1` | Singapore |
| `asia-northeast1` | Tokyo |
| `australia-southeast1` | Sydney |
| `southamerica-east1` | São Paulo |

Most services are available in all 12. The exceptions in the course's matrix:

| Service | Restricted regions | Status |
|---|---|---|
| BigQuery ML | `southamerica-east1` | Not available |
| Datastore | `asia-southeast1`, `southamerica-east1` | Limited, restricted |
| Memorystore | `southamerica-east1` | Limited |
| Kafka | `southamerica-east1` | Limited |
| Datastream | `asia-southeast1`, `southamerica-east1` | Limited |
| Data Fusion | `asia-southeast1`, `southamerica-east1` | Limited |
| Dataprep | `southamerica-east1` | Limited |
| Dataplex | `asia-southeast1`, `southamerica-east1` | Limited |
| BigLake | `southamerica-east1` | Limited |
| Bigtable | `southamerica-east1` | Limited |
| App Engine | `southamerica-east1` | Limited |

Regions and zones:

```text
gcloud compute regions list
gcloud compute zones list
gcloud compute zones list --filter="region:us-central1"
```

`us-central1` has zones `us-central1-a`, `us-central1-b`, `us-central1-c`. A zone is a physical deployment location within a region. Region-level services (BigQuery, Cloud Storage, Dataflow, Composer) have no zones; zonal services (Compute Engine, GKE) do.

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import regions_for, zones_in, nearest_region, services_available_in

print(regions_for("bigquery")[:3])
print(zones_in("us-central1"))
print(nearest_region("us-west1", "datastore"))
print(len(services_available_in("us-central1")))
```

## 🖥️ Console Actions as CLI Commands

| Console action | CLI equivalent |
|---|---|
| Create a project | `gcloud projects create PROJECT_ID --name="NAME"` |
| View all projects | `gcloud projects list` |
| Delete a project | `gcloud projects delete PROJECT_ID --quiet` |
| Link billing | `gcloud billing projects link PROJECT_ID --billing-account=YOUR_BILLING_ACCOUNT` |
| Enable an API | `gcloud services enable storage.googleapis.com` |
| List enabled APIs | `gcloud services list --enabled` |
| Create a bucket | `gsutil mb -l us-central1 -b on gs://BUCKET` |
| Upload objects | `gsutil cp file.csv gs://BUCKET/` |
| List buckets | `gsutil ls` |
| Delete a bucket | `gsutil rm -r gs://BUCKET` |
| Set bucket IAM | `gsutil iam ch serviceAccount:pipeline-sa@PROJECT_ID.iam.gserviceaccount.com:objectAdmin gs://BUCKET` |
| Create a BigQuery dataset | `bq mk --location=us-central1 PROJECT_ID:DATASET` |
| Run a query | `bq query --use_legacy_sql=false 'SELECT ...'` |
| Dry-run a query | `bq query --use_legacy_sql=false --dry_run 'SELECT ...'` |
| Create a topic | `gcloud pubsub topics create TOPIC --region=us-central1` |
| Publish a message | `gcloud pubsub topics publish TOPIC --message="hello"` |
| Create a subscription | `gcloud pubsub subscriptions create SUB --topic=TOPIC` |
| Launch a Dataflow job | `gcloud dataflow jobs run JOB --runner=DataflowRunner --region=us-central1` |
| Create a Dataproc cluster | `gcloud dataproc clusters create CLUSTER --region=us-central1` |
| Submit a Spark job | `gcloud dataproc jobs submit pyspark job.py --cluster=CLUSTER` |
| Create a Composer environment | `gcloud composer environments create ENV --location=us-central1 --image-version=composer-2` |
| Deploy a Cloud Run service | `gcloud run deploy SERVICE --image=IMAGE --region=us-central1` |
| Deploy a function | `gcloud functions deploy FUNCTION --gen2 --runtime=python311 --source=.` |
| Create a service account | `gcloud iam service-accounts create pipeline-sa` |
| Grant a role | `gcloud projects add-iam-policy-binding PROJECT_ID --member=serviceAccount:SA@PROJECT_ID.iam.gserviceaccount.com --role=roles/bigquery.dataEditor` |
| View the IAM policy | `gcloud projects get-iam-policy PROJECT_ID` |
| Read the audit log | `gcloud logging read 'protoPayload.serviceName="cloudresourcemanager.googleapis.com"' --limit=20` |
| List all resources | `gcloud asset search-all-resources --scope=projects/PROJECT_ID` |
| Export the billing data | `gcloud billing accounts list` then BigQuery export in the console |
| Create a budget alert | `gcloud billing budgets create --billing-account=YOUR_BILLING_ACCOUNT --budget-amount=25` |

## 🔗 Related

| Document | Contents |
|---|---|
| [SETUP.md](SETUP.md) | Installation, the optional GCP path, troubleshooting |
| [GLOSSARY.md](GLOSSARY.md) | Every term, defined |
| [FAQ.md](FAQ.md) | The questions students ask |
| [../interview/top-40.md](../interview/top-40.md) | The 40 most-asked interview questions |
