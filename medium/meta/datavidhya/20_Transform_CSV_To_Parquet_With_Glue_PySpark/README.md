# 20 — Transform CSV to Parquet with Glue PySpark

A runnable, **offline-first** mirror of the AWS Skill Builder lab
**"Transform CSV to Parquet with Glue PySpark."** Six stages, eight shell
scripts that map exactly to the lab's "click in the console" instructions,
plus a pytest suite that drives the same PySpark script against a local
SparkSession. No AWS credentials needed for verification.

```
                       ┌──────────────────────────────────┐
                       │   glue-etl-lab-bucket-…           │
                       │                                    │
                       │   raw/sales_transactions.csv       │
                       │       ↓ Glue catalog table          │
                       │       (all columns = string)        │
                       └───────────────┬────────────────────┘
                                       │  spark.read.csv + cast
                                       ▼
                       ┌──────────────────────────────────┐
                       │   Glue job (Spark on AWS)         │
                       │                                    │
                       │   glue_jobs/sales_etl_job.py:      │
                       │     1. cast quantity, unit_price   │
                       │     2. derive total_amount         │
                       │     3. filter status='completed'   │
                       │     4. write Parquet, partitionBy  │
                       │        order_date                  │
                       └───────────────┬────────────────────┘
                                       │  write.parquet(partitionBy=date)
                                       ▼
                       ┌──────────────────────────────────┐
                       │   curated/sales/                   │
                       │       order_date=2026-09-20/      │
                       │         part-00000.parquet         │
                       │       order_date=2026-09-21/      │
                       │       ...                          │
                       │                                    │
                       │   Glue catalog table:              │
                       │     curated_sales (with partition) │
                       └───────────────┬────────────────────┘
                                       │
                                       ▼
                       ┌──────────────────────────────────┐
                       │   Athena (engine v3)               │
                       │     SELECT ... FROM curated_sales │
                       │     (partition-pruning on date)   │
                       └────────────────────────────────────┘
```

## Files

| Path                                              | Purpose                                  |
|---------------------------------------------------|------------------------------------------|
| `sample_data/raw_sales_transactions.csv`          | The 15-row seed CSV the lab provisions (with 2 cancelled + 1 pending) |
| `glue_jobs/sales_etl_job.py`                       | The actual PySpark ETL script -- runs both in Glue (prod) and via subprocess (offline) |
| `01_csv_to_parquet_glue_pyspark.py`               | Self-asserting driver (6 stages, 17 checks) |
| `scripts/00_set_lab.sh`                           | Helper: set BUCKET / DATABASE / ROLE_ARN   |
| `scripts/01_inspect_raw.sh` through `06_teardown.sh` | Six stage scripts (one per lab stage)   |
| `scripts/run_all.sh`                              | Optional: run stages 1–5 in sequence      |
| `tests/conftest.py`                               | Pytest fixtures: shared SparkSession, tempdir |
| `tests/test_etl.py`                               | 10 pytest tests, no AWS creds             |
| `README.md`                                       | This file                                |

## The 6 lab stages — mapped to artifacts

| Stage | Lab step                                                       | Artifact                                |
|-------|----------------------------------------------------------------|-----------------------------------------|
| 1     | Inspect the raw CSV + the (all-string) Glue catalog table       | `01_inspect_raw.sh`, `test_stage1_*`    |
| 2     | Define the Glue job with IAM role + script location            | `02_create_job.sh`, `test_stage2_*`     |
| 3     | Run the job, wait for SUCCEEDED                                | `03_run_job.sh`, `test_stage3_*`        |
| 4     | Register the curated Parquet as a Glue catalog table           | `04_register_curated.sh`, `test_stage4_*` |
| 5     | Query the curated output via Athena (count + top + per-day)   | `05_query_curated.sh`, `test_stage5_*`  |
| 6     | Re-run the job; prove idempotency                              | driver stage 6, `test_stage6_*`         |

## Run it offline (no AWS account)

```bash
cd medium/meta/datavidhya/20_Transform_CSV_To_Parquet_With_Glue_PySpark/

# Self-asserting driver -- 17 checks, all PASS.
../../../.env/bin/python 01_csv_to_parquet_glue_pyspark.py

# pytest -- 10 tests, all PASS.
../../../.env/bin/python -m pytest tests/ -v
```

The driver and tests run the **same** `glue_jobs/sales_etl_job.py` script
that production Glue runs. The only difference is the input/output URLs:
production uses `s3://$BUCKET/...`; offline uses `file://`. The script's
own SparkSession replaces Glue's runtime SparkContext.

## Run it against a real AWS account

```bash
export BUCKET=glue-etl-lab-bucket-a1b2c3
export DATABASE=sales_db_a1b2c3
export ROLE_ARN="arn:aws:iam::123456789012:role/GlueEtlLabRole-Ab3xYz"
export WORKGROUP=<Athena workgroup from the lab panel>
export AWS_REGION=us-east-1

./scripts/run_all.sh      # stages 1-5
./scripts/06_teardown.sh  # explicit teardown
```

`run_all.sh` runs the five mutating scripts in order. Stage 0 (capture
resource names) is run separately because it requires pasting from the
lab console. Stage 6 (teardown) is also separate so you can inspect the
output before destroying it.

## What each lab stage actually does

### Stage 1 — Inspect the raw CSV

The lab provisions `s3://$BUCKET/raw/sales_transactions.csv` plus a
**pre-provisioned** Glue catalog table `sales_db_xxx.raw_sales_transactions`
where every column is typed `string` (because the raw CSV was untyped).
The first spark assertion: `unit_price` of the first row is the text
`"29.99"`, not the number `29.99`.

### Stage 2 — Author the ETL script (paste into Glue Script editor)

The script does four things:

```python
def transform(df):
    df = df.withColumn("quantity",   col("quantity").cast(IntegerType()))
    df = df.withColumn("unit_price", col("unit_price").cast(DoubleType()))
    df = df.withColumn("total_amount", col("quantity") * col("unit_price"))
    df = df.withColumn("order_date",   to_date(col("order_date"), "yyyy-MM-dd"))
    df = df.filter(col("status") == "completed").drop("status")
    return df
```

Three ID columns (`transaction_id`, `customer_id`, `product_id`) stay
**string** even though they look numeric -- `CAST('C042' AS INT)` is
`null`, not zero. The script trusts Glue's default behaviour: don't
shoot your own IDs in the foot.

### Stage 3 — Configure + run the Glue job

```bash
aws glue create-job \
    --name sales-etl-q20 \
    --role "$ROLE_ARN" \
    --command "Name=glueetl,ScriptLocation=s3://$BUCKET/scripts/sales_etl_job.py" \
    --glue-version 4.0 \
    --worker-type Standard \
    --number-of-workers 2
```

`aws glue start-job-run` returns a `JobRunId` immediately; the job runs
on AWS-provisioned Spark workers. The lab polls `GetJobRun.JobRunState`
until it flips to `SUCCEEDED`.

### Stage 4 — Register the curated Parquet as a catalog table

The job wrote `s3://$BUCKET/curated/sales/order_date=YYYY-MM-DD/*.parquet`
but Athena can't see it without a catalog entry. Either:
- Run a Glue crawler, **or**
- `aws glue create-table` with the known schema.

The lab uses the latter (faster, deterministic). The catalog table has
`PartitionKeys: [{Name: order_date, Type: date}]` so Athena knows to
prune partitions on date predicates.

### Stage 5 — Athena queries

```sql
SELECT customer_id, COUNT(*) AS orders, SUM(total_amount) AS spend
FROM curated_sales
GROUP BY customer_id
ORDER BY spend DESC LIMIT 5;
```

The lab's expected top row: `C055` with $4799.90 across 3 orders
(`T0004` + `T0009` + `T0014`).

The partition-pruning demo:

```sql
SELECT order_date, SUM(total_amount) AS revenue
FROM curated_sales
WHERE order_date BETWEEN DATE '2026-09-20' AND DATE '2026-09-22'
GROUP BY order_date;
```

Athena reads **only** the three partition directories in the range, not
all eight. At scale that's the difference between scanning 3 GB and
scanning 300 GB.

### Stage 6 — Re-run the job; prove idempotency

`mode("overwrite")` drops the destination directory and rewrites it.
Re-running with the same input produces the same 12 rows and 8
partitions, with no duplication. This is the property the lab's
"--job-bookmark-option" flag is designed to preserve between runs:
Glue remembers which partitions it has processed, so a re-run only
re-processes partitions whose source data changed.

## Traps the lab expects you to hit

- **String IDs that look numeric.** `C042`, `T0001`, `P100` -- they look
  like integers but they're IDs. Casting to `INT` produces `null` and
  silently breaks every downstream aggregation. The ETL script keeps
  them as string.
- **`status` is dropped after the filter.** Once you filter to
  `status = 'completed'`, the column is constant -- drop it. Keeping
  it bloats Parquet with a single-value column.
- **Partitioning by a unique column.** Don't `partitionBy(transaction_id)`.
  That creates 12 directories (one per row); Athena's partition-pruning
  then has to open 12 files to answer any query. Partition only by low-
  cardinality, queryable columns (here, `order_date` with 8 values).
- **`mode("overwrite")` on partitioned data.** Spark drops the whole
  destination directory then rewrites it. If the script crashes mid-
  write, the curated output is gone. For real production use Glue job
  bookmarks + `mode("append")`, or write to a staging prefix then
  rename atomically.
- **Spark's strict casting.** `cast(IntegerType())` on a string that
  doesn't parse produces `null`, not zero. The script's job is to
  validate before the cast, or accept the null and let downstream
  queries filter it out.

## Going to production

Four things to add before this leaves a lab:

1. **Job bookmarks.** `--job-bookmark-option=job-bookmark-enable` lets
   Glue remember which partitions it has processed. Re-running only
   re-processes changed partitions.
2. **Schema evolution.** Spark's Parquet writer can evolve the schema
   (`mergeSchema=true`) so adding a column doesn't break the job.
3. **Data Quality rules.** Glue Data Quality rules can assert
   `total_amount > 0`, `quantity > 0`, and `order_date` parses as
   `date` BEFORE the curated output is written. Lab doesn't show this.
4. **Worker type tuning.** The lab uses 2 Standard workers ($0.44/DPU-h
   each). For a 4-hour job that's $3.52. Switching to G.1X (1 DPU,
   smaller memory footprint per worker) for streaming workloads, or
   G.2X (2 DPUs) for memory-bound joins, is where the production cost
   wins hide.

## Verification

The lab's "lab complete" check is: the curated Glue table
`sales_db_xxx.curated_sales` has 12 rows, 8 partitions, every row's
`total_amount` equals `quantity * unit_price`, and Athena returns
`C055` as the top customer with $4799.90. The driver and pytest suite
exercise all four without AWS. The shell scripts are the live-account
equivalent.
