# tests/test_document_processor.py
"""
Unit tests for document processing components
"""

import unittest
import pytest
from unittest.mock import Mock, patch, MagicMock
from pyspark.sql import SparkSession
from pyspark.sql.types import *
import pandas as pd

from utils.document_processor import DocumentProcessor
from utils.model_selector import ModelSelector
from utils.error_handler import ErrorHandler


class TestDocumentProcessor(unittest.TestCase):
    """Test document processing functionality"""

    @classmethod
    def setUpClass(cls):
        cls.spark = SparkSession.builder \
            .master("local[1]") \
            .appName("TestDocumentProcessor") \
            .getOrCreate()

    def test_model_selection(self):
        """Test intelligent model selection"""

        # Test invoice detection
        self.assertEqual(
            ModelSelector.select_model("invoice_123.pdf", "auto"),
            "prebuilt-invoice"
        )

        # Test receipt detection
        self.assertEqual(
            ModelSelector.select_model("receipt_456.jpg", "auto"),
            "prebuilt-receipt"
        )

        # Test ID document detection
        self.assertEqual(
            ModelSelector.select_model("passport_789.pdf", "auto"),
            "prebuilt-idDocument"
        )

        # Test manual model selection
        self.assertEqual(
            ModelSelector.select_model("document.pdf", "prebuilt-read"),
            "prebuilt-read"
        )

    def test_error_categorization(self):
        """Test error categorization logic"""

        handler = ErrorHandler(self.spark, "test_path")

        # Test rate limit errors
        self.assertEqual(
            handler.dlq.categorize_error("Rate limit exceeded"),
            ErrorCategory.RATE_LIMIT
        )

        # Test timeout errors
        self.assertEqual(
            handler.dlq.categorize_error("Request timed out"),
            ErrorCategory.TIMEOUT
        )

        # Test format errors
        self.assertEqual(
            handler.dlq.categorize_error("Invalid file format"),
            ErrorCategory.INVALID_FORMAT
        )

    @patch('azure.ai.documentintelligence.DocumentIntelligenceClient')
    def test_document_processing(self, mock_client):
        """Test document processing with mock API"""

        # Mock API response
        mock_result = MagicMock()
        mock_result.content = "Test content"
        mock_result.pages = []
        mock_result.tables = []
        mock_result.key_value_pairs = []
        mock_result.entities = []

        mock_poller = MagicMock()
        mock_poller.result.return_value = mock_result
        mock_client.return_value.begin_analyze_document.return_value = mock_poller

        # Create processor
        processor = DocumentProcessor(
            endpoint="https://test.endpoint",
            api_key="test-key",
            spark_session=self.spark
        )

        # Test processing
        result = processor._process_document_udf(
            b"test content",
            "test.pdf",
            "prebuilt-read"
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["content"], "Test content")

    def test_optimization_deduplication(self):
        """Test deduplication logic"""

        from utils.optimizations import DocumentOptimizer

        optimizer = DocumentOptimizer(self.spark)

        # Create test data with duplicates
        data = [
            ("doc1", "file1.pdf", "hash1"),
            ("doc2", "file2.pdf", "hash2"),
            ("doc3", "file3.pdf", "hash1"),  # Duplicate of doc1
        ]

        schema = StructType([
            StructField("document_id", StringType()),
            StructField("file_name", StringType()),
            StructField("checksum", StringType())
        ])

        incoming_df = self.spark.createDataFrame(data, schema)

        # Create processed table with one document
        processed_data = [("doc1", "hash1")]
        processed_schema = StructType([
            StructField("document_id", StringType()),
            StructField("checksum", StringType())
        ])

        processed_df = self.spark.createDataFrame(processed_data, processed_schema)
        processed_df.createOrReplaceTempView("processed_documents")

        # Test deduplication
        unique_df = optimizer.filter_duplicates(
            incoming_df,
            "processed_documents"
        )

        # Should have 1 unique document (doc2)
        self.assertEqual(unique_df.count(), 1)
        self.assertEqual(unique_df.first()["document_id"], "doc2")


if __name__ == "__main__":
    unittest.main()