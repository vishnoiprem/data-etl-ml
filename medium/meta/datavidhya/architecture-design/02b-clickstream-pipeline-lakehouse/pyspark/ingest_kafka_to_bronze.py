"""
Spark Structured Streaming: Kafka → Iceberg Bronze.

- Reads raw events from Kafka (Avro / JSON)
- Parses with explicit schema
- Adds ingest_ts and ingest_status
- Writes to Iceberg Bronze partitioned by date
- 24h watermark for late events
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp, to_date, hour, lit
from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType, MapType, ArrayType
)


EVENT_SCHEMA = StructType([
    StructField("event_id",     StringType(),  False),
    StructField("user_id",      StringType(),  False),
    StructField("event_ts",     TimestampType(), False),
    StructField("event_name",   StringType(),  False),
    StructField("session_id",   StringType(),  True),
    StructField("platform",     StringType(),  True),
    StructField("app_version",  StringType(),  True),
    StructField("country",      StringType(),  True),
    StructField("device_class", StringType(),  True),
    StructField("user_agent",   StringType(),  True),
    StructField("ip_hash",      StringType(),  True),
    StructField("properties",   MapType(StringType(), StringType()), True),
    StructField("context",      MapType(StringType(), StringType()), True),
    StructField("received_ts",  TimestampType(), True),
])


def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("clickstream_ingest")
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.local.type", "hadoop")
        .config("spark.sql.catalog.local.warehouse", "s3://lakehouse/warehouse")
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        .getOrCreate()
    )


def ingest(
    kafka_bootstrap: str,
    topic: str,
    bronze_table: str,
    checkpoint: str = "s3://lakehouse/checkpoints/bronze",
    trigger_seconds: int = 30,
    max_offsets_per_trigger: int = 200_000,
):
    spark = build_spark()

    raw = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("subscribe", topic)
        .option("startingOffsets", "latest")
        .option("maxOffsetsPerTrigger", max_offsets_per_trigger)
        .option("kafka.isolation.level", "read_committed")
        .load()
        .selectExpr("CAST(value AS STRING) AS json_str",
                    "CAST(timestamp AS TIMESTAMP) AS kafka_ts")
    )

    parsed = (
        raw
        .withColumn("e", from_json(col("json_str"), EVENT_SCHEMA))
        .select("e.*", "kafka_ts")
        .withColumn("ingested_ts", current_timestamp())
        .withColumn("ingest_status", lit("OK"))          # upgraded by bot filter job
        .withColumn("bot_score",    lit(0.0))
        .withColumn("dt",           to_date(col("event_ts")))
        .withColumn("hr",           hour(col("event_ts")))
    )

    # Drop dups by event_id within 24h watermark window
    deduped = parsed.withWatermark("event_ts", "24 hours").dropDuplicates(["event_id"])

    query = (
        deduped.writeStream
        .format("iceberg")
        .outputMode("append")
        .option("checkpointLocation", checkpoint)
        .trigger(processingTime=f"{trigger_seconds} seconds")
        .toTable(bronze_table)
    )
    query.awaitTermination()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--bootstrap", default="localhost:9092")
    p.add_argument("--topic",     default="events.raw")
    p.add_argument("--table",     default="local.bronze.events")
    args = p.parse_args()
    ingest(args.bootstrap, args.topic, args.table)
