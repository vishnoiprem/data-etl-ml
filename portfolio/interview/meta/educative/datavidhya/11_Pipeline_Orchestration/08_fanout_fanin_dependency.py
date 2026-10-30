"""
Problem 08: Dependency DAG: fan-out then fan-in.

Meta flavor: Multiple parallel transformations, then a single aggregator.
Show the Airflow pattern.

How to Think:
- Fan-out: parallel tasks on partitioned slices (e.g., by country).
- Fan-in: aggregator task waits for ALL fan-out tasks.
- Use `trigger_rule='all_success'` on the aggregator.

How to Remember:
- "fan-out: list comprehension of operators; fan-in: trigger_rule='all_success'."
- "Limit parallelism to avoid resource exhaustion."

AI Use Cases:
- Auto-fanout by detected partition columns.
- Adaptive parallelism based on cluster load.
- Auto-rebalance skewed partitions.
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
from datetime import timedelta

COUNTRIES = ["US", "IN", "BR", "GB", "DE", "JP"]

def transform_country(country, **ctx):
    # read partitioned slice, transform, write
    print(f"Transforming {country} for {ctx['ds']}")

def aggregate(**ctx):
    # combine per-country outputs
    print(f"Aggregating {ctx['ds']}")

default_args = {"owner": "data-eng", "retries": 2, "retry_delay": timedelta(minutes=5)}

with DAG("fanout_fanin", default_args=default_args,
         schedule_interval="@daily",
         start_date=days_ago(7), catchup=False) as dag:

    country_tasks = [
        PythonOperator(
            task_id=f"transform_{c}",
            python_callable=transform_country,
            op_kwargs={"country": c},
        ) for c in COUNTRIES
    ]

    agg = PythonOperator(
        task_id="aggregate",
        python_callable=aggregate,
        trigger_rule=TriggerRule.ALL_SUCCESS,
    )

    # Fan-in: ALL country tasks feed aggregator
    country_tasks >> agg
