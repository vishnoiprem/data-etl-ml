"""
Problem 04: Backfill strategy for 90 days.

Meta flavor: After a bug fix or logic change, re-run the last 90 days.
Critical: idempotent jobs, controlled concurrency, monitoring.

How to Think:
- Set `catchup=True` for one-shot backfill DAG.
- Use `max_active_runs` to limit concurrency (avoid cluster overload).
- Use `execution_date` between start and end.
- Pause prod-DAG while backfill runs.

How to Remember:
- "Separate DAG for backfill; limit concurrency."
- "Always dry-run first on 1-2 days."

AI Use Cases:
- Auto-detect affected date ranges from code diff.
- Smart concurrency (only run as fast as cluster allows).
- Auto-validation of backfill output vs prior run.
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta

BACKFILL_START = datetime(2025, 10, 1)
BACKFILL_END   = datetime(2025, 12, 30)   # inclusive end

default_args = {
    "owner":   "data-eng",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

def reprocess_day(**ctx):
    ds = ctx["ds"]
    # idempotent: partition overwrite
    spark.sql(f"""
        INSERT OVERWRITE TABLE prod.events PARTITION (dt='{ds}')
        SELECT * FROM staging.events_v2 WHERE dt='{ds}'
    """)

with DAG(
    dag_id="backfill_events_90d",
    default_args=default_args,
    start_date=BACKFILL_START,
    end_date=BACKFILL_END,
    schedule_interval="@daily",
    catchup=True,
    max_active_runs=4,         # limit cluster pressure
    tags=["backfill", "prod"],
) as dag:
    PythonOperator(
        task_id="reprocess_day",
        python_callable=reprocess_day,
    )

# Operational checklist
CHECKLIST = [
    "1. Dry-run on 1-2 days; compare row counts + spot-check metrics.",
    "2. Pause downstream prod DAGs that read prod.events.",
    "3. Set max_active_runs (4-8) to avoid cluster saturation.",
    "4. Monitor SLA + cluster health during backfill.",
    "5. Validate final partition counts before re-enabling prod.",
]
