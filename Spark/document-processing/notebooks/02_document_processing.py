# notebooks/02_document_processing.py
"""
Core Document Processing with Azure Document Intelligence
Handles OCR, text extraction, and structured data parsing
"""

import time
import logging
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import pandas as pd

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Main processor for Azure Document Intelligence integration"""

    def __init__(self, endpoint: str, api_key: str, spark_session: SparkSession):
        self.endpoint = endpoint
        self.api_key = api_key
        self.spark = spark_session
        self._setup_udfs()

    def _setup_udfs(self):
        """Register UDFs for distributed processing"""

        # Broadcast credentials for worker access
        self.endpoint_bc = self.spark.sparkContext.broadcast(self.endpoint)
        self.key_bc = self.spark.sparkContext.broadcast(self.api_key)

        # Register processing UDF
        self.spark.udf.register(
            "process_document_udf",
            self._process_document_udf,
            StructType([
                StructField("status", StringType()),
                StructField("content", StringType()),
                StructField("page_count", IntegerType()),
                StructField("total_word_count", IntegerType()),
                StructField("confidence_score", FloatType()),
                StructField("pages", ArrayType(
                    StructType([
                        StructField("page_number", IntegerType()),
                        StructField("text", StringType()),
                        StructField("word_count", IntegerType()),
                        StructField("width", FloatType()),
                        StructField("height", FloatType()),
                        StructField("angle", FloatType())
                    ])
                )),
                StructField("tables", ArrayType(
                    StructType([
                        StructField("table_number", IntegerType()),
                        StructField("row_count", IntegerType()),
                        StructField("column_count", IntegerType()),
                        StructField("cells", ArrayType(
                            StructType([
                                StructField("row_index", IntegerType()),
                                StructField("column_index", IntegerType()),
                                StructField("content", StringType()),
                                StructField("confidence", FloatType())
                            ])
                        ))
                    ])
                )),
                StructField("key_value_pairs", ArrayType(
                    StructType([
                        StructField("key", StringType()),
                        StructField("value", StringType()),
                        StructField("confidence", FloatType())
                    ])
                )),
                StructField("entities", ArrayType(
                    StructType([
                        StructField("category", StringType()),
                        StructField("subcategory", StringType()),
                        StructField("content", StringType()),
                        StructField("confidence", FloatType())
                    ])
                )),
                StructField("error_message", StringType()),
                StructField("model_used", StringType()),
                StructField("processing_time_ms", LongType())
            ])
        )

    def _process_document_udf(self,
                              content: bytes,
                              file_path: str,
                              model_preference: str = "auto") -> Dict[str, Any]:
        """UDF wrapper for document processing"""
        import time
        start_time = time.time()

        try:
            # Initialize client with broadcasted credentials
            client = DocumentIntelligenceClient(
                endpoint=self.endpoint_bc.value,
                credential=AzureKeyCredential(self.key_bc.value)
            )

            # Auto-select model based on content
            model_id = self._select_model(file_path, model_preference)

            # Process document with retry logic
            result = self._process_with_retry(
                client, content, model_id, max_retries=3
            )

            # Extract and structure results
            extracted_data = self._extract_structure(result)

            processing_time = int((time.time() - start_time) * 1000)

            return {
                "status": "success",
                "content": extracted_data["content"],
                "page_count": extracted_data["page_count"],
                "total_word_count": extracted_data["total_word_count"],
                "confidence_score": extracted_data["confidence_score"],
                "pages": extracted_data["pages"],
                "tables": extracted_data["tables"],
                "key_value_pairs": extracted_data["key_value_pairs"],
                "entities": extracted_data["entities"],
                "error_message": None,
                "model_used": model_id,
                "processing_time_ms": processing_time
            }

        except Exception as e:
            return {
                "status": "error",
                "content": None,
                "page_count": 0,
                "total_word_count": 0,
                "confidence_score": 0.0,
                "pages": [],
                "tables": [],
                "key_value_pairs": [],
                "entities": [],
                "error_message": str(e),
                "model_used": model_preference,
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }

    def _select_model(self, file_path: str, preference: str) -> str:
        """Select appropriate Document Intelligence model"""
        from utils.model_selector import ModelSelector
        return ModelSelector.select_model(file_path, preference)

    def _process_with_retry(self, client: DocumentIntelligenceClient,
                            content: bytes, model_id: str,
                            max_retries: int = 3) -> AnalyzeResult:
        """Process document with exponential backoff retry"""

        for attempt in range(max_retries):
            try:
                poller = client.begin_analyze_document(
                    model_id=model_id,
                    analyze_request=content,
                    content_type="application/octet-stream",
                    features=["keyValuePairs", "ocr.highResolution"]
                )

                result = poller.result()
                return result

            except HttpResponseError as e:
                if e.status_code == 429:  # Rate limit
                    wait_time = 2 ** attempt  # Exponential backoff
                    if 'Retry-After' in e.response.headers:
                        wait_time = int(e.response.headers['Retry-After'])

                    logger.warning(f"Rate limited, waiting {wait_time}s (attempt {attempt + 1})")
                    time.sleep(wait_time)

                elif e.status_code >= 500:  # Server error
                    logger.warning(f"Server error: {e}, retrying...")
                    time.sleep(2 ** attempt)

                else:
                    raise

            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Error: {e}, retrying...")
                time.sleep(2 ** attempt)

        raise Exception(f"Failed after {max_retries} retries")

    def _extract_structure(self, result: AnalyzeResult) -> Dict[str, Any]:
        """Extract structured data from analysis result"""

        if not result.pages:
            return self._create_empty_result()

        # Extract pages
        pages = []
        total_words = 0

        for i, page in enumerate(result.pages or []):
            page_text = "\n".join([line.content for line in (page.lines or [])])
            word_count = len(page_text.split())
            total_words += word_count

            pages.append({
                "page_number": i + 1,
                "text": page_text,
                "word_count": word_count,
                "width": page.width if page.width else 0.0,
                "height": page.height if page.height else 0.0,
                "angle": page.angle if page.angle else 0.0
            })

        # Extract tables
        tables = []
        for i, table in enumerate(result.tables or []):
            cells = []
            for cell in table.cells or []:
                cells.append({
                    "row_index": cell.row_index,
                    "column_index": cell.column_index,
                    "content": cell.content,
                    "confidence": cell.confidence
                })

            tables.append({
                "table_number": i + 1,
                "row_count": table.row_count,
                "column_count": table.column_count,
                "cells": cells
            })

        # Extract key-value pairs
        key_value_pairs = []
        for kv in result.key_value_pairs or []:
            if kv.key and kv.value:
                key_value_pairs.append({
                    "key": kv.key.content,
                    "value": kv.value.content,
                    "confidence": min(kv.key.confidence or 0.0, kv.value.confidence or 0.0)
                })

        # Extract entities
        entities = []
        if hasattr(result, 'entities'):
            for entity in result.entities or []:
                entities.append({
                    "category": entity.category,
                    "subcategory": entity.subcategory,
                    "content": entity.content,
                    "confidence": entity.confidence
                })

        # Calculate confidence score
        confidence = self._calculate_confidence(result)

        return {
            "content": result.content,
            "page_count": len(pages),
            "total_word_count": total_words,
            "confidence_score": confidence,
            "pages": pages,
            "tables": tables,
            "key_value_pairs": key_value_pairs,
            "entities": entities
        }

    def _calculate_confidence(self, result: AnalyzeResult) -> float:
        """Calculate average confidence score"""
        confidences = []

        # Page confidence
        for page in result.pages or []:
            if page.confidence:
                confidences.append(page.confidence)

        # Line confidence
        for page in result.pages or []:
            for line in page.lines or []:
                if line.confidence:
                    confidences.append(line.confidence)

        # Word confidence
        for page in result.pages or []:
            for word in page.words or []:
                if word.confidence:
                    confidences.append(word.confidence)

        return sum(confidences) / len(confidences) if confidences else 0.0

    def _create_empty_result(self) -> Dict[str, Any]:
        """Create empty result structure"""
        return {
            "content": "",
            "page_count": 0,
            "total_word_count": 0,
            "confidence_score": 0.0,
            "pages": [],
            "tables": [],
            "key_value_pairs": [],
            "entities": []
        }

    def process_documents_batch(self,
                                input_df: DataFrame,
                                parallelism: int = 10) -> DataFrame:
        """Process documents in parallel batches"""

        # Repartition to control API call parallelism
        repartitioned_df = input_df.repartition(parallelism)

        # Apply processing UDF
        processed_df = repartitioned_df.withColumn(
            "extraction_result",
            expr("process_document_udf(content, file_path, 'auto')")
        )

        # Extract result fields
        result_df = processed_df.select(
            "document_id",
            "file_name",
            "file_path",
            "file_size",
            "content_type",
            "checksum",
            "partition_date",
            "ingestion_time",
            col("extraction_result.status").alias("processing_status"),
            col("extraction_result.content").alias("extracted_content"),
            col("extraction_result.page_count").alias("page_count"),
            col("extraction_result.total_word_count").alias("total_word_count"),
            col("extraction_result.confidence_score").alias("confidence_score"),
            col("extraction_result.pages").alias("pages"),
            col("extraction_result.tables").alias("tables"),
            col("extraction_result.key_value_pairs").alias("key_value_pairs"),
            col("extraction_result.entities").alias("entities"),
            col("extraction_result.error_message").alias("error_message"),
            col("extraction_result.model_used").alias("model_used"),
            col("extraction_result.processing_time_ms").alias("processing_time_ms"),
            current_timestamp().alias("processing_time"),
            lit("processed").alias("processing_stage")
        )

        return result_df

    def write_to_silver(self,
                        processed_df: DataFrame,
                        delta_path: str,
                        trigger_interval: str = "5 minutes"):
        """Write processed documents to Silver Delta table"""

        # Create Silver table if it doesn't exist
        self.spark.sql(f"""
            CREATE TABLE IF NOT EXISTS silver.processed_documents (
                document_id STRING NOT NULL,
                file_name STRING NOT NULL,
                file_path STRING NOT NULL,
                file_size LONG NOT NULL,
                content_type STRING,
                checksum STRING NOT NULL,
                partition_date DATE NOT NULL,
                ingestion_time TIMESTAMP NOT NULL,
                processing_status STRING NOT NULL,
                extracted_content STRING,
                page_count INT,
                total_word_count INT,
                confidence_score FLOAT,
                pages ARRAY<STRUCT<
                    page_number: INT,
                    text: STRING,
                    word_count: INT,
                    width: FLOAT,
                    height: FLOAT,
                    angle: FLOAT
                >>,
                tables ARRAY<STRUCT<
                    table_number: INT,
                    row_count: INT,
                    column_count: INT,
                    cells: ARRAY<STRUCT<
                        row_index: INT,
                        column_index: INT,
                        content: STRING,
                        confidence: FLOAT
                    >>
                >>,
                key_value_pairs ARRAY<STRUCT<
                    key: STRING,
                    value: STRING,
                    confidence: FLOAT
                >>,
                entities ARRAY<STRUCT<
                    category: STRING,
                    subcategory: STRING,
                    content: STRING,
                    confidence: FLOAT
                >>,
                error_message STRING,
                model_used STRING,
                processing_time_ms LONG,
                processing_time TIMESTAMP NOT NULL,
                processing_stage STRING,
                silver_load_time TIMESTAMP
            )
            USING DELTA
            LOCATION '{delta_path}/silver/processed_documents'
            PARTITIONED BY (partition_date)
            TBLPROPERTIES (
                delta.enableChangeDataFeed = true,
                delta.autoOptimize.optimizeWrite = true
            )
        """)

        # Write stream to Silver
        query = (
            processed_df.withColumn("silver_load_time", current_timestamp())
            .writeStream
            .format("delta")
            .option("checkpointLocation",
                    f"{delta_path}/checkpoints/silver_processing")
            .trigger(processingTime=trigger_interval)
            .outputMode("append")
            .start(f"{delta_path}/silver/processed_documents")
        )

        return query