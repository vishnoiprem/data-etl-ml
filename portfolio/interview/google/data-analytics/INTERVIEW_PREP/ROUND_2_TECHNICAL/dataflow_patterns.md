# Dataflow Patterns - Batch & Streaming
## Apache Beam on Google Cloud Dataflow - Interview Ready

---

## 🔄 Batch Pipeline Pattern (GCS → Dataflow → BigQuery)

### Architecture
```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌─────────────┐
│  GCS Landing│───▶│   Dataflow       │───▶│   BigQuery      │───▶│  Composer   │
│  (Parquet/  │    │  (Apache Beam)   │    │  (Partitioned/  │    │  Orchestration│
│   Avro/CSV) │    │                  │    │   Clustered)    │    │               │
└─────────────┘    └──────────────────┘    └─────────────────┘    └─────────────┘
                          │                        │
                   ┌──────┴──────┐          ┌─────┴─────┐
                   ▼             ▼          ▼           ▼
             ┌──────────┐  ┌──────────┐ ┌────────┐ ┌────────┐
             │ Validate │  │ Transform│ │ Dead   │ │ Audit  │
             │ (DoFn)   │  │ (DoFn)   │ │ Letter │ │ Table  │
             └──────────┘  └──────────┘ └────────┘ └────────┘
```

### Complete Python Implementation
```python
# dataflow_batch_pipeline.py
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io.gcp.bigquery import WriteToBigQuery
from apache_beam.io.gcp.bigquery import BigQueryDisposition
import logging
import json
from datetime import datetime
from typing import Dict, Any, Tuple

class ValidateAndEnrich(beam.DoFn):
    """Validate schema, enrich with lookups, route valid/invalid."""
    
    VALID_TAG = 'valid'
    DEAD_LETTER_TAG = 'dead_letter'
    
    def __init__(self, schema: Dict, lookup_table: str):
        self.schema = schema
        self.lookup_table = lookup_table  # Side input for enrichment
    
    def process(self, element: Dict, lookup_data: beam.pvalue.AsDict) -> Tuple:
        try:
            # 1. Schema validation
            validated = self._validate_schema(element)
            
            # 2. Business rule validation
            if not self._business_rules(validated):
                raise ValueError("Business rule violation")
            
            # 3. Enrichment via side input
            enriched = self._enrich(validated, lookup_data)
            
            # 4. Add processing metadata
            enriched['_processed_ts'] = datetime.utcnow().isoformat()
            enriched['_pipeline_version'] = '1.0.0'
            
            yield beam.pvalue.TaggedOutput(self.VALID_TAG, enriched)
            
        except Exception as e:
            # Dead letter with full context
            dead_record = {
                **element,
                '_error': str(e),
                '_error_type': type(e).__name__,
                '_failed_ts': datetime.utcnow().isoformat(),
                '_source_file': element.get('_source_file', 'unknown')
            }
            yield beam.pvalue.TaggedOutput(self.DEAD_LETTER_TAG, dead_record)
    
    def _validate_schema(self, record: Dict) -> Dict:
        """Coerce types, check required fields."""
        validated = {}
        for field, expected_type in self.schema.items():
            value = record.get(field)
            if value is None:
                if field in self.schema.get('required', []):
                    raise ValueError(f"Required field missing: {field}")
                validated[field] = None
            else:
                validated[field] = self._coerce_type(value, expected_type)
        return validated
    
    def _coerce_type(self, value: Any, expected_type: str) -> Any:
        try:
            if expected_type == 'INTEGER':
                return int(value)
            elif expected_type == 'FLOAT':
                return float(value)
            elif expected_type == 'BOOLEAN':
                return str(value).lower() in ('true', '1', 'yes')
            elif expected_type == 'TIMESTAMP':
                return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
            else:
                return str(value)
        except (ValueError, TypeError):
            raise ValueError(f"Type coercion failed: {value} -> {expected_type}")
    
    def _business_rules(self, record: Dict) -> bool:
        """Custom business validation."""
        # Example: amount > 0, date not future, valid status
        if record.get('amount', 0) <= 0:
            return False
        if record.get('order_date') and record['order_date'] > datetime.utcnow().date():
            return False
        return True
    
    def _enrich(self, record: Dict, lookup: Dict) -> Dict:
        """Join with reference data via side input."""
        customer_id = record.get('customer_id')
        if customer_id and customer_id in lookup:
            record['customer_tier'] = lookup[customer_id].get('tier', 'unknown')
            record['customer_region'] = lookup[customer_id].get('region', 'unknown')
        return record


class WriteDeadLetter(beam.DoFn):
    """Write dead letters to GCS for replay."""
    
    def __init__(self, dead_letter_path: str):
        self.dead_letter_path = dead_letter_path
    
    def process(self, element: Dict, window=beam.DoFn.WindowParam):
        # Partition by date for organized replay
        date_str = datetime.utcnow().strftime('%Y/%m/%d')
        file_path = f"{self.dead_letter_path}/{date_str}/dead_letters_{window.start.to_utc_datetime().strftime('%H%M%S')}.jsonl"
        
        # In production: use beam.io.WriteToText with file naming
        # For demo: log (replace with actual GCS write)
        logging.info(f"DEAD LETTER: {json.dumps(element)}")
        yield element


def run_pipeline(options: PipelineOptions):
    """Main pipeline entry point."""
    
    # Schema definition (in production: load from Schema Registry)
    SCHEMA = {
        'order_id': 'STRING',
        'customer_id': 'STRING',
        'product_id': 'STRING',
        'amount': 'FLOAT',
        'quantity': 'INTEGER',
        'order_date': 'TIMESTAMP',
        'status': 'STRING',
        'required': ['order_id', 'customer_id', 'amount', 'order_date']
    }
    
    # BigQuery table spec with partitioning & clustering
    BQ_TABLE_SPEC = {
        'project': 'my-project',
        'dataset': 'analytics',
        'table': 'orders',
        'schema': 'SCHEMA_AUTODETECT',
        'time_partitioning': {
            'type': 'DAY',
            'field': 'order_date',
            'expiration_ms': 7776000000  # 90 days
        },
        'clustering': {
            'fields': ['customer_id', 'region', 'status']
        }
    }
    
    with beam.Pipeline(options=options) as p:
        # Side input: customer lookup (small enough for memory)
        customer_lookup = (
            p 
            | 'ReadCustomerLookup' >> beam.io.ReadFromBigQuery(
                query='SELECT customer_id, tier, region FROM `project.dim.customers`',
                use_standard_sql=True
            )
            | 'ToDict' >> beam.Map(lambda r: (r['customer_id'], r))
        )
        
        # Main pipeline
        valid, dead_letter = (
            p
            | 'ReadFromGCS' >> beam.io.ReadFromParquet(
                'gs://my-bucket/landing/orders/*.parquet',
                with_filename=True
            )
            | 'AddSourceFile' >> beam.Map(lambda kv: {**kv[0], '_source_file': kv[1]})
            | 'ValidateAndEnrich' >> beam.ParDo(
                ValidateAndEnrich(SCHEMA, 'customers'),
                lookup_data=beam.pvalue.AsDict(customer_lookup)
            ).with_outputs(
                ValidateAndEnrich.VALID_TAG,
                ValidateAndEnrich.DEAD_LETTER_TAG
            )
        )
        
        # Valid records → BigQuery
        _ = (
            valid
            | 'WriteToBigQuery' >> WriteToBigQuery(
                table=BQ_TABLE_SPEC['table'],
                dataset=BQ_TABLE_SPEC['dataset'],
                project=BQ_TABLE_SPEC['project'],
                schema=BQ_TABLE_SPEC['schema'],
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
                additional_bq_parameters={
                    'timePartitioning': BQ_TABLE_SPEC['time_partitioning'],
                    'clustering': BQ_TABLE_SPEC['clustering']
                }
            )
        )
        
        # Dead letters → GCS for replay
        _ = (
            dead_letter
            | 'WriteDeadLetter' >> beam.ParDo(
                WriteDeadLetter('gs://my-bucket/dead-letters/orders')
            )
        )

if __name__ == '__main__':
    options = PipelineOptions(
        runner='DataflowRunner',
        project='my-project',
        region='us-central1',
        temp_location='gs://my-bucket/temp',
        staging_location='gs://my-bucket/staging',
        job_name='orders-batch-pipeline',
        max_num_workers=20,
        autoscaling_algorithm='THROUGHPUT_BASED',
        worker_machine_type='n1-standard-4',
        disk_size_gb=50,
        save_main_session=True
    )
    run_pipeline(options)
```

---

## 🌊 Streaming Pipeline Pattern (Pub/Sub → Dataflow → BigQuery)

### Architecture with Windowing & Late Data Handling
```
┌─────────────┐    ┌────────────────────────────────────────────────────────┐
│  Pub/Sub    │───▶│                    Dataflow (Beam)                      │
│  (Events)   │    │                                                           │
└─────────────┘    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
                   │  │  Window     │  │  Watermark  │  │  Allowed    │     │
                   │  │  (Fixed/    │──▶│  (Event     │──▶│  Lateness   │     │
                   │  │   Session)  │   │   Time)     │   │  (24 hrs)   │     │
                   │  └─────────────┘  └─────────────┘  └─────────────┘     │
                   │        │               │               │                │
                   │        ▼               ▼               ▼                │
                   │  ┌─────────────────────────────────────────────┐       │
                   │  │           Deduplication                     │       │
                   │  │  GroupByKey(event_id) → Keep first          │       │
                   │  └─────────────────────────────────────────────┘       │
                   │        │                                               │
                   │        ▼                                               │
                   │  ┌─────────────────────────────────────────────┐       │
                   │  │           Transform & Enrich                │       │
                   │  └─────────────────────────────────────────────┘       │
                   │        │                                               │
                   ▼        ▼                                               ▼
            ┌─────────────────────┐    ┌─────────────────────────────┐
            │ BigQuery Streaming  │    │ Dead Letter (Late/Invalid)  │
            │ (Partitioned/       │    │ GCS + BigQuery Audit Table  │
            │  Clustered)         │    │                             │
            └─────────────────────┘    └─────────────────────────────┘
```

### Complete Streaming Implementation
```python
# dataflow_streaming_pipeline.py
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
from typing import Dict, Any

# Late data tag for side output
LATE_DATA_TAG = 'late_data'

class ParseAndValidate(beam.DoFn):
    """Parse Pub/Sub message, validate schema, extract event timestamp."""
    
    def process(self, element: bytes, timestamp=beam.DoFn.TimestampParam):
        try:
            message = json.loads(element.decode('utf-8'))
            
            # Extract event timestamp (REQUIRED for event-time processing)
            event_ts_str = message.get('event_timestamp')
            if not event_ts_str:
                raise ValueError("Missing event_timestamp")
            
            event_ts = datetime.fromisoformat(event_ts_str.replace('Z', '+00:00'))
            
            # Validate required fields
            required = ['event_id', 'event_type', 'user_id', 'event_timestamp']
            for field in required:
                if field not in message:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add processing metadata
            message['_processing_ts'] = datetime.utcnow().isoformat()
            message['_event_ts'] = event_ts.isoformat()
            
            # Return with event timestamp for windowing
            yield beam.window.TimestampedValue(message, event_ts.timestamp())
            
        except Exception as e:
            # Invalid messages to dead letter
            dead_record = {
                '_raw_message': element.decode('utf-8', errors='ignore'),
                '_error': str(e),
                '_failed_ts': datetime.utcnow().isoformat()
            }
            yield beam.pvalue.TaggedOutput('invalid', dead_record)


class DeduplicateEvents(beam.DoFn):
    """Exactly-once deduplication using event_id + event_time window."""
    
    def __init__(self, dedup_window_hours: int = 24):
        self.dedup_window_hours = dedup_window_hours
    
    def process(self, elements: list, window=beam.DoFn.WindowParam):
        # Elements already grouped by event_id within window
        # Keep first (earliest event_time) - assumes at-least-once delivery
        if elements:
            # Sort by event timestamp, keep first
            sorted_elements = sorted(elements, key=lambda x: x.get('_event_ts', ''))
            yield sorted_elements[0]


def run_streaming_pipeline(options: PipelineOptions):
    """Streaming pipeline with windowing, watermarks, late data handling."""
    
    BQ_TABLE_SPEC = {
        'project': 'my-project',
        'dataset': 'analytics',
        'table': 'events_streaming',
        'schema': 'SCHEMA_AUTODETECT',
        'time_partitioning': {
            'type': 'DAY',
            'field': 'event_timestamp'
        },
        'clustering': {
            'fields': ['user_id', 'event_type', 'region']
        }
    }
    
    with beam.Pipeline(options=options) as p:
        # Read from Pub/Sub with timestamp attribute
        raw_events = (
            p
            | 'ReadFromPubSub' >> ReadFromPubSub(
                subscription='projects/my-project/subscriptions/events-sub',
                timestamp_attribute='event_timestamp'  # Use event time!
            )
        )
        
        # Parse and validate
        parsed, invalid = (
            raw_events
            | 'ParseAndValidate' >> beam.ParDo(ParseAndValidate()).with_outputs('invalid', main='valid')
        )
        
        # Windowing: 5-minute fixed windows with 24-hour allowed lateness
        windowed = (
            parsed
            | 'WindowInto' >> beam.WindowInto(
                FixedWindows(300),  # 5 minutes
                allowed_lateness=timedelta(hours=24),
                trigger=AfterWatermark(
                    early=AfterProcessingTime(60),      # Speculative at 60s
                    late=AfterWatermark(AfterCount(1))  # Final when watermark passes
                ),
                accumulation_mode=AccumulationMode.ACCUMULATING
            )
        )
        
        # Deduplication: Group by event_id within window
        deduplicated = (
            windowed
            | 'KeyByEventId' >> beam.Map(lambda x: (x['event_id'], x))
            | 'GroupByEventId' >> beam.GroupByKey()
            | 'Deduplicate' >> beam.ParDo(DeduplicateEvents())
        )
        
        # Handle late data (side output from watermark)
        late_data = (
            deduplicated
            | 'ExtractLateData' >> beam.FlatMap(
                lambda x: [beam.pvalue.TaggedOutput(LATE_DATA_TAG, x)] if x.get('_is_late') else [x]
            ).with_outputs(LATE_DATA_TAG, main='on_time')
        )
        
        # On-time data → BigQuery Streaming
        _ = (
            late_data.on_time
            | 'WriteToBigQuery' >> WriteToBigQuery(
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
                method='STREAMING_INSERTS'
            )
        )
        
        # Late data → Dead letter (separate table for analysis)
        _ = (
            late_data[LATE_DATA_TAG]
            | 'WriteLateData' >> WriteToBigQuery(
                table='events_late',
                dataset='analytics',
                project='my-project',
                schema='SCHEMA_AUTODETECT',
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                method='STREAMING_INSERTS'
            )
        )
        
        # Invalid messages → Dead letter
        _ = (
            invalid
            | 'WriteInvalid' >> WriteToBigQuery(
                table='events_invalid',
                dataset='analytics',
                project='my-project',
                schema='SCHEMA_AUTODETECT',
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                method='STREAMING_INSERTS'
            )
        )

if __name__ == '__main__':
    options = PipelineOptions(
        runner='DataflowRunner',
        project='my-project',
        region='us-central1',
        temp_location='gs://my-bucket/temp',
        staging_location='gs://my-bucket/staging',
        job_name='events-streaming-pipeline',
        streaming=True,
        max_num_workers=50,
        autoscaling_algorithm='THROUGHPUT_BASED',
        worker_machine_type='n1-standard-4',
        disk_size_gb=50,
        save_main_session=True,
        # Streaming-specific
        streaming_mode='exactly_once',
        enable_streaming_engine=True
    )
    run_streaming_pipeline(options)
```

---

## ⚖️ Lambda vs Kappa Architecture Decision

| Dimension | Lambda | Kappa |
|-----------|--------|-------|
| **Complexity** | Dual codebase (batch + stream) | Single codebase |
| **Latency** | Batch: hours, Stream: seconds | Unified: seconds-minutes |
| **Correctness** | Batch as truth, stream approx | Stream as truth, backfill for correction |
| **Cost** | 2x compute | 1x compute |
| **Operational** | 2 pipelines to monitor | 1 pipeline |
| **Use Case** | Legacy migration, regulatory | Greenfield, modern stack |

### Recommendation for GCP
> **Kappa on Dataflow** - Single Beam pipeline handles both:
> - **Streaming mode** for real-time
> - **Batch mode** (bounded source) for backfill/reprocessing
> - Same code, same logic, same output

---

## 🎯 Interview Whiteboard Checklist

### Batch Pipeline (Draw in 3 min)
- [ ] GCS source with file patterns
- [ ] Dataflow: Read → Validate → Transform → Write
- [ ] Side input for enrichment
- [ ] Dead letter output to GCS
- [ ] BigQuery: Partition by date, Cluster by (customer_id, region)
- [ ] Composer DAG orchestration

### Streaming Pipeline (Draw in 3 min)
- [ ] Pub/Sub with timestamp attribute
- [ ] Fixed windows (5 min) + Session windows
- [ ] Watermark + Allowed lateness (24hr)
- [ ] Triggers: Early (speculative) + Late (final)
- [ ] Deduplication via GroupByKey
- [ ] Late data side output
- [ ] BigQuery Streaming inserts

### Code You Must Write from Memory (10 min each)
- [ ] `ValidateAndEnrich` DoFn with tagged outputs
- [ ] `DeduplicateEvents` DoFn
- [ ] Windowing configuration with triggers
- [ ] BigQuery WriteToBigQuery with partitioning/clustering

---

## 📝 Related Files
- `code/dataflow_batch_pipeline.py` - Full runnable batch pipeline
- `code/dataflow_streaming_pipeline.py` - Full runnable streaming pipeline
- `notebooks/dataflow_streaming_demo.ipynb` - Interactive streaming demo
- `migration_strategies.md` - Migration pipeline patterns

---

*Last Updated: 2026-01-15 | For: Google Cloud Data & Analytics Lead Technical Screen*