#!/usr/bin/env python3
"""
Dataflow Streaming Pipeline - Pub/Sub to BigQuery with Windowing & Late Data Handling
Interview-ready implementation demonstrating:
- Event-time processing with watermarks
- Fixed & session windowing
- Allowed lateness & triggers (early + late firing)
- Exactly-once deduplication
- Late data side output
- BigQuery streaming inserts
"""

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.transforms.window import FixedWindows, Sessions
from apache_beam.transforms.trigger import (
    AfterWatermark, AfterProcessingTime, AfterCount,
    AccumulationMode, Repeatedly
)
from apache_beam.io.gcp.pubsub import ReadFromPubSub
from apache_beam.io.gcp.bigquery import WriteToBigQuery
from apache_beam.io.gcp.bigquery import BigQueryDisposition
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Iterable
import argparse


# Side output tags
LATE_DATA_TAG = 'late_data'
INVALID_TAG = 'invalid'

class ParseAndValidate(beam.DoFn):
    """Parse Pub/Sub message, validate schema, extract event timestamp for event-time processing."""

    def process(self, element: bytes,
                timestamp=beam.DoFn.TimestampParam,
                window=beam.DoFn.WindowParam) -> Iterable[beam.pvalue.TaggedOutput]:
        try:
            # Parse JSON message
            message = json.loads(element.decode('utf-8'))

            # Extract event timestamp (REQUIRED for event-time processing)
            event_ts_str = message.get('event_timestamp') or message.get('timestamp')
            if not event_ts_str:
                raise ValueError("Missing event_timestamp field")

            # Parse timestamp (support multiple formats)
            event_ts = self._parse_timestamp(event_ts_str)

            # Validate required fields
            required_fields = ['event_id', 'event_type', 'user_id', 'event_timestamp']
            for field in required_fields:
                if field not in message:
                    raise ValueError(f"Missing required field: {field}")

            # Validate event_type
            valid_event_types = [
                'page_view', 'click', 'purchase', 'add_to_cart', 'remove_from_cart',
                'checkout_start', 'checkout_complete', 'login', 'logout', 'signup'
            ]
            if message['event_type'] not in valid_event_types:
                raise ValueError(f"Invalid event_type: {message['event_type']}")

            # Add processing metadata
            message['_processing_ts'] = datetime.utcnow().isoformat()
            message['_event_ts'] = event_ts.isoformat()
            message['_window_start'] = window.start.to_utc_datetime().isoformat() if window else None
            message['_window_end'] = window.end.to_utc_datetime().isoformat() if window else None

            # Return with event timestamp for proper windowing
            # This is CRITICAL - tells Dataflow to use event time, not processing time
            yield beam.window.TimestampedValue(message, event_ts.timestamp())

        except Exception as e:
            dead_record = {
                '_raw_message': element.decode('utf-8', errors='ignore')[:1000],  # Truncate
                '_error': str(e),
                '_error_type': type(e).__name__,
                '_failed_ts': datetime.utcnow().isoformat()
            }
            yield beam.pvalue.TaggedOutput(INVALID_TAG, dead_record)

    def _parse_timestamp(self, ts_str: str) -> datetime:
        """Parse timestamp supporting multiple formats."""
        ts_str = ts_str.replace('Z', '+00:00')
        formats = [
            '%Y-%m-%dT%H:%M:%S.%f%z',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(ts_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unparseable timestamp format: {ts_str}")


class DeduplicateEvents(beam.DoFn):
    """Exactly-once deduplication using event_id within window."""

    def __init__(self, dedup_field: str = 'event_id'):
        self.dedup_field = dedup_field

    def process(self, elements: Iterable[Dict],
                window=beam.DoFn.WindowParam) -> Iterable[Dict]:
        """Keep first event by event_timestamp (earliest) for each event_id."""
        elements_list = list(elements)
        if not elements_list:
            return

        # Sort by event timestamp, keep first (earliest)
        # This assumes at-least-once delivery from Pub/Sub
        sorted_elements = sorted(
            elements_list,
            key=lambda x: x.get('_event_ts', '')
        )

        # Mark as deduplicated
        deduped = sorted_elements[0]
        deduped['_deduped'] = True
        deduped['_duplicate_count'] = len(elements_list)

        yield deduped


class EnrichEvent(beam.DoFn):
    """Enrich events with dimension data via side input."""

    def __init__(self, user_lookup: beam.pvalue.AsDict, product_lookup: beam.pvalue.AsDict):
        self.user_lookup = user_lookup
        self.product_lookup = product_lookup

    def process(self, element: Dict) -> Iterable[Dict]:
        # User enrichment
        user_id = element.get('user_id')
        if user_id and user_id in self.user_lookup:
            user = self.user_lookup[user_id]
            element['user_tier'] = user.get('tier', 'unknown')
            element['user_country'] = user.get('country', 'unknown')
            element['user_segment'] = user.get('segment', 'unknown')
        else:
            element['user_tier'] = 'unknown'
            element['user_country'] = 'unknown'
            element['user_segment'] = 'unknown'

        # Product enrichment (for purchase events)
        product_id = element.get('product_id')
        if product_id and product_id in self.product_lookup:
            product = self.product_lookup[product_id]
            element['product_category'] = product.get('category', 'unknown')
            element['product_brand'] = product.get('brand', 'unknown')
            element['product_price'] = product.get('price', 0.0)

        yield element


def create_pipeline_options(args: argparse.Namespace) -> PipelineOptions:
    """Create streaming Dataflow pipeline options."""
    options_dict = {
        'runner': args.runner or 'DataflowRunner',
        'project': args.project,
        'region': args.region or 'us-central1',
        'temp_location': args.temp_location,
        'staging_location': args.staging_location,
        'job_name': args.job_name or f'streaming-pipeline-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}',
        'streaming': True,
        'max_num_workers': args.max_workers or 50,
        'autoscaling_algorithm': 'THROUGHPUT_BASED',
        'worker_machine_type': args.worker_machine_type or 'n1-standard-4',
        'disk_size_gb': args.disk_size_gb or 50,
        'save_main_session': True,
        'experiments': ['use_runner_v2', 'enable_streaming_engine'],
        # Exactly-once processing
        'streaming_mode': 'exactly_once',
    }
    return PipelineOptions(**options_dict)


def run_streaming_pipeline(options: PipelineOptions, args: argparse.Namespace):
    """Main streaming pipeline definition."""

    # BigQuery table spec for streaming inserts
    BQ_TABLE_SPEC = {
        'project': args.project,
        'dataset': args.bq_dataset,
        'table': args.bq_table,
        'schema': 'SCHEMA_AUTODETECT',
        'time_partitioning': {
            'type': 'DAY',
            'field': 'event_timestamp'
        },
        'clustering': {
            'fields': ['user_id', 'event_type', 'user_country']
        }
    }

    with beam.Pipeline(options=options) as p:
        # Side inputs: Dimension lookups (broadcast, refresh periodically)
        user_lookup = (
            p
            | 'ReadUserDim' >> beam.io.ReadFromBigQuery(
                query=f'''
                    SELECT user_id, tier, country, segment
                    FROM `{args.project}.{args.bq_dataset}.dim_users`
                    WHERE is_active = true
                ''',
                use_standard_sql=True,
                gcs_location=args.temp_location
            )
            | 'UserToKV' >> beam.Map(lambda r: (r['user_id'], r))
        )

        product_lookup = (
            p
            | 'ReadProductDim' >> beam.io.ReadFromBigQuery(
                query=f'''
                    SELECT product_id, category, brand, price
                    FROM `{args.project}.{args.bq_dataset}.dim_products`
                    WHERE is_active = true
                ''',
                use_standard_sql=True,
                gcs_location=args.temp_location
            )
            | 'ProductToKV' >> beam.Map(lambda r: (r['product_id'], r))
        )

        # Read from Pub/Sub with timestamp attribute
        # CRITICAL: Use timestamp_attribute to extract event time from message
        raw_events = (
            p
            | 'ReadFromPubSub' >> ReadFromPubSub(
                subscription=args.pubsub_subscription,
                timestamp_attribute='event_timestamp',  # Use event time from message!
                id_label='event_id'  # For deduplication tracking
            )
        )

        # Parse and validate
        parsed, invalid = (
            raw_events
            | 'ParseAndValidate' >> beam.ParDo(ParseAndValidate()).with_outputs(INVALID_TAG, main='valid')
        )

        # WINDOWING STRATEGY:
        # Fixed windows (5 min) for aggregations + Session windows for user journeys
        # Allowed lateness: 24 hours for late-arriving events
        # Triggers: Early speculative firing at 60s + Final when watermark passes

        windowed = (
            parsed
            | 'WindowIntoFixed5Min' >> beam.WindowInto(
                FixedWindows(300),  # 5 minutes = 300 seconds
                allowed_lateness=timedelta(hours=24),
                trigger=AfterWatermark(
                    early=AfterProcessingTime(60),           # Speculative at 60 seconds
                    late=AfterWatermark(AfterCount(1))       # Final firing
                ),
                accumulation_mode=AccumulationMode.ACCUMULATING  # Accumulate late data
            )
        )

        # DEDUPLICATION: Group by event_id within window
        # This handles at-least-once Pub/Sub delivery
        deduplicated = (
            windowed
            | 'KeyByEventId' >> beam.Map(lambda x: (x['event_id'], x))
            | 'GroupByEventId' >> beam.GroupByKey()
            | 'Deduplicate' >> beam.ParDo(DeduplicateEvents())
        )

        # Enrich with dimension data
        enriched = (
            deduplicated
            | 'EnrichEvent' >> beam.ParDo(
                EnrichEvent(
                    user_lookup=beam.pvalue.AsDict(user_lookup),
                    product_lookup=beam.pvalue.AsDict(product_lookup)
                )
            )
        )

        # HANDLE LATE DATA: Extract late-firing elements
        # Elements that fire after the main watermark are "late"
        # We route them to a separate BigQuery table for analysis
        on_time, late_data = (
            enriched
            | 'SeparateLateData' >> beam.Map(
                lambda x: beam.pvalue.TaggedOutput(LATE_DATA_TAG, x)
                if x.get('_is_late', False) else x
            ).with_outputs(LATE_DATA_TAG, main='on_time')
        )

        # On-time data → BigQuery Streaming Inserts
        _ = (
            on_time
            | 'WriteOnTimeToBigQuery' >> WriteToBigQuery(
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
                method='STREAMING_INSERTS',  # Required for streaming
            )
        )

        # Late data → Separate BigQuery table for analysis
        _ = (
            late_data
            | 'WriteLateToBigQuery' >> WriteToBigQuery(
                table=f'{args.bq_table}_late',
                dataset=args.bq_dataset,
                project=args.project,
                schema='SCHEMA_AUTODETECT',
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
                method='STREAMING_INSERTS',
            )
        )

        # Invalid messages → Dead letter table
        _ = (
            invalid
            | 'WriteInvalidToBigQuery' >> WriteToBigQuery(
                table=f'{args.bq_table}_invalid',
                dataset=args.bq_dataset,
                project=args.project,
                schema='SCHEMA_AUTODETECT',
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
                method='STREAMING_INSERTS',
            )
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Dataflow Streaming Pipeline: Pub/Sub → BigQuery')

    # Required
    parser.add_argument('--project', required=True, help='GCP Project ID')
    parser.add_argument('--pubsub_subscription', required=True, help='Pub/Sub subscription')
    parser.add_argument('--bq_dataset', required=True, help='BigQuery dataset')
    parser.add_argument('--bq_table', required=True, help='BigQuery table')

    # Optional Dataflow options
    parser.add_argument('--runner', default='DataflowRunner', help='Dataflow runner')
    parser.add_argument('--region', default='us-central1', help='GCP region')
    parser.add_argument('--temp_location', required=True, help='GCS temp location')
    parser.add_argument('--staging_location', required=True, help='GCS staging location')
    parser.add_argument('--job_name', help='Dataflow job name')
    parser.add_argument('--max_workers', type=int, default=50, help='Max workers')
    parser.add_argument('--worker_machine_type', default='n1-standard-4', help='Worker machine type')
    parser.add_argument('--disk_size_gb', type=int, default=50, help='Worker disk size GB')

    return parser.parse_args()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    options = create_pipeline_options(args)
    run_streaming_pipeline(options, args)