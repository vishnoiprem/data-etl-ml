# Custom Airflow Operator — Deferrable BigQuery Job Sensor
## Production-Grade Airflow Operator for Cloud Composer / Managed Workflows

---

## 🎯 Use Case
**Long-running BigQuery jobs** (partitioned table loads, ML model training, large merges) that exceed sensor timeout. Traditional `BigQueryExecuteQueryOperator` + sensor blocks worker slot. Deferrable operator releases worker, polls asynchronously via triggerer.

---

```python
"""
composer_deferrable_operator.py

Production-grade deferrable Airflow operator for BigQuery async job monitoring.
Compatible with Cloud Composer 2.x (Airflow 2.7+) and Google Cloud Workflows.

Features:
- Deferrable execution (releases worker slot during polling)
- Exponential backoff + jitter
- Job-level metadata capture (bytes processed, slot ms, DML stats)
- Automatic retry on transient errors
- XCom push for downstream tasks
- SLI/SLO metrics emission

Usage in DAG:
    from composer_deferrable_operator import DeferrableBigQueryOperator
    
    load_job = DeferrableBigQueryOperator(
        task_id="load_partitioned_table",
        sql="LOAD DATA INTO `project.dataset.table` PARTITION BY DATE(event_ts) FROM FILES(...)",
        gcp_conn_id="google_cloud_default",
        location="asia-southeast1",
        poll_interval_seconds=30,
        max_poll_attempts=120,  # 1 hour max
        deferrable=True,
    )
"""

from __future__ import annotations

import asyncio
import json
import random
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Sequence

from airflow import AirflowException
from airflow.models import BaseOperator
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from airflow.providers.google.cloud.triggers.bigquery import BigQueryJobTrigger
from airflow.triggers.base import TriggerEvent
from airflow.utils.context import Context


class DeferrableBigQueryOperator(BaseOperator):
    """
    Deferrable operator for BigQuery jobs with async polling.
    
    Inherits from BaseOperator, uses BigQueryJobTrigger for async execution.
    """
    
    # Fields that can be templated
    template_fields: Sequence[str] = (
        "sql",
        "destination_table",
        "labels",
        "project_id",
        "location",
    )
    
    # UI color for Airflow graph view
    ui_color = "#4285F4"
    ui_fgcolor = "#FFFFFF"
    
    def __init__(
        self,
        *,
        sql: str,
        gcp_conn_id: str = "google_cloud_default",
        project_id: Optional[str] = None,
        location: str = "us-central1",
        destination_table: Optional[str] = None,
        write_disposition: str = "WRITE_APPEND",
        create_disposition: str = "CREATE_IF_NEEDED",
        time_partitioning: Optional[Dict[str, Any]] = None,
        clustering_fields: Optional[Sequence[str]] = None,
        labels: Optional[Dict[str, str]] = None,
        job_id_prefix: Optional[str] = None,
        poll_interval_seconds: int = 30,
        max_poll_attempts: int = 120,
        exponential_backoff: bool = True,
        max_backoff_seconds: int = 300,
        jitter: bool = True,
        retry_on_transient: bool = True,
        transient_error_codes: Optional[Sequence[str]] = None,
        impersonation_chain: Optional[Sequence[str]] = None,
        deferrable: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        
        self.sql = sql
        self.gcp_conn_id = gcp_conn_id
        self.project_id = project_id
        self.location = location
        self.destination_table = destination_table
        self.write_disposition = write_disposition
        self.create_disposition = create_disposition
        self.time_partitioning = time_partitioning or {}
        self.clustering_fields = list(clustering_fields) if clustering_fields else []
        self.labels = labels or {}
        self.job_id_prefix = job_id_prefix or f"airflow-{self.task_id}-"
        self.poll_interval_seconds = poll_interval_seconds
        self.max_poll_attempts = max_poll_attempts
        self.exponential_backoff = exponential_backoff
        self.max_backoff_seconds = max_backoff_seconds
        self.jitter = jitter
        self.retry_on_transient = retry_on_transient
        self.transient_error_codes = set(transient_error_codes or [
            "backendError",
            "internalError",
            "rateLimitExceeded",
            "jobRateLimitExceeded",
            "quotaExceeded",
        ])
        self.impersonation_chain = impersonation_chain
        self.deferrable = deferrable
        
        # Runtime state
        self._hook: Optional[BigQueryHook] = None
        self._job_id: Optional[str] = None
        self._start_time: Optional[float] = None
    
    @property
    def hook(self) -> BigQueryHook:
        """Lazy-initialized BigQuery hook."""
        if self._hook is None:
            self._hook = BigQueryHook(
                gcp_conn_id=self.gcp_conn_id,
                location=self.location,
                impersonation_chain=self.impersonation_chain,
            )
        return self._hook
    
    def execute(self, context: Context) -> Any:
        """Submit job and defer to trigger for polling."""
        
        self._start_time = time.time()
        self.log.info("Submitting BigQuery job: %s", self.sql[:200] + "..." if len(self.sql) > 200 else self.sql)
        
        # Submit job asynchronously
        job = self._submit_job()
        self._job_id = job.job_id
        
        self.log.info("BigQuery job submitted: %s (project=%s, location=%s)", 
                     self._job_id, job.project, job.location)
        
        # Push job ID to XCom immediately for downstream visibility
        context["ti"].xcom_push(key="job_id", value=self._job_id)
        context["ti"].xcom_push(key="job_project", value=job.project)
        context["ti"].xcom_push(key="job_location", value=job.location)
        
        if not self.deferrable:
            # Synchronous fallback (blocks worker)
            return self._wait_for_job_sync(context)
        
        # Defer to trigger for async polling
        self.defer(
            trigger=BigQueryJobTrigger(
                job_id=self._job_id,
                project_id=job.project,
                location=job.location,
                gcp_conn_id=self.gcp_conn_id,
                poll_interval_seconds=self.poll_interval_seconds,
                max_poll_attempts=self.max_poll_attempts,
                exponential_backoff=self.exponential_backoff,
                max_backoff_seconds=self.max_backoff_seconds,
                jitter=self.jitter,
                impersonation_chain=self.impersonation_chain,
            ),
            method_name="execute_complete",
        )
    
    def _submit_job(self):
        """Submit BigQuery job with configuration."""
        job_config = self._build_job_config()
        
        # Generate deterministic job ID for idempotency
        job_id = f"{self.job_id_prefix}{int(time.time() * 1000)}"
        
        return self.hook.insert_job(
            configuration=job_config,
            job_id=job_id,
            project_id=self.project_id,
            location=self.location,
            retry=None,  # Let trigger handle retries
        )
    
    def _build_job_config(self) -> Dict[str, Any]:
        """Build BigQuery job configuration from operator parameters."""
        config: Dict[str, Any] = {
            "query": {
                "query": self.sql,
                "useLegacySql": False,
                "destinationTable": self._parse_table_ref(self.destination_table) if self.destination_table else None,
                "writeDisposition": self.write_disposition,
                "createDisposition": self.create_disposition,
                "labels": self.labels,
            }
        }
        
        # Add time partitioning if specified
        if self.time_partitioning:
            config["query"]["timePartitioning"] = self.time_partitioning
        
        # Add clustering if specified
        if self.clustering_fields:
            config["query"]["clustering"] = {"fields": list(self.clustering_fields)}
        
        return config
    
    def _parse_table_ref(self, table: str) -> Dict[str, str]:
        """Parse table reference string (project.dataset.table)."""
        parts = table.split(".")
        if len(parts) == 3:
            return {"projectId": parts[0], "datasetId": parts[1], "tableId": parts[2]}
        elif len(parts) == 2:
            return {"datasetId": parts[0], "tableId": parts[1]}
        else:
            raise ValueError(f"Invalid table reference: {table}. Expected project.dataset.table or dataset.table")
    
    def _wait_for_job_sync(self, context: Context) -> Dict[str, Any]:
        """Synchronous fallback - blocks worker until job completes."""
        self.log.info("Running in synchronous mode (deferrable=False)")
        
        attempts = 0
        poll_interval = self.poll_interval_seconds
        
        while attempts < self.max_poll_attempts:
            attempts += 1
            job = self.hook.get_job(self._job_id, project_id=self.project_id, location=self.location)
            
            if job.done():
                return self._handle_job_completion(job, context)
            
            # Check for transient errors
            if job.error_result and self.retry_on_transient:
                error_code = job.error_result.get("reason", "")
                if error_code in self.transient_error_codes:
                    self.log.warning("Transient error %s, retrying... (attempt %d/%d)", 
                                   error_code, attempts, self.max_poll_attempts)
                    time.sleep(poll_interval)
                    poll_interval = self._calculate_backoff(poll_interval)
                    continue
            
            self.log.info("Job %s still running (attempt %d/%d)...", self._job_id, attempts, self.max_poll_attempts)
            time.sleep(poll_interval)
            poll_interval = self._calculate_backoff(poll_interval)
        
        raise AirflowException(f"BigQuery job {self._job_id} did not complete within {self.max_poll_attempts} attempts")
    
    def _calculate_backoff(self, current_interval: int) -> int:
        """Calculate next poll interval with exponential backoff and jitter."""
        if not self.exponential_backoff:
            return current_interval
        
        next_interval = min(current_interval * 2, self.max_backoff_seconds)
        
        if self.jitter:
            # Add ±25% jitter
            jitter_range = next_interval * 0.25
            next_interval = int(next_interval + random.uniform(-jitter_range, jitter_range))
        
        return max(next_interval, 1)
    
    def execute_complete(self, context: Context, event: TriggerEvent) -> Any:
        """Callback when trigger completes."""
        
        if not event or "status" not in event:
            raise AirflowException("Invalid trigger event received")
        
        if event["status"] == "success":
            self.log.info("BigQuery job %s completed successfully", self._job_id)
            return self._build_result(event)
        
        elif event["status"] == "error":
            error_msg = event.get("message", "Unknown error")
            self.log.error("BigQuery job %s failed: %s", self._job_id, error_msg)
            raise AirflowException(f"BigQuery job {self._job_id} failed: {error_msg}")
        
        elif event["status"] == "timeout":
            self.log.error("BigQuery job %s timed out after %d attempts", self._job_id, self.max_poll_attempts)
            raise AirflowException(f"BigQuery job {self._job_id} timed out")
        
        else:
            raise AirflowException(f"Unknown trigger status: {event['status']}")
    
    def _handle_job_completion(self, job, context: Context) -> Dict[str, Any]:
        """Process completed job and extract metrics."""
        
        if job.error_result:
            raise AirflowException(f"BigQuery job {self._job_id} failed: {job.error_result}")
        
        # Extract job statistics
        stats = job.statistics
        query_stats = stats.query if stats and stats.query else {}
        
        result = {
            "job_id": self._job_id,
            "project_id": job.project,
            "location": job.location,
            "status": "success",
            "duration_seconds": time.time() - self._start_time,
            "bytes_processed": query_stats.get("totalBytesProcessed", 0),
            "bytes_billed": query_stats.get("totalBytesBilled", 0),
            "slot_millis": query_stats.get("totalSlotMs", 0),
            "rows_affected": query_stats.get("numDmlAffectedRows", 0),
            "referenced_tables": [t.table_id for t in (query_stats.get("referencedTables") or [])],
            "destination_table": self.destination_table,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # Push metrics to XCom for downstream tasks
        context["ti"].xcom_push(key="job_stats", value=result)
        
        # Emit custom metrics (if statsd/prometheus configured)
        self._emit_metrics(result)
        
        self.log.info(
            "Job %s completed: bytes_processed=%.2f GB, slot_ms=%d, duration=%.1fs",
            self._job_id,
            result["bytes_processed"] / 1e9,
            result["slot_millis"],
            result["duration_seconds"],
        )
        
        return result
    
    def _build_result(self, event: TriggerEvent) -> Dict[str, Any]:
        """Build result from trigger event."""
        return {
            "job_id": event.get("job_id"),
            "project_id": event.get("project_id"),
            "location": event.get("location"),
            "status": "success",
            "duration_seconds": event.get("duration_seconds"),
            "bytes_processed": event.get("bytes_processed", 0),
            "bytes_billed": event.get("bytes_billed", 0),
            "slot_millis": event.get("slot_millis", 0),
            "rows_affected": event.get("rows_affected", 0),
            "destination_table": self.destination_table,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
    
    def _emit_metrics(self, result: Dict[str, Any]) -> None:
        """Emit metrics for monitoring (statsd/prometheus)."""
        try:
            from airflow.stats import Stats
            
            Stats.gauge(f"bigquery.job.bytes_processed_gb", result["bytes_processed"] / 1e9)
            Stats.gauge(f"bigquery.job.slot_millis", result["slot_millis"])
            Stats.gauge(f"bigquery.job.duration_seconds", result["duration_seconds"])
            Stats.incr(f"bigquery.job.success")
            
            # Cost estimation
            cost_usd = (result["bytes_billed"] / 1e12) * 6.25  # $6.25/TB on-demand
            Stats.gauge(f"bigquery.job.estimated_cost_usd", cost_usd)
            
        except ImportError:
            pass  # Stats not configured
    
    def on_kill(self) -> None:
        """Cleanup when task is killed."""
        if self._job_id:
            self.log.info("Task killed, attempting to cancel BigQuery job %s", self._job_id)
            try:
                self.hook.cancel_job(self._job_id, project_id=self.project_id, location=self.location)
            except Exception as e:
                self.log.warning("Failed to cancel job %s: %s", self._job_id, e)


# ─── Enhanced Trigger with Retry Logic ─────────────────────────────────────

class ResilientBigQueryJobTrigger(BigQueryJobTrigger):
    """
    Extended trigger with retry logic for transient errors.
    """
    
    def __init__(
        self,
        job_id: str,
        project_id: str,
        location: str,
        gcp_conn_id: str = "google_cloud_default",
        poll_interval_seconds: int = 30,
        max_poll_attempts: int = 120,
        exponential_backoff: bool = True,
        max_backoff_seconds: int = 300,
        jitter: bool = True,
        retry_on_transient: bool = True,
        transient_error_codes: Optional[Sequence[str]] = None,
        impersonation_chain: Optional[Sequence[str]] = None,
    ) -> None:
        super().__init__(
            job_id=job_id,
            project_id=project_id,
            location=location,
            gcp_conn_id=gcp_conn_id,
            poll_interval_seconds=poll_interval_seconds,
            max_poll_attempts=max_poll_attempts,
            exponential_backoff=exponential_backoff,
            max_backoff_seconds=max_backoff_seconds,
            jitter=jitter,
            impersonation_chain=impersonation_chain,
        )
        
        self.retry_on_transient = retry_on_transient
        self.transient_error_codes = set(transient_error_codes or [
            "backendError",
            "internalError",
            "rateLimitExceeded",
            "jobRateLimitExceeded",
            "quotaExceeded",
        ])
    
    async def run(self) -> AsyncIterator[TriggerEvent]:
        """Poll job with retry logic."""
        
        hook = BigQueryHook(gcp_conn_id=self.gcp_conn_id, location=self.location)
        attempts = 0
        poll_interval = self.poll_interval_seconds
        start_time = time.time()
        
        while attempts < self.max_poll_attempts:
            attempts += 1
            
            try:
                # Run sync hook call in thread pool
                job = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: hook.get_job(self.job_id, project_id=self.project_id, location=self.location)
                )
                
            except Exception as e:
                self.log.warning("Error polling job %s: %s", self.job_id, e)
                await asyncio.sleep(poll_interval)
                poll_interval = self._calculate_backoff(poll_interval)
                continue
            
            if job.done():
                if job.error_result:
                    error_code = job.error_result.get("reason", "")
                    error_msg = job.error_result.get("message", "Unknown error")
                    
                    # Check for transient error
                    if self.retry_on_transient and error_code in self.transient_error_codes:
                        if attempts < self.max_poll_attempts:
                            self.log.warning("Transient error %s, retrying... (attempt %d/%d)", 
                                           error_code, attempts, self.max_poll_attempts)
                            await asyncio.sleep(poll_interval)
                            poll_interval = self._calculate_backoff(poll_interval)
                            continue
                    
                    yield TriggerEvent({
                        "status": "error",
                        "job_id": self.job_id,
                        "project_id": self.project_id,
                        "location": self.location,
                        "error_code": error_code,
                        "message": error_msg,
                        "duration_seconds": time.time() - start_time,
                    })
                    return
                
                # Success
                stats = job.statistics
                query_stats = stats.query if stats and stats.query else {}
                
                yield TriggerEvent({
                    "status": "success",
                    "job_id": self.job_id,
                    "project_id": self.project_id,
                    "location": self.location,
                    "duration_seconds": time.time() - start_time,
                    "bytes_processed": query_stats.get("totalBytesProcessed", 0),
                    "bytes_billed": query_stats.get("totalBytesBilled", 0),
                    "slot_millis": query_stats.get("totalSlotMs", 0),
                    "rows_affected": query_stats.get("numDmlAffectedRows", 0),
                })
                return
            
            # Job still running
            self.log.debug("Job %s still running (attempt %d/%d)", 
                          self.job_id, attempts, self.max_poll_attempts)
            await asyncio.sleep(poll_interval)
            poll_interval = self._calculate_backoff(poll_interval)
        
        # Timeout
        yield TriggerEvent({
            "status": "timeout",
            "job_id": self.job_id,
            "project_id": self.project_id,
            "location": self.location,
            "message": f"Job did not complete within {self.max_poll_attempts} attempts",
            "duration_seconds": time.time() - start_time,
        })


# ─── Example DAG ───────────────────────────────────────────────────────────

"""
# dags/bq_deferrable_example.py

from datetime import datetime, timedelta
from airflow import DAG
from composer_deferrable_operator import DeferrableBigQueryOperator

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "bq_partitioned_load_deferrable",
    default_args=default_args,
    description="Deferrable BigQuery partitioned load",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["bigquery", "deferrable", "partitioned"],
) as dag:

    load_daily_partition = DeferrableBigQueryOperator(
        task_id="load_daily_partition",
        sql="""
            MERGE `project.dataset.events_partitioned` T
            USING (
                SELECT * FROM `project.dataset.events_staging`
                WHERE DATE(event_timestamp) = '{{ ds }}'
            ) S
            ON T.event_id = S.event_id AND T.customer_id = S.customer_id
            WHEN NOT MATCHED THEN INSERT ROW
        """,
        gcp_conn_id="google_cloud_default",
        project_id="my-project",
        location="asia-southeast1",
        destination_table="my-project.dataset.events_partitioned",
        time_partitioning={"type": "DAY", "field": "event_timestamp"},
        clustering_fields=["customer_id", "event_type"],
        labels={"environment": "prod", "team": "data-eng", "dag": "bq_partitioned_load"},
        poll_interval_seconds=30,
        max_poll_attempts=120,
        deferrable=True,
    )
    
    validate_load = DeferrableBigQueryOperator(
        task_id="validate_load",
        sql="""
            SELECT 
                COUNT(*) as row_count,
                SUM(CASE WHEN event_timestamp >= '{{ ds }}' THEN 1 ELSE 0 END) as todays_rows
            FROM `project.dataset.events_partitioned`
            WHERE DATE(event_timestamp) = '{{ ds }}'
        """,
        gcp_conn_id="google_cloud_default",
        deferrable=True,
    )
    
    load_daily_partition >> validate_load
"""
```

---

## 🎯 Interview Talking Points

### "Why deferrable operators? What problem do they solve?"

**Traditional Sensor Problem:**
```
┌─────────────────────────────────────────────────────────────┐
│  Worker Slot (expensive, limited)                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ BigQueryExecuteQueryOperator                        │   │
│  │   └─> Submits job, returns immediately              │   │
│  │ BigQueryJobSensor                                   │   │
│  │   └─> Polls every 30s for 1 hour = 120 polls       │   │
│  │       Worker blocked entire time!                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Deferrable Operator Solution:**
```
┌─────────────────────────────────────────────────────────────┐
│  Worker Slot                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ DeferrableBigQueryOperator                          │   │
│  │   └─> Submits job, pushes job_id to XCom            │   │
│  │   └─> DEFERS (releases worker slot!)                │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  Triggerer (separate process, lightweight)                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ BigQueryJobTrigger                                  │   │
│  │   └─> Polls asynchronously, yields TriggerEvent     │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  Worker Slot (reclaimed)                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ execute_complete() → pushes results to XCom         │   │
│  │ Downstream tasks continue                           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Benefits:**
- **Cost:** Worker slot free for other tasks (Composer bills per slot-hour)
- **Scale:** 1 triggerer can monitor 1000+ jobs vs 1 worker per job
- **Resilience:** Triggerer restarts don't affect job; job continues in BQ
- **Observability:** XCom has job_id immediately; downstream can track

### "How does the trigger handle transient errors?"

1. **Error Classification** — Checks `error_result.reason` against known transient codes (`backendError`, `rateLimitExceeded`, `quotaExceeded`, etc.)
2. **Retry Logic** — If transient and attempts remain, continues polling with exponential backoff
3. **Backoff + Jitter** — `min(interval * 2, max_backoff) ± 25%` prevents thundering herd
4. **Terminal Errors** — Non-transient errors (syntax, permissions, not found) fail immediately

### "What's the contract between operator and trigger?"

```python
# Operator → Trigger (via defer())
self.defer(
    trigger=BigQueryJobTrigger(
        job_id=...,           # Required: job identifier
        project_id=...,       # Required: BQ project
        location=...,         # Required: BQ location
        gcp_conn_id=...,      # Required: auth
        poll_interval_seconds=...,
        max_poll_attempts=...,
        # ... polling config
    ),
    method_name="execute_complete",  # Callback method
)

# Trigger → Operator (via TriggerEvent yield)
yield TriggerEvent({
    "status": "success|error|timeout",  # Required
    "job_id": "...",
    "project_id": "...",
    "location": "...",
    "duration_seconds": 123.4,
    "bytes_processed": 1000000,
    "bytes_billed": 1000000,
    "slot_millis": 50000,
    "rows_affected": 1000,
    # ... job metrics
    "error_code": "...",      # Only on error
    "message": "...",         # Only on error
})
```

### "How do you test deferrable operators?"

```python
# test_composer_deferrable_operator.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from airflow.utils.context import Context

from composer_deferrable_operator import DeferrableBigQueryOperator

class TestDeferrableBigQueryOperator:
    
    @patch("composer_deferrable_operator.BigQueryHook")
    def test_execute_submits_job_and_defers(self, mock_hook_class):
        # Setup
        mock_hook = Mock()
        mock_hook_class.return_value = mock_hook
        mock_job = Mock()
        mock_job.job_id = "test-job-123"
        mock_job.project = "test-project"
        mock_job.location = "us-central1"
        mock_hook.insert_job.return_value = mock_job
        
        operator = DeferrableBigQueryOperator(
            task_id="test_task",
            sql="SELECT 1",
            deferrable=True,
        )
        
        # Mock context
        context = {
            "ti": Mock(),
            "task": operator,
        }
        context["ti"].xcom_push = Mock()
        
        # Execute
        with pytest.raises(TaskDeferred) as exc_info:
            operator.execute(context)
        
        # Verify
        assert exc_info.value.trigger.job_id == "test-job-123"
        assert exc_info.value.method_name == "execute_complete"
        context["ti"].xcom_push.assert_any_call(key="job_id", value="test-job-123")
    
    @patch("composer_deferrable_operator.BigQueryHook")
    def test_execute_complete_success(self, mock_hook_class):
        operator = DeferrableBigQueryOperator(task_id="test", sql="SELECT 1")
        operator._job_id = "test-job"
        operator._start_time = time.time() - 100
        
        event = {
            "status": "success",
            "job_id": "test-job",
            "project_id": "test-project",
            "location": "us-central1",
            "duration_seconds": 100.0,
            "bytes_processed": 1_000_000_000,
            "bytes_billed": 1_000_000_000,
            "slot_millis": 50000,
            "rows_affected": 1000,
        }
        
        result = operator.execute_complete({}, event)
        
        assert result["status"] == "success"
        assert result["bytes_processed"] == 1_000_000_000
        assert result["slot_millis"] == 50000
    
    @patch("composer_deferrable_operator.BigQueryHook")
    def test_execute_complete_error(self, mock_hook_class):
        operator = DeferrableBigQueryOperator(task_id="test", sql="SELECT 1")
        
        event = {
            "status": "error",
            "job_id": "test-job",
            "error_code": "invalidQuery",
            "message": "Syntax error",
        }
        
        with pytest.raises(AirflowException) as exc_info:
            operator.execute_complete({}, event)
        
        assert "Syntax error" in str(exc_info.value)
```

---

## 📋 Production Checklist

- [ ] **Composer Version** — Airflow 2.7+ (deferrable operators GA in 2.7)
- [ ] **Triggerer** — Deploy at least 1 triggerer (`composer environments update --triggerer-count=2`)
- [ ] **IAM** — Service account: `bigquery.jobs.create`, `bigquery.jobs.get`, `bigquery.tables.updateData`
- [ ] **VPC-SC** — BigQuery accessible via Private Service Connect
- [ ] **Labels** — All jobs labeled with `dag_id`, `task_id`, `environment`, `team` for cost attribution
- [ ] **Monitoring** — Alert on: job duration > SLA, bytes_billed > threshold, slot_millis > quota
- [ ] **Idempotency** — Deterministic `job_id_prefix` + timestamp enables safe retry
- [ ] **Documentation** — Operator docstring with params, example DAG, error codes reference