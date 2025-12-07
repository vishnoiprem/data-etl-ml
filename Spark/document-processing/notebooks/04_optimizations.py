# notebooks/04_optimizations.py
"""
Performance Optimizations and Cost Savings
Advanced techniques for large-scale document processing
"""

import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class OptimizationMetrics:
    """Metrics for optimization performance"""
    deduplication_rate: float
    cost_savings_percentage: float
    processing_time_reduction: float
    api_calls_saved: int
    total_documents_processed: int


class DocumentOptimizer:
    """Optimizes document processing for performance and cost"""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    @lru_cache(maxsize=1000)
    def get_content_hash(self, content: bytes) -> str:
        """Get cached content hash for deduplication"""
        return hashlib.sha256(content).hexdigest()

    def filter_duplicates(self,
                          incoming_df: DataFrame,
                          processed_table: str = "silver.processed_documents",
                          lookback_days: int = 365) -> DataFrame:
        """
        Filter out documents that have already been processed

        Args:
            incoming_df: DataFrame with new documents
            processed_table: Table with processed documents
            lookback_days: Number of days to look back for duplicates

        Returns:
            DataFrame with duplicates removed
        """

        # Get checksums of already processed documents
        processed_checksums = self.spark.sql(f"""
            SELECT DISTINCT checksum
            FROM {processed_table}
            WHERE processing_time >= DATE_SUB(CURRENT_DATE(), {lookback_days})
            UNION
            SELECT DISTINCT checksum
            FROM bronze.dlq_documents
            WHERE created_at >= DATE_SUB(CURRENT_DATE(), {lookback_days})
        """)

        # Get counts for logging
        total_incoming = incoming_df.count()

        # Remove duplicates
        unique_df = incoming_df.join(
            processed_checksums,
            "checksum",
            "left_anti"
        )

        unique_count = unique_df.count()
        duplicates = total_incoming - unique_count

        if total_incoming > 0:
            deduplication_rate = duplicates / total_incoming
            print(f"Deduplication: Removed {duplicates} duplicates ({deduplication_rate:.2%})")

        return unique_df

    def optimize_batch_size(self,
                            df: DataFrame,
                            target_size_mb: int = 100,
                            max_documents: int = 1000) -> List[DataFrame]:
        """
        Split DataFrame into optimal batches for API processing

        Args:
            df: DataFrame to batch
            target_size_mb: Target batch size in MB
            max_documents: Maximum documents per batch

        Returns:
            List of batched DataFrames
        """

        # Calculate size per document
        df_with_size = df.withColumn(
            "estimated_size_mb",
            col("file_size") / (1024 * 1024)
        )

        # Collect and create batches
        documents = df_with_size.collect()
        batches = []
        current_batch = []
        current_batch_size = 0

        for doc in documents:
            doc_size = doc["estimated_size_mb"]

            # Check if adding this document would exceed limits
            if (len(current_batch) >= max_documents or
                    (current_batch_size + doc_size) > target_size_mb):

                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_batch_size = 0

            current_batch.append(doc)
            current_batch_size += doc_size

        # Add last batch if not empty
        if current_batch:
            batches.append(current_batch)

        # Convert batches back to DataFrames
        batch_dfs = []
        for i, batch in enumerate(batches):
            batch_df = self.spark.createDataFrame(batch)
            batch_df = batch_df.withColumn("batch_id", lit(i))
            batch_dfs.append(batch_df)

        print(f"Created {len(batch_dfs)} batches for processing")
        return batch_dfs

    def parallelize_api_calls(self,
                              documents_df: DataFrame,
                              max_concurrent: int = 10,
                              rate_limit_tps: int = 15) -> DataFrame:
        """
        Control parallelism to stay within API rate limits

        Args:
            documents_df: Documents to process
            max_concurrent: Maximum concurrent API calls
            rate_limit_tps: API rate limit in transactions per second
        """

        # Calculate optimal partitions based on rate limit
        # Assuming each document takes ~2 seconds on average
        avg_processing_time = 2  # seconds
        optimal_concurrent = min(
            max_concurrent,
            rate_limit_tps * avg_processing_time
        )

        print(f"Optimal concurrent API calls: {optimal_concurrent}")

        # Repartition for controlled parallelism
        repartitioned_df = documents_df.repartition(optimal_concurrent)

        return repartitioned_df

    def cache_intermediate_results(self, df: DataFrame) -> DataFrame:
        """Cache intermediate results for iterative processing"""

        # Cache if DataFrame will be used multiple times
        df.cache()
        df.count()  # Force caching

        return df

    def optimize_storage(self,
                         table_name: str,
                         zorder_columns: List[str] = None,
                         optimize_frequency: str = "daily") -> None:
        """
        Optimize Delta table storage layout

        Args:
            table_name: Table to optimize
            zorder_columns: Columns for Z-Ordering
            optimize_frequency: How often to run optimization
        """

        # Optimize file size
        self.spark.sql(f"""
            OPTIMIZE {table_name}
            ZORDER BY {', '.join(zorder_columns) if zorder_columns else 'partition_date'}
        """)

        # Vacuum old files
        retention_hours = 168  # 7 days
        self.spark.sql(f"""
            VACUUM {table_name} RETAIN {retention_hours} HOURS
        """)

        print(f"Optimized storage for {table_name}")

    def monitor_performance(self) -> Dict:
        """Monitor processing performance metrics"""

        metrics = self.spark.sql("""
            SELECT 
                DATE(processing_time) as processing_date,
                COUNT(*) as total_documents,
                AVG(processing_time_ms) as avg_processing_time_ms,
                AVG(page_count) as avg_page_count,
                AVG(confidence_score) as avg_confidence,
                SUM(CASE WHEN processing_status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN processing_status = 'error' THEN 1 ELSE 0 END) as error_count,
                COUNT(DISTINCT model_used) as models_used
            FROM silver.processed_documents
            WHERE processing_time >= DATE_SUB(CURRENT_DATE(), 7)
            GROUP BY DATE(processing_time)
            ORDER BY processing_date DESC
        """).collect()

        # Calculate error rate
        error_rates = []
        for row in metrics:
            if row["total_documents"] > 0:
                error_rate = row["error_count"] / row["total_documents"]
                error_rates.append(error_rate)

        avg_error_rate = sum(error_rates) / len(error_rates) if error_rates else 0

        # Get cost optimization metrics
        model_usage = self.spark.sql("""
            SELECT 
                model_used,
                COUNT(*) as document_count,
                SUM(page_count) as total_pages
            FROM silver.processed_documents
            WHERE processing_time >= DATE_SUB(CURRENT_DATE(), 30)
            GROUP BY model_used
        """).collect()

        return {
            "daily_metrics": [row.asDict() for row in metrics],
            "avg_error_rate": avg_error_rate,
            "model_usage": [row.asDict() for row in model_usage]
        }

    def create_performance_report(self) -> Dict:
        """Create comprehensive performance report"""

        metrics = self.monitor_performance()

        report = {
            "generated_at": datetime.now().isoformat(),
            "time_period": "Last 7 days",
            "summary": {
                "total_documents": sum(m["total_documents"] for m in metrics["daily_metrics"]),
                "avg_processing_time_ms": sum(m["avg_processing_time_ms"] for m in metrics["daily_metrics"]) / len(
                    metrics["daily_metrics"]),
                "avg_error_rate": metrics["avg_error_rate"]
            },
            "model_efficiency": self._calculate_model_efficiency(metrics["model_usage"]),
            "recommendations": self._generate_recommendations(metrics)
        }

        return report

    def _calculate_model_efficiency(self, model_usage: List[Dict]) -> Dict:
        """Calculate efficiency metrics for each model"""

        # Model costs (relative)
        model_costs = {
            "prebuilt-read": 1.0,
            "prebuilt-layout": 6.67,
            "prebuilt-invoice": 6.67,
            "prebuilt-receipt": 6.67,
            "prebuilt-idDocument": 6.67
        }

        efficiency = {}
        for usage in model_usage:
            model = usage["model_used"]
            pages = usage["total_pages"]
            cost_multiplier = model_costs.get(model, 6.67)

            efficiency[model] = {
                "documents": usage["document_count"],
                "pages": pages,
                "cost_multiplier": cost_multiplier,
                "relative_cost": pages * cost_multiplier
            }

        return efficiency

    def _generate_recommendations(self, metrics: Dict) -> List[str]:
        """Generate optimization recommendations"""

        recommendations = []

        # Check error rate
        if metrics["avg_error_rate"] > 0.05:
            recommendations.append(
                "High error rate detected. Consider improving error handling or preprocessing."
            )

        # Check model usage
        model_usage = metrics["model_usage"]
        read_count = sum(1 for m in model_usage if m["model_used"] == "prebuilt-read")
        layout_count = sum(1 for m in model_usage if m["model_used"] == "prebuilt-layout")

        if layout_count > read_count * 2:
            recommendations.append(
                "High usage of expensive layout model. Consider implementing better model selection "
                "to use prebuilt-read for simple documents."
            )

        # Check processing time
        avg_time = metrics["daily_metrics"][0]["avg_processing_time_ms"]
        if avg_time > 5000:  # 5 seconds
            recommendations.append(
                f"High average processing time ({avg_time:.0f}ms). Consider optimizing batch sizes "
                "or implementing parallel processing."
            )

        return recommendations


class CostOptimizer:
    """Optimizes processing costs through intelligent strategies"""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def analyze_cost_savings(self) -> Dict:
        """Analyze potential cost savings opportunities"""

        # Analyze model usage patterns
        usage_patterns = self.spark.sql("""
            WITH document_stats AS (
                SELECT 
                    document_id,
                    page_count,
                    total_word_count,
                    confidence_score,
                    model_used,
                    CASE 
                        WHEN ARRAY_SIZE(tables) > 0 THEN true
                        ELSE false
                    END as has_tables,
                    CASE 
                        WHEN ARRAY_SIZE(key_value_pairs) > 0 THEN true
                        ELSE false
                    END as has_key_value_pairs
                FROM silver.processed_documents
                WHERE processing_status = 'success'
                AND processing_time >= DATE_SUB(CURRENT_DATE(), 30)
            )
            SELECT 
                model_used,
                COUNT(*) as document_count,
                AVG(page_count) as avg_pages,
                AVG(total_word_count) as avg_words,
                AVG(confidence_score) as avg_confidence,
                SUM(CASE WHEN has_tables THEN 1 ELSE 0 END) as docs_with_tables,
                SUM(CASE WHEN has_key_value_pairs THEN 1 ELSE 0 END) as docs_with_kv_pairs
            FROM document_stats
            GROUP BY model_used
        """).collect()

        # Calculate potential savings
        potential_savings = 0
        recommendations = []

        for pattern in usage_patterns:
            model = pattern["model_used"]
            docs = pattern["document_count"]
            avg_pages = pattern["avg_pages"]

            # Check if layout model was used unnecessarily
            if model == "prebuilt-layout" and pattern["docs_with_tables"] == 0:
                potential_docs = pattern["document_count"]
                potential_pages = potential_docs * avg_pages

                # Calculate savings (layout is 6.67x more expensive than read)
                savings = potential_pages * (6.67 - 1.0)
                potential_savings += savings

                recommendations.append({
                    "model": model,
                    "recommendation": f"Consider using prebuilt-read for {potential_docs} documents without tables",
                    "potential_savings": savings,
                    "documents_affected": potential_docs
                })

        return {
            "usage_patterns": [p.asDict() for p in usage_patterns],
            "potential_savings": potential_savings,
            "recommendations": recommendations
        }

    def implement_cost_saving_rules(self, df: DataFrame) -> DataFrame:
        """Apply cost-saving rules to document processing"""

        from utils.model_selector import ModelSelector

        # Define cost-saving rules
        @udf(StringType())
        def cost_optimized_model_udf(file_path: str,
                                     has_tables: bool,
                                     is_structured: bool) -> str:
            if not has_tables and not is_structured:
                # Use cheaper read model for simple documents
                return ModelType.READ.value

            # Use original model selection logic for others
            return ModelSelector.select_model(file_path, "auto")

        # Apply cost optimization
        optimized_df = df.withColumn(
            "optimized_model",
            cost_optimized_model_udf(
                col("file_path"),
                col("has_tables"),
                col("is_structured_document")
            )
        )

        return optimized_df

    def create_cost_report(self, time_period_days: int = 30) -> Dict:
        """Create detailed cost analysis report"""

        # Get actual usage data
        usage_data = self.spark.sql(f"""
            SELECT 
                model_used,
                SUM(page_count) as total_pages,
                COUNT(*) as document_count
            FROM silver.processed_documents
            WHERE processing_time >= DATE_SUB(CURRENT_DATE(), {time_period_days})
            AND processing_status = 'success'
            GROUP BY model_used
        """).collect()

        # Convert to model selector format
        model_usage = {
            row["model_used"]: row["total_pages"]
            for row in usage_data
        }

        # Calculate savings
        from utils.model_selector import ModelSelector
        cost_analysis = ModelSelector.calculate_cost_savings(model_usage)

        # Add business context
        report = {
            "period_days": time_period_days,
            "total_documents": sum(row["document_count"] for row in usage_data),
            "total_pages": sum(row["total_pages"] for row in usage_data),
            "cost_analysis": cost_analysis,
            "model_distribution": model_usage,
            "estimated_monthly_cost": cost_analysis["current_cost"] * (30 / time_period_days),
            "optimization_opportunities": self._identify_cost_opportunities(usage_data)
        }

        return report

    def _identify_cost_opportunities(self, usage_data: List[Row]) -> List[Dict]:
        """Identify specific cost optimization opportunities"""

        opportunities = []

        # Look for layout model usage on simple documents
        layout_usage = next((row for row in usage_data if row["model_used"] == "prebuilt-layout"), None)

        if layout_usage:
            # Sample documents to check for table presence
            sample_docs = self.spark.sql("""
                SELECT 
                    document_id,
                    file_name,
                    ARRAY_SIZE(tables) as table_count,
                    page_count
                FROM silver.processed_documents
                WHERE model_used = 'prebuilt-layout'
                AND processing_time >= DATE_SUB(CURRENT_DATE(), 7)
                LIMIT 100
            """).collect()

            docs_without_tables = [doc for doc in sample_docs if doc["table_count"] == 0]

            if docs_without_tables:
                percentage = len(docs_without_tables) / len(sample_docs)
                opportunities.append({
                    "type": "model_overuse",
                    "description": f"{percentage:.1%} of layout-model documents have no tables",
                    "potential_savings": f"Up to {percentage:.1%} of layout model costs",
                    "action": "Implement better model selection for documents without tables"
                })

        return opportunities