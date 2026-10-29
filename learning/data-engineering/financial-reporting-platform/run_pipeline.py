#!/usr/bin/env python3
"""
Main pipeline runner for Financial Reporting Platform
"""
import sys
import os
import logging
from datetime import datetime
from loguru import logger

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ingestion.extractor import DataExtractor
from ingestion.transformer import DataTransformer
from processing.business_logic import FinancialMetricsCalculator
from monitoring.quality_checks import DataQualityChecker


class FinancialReportingPipeline:
    """Main pipeline orchestrator"""

    def __init__(self, config_path: str = None):
        self.setup_logging()
        self.extractor = DataExtractor()
        self.transformer = DataTransformer()
        self.calculator = FinancialMetricsCalculator()
        self.quality_checker = DataQualityChecker()

    def setup_logging(self):
        """Configure logging"""
        logger.remove()  # Remove default handler
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO"
        )
        logger.add(
            "logs/pipeline_{time:YYYY-MM-DD}.log",
            rotation="500 MB",
            retention="10 days",
            level="DEBUG"
        )

    def run_full_pipeline(self, generate_data: bool = True):
        """Run complete ETL pipeline"""
        logger.info("=" * 60)
        logger.info("Starting Financial Reporting Pipeline")
        logger.info("=" * 60)

        try:
            # Step 1: Extract
            logger.info("Step 1: Data Extraction")
            if generate_data:
                logger.info("Generating sample data...")
                bronze_data = self.extractor.extract_all_sources()
                self.extractor.save_to_bronze(bronze_data)
                logger.info(f"Generated {sum(len(df) for df in bronze_data.values())} records")
            else:
                bronze_data = self.extractor.load_from_bronze()
                logger.info(f"Loaded {sum(len(df) for df in bronze_data.values())} records from bronze")

            # Step 2: Transform
            logger.info("Step 2: Data Transformation")
            silver_data = self.transformer.transform_to_silver(bronze_data)
            total_silver = sum(len(df) for df in silver_data.values())
            logger.info(f"Transformed {total_silver} records to silver layer")

            # Step 3: Quality Check
            logger.info("Step 3: Data Quality Check")
            quality_report = self.quality_checker.run_all_checks(silver_data)
            self.quality_checker.generate_report(quality_report)

            # Step 4: Business Logic Processing
            logger.info("Step 4: Business Logic Processing")
            gold_data = self.calculator.create_gold_layer(silver_data)
            logger.info(f"Created {len(gold_data)} gold layer tables")

            # Step 5: Generate Reports
            logger.info("Step 5: Report Generation")
            self.generate_reports(gold_data)

            logger.info("=" * 60)
            logger.info("Pipeline completed successfully!")
            logger.info("=" * 60)

            return {
                "status": "success",
                "records_processed": total_silver,
                "tables_created": len(gold_data),
                "quality_score": quality_report.get('overall_score', 0)
            }

        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            return {"status": "failed", "error": str(e)}

    def generate_reports(self, gold_data: dict):
        """Generate output reports"""
        from src.reporting.dashboard import DashboardGenerator

        dashboard_gen = DashboardGenerator()

        # Generate HTML dashboard
        dashboard_path = dashboard_gen.create_html_dashboard(gold_data)
        logger.info(f"Dashboard generated: {dashboard_path}")

        # Generate Excel report
        excel_path = "output/financial_report.xlsx"
        dashboard_gen.export_to_excel(gold_data, excel_path)
        logger.info(f"Excel report generated: {excel_path}")

        # Print summary to console
        self.print_executive_summary(gold_data)

    def print_executive_summary(self, gold_data: dict):
        """Print executive summary to console"""
        if 'executive_summary' in gold_data:
            summary = gold_data['executive_summary']
            print("\n" + "=" * 60)
            print("EXECUTIVE SUMMARY")
            print("=" * 60)

            for _, row in summary.iterrows():
                country = row.get('country_key', 'Unknown')
                revenue = row.get('REVENUE', 0)
                cogs = row.get('COGS', 0)
                expenses = row.get('EXPENSE', 0)
                gross_profit = row.get('gross_profit', 0)
                net_profit = row.get('net_profit', 0)

                print(f"\nCountry: {country}")
                print(f"  Revenue: ${revenue:,.2f}")
                print(f"  COGS: ${cogs:,.2f}")
                print(f"  Gross Profit: ${gross_profit:,.2f}")
                print(f"  Operating Expenses: ${expenses:,.2f}")
                print(f"  Net Profit: ${net_profit:,.2f}")

                if revenue > 0:
                    gross_margin = (gross_profit / revenue) * 100
                    net_margin = (net_profit / revenue) * 100
                    print(f"  Gross Margin: {gross_margin:.1f}%")
                    print(f"  Net Margin: {net_margin:.1f}%")

            print("=" * 60)


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Financial Reporting Pipeline")
    parser.add_argument("--no-generate", action="store_true", help="Skip data generation")
    parser.add_argument("--quick", action="store_true", help="Run quick test with less data")
    parser.add_argument("--config", type=str, help="Path to config file")

    args = parser.parse_args()

    # Create necessary directories
    os.makedirs("data/bronze", exist_ok=True)
    os.makedirs("data/silver", exist_ok=True)
    os.makedirs("data/gold", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    # Run pipeline
    pipeline = FinancialReportingPipeline(args.config)
    result = pipeline.run_full_pipeline(not args.no_generate)

    if result["status"] == "success":
        print(f"\n✓ Pipeline completed successfully!")
        print(f"  Records processed: {result['records_processed']:,}")
        print(f"  Tables created: {result['tables_created']}")
        print(f"  Data quality score: {result['quality_score']:.1%}")
    else:
        print(f"\n✗ Pipeline failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()