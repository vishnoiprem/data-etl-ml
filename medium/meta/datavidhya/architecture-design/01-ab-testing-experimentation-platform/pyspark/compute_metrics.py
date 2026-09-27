"""
Spark Batch: Compute user_metric_daily for one date.

Reads Iceberg Silver events, joins with experiment_assignments, joins with
metric_definitions, and emits user × experiment × metric × date aggregates.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, to_date, when, explode, array, struct, avg, sum, count, countDistinct
)
from pyspark.sql.window import Window


def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("ab_compute_metrics")
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.local.type", "hadoop")
        .config("spark.sql.catalog.local.warehouse", "s3://lakehouse/warehouse")
        .getOrCreate()
    )


def compute_metrics_for_date(
    silver_events_table: str,
    assignments_table:   str,
    metric_defs_table:    str,
    out_table:            str,
    run_date:             str,        # 'YYYY-MM-DD'
):
    spark = build_spark()

    events = spark.read.format("iceberg").load(silver_events_table) \
                       .filter(col("dt") == run_date) \
                       .filter(col("is_bot") == False)             # noqa: E712

    assignments = spark.read.format("iceberg").load(assignments_table) \
                            .filter(col("start_ts") <= run_date) \
                            .filter((col("end_ts") >= run_date) | col("end_ts").isNull())

    metric_defs = spark.read.format("iceberg").load(metric_defs_table)

    # Each event is mapped to one (user, experiment, metric, value) tuple
    tagged = (
        events
        .filter(col("experiment_tags").isNotNull())
        .select(
            col("user_id"),
            col("event_name"),
            col("event_ts"),
            col("properties"),
            explode(col("experiment_tags")).alias("experiment_id"),
        )
        .join(assignments,
              on=["user_id", "experiment_id"], how="inner")
        .join(metric_defs,
              on=metric_defs["numerator_event"] == col("event_name"),
              how="inner")
    )

    # Compute metric value per row based on metric_type
    val = (
        when(col("metric_type") == "COUNT",      lit(1))
        .when(col("metric_type") == "PROPORTION", col(f"properties.`{col('event_field')}`").cast("double"))
        .when(col("metric_type") == "MEAN",       col(f"properties.`{col('event_field')}`").cast("double"))
        .when(col("metric_type") == "RATIO",
              col(f"properties.`{col('num_field')}`").cast("double") /
              col(f"properties.`{col('denom_field')}`").cast("double"))
        .alias("value")
    )

    per_user = (
        tagged
        .withColumn("value", val)
        .groupBy("user_id", "experiment_id", "variant_id", "metric_id")
        .agg(avg("value").alias("value"))
        .withColumn("dt", lit(run_date))
    )

    (
        per_user
        .write
        .format("iceberg")
        .mode("append")
        .partitionedBy("dt")
        .saveAsTable(out_table)
    )


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--silver", default="local.silver.events")
    p.add_argument("--assignments", default="local.gold.assignments")
    p.add_argument("--metric_defs",  default="local.gold.metric_definitions")
    p.add_argument("--out",          default="local.gold.user_metric_daily")
    p.add_argument("--date",         required=True)
    args = p.parse_args()
    compute_metrics_for_date(args.silver, args.assignments, args.metric_defs,
                             args.out, args.date)
