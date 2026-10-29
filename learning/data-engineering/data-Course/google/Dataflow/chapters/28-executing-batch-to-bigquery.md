# 5.5 — Executing Batch → BigQuery

> **Section 5 · Dataflow Templates & Deployment · Lecture 5.5 · 6:30**

## 🎯 What you will learn

- The complete operational runbook: build, run, watch, verify, clean up
- When BigQuery SQL is the right tool, and when Beam is — answered honestly
- The hybrid pattern: Beam for the edges, BigQuery for the middle
- The verification queries to run after every job
- A realistic cost estimate for the whole exercise
- A correctness checklist: row counts, null rates, checksums

---

## 🧠 Concept

### The runbook

Deployment is not the hard part. Verification is.

The sequence below is the one to memorise. Each step has a check, and each
check has a defined pass condition.

```text
┌──────────────────────────────────────────────────────────────────┐
│ 0. LOCAL PROOF      run the pipeline with DirectRunner           │
│                     no credentials, no bill, 30 seconds           │
├──────────────────────────────────────────────────────────────────┤
│ 1. BUILD            upload the template, record the version      │
│                     check: the file is in GCS, metadata matches  │
├──────────────────────────────────────────────────────────────────┤
│ 2. SUBMIT           run with --wait=false, capture the job ID    │
│                     check: the job ID was printed                │
├──────────────────────────────────────────────────────────────────┤
│ 3. WATCH            poll the state, watch the metrics            │
│                     check: state reaches DONE, not FAILED        │
├──────────────────────────────────────────────────────────────────┤
│ 4. VERIFY           row counts, null rates, checksums             │
│                     check: every count matches expectation       │
├──────────────────────────────────────────────────────────────────┤
│ 5. PROMOTE          staging table -> production table (optional) │
│                     check: the production table has new data     │
├──────────────────────────────────────────────────────────────────┤
│ 6. CLEAN UP         delete the staging prefix, check the bill    │
│                     check: temp objects are gone                 │
└──────────────────────────────────────────────────────────────────┘
```

Skipping step 0 is how you pay $2 for a syntax error. Skipping step 4 is
how you publish a wrong number to a dashboard and find out three weeks
later.

### "Why would I ever do this in BigQuery SQL instead?"

This is the right question to ask, and it deserves a straight answer rather
than a defence of Beam.

**BigQuery SQL wins when:**

| Situation | Why SQL wins |
|---|---|
| The logic is expressible in SQL | BigQuery SQL is a distributed query engine. A `GROUP BY` over a 10 TB table is one statement, no cluster, no workers, no staging. |
| The input is already in BigQuery | Loading is the expensive part. If the data is already there, Beam adds a read and a write for no benefit. |
| The job runs once a day over a fixed snapshot | A BigQuery scheduled query costs pennies and has no warm-up. |
| The team is SQL-literate and Beam is not | The maintainability cost of a Beam codebase is real. |
| The output is a view, not a table | A view costs nothing to maintain and is always fresh. |

A BigQuery scheduled query over a 10 TB table typically costs **$0.10 to
$1.00** in bytes scanned, depending on the partition pruning. The
equivalent Beam job costs **$10 to $50** in Dataflow vCPU-hours, plus the
BigQuery write cost of the output, plus the operational surface area of a
distributed job. That is a one-to-two-order-of-magnitude difference, and
it is not close.

**Beam wins when:**

| Situation | Why Beam wins |
|---|---|
| The logic is not SQL-expressible | Custom parsing, ML inference, fuzzy matching, geospatial joins, image processing, format conversion. |
| The input is not in BigQuery | Files on disk, Kafka, Pub/Sub, a SaaS API, a proprietary database. |
| You need one codebase for batch and streaming | This is Beam's founding premise. The same transform code runs in both modes. |
| The pipeline must scale with the input, not with the query engine | Beam's autoscaling is per-stage and per-bundle; a BigQuery query is one monolithic unit. |
| You need to write back to many systems | Beam fans out to GCS, BigQuery, Pub/Sub, Spanner, Cloud Storage, Salesforce. |
| The job needs custom partitioning or per-record state | Streaming state, timers, and triggers have no SQL equivalent. |
| The input arrives continuously | A streaming pipeline is not a scheduled query. |

**The honest summary:** if your input is in BigQuery and your logic is
SQL-shaped, **use BigQuery SQL**. Do not use Beam because you have read a
blog post. Beam earns its cost when it does something BigQuery cannot, or
when the *same code* must run in batch and streaming.

### The hybrid pattern

The most common production architecture is neither pure Beam nor pure SQL.
It splits by where the work is cheap.

```text
                    ┌─────────────────────────────────┐
   GCS files ──────▶│                                 │
                    │      BEAM (the edges)           │
   Pub/Sub    ──────▶│  parse, decode, validate,       │
                    │  join to reference data,         │
                    │  normalise, deduplicate         │
                    └──────────────┬──────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────┐
                    │   BIGQUERY (the middle)          │
                    │  aggregate, window, join,        │
                    │  compute derived metrics,        │
                    │  serve the dashboards             │
                    └──────────────┬──────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────┐
                    │  BigQuery tables, views,         │
                    │  Looker dashboards, exports      │
                    └─────────────────────────────────┘
```

Beam's job is the part SQL cannot do: getting data *into* BigQuery in a
usable shape. BigQuery's job is the part Beam does badly: the aggregation
and the querying.

This is also the pattern with the best cost profile. Beam's expensive part
is the per-element processing; BigQuery's expensive part is the bytes
scanned. Beam produces one narrow, clean, well-partitioned table; BigQuery
does the rest.

A concrete example from this course's data: the orders file has
`region,currency,amount` with mixed currencies and occasional malformed
rows. In BigQuery SQL, cleaning that is:

```sql
SELECT
  region,
  SUM(CASE currency WHEN 'EUR' THEN amount WHEN 'USD' THEN amount * 0.92 END) AS revenue_eur
FROM `YOUR_PROJECT_ID.YOUR_DATASET.raw_orders`
GROUP BY region
```

That works — but only if the raw table is already clean enough to query,
and only for currencies with a rate in the CASE expression. The moment a
new currency appears, the CASE expression needs updating, and someone has
to remember. A Beam template with a currency lookup table handles the new
currency automatically, and it runs the same code for the streaming case
where the rate arrives late.

### Verification queries

After every run, run these. They take seconds and they catch nearly
everything.

#### 1. Row count against expectation

```sql
SELECT
  COUNT(*) AS rows_in_table,
  COUNT(DISTINCT region) AS distinct_regions
FROM `YOUR_PROJECT_ID.YOUR_DATASET.orders_by_region`;
```

The expectation comes from the input, not from a guess. If the input has
five regions, the output must have five rows.

#### 2. Null rate per column

```sql
SELECT
  COUNT(*) AS total,
  COUNTIF(region IS NULL) AS null_region,
  COUNTIF(order_count IS NULL) AS null_order_count,
  COUNTIF(revenue_eur IS NULL) AS null_revenue,
  ROUND(100.0 * COUNTIF(region IS NULL) / COUNT(*), 3) AS pct_null_region
FROM `YOUR_PROJECT_ID.YOUR_DATASET.orders_by_region`;
```

A null rate that has changed since yesterday is a signal, even if it is
small. `revenue_eur` being nullable is fine — but it should be null for
the *same* rows every run.

#### 3. Value sanity

```sql
SELECT
  MIN(revenue_eur) AS min_revenue,
  MAX(revenue_eur) AS max_revenue,
  SUM(revenue_eur) AS total_revenue,
  SUM(order_count) AS total_orders
FROM `YOUR_PROJECT_ID.YOUR_DATASET.orders_by_region`;
```

Compare `total_revenue` and `total_orders` against a source-of-truth
figure. A sudden change in `total_orders` means the input changed, the
filter changed, or the job silently dropped rows.

#### 4. The checksum

A checksum makes "did the output change?" a one-query question. Sum a
stable function of the row contents:

```sql
SELECT
  COUNT(*) AS rows_in_table,
  SUM(
    FARM_FINGERPRINT(
      CONCAT(region, '|', CAST(order_count AS STRING), '|',
             CAST(revenue_eur AS STRING))
    )
  ) AS checksum
FROM `YOUR_PROJECT_ID.YOUR_DATASET.orders_by_region`;
```

`FARM_FINGERPRINT` is a 64-bit hash. Summing it over all rows gives a
value that is stable for identical content and changes for any
difference. Store it next to the run's timestamp, and you have a
regression test:

```sql
SELECT
  run_date,
  checksum,
  rows_in_table
FROM `YOUR_PROJECT_ID.YOUR_DATASET.orders_by_region_runs`
ORDER BY run_date DESC;
```

The table of runs is the artefact that makes this useful over time. A
checksum you cannot compare to a previous checksum tells you nothing.

#### 5. Partition coverage

```sql
SELECT
  partition_id,
  total_rows,
  creation_time
FROM `YOUR_PROJECT_ID.YOUR_DATASET.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name = 'orders_by_region'
ORDER BY partition_id DESC
LIMIT 10;
```

Exactly one new partition per run, and no gaps. A missing partition means
the job did not write the day's data.

### The cost of the whole exercise

A realistic estimate for the end-to-end exercise in this chapter, on a
small dataset.

**Assumptions:**

- 5,000 input orders, roughly 600 KB of CSV.
- One `n1-standard-2` worker (2 vCPUs).
- Job runs for about 90 seconds, including the staging phase.
- Output: 5 rows in BigQuery, plus a scratch copy in GCS.

| Component | Calculation | Cost |
|---|---|---|
| Dataflow worker | 2 vCPU × 0.05 h × $0.08/vCPU-h | **$0.008** |
| Dataflow staging/temp storage | 5 MB for 2 hours | **$0.0001** |
| BigQuery write | 0.5 MB at $0.01/GB | **$0.000005** |
| BigQuery active storage | 0.5 MB ≈ 0.0005 GB-month | **$0.00001** |
| BigQuery verification queries | ~5 MB scanned × 5 queries | **$0.00006** |
| Cloud Storage output | 0.5 MB for a month | **$0.00001** |
| **Total** | | **≈ $0.008** |

Under a cent. The Dataflow worker dominates at 97% of the total, which is
the shape of every small Dataflow job: **you are paying for worker startup,
not for the data.**

Now the same exercise at a scale that matters:

| | Small (5K rows) | Medium (500M rows, 60 GB) | Large (50B rows, 6 TB) |
|---|---|---|---|
| Workers | 1 | 50 | 2,000 |
| Duration | 90 s | 25 min | 4 h |
| Dataflow | $0.008 | $16 | $1,280 |
| BigQuery write | ~$0 | $0.60 | $60 |
| BigQuery output storage | ~$0 | $1.20/mo | $120/mo |
| Temp GCS (peak) | ~$0 | $0.06 | $6 |
| **Total per run** | **$0.008** | **≈ $17** | **≈ $1,340** |

The scaling is what matters: cost is roughly linear in data volume, and
**Dataflow is 85–95% of it** at every scale. That is why the levers are
worker count, machine type, and the number of shuffles — and why "we could
have done it in BigQuery SQL" is often the right question to ask.

The BigQuery SQL alternative for the medium case, if the input were
already in BigQuery:

| | Beam | BigQuery SQL |
|---|---|---|
| Compute | $16 | $0.75 (60 TB scanned at $0.0125/TB) |
| Write output | $0.60 | $0.60 |
| Operational overhead | high (a distributed job to deploy, watch, debug) | none |
| Total | $16.60 | $1.35 |

An 12× cost difference, and the SQL version has no failure modes beyond
BigQuery's own. This is the calculation that should make you hesitate
before reaching for Beam on data that already lives in BigQuery.

### The correctness checklist

Run this after every job. It takes five minutes and it is the difference
between "the job succeeded" and "the data is correct".

```text
□  The job reached DONE (not FAILED, not CANCELLED).
□  The job's runtime was in the expected range — not 10× last run.
□  estimated_cpu_seconds is within 2× of the previous run.
□  max_workers did not sit at the ceiling for the whole run.
□  worker_health stayed above 0.95.
□  Row count matches the expected count derived from the input.
□  Distinct key count matches the expected distinct key count.
□  Null rate per column matches the previous run (± small tolerance).
□  MIN / MAX / SUM of the key measures are plausible.
□  The checksum matches the previous run, or the change is explained.
□  Exactly one new partition exists, and it is the expected date.
□  No rows landed in a DLQ table (or the DLQ count is expected).
□  The output is queryable by the consumer — run one of their queries.
□  The bill for the run is in the expected range.
```

Two of these deserve emphasis.

**"The runtime was in the expected range."** A job that takes 10× longer
than usual usually produced the right answer with much more work, or
produced a wrong answer. Either way, it is a signal. Most teams only
alert on `FAILED`, and they miss every silent degradation.

**"The checksum matches, or the change is explained."** An unexplained
checksum change is the strongest signal you have. It means the output
changed and nobody can say why. Treat it as an incident until it is
explained.

---

## 🛠️ Hands-On: The Full Runbook

### Step 0 — the local proof

Nothing in this step costs money and everything downstream depends on it.

```bash
cd data-engineering/data-Course/google/Dataflow

python resources/sample_data.py --output-dir ./sample_data

python project/batch_pipeline.py \
  --input=./sample_data/orders.csv \
  --output=./out/runbook_local
```

Record the expected numbers. These are your ground truth for the whole
exercise:

```bash
# Row count of the local output
wc -l out/runbook_local*

# The actual rows
cat out/runbook_local*

# The checksum of the local output
cat out/runbook_local* | sort | shasum -a 256
```

Write that checksum down. You will compare the BigQuery checksum against
it.

### Step 1 — prepare the GCP side

```bash
export PROJECT=YOUR_PROJECT_ID
export REGION=us-central1
export BUCKET=YOUR_BUCKET
export DATASET=YOUR_DATASET
export TEMPLATE=gs://$BUCKET/templates/orders-to-bq.py
export RUN_ID=$(date +%Y%m%d-%H%M%S)

# The dataset
bq mk --project_id=$PROJECT --location=$REGION $DATASET

# Upload the input
gcloud storage cp ./sample_data/orders.csv gs://$BUCKET/orders.csv

# The template
gcloud dataflow flex-template build orders-to-bq \
  --project=$PROJECT --region=$REGION \
  --template-file=./templates/orders_to_bigquery.py \
  --template-file-gcs-path=$TEMPLATE \
  --metadata="version=1.0.0,run=$RUN_ID" \
  --temp-location=gs://$BUCKET/dataflow/temp \
  --staging-location=gs://$BUCKET/dataflow/staging \
  --service-account=dataflow-worker@$PROJECT.iam.gserviceaccount.com

# Confirm the template landed
gcloud storage ls gs://$BUCKET/templates/
gcloud dataflow templates describe orders-to-bq \
  --project=$PROJECT --region=$REGION
```

### Step 2 — submit

```bash
JOB_ID=$(gcloud dataflow flex-template run orders-to-bq \
  --project=$PROJECT --region=$REGION \
  --template=$TEMPLATE \
  --temp-location=gs://$BUCKET/dataflow/temp/$RUN_ID \
  --staging-location=gs://$BUCKET/dataflow/staging/$RUN_ID \
  --service-account=dataflow-worker@$PROJECT.iam.gserviceaccount.com \
  --parameters="input=gs://$BUCKET/orders.csv,bq-table=$PROJECT.$DATASET.orders_by_region,event-date=2026-01-01" \
  --worker-machine-type=n1-standard-2 \
  --max-workers=10 \
  --min-workers=1 \
  --autoscaling_algorithm=Basic \
  --wait=false \
  --format='value(job.id)')

echo "submitted: $JOB_ID"
```

### Step 3 — watch

```bash
# Poll the state
while true; do
  STATE=$(gcloud dataflow jobs describe $JOB_ID --project=$PROJECT \
    --format='value(status.state)')
  echo "$(date +%H:%M:%S) $STATE"
  case "$STATE" in
    JOB_STATE_DONE|JOB_STATE_FAILED|JOB_STATE_CANCELLED) break ;;
  esac
  sleep 20
done
```

Watch the metrics while it runs:

```bash
gcloud dataflow jobs describe $JOB_ID --project=$PROJECT --format=json \
  | jq '.metrics | {
           cpu: .estimatedCpuSeconds,
           max_workers: .maxWorkers,
           current_workers: .currentWorkers,
           worker_health: .workerHealth,
           input_bytes: .inputBytes,
           output_bytes: .outputBytes
         }'
```

If it fails:

```bash
gcloud logging read \
  "resource.type=cloud_dataflow_job AND resource.labels.job_id=$JOB_ID AND severity>=ERROR" \
  --project=$PROJECT --limit=20 --sort-by="~timestamp" \
  --format='value(textPayload)'
```

### Step 4 — verify

```bash
bq query --project_id=$PROJECT --use_legacy_sql=false --format=pretty \
  "SELECT region, order_count, revenue_eur
   FROM \`$PROJECT.$DATASET.orders_by_region\`
   ORDER BY revenue_eur DESC"
```

The row count and the values must match the local run exactly.

### Step 5 — the full verification suite

```bash
bq query --project_id=$PROJECT --use_legacy_sql=false --format=pretty "
SELECT
  COUNT(*) AS rows_in_table,
  COUNT(DISTINCT region) AS distinct_regions,
  COUNTIF(region IS NULL) AS null_region,
  COUNTIF(order_count IS NULL) AS null_count,
  COUNTIF(revenue_eur IS NULL) AS null_revenue,
  SUM(order_count) AS total_orders,
  ROUND(SUM(revenue_eur), 2) AS total_revenue,
  SUM(FARM_FINGERPRINT(
    CONCAT(region, '|', CAST(order_count AS STRING), '|',
           CAST(revenue_eur AS STRING)))) AS checksum
FROM \`$PROJECT.$DATASET.orders_by_region\`"
```

Compare `checksum` against the local `shasum` output. Different algorithms
produce different hashes, so compare the *structure* — the row count, the
distinct region count, and the total revenue must match to the cent.

Check the partitions:

```bash
bq query --project_id=$PROJECT --use_legacy_sql=false --format=pretty \
  "SELECT partition_id, total_rows, creation_time
   FROM \`$PROJECT.$DATASET.INFORMATION_SCHEMA.PARTITIONS\`
   WHERE table_name = 'orders_by_region'
   ORDER BY partition_id DESC"
```

### Step 6 — the run ledger

Store the checksum so tomorrow's run can be compared against it:

```sql
CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.YOUR_DATASET.orders_by_region_runs` (
  run_id STRING,
  run_timestamp TIMESTAMP,
  job_id STRING,
  rows_in_table INT64,
  checksum INT64,
  total_revenue FLOAT64
);
```

```bash
bq query --project_id=$PROJECT --use_legacy_sql=false "
INSERT INTO \`$PROJECT.$DATASET.orders_by_region_runs\`
(run_id, run_timestamp, job_id, rows_in_table, checksum, total_revenue)
SELECT
  '$RUN_ID',
  CURRENT_TIMESTAMP(),
  '$JOB_ID',
  COUNT(*),
  SUM(FARM_FINGERPRINT(
    CONCAT(region, '|', CAST(order_count AS STRING), '|',
           CAST(revenue_eur AS STRING)))),
  SUM(revenue_eur)
FROM \`$PROJECT.$DATASET.orders_by_region\`"
```

### Step 7 — clean up

```bash
# The temp and staging objects for this run
gcloud storage rm -r gs://$BUCKET/dataflow/temp/$RUN_ID
gcloud storage rm -r gs://$BUCKET/dataflow/staging/$RUN_ID

# Confirm the job's cost
gcloud dataflow jobs describe $JOB_ID --project=$PROJECT --format=json \
  | jq '.metrics.estimatedCpuSeconds'

# The staging table, if you used the promotion pattern
bq query --project_id=$PROJECT --use_legacy_sql=false \
  "DROP TABLE IF EXISTS \`$PROJECT.$DATASET.orders_by_region__staging_$RUN_ID\`"
```

### The hybrid pattern, end to end

Beam for the edge, BigQuery for the middle:

```bash
# 1. Beam reads the raw file and writes a clean, narrow table
gcloud dataflow flex-template run orders-to-bq \
  --project=$PROJECT --region=$REGION \
  --template=$TEMPLATE \
  --temp-location=gs://$BUCKET/dataflow/temp/$RUN_ID \
  --staging-location=gs://$BUCKET/dataflow/staging/$RUN_ID \
  --service-account=dataflow-worker@$PROJECT.iam.gserviceaccount.com \
  --parameters="input=gs://$BUCKET/orders.csv,bq-table=$PROJECT.$DATASET.orders_clean" \
  --wait=false

# 2. BigQuery does the aggregation and the serving
bq query --project_id=$PROJECT --use_legacy_sql=false "
CREATE OR REPLACE TABLE \`$PROJECT.$DATASET.orders_by_region\`
PARTITION BY DATE(event_date)
CLUSTER BY region
AS
SELECT
  event_date,
  region,
  COUNT(*) AS order_count,
  SUM(revenue_eur) AS revenue_eur
FROM \`$PROJECT.$DATASET.orders_clean\`
GROUP BY event_date, region"
```

Beam did the part SQL could not: reading a non-BigQuery file, parsing
malformed rows, dropping bad ones, and converting currencies using a
lookup table. BigQuery did the part Beam does badly: the aggregation, over
data that is already there, in one statement, for pennies.

---

## 🛠️ Common Errors and Fixes

### The job succeeded but the table is empty

```text
Query results: 0 rows
```

Check, in this order:

```bash
# 1. Did the source produce anything?
gcloud dataflow jobs describe $JOB_ID --project=$PROJECT --format=json \
  | jq '.metrics | {input_bytes: .inputBytes, elements: .elements}'

# 2. Is the table the one you think?
bq query --project_id=$PROJECT --use_legacy_sql=false \
  "SELECT table_name FROM \`$PROJECT.$DATASET.INFORMATION_SCHEMA.TABLES\`
   WHERE table_name LIKE 'orders%'"
```

`input_bytes` at 0 means the source path was wrong. A non-zero input with
zero elements means a filter dropped everything.

### The job wrote to a different table than expected

The `--parameters` value was truncated or mis-quoted. A table reference
with a typo in the dataset name creates a *different* table, not an error.

```bash
bq query --project_id=$PROJECT --use_legacy_sql=false \
  "SELECT table_name, creation_time
   FROM \`$PROJECT.$DATASET.INFORMATION_SCHEMA.TABLES\`
   ORDER BY creation_time DESC LIMIT 10"
```

### The checksum differs from yesterday's

This is the important one. Do **not** dismiss it. Determine whether the
*input* changed:

```sql
SELECT COUNT(*), SUM(order_count), ROUND(SUM(revenue_eur), 2)
FROM `YOUR_PROJECT_ID.YOUR_DATASET.orders_by_region_runs`
WHERE run_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY run_date DESC;
```

If the input row count changed, the output *should* change. If the input
is identical and the output is not, the pipeline is non-deterministic —
look for a `DoFn` that reads a clock, calls a random source, or iterates
over an unordered set.

### `Only DML statements are allowed in scripts`

```text
Error while reading data: Only DML statements are allowed in scripts
```

`bq query` with a multi-statement string needs `--use_legacy_sql=false` and
a `flags` file, or each statement run separately. Split the DDL and the
DML.

### The verification query scans the whole table

```text
Query exceeded maximum bytes billed for this project
```

The table is unpartitioned, or the query is missing a partition filter.
Add the filter:

```sql
WHERE event_date = '2026-01-01'
```

and check the table is partitioned.

### `LOADED` state but no rows

A BigQuery load job can report `SUCCESS` with zero rows if the source file
was empty. Check the job's own logs:

```bash
gcloud logging read \
  "resource.type=cloud_dataflow_job AND resource.labels.job_id=$JOB_ID" \
  --project=$PROJECT --limit=50 --sort-by="~timestamp" \
  --format='value(textPayload)' | grep -i "load job\|rows\|empty"
```

### `Resource has been exhausted (e.g. 'quota exceeded')`

```text
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded for quota
'BigQuery Jobs per project per day'
```

You are submitting too many BigQuery load jobs. Raise the quota, or batch
the writes by increasing `max_rows_per_batch` on the sink.

### The staging table has the data but the production table does not

The promotion step failed or was never run. Re-run it — that is the whole
point of the staging pattern:

```sql
BEGIN TRANSACTION;
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.YOUR_DATASET.orders_by_region`
PARTITION BY DATE(event_date)
CLUSTER BY region
AS SELECT * FROM `YOUR_PROJECT_ID.YOUR_DATASET.orders_by_region__staging`;
COMMIT TRANSACTION;
```

### The job is far more expensive than expected

Read `estimated_cpu_seconds` and compute the cost. Then look for the
usual causes: `--max-workers` set far too high (the autoscaler grew to the
ceiling and stayed), a `GroupByKey` that materialised a huge group, or a
`DoFn` making a network call per element.

---

## 💡 Production Notes

- **Automate the checklist, do not run it by hand.** A shell script that
  submits, polls, verifies, and exits non-zero on any check is worth more
  than a runbook in a wiki. The checks are mechanical; make them
  mechanical.
- **Alert on the anomaly, not only on the failure.** "The job failed" is
  the easy alert. "The job took 4× longer" and "the checksum changed" are
  the alerts that catch real problems. Every item on the checklist is
  alertable.
- **Keep the run ledger.** A table with one row per run — timestamp, job
  ID, row count, checksum, total — is the cheapest observability you will
  ever build, and it is the artefact that makes "is this number right?"
  answerable in seconds.
- **Compute the BigQuery SQL alternative before you deploy.** If the input
  is already in BigQuery and the logic is SQL-shaped, do the arithmetic.
  A 12× cost difference and a much smaller operational surface area is a
  strong argument, and the correct answer is sometimes "don't use Beam".
- **Use the hybrid pattern by default.** Beam for parsing, enrichment and
  the edges; BigQuery for aggregation and serving. It is the best cost
  profile and it plays to each tool's strengths.
- **Promote atomically.** `CREATE OR REPLACE ... AS SELECT` inside a
  transaction is atomic and costs one extra write. For a table a
  dashboard reads, that is worth it every time.
- **Watch the storage.** Partitioned tables with `partition_expiration_days`
  are bounded. Unpartitioned tables, and partitioned ones without
  expiration, grow forever and the BigQuery bill follows them.
- **Delete the temp and staging prefixes.** Dataflow does not always
  clean up after itself, especially after a failure. A lifecycle rule on
  `dataflow/temp/` is two lines of JSON and prevents an unnoticed storage
  bill.
- **Budget for the small jobs.** A one-cent job that runs 500 times a day
  is $15 a month. Small jobs are cheap individually and add up
  relentlessly when there are many of them. The lever is the worker count.

---

## 🔑 Key Takeaways

- The runbook is **local proof → build → submit → watch → verify →
  promote → clean up**. Step 0 and step 4 are the ones people skip, and
  they are the ones that matter.
- **BigQuery SQL is cheaper and simpler for pure-SQL logic over data that
  is already in BigQuery** — sometimes by 12×. Beam earns its cost when
  the logic is not SQL-expressible, the input is not in BigQuery, or the
  same code must run in batch and streaming.
- The **hybrid pattern** — Beam for the edges, BigQuery for the middle — is
  the best cost profile and the best fit for each tool.
- Verify with **row counts, null rates, MIN/MAX/SUM, a checksum, and
  partition coverage**. The checksum needs a ledger of previous runs to be
  worth anything.
- The cost of a small batch job is **under a cent**, and it is dominated
  by worker startup. At scale, Dataflow is 85–95% of the total, and the
  cost is linear in data volume.
- The correctness checklist has **14 items**, and two of them — "runtime in
  the expected range" and "checksum matches or the change is explained" —
  catch failures that `FAILED` never will.

---

## 📚 Practice Exercises

1. **Write the verification script.** Build
   `scripts/verify_orders.sh` that takes a project, dataset and table, runs
   all five verification queries, compares the row count and total revenue
   against values passed as arguments, and exits non-zero on any
   mismatch. Run it against a deliberately corrupted table to prove it
   fails.

2. **Cost comparison, done properly.** Deploy the pipeline against the
   5,000-row sample and against a synthetic 500,000-row dataset. Record
   `estimated_cpu_seconds` and the BigQuery write bytes for each. Write the
   BigQuery SQL equivalent for each. Produce a table with four columns —
   Beam, BigQuery SQL, difference, and the crossover data volume above
   which Beam is the better choice. Show your reasoning.

3. **The hybrid pattern, complete.** Build a two-stage pipeline: a Beam
   flex template that reads the raw CSV and writes a clean table, and a
   BigQuery scheduled query that aggregates it. Deploy both, schedule the
   query, and verify the whole chain end to end. Then explain what breaks
   if the Beam job runs twice in a day and the query runs hourly.

4. **Anomaly detection.** Extend the run ledger with a table of expected
   values, and write a query that flags any run whose row count, checksum
   or total revenue deviates from the trailing 7-day median by more than
   2%. Run it against the ledger and show what it flags.

5. **The staging promotion.** Implement the full staging pattern: a
   template that writes to `orders_by_region__staging_<run_id>`, a
   verification step, and an atomic promotion script. Make the promotion
   script refuse to run if the verification failed, and make it safe to
   run twice.

6. **Argument for or against Beam.** Write a one-page memo to your team
   recommending either Beam or BigQuery SQL for a specific pipeline of
   your own. Include the data location, the logic, the batch/streaming
   requirement, and the cost arithmetic. The memo must be defensible
   either way — the point is the reasoning, not the conclusion.

---

## 📖 Further Reading

- Google Cloud BigQuery: scheduled queries — https://cloud.google.com/bigquery/docs/scheduled-queries
- Google Cloud BigQuery: partition and cluster tables — https://cloud.google.com/bigquery/docs/partitioned-tables
- Google Cloud BigQuery: `FARM_FINGERPRINT` — https://cloud.google.com/bigquery/docs/reference/standard-sql/string_functions#farm_fingerprint
- Google Cloud Dataflow: monitoring a pipeline — https://cloud.google.com/dataflow/docs/guides/monitoring
- Google Cloud BigQuery: cost optimisation — https://cloud.google.com/bigquery/docs/best-practices-cost-optimization
- Apache Beam: Beam SQL — https://beam.apache.org/documentation/transforms/sql/
