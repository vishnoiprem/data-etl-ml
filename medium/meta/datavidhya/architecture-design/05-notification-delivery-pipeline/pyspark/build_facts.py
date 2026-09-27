"""
Spark Batch: Build notification_facts (one row per notification_group_id).

Joins:
  - notifications_sent (one row per send)
  - notification_events (delivered/opened/clicked/converted)

Produces deduped, attributed facts per group.
"""

import argparse
from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import (
    col, min as min_, first, collect_set, when, lit
)


def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("notification_build_facts")
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.local.type", "hadoop")
        .getOrCreate()
    )


def build(sent_table: str, events_table: str, out_table: str, run_date: str):
    spark = build_spark()

    sent = (spark.read.format("iceberg").load(sent_table)
                       .filter(col("sent_ts").cast("date") == run_date))

    # Pivot events by type — get earliest per group
    events = (spark.read.format("iceberg").load(events_table)
                        .filter(col("event_ts").cast("date") <= run_date))

    def earliest_by(event_type: str):
        return (events.filter(col("event_type") == event_type)
                     .groupBy("notification_group_id")
                     .agg(min_("event_ts").alias(f"{event_type}_ts")))

    delivered = earliest_by("delivered")
    opened    = earliest_by("opened")
    clicked   = earliest_by("clicked")
    converted = earliest_by("converted")

    facts = (sent.groupBy("notification_group_id", "user_id", "notification_type",
                          "campaign_id", "variant_id")
                .agg(
                    min_("sent_ts").alias("sent_ts"),
                    collect_set("channel").alias("channels_sent"),
                    first("user_pixel_opted_in").alias("user_pixel_opted_in"),
                )
                .join(delivered, "notification_group_id", "left")
                .join(opened,    "notification_group_id", "left")
                .join(clicked,   "notification_group_id", "left")
                .join(converted, "notification_group_id", "left")
                .withColumn("attribution_window_end",
                            (col("sent_ts").cast("long") + lit(30 * 60)).cast("timestamp"))
                .withColumn("attributed_open",
                            when(col("opened_ts").isNotNull(), lit(True)).otherwise(lit(False)))
                .withColumn("attributed_click",
                            when(col("clicked_ts").isNotNull(), lit(True)).otherwise(lit(False)))
                .withColumn("attributed_convert",
                            when(col("converted_ts").isNotNull(), lit(True)).otherwise(lit(False)))
                .withColumn("dt", col("sent_ts").cast("date"))
                )

    (facts.write
          .format("iceberg")
          .mode("overwrite")
          .partitionedBy("dt")
          .saveAsTable(out_table))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--sent",    default="local.bronze.notifications_sent")
    p.add_argument("--events",  default="local.bronze.notification_events")
    p.add_argument("--out",     default="local.gold.notification_facts")
    p.add_argument("--dt",      required=True)
    args = p.parse_args()
    build(args.sent, args.events, args.out, args.dt)
