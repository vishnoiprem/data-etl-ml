# Daily Airflow DAG: Extract -> Transform -> Load

## Problem
Design a standard nightly batch ETL DAG in Airflow.

## How to Think
1. **Three tasks**: extract -> transform -> load.
2. **Schedule**: daily at 02:00 UTC.
3. **Retries**: 3 with exponential backoff.
4. **SLA**: must finish by 06:00 UTC.
5. **Hand-off**: XCom for partition dates.

## How to Remember
- **Pattern**: "XCom for handoff."
- **Retries**: exponential backoff with a max-delay cap.

## Code (Airflow DAG)
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

default_args = {
    "owner":            "data-eng",
    "depends_on_past":  False,
    "retries":          3,
    "retry_delay":      timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay":  timedelta(minutes=30),
    "sla":              timedelta(hours=4),
}

def extract(**ctx):
    ds = ctx["ds"]
    return f"s3://raw/events/dt={ds}"

def transform(**ctx):
    ds = ctx["ds"]
    src = ctx["ti"].xcom_pull(task_ids="extract")
    return f"s3://staging/events/dt={ds}"

def load(**ctx):
    ds = ctx["ds"]
    staged = ctx["ti"].xcom_pull(task_ids="transform")
    return f"s3://prod/events/dt={ds}"

with DAG(
    dag_id="daily_events_etl",
    default_args=default_args,
    schedule_interval="0 2 * * *",
    start_date=days_ago(30),
    catchup=False,
    tags=["prod", "nightly"],
) as dag:
    t1 = PythonOperator(task_id="extract",   python_callable=extract)
    t2 = PythonOperator(task_id="transform", python_callable=transform)
    t3 = PythonOperator(task_id="load",      python_callable=load)
    t1 >> t2 >> t3
```

## Common Mistakes
- No `catchup=False` -> silent backfill of all missing days on deploy.
- No SLA -> silent delays.
- No XCom hand-off -> hardcoded paths between tasks.

## AI Use Cases
- Auto-generate DAG skeleton from SQL/Python ETL definition.
- Anomaly detection on DAG run duration.
- Smart backfill on partial failure.
