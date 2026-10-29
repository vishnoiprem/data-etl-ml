"""
Compaction + Z-ORDER job for Iceberg tables.

Runs hourly via Airflow. Triggers when small-file ratio exceeds threshold.
"""

import argparse
from pyspark.sql import SparkSession


def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("iceberg_compaction")
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.local.type", "hadoop")
        .config("spark.sql.catalog.local.warehouse", "s3://lakehouse/warehouse")
        .getOrCreate()
    )


def compact_table(table: str, z_order_cols: list[str], target_file_size_mb: int = 256):
    spark = build_spark()

    # Inspect table for small-file ratio
    files_df = spark.sql(f"CALL local.system.files(table => '{table}')")
    small_files = files_df.filter("file_size_in_bytes < 32 * 1024 * 1024").count()
    total_files = files_df.count()
    small_file_ratio = small_files / max(total_files, 1)

    print(f"[{table}] small files: {small_files}/{total_files} ({small_file_ratio:.1%})")

    if small_file_ratio < 0.20:
        print(f"[{table}] no compaction needed")
        return

    z_order_expr = "zorder(" + ", ".join(z_order_cols) + ")"
    print(f"[{table}] rewriting with {z_order_expr}, target={target_file_size_mb}MB")

    spark.sql(f"""
        CALL local.system.rewrite_data_files(
            table => '{table}',
            strategy => 'sort',
            sort_order => '{z_order_expr}',
            options => map('target-file-size-bytes', '{target_file_size_mb * 1024 * 1024}')
        )
    """)
    print(f"[{table}] compaction done")


def expire_snapshots(table: str, older_than_days: int):
    spark = build_spark()
    spark.sql(f"""
        CALL local.system.expire_snapshots(
            table => '{table}',
            older_than => TIMESTAMP '{older_than_days} days ago'
        )
    """)
    print(f"[{table}] expired snapshots older than {older_than_days} days")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--table", required=True)
    p.add_argument("--z-order", nargs="+", default=["user_id"])
    p.add_argument("--target-file-mb", type=int, default=256)
    p.add_argument("--expire-snapshots-days", type=int, default=7)
    args = p.parse_args()

    compact_table(args.table, args.z_order, args.target_file_mb)
    expire_snapshots(args.table, args.expire_snapshots_days)
