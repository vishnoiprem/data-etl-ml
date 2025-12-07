# notebooks/01_ingestion_setup.py
"""
Document Ingestion Setup with Auto Loader
Handles exactly-once processing of incoming documents
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import hashlib


@dataclass
class DocumentMetadata:
    """Metadata for incoming documents"""
    document_id: str
    file_name: str
    file_size: int
    content_type: str
    ingestion_time: datetime
    source_path: str
    checksum: str
    partition_date: str


class DocumentIngestion:
    """Handles document ingestion using Databricks Auto Loader"""

    def __init__(self, storage_account: str, container: str):
        self.storage_account = storage_account
        self.container = container
        self.spark = SparkSession.builder.getOrCreate()

    def get_ingestion_path(self, environment: str = "prod") -> str:
        """Get Azure Data Lake Storage path for ingestion"""
        return f"abfss://{self.container}@{self.storage_account}.dfs.core.windows.net/{environment}/incoming/"

    def calculate_checksum(self, content: bytes) -> str:
        """Calculate SHA-256 checksum for deduplication"""
        return hashlib.sha256(content).hexdigest()

    def create_bronze_table(self, delta_path: str):
        """Create Bronze Delta table for raw document storage"""

        schema = StructType([
            StructField("document_id", StringType(), nullable=False),
            StructField("file_name", StringType(), nullable=False),
            StructField("file_path", StringType(), nullable=False),
            StructField("file_size", LongType(), nullable=False),
            StructField("content_type", StringType(), nullable=False),
            StructField("content", BinaryType(), nullable=False),
            StructField("checksum", StringType(), nullable=False),
            StructField("partition_date", DateType(), nullable=False),
            StructField("ingestion_time", TimestampType(), nullable=False),
            StructField("processed", BooleanType(), nullable=False),
            StructField("processing_attempts", IntegerType(), nullable=False)
        ])

        # Create Delta table if it doesn't exist
        self.spark.sql(f"""
            CREATE TABLE IF NOT EXISTS bronze.raw_documents
            USING DELTA
            LOCATION '{delta_path}/bronze/raw_documents'
            PARTITIONED BY (partition_date)
            TBLPROPERTIES (
                delta.autoOptimize.optimizeWrite = true,
                delta.autoOptimize.autoCompact = true
            )
        """)

        return schema

    def ingest_documents_stream(self, config: Dict) -> DataFrame:
        """Ingest documents using Auto Loader with binary format"""

        incoming_path = self.get_ingestion_path()

        raw_stream = (
            self.spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "binaryFile")
            .option("cloudFiles.schemaLocation",
                    f"{config['databricks']['checkpoint_location']}/schema")
            .option("cloudFiles.includeExistingFiles", "false")
            .option("cloudFiles.useNotifications", "true")
            .option("cloudFiles.validateOptions", "true")
            .option("pathGlobFilter", "*.{pdf,png,jpg,jpeg,tiff,bmp,docx}")
            .option("recursiveFileLookup", "true")
            .load(incoming_path)
        )

        # Add metadata and checksum
        processed_stream = raw_stream.select(
            sha2(col("path"), 256).alias("document_id"),
            input_file_name().alias("file_name"),
            col("path").alias("file_path"),
            col("length").alias("file_size"),
            self._infer_content_type_udf(col("path")).alias("content_type"),
            col("content"),
            sha2(col("content"), 256).alias("checksum"),
            current_date().alias("partition_date"),
            current_timestamp().alias("ingestion_time"),
            lit(False).alias("processed"),
            lit(0).alias("processing_attempts")
        )

        # Filter out unsupported formats
        supported_formats = config['processing']['supported_formats']
        processed_stream = processed_stream.filter(
            lower(split(col("file_name"), "\\.")[-1]).isin(supported_formats)
        )

        # Filter by size
        max_size = config['processing']['max_file_size_mb'] * 1024 * 1024
        processed_stream = processed_stream.filter(col("file_size") <= max_size)

        return processed_stream

    @udf(StringType())
    def _infer_content_type_udf(file_path: str) -> str:
        """Infer content type from file extension"""
        import os
        extension = os.path.splitext(file_path)[1].lower()

        content_types = {
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.bmp': 'image/bmp',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }

        return content_types.get(extension, 'application/octet-stream')

    def write_to_bronze(self, stream_df: DataFrame, delta_path: str):
        """Write ingested documents to Bronze Delta table"""

        query = (
            stream_df.writeStream
            .format("delta")
            .option("checkpointLocation",
                    f"{delta_path}/checkpoints/bronze_ingestion")
            .trigger(availableNow=True)
            .foreachBatch(self._deduplicate_batch)
            .outputMode("append")
            .start(f"{delta_path}/bronze/raw_documents")
        )

        query.awaitTermination()

    def _deduplicate_batch(self, batch_df: DataFrame, batch_id: int):
        """Deduplicate by checksum within batch"""

        # Check for existing documents with same checksum
        existing_checksums = self.spark.read.table("bronze.raw_documents") \
            .select("checksum").distinct()

        # Keep only new documents
        new_documents = batch_df.join(
            existing_checksums, "checksum", "left_anti"
        )

        if new_documents.count() > 0:
            new_documents.write \
                .format("delta") \
                .mode("append") \
                .saveAsTable("bronze.raw_documents")

            print(f"Batch {batch_id}: Added {new_documents.count()} new documents")