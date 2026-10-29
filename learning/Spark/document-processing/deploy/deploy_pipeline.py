# deploy/deploy_pipeline.py
"""
Deployment script for the document processing pipeline
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config import load_config
from notebooks import (
    DocumentIngestion,
    DocumentProcessor,
    ErrorHandler,
    DocumentOptimizer,
    DownstreamProcessor
)


def deploy_full_pipeline(config_path: str = "config/config.yaml"):
    """Deploy the complete document processing pipeline"""

    print("=" * 80)
    print("Deploying Document Processing Pipeline")
    print("=" * 80)

    # Load configuration
    config = load_config(config_path)

    # Initialize Spark session
    from pyspark.sql import SparkSession

    spark = SparkSession.builder \
        .appName("DocumentProcessingPipeline") \
        .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
        .config("spark.sql.shuffle.partitions", "200") \
        .config("spark.default.parallelism", "100") \
        .getOrCreate()

    try:
        # Step 1: Set up ingestion
        print("\n[1/5] Setting up document ingestion...")
        ingestion = DocumentIngestion(
            storage_account=config['storage']['account_name'],
            container=config['storage']['containers']['incoming']
        )

        ingestion_schema = ingestion.create_bronze_table(
            config['databricks']['delta_path']
        )

        # Step 2: Set up document processor
        print("[2/5] Setting up document processor...")
        processor = DocumentProcessor(
            endpoint=config['azure']['document_intelligence']['endpoint'],
            api_key=config['azure']['document_intelligence']['api_key'],
            spark_session=spark
        )

        # Step 3: Set up error handler
        print("[3/5] Setting up error handling...")
        error_handler = ErrorHandler(
            spark=spark,
            delta_path=config['databricks']['delta_path']
        )

        # Step 4: Set up optimizer
        print("[4/5] Setting up optimizations...")
        optimizer = DocumentOptimizer(spark)

        # Step 5: Set up downstream processor
        print("[5/5] Setting up downstream integration...")
        downstream = DownstreamProcessor(spark)

        # Create gold layer tables
        downstream.create_gold_layer(
            gold_path=f"{config['databricks']['delta_path']}/gold"
        )

        print("\n" + "=" * 80)
        print("Pipeline deployment completed successfully!")
        print("=" * 80)

        # Print next steps
        print("\nNext steps:")
        print(
            "1. Upload documents to: abfss://incoming-documents@yourstorageaccount.dfs.core.windows.net/prod/incoming/")
        print("2. Monitor processing at: Databricks Jobs Dashboard")
        print("3. Query results from: gold.documents table")
        print("4. Set up alerts in: Databricks Alerts")

        return True

    except Exception as e:
        print(f"\nError during deployment: {e}")
        raise

    finally:
        spark.stop()


def deploy_monitoring_dashboard():
    """Deploy monitoring and alerting dashboard"""

    from monitoring.dashboard import create_monitoring_dashboard

    print("\nDeploying monitoring dashboard...")

    dashboard = create_monitoring_dashboard()
    dashboard.deploy()

    print("Monitoring dashboard deployed!")
    print("Access at: https://your-databricks-workspace/sql/dashboards/document-processing-monitoring")


def run_initial_test(config_path: str = "config/config.yaml"):
    """Run initial test with sample documents"""

    from tests.integration_test import run_integration_test

    print("\nRunning initial integration test...")

    success = run_integration_test(config_path)

    if success:
        print("Integration test passed!")
    else:
        print("Integration test failed. Check logs for details.")

    return success


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Deploy document processing pipeline")
    parser.add_argument("--config", default="config/config.yaml", help="Configuration file path")
    parser.add_argument("--test", action="store_true", help="Run integration test after deployment")
    parser.add_argument("--dashboard", action="store_true", help="Deploy monitoring dashboard")

    args = parser.parse_args()

    # Deploy pipeline
    deploy_full_pipeline(args.config)

    # Run test if requested
    if args.test:
        run_initial_test(args.config)

    # Deploy dashboard if requested
    if args.dashboard:
        deploy_monitoring_dashboard()