# monitoring/dashboard.py
"""
Monitoring dashboard for document processing pipeline
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pyspark.sql import SparkSession
import plotly.graph_objects as go
from plotly.subplots import make_subplots


@dataclass
class DashboardMetrics:
    """Metrics for dashboard display"""
    processing_volume: int
    success_rate: float
    avg_processing_time: float
    cost_today: float
    dlq_size: int
    top_error_categories: List[Dict]
    model_distribution: List[Dict]


class MonitoringDashboard:
    """Creates and manages monitoring dashboard"""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def get_daily_metrics(self) -> DashboardMetrics:
        """Get daily metrics for dashboard"""

        # Processing volume and success rate
        processing_stats = self.spark.sql("""
            SELECT 
                COUNT(*) as total_processed,
                AVG(processing_time_ms) as avg_processing_time,
                SUM(CASE WHEN processing_status = 'success' THEN 1 ELSE 0 END) as success_count
            FROM silver.processed_documents
            WHERE processing_time >= DATE_SUB(CURRENT_TIMESTAMP(), 1)
        """).first()

        # DLQ size
        dlq_stats = self.spark.sql("""
            SELECT COUNT(*) as dlq_count
            FROM bronze.dlq_documents
            WHERE resolved = false
            AND created_at >= DATE_SUB(CURRENT_TIMESTAMP(), 7)
        """).first()

        # Error categories
        error_categories = self.spark.sql("""
            SELECT 
                error_category,
                COUNT(*) as error_count
            FROM bronze.dlq_documents
            WHERE created_at >= DATE_SUB(CURRENT_TIMESTAMP(), 7)
            GROUP BY error_category
            ORDER BY error_count DESC
            LIMIT 5
        """).collect()

        # Model distribution
        model_distribution = self.spark.sql("""
            SELECT 
                model_used,
                COUNT(*) as document_count
            FROM silver.processed_documents
            WHERE processing_time >= DATE_SUB(CURRENT_TIMESTAMP(), 7)
            AND processing_status = 'success'
            GROUP BY model_used
        """).collect()

        # Calculate success rate
        total = processing_stats["total_processed"] or 0
        success = processing_stats["success_count"] or 0
        success_rate = success / total if total > 0 else 0

        return DashboardMetrics(
            processing_volume=total,
            success_rate=success_rate,
            avg_processing_time=processing_stats["avg_processing_time"] or 0,
            cost_today=self._estimate_daily_cost(),
            dlq_size=dlq_stats["dlq_count"] or 0,
            top_error_categories=[row.asDict() for row in error_categories],
            model_distribution=[row.asDict() for row in model_distribution]
        )

    def _estimate_daily_cost(self) -> float:
        """Estimate daily processing cost"""

        # Get page count by model
        page_counts = self.spark.sql("""
            SELECT 
                model_used,
                SUM(page_count) as total_pages
            FROM silver.processed_documents
            WHERE processing_time >= DATE_SUB(CURRENT_TIMESTAMP(), 1)
            AND processing_status = 'success'
            GROUP BY model_used
        """).collect()

        # Cost per 1000 pages (Azure Document Intelligence pricing)
        model_costs = {
            "prebuilt-read": 1.50,
            "prebuilt-layout": 10.00,
            "prebuilt-invoice": 10.00,
            "prebuilt-receipt": 10.00,
            "prebuilt-idDocument": 10.00
        }

        total_cost = 0
        for row in page_counts:
            model = row["model_used"]
            pages = row["total_pages"] or 0
            cost_per_k = model_costs.get(model, 10.00)
            total_cost += (pages / 1000) * cost_per_k

        return total_cost

    def create_metrics_plot(self) -> go.Figure:
        """Create metrics visualization plot"""

        # Get time series data
        time_series = self.spark.sql("""
            SELECT 
                DATE(processing_time) as date,
                COUNT(*) as documents,
                AVG(processing_time_ms) as avg_time,
                AVG(confidence_score) as avg_confidence
            FROM silver.processed_documents
            WHERE processing_time >= DATE_SUB(CURRENT_TIMESTAMP(), 30)
            AND processing_status = 'success'
            GROUP BY DATE(processing_time)
            ORDER BY date
        """).collect()

        # Prepare data
        dates = [row["date"] for row in time_series]
        documents = [row["documents"] for row in time_series]
        avg_times = [row["avg_time"] for row in time_series]
        avg_confidences = [row["avg_confidence"] for row in time_series]

        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Document Volume', 'Average Processing Time',
                            'Confidence Scores', 'Model Distribution'),
            specs=[[{'type': 'bar'}, {'type': 'scatter'}],
                   [{'type': 'scatter'}, {'type': 'pie'}]]
        )

        # Document volume
        fig.add_trace(
            go.Bar(x=dates, y=documents, name='Documents'),
            row=1, col=1
        )

        # Processing time
        fig.add_trace(
            go.Scatter(x=dates, y=avg_times, mode='lines+markers', name='Processing Time (ms)'),
            row=1, col=2
        )

        # Confidence scores
        fig.add_trace(
            go.Scatter(x=dates, y=avg_confidences, mode='lines+markers', name='Confidence'),
            row=2, col=1
        )

        # Model distribution (last 7 days)
        model_data = self.spark.sql("""
            SELECT 
                model_used,
                COUNT(*) as count
            FROM silver.processed_documents
            WHERE processing_time >= DATE_SUB(CURRENT_TIMESTAMP(), 7)
            GROUP BY model_used
        """).collect()

        models = [row["model_used"] for row in model_data]
        counts = [row["count"] for row in model_data]

        fig.add_trace(
            go.Pie(labels=models, values=counts, name='Model Distribution'),
            row=2, col=2
        )

        # Update layout
        fig.update_layout(
            title='Document Processing Metrics',
            showlegend=True,
            height=800
        )

        return fig

    def generate_daily_report(self) -> str:
        """Generate daily report in markdown format"""

        metrics = self.get_daily_metrics()

        report = f"""# Document Processing Daily Report
## {datetime.now().strftime('%Y-%m-%d')}

### Summary
- **Documents Processed**: {metrics.processing_volume:,}
- **Success Rate**: {metrics.success_rate:.2%}
- **Average Processing Time**: {metrics.avg_processing_time:.0f} ms
- **Estimated Daily Cost**: ${metrics.cost_today:.2f}
- **Documents in DLQ**: {metrics.dlq_size}

### Top Error Categories
"""

        for error in metrics.top_error_categories:
            report += f"- **{error['error_category']}**: {error['error_count']} errors\n"

        report += "\n### Model Distribution\n"
        for model in metrics.model_distribution:
            report += f"- **{model['model_used']}**: {model['document_count']} documents\n"

        # Add recommendations
        report += "\n### Recommendations\n"

        if metrics.success_rate < 0.95:
            report += "- ⚠️  Success rate below 95%. Review error logs.\n"

        if metrics.dlq_size > 100:
            report += "- ⚠️  DLQ size exceeds 100 documents. Investigate persistent failures.\n"

        if "prebuilt-layout" in [m['model_used'] for m in metrics.model_distribution]:
            layout_count = next(m['document_count'] for m in metrics.model_distribution
                                if m['model_used'] == 'prebuilt-layout')
            if layout_count > metrics.processing_volume * 0.5:
                report += "- 💰  High usage of expensive layout model. Consider model optimization.\n"

        return report

    def create_alert_rules(self) -> List[Dict]:
        """Create alert rules for monitoring"""

        alert_rules = [
            {
                "name": "high_error_rate",
                "condition": "success_rate < 0.95",
                "severity": "warning",
                "message": "Document processing success rate below 95%"
            },
            {
                "name": "dlq_threshold",
                "condition": "dlq_size > 100",
                "severity": "critical",
                "message": "DLQ size exceeds 100 documents"
            },
            {
                "name": "processing_slowdown",
                "condition": "avg_processing_time > 10000",
                "severity": "warning",
                "message": "Average processing time exceeds 10 seconds"
            },
            {
                "name": "cost_alert",
                "condition": "cost_today > 100",
                "severity": "warning",
                "message": "Daily processing cost exceeds $100"
            }
        ]

        return alert_rules