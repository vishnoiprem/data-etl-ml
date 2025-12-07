# notebooks/03_error_handling.py
"""
Error Handling and Dead Letter Queue Implementation
Ensures no document is lost during processing
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of processing errors"""
    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    INVALID_FORMAT = "invalid_format"
    CORRUPTED_FILE = "corrupted_file"
    SIZE_EXCEEDED = "size_exceeded"
    TIMEOUT = "timeout"
    UNSUPPORTED_TYPE = "unsupported_type"
    UNKNOWN = "unknown"


class DeadLetterQueue:
    """Manages failed document processing with retry logic"""

    def __init__(self, spark: SparkSession, delta_path: str):
        self.spark = spark
        self.delta_path = delta_path
        self._create_dlq_table()

    def _create_dlq_table(self):
        """Create Dead Letter Queue Delta table"""

        self.spark.sql(f"""
            CREATE TABLE IF NOT EXISTS bronze.dlq_documents (
                dlq_id STRING GENERATED ALWAYS AS (uuid()),
                document_id STRING NOT NULL,
                file_name STRING NOT NULL,
                file_path STRING NOT NULL,
                file_size LONG,
                content_type STRING,
                checksum STRING,
                original_partition_date DATE,
                ingestion_time TIMESTAMP,
                error_category STRING NOT NULL,
                error_message STRING,
                error_details STRING,
                processing_attempts INT NOT NULL,
                max_attempts INT NOT NULL,
                next_retry_time TIMESTAMP,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                resolved BOOLEAN NOT NULL,
                resolution STRING,
                resolution_time TIMESTAMP,
                resolution_notes STRING
            )
            USING DELTA
            LOCATION '{self.delta_path}/bronze/dlq_documents'
            PARTITIONED BY (original_partition_date)
            TBLPROPERTIES (
                delta.enableChangeDataFeed = true,
                delta.autoOptimize.optimizeWrite = true
            )
        """)

    def categorize_error(self, error_message: str) -> ErrorCategory:
        """Categorize error for better handling"""

        error_lower = error_message.lower()

        if "rate limit" in error_lower or "429" in error_lower:
            return ErrorCategory.RATE_LIMIT

        elif "timeout" in error_lower or "timed out" in error_lower:
            return ErrorCategory.TIMEOUT

        elif "invalid format" in error_lower or "unsupported format" in error_lower:
            return ErrorCategory.INVALID_FORMAT

        elif "corrupted" in error_lower or "cannot read" in error_lower:
            return ErrorCategory.CORRUPTED_FILE

        elif "size limit" in error_lower or "too large" in error_lower:
            return ErrorCategory.SIZE_EXCEEDED

        elif "api" in error_lower or "service" in error_lower:
            return ErrorCategory.API_ERROR

        else:
            return ErrorCategory.UNKNOWN

    def route_failed_documents(self,
                               failed_df: DataFrame,
                               error_category: ErrorCategory,
                               error_details: str = "") -> None:
        """Route failed documents to DLQ"""

        current_time = datetime.now()
        next_retry = current_time + timedelta(hours=1)  # Initial retry after 1 hour

        dlq_records = failed_df.select(
            "document_id",
            "file_name",
            "file_path",
            "file_size",
            "content_type",
            "checksum",
            "partition_date",
            "ingestion_time",
            lit(error_category.value).alias("error_category"),
            col("error_message").alias("error_message"),
            lit(error_details).alias("error_details"),
            lit(1).alias("processing_attempts"),
            lit(3).alias("max_attempts"),  # Max 3 retries
            lit(next_retry).alias("next_retry_time"),
            lit(current_time).alias("created_at"),
            lit(current_time).alias("updated_at"),
            lit(False).alias("resolved"),
            lit(None).alias("resolution"),
            lit(None).alias("resolution_time"),
            lit(None).alias("resolution_notes")
        )

        # Write to DLQ
        dlq_records.write \
            .format("delta") \
            .mode("append") \
            .saveAsTable("bronze.dlq_documents")

        logger.info(f"Routed {failed_df.count()} documents to DLQ with category: {error_category}")

    def get_retry_candidates(self,
                             max_attempts: int = 3,
                             retry_window_hours: int = 24) -> DataFrame:
        """Get documents eligible for retry"""

        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=retry_window_hours)

        retry_candidates = self.spark.sql(f"""
            SELECT 
                dlq_id,
                document_id,
                file_name,
                file_path,
                file_size,
                content_type,
                checksum,
                original_partition_date,
                ingestion_time,
                error_category,
                error_message,
                error_details,
                processing_attempts,
                max_attempts,
                next_retry_time,
                created_at,
                updated_at
            FROM bronze.dlq_documents
            WHERE 
                resolved = false
                AND processing_attempts < max_attempts
                AND next_retry_time <= '{current_time.isoformat()}'
                AND created_at >= '{cutoff_time.isoformat()}'
            ORDER BY 
                processing_attempts ASC,
                created_at ASC
            LIMIT 1000  # Batch size for retry
        """)

        return retry_candidates

    def update_retry_attempt(self,
                             dlq_id: str,
                             success: bool,
                             new_error_message: str = None,
                             increment_attempt: bool = True) -> None:
        """Update DLQ record after retry attempt"""

        current_time = datetime.now()

        if success:
            # Mark as resolved
            update_sql = f"""
                UPDATE bronze.dlq_documents
                SET 
                    resolved = true,
                    resolution = 'retry_success',
                    resolution_time = '{current_time.isoformat()}',
                    updated_at = '{current_time.isoformat()}'
                WHERE dlq_id = '{dlq_id}'
            """
        else:
            if increment_attempt:
                # Increment attempt count and set next retry
                next_retry = current_time + timedelta(hours=2)  # Exponential backoff
                update_sql = f"""
                    UPDATE bronze.dlq_documents
                    SET 
                        processing_attempts = processing_attempts + 1,
                        error_message = '{new_error_message}',
                        next_retry_time = '{next_retry.isoformat()}',
                        updated_at = '{current_time.isoformat()}'
                    WHERE dlq_id = '{dlq_id}'
                """
            else:
                # Update error without incrementing attempt
                update_sql = f"""
                    UPDATE bronze.dlq_documents
                    SET 
                        error_message = '{new_error_message}',
                        updated_at = '{current_time.isoformat()}'
                    WHERE dlq_id = '{dlq_id}'
                """

        self.spark.sql(update_sql)

    def resolve_manually(self,
                         dlq_id: str,
                         resolution: str,
                         notes: str = "") -> None:
        """Manually resolve a DLQ entry"""

        current_time = datetime.now()

        update_sql = f"""
            UPDATE bronze.dlq_documents
            SET 
                resolved = true,
                resolution = '{resolution}',
                resolution_notes = '{notes}',
                resolution_time = '{current_time.isoformat()}',
                updated_at = '{current_time.isoformat()}'
            WHERE dlq_id = '{dlq_id}'
        """

        self.spark.sql(update_sql)

    def get_dlq_metrics(self) -> Dict:
        """Get metrics on DLQ status"""

        metrics_df = self.spark.sql("""
            SELECT 
                error_category,
                COUNT(*) as error_count,
                AVG(processing_attempts) as avg_attempts,
                SUM(CASE WHEN resolved THEN 1 ELSE 0 END) as resolved_count,
                MIN(created_at) as oldest_error,
                MAX(created_at) as newest_error
            FROM bronze.dlq_documents
            WHERE created_at >= DATE_SUB(CURRENT_TIMESTAMP(), 7)
            GROUP BY error_category
            ORDER BY error_count DESC
        """)

        total_df = self.spark.sql("""
            SELECT 
                COUNT(*) as total_errors,
                COUNT(CASE WHEN resolved THEN 1 END) as total_resolved,
                COUNT(CASE WHEN NOT resolved AND processing_attempts >= max_attempts THEN 1 END) as permanent_failures
            FROM bronze.dlq_documents
            WHERE created_at >= DATE_SUB(CURRENT_TIMESTAMP(), 30)
        """)

        metrics = {
            "by_category": metrics_df.collect(),
            "totals": total_df.first().asDict() if total_df.count() > 0 else {}
        }

        return metrics

    def clean_old_records(self, days_to_keep: int = 90) -> None:
        """Clean old DLQ records"""

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        self.spark.sql(f"""
            DELETE FROM bronze.dlq_documents
            WHERE created_at < '{cutoff_date.isoformat()}'
            AND resolved = true
        """)

        logger.info(f"Cleaned old DLQ records older than {days_to_keep} days")


class ErrorHandler:
    """Main error handling orchestrator"""

    def __init__(self, spark: SparkSession, delta_path: str):
        self.spark = spark
        self.dlq = DeadLetterQueue(spark, delta_path)
        self._setup_alerts()

    def _setup_alerts(self):
        """Set up alerting thresholds"""

        self.alert_thresholds = {
            "error_rate": 0.05,  # 5% error rate
            "dlq_size": 1000,  # 1000 documents in DLQ
            "stale_errors": 24,  # Errors older than 24 hours
        }

    def handle_processing_errors(self, processed_df: DataFrame) -> Tuple[DataFrame, DataFrame]:
        """Split processing results into success and failure DataFrames"""

        # Separate successful and failed documents
        successful_df = processed_df.filter(
            col("processing_status") == "success"
        )

        failed_df = processed_df.filter(
            col("processing_status") == "error"
        )

        # Categorize and route failures
        if failed_df.count() > 0:
            failed_df = failed_df.withColumn(
                "error_category",
                self._categorize_error_udf(col("error_message"))
            )

            # Route to DLQ by category
            error_categories = failed_df.select("error_category").distinct().collect()

            for category_row in error_categories:
                category = category_row["error_category"]
                category_failures = failed_df.filter(
                    col("error_category") == category
                )

                self.dlq.route_failed_documents(
                    category_failures,
                    ErrorCategory(category),
                    "Initial processing failure"
                )

        return successful_df, failed_df

    @staticmethod
    @udf(StringType())
    def _categorize_error_udf(error_message: str) -> str:
        """UDF for error categorization"""
        handler = ErrorHandler._create_handler_instance()
        category = handler.dlq.categorize_error(error_message)
        return category.value

    @staticmethod
    def _create_handler_instance():
        """Create handler instance for UDF context"""
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        return ErrorHandler(spark, "dbfs:/mnt/document_processing")

    def check_alerts(self) -> List[Dict]:
        """Check if any alert thresholds are exceeded"""

        alerts = []

        # Get current error rate
        recent_processing = self.spark.sql("""
            SELECT 
                COUNT(*) as total_processed,
                COUNT(CASE WHEN processing_status = 'error' THEN 1 END) as error_count
            FROM silver.processed_documents
            WHERE processing_time >= DATE_SUB(CURRENT_TIMESTAMP(), 1)
        """).first()

        if recent_processing["total_processed"] > 0:
            error_rate = recent_processing["error_count"] / recent_processing["total_processed"]

            if error_rate > self.alert_thresholds["error_rate"]:
                alerts.append({
                    "type": "high_error_rate",
                    "message": f"Error rate {error_rate:.2%} exceeds threshold {self.alert_thresholds['error_rate']:.2%}",
                    "severity": "warning",
                    "details": {
                        "error_count": recent_processing["error_count"],
                        "total_processed": recent_processing["total_processed"],
                        "error_rate": error_rate
                    }
                })

        # Check DLQ size
        dlq_size = self.spark.sql("""
            SELECT COUNT(*) as dlq_count
            FROM bronze.dlq_documents
            WHERE resolved = false
        """).first()["dlq_count"]

        if dlq_size > self.alert_thresholds["dlq_size"]:
            alerts.append({
                "type": "dlq_size_exceeded",
                "message": f"DLQ size {dlq_size} exceeds threshold {self.alert_thresholds['dlq_size']}",
                "severity": "critical",
                "details": {"dlq_size": dlq_size}
            })

        # Check for stale errors
        stale_errors = self.spark.sql(f"""
            SELECT COUNT(*) as stale_count
            FROM bronze.dlq_documents
            WHERE 
                resolved = false
                AND created_at < DATE_SUB(CURRENT_TIMESTAMP(), {self.alert_thresholds['stale_errors']})
        """).first()["stale_count"]

        if stale_errors > 0:
            alerts.append({
                "type": "stale_errors",
                "message": f"Found {stale_errors} unresolved errors older than {self.alert_thresholds['stale_errors']} hours",
                "severity": "warning",
                "details": {"stale_count": stale_errors}
            })

        return alerts

    def send_alerts(self, alerts: List[Dict]):
        """Send alerts through configured channels"""

        for alert in alerts:
            if alert["severity"] == "critical":
                self._send_critical_alert(alert)
            elif alert["severity"] == "warning":
                self._send_warning_alert(alert)

            # Log all alerts
            logger.warning(f"Alert: {alert['type']} - {alert['message']}")

    def _send_critical_alert(self, alert: Dict):
        """Send critical alert (implement based on your alerting system)"""
        # Example: Send to Slack, Email, PagerDuty, etc.
        print(f"CRITICAL ALERT: {alert['message']}")

    def _send_warning_alert(self, alert: Dict):
        """Send warning alert"""
        print(f"WARNING: {alert['message']}")