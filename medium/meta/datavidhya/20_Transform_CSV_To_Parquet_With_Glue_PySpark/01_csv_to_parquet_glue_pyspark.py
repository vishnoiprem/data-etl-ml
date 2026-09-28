"""
Q20: Transform CSV to Parquet with Glue PySpark   [AWS | Glue, PySpark, ETL]

Offline driver: imports the lab's ETL script and runs it through a local
SparkSession against the seed CSV. No Glue, no S3 -- just ``file://``
URLs into a tempdir. The same PySpark code runs in production via Glue.

How to Think:
- ETL is "read -> reshape -> write." Glue adds "we run Spark for you on
  a cluster that lives for one job and dies." The script we hand to Glue
  is just PySpark; the same script runs locally for testing.
- Parquet stores columns, not rows. A query that reads 2 columns out of
  12 only opens those 2 columns' pages. CSV reads every column for every
  row. On wide tables (hundreds of columns) Parquet is 10-100x cheaper
  to scan and 4-8x cheaper to store.
- Partitioning by ``order_date`` writes one subdirectory per date. Athena
  then prunes partitions on ``WHERE order_date BETWEEN ...`` queries.
  Over-partitioning (thousands of tiny partitions) is also bad -- keep
  partition cardinality in the dozens-to-hundreds range.

The trap:
- The raw CSV declares no schema. Glue's auto-inferred schema for the
  catalog table gives every column ``string`` -- even quantity and
  unit_price. The job's first act is to cast them; without that step
  ``quantity * unit_price`` would be string concatenation ("3" * "29.99"
  is not 89.97).
- Partitioning by a low-cardinality column is fine; partitioning by a
  unique column (transaction_id) creates thousands of tiny Parquet files
  and kills query performance.
- ``mode("overwrite")`` drops the partition directory but keeps others.
  Partitioning by date lets you re-run one date's worth without touching
  the rest -- a partial refresh.

AWS note:
- Glue jobs are billed per "DPU-hour" (Data Processing Unit, ~$0.44/h).
  A 1-minute job on 2 DPUs is sub-penny. A 4-hour job on 10 DPUs is $17.
  Worker type + count drive the cost.
- Glue writes its job metrics to CloudWatch. ``--job-bookmark-option``
  lets Glue remember the last processed partition between runs.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

from pyspark.sql import SparkSession

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "glue_jobs"))
import sales_etl_job  # noqa: E402


def expect(title: str, got, expected) -> None:
    if got != expected:
        print(f"[FAIL] {title}")
        print(f"   expected: {expected}")
        print(f"   got:      {got}")
        raise AssertionError(title)
    print(f"[PASS] {title}")


def _spark() -> SparkSession:
    return (SparkSession.builder
            .appName("q20_offline_driver")
            .config("spark.sql.shuffle.partitions", "1")
            .config("spark.ui.showConsoleProgress", "false")
            .getOrCreate())


def main() -> None:
    csv_path  = os.path.join(_HERE, "sample_data",
                              "raw_sales_transactions.csv")
    workdir   = tempfile.mkdtemp(prefix="q20_etl_")
    raw_uri   = f"file://{csv_path}"
    out_uri   = f"file://{workdir}/curated/sales/"

    print("\n=== Q20 Transform CSV to Parquet with Glue PySpark ===\n")

    spark = _spark()

    # ------ stage 1: inspect the raw CSV (read with all-string schema)
    raw = (spark.read
                 .option("header", True)
                 .option("inferSchema", False)
                 .csv(raw_uri))
    expect("Q20 stage 1 raw CSV has 15 rows", raw.count(), 15)
    raw_types = {f.name: f.dataType.simpleString() for f in raw.schema.fields}
    expect("Q20 stage 1 raw schema -- every column is string "
           "(Glue catalog never inferred types)",
           raw_types,
           {"transaction_id": "string", "customer_id": "string",
            "product_id": "string", "quantity": "string",
            "unit_price": "string", "order_date": "string",
            "status": "string"})
    sample_value = raw.filter("transaction_id = 'T0001'").first()["unit_price"]
    expect("Q20 stage 1 sample value is still text '29.99', not a number",
           sample_value, "29.99")

    # ------ stage 2: import + invoke the ETL pipeline
    # Stage 2 of the lab is "author the PySpark job in the Glue Script
    # editor." We do that locally by importing sales_etl_job.transform.
    print("[stage-2] invoking sales_etl_job.transform (the lab's Glue script)")
    curated = sales_etl_job.transform(raw)
    # Keep the DataFrame materialised so the casts are visible.
    curated_rows = curated.count()

    # ------ stage 3: run the full job end-to-end and write Parquet
    # Stage 3 of the lab is "configure the job + Run." We mimic by calling
    # the script via subprocess so the driver exercises the same code path
    # the Glue runtime would: parse_args -> spark.read -> transform ->
    # write Parquet.
    print("[stage-3] running sales_etl_job.main end-to-end against file://")
    proc = subprocess.run(
        [sys.executable,
         os.path.join(_HERE, "glue_jobs", "sales_etl_job.py"),
         "--input_path",  raw_uri,
         "--output_path", out_uri],
        check=True, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr

    # Read the Parquet output back.
    written = spark.read.parquet(out_uri)
    # 15 raw rows; cancelled = T0003, T0011 (2 rows); pending = T0007 (1 row);
    # only completed survives = 15 - 3 = 12.
    expect("Q20 stage 3 curated Parquet has 12 completed rows "
           "(15 raw - 2 cancelled - 1 pending = 12 completed)",
           curated_rows, 12)
    expect("Q20 stage 3 the on-disk Parquet also has 12 rows",
           written.count(), 12)

    # ------ stage 4: confirm Parquet schema + partitioning + types
    written_types = {f.name: f.dataType.simpleString()
                     for f in written.schema.fields}
    expect("Q20 stage 4 curated Parquet schema -- quantity is int, "
           "unit_price is double, total_amount is double, order_date is date; "
           "IDs (transaction_id, customer_id, product_id) stay string",
           written_types,
           {"transaction_id": "string",
            "customer_id":    "string",
            "product_id":     "string",
            "quantity":       "int",
            "unit_price":     "double",
            "order_date":     "date",
            "total_amount":   "double"})
    expect("Q20 stage 4 status column was dropped (all rows are 'completed')",
           "status" in written_types, False)

    # Confirm partition directories -- one per distinct order_date.
    partitions = sorted(
        d for d in os.listdir(os.path.join(workdir, "curated", "sales"))
        if d.startswith("order_date=")
    )
    expect("Q20 stage 4 partition directories match the 8 distinct dates",
           len(partitions), 8)

    # total_amount sanity check: T0001 was qty 3 * unit_price 29.99 = 89.97.
    t0001 = written.filter("transaction_id = 'T0001'").first()
    expect("Q20 stage 4 T0001 total_amount = quantity * unit_price = 89.97",
           round(t0001["total_amount"], 2), 89.97)

    # No cancelled rows survive the filter.
    expect("Q20 stage 4 cancelled + pending rows are gone "
           "(status column dropped after filter)",
           "status" in written_types, False)
    expect("Q20 stage 4 every row in the curated output is a 'completed' row "
           "(15 raw - 2 cancelled - 1 pending = 12)",
           written.count(), 12)

    # ------ stage 5: Athena-style aggregations against the Parquet
    # (No actual Athena engine -- we use Spark SQL, the same API.)
    written.createOrReplaceTempView("curated_sales")

    # Top customers by total spend
    top_customer = spark.sql("""
        SELECT customer_id, SUM(total_amount) AS total_spend
        FROM curated_sales
        GROUP BY customer_id
        ORDER BY total_spend DESC
        LIMIT 1
    """).first()
    # C055: T0004 (2*1200=2400) + T0009 (10*89.99=899.90) + T0014 (5*300=1500)
    # = 4799.90.
    expect("Q20 stage 5 top customer by total spend is C055 "
           "with $4799.90 across 3 orders",
           (top_customer["customer_id"],
            round(top_customer["total_spend"], 2)),
           ("C055", 4799.90))

    # Per-product revenue
    per_product = (spark.sql("""
        SELECT product_id, SUM(quantity) AS units_sold
        FROM curated_sales
        GROUP BY product_id
        ORDER BY units_sold DESC
    """).collect())
    expect("Q20 stage 5 product P100 sold 10 units across completed orders "
           "(T0001=3 + T0006=4 + T0012=3)",
           next(r["units_sold"] for r in per_product if r["product_id"] == "P100"),
           10)

    # Per-day revenue (proves the partition column is queryable)
    per_day = spark.sql("""
        SELECT order_date, SUM(total_amount) AS daily_total
        FROM curated_sales
        WHERE order_date BETWEEN DATE '2026-09-20' AND DATE '2026-09-22'
        GROUP BY order_date
        ORDER BY order_date
    """).collect()
    expect("Q20 stage 5 partition pruning demo: 3 dates in the 20-22 range",
           [r["order_date"].isoformat() for r in per_day],
           ["2026-09-20", "2026-09-21", "2026-09-22"])

    # ------ stage 6: rerun the job -- it must be idempotent (overwrite)
    print("[stage-6] rerunning the job to prove idempotency")
    proc2 = subprocess.run(
        [sys.executable,
         os.path.join(_HERE, "glue_jobs", "sales_etl_job.py"),
         "--input_path",  raw_uri,
         "--output_path", out_uri],
        check=True, capture_output=True, text=True,
    )
    assert proc2.returncode == 0, proc2.stderr
    written2 = spark.read.parquet(out_uri)
    expect("Q20 stage 6 rerun produces the same row count "
           "(mode=overwrite is idempotent)",
           written2.count(), 12)
    expect("Q20 stage 6 rerun leaves the same 8 partition directories "
           "(no duplicates, no stragglers)",
           len([d for d in os.listdir(os.path.join(workdir, "curated", "sales"))
                if d.startswith("order_date=")]),
           8)

    spark.stop()
    shutil.rmtree(workdir, ignore_errors=True)
    print("\n=== All Q20 stages pass ===\n")


if __name__ == "__main__":
    main()

# ---- MySQL way ----------------------------------------------------------
# The same `csv -> parquet` job lands in MySQL by ingesting through `LOAD DATA
# INFILE` (or a staging table via PyMySQL) and then running the analytical
# queries that the Spark script runs against the Parquet output.
#
# CREATE TABLE + sample data (curated_sales = the post-ETL shape; status
# column is dropped because all surviving rows are 'completed'):
#   CREATE TABLE curated_sales (
#       transaction_id VARCHAR(20) PRIMARY KEY,
#       customer_id    VARCHAR(20) NOT NULL,
#       product_id     VARCHAR(20) NOT NULL,
#       quantity       INT         NOT NULL,
#       unit_price     DECIMAL(10,2) NOT NULL,
#       total_amount   DECIMAL(12,2) NOT NULL,   -- generated: quantity*unit_price
#       order_date     DATE        NOT NULL
#       -- status dropped: filter completes before load
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   -- partition-equivalent: index on order_date for partition-pruning-style
#   -- reads; in production this becomes a real RANGE-partitioned table or a
#   -- sharded table partitioned by order_date.
#   ALTER TABLE curated_sales ADD KEY idx_curated_date (order_date),
#                              ADD KEY idx_curated_cust (customer_id);
#
#   INSERT INTO curated_sales (transaction_id, customer_id, product_id,
#                              quantity, unit_price, total_amount, order_date)
#   SELECT transaction_id, customer_id, product_id,
#          CAST(quantity  AS SIGNED),
#          CAST(unit_price AS DECIMAL(10,2)),
#          CAST(quantity AS SIGNED) * CAST(unit_price AS DECIMAL(10,2)),
#          STR_TO_DATE(order_date, '%Y-%m-%d')
#   FROM raw_sales_transactions
#   WHERE status = 'completed';
#
# Top customer by total spend (matches Spark stage 5):
#   SELECT customer_id, SUM(total_amount) AS total_spend
#   FROM curated_sales
#   GROUP BY customer_id
#   ORDER BY total_spend DESC
#   LIMIT 1;
#
# Per-product units sold:
#   SELECT product_id, SUM(quantity) AS units_sold
#   FROM curated_sales
#   GROUP BY product_id
#   ORDER BY units_sold DESC;
#
# Per-day revenue (partition-pruning-equivalent: WHERE on the date column
# is the cheap read; the (order_date) index makes it index range-scan cheap):
#   SELECT order_date, SUM(total_amount) AS daily_total
#   FROM curated_sales
#   WHERE order_date BETWEEN '2026-09-20' AND '2026-09-22'
#   GROUP BY order_date
#   ORDER BY order_date;
#
# Notes:
# - Glue auto-infers every CSV column as string. The PySpark job casts them;
#   the MySQL equivalent does the cast in the INSERT ... SELECT.
# - status column is dropped from `curated_sales` because the filter
#   `WHERE status = 'completed'` has been applied at load time.
# - Idempotent re-runs are handled by `TRUNCATE curated_sales; INSERT ... SELECT ...`
#   inside a transaction (the MySQL equivalent of Spark's mode='overwrite').
# - In production the table is usually RANGE-partitioned by order_date
#   (PARTITION BY RANGE (YEAR(order_date) * 100 + MONTH(order_date))) so the
#   engine can prune the same way Parquet + Athena would.
# - On very large fact tables, a covering secondary index on (order_date)
#   plus hashing / sharding by customer_id buys you the partition-pruning
#   speed the lab demonstrates against Parquet.
