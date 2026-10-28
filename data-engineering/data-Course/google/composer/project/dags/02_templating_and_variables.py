"""
02_templating_and_variables.py — templating, params, Variables and Connections.

Deploy to Composer and trigger with:

    {"audience": "platform-team", "bucket": "my-bucket"}

What it demonstrates:
  * ``{{ ds }}``, ``{{ ts }}``, ``{{ prev_ds }}``, ``{{ data_interval_start }}``
  * ``{{ params.x }}`` — a DAG-run parameter
  * ``{{ var.value.x }}`` — an Airflow Variable (environment-level config)
  * ``{{ conn.my_conn.host }}`` — an Airflow Connection (credentials)
  * ``{{ macros.ds_add(ds, -1) }}`` — a macro
  * ``{{ dag.dag_id }}`` and ``{{ task.task_id }}`` — the object graph
  * ``template_fields`` on a custom operator

The layering rule this DAG encodes:

    params      -> differs per RUN       (a backfill date, a flag)
    Variables   -> differs per ENVIRONMENT (bucket names, project IDs)
    Connections -> holds CREDENTIALS     (never put a password in a Variable)
    DAG file    -> LOGIC and STRUCTURE

The failure this prevents: a password stored in a Variable is visible in
the Composer UI to every user with Variable read access, and is written to
the metadata database in plain text. Use a Connection.
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
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


def report_environment(**context) -> dict:
    """Log every kind of configuration source Airflow offers.

    Args:
        context: The Airflow task context.

    Returns:
        A dict summarising the configuration, which is pushed to XCom.
    """
    ti = context["ti"]
    log.info("dag_id        : %s", context["dag"].dag_id)
    log.info("task_id      : %s", ti.task_id)
    log.info("logical_date : %s", context["logical_date"])
    log.info("run_id       : %s", context["run_id"])
    log.info("params       : %s", context["params"])
    log.info("data_interval: %s -> %s",
             context["data_interval_start"], context["data_interval_end"])

    # A Variable is environment-level configuration. Use `default()` so the
    # DAG still parses in an environment where it has not been set — a
    # missing Variable would otherwise fail the task at run time.
    owner = context["var"].get("pipeline_owner", "unassigned")
    log.info("owner (var)  : %s", owner)

    # A Connection holds credentials. Reading the host is safe; reading a
    # password into a log is not.
    try:
        conn = context["conn"].get("http_orders_api")
        if conn is not None:
            log.info("api host     : %s", conn.host)
    except Exception as exc:  # noqa: BLE001 - a missing connection is not fatal
        log.warning("no http_orders_api connection: %s", exc)

    return {"dag_id": context["dag"].dag_id, "owner": owner}


with DAG(
    dag_id="templating_and_variables",
    description="Templating, params, Variables and Connections.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["tutorial", "templating"],
    params={
        "audience": "data-engineers",
        "bucket": "default-bucket",
    },
) as dag:
    show = PythonOperator(
        task_id="report_environment",
        python_callable=report_environment,
    )

    # Templating works in BashOperator too — Airflow renders the command
    # before the shell sees it.
    show_paths = BashOperator(
        task_id="show_paths",
        bash_command=(
            "echo 'source : gs://{{ var.value.source_bucket | default('demo') }}/{{ ds }}/orders.csv'; "
            "echo 'target : gs://{{ params.bucket | default(var.value.target_bucket) }}/{{ dag.dag_id }}/{{ ds }}'; "
            "echo 'prev   : {{ prev_ds }}'; "
            "echo 'yesterday+1 : {{ macros.ds_add(ds, 1) }}'; "
            "echo 'partition   : {{ ds_nodash }}'"
        ),
    )

    show >> show_paths
