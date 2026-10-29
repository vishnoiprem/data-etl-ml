"""
Spark Batch: Bulk Iceberg row-level deletes for many users.

Two modes:
  - small (< 10k ids): Python IN-list, fast for one-off GDPR deletes
  - large (>= 10k ids): staged Parquet file, then Iceberg MERGE/DELETE FROM
    using a side table — avoids driver-side collect OOM at scale

References:
  - https://iceberg.apache.org/docs/latest/spark-ddl/#delete-from
"""

import argparse
from pathlib import Path
from typing import List, Union

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


def bulk_delete(spark: SparkSession, table: str,
                user_ids: Union[List[str], str]) -> int:
    """
    user_ids can be a Python list (small) or a path to a parquet file with a
    user_id column (large).
    """
    if isinstance(user_ids, str):
        # Path to parquet file containing user_id column
        users_view = f"users_to_delete_{abs(hash(user_ids))}"
        (spark.read.parquet(user_ids)
                   .createOrReplaceTempView(users_view))
    else:
        if not user_ids:
            return 0
        users_view = f"users_to_delete_{abs(hash(tuple(user_ids)))}"
        spark.createDataFrame([(u,) for u in user_ids], "user_id STRING") \
             .createOrReplaceTempView(users_view)

    # Use Iceberg's native DELETE FROM for file-level rewrite (NOT full overwrite).
    # Iceberg rewrites only files containing matched rows.
    result = spark.sql(f"""
        DELETE FROM {table}
        WHERE user_id IN (SELECT user_id FROM {users_view})
    """)
    return result.collect()[0][0] if result else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--table", required=True)
    p.add_argument("--user-ids", nargs="*", help="inline user IDs")
    p.add_argument("--user-ids-file", help="parquet file with user_id column")
    args = p.parse_args()

    if not args.user_ids and not args.user_ids_file:
        raise SystemExit("provide --user-ids or --user-ids-file")

    user_ids = args.user_ids_file if args.user_ids_file else args.user_ids
    spark = build_spark()
    deleted = bulk_delete(spark, args.table, user_ids)
    print(f"Deleted {deleted} rows from {args.table}")
