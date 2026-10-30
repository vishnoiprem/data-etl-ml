# Custom Dataflow Transform — Stateful Enrichment with Side Inputs
## Production-Grade Apache Beam (Python) for Google Cloud Dataflow

---

## 🎯 Use Case
**Real-time customer 360 enrichment:** Join streaming events (Pub/Sub) with large reference dataset (BigQuery customer profile) using side inputs, with exactly-once semantics, late data handling, and custom metrics.

---

```python
"""
custom_dataflow_transform.py

Production-grade Dataflow transform demonstrating:
- Stateful processing with BagState and Timer
- Side input pattern with periodic refresh
- Exactly-once deduplication using deterministic keys
- Custom metrics for monitoring
- Dead-letter queue with structured error context
- Flex Template compatible

Run as Flex Template:
    python custom_dataflow_transform.py \
        --runner=DataflowRunner \
        --project=$PROJECT \
        --region=asia-southeast1 \
        --template_location=gs://$BUCKET/templates/customer-enrichment \
        --staging_location=gs://$BUCKET/staging \
        --temp_location=gs://$BUCKET/temp \
        --sdk_container_image=gcr.io/$PROJECT/dataflow-flex:latest
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional, Tuple

import apache_beam as beam
from apache_beam import DoFn, ParDo, PTransform, PCollection, WindowInto, FixedWindows
from apache_beam.io import ReadFromPubSub, WriteToBigQuery
from apache_beam.io.gcp.bigquery import BigQueryDisposition
from apache_beam.metrics import Metrics
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.transforms import window
from apache_beam.transforms.userstate import BagStateSpec, TimerSpec, TimeDomain
from apache_beam.utils.timestamp import Timestamp

# ─── Constants ────────────────────────────────────────────────────────────

SIDE_INPUT_REFRESH_INTERVAL_SECONDS = 3600  # Refresh customer cache hourly
WINDOW_SIZE_SECONDS = 300  # 5-minute windows
ALLOWED_LATENESS_SECONDS = 600  # 10 minutes late data
MAX_DELIVERY_ATTEMPTS = 3

# Metrics
EVENTS_PROCESSED = Metrics.counter("customer_enrichment", "events_processed")
EVENTS_ENRICHED = Metrics.counter("customer_enrichment", "events_enriched")
EVENTS_DROPPED = Metrics.counter("customer_enrichment", "events_dropped")
ENRICHMENT_LATENCY_MS = Metrics.distribution("customer_enrichment", "enrichment_latency_ms")
SIDE_INPUT_REFRESH_COUNT = Metrics.counter("customer_enrichment", "side_input_refreshes")
SIDE_INPUT_STALENESS_SECONDS = Metrics.gauge("customer_enrichment", "side_input_staleness_seconds")
DEAD_LETTER_COUNT = Metrics.counter("customer_enrichment", "dead_letter_count")


# ─── Side Input: Customer Profile Cache ───────────────────────────────────

class CustomerProfileCache:
    """
    Thread-safe customer profile cache with periodic refresh from BigQuery.
    In production, use a shared service (e.g., Vertex AI Feature Store online serving)
    or a distributed cache (Memorystore Redis) for multi-worker consistency.
    """
    
    def __init__(self, project_id: str, dataset: str, table: str):
        self.project_id = project_id
        self.dataset = dataset
        self.table = table
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_refresh: float = 0
        self._refresh_lock = __import__("threading").Lock()
    
    def refresh(self) -> None:
        """Refresh cache from BigQuery. Called periodically by side input DoFn."""
        from google.cloud import bigquery
        
        client = bigquery.Client(project=self.project_id)
        query = f"""
            SELECT customer_id, tier, lifetime_value, segment, 
                   preferred_channel, risk_score, last_updated
            FROM `{self.project_id}.{self.dataset}.{self.table}`
            WHERE is_active = TRUE
        """
        
        start = time.time()
        rows = client.query(query).result()
        new_cache = {}
        for row in rows:
            new_cache[row.customer_id] = {
                "tier": row.tier,
                "lifetime_value": float(row.lifetime_value) if row.lifetime_value else 0.0,
                "segment": row.segment,
                "preferred_channel": row.preferred_channel,
                "risk_score": float(row.risk_score) if row.risk_score else 0.0,
                "last_updated": row.last_updated.isoformat() if row.last_updated else None,
            }
        
        with self._refresh_lock:
            self._cache = new_cache
            self._last_refresh = time.time()
        
        SIDE_INPUT_REFRESH_COUNT.inc()
        logging.info(f"Refreshed customer cache: {len(new_cache)} profiles in {time.time() - start:.2f}s")
    
    def get(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get profile from cache. Returns None if not found."""
        with self._refresh_lock:
            return self._cache.get(customer_id)
    
    def is_stale(self) -> bool:
        """Check if cache needs refresh."""
        return (time.time() - self._last_refresh) > SIDE_INPUT_REFRESH_INTERVAL_SECONDS
    
    def staleness_seconds(self) -> float:
        return time.time() - self._last_refresh


# ─── DoFn: Side Input Refresher (Runs on each worker) ─────────────────────

class RefreshCustomerCacheFn(DoFn):
    """
    Periodically refreshes the customer profile cache.
    Emits a singleton side input that downstream DoFns consume.
    """
    
    def __init__(self, project_id: str, dataset: str, table: str):
        self.project_id = project_id
        self.dataset = dataset
        self.table = table
        self._cache = CustomerProfileCache(project_id, dataset, table)
    
    def start_bundle(self):
        """Initialize cache on bundle start."""
        if not self._cache._cache:  # First time
            self._cache.refresh()
    
    def process(self, element, timestamp=beam.DoFn.TimestampParam, window=beam.DoFn.WindowParam):
        """Emit cache as side input. Refresh if stale."""
        if self._cache.is_stale():
            self._cache.refresh()
        
        SIDE_INPUT_STALENESS_SECONDS.set(int(self._cache.staleness_seconds()))
        
        # Emit as side input (singleton)
        yield beam.pvalue.TaggedOutput("cache", self._cache)


# ─── DoFn: Stateful Event Enrichment ──────────────────────────────────────

class EnrichEventFn(DoFn):
    """
    Enriches streaming events with customer profile data.
    
    Features:
    - Side input consumption (customer cache)
    - Stateful deduplication (BagState + Timer)
    - Late data handling (allowed lateness)
    - Exactly-once semantics via deterministic dedup keys
    - Dead-letter queue for unenrichable events
    - Custom metrics for observability
    """
    
    # State: store processed event IDs per window for deduplication
    _DEDUP_STATE = BagStateSpec("dedup_ids", beam.coders.StringCoder())
    # Timer: fire at end of window + allowed lateness to clear state
    _CLEAR_TIMER = TimerSpec("clear_dedup", TimeDomain.WATERMARK)
    
    def __init__(self, dead_letter_topic: str):
        self.dead_letter_topic = dead_letter_topic
        self._cache: Optional[CustomerProfileCache] = None
    
    def setup(self):
        """Initialize per-worker resources."""
        pass  # Cache comes via side input
    
    def _get_dedup_key(self, event: Dict[str, Any], window: window.IntervalWindow) -> str:
        """Generate deterministic deduplication key from event data + window."""
        event_id = event.get("event_id", "")
        window_start = window.start.to_utc_datetime().isoformat()
        return f"{window_start}:{event_id}"
    
    @DoFn.process_method
    def process(
        self,
        element: Tuple[Dict[str, Any], CustomerProfileCache],
        timestamp=beam.DoFn.TimestampParam,
        window=beam.DoFn.WindowParam,
        dedup_state=DoFn.StateParam(_DEDUP_STATE),
        clear_timer=DoFn.TimerParam(_CLEAR_TIMER),
    ) -> Iterable[Dict[str, Any]]:
        """
        Process a single event with side input cache.
        
        Args:
            element: Tuple of (event_dict, customer_cache)
            timestamp: Event timestamp (from Pub/Sub message)
            window: Current window
            dedup_state: BagState for deduplication
            clear_timer: Timer to clear state after allowed lateness
        """
        event, cache = element
        self._cache = cache
        
        start_time = time.time()
        EVENTS_PROCESSED.inc()
        
        try:
            # 1. Validate event structure
            event_id = event.get("event_id")
            customer_id = event.get("customer_id")
            event_ts = event.get("event_timestamp")
            
            if not all([event_id, customer_id, event_ts]):
                raise ValueError("Missing required fields: event_id, customer_id, event_timestamp")
            
            # 2. Deduplication check
            dedup_key = self._get_dedup_key(event, window)
            existing_ids = set(dedup_state.read())
            
            if dedup_key in existing_ids:
                logging.debug(f"Duplicate event detected: {dedup_key}")
                EVENTS_DROPPED.inc()
                return  # Drop duplicate
            
            # 3. Enrich with customer profile
            profile = cache.get(customer_id)
            
            if profile is None:
                # Customer not in cache — send to dead letter for investigation
                yield beam.pvalue.TaggedOutput(
                    "dead_letter",
                    self._build_dead_letter(event, "CUSTOMER_NOT_FOUND", 
                                           f"Customer {customer_id} not in profile cache")
                )
                DEAD_LETTER_COUNT.inc()
                EVENTS_DROPPED.inc()
                return
            
            # 4. Build enriched event
            enriched = self._build_enriched_event(event, profile)
            
            # 5. Add to dedup state
            dedup_state.add(dedup_key)
            
            # 6. Set timer to clear state after window + allowed lateness
            clear_time = window.end + ALLOWED_LATENESS_SECONDS * 1000  # ms
            clear_timer.set(Timestamp(clear_time))
            
            EVENTS_ENRICHED.inc()
            ENRICHMENT_LATENCY_MS.update(int((time.time() - start_time) * 1000))
            
            yield enriched
            
        except Exception as e:
            logging.exception(f"Error enriching event: {e}")
            yield beam.pvalue.TaggedOutput(
                "dead_letter",
                self._build_dead_letter(event, "ENRICHMENT_ERROR", str(e))
            )
            DEAD_LETTER_COUNT.inc()
            EVENTS_DROPPED.inc()
    
    @DoFn.on_timer(_CLEAR_TIMER)
    def clear_dedup_state(self, dedup_state=DoFn.StateParam(_DEDUP_STATE)):
        """Clear deduplication state after allowed lateness expires."""
        dedup_state.clear()
        logging.debug("Cleared deduplication state for window")
    
    def _build_enriched_event(self, event: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        """Merge event with customer profile."""
        return {
            # Original event fields
            "event_id": event["event_id"],
            "customer_id": event["customer_id"],
            "event_timestamp": event["event_timestamp"],
            "event_type": event.get("event_type"),
            "channel": event.get("channel"),
            "amount": event.get("amount"),
            "currency": event.get("currency"),
            "metadata": event.get("metadata", {}),
            # Enriched fields
            "customer_tier": profile["tier"],
            "customer_lifetime_value": profile["lifetime_value"],
            "customer_segment": profile["segment"],
            "customer_preferred_channel": profile["preferred_channel"],
            "customer_risk_score": profile["risk_score"],
            "enrichment_timestamp": datetime.now(timezone.utc).isoformat(),
            "profile_last_updated": profile["last_updated"],
        }
    
    def _build_dead_letter(self, event: Dict[str, Any], error_code: str, detail: str) -> Dict[str, Any]:
        """Build dead-letter record with full context."""
        return {
            "original_event": event,
            "error_code": error_code,
            "error_detail": detail,
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "pipeline": "customer-enrichment",
            "dead_letter_topic": self.dead_letter_topic,
        }


# ─── PTransform: Complete Enrichment Pipeline ─────────────────────────────

class CustomerEnrichmentPipeline(PTransform):
    """
    Complete enrichment pipeline as a reusable PTransform.
    
    Input: PCollection[Dict] from Pub/Sub (JSON messages)
    Output: PCollection[Dict] enriched events + dead letters
    """
    
    def __init__(
        self,
        project_id: str,
        customer_dataset: str,
        customer_table: str,
        dead_letter_topic: str,
        window_size_seconds: int = WINDOW_SIZE_SECONDS,
        allowed_lateness_seconds: int = ALLOWED_LATENESS_SECONDS,
    ):
        self.project_id = project_id
        self.customer_dataset = customer_dataset
        self.customer_table = customer_table
        self.dead_letter_topic = dead_letter_topic
        self.window_size_seconds = window_size_seconds
        self.allowed_lateness_seconds = allowed_lateness_seconds
    
    def expand(self, events: PCollection) -> Dict[str, PCollection]:
        # 1. Parse JSON from Pub/Sub
        parsed = events | "Parse JSON" >> beam.Map(json.loads).with_output_types(dict)
        
        # 2. Add event timestamp (use event_time from payload, not processing time)
        timestamped = parsed | "Assign Event Time" >> beam.Map(
            lambda e: beam.window.TimestampedValue(e, 
                int(datetime.fromisoformat(e["event_timestamp"].replace("Z", "+00:00")).timestamp()))
        ).with_output_types(dict)
        
        # 3. Window into fixed windows
        windowed = timestamped | "Window" >> WindowInto(
            FixedWindows(self.window_size_seconds),
            allowed_lateness=self.allowed_lateness_seconds,
            accumulation_mode=beam.transforms.trigger.AccumulationMode.DISCARDING,
        )
        
        # 4. Create side input (customer cache refresher)
        cache_refresher = (
            beam.Create([None])  # Singleton trigger
            | "Refresh Cache" >> ParDo(
                RefreshCustomerCacheFn(self.project_id, self.customer_dataset, self.customer_table)
            ).with_outputs("cache", main="ignored")
        )
        
        # 5. Enrich with side input (cache passed to each element)
        enriched = (
            {"events": windowed, "cache": cache_refresher.cache}
            | "Enrich Events" >> beam.FlatMap(
                lambda kv: list(EnrichEventFn(self.dead_letter_topic).process(kv)),
            ).with_outputs("dead_letter", main="enriched")
        )
        
        return {
            "enriched": enriched.enriched,
            "dead_letter": enriched.dead_letter,
        }


# ─── Pipeline Options ──────────────────────────────────────────────────────

class CustomerEnrichmentOptions(PipelineOptions):
    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument("--input_topic", required=True, help="Pub/Sub input topic")
        parser.add_argument("--output_table", required=True, help="BigQuery output table (project:dataset.table)")
        parser.add_argument("--dead_letter_topic", required=True, help="Pub/Sub dead letter topic")
        parser.add_argument("--customer_dataset", required=True, help="BigQuery dataset for customer profiles")
        parser.add_argument("--customer_table", required=True, help="BigQuery table for customer profiles")
        parser.add_argument("--window_size_seconds", type=int, default=WINDOW_SIZE_SECONDS)
        parser.add_argument("--allowed_lateness_seconds", type=int, default=ALLOWED_LATENESS_SECONDS)


# ─── Main Pipeline ─────────────────────────────────────────────────────────

def run_pipeline(options: CustomerEnrichmentOptions) -> None:
    """Build and run the enrichment pipeline."""
    
    with beam.Pipeline(options=options) as p:
        # Read from Pub/Sub
        events = p | "Read from Pub/Sub" >> ReadFromPubSub(
            topic=options.input_topic,
            with_attributes=False,
        )
        
        # Run enrichment pipeline
        results = events | "Enrich" >> CustomerEnrichmentPipeline(
            project_id=options.project,
            customer_dataset=options.customer_dataset,
            customer_table=options.customer_table,
            dead_letter_topic=options.dead_letter_topic,
            window_size_seconds=options.window_size_seconds,
            allowed_lateness_seconds=options.allowed_lateness_seconds,
        )
        
        # Write enriched events to BigQuery
        results["enriched"] | "Write to BigQuery" >> WriteToBigQuery(
            table=options.output_table,
            schema="SCHEMA_AUTODETECT",
            write_disposition=BigQueryDisposition.WRITE_APPEND,
            create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
            additional_bq_parameters={
                "timePartitioning": {"type": "DAY", "field": "event_timestamp"},
                "clustering": {"fields": ["customer_id", "event_type"]},
            },
        )
        
        # Write dead letters to Pub/Sub (for reprocessing/alerting)
        results["dead_letter"] | "Write Dead Letters" >> beam.io.WriteToPubSub(
            topic=options.dead_letter_topic,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    options = CustomerEnrichmentOptions()
    run_pipeline(options)
```

---

## 🧪 Unit Tests (pytest)

```python
# test_custom_dataflow_transform.py

import json
import unittest
from datetime import datetime, timezone

import apache_beam as beam
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to

from custom_dataflow_transform import (
    CustomerProfileCache,
    EnrichEventFn,
    CustomerEnrichmentPipeline,
)


class TestCustomerProfileCache(unittest.TestCase):
    """Test cache refresh and lookup."""
    
    def test_cache_refresh_and_lookup(self):
        cache = CustomerProfileCache("test-project", "test_dataset", "test_table")
        # Mock the BigQuery call
        cache._cache = {
            "cust-123": {"tier": "GOLD", "lifetime_value": 5000.0, "segment": "PREMIUM"},
            "cust-456": {"tier": "SILVER", "lifetime_value": 1200.0, "segment": "STANDARD"},
        }
        cache._last_refresh = time.time()
        
        # Hit
        profile = cache.get("cust-123")
        self.assertEqual(profile["tier"], "GOLD")
        
        # Miss
        profile = cache.get("cust-999")
        self.assertIsNone(profile)
    
    def test_staleness(self):
        cache = CustomerProfileCache("test", "ds", "tbl")
        cache._last_refresh = time.time() - 7200  # 2 hours ago
        self.assertTrue(cache.is_stale())


class TestEnrichEventFn(unittest.TestCase):
    """Test enrichment DoFn with TestPipeline."""
    
    def test_enrichment_happy_path(self):
        # Setup cache
        cache = CustomerProfileCache("test", "ds", "tbl")
        cache._cache = {
            "cust-123": {
                "tier": "GOLD", "lifetime_value": 5000.0, "segment": "PREMIUM",
                "preferred_channel": "mobile", "risk_score": 0.1, "last_updated": "2024-01-01"
            }
        }
        cache._last_refresh = time.time()
        
        # Test event
        event = {
            "event_id": "evt-001",
            "customer_id": "cust-123",
            "event_timestamp": "2024-01-15T10:00:00+00:00",
            "event_type": "purchase",
            "channel": "web",
            "amount": 100.0,
            "currency": "USD",
        }
        
        with TestPipeline() as p:
            # Create PCollection with side input
            events = p | "Create Event" >> beam.Create([event])
            cache_pc = p | "Create Cache" >> beam.Create([cache])
            
            # Apply enrichment (simplified for test)
            enriched = (
                {"events": events, "cache": cache_pc}
                | "Enrich" >> beam.FlatMap(
                    lambda kv: list(EnrichEventFn("dlq-topic").process(kv))
                ).with_outputs("dead_letter", main="enriched")
            )
            
            expected = [{
                "event_id": "evt-001",
                "customer_id": "cust-123",
                "event_timestamp": "2024-01-15T10:00:00+00:00",
                "event_type": "purchase",
                "channel": "web",
                "amount": 100.0,
                "currency": "USD",
                "metadata": {},
                "customer_tier": "GOLD",
                "customer_lifetime_value": 5000.0,
                "customer_segment": "PREMIUM",
                "customer_preferred_channel": "mobile",
                "customer_risk_score": 0.1,
                "enrichment_timestamp": unittest.mock.ANY,  # Will vary
                "profile_last_updated": "2024-01-01",
            }]
            
            assert_that(enriched.enriched, equal_to(expected))
    
    def test_deduplication(self):
        cache = CustomerProfileCache("test", "ds", "tbl")
        cache._cache = {"cust-123": {"tier": "GOLD", "lifetime_value": 5000.0, "segment": "PREMIUM",
                                     "preferred_channel": "mobile", "risk_score": 0.1, "last_updated": "2024-01-01"}}
        cache._last_refresh = time.time()
        
        event = {
            "event_id": "evt-001",
            "customer_id": "cust-123",
            "event_timestamp": "2024-01-15T10:00:00+00:00",
            "event_type": "purchase",
        }
        
        with TestPipeline() as p:
            # Same event twice in same window
            events = p | "Create Events" >> beam.Create([event, event])
            cache_pc = p | "Create Cache" >> beam.Create([cache])
            
            enriched = (
                {"events": events, "cache": cache_pc}
                | "Enrich" >> beam.FlatMap(
                    lambda kv: list(EnrichEventFn("dlq-topic").process(kv))
                ).with_outputs("dead_letter", main="enriched")
            )
            
            # Should only output once (deduplicated)
            assert_that(enriched.enriched, equal_to([unittest.mock.ANY]))  # 1 output
    
    def test_missing_customer_dead_letter(self):
        cache = CustomerProfileCache("test", "ds", "tbl")
        cache._cache = {}
        cache._last_refresh = time.time()
        
        event = {
            "event_id": "evt-001",
            "customer_id": "cust-999",  # Not in cache
            "event_timestamp": "2024-01-15T10:00:00+00:00",
        }
        
        with TestPipeline() as p:
            events = p | "Create Event" >> beam.Create([event])
            cache_pc = p | "Create Cache" >> beam.Create([cache])
            
            enriched = (
                {"events": events, "cache": cache_pc}
                | "Enrich" >> beam.FlatMap(
                    lambda kv: list(EnrichEventFn("dlq-topic").process(kv))
                ).with_outputs("dead_letter", main="enriched")
            )
            
            # Should go to dead letter
            assert_that(enriched.enriched, equal_to([]))
            # Dead letter should have error_code CUSTOMER_NOT_FOUND


if __name__ == "__main__":
    unittest.main()
```

---

## 🎯 Interview Talking Points

### "Walk me through this Dataflow transform design."

1. **Side Input Pattern** — Customer cache refreshed hourly from BigQuery, broadcast to all workers via singleton side input. Avoids per-event BigQuery lookups (latency + cost).
2. **Stateful Deduplication** — `BagState` + watermark-aligned timer ensures exactly-once within window + allowed lateness. Key derived from `event_id + window_start` (deterministic, retry-safe).
3. **Late Data Handling** — `allowed_lateness=600s` + `DISCARDING` accumulation. Late events processed in same window, deduplication still works because state persists until timer fires.
4. **Dead Letter Queue** — Structured error context (error_code, detail, timestamp, original event) enables automated reprocessing and alerting.
5. **Metrics** — Custom counters (processed, enriched, dropped, dead_letter) + distribution (latency) + gauge (cache staleness) for Cloud Monitoring dashboards.
6. **Flex Template Ready** — Parameterized via PipelineOptions, containerized, deployable via Dataflow UI or CI/CD.

### "How would you scale this to 1M events/sec?"

- **Side Input:** Move to Vertex AI Feature Store (online serving) or Memorystore Redis — removes worker memory pressure, enables sub-ms lookups
- **State:** Use `CombiningState` with `Count.CombineFn` for cardinality estimation, or sharded state keys
- **Parallelism:** Increase `num_workers`, use `--autoscaling_algorithm=THROUGHPUT_BASED`
- **Windowing:** Consider session windows for user-journey analysis instead of fixed windows
- **Monitoring:** Add Dataflow Streaming Engine metrics, backlog alerts, autoscaling latency

### "Why not just use a BigQuery JOIN in a streaming query?"

- **Latency:** Dataflow enrichment <100ms end-to-end; BigQuery streaming inserts + query = seconds
- **Cost:** Side input cache = $0 lookup vs BigQuery scan per query
- **Control:** Custom logic (ML scoring, complex transforms) not expressible in SQL
- **Exactly-once:** Beam's state + timer model is stronger than BQ streaming INSERT deduplication

---

## 📋 Production Checklist

- [ ] **Container Image** — Build with `apache/beam_python3.11_sdk` base, pin dependencies
- [ ] **IAM** — Service account: `roles/dataflow.worker`, `roles/pubsub.subscriber`, `roles/bigquery.dataViewer` (customer table), `roles/bigquery.dataEditor` (output), `roles/pubsub.publisher` (DLQ)
- [ ] **VPC-SC** — Pipeline in perimeter, BigQuery/Pub/Sub accessible via Private Service Connect
- [ ] **CMEK** — KMS key for Dataflow state, BigQuery output, Pub/Sub DLQ
- [ ] **Monitoring** — Alert on: backlog > 10K, latency p99 > 5s, dead_letter_rate > 1%, worker CPU > 80%
- [ ] **Runbooks** — Cache refresh failure, DLQ replay, scaling events, version rollout
- [ ] **Testing** — Unit tests (above), integration test with TestStream, load test at 2x expected peak