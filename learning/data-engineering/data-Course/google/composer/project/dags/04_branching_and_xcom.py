"""
04_branching_and_xcom.py — branching, XCom and sensors.

Deploy to Composer and trigger with:

    {"row_count": 1500000, "force_full_load": false}

What it demonstrates:
  * `BranchOperator` — choose one of two paths at run time
  * `branch` + `trigger_rule` — how a task downstream of a branch runs
  * `ShortCircuitOperator` — skip everything downstream in one step
  * XCom push and pull, and the 48 KB size limit that bites
  * `PythonSensor` and `HttpSensor` — waiting for a condition
  * `TriggerDagRunOperator` — chain DAGs together
  * `EmptyOperator` — a join point with no work of its own

Two ideas carry most of the weight here.

**Branching is about downstream skip, not about skipping yourself.**
`BranchOperator` returns a list of task_ids to run. Every other
downstream task is marked *skipped*. The chosen task runs normally. A
task that depends on *both* branches must use `trigger_rule="none_failed"`
or `"all_done"` — otherwise it is skipped too, because one of its
dependencies was skipped. That is the most common branching bug, and it
produces a DAG that looks correct and quietly does nothing.

**XCom is a database, not a dict.** In Airflow, XCom values live in the
metadata database (or an external XCom backend). They are meant for
*small* control data — a count, a partition name, a decision. Putting a
million-row result in one XCom will blow up the metadata database and
slow every task in the environment down. Pass bulk data through Cloud
Storage or BigQuery, and pass only the *reference* through XCom.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import (
    BranchOperator,
    PythonOperator,
    ShortCircuitOperator,
)
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sensors.python import PythonSensor

log = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

#: The threshold above which the pipeline switches to a full reload.
#: Exceeding BigQuery's per-table load limits is the usual reason a
#: full reload exists at all.
FULL_LOAD_THRESHOLD = 1_000_000


def count_rows(**context) -> int:
    """Count the rows available for this run and push the count via XCom.

    Args:
        context: The Airflow task context.

    Returns:
        The row count.
    """
    params = context["params"]
    row_count = int(params.get("row_count", 0))

    # The return value of a PythonOperator is automatically pushed to
    # XCom under the key "return_value". You can push other keys with
    # ti.xcom_push().
    context["ti"].xcom_push(key="threshold", value=FULL_LOAD_THRESHOLD)
    log.info("row_count=%d threshold=%d", row_count, FULL_LOAD_THRESHOLD)
    return row_count


def choose_strategy(**context) -> list[str]:
    """Choose between the full-load and incremental paths.

    The return value is the list of task_ids that should run. Everything
    else downstream is skipped.

    Args:
        context: The Airflow task context.

    Returns:
        A single-element list naming the task to run.
    """
    ti = context["ti"]
    row_count = int(ti.xcom_pull(task_ids="count_rows") or 0)
    threshold = int(ti.xcom_pull(task_ids="count_rows", key="threshold") or FULL_LOAD_THRESHOLD)

    force = bool(context["params"].get("force_full_load", False))
    chosen = "full_load" if (row_count > threshold or force) else "incremental_load"

    log.info("row_count=%d threshold=%d force=%s -> %s", row_count, threshold, force, chosen)
    return [chosen]


def full_load(**context) -> str:
    """Rewrite the whole table.

    Args:
        context: The Airflow task context.

    Returns:
        A description of what was done.
    """
    log.info("FULL LOAD: rewriting the entire table")
    return "full_load"


def incremental_load(**context) -> str:
    """Append one partition.

    Args:
        context: The Airflow task context.

    Returns:
        A description of what was done.
    """
    partition = context["ds_nodash"]
    log.info("INCREMENTAL LOAD: appending partition %s", partition)
    return f"incremental_load:{partition}"


def wait_for_upstream_data(**context) -> bool:
    """Poll until the upstream data is ready.

    A sensor *resumes* the task when its condition is met; it does not
    busy-wait in a loop. The Airflow worker is released while the sensor
    waits, and the task is re-evaluated later. That is the key property
    that makes sensors the right tool for "wait for X" and a
    ``time.sleep`` loop the wrong one.

    Args:
        context: The Airflow task context.

    Returns:
        True when the condition is satisfied.
    """
    expected_rows = int(context["params"].get("expected_rows", 0))
    actual_rows = int(context["params"].get("row_count", 0))
    ready = actual_rows >= expected_rows
    log.info("sensor: expected>=%d actual=%d ready=%s", expected_rows, actual_rows, ready)
    return ready


with DAG(
    dag_id="branching_and_xcom",
    description="Branching, XCom and sensors.",
    schedule=None,  # manual trigger only
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["tutorial", "branching", "xcom"],
    params={
        "row_count": 0,
        "expected_rows": 0,
        "force_full_load": False,
    },
) as dag:
    # --- XCom: count rows, and pass the count downstream -------------
    count = PythonOperator(
        task_id="count_rows",
        python_callable=count_rows,
    )

    # --- A sensor that gates the pipeline ---------------------------
    # `mode="reschedule"` releases the worker slot while it waits — use
    # it for long waits. `mode="poke"` holds the slot but responds
    # faster. For anything over a few minutes, use "reschedule".
    sensor = PythonSensor(
        task_id="wait_for_upstream_data",
        python_callable=wait_for_upstream_data,
        mode="reschedule",
        timeout=3600,
        poke_interval=300,
        soft_fail=True,
    )

    # --- The branch --------------------------------------------------
    branch = BranchOperator(
        task_id="choose_strategy",
        python_callable=choose_strategy,
    )

    full = PythonOperator(task_id="full_load", python_callable=full_load)
    incremental = PythonOperator(task_id="incremental_load", python_callable=incremental_load)

    # --- A join point ------------------------------------------------
    # This task depends on BOTH branches. Because one branch will be
    # skipped, the default trigger_rule ("all_success") would skip this
    # task too. `none_failed` means "run as long as nothing failed" —
    # a skipped dependency does not count as a failure.
    join = EmptyOperator(
        task_id="load_complete",
        trigger_rule="none_failed",
    )

    # --- Chaining to another DAG -------------------------------------
    trigger_next = TriggerDagRunOperator(
        task_id="trigger_downstream_dag",
        trigger_dag_id="branching_and_xcom_child",
        wait_for_completion=False,
        conf={"parent_run_id": "{{ run_id }}"},
    )

    count >> sensor >> branch
    branch >> full >> join
    branch >> incremental >> join
    join >> trigger_next
