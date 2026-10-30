# Backfill Strategy for 90 Days

## Problem
Re-run the last 90 days of a daily job after a bug fix. Design the strategy.

## How to Think
1. **Separate backfill DAG** with `catchup=True`.
2. **Idempotent** job logic (partition overwrite).
3. **Limit concurrency** via `max_active_runs`.
4. **Dry-run** first on 1-2 days.
5. **Pause downstream** prod DAGs that read the affected table.
6. **Validate** before re-enabling prod.

## How to Remember
- **"Separate DAG for backfill; limit concurrency."**
- **"Dry-run, then ramp."**

## Code (Backfill DAG)
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

BACKFILL_START = datetime(2025, 10, 1)
BACKFILL_END   = datetime(2025, 12, 30)

default_args = {"owner": "data-eng", "retries": 2, "retry_delay": timedelta(minutes=5)}

def reprocess_day(**ctx):
    ds = ctx["ds"]
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
    max_active_runs=4,
    tags=["backfill", "prod"],
) as dag:
    PythonOperator(task_id="reprocess_day", python_callable=reprocess_day)
```

## Operational Checklist
1. Dry-run on 1-2 days; compare row counts + spot-check metrics.
2. Pause downstream prod DAGs that read the affected table.
3. Set `max_active_runs=4-8` to avoid cluster saturation.
4. Monitor SLA + cluster health during backfill.
5. Validate final partition counts before re-enabling prod.

## Common Mistakes
- `catchup=True` without `max_active_runs` -> cluster overload.
- Forgetting to pause downstream DAGs -> readers see partial data.
- No idempotency -> duplicate rows.

## AI Use Cases
- Auto-detect affected date range from code diff.
- Smart concurrency (auto-tune max_active_runs).
- Auto-validate backfill vs prior run (anomaly flag).
