"""Q20: Glue PySpark ETL -- raw_sales_transactions (CSV) -> curated (Parquet).

The actual script the lab pastes into the AWS Glue Script editor and runs
as a Glue job. Drop-in compatible: the same code runs against a local
SparkSession for the offline driver / pytest, and against the Glue
runtime in production.

Pipeline:
  1. Read the raw CSV from S3 (or local file:// for tests).
  2. Cast every numeric column from string to its real type
     (quantity: int, unit_price: double, transaction_id: long).
  3. Derive total_amount = quantity * unit_price.
  4. Filter status = 'completed' (drop cancelled + pending).
  5. Write the curated DataFrame as Parquet, partitioned by order_date
     so Athena can prune partitions on date-range queries.
"""
from __future__ import annotations

import argparse
import sys

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, to_date
from pyspark.sql.types import DoubleType, IntegerType, LongType


# Column types per the lab's "every column is text" raw table.
_CASTS = {
    "transaction_id": LongType(),
    "customer_id":    IntegerType(),
    "product_id":     IntegerType(),
    "quantity":       IntegerType(),
    "unit_price":     DoubleType(),
}


def parse_args() -> argparse.Namespace:
    """Glue passes --input_path / --output_path via the job's Arguments
    list. The same script can be run locally with the same flags.
    """
    p = argparse.ArgumentParser()
    p.add_argument("--input_path",  required=True, help="s3://.../raw_sales_transactions/ (or file://)")
    p.add_argument("--output_path", required=True, help="s3://.../curated/sales/             (or file://)")
    return p.parse_args()


def build_spark() -> SparkSession:
    """Local-mode SparkSession. Glue replaces this with its own.

    The Glue runtime injects Spark + GlueContext via the entrypoint; the
    script gets them via ``glueContext`` parameter. For offline we build
    a vanilla SparkSession. Same DataFrame API either way.
    """
    return (SparkSession.builder
            .appName("sales_etl_glue_q20")
            .config("spark.sql.shuffle.partitions", "1")
            .config("spark.ui.showConsoleProgress", "false")
            .getOrCreate())


def transform(df: DataFrame) -> DataFrame:
    """The four-step pipeline: cast -> derive -> filter -> partition."""
    # 1. Cast every text column to its real type.
    casted = df
    for col_name, spark_type in _CASTS.items():
        casted = casted.withColumn(col_name, col(col_name).cast(spark_type))

    # 2. Derive total_amount = quantity * unit_price.
    derived = casted.withColumn("total_amount",
                                 col("quantity") * col("unit_price"))

    # 3. Cast order_date from string to a real date type so Parquet writes
    #    it as DATE (32 bits) instead of STRING (variable length). Athena
    #    then filters on it natively.
    typed = derived.withColumn("order_date",
                                to_date(col("order_date"), "yyyy-MM-dd"))

    # 4. Keep only completed orders; drop cancelled + pending.
    completed = typed.filter(col("status") == "completed")

    # 5. Drop the status column (every row is now 'completed' -- redundant).
    return completed.drop("status")


def main() -> None:
    args = parse_args()
    spark = build_spark()

    # ------ read raw
    raw = (spark.read
                 .option("header", True)
                 .option("inferSchema", False)   # lab: all-string raw
                 .csv(args.input_path))

    # ------ transform
    curated = transform(raw)

    # ------ write curated Parquet, partitioned by order_date
    # Parquet is columnar; partitioning by date makes Athena partition-prune.
    # 'overwrite' mode matches the lab's "rerun-safe" expectation.
    (curated.write
            .mode("overwrite")
            .partitionBy("order_date")
            .parquet(args.output_path))

    spark.stop()


if __name__ == "__main__":
    main()
