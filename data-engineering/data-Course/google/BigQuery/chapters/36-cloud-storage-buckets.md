# 5.1 — Cloud Storage Buckets for BigQuery

> **Section 5 · External Data, Views & Materialized Views · Lecture 5.1 · 6:49**

## 🎯 What you will learn

- Set up Cloud Storage optimally for BigQuery access
- The URI conventions that make external tables work
- Lifecycle rules as a cost control
- When external storage beats managed BigQuery tables

---

## 🧠 Concept

Cloud Storage is BigQuery's companion — the place where raw data lives before (and sometimes
instead of) entering the warehouse.

### Bucket configuration for BigQuery

```bash
# Create a bucket
gcloud storage buckets create gs://YOUR_PROJECT_ID-bq-course \
    --location=us-central1 \
    --uniform-bucket-level-access

# Enable versioning — this is your safety net for external tables
gcloud storage buckets update gs://YOUR_PROJECT_ID-bq-course \
    --versioning

# Block public access
gcloud storage buckets update gs://YOUR_PROJECT_ID-bq-course \
    --public-access-prevention
```

💡 **Enable object versioning.** BigQuery external tables have no time travel. Versioned GCS
objects are the only way to recover a corrupted or overwritten file.

### The URI conventions BigQuery understands

BigQuery can infer structure from the URI path. This is the difference between a fast, cheap
query and a slow, expensive one.

```text
gs://bucket/prefix/
    ├── dt=2026-01-01/part-00000.parquet
    ├── dt=2026-01-01/part-00001.parquet
    ├── dt=2026-01-02/part-00000.parquet
    └── dt=2026-01-02/part-00001.parquet
```

The `key=value/` segments are **Hive-style partition keys**. BigQuery parses them and applies
partition pruning automatically.

```sql
-- ✅ Hive-partitioned external table
CREATE EXTERNAL TABLE `YOUR_PROJECT_ID.raw.events_hive`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://YOUR_PROJECT_ID-bq-course/events/*'],
  hive_partition_uri_prefix = 'gs://YOUR_PROJECT_ID-bq-course/events/'
);
```

```sql
-- Query it — the dt filter prunes files
SELECT dt, COUNT(*)
FROM `YOUR_PROJECT_ID.raw.events_hive`
WHERE dt >= '2026-01-01'
GROUP BY dt;
```

⚠️ **Without `hive_partition_uri_prefix`, BigQuery treats `dt=` as part of the filename and reads
the `dt` column as a regular column** — no pruning, and the column may not exist.

### The file-naming convention

```
gs://bucket/data/<dataset>/<table>/dt=YYYY-MM-DD/file.parquet
```

💡 **Adopt one convention and stick to it.** A consistent layout means external table creation is
a copy-paste operation, and new tables can be auto-discovered.

---

## 🧠 Lifecycle Rules for Cost Control

```bash
gcloud storage buckets update gs://YOUR_PROJECT_ID-bq-course \
    --lifecycle-file=lifecycle.json
```

```json
{
  "rule": [
    {
      "action": { "type": "SetStorageClass", "storageClass": "NEARLINE" },
      "condition": { "age": 30, "matchesPrefix": ["staging/"] }
    },
    {
      "action": { "type": "SetStorageClass", "storageClass": "COLDLINE" },
      "condition": { "age": 90 }
    },
    {
      "action": { "type": "SetStorageClass", "storageClass": "ARCHIVE" },
      "condition": { "age": 365, "matchesPrefix": ["archive/"] }
    },
    {
      "action": { "type": "Delete" },
      "condition": { "age": 1095, "matchesPrefix": ["staging/"] }
    }
  ]
}
```

| Prefix | Lifecycle |
|--------|-----------|
| `staging/` | Nearline at 30d, deleted at 3 years |
| `raw/` | Coldline at 90d |
| `archive/` | Archive at 365d |

⚠️ **Never point a BigQuery external table at the Archive class.** Archive has a $0.05/GB
retrieval fee — reading 1 TB costs $50 in retrieval alone, plus the query cost.

---

## 🛠️ Hands-On

### 1. Create the bucket and upload data

```bash
gcloud storage buckets create gs://YOUR_PROJECT_ID-bq-course \
    --location=us-central1 --uniform-bucket-level-access

gcloud storage cp ./sample_data/orders_2026-01-01.csv \
    gs://YOUR_PROJECT_ID-bq-course/staging/
```

### 2. List what is in the bucket

```bash
gcloud storage ls --recursive gs://YOUR_PROJECT_ID-bq-course/
gcloud storage ls --long gs://YOUR_PROJECT_ID-bq-course/staging/
```

### 3. Check the storage cost breakdown

```bash
gcloud storage buckets describe gs://YOUR_PROJECT_ID-bq-course --format=json | \
  jq '.storageClass, .lifecycle'
```

---

## 💡 Production Notes

- **Use Uniform Bucket-Level Access.** Legacy ACLs are deprecated and add confusion.
- **Versioning on raw buckets** — your only recovery path for external data.
- **Match the bucket region to the BigQuery dataset region.** Cross-region reads are slower.
- **Use `gsutil -m` for bulk operations** — it parallelizes.
- **Set lifecycle rules per prefix**, not globally — different data has different access patterns.

---

## 🔑 Key Takeaways

- Enable versioning and public-access prevention on every bucket.
- **Hive-style `key=value/` URI paths enable automatic partition pruning** on external tables.
- Adopt one consistent file-naming convention.
- Lifecycle rules per prefix are the cost control.
- Never point a BigQuery external table at Archive storage.

---

## 📚 Practice Exercises

1. **Bucket layout.** Design a bucket layout for a data lake with staging, raw, curated, and
   archive tiers. Include the lifecycle policy for each and the reasoning.

2. **Hive partitioning.** Create a Hive-partitioned Parquet dataset in GCS, create the external
   table, and prove that a `dt` filter prunes. Record the bytes processed with and without.

3. **Versioning recovery.** Demonstrate recovering an overwritten Parquet file using GCS object
   versioning. Write the full procedure.

---

## 📖 Further Reading

- Cloud Storage storage classes — https://cloud.google.com/storage/docs/storage-classes
- Object versioning — https://cloud.google.com/storage/docs/object-versioning
- Lifecycle management — https://cloud.google.com/storage/docs/lifecycle
