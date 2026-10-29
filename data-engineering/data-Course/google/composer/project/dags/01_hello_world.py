"""
01_hello_world.py — the smallest useful DAG.

Deploy this to Composer to verify your environment end to end.

What it demonstrates:
  * the `DAG` object, its `schedule`, `start_date`, `catchup` and `retries`
  * `PythonOperator` and `BashOperator`
  * the `>>` dependency operator
  * `{{ ds }}` — Airflow's most-used template
  * `{{ params.x }}` — a per-run parameter, with a default

In Composer, every DAG file you upload to the ``dags/`` folder is parsed
within 1–2 minutes. If it imports cleanly, it appears in the DAG list.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

log = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def say_hello(**context) -> str:
    """Log a greeting that includes the run's date.

    The ``**context`` argument is how a PythonOperator receives the
    Airflow context. You can pull named values out of it instead:

        from airflow.operators.python import get_current_context
        context = get_current_context()
        logical_date = context["logical_date"]

    Args:
        context: The Airflow task context, injected by the operator.

    Returns:
        A greeting string, which becomes the task's XCom return value.
    """
    logical_date = context["logical_date"]
    greeting = f"Hello from Airflow! The logical date is {logical_date}."
    log.info(greeting)
    return greeting


with DAG(
    dag_id="hello_world",
    description="The smallest useful DAG — verify your Composer environment.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["tutorial", "composer"],
    params={"audience": "data-engineers"},
) as dag:
    greet = PythonOperator(
        task_id="say_hello",
        python_callable=say_hello,
    )

    print_date = BashOperator(
        task_id="print_date",
        bash_command="echo 'Run date: {{ ds }} (previous: {{ prev_ds }})'",
    )

    # The `>>` operator sets the dependency. `greet >> print_date` means
    # "print_date runs after greet succeeds".
    greet >> print_date
