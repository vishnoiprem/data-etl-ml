#!/usr/bin/env python3
"""
Dataflow Batch Pipeline - GCS to BigQuery with Validation & Dead Letter
Interview-ready implementation demonstrating:
- Schema validation & type coercion
- Side input enrichment
- Tagged outputs (valid / dead_letter)
- BigQuery partitioned & clustered writes
- Composer-ready structure
"""

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io.gcp.bigquery import WriteToBigQuery
from apache_beam.io.gcp.bigquery import BigQueryDisposition
from apache_beam.io.parquetio import ReadFromParquet
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
import argparse


class ValidateAndEnrich(beam.DoFn):
    """Validate schema, enforce business rules, enrich with lookups."""

    VALID_TAG = 'valid'
    DEAD_LETTER_TAG = 'dead_letter'

    def __init__(self, schema: Dict[str, Any], required_fields: list):
        self.schema = schema
        self.required_fields = required_fields

    def process(self, element: Dict[str, Any],
                customer_lookup: beam.pvalue.AsDict) -> beam.pvalue.TaggedOutput:
        try:
            # 1. Schema validation & type coercion
            validated = self._validate_and_coerce(element)

            # 2. Business rule validation
            if not self._business_rules(validated):
                raise ValueError("Business rule validation failed")

            # 3. Enrichment via side input (customer dimension)
            enriched = self._enrich_customer(validated, customer_lookup)

            # 4. Add processing metadata
            enriched['_processed_ts'] = datetime.utcnow().isoformat()
            enriched['_pipeline_version'] = '1.0.0'

            yield beam.pvalue.TaggedOutput(self.VALID_TAG, enriched)

        except Exception as e:
            dead_record = {
                **element,
                '_error': str(e),
                '_error_type': type(e).__name__,
                '_failed_ts': datetime.utcnow().isoformat(),
                '_source_file': element.get('_source_file', 'unknown')
            }
            yield beam.pvalue.TaggedOutput(self.DEAD_LETTER_TAG, dead_record)

    def _validate_and_coerce(self, record: Dict) -> Dict:
        """Validate required fields and coerce types per schema."""
        validated = {}
        for field, expected_type in self.schema.items():
            value = record.get(field)

            if value is None or value == '':
                if field in self.required_fields:
                    raise ValueError(f"Required field missing or empty: {field}")
                validated[field] = None
            else:
                validated[field] = self._coerce_type(value, expected_type)
        return validated

    def _coerce_type(self, value: Any, expected_type: str) -> Any:
        """Coerce value to expected BigQuery type."""
        try:
            if expected_type == 'INTEGER':
                return int(float(value))  # Handle "1.0" -> 1
            elif expected_type == 'FLOAT':
                return float(value)
            elif expected_type == 'BOOLEAN':
                return str(value).lower() in ('true', '1', 'yes', 'y', 't')
            elif expected_type == 'TIMESTAMP':
                # Handle multiple timestamp formats
                val_str = str(value).replace('Z', '+00:00')
                for fmt in ['%Y-%m-%dT%H:%M:%S.%f%z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S']:
                    try:
                        return datetime.strptime(val_str, fmt)
                    except ValueError:
                        continue
                raise ValueError(f"Unparseable timestamp: {value}")
            elif expected_type == 'DATE':
                val_str = str(value)
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y']:
                    try:
                        return datetime.strptime(val_str, fmt).date()
                    except ValueError:
                        continue
                raise ValueError(f"Unparseable date: {value}")
            else:
                return str(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Type coercion failed for {field}={value} -> {expected_type}: {e}")

    def _business_rules(self, record: Dict) -> bool:
        """Enforce business logic rules."""
        # Amount must be positive
        if record.get('amount', 0) <= 0:
            return False

        # Order date not in future
        order_date = record.get('order_date')
        if order_date and order_date > datetime.utcnow().date():
            return False

        # Status must be valid
        valid_statuses = ['PENDING', 'CONFIRMED', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'RETURNED']
        if record.get('status') and record['status'] not in valid_statuses:
            return False

        # Quantity positive integer
        if record.get('quantity', 0) <= 0:
            return False

        return True

    def _enrich_customer(self, record: Dict, lookup: Dict) -> Dict:
        """Enrich with customer dimension data via side input."""
        customer_id = record.get('customer_id')
        if customer_id and customer_id in lookup:
            cust = lookup[customer_id]
            record['customer_tier'] = cust.get('tier', 'unknown')
            record['customer_region'] = cust.get('region', 'unknown')
            record['customer_segment'] = cust.get('segment', 'unknown')
        else:
            record['customer_tier'] = 'unknown'
            record['customer_region'] = 'unknown'
            record['customer_segment'] = 'unknown'
        return record


class WriteDeadLetterToGCS(beam.DoFn):
    """Write dead letter records to GCS for replay/analysis."""

    def __init__(self, dead_letter_bucket: str, dead_letter_prefix: str):
        self.dead_letter_bucket = dead_letter_bucket
        self.dead_letter_prefix = dead_letter_prefix

    def process(self, element: Dict, window=beam.DoFn.WindowParam):
        # Organize by date for easy replay
        date_str = datetime.utcnow().strftime('%Y/%m/%d')
        hour_str = datetime.utcnow().strftime('%H')

        # In production: batch writes using FileIO or write to Pub/Sub for separate consumer
        # This is a simplified version - replace with beam.io.WriteToText with custom naming
        gcs_path = f"gs://{self.dead_letter_bucket}/{self.dead_letter_prefix}/{date_str}/{hour_str}/dead_letters.jsonl"

        logging.info(f"DEAD LETTER [{gcs_path}]: {json.dumps(element, default=str)}")

        # Yield for potential downstream processing
        yield beam.pvalue.TaggedOutput('logged', element)


def create_pipeline_options(args: argparse.Namespace) -> PipelineOptions:
    """Create Dataflow pipeline options from CLI args."""
    options_dict = {
        'runner': args.runner or 'DataflowRunner',
        'project': args.project,
        'region': args.region or 'us-central1',
        'temp_location': args.temp_location,
        'staging_location': args.staging_location,
        'job_name': args.job_name or f'batch-pipeline-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}',
        'max_num_workers': args.max_workers or 20,
        'autoscaling_algorithm': 'THROUGHPUT_BASED',
        'worker_machine_type': args.worker_machine_type or 'n1-standard-4',
        'disk_size_gb': args.disk_size_gb or 50,
        'save_main_session': True,
        'experiments': ['use_runner_v2'],
    }

    # Streaming-specific (not used for batch but good to know)
    # 'streaming': False,
    # 'enable_streaming_engine': False,

    return PipelineOptions(**options_dict)


def run_pipeline(options: PipelineOptions, args: argparse.Namespace):
    """Main pipeline definition."""

    # Schema definition (in production: load from Schema Registry / Data Catalog)
    SCHEMA = {
        'order_id': 'STRING',
        'customer_id': 'STRING',
        'product_id': 'STRING',
        'amount': 'FLOAT',
        'quantity': 'INTEGER',
        'order_date': 'TIMESTAMP',
        'status': 'STRING',
        'channel': 'STRING',
        'currency': 'STRING',
    }
    REQUIRED_FIELDS = ['order_id', 'customer_id', 'amount', 'order_date', 'status']

    # BigQuery table specification with partitioning & clustering
    BQ_TABLE_SPEC = {
        'project': args.project,
        'dataset': args.bq_dataset,
        'table': args.bq_table,
        'schema': 'SCHEMA_AUTODETECT',
        'time_partitioning': {
            'type': 'DAY',
            'field': 'order_date',
            'expiration_ms': 7776000000  # 90 days retention
        },
        'clustering': {
            'fields': ['customer_id', 'region', 'status', 'channel']
        }
    }

    with beam.Pipeline(options=options) as p:
        # Side input: Customer dimension lookup (broadcast to all workers)
        # In production: use CoGroupByKey for large dimensions, or BigQuery side input
        customer_lookup = (
            p
            | 'ReadCustomerDim' >> beam.io.ReadFromBigQuery(
                query=f'''
                    SELECT customer_id, tier, region, segment
                    FROM `{args.project}.{args.bq_dataset}.dim_customers`
                    WHERE is_active = true
                ''',
                use_standard_sql=True,
                gcs_location=args.temp_location
            )
            | 'CustomerToKV' >> beam.Map(lambda r: (r['customer_id'], r))
        )

        # Main pipeline: Read → Validate → Enrich → Write
        valid, dead_letter = (
            p
            | 'ReadParquetFromGCS' >> ReadFromParquet(
                f'gs://{args.gcs_bucket}/{args.gcs_prefix}/*.parquet',
                with_filename=True
            )
            | 'AddSourceFilename' >> beam.Map(
                lambda kv: {**kv[0], '_source_file': kv[1]}
            )
            | 'ValidateEnrich' >> beam.ParDo(
                ValidateAndEnrich(SCHEMA, REQUIRED_FIELDS),
                customer_lookup=beam.pvalue.AsDict(customer_lookup)
            ).with_outputs(
                ValidateAndEnrich.VALID_TAG,
                ValidateAndEnrich.DEAD_LETTER_TAG
            )
        )

        # Valid records → BigQuery (partitioned by order_date, clustered by customer_id, region)
        _ = (
            valid
            | 'WriteValidToBigQuery' >> WriteToBigQuery(
                table=BQ_TABLE_SPEC['table'],
                dataset=BQ_TABLE_SPEC['dataset'],
                project=BQ_TABLE_SPEC['project'],
                schema=BQ_TABLE_SPEC['schema'],
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
                additional_bq_parameters={
                    'timePartitioning': BQ_TABLE_SPEC['time_partitioning'],
                    'clustering': BQ_TABLE_SPEC['clustering']
                },
                method='FILE_LOADS',  # Use FILE_LOADS for batch, STREAMING_INSERTS for streaming
                triggering_frequency=60  # Seconds between loads
            )
        )

        # Dead letters → GCS for replay/analysis
        _ = (
            dead_letter
            | 'WriteDeadLetterToGCS' >> beam.ParDo(
                WriteDeadLetterToGCS(args.dead_letter_bucket, args.dead_letter_prefix)
            )
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Dataflow Batch Pipeline: GCS → BigQuery')

    # Required
    parser.add_argument('--project', required=True, help='GCP Project ID')
    parser.add_argument('--gcs_bucket', required=True, help='GCS bucket for source data')
    parser.add_argument('--gcs_prefix', required=True, help='GCS prefix/path for source files')
    parser.add_argument('--bq_dataset', required=True, help='BigQuery dataset')
    parser.add_argument('--bq_table', required=True, help='BigQuery table')
    parser.add_argument('--dead_letter_bucket', required=True, help='GCS bucket for dead letters')
    parser.add_argument('--dead_letter_prefix', required=True, help='GCS prefix for dead letters')

    # Optional Dataflow options
    parser.add_argument('--runner', default='DataflowRunner', help='Dataflow runner')
    parser.add_argument('--region', default='us-central1', help='GCP region')
    parser.add_argument('--temp_location', required=True, help='GCS temp location')
    parser.add_argument('--staging_location', required=True, help='GCS staging location')
    parser.add_argument('--job_name', help='Dataflow job name')
    parser.add_argument('--max_workers', type=int, default=20, help='Max workers')
    parser.add_argument('--worker_machine_type', default='n1-standard-4', help='Worker machine type')
    parser.add_argument('--disk_size_gb', type=int, default=50, help='Worker disk size GB')

    return parser.parse_args()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    options = create_pipeline_options(args)
    run_pipeline(options, args)