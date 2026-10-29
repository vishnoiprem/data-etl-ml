"""Kafka to Delta Lake streaming pipeline for PostgreSQL CDC data.

This module reads CDC events from Kafka, parses them, and writes to Delta Lake
with proper schema evolution and fault tolerance.
"""

import logging
import signal
import sys
from dataclasses import dataclass
from typing import Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, from_json, get_json_object
from pyspark.sql.types import (
    StructType, StringType, LongType, DoubleType, TimestampType, StructField
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class KafkaConfig:
    """Kafka connection configuration."""
    bootstrap_servers: str = "localhost:9092"
    topic: str = "dbserver1.public.my_table"
    starting_offsets: str = "latest"
    max_offsets_per_trigger: Optional[int] = None


@dataclass(frozen=True)
class DeltaConfig:
    """Delta Lake configuration."""
    output_path: str = "/data/delta/retail"
    checkpoint_path: str = "/data/delta/checkpoints"
    partition_by: Optional[str] = None


@dataclass(frozen=True)
class CDCConfig:
    """CDC parsing configuration."""
    # Expected Debezium CDC envelope fields
    schema = StructType([
        StructField("op", StringType(), True),  # c=create, u=update, d=delete, r=read
        StructField("before", StringType(), True),  # JSON string of before state
        StructField("after", StringType(), True),   # JSON string of after state
        StructField("ts_ms", LongType(), True),     # Timestamp of change
        StructField("source", StringType(), True),  # Source metadata as JSON
    ])


class KafkaToDeltaPipeline:
    """Streaming pipeline from Kafka to Delta Lake."""

    def __init__(
        self,
        kafka_config: Optional[KafkaConfig] = None,
        delta_config: Optional[DeltaConfig] = None,
        cdc_config: Optional[CDCConfig] = None,
    ):
        self.kafka_config = kafka_config or KafkaConfig()
        self.delta_config = delta_config or DeltaConfig()
        self.cdc_config = cdc_config or CDCConfig()
        self._spark: Optional[SparkSession] = None
        self._running = False

    def _create_spark_session(self) -> SparkSession:
        """Create Spark session with Delta Lake and Kafka support."""
        return SparkSession.builder \
            .appName("KafkaToDelta") \
            .config("spark.jars.packages", ",".join([
                "io.delta:delta-core_2.12:2.4.0",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0",
            ])) \
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
            .config("spark.streaming.stopGracefullyOnShutdown", "true") \
            .config("spark.sql.streaming.schemaInference", "true") \
            .getOrCreate()

    def _shutdown(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully."""
        logger.info("Shutdown signal received, stopping pipeline...")
        self._running = False
        if self._spark:
            self._spark.streams.active[0].stop() if self._spark.streams.active else None
            self._spark.stop()

    def _read_kafka_stream(self) -> DataFrame:
        """Read streaming DataFrame from Kafka."""
        logger.info("Reading from Kafka topic: %s", self.kafka_config.topic)
        reader = self._spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.kafka_config.bootstrap_servers) \
            .option("subscribe", self.kafka_config.topic) \
            .option("startingOffsets", self.kafka_config.starting_offsets)

        if self.kafka_config.max_offsets_per_trigger:
            reader = reader.option("maxOffsetsPerTrigger", self.kafka_config.max_offsets_per_trigger)

        return reader.load()

    def _parse_cdc_events(self, kafka_df: DataFrame) -> DataFrame:
        """Parse Kafka CDC events into structured DataFrame."""
        # Convert binary value to string
        value_df = kafka_df.selectExpr("CAST(value AS STRING) as json_value")

        # Parse JSON with CDC schema
        parsed_df = value_df.select(
            from_json(col("json_value"), self.cdc_config.schema).alias("cdc")
        ).select("cdc.*")

        # Extract operation type and after-state
        # The 'after' field contains the actual row data as JSON string
        # We need to parse it based on the actual table schema
        return parsed_df

    def _extract_row_data(self, cdc_df: DataFrame, table_schema: StructType) -> DataFrame:
        """Extract row data from CDC 'after' field using table schema.

        Args:
            cdc_df: DataFrame with CDC envelope (op, before, after, ts_ms, source)
            table_schema: Schema of the actual table data in 'after' field

        Returns:
            DataFrame with flattened row data plus CDC metadata
        """
        return cdc_df.select(
            col("op"),
            col("ts_ms"),
            from_json(col("after"), table_schema).alias("data"),
            col("source"),
        ).select(
            "op",
            "ts_ms",
            "source",
            "data.*"
        )

    def _write_to_delta(self, df: DataFrame) -> None:
        """Write streaming DataFrame to Delta Lake."""
        writer = df.writeStream \
            .format("delta") \
            .outputMode("append") \
            .option("checkpointLocation", self.delta_config.checkpoint_path)

        if self.delta_config.partition_by:
            writer = writer.partitionBy(self.delta_config.partition_by)

        query = writer.start(self.delta_config.output_path)
        logger.info("Started Delta Lake streaming to: %s", self.delta_config.output_path)
        return query

    def run(self, table_schema: Optional[StructType] = None) -> None:
        """Run the streaming pipeline.

        Args:
            table_schema: Optional schema for the 'after' field data.
                         If not provided, writes raw CDC envelope.
        """
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

        self._spark = self._create_spark_session()
        self._spark.sparkContext.setLogLevel("WARN")
        self._running = True

        logger.info("Starting Kafka to Delta Lake pipeline")

        try:
            # Read from Kafka
            kafka_df = self._read_kafka_stream()

            # Parse CDC envelope
            cdc_df = self._parse_cdc_events(kafka_df)

            # Extract row data if table schema provided
            if table_schema:
                processed_df = self._extract_row_data(cdc_df, table_schema)
            else:
                # Write raw CDC envelope
                processed_df = cdc_df

            # Write to Delta Lake
            query = self._write_to_delta(processed_df)

            # Wait for termination
            query.awaitTermination()

        except Exception as e:
            logger.exception("Pipeline failed: %s", e)
            raise
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Clean up resources."""
        if self._spark:
            self._spark.stop()
            logger.info("Spark session stopped")


def create_sample_table_schema() -> StructType:
    """Create a sample table schema for demonstration."""
    return StructType([
        StructField("id", LongType(), False),
        StructField("user_id", StringType(), True),
        StructField("amount", DoubleType(), True),
        StructField("status", StringType(), True),
        StructField("created_at", TimestampType(), True),
    ])


def main() -> None:
    """Main entry point."""
    # Example configuration for production
    kafka_config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        topic="dbserver1.public.orders",
        starting_offsets="latest",
    )
    delta_config = DeltaConfig(
        output_path="/data/delta/orders",
        checkpoint_path="/data/delta/checkpoints/orders",
        partition_by="created_at",
    )

    pipeline = KafkaToDeltaPipeline(
        kafka_config=kafka_config,
        delta_config=delta_config,
    )

    # Run with table schema for structured output
    table_schema = create_sample_table_schema()
    pipeline.run(table_schema=table_schema)


if __name__ == "__main__":
    main()