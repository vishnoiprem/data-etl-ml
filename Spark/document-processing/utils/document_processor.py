"""
Document Processor: Core functionality for Azure Document Intelligence integration
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

from .model_selector import ModelSelector, ModelType
from .validators import DocumentValidator

logger = logging.getLogger(__name__)


@dataclass
class ProcessingConfig:
    """Configuration for document processing"""
    endpoint: str
    api_key: str
    max_retries: int = 3
    rate_limit_tps: int = 15
    timeout_seconds: int = 30
    parallelism: int = 10
    min_confidence: float = 0.7


class DocumentProcessor:
    """Main processor for Azure Document Intelligence integration"""

    def __init__(self, config: ProcessingConfig, spark_session: SparkSession):
        self.config = config
        self.spark = spark_session
        self.validator = DocumentValidator()
        self._setup_udfs()

    def _setup_udfs(self):
        """Register UDFs for distributed processing"""

        # Broadcast credentials for worker access
        self.endpoint_bc = self.spark.sparkContext.broadcast(self.config.endpoint)
        self.key_bc = self.spark.sparkContext.broadcast(self.config.api_key)
        self.config_bc = self.spark.sparkContext.broadcast(self.config)

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
                        StructField("angle", FloatType()),
                        StructField("confidence", FloatType())
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
                StructField("processing_time_ms", LongType()),
                StructField("language", StringType())
            ])
        )

    def _process_document_udf(self,
                              content: bytes,
                              file_path: str,
                              file_name: str,
                              model_preference: str = "auto") -> Dict[str, Any]:
        """UDF wrapper for document processing"""
        import time
        start_time = time.time()

        try:
            # Validate input
            if not content or len(content) == 0:
                return self._create_error_result("Empty document content", start_time)

            if len(content) > 50 * 1024 * 1024:  # 50MB limit
                return self._create_error_result("Document exceeds size limit (50MB)", start_time)

            # Initialize client
            client = DocumentIntelligenceClient(
                endpoint=self.endpoint_bc.value,
                credential=AzureKeyCredential(self.key_bc.value)
            )

            # Select appropriate model
            model_id = ModelSelector.select_model(file_path, model_preference)

            # Process document with retry logic
            result = self._process_with_retry(
                client, content, model_id, max_retries=self.config_bc.value.max_retries
            )

            # Extract and structure results
            extracted_data = self._extract_structure(result)

            # Validate extracted data
            validation_result = self.validator.validate_extraction(extracted_data)
            if not validation_result["is_valid"]:
                return self._create_error_result(
                    f"Validation failed: {validation_result['errors']}",
                    start_time
                )

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
                "processing_time_ms": processing_time,
                "language": extracted_data.get("language", "en")
            }

        except Exception as e:
            logger.error(f"Error processing document {file_name}: {str(e)}")
            return self._create_error_result(str(e), start_time, model_preference)

    def _process_with_retry(self,
                            client: DocumentIntelligenceClient,
                            content: bytes,
                            model_id: str,
                            max_retries: int = 3) -> AnalyzeResult:
        """Process document with exponential backoff retry"""

        for attempt in range(max_retries):
            try:
                # Configure analysis options based on model
                features = ["keyValuePairs", "ocr.highResolution"]
                if model_id == ModelType.LAYOUT.value:
                    features.append("tables")

                poller = client.begin_analyze_document(
                    model_id=model_id,
                    analyze_request=content,
                    content_type="application/octet-stream",
                    features=features,
                    output_content_format="text"
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
                    logger.error(f"HTTP error {e.status_code}: {e}")
                    raise

            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed after {max_retries} retries: {e}")
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
        all_confidences = []

        for i, page in enumerate(result.pages or []):
            page_text = "\n".join([line.content for line in (page.lines or [])])
            word_count = len(page_text.split())
            total_words += word_count

            # Calculate page confidence
            page_confidences = []
            for line in page.lines or []:
                if line.confidence:
                    page_confidences.append(line.confidence)
                for word in line.words or []:
                    if word.confidence:
                        page_confidences.append(word.confidence)

            page_confidence = sum(page_confidences) / len(page_confidences) if page_confidences else 0.0
            all_confidences.extend(page_confidences)

            pages.append({
                "page_number": i + 1,
                "text": page_text,
                "word_count": word_count,
                "width": page.width if page.width else 0.0,
                "height": page.height if page.height else 0.0,
                "angle": page.angle if page.angle else 0.0,
                "confidence": page_confidence
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
                key_confidence = kv.key.confidence if kv.key.confidence else 0.0
                value_confidence = kv.value.confidence if kv.value.confidence else 0.0
                key_value_pairs.append({
                    "key": kv.key.content,
                    "value": kv.value.content,
                    "confidence": min(key_confidence, value_confidence)
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

        # Detect language (simple heuristic)
        language = self._detect_language(result.content if result.content else "")

        # Calculate overall confidence
        confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

        return {
            "content": result.content if result.content else "",
            "page_count": len(pages),
            "total_word_count": total_words,
            "confidence_score": confidence,
            "pages": pages,
            "tables": tables,
            "key_value_pairs": key_value_pairs,
            "entities": entities,
            "language": language
        }

    def _detect_language(self, text: str) -> str:
        """Simple language detection (in production, use Azure Text Analytics)"""
        if not text:
            return "unknown"

        # Common English words
        english_words = {'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i'}
        # Common non-English characters
        non_latin_chars = set('áéíóúàèìòùäëïöüñçß')

        words = set(text.lower().split()[:100])  # Check first 100 words
        english_count = len(words.intersection(english_words))

        if english_count > 5:
            return "en"
        elif any(char in text for char in non_latin_chars):
            # Could be Spanish, German, French, etc.
            return "multilingual"
        else:
            return "en"  # Default to English

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
            "entities": [],
            "language": "unknown"
        }

    def _create_error_result(self,
                             error_message: str,
                             start_time: float,
                             model_used: str = "unknown") -> Dict[str, Any]:
        """Create error result structure"""
        processing_time = int((time.time() - start_time) * 1000)

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
            "error_message": error_message,
            "model_used": model_used,
            "processing_time_ms": processing_time,
            "language": None
        }

    def process_documents_batch(self,
                                input_df: DataFrame,
                                parallelism: int = None) -> DataFrame:
        """Process documents in parallel batches"""

        if parallelism is None:
            parallelism = self.config.parallelism

        # Repartition to control API call parallelism
        repartitioned_df = input_df.repartition(parallelism)

        # Apply processing UDF
        processed_df = repartitioned_df.withColumn(
            "extraction_result",
            expr("process_document_udf(content, file_path, file_name, 'auto')")
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
            col("extraction_result.language").alias("language"),
            current_timestamp().alias("processing_time"),
            lit("processed").alias("processing_stage")
        )

        return result_df

    def filter_low_confidence(self,
                              processed_df: DataFrame,
                              min_confidence: float = None) -> Tuple[DataFrame, DataFrame]:
        """Filter out low confidence results"""

        if min_confidence is None:
            min_confidence = self.config.min_confidence

        high_confidence_df = processed_df.filter(
            (col("processing_status") == "success") &
            (col("confidence_score") >= min_confidence)
        )

        low_confidence_df = processed_df.filter(
            (col("processing_status") == "success") &
            (col("confidence_score") < min_confidence)
        )

        return high_confidence_df, low_confidence_df

    def calculate_processing_metrics(self, processed_df: DataFrame) -> Dict[str, Any]:
        """Calculate processing metrics"""

        metrics = processed_df.select(
            count("*").alias("total_documents"),
            sum(when(col("processing_status") == "success", 1).otherwise(0)).alias("success_count"),
            sum(when(col("processing_status") == "error", 1).otherwise(0)).alias("error_count"),
            avg(col("processing_time_ms")).alias("avg_processing_time"),
            avg(col("confidence_score")).alias("avg_confidence"),
            avg(col("page_count")).alias("avg_page_count"),
            avg(col("total_word_count")).alias("avg_word_count")
        ).first()

        total = metrics["total_documents"] or 0
        success = metrics["success_count"] or 0

        return {
            "total_documents": total,
            "success_count": success,
            "error_count": metrics["error_count"] or 0,
            "success_rate": success / total if total > 0 else 0,
            "avg_processing_time_ms": metrics["avg_processing_time"] or 0,
            "avg_confidence": metrics["avg_confidence"] or 0,
            "avg_page_count": metrics["avg_page_count"] or 0,
            "avg_word_count": metrics["avg_word_count"] or 0
        }