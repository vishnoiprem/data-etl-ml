# 1.3 — Storage Services in GCP

> **Section 1 · Introduction to Google Cloud Platform · Lecture 1.3 · 5:32**

## 🎯 What you will learn

- Cloud Storage classes and when to use each
- Filestore, Persistent Disk, and the storage hierarchy
- How storage connects to BigQuery: external tables, transfers, and exports

---

## 🧠 Concept

Storage in GCP is layered, and the layers differ mainly in **access pattern**:

```
Object Storage (Cloud Storage)  →  files, blobs, arbitrary bytes
   ▲
   │  via external tables / transfers / exports
   │
BigQuery (managed table storage) →  columnar, schema'd, queryable
   ▲
   │  via pipelines
   │
Lakehouse pattern: GCS = system of record, BigQuery = query engine
```

### Cloud Storage classes

| Class | For | Access | $ / GB-month | Min duration | Typical use |
|-------|-----|--------|--------------|--------------|-------------|
| **Standard** | Frequent access | ms | $0.020 | none | Active data, staging |
| **Nearline** | Once/month | ms | $0.010 | 30 days | Backups, monthly reports |
| **Coldline** | Once/quarter | ms | $0.004 | 90 days | Data lake, archives |
| **Archive** | Once/year+ | **hours** | $0.0012 | 365 days | Long-term retention, compliance |
| **Autoclass** | Unknown pattern | ms | varies | none | Let GCP decide |

**Retrieval fees** are the trap:

- Nearline: **$0.01/GB** retrieval
- Coldline: **$0.02/GB** retrieval
- Archive: **$0.05/GB** retrieval

Reading 1 TB from Archive costs $50 in retrieval fees alone. 💡 **Never point a BigQuery external
table at Archive.** BigQuery reads files through the storage API, and the per-GB retrieval charge
lands on every scan.

### The other storage services

| Service | What it is | Use when |
|---------|-----------|----------|
| **Filestore** | Managed NFS/filer | Shared POSIX filesystem; legacy app workloads |
| **Persistent Disk** | Block storage attached to VMs | OS disks, database volumes |
| **Local SSD** | NVMe on Compute Engine | Low-latency temp/scratch space |
| **Archive / Snapshot** | Point-in-time disk images | Backup and recovery |
| **Transfer Appliance** | Physical appliance | Moving PB-scale data to GCP |

---

## 🛠️ Hands-On

### 1. Create a bucket with the right lifecycle rules

```bash
# Create a bucket (names are globally unique)
gcloud storage buckets create gs://YOUR_PROJECT_ID-bq-course \
    --location=us-central1 \
    --uniform-bucket-level-access

# List buckets
gcloud storage ls

# Make it private by default (also set org-level public access prevention)
gcloud storage buckets update gs://YOUR_PROJECT_ID-bq-course \
    --public-access-prevention
```

Lifecycle rule — move cold data down a class after 90 days:

```bash
gcloud storage buckets update gs://YOUR_PROJECT_ID-bq-course \
    --lifecycle-file 'lifecycle.json'
```

```json
{
  "rule": [
    {
      "action": { "type": "SetStorageClass", "storageClass": "NEARLINE" },
      "condition": { "age": 30 }
    },
    {
      "action": { "type": "SetStorageClass", "storageClass": "COLDLINE" },
      "condition": { "age": 90 }
    },
    {
      "action": { "type": "Delete" },
      "condition": { "age": 365 }
    }
  ]
}
```

### 2. Upload data and load it into BigQuery

```bash
# Upload a file
gcloud storage cp ./data/orders.csv gs://YOUR_PROJECT_ID-bq-course/staging/

# Load directly from Cloud Storage into a BigQuery table
bq load \
  --source_format=CSV \
  --autodetect \
  --replace \
  YOUR_PROJECT_ID:analytics.orders \
  gs://YOUR_PROJECT_ID-bq-course/staging/orders.csv
```

### 3. Create an external table (query the file in place, no load)

```sql
CREATE EXTERNAL TABLE `YOUR_PROJECT_ID.analytics.orders_external`
OPTIONS (
  format = 'CSV',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/staging/orders*.csv'],
  skip_leading_rows = 1,
  max_bad_records = 10
);

SELECT COUNT(*) FROM `YOUR_PROJECT_ID.analytics.orders_external`;
```

### 4. Export a BigQuery table to Cloud Storage

```sql
EXPORT DATA OPTIONS(
  uri = 'gs://YOUR_PROJECT_ID-bq-course/exports/orders_*.csv',
  format = 'CSV',
  overwrite = true
)
AS SELECT * FROM `YOUR_PROJECT_ID.analytics.orders`;
```

💡 **Use EXPORT DATA, not `bq extract`.** `bq extract` runs a table copy job and writes a
single format; `EXPORT DATA` supports wildcard output, parallelism, compression, and Avro/Parquet
for Hive-compatible targets.

---

## 💡 Production Notes

- **Always enable Public Access Prevention** on buckets. Default should be private, no exceptions.
- **Uniform bucket-level access** (IAM-only) is now the norm; avoid `gcloud storage buckets update
  --enable-legacy-acl`.
- **Lifecycle rules are your cost control.** Without them, cold data silently bills at Standard rates.
- **Storage → BigQuery is not free of egress.** Dataflow and Dataflow-style pipelines that move
  data between GCS and BigQuery within the same region avoid internet egress charges, but moving
  data *out* of GCP to your laptop or another cloud does not.

---

## 🔑 Key Takeaways

- Cloud Storage has 4 explicit classes plus Autoclass; **retrieval fees** make Archive unsuitable
  for query workloads.
- BigQuery is the query layer; Cloud Storage is the system of record in a lakehouse design.
- External tables query files in place — no load, but no free lunch on storage or retrieval fees.
- Lifecycle rules are mandatory for cost control; without them everything bills at Standard.
- `EXPORT DATA` beats `bq extract` for anything but trivial tables.

---

## 📚 Practice Exercises

1. **Class selection.** Design a storage class plan for:
   - (a) A 500 GB nightly backup retained 7 years, read once a year for disaster recovery
   - (b) A 20 TB clickstream lake, queried hourly for 30 days, then occasionally
   - (c) A 10 GB model artifact read every 4 hours

2. **Retrieval cost.** Compute the total cost of archiving 1 TB and reading it back once with each
   class. Which is cheapest for a single annual read?

3. **External vs internal.** Compare cost and latency for a 1 TB CSV queried daily:
   external table vs loaded table. Include the load cost.

4. **Lifecycle.** Write a `lifecycle.json` for a bucket holding: 7 days of hot logs, 90 days of
   warm application data, and permanent compliance records.

---

## 📖 Further Reading

- Cloud Storage classes — https://cloud.google.com/storage/docs/storage-classes
- Storage pricing — https://cloud.google.com/storage/pricing
- BigQuery external tables — https://cloud.google.com/bigquery/docs/external-tables
