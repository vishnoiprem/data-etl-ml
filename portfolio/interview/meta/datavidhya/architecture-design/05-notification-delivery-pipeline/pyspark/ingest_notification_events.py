"""
Spark Streaming: Kafka → Iceberg Bronze for notification events.

Reads from:
  - notifications.sent
  - notifications.delivered
  - notifications.opened
  - notifications.clicked
  - notifications.converted
  - notifications.dismissed
  - notifications.unsubscribed

Writes everything to a single Iceberg Bronze table partitioned by day.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp, to_date
from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType,
    MapType, BooleanType, ArrayType
)


EVENT_SCHEMA = StructType([
    StructField("event_id",              StringType(),  False),
    StructField("notification_id",       StringType(),  True),
    StructField("notification_group_id", StringType(),  True),
    StructField("user_id",               StringType(),  False),
    StructField("event_type",            StringType(),  False),  # delivered|opened|clicked|...
    StructField("event_ts",              TimestampType(), False),
    StructField("metadata",              MapType(StringType(), StringType()), True),
])


def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("notification_ingest")
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.local.type", "hadoop")
        .config("spark.sql.catalog.local.warehouse", "s3://lakehouse/warehouse")
        .getOrCreate()
    )


def ingest(kafka_bootstrap: str, topic: str, bronze_table: str,
           checkpoint: str = "s3://lakehouse/checkpoints/notif"):
    spark = build_spark()
    raw = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("subscribe", topic)
        .option("startingOffsets", "latest")
        .option("maxOffsetsPerTrigger", 200_000)
        .load()
        .selectExpr("CAST(value AS STRING) AS json_str")
        .withColumn("e", from_json(col("json_str"), EVENT_SCHEMA))
        .select("e.*")
        .withColumn("ingested_ts", current_timestamp())
        .withColumn("dt", to_date(col("event_ts")))
    )

    deduped = raw.withWatermark("event_ts", "24 hours").dropDuplicates(["event_id"])

    (deduped.writeStream
            .format("iceberg")
            .outputMode("append")
            .option("checkpointLocation", checkpoint)
            .partitionedBy("dt")
            .toTable(bronze_table))


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--bootstrap", default="localhost:9092")
    p.add_argument("--topic",     default="notifications.events")
    p.add_argument("--table",     default="local.bronze.notification_events")
    args = p.parse_args()
    ingest(args.bootstrap, args.topic, args.table)
