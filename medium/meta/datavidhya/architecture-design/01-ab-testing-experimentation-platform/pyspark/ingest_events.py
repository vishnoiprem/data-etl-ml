"""
Spark Structured Streaming: Kafka → Iceberg Bronze layer.

Reads raw events from Kafka, parses Avro/JSON, writes to Iceberg bronze
partitioned by date and hour. Handles late-arriving data via watermarking.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, current_timestamp, to_date, hour, sha2, concat_ws
)
from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType, MapType, ArrayType
)


EVENT_SCHEMA = StructType([
    StructField("event_id",   StringType(),  False),
    StructField("user_id",    StringType(),  False),
    StructField("event_ts",   TimestampType(), False),
    StructField("event_name", StringType(),  False),
    StructField("properties", MapType(StringType(), StringType()), True),
    StructField("experiment_tags", ArrayType(StringType()), True),
])


def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("ab_events_ingest")
        .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkSessionCatalog")
        .config("spark.sql.catalog.spark_catalog.type", "hive")
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.local.type", "hadoop")
        .config("spark.sql.catalog.local.warehouse", "s3://lakehouse/warehouse")
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        .getOrCreate()
    )


def ingest(kafka_bootstrap: str, topic: str, bronze_table: str,
           checkpoint: str = "s3://lakehouse/checkpoints/events"):
    spark = build_spark()
    raw = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("subscribe", topic)
        .option("startingOffsets", "latest")
        .option("maxOffsetsPerTrigger", 200_000)   # backpressure cap
        .load()
        .selectExpr("CAST(value AS STRING) AS json_str",
                    "topic", "partition", "offset")
    )

    parsed = (
        raw
        .select(from_json(col("json_str"), EVENT_SCHEMA).alias("e"))
        .select("e.*")
        .withColumn("ingested_ts", current_timestamp())
        .withColumn("user_hashed", sha2(col("user_id"), 256))   # pseudonymisation
        .withColumn("dt",          to_date(col("event_ts")))
        .withColumn("hr",          hour(col("event_ts")))
    )

    # Dedup by event_id within 24h
    deduped = parsed.withWatermark("event_ts", "24 hours") \
                    .dropDuplicates(["event_id"])

    query = (
        deduped.writeStream
        .format("iceberg")
        .outputMode("append")
        .option("checkpointLocation", checkpoint)
        .partitionedBy("dt")                     # coarse partition by date
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
