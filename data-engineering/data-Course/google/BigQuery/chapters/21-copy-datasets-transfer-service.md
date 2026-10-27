# 3.7 — Copy Datasets & Transfer Service

> **Section 3 · Running Queries with Various Query Settings · Lectures 3.9–3.10 · 5:05 + 4:03**

## 🎯 What you will learn

- The four copy operations and when each applies
- Cross-region copies and their cost implications
- The Transfer Service for scheduled, managed ingestion
- BigQuery Data Transfer Service vs Storage Transfer Service vs third-party transfers

---

## 🧠 Concept

Moving data inside BigQuery — or into it from elsewhere — has several distinct mechanisms.

### The four copy operations

| Operation | What it copies | Cost | Use when |
|-----------|---------------|------|----------|
| `CREATE TABLE AS SELECT` | Query results | Query cost + storage | Transforming while copying |
| `CREATE TABLE AS SELECT ... AS OF` | Snapshot of a table | Query cost + storage | Time-travel copy |
| `CREATE SNAPSHOT TABLE` | Point-in-time copy | Storage only (no query cost) | Safe backups, fast copies |
| `bq cp` / `COPY` job | A table | Storage only (no query cost) | Plain copy, no transformation |

💡 **The key distinction:** a **copy job** (`bq cp`) moves bytes without running a query — it is
fast and costs only storage. A **CTAS** runs a query — it costs query fees and gives you
transformation for free.

### Copying within BigQuery

```sql
-- 1. Plain copy (no query cost)
CREATE TABLE `YOUR_PROJECT_ID.curated.orders_copy`
COPY `YOUR_PROJECT_ID.curated.orders`;

-- 2. Snapshot copy with a specific point in time
CREATE SNAPSHOT TABLE `YOUR_PROJECT_ID.curated.orders_snapshot`
FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY) AS
SELECT * FROM `YOUR_PROJECT_ID.curated.orders`;

-- 3. Copy with transformation (costs query + storage)
CREATE TABLE `YOUR_PROJECT_ID.curated.orders_2026`
PARTITION BY order_date
AS
SELECT
    order_id, customer_id, order_date, total_amount, status
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE order_date >= DATE('2026-01-01');
```

```bash
# CLI copy — no query cost
bq cp \
  --destination_table_expiration_timestamp=2027-01-01T00:00:00Z \
  YOUR_PROJECT_ID:curated.orders \
  YOUR_PROJECT_ID:curated.orders_backup

# Copy multiple tables with a wildcard
bq cp --ignore_existing \
  YOUR_PROJECT_ID:curated.events_* \
  YOUR_PROJECT_ID:backup.events_*
```

⚠️ **Copy jobs have quotas.** Copying many large tables concurrently can hit
`copy` job limits. Batch them.

---

## 🧠 Cross-Region Copies

Copying data between locations is a first-class operation with specific considerations.

```sql
-- Copy a table from US to EU
CREATE TABLE `YOUR_PROJECT_ID.eu_orders.orders`
COPY `YOUR_PROJECT_ID.us_orders.orders`;
```

```bash
bq cp \
  YOUR_PROJECT_ID:us_orders.orders \
  YOUR_PROJECT_ID:eu_orders.orders
```

### What to know

| Aspect | Behaviour |
|--------|-----------|
| **Mechanism** | Snapshot the source, then asynchronously copy the bytes |
| **Cost** | Storage in the source + storage in the destination + network transfer |
| **Egress** | Cross-region copies **within Google Cloud are free** of internet egress charges |
| **Time** | Asynchronous — hours for large tables |
| **Source state** | The source is snapshotted at job start; it is not locked |

💡 **Cross-region copies within GCP do not incur internet egress charges.** Moving data *out* of
GCP entirely (to another cloud, or to a local machine) does.

### The migration pattern

```sql
-- Step 1: Snapshot + copy to the destination
CREATE TABLE `YOUR_PROJECT_ID.eu.orders`
COPY `YOUR_PROJECT_ID.us.orders`;

-- Step 2: Verify row counts and checksums
SELECT
    (SELECT COUNT(*) FROM `YOUR_PROJECT_ID.us.orders`)     AS src_rows,
    (SELECT COUNT(*) FROM `YOUR_PROJECT_ID.eu.orders`)      AS dst_rows,
    (SELECT SUM(total_amount) FROM `YOUR_PROJECT_ID.us.orders`) AS src_sum,
    (SELECT SUM(total_amount) FROM `YOUR_PROJECT_ID.eu.orders`) AS dst_sum;
```

```sql
-- Step 3: Keep both in sync during the transition
CREATE SCHEDULED QUERY `YOUR_PROJECT_ID.analytics.sync_orders_to_eu`
OPTIONS (
  schedule = "0 */2 * * *",
  destination_table = "YOUR_PROJECT_ID.eu.orders_incremental",
  write_disposition = "WRITE_APPEND",
  maximum_bytes_billed = 5000000000
)
AS
SELECT * FROM `YOUR_PROJECT_ID.us.orders`
WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY);
```

---

## 🧠 The Transfer Service

BigQuery's **Data Transfer Service (DTS)** runs and schedules transfers between BigQuery and
supported sources — managed by Google, with built-in scheduling, retries, and monitoring.

### Supported sources

| Source | Transfer type |
|--------|---------------|
| **Google Cloud Storage** | ✅ (via Storage Transfer Service) |
| **Google Ads** | ✅ |
| **Google Analytics (GA4)** | ✅ |
| **Google Cloud Billing** | ✅ |
| **Google Finance / Google Ads Reports** | ✅ |
| **Amazon S3** | ✅ (via third-party) |
| **Salesforce** | ✅ (third-party) |
| **HubSpot** | ✅ (third-party) |
| **Facebook Ads** | ✅ (third-party) |
| **MySQL / PostgreSQL** | ✅ (via third-party) |

### Storage Transfer Service vs BigQuery Transfer Service

These are different products and are frequently confused:

| | **BigQuery Data Transfer Service** | **Storage Transfer Service** |
|---|---|---|
| Purpose | Load data *into BigQuery* | Move objects *between GCS buckets* |
| Destinations | BigQuery tables | GCS buckets |
| Scheduling | ✅ | ✅ |
| BigQuery-specific features | Schema mapping, table creation | None |
| Use for | S3 → BigQuery, GA4 → BigQuery | S3 → GCS, GCS → GCS cross-region |

💡 **For S3 → BigQuery, use the BigQuery DTS with an S3 connector** — it handles schema mapping and
table creation. For S3 → GCS → BigQuery (external table), use the Storage Transfer Service.

### Creating a transfer

```bash
# Create a scheduled transfer from GCS to BigQuery
bq mk --transfer_config \
  --display_name="Nightly GCS Load" \
  --destination_dataset=curated \
  --destination_table=events \
  --source_uris="gs://YOUR_PROJECT_ID-bq-course/staging/events_*.parquet" \
  --source_format=PARQUET \
  --schedule="0 3 * * *" \
  --time_zone="UTC" \
  --transfer_type=copy \
  --max_bad_records=10 \
  YOUR_PROJECT_ID
```

```bash
# List transfers
bq ls --transfers

# Run one immediately (useful for testing)
bq transfer run --transfer_config=NightlyGCSLoad YOUR_PROJECT_ID

# Get the run history
bq ls --transfer_run --transfer_config=NightlyGCSLoad YOUR_PROJECT_ID

# Delete a transfer
bq rm --transfer_config --delete_contents YOUR_PROJECT_ID:NightlyGCSLoad
```

### S3 → BigQuery via the AWS S3 connection

```sql
-- Create an AWS connection (admin must do this first)
CREATE CONNECTION `YOUR_PROJECT_ID.connections.s3_connection`
OPTIONS (
  aws_access_key_id = '...',
  aws_secret_access_key = '...'
);

-- Create the transfer using the connection
CREATE TRANSFER SET
  `YOUR_PROJECT_ID.transfers.s3_to_bq`
OPTIONS (
  source_uris = ['s3://my-bucket/events/*.parquet'],
  destination_dataset = 'curated',
  destination_table = 'events_s3',
  source_format = 'PARQUET',
  schedule = '0 4 * * *',
  transfer_type = 'COPY',
  create_disposition = 'CREATE_IF_NEEDED',
  write_disposition = 'WRITE_APPEND',
  max_bad_records = 10,
  connection_id = 'projects/YOUR_PROJECT_ID/connections/s3_connection'
);
```

### Monitoring transfers

```sql
-- Transfer run history and errors
SELECT
    transfer_config_id,
    destination_table_id,
    error_status,
    start_time,
    end_time,
    TIMESTAMP_DIFF(end_time, start_time, SECOND) AS duration_seconds
FROM `region-us.INFORMATION_SCHEMA.TRANSFER_RUNS`
ORDER BY start_time DESC
LIMIT 20;
```

---

## 🛠️ Hands-On

### 1. Compare copy vs CTAS cost

```sql
-- Copy job: no query cost, only storage
CREATE TABLE `YOUR_PROJECT_ID.curated.orders_copy_a`
COPY `YOUR_PROJECT_ID.curated.orders`;

-- CTAS: query cost + storage
CREATE TABLE `YOUR_PROJECT_ID.curated.orders_copy_b`
AS SELECT * FROM `YOUR_PROJECT_ID.curated.orders`;

-- Compare the job records
SELECT
    job_type,
    total_bytes_processed,
    total_bytes_billed,
    ROUND(total_slot_ms / 1000, 2) AS slot_seconds
FROM `region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
  AND job_type IN ('COPY', 'QUERY')
ORDER BY creation_time DESC;
```

💡 **The copy job shows `total_bytes_processed = 0`** because no query ran — it moved bytes
directly. This is why copies are so much cheaper than CTAS.

### 2. Snapshot vs copy for a point-in-time reference

```sql
-- Snapshot: fast, cheap, exact point in time
CREATE SNAPSHOT TABLE `YOUR_PROJECT_ID.curated.orders_as_of_jan1`
FOR SYSTEM_TIME AS OF TIMESTAMP('2026-01-01 00:00:00') AS
SELECT * FROM `YOUR_PROJECT_ID.curated.orders`;

-- CTAS with AS OF: runs a query, costs query fees
CREATE TABLE `YOUR_PROJECT_ID.curated.orders_as_of_jan1_query`
AS OF TIMESTAMP('2026-01-01 00:00:00')
SELECT * FROM `YOUR_PROJECT_ID.curated.orders`;
```

### 3. Set up a scheduled GCS → BigQuery transfer

```bash
# Prepare the source data
gsutil mb -l us-central1 gs://YOUR_PROJECT_ID-bq-course/staging
gsutil cp ./sample_data/orders_*.csv gs://YOUR_PROJECT_ID-bq-course/staging/

# Create the transfer
bq mk --transfer_config \
  --display_name="Nightly Orders Load" \
  --destination_dataset=raw \
  --destination_table=orders_incoming \
  --source_uris="gs://YOUR_PROJECT_ID-bq-course/staging/orders_*.csv" \
  --source_format=CSV \
  --autodetect \
  --schedule="0 2 * * *" \
  --time_zone="UTC" \
  YOUR_PROJECT_ID
```

```bash
# Test it immediately
bq transfer run --transfer_config=NightlyOrdersLoad YOUR_PROJECT_ID

# Check the result
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `YOUR_PROJECT_ID.raw.orders_incoming`'
```

---

## 💡 Production Notes

- **Copy jobs are the cheapest way to duplicate data** — no query fees. Use them for backups and
  dataset duplication.
- **`WRITE_TRUNCATE` on a transfer destroys the destination table's schema extras.** If the
  destination is partitioned or clustered, the transfer will replace it with an unpartitioned
  table. Load into a staging table and `MERGE` into the real one.
- **Transfer Service has a 24-hour minimum schedule interval** and some sources impose their own
  limits (e.g. GA4 minimum 4 hours).
- **Always set `max_bad_records`** on a transfer. Without it, one corrupt row in the source fails
  the entire transfer, and a 400-row-per-day GA4 export makes that failure frequent.
- **Monitor `INFORMATION_SCHEMA.TRANSFER_RUNS`** — transfer failures are silent unless you alert.

---

## 🔑 Key Takeaways

- Four copy mechanisms; **copy jobs (`bq cp`) cost only storage, CTAS costs query + storage**.
- Cross-region copies within GCP are **free of internet egress fees**.
- `CREATE SNAPSHOT TABLE` is the cheapest way to make a point-in-time copy.
- BigQuery DTS handles ingest into BigQuery; **Storage Transfer Service** handles GCS-to-GCS.
- Set `max_bad_records` on every transfer — one bad row should not fail the pipeline.
- `WRITE_TRUNCATE` on a transfer loses partitioning, clustering, and grants on the destination.

---

## 📚 Practice Exercises

1. **Copy strategy.** For each scenario, choose the cheapest correct copy method and justify:
   - (a) Daily backup of a 2 TB table, kept 30 days
   - (b) Creating a point-in-time reference for a quarterly audit
   - (c) Moving a table from `us-central1` to `europe-west2`
   - (d) Building a filtered, re-partitioned version of a table

2. **Transfer design.** Design a daily transfer from GA4 into a partitioned BigQuery table. Cover:
   transfer type, destination, schema handling, bad records, scheduling, and monitoring.

3. **Migration cutover.** Design a zero-downtime migration of a dataset from `US` to `EU`. Include:
   the copy, the verification, the dual-write, the cutover, and the rollback.

4. **Cost audit.** Run a query over `INFORMATION_SCHEMA.JOBS` that compares the total cost of COPY
   jobs vs CTAS jobs in your project over 30 days. What would you change?

5. **Monitoring.** Write the alert query for failed transfer runs, including the error message and
   the affected destination table.

---

## 📖 Further Reading

- BigQuery Data Transfer Service — https://cloud.google.com/bigquery/docs/transfer-service-overview
- Storage Transfer Service — https://cloud.google.com/storage/docs/transfer-service-overview
- Copy jobs — https://cloud.google.com/bigquery/docs/managing-copy-jobs
