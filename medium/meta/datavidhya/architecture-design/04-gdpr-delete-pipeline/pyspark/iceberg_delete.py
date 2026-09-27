"""
Spark Batch: Bulk Iceberg row-level deletes for many users.

Used for:
  - Bulk backfill (e.g. company acquires competitor and merges data)
  - Periodic privacy sweeps
  - Per-user GDPR deletion when SQL is preferred over the Python coordinator
"""

import argparse
from pyspark.sql import SparkSession


def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("iceberg_bulk_delete")
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.local.type", "hadoop")
        .config("spark.sql.catalog.local.warehouse", "s3://lakehouse/warehouse")
        .getOrCreate()
    )


def bulk_delete(spark: SparkSession, table: str, user_ids: list[str]):
    if not user_ids:
        return 0
    # Build IN-clause safely (parameterized for small batches)
    # For very large lists: temp view + semi-join
    df_users = spark.createDataFrame([(u,) for u in user_ids], "user_id STRING")
    df_users.createOrReplaceTempView("users_to_delete")

    df = spark.read.format("iceberg").load(table)
    before = df.count()
    after = df.join(df_users, on="user_id", how="left_anti").count()

    # Write back
    (df.join(df_users, on="user_id", how="left_anti")
       .write
       .format("iceberg")
       .mode("overwrite")
       .option("write.distribution-mode", "hash")
       .saveAsTable(table))

    return before - after


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--table", required=True)
    p.add_argument("--user-ids", nargs="+", required=True)
    args = p.parse_args()
    spark = build_spark()
    deleted = bulk_delete(spark, args.table, args.user_ids)
    print(f"Deleted {deleted} rows from {args.table}")
