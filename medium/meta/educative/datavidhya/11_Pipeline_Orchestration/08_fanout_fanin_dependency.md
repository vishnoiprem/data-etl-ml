# Dependency DAG: Fan-Out then Fan-In

## Problem
Build an Airflow DAG that fans out by partition, then aggregates the results.

## How to Think
1. **Fan-out** – parallel tasks per slice (country, surface, etc.).
2. **Fan-in** – aggregator waits for ALL upstream tasks.
3. **trigger_rule='all_success'** on the aggregator.
4. **Limit parallelism** to protect the cluster.

## How to Remember
- **"Fan-out: list comprehension of operators."**
- **"Fan-in: trigger_rule='all_success'."**

## Code (Airflow)
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
from datetime import timedelta

COUNTRIES = ["US", "IN", "BR", "GB", "DE", "JP"]

def transform_country(country, **ctx):
    print(f"Transforming {country} for {ctx['ds']}")

def aggregate(**ctx):
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

    country_tasks >> agg
```

## Common Mistakes
- No `trigger_rule='all_success'` -> aggregator runs after first task.
- Unbounded fan-out -> resource exhaustion.
- Skewed partitions (one slow country blocks fan-in).

## AI Use Cases
- Auto-fanout by detected partition columns.
- Adaptive parallelism based on cluster load.
- Auto-rebalance skewed partitions.
