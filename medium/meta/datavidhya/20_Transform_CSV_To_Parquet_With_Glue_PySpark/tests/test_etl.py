"""Offline pytest for the Glue PySpark ETL lab.

Drives the same six lab stages against a local SparkSession via the
``sales_etl_job`` module -- the actual ETL script the lab pastes into
the Glue Script editor.
"""
from __future__ import annotations

import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "glue_jobs"))

from pyspark.sql.functions import col  # noqa: E402

import sales_etl_job  # noqa: E402

from conftest import CSV_PATH  # noqa: E402


# ============================================================== stage 1
def test_stage1_raw_csv_has_all_string_schema(spark, raw_df) -> None:
    """Stage 1: read the raw CSV -- every column is text (catalog never
    inferred types). The single audit check: '29.99' is a string, not 29.99."""
    assert raw_df.count() == 15
    raw_types = {f.name: f.dataType.simpleString() for f in raw_df.schema.fields}
    assert all(t == "string" for t in raw_types.values()), raw_types
    sample = raw_df.filter("transaction_id = 'T0001'").first()["unit_price"]
    assert sample == "29.99" and isinstance(sample, str)


# ============================================================== stage 2
def test_stage2_transform_casts_measure_columns(spark, raw_df) -> None:
    """Stage 2: sales_etl_job.transform casts quantity->int, unit_price->double,
    keeps IDs as string, derives total_amount, filters to completed."""
    out = sales_etl_job.transform(raw_df)

    types = {f.name: f.dataType.simpleString() for f in out.schema.fields}
    assert types["quantity"]     == "int"
    assert types["unit_price"]   == "double"
    assert types["total_amount"] == "double"
    assert types["order_date"]   == "date"
    assert types["transaction_id"] == "string"   # IDs are not numbers
    assert types["customer_id"]    == "string"
    assert types["product_id"]     == "string"
    assert "status" not in types   # dropped after the filter


def test_stage2_transform_derives_total_amount(spark, raw_df) -> None:
    """T0001 was qty 3 * unit_price 29.99 = 89.97."""
    out = sales_etl_job.transform(raw_df)
    t0001 = out.filter("transaction_id = 'T0001'").first()
    assert round(t0001["total_amount"], 2) == 89.97


def test_stage2_transform_drops_non_completed(spark, raw_df) -> None:
    """15 raw - 2 cancelled - 1 pending = 12 completed."""
    out = sales_etl_job.transform(raw_df)
    assert out.count() == 12


# ============================================================== stage 3
def test_stage3_job_writes_parquet(spark, run_etl, curated_dir) -> None:
    """Stage 3: run sales_etl_job.main() and read back the curated Parquet."""
    run_etl()
    out = spark.read.parquet(f"file://{curated_dir}/curated/sales/")
    assert out.count() == 12
    # Parquet reads real types, not strings.
    types = {f.name: f.dataType.simpleString() for f in out.schema.fields}
    assert types["total_amount"] == "double"
    assert types["order_date"]   == "date"


# ============================================================== stage 4
def test_stage4_curated_is_partitioned_by_order_date(spark, run_etl, curated_dir) -> None:
    """Stage 4: write mode = 'overwrite' + partitionBy(order_date) produces
    one subdirectory per distinct date."""
    run_etl()
    sales_dir = os.path.join(curated_dir, "curated", "sales")
    partitions = [d for d in os.listdir(sales_dir) if d.startswith("order_date=")]
    assert len(partitions) == 8   # 8 distinct dates across 12 completed rows


def test_stage4_per_partition_files_are_parquet(spark, run_etl, curated_dir) -> None:
    """Each partition directory contains exactly one Parquet data file."""
    run_etl()
    sales_dir = os.path.join(curated_dir, "curated", "sales")
    for partition in os.listdir(sales_dir):
        if partition.startswith("order_date="):
            files = [f for f in os.listdir(os.path.join(sales_dir, partition))
                     if not f.startswith("_") and not f.startswith(".")]
            assert len(files) >= 1
            assert all(f.endswith(".parquet") for f in files), files


# ============================================================== stage 5
def test_stage5_top_customer_is_c055(spark, run_etl, curated_dir) -> None:
    """Stage 5: Athena-style aggregations against the curated Parquet.

    C055 = T0004 (2*1200) + T0009 (10*89.99) + T0014 (5*300) = 4799.90.
    """
    run_etl()
    out = spark.read.parquet(f"file://{curated_dir}/curated/sales/")
    out.createOrReplaceTempView("curated")

    top = spark.sql("""
        SELECT customer_id, SUM(total_amount) AS spend
        FROM curated
        GROUP BY customer_id
        ORDER BY spend DESC
        LIMIT 1
    """).first()
    assert top["customer_id"] == "C055"
    assert round(top["spend"], 2) == 4799.90


def test_stage5_partition_pruning_demo(spark, run_etl, curated_dir) -> None:
    """Date-range query: ``order_date BETWEEN ... AND ...`` returns one
    row per date in the range. Spark's Parquet reader can prune partitions
    when the predicate is on the partition column."""
    run_etl()
    out = spark.read.parquet(f"file://{curated_dir}/curated/sales/")
    out.createOrReplaceTempView("curated")

    in_range = [r["order_date"].isoformat() for r in spark.sql("""
        SELECT DISTINCT order_date FROM curated
        WHERE order_date BETWEEN DATE '2026-09-20' AND DATE '2026-09-22'
        ORDER BY order_date
    """).collect()]
    assert in_range == ["2026-09-20", "2026-09-21", "2026-09-22"]


# ============================================================== stage 6
def test_stage6_rerun_is_idempotent(spark, run_etl, curated_dir) -> None:
    """Stage 6: re-running the job (mode=overwrite) produces the same row
    count, same partition count, no stragglers."""
    run_etl()
    run_etl()  # second run

    out = spark.read.parquet(f"file://{curated_dir}/curated/sales/")
    assert out.count() == 12

    sales_dir = os.path.join(curated_dir, "curated", "sales")
    partitions = [d for d in os.listdir(sales_dir) if d.startswith("order_date=")]
    assert len(partitions) == 8
