# 23 — Query S3 Data with Amazon Athena

A runnable, **offline-first** mirror of the AWS Skill Builder lab
**"Query S3 Data with Amazon Athena."** Six stages, seven shell scripts
that map exactly to the lab's "click in the console" instructions, plus
a pytest suite that drives the same DuckDB-backed SQL. No AWS
credentials needed for verification.

```
                        ┌──────────────────────────────────┐
                        │   s3://athena-taxi-playground-bucket-…
                        │     taxi/yellow_taxi_sample.csv
                        │     (15 columns, 24 rows, header)
                        └───────────────┬────────────────────┘
                                        │
                                        │  CREATE EXTERNAL TABLE
                                        │    LOCATION 's3://…/taxi/'
                                        │    STORED AS TEXTFILE
                                        ▼
                        ┌──────────────────────────────────┐
                        │   Glue Data Catalog               │
                        │     Database: taxi_db              │
                        │     Table:    taxi_trips (15 cols)│
                        │     Pointer:  s3://…/taxi/         │
                        │              (NO data copied)      │
                        └───────────────┬────────────────────┘
                                        │  SQL at query time
                                        ▼
                        ┌──────────────────────────────────┐
                        │   Amazon Athena (Trino engine)    │
                        │     Serverless, pay-per-scan       │
                        │     workgroup: taxi-playground-…   │
                        │     results:  s3://…/query-results/│
                        └────────────────────────────────────┘
```

## Files

| Path                                                | Purpose                                  |
|-----------------------------------------------------|------------------------------------------|
| `sample_data/yellow_taxi_sample.csv`                | 24-row NYC taxi sample (15 cols)         |
| `01_query_s3_data_with_amazon_athena.py`           | Self-asserting driver (6 stages, 32 checks) |
| `scripts/00_set_lab.sh`                             | Helper: set BUCKET / WORKGROUP            |
| `scripts/01_inspect_s3.sh` through `06_teardown.sh` | Six stage scripts                         |
| `scripts/run_all.sh`                                | Optional: run stages 1–5 in sequence      |
| `tests/conftest.py`                                 | Pytest fixtures: shared DuckDB connection |
| `tests/test_athena.py`                              | 14 pytest tests, no AWS creds             |
| `README.md`                                         | This file                                |

## The 6 lab stages — mapped to artifacts

| Stage | Lab step                                                       | Artifact                                |
|-------|----------------------------------------------------------------|-----------------------------------------|
| 1     | Inspect the CSV in S3                                           | `01_inspect_s3.sh`, `test_stage1_*`     |
| 2     | Pick a workgroup + create the Glue database                     | `02_create_database.sh`, `test_stage2_*` |
| 3     | CREATE EXTERNAL TABLE (schema on read)                          | `03_create_table.sh`, `test_stage3_*`  |
| 4     | Run 5 analytical queries (count, by payment, by zone, by day)  | `04_run_queries.sh`, `test_stage4_*`   |
| 5     | Challenge query (zone-pair breakdown)                          | `05_challenge_query.sh`, `test_stage5_*` |
| 6     | DROP DATABASE + clean Athena results                            | `06_teardown.sh`, `test_stage6_*`      |

## Run it offline (no AWS account)

```bash
cd medium/meta/datavidhya/23_Query_S3_Data_With_Amazon_Athena/

# Install DuckDB once (Athena's offline mirror).
pip install duckdb

# Self-asserting driver -- 32 checks, all PASS.
../../../.env/bin/python 01_query_s3_data_with_amazon_athena.py

# pytest -- 14 tests, all PASS.
../../../.env/bin/python -m pytest tests/ -v
```

The driver and tests run the **same** SQL an Athena query editor
would. DuckDB's dialect intentionally overlaps with Trino's (Athena's
engine), so the queries are portable with at most a `database -> schema`
rename.

## Run it against a real AWS account

```bash
export BUCKET=athena-taxi-playground-bucket-a1b2c3
export WORKGROUP=taxi-playground-Ab3xYz
export DATABASE=taxi_db
export AWS_REGION=us-east-1

./scripts/run_all.sh      # stages 1-5
./scripts/06_teardown.sh  # explicit teardown
```

`run_all.sh` runs the five mutating stages in sequence. Stage 0 (capture
resource names) is run separately because it requires pasting from the
lab console. Stage 6 (teardown) is also separate so you can inspect the
Athena results before destroying them.

## What each lab stage actually does

### Stage 1 — Inspect the S3 CSV

`aws s3 ls s3://$BUCKET/taxi/` shows the lab's seed file. The CSV has
15 columns: vendor, pickup/dropoff datetime, passenger count, distance,
zones, rate code, payment type, and a full money breakdown (fare,
extra, mta tax, tip, tolls, total).

### Stage 2 — Pick a workgroup + create the database

The lab pre-creates an Athena workgroup with a query-results location.
The user pastes the workgroup name, then creates a Glue database
(`aws glue create-database --database-input '{"Name":"taxi_db"}'`).
Athena reads catalogs from Glue, so the database lives in Glue.

### Stage 3 — CREATE EXTERNAL TABLE (the lab's centerpiece)

```sql
CREATE EXTERNAL TABLE taxi_trips (
    vendor_id          INT,
    pickup_datetime    TIMESTAMP,
    ...
    total_amount       DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://$BUCKET/taxi/'
TBLPROPERTIES ('skip.header.line.count'='1')
```

This DDL just **describes** the CSV. No data is copied. Athena reads
the file at query time. Drop the table and the CSV is untouched.

### Stage 4 — Run the 5 analytical queries

```sql
-- Total trips
SELECT COUNT(*) FROM taxi_trips;                                      -- 24

-- By payment type
SELECT payment_type, COUNT(*), AVG(fare_amount), AVG(tip_amount)
FROM taxi_trips GROUP BY payment_type;                                -- 4 buckets

-- Top pickup zones by revenue
SELECT pickup_zone, SUM(total_amount) AS revenue
FROM taxi_trips GROUP BY pickup_zone ORDER BY revenue DESC LIMIT 5;

-- Per-day distribution
SELECT DATE(pickup_datetime), COUNT(*) FROM taxi_trips
GROUP BY 1 ORDER BY 1;                                               -- 3 days

-- Cash trips with zero tips (proves the cash/no-tip trap)
SELECT COUNT(*) FROM taxi_trips
WHERE payment_type='CSH' AND tip_amount=0;                            -- 4
```

### Stage 5 — Challenge query

The lab asks the user to write a query that finds the busiest
pickup-zone → dropoff-zone pairs (excluding zero-passenger trips):

```sql
SELECT pickup_zone, dropoff_zone, COUNT(*) AS trips,
       ROUND(AVG(trip_distance), 2) AS avg_miles
FROM taxi_trips
WHERE passenger_count > 0
GROUP BY pickup_zone, dropoff_zone
ORDER BY trips DESC LIMIT 5;
```

### Stage 6 — Teardown

`aws glue delete-database --name taxi_db` removes all tables in the
database (single transaction). Athena's per-query results are CSVs in
`s3://$BUCKET/query-results/`; the script cleans them up so the bucket
stays tidy for the next lab session.

## Traps the lab expects you to hit

- **`SELECT *` on the full table.** Athena charges per byte scanned.
  A `SELECT *` on a 24-row CSV is $0.00; on a 100 GB CSV it's $5.00.
  The lab's query panel intentionally filters to a few columns.
- **Forgetting the `LOCATION` clause.** Athena stores only the schema
  in Glue; the `LOCATION` is what binds it to S3. Without it, queries
  return 0 rows with no error.
- **Wrong types in the DDL.** `pickup_datetime TIMESTAMP` lets Athena
  use `DATE(pickup_datetime)`. `STRING` means you'd have to cast
  explicitly. The lab's DDL types columns aggressively to avoid this.
- **`STORED AS PARQUET` on a CSV.** Glue happily accepts this even
  though the file is text. Athena's reader then fails at query time
  with a `Not a Parquet file` error. The lab uses `STORED AS TEXTFILE`.
- **Cash tips = 0 is normal, not an error.** Cash riders don't enter
  tips on the terminal. `tip_amount=0` for `payment_type='CSH'` is the
  *expected* state, not a data quality flag.

## Going to production

Four things to add before this leaves a lab:

1. **Partition projection.** The lab's CSV is one file. Production
   partition-by-date (or by hour) so queries can prune. Athena's
   partition projection uses naming conventions (`taxi/year=2026/month=08/`)
   so you don't have to manage a partition table.
2. **Convert CSV → Parquet.** Parquet is ~10x smaller on disk and
   ~10x faster to scan because Athena reads only the columns the query
   selects. Use Glue (slot 20) to do the conversion.
3. **Workgroup byte caps.** Production workgroups enforce per-query
   byte-scanned caps ($1, $5, $10). The lab's workgroup has no cap.
4. **Athena views.** Production teams wrap repeated subqueries as
   `CREATE VIEW … AS` so analysts don't re-paste the same `WHERE`
   clause. The lab doesn't show this.

## Verification

The lab's "lab complete" check is: 24 trips in `taxi_trips`, four
payment-type buckets, top pickup zone `Midtown Center` with the
highest revenue, three distinct days (2026-08-15 → 2026-08-17), and
the cash/no-tip invariant (`COUNT(CSH ∩ tip=0) == 4`). The driver and
pytest suite exercise all five without AWS.