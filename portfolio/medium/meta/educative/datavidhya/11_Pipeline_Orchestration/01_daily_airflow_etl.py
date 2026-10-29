"""
Problem 01: Daily Airflow DAG - extract -> transform -> load.

Meta flavor: Standard nightly batch ETL. Show how to wire tasks with
dependencies, retries, and SLA.

How to Think:
- DAG with three tasks: extract, transform, load.
- Schedule: daily at 02:00 UTC.
- Retries: 3 with exponential backoff.
- SLA: must complete by 06:00 UTC (alert on miss).

How to Remember:
- "extract -> transform -> load (XCom for handoff)."
- Use task_id-based XComs to pass partition dates between tasks.

AI Use Cases:
- Auto-generate DAGs from SQL/Python ETL definitions.
- Anomaly detection on DAG run duration.
- Smart backfill on partial failures.
"""
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
    ds = ctx["ds"]                      # execution date YYYY-MM-DD
    # Pull from upstream API / S3 / Hive
    return f"s3://raw/events/dt={ds}"

def transform(**ctx):
    ds = ctx["ds"]
    src = ctx["ti"].xcom_pull(task_ids="extract")
    # write to s3://staging/dt=...
    return f"s3://staging/events/dt={ds}"

def load(**ctx):
    ds = ctx["ds"]
    staged = ctx["ti"].xcom_pull(task_ids="transform")
    # atomic rename into s3://prod/events/dt=...
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
