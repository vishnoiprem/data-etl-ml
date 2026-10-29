"""Structure tests for the course's DAGs.

These require Airflow. When Airflow is absent, the whole module skips
and the fast pure-logic suite still runs green.
"""
from __future__ import annotations

from pathlib import Path

import pytest

DAGS_DIR = Path(__file__).resolve().parent.parent / "dags"

EXPECTED_DAG_IDS = {
    "hello_world",
    "templating_and_variables",
    "etl_orders_to_bigquery",
    "branching_and_xcom",
}


def _require_airflow() -> None:
    """Skip the test if Airflow is not installed.

    Raises:
        pytest.skip: Always.
    """
    try:
        import airflow  # noqa: F401
    except ImportError:
        pytest.skip("Airflow is not installed — skipping structure tests")


@pytest.fixture(scope="session")
def dagbag():
    """Return a DagBag with the course's DAGs.

    Returns:
        The DagBag.
    """
    _require_airflow()
    from airflow.models import DagBag

    return DagBag(dag_folder=str(DAGS_DIR), include_examples=False)


def test_no_import_errors(dagbag) -> None:
    """No DAG file raises on import."""
    assert dagbag.import_errors == {}, (
        f"Import errors:\n{dagbag.import_errors}"
    )


@pytest.mark.parametrize("dag_id", sorted(EXPECTED_DAG_IDS))
def test_expected_dag_exists(dagbag, dag_id: str) -> None:
    """Every expected DAG is present."""
    assert dag_id in dagbag.dags


def test_etl_dag_shape(dagbag) -> None:
    """The ETL DAG has the tasks and dependencies we expect."""
    dag = dagbag.dags["etl_orders_to_bigquery"]

    assert len(dag.tasks) == 5
    assert dag.get_task("check_source_exists").upstream_task_ids == set()
    assert dag.get_task("validate_and_stage").upstream_task_ids == {
        "check_source_exists"
    }
    assert dag.get_task("load_to_bigquery").upstream_task_ids == {
        "validate_and_stage"
    }
    assert dag.get_task("export_to_gcs").upstream_task_ids == {
        "aggregate_by_region"
    }


def test_etl_dag_reliability_defaults(dagbag) -> None:
    """The ETL DAG sets the reliability defaults we depend on."""
    dag = dagbag.dags["etl_orders_to_bigquery"]

    assert dag.catchup is False
    assert dag.max_active_runs == 1
    assert dag.default_args["owner"] == "data-platform"
    assert dag.default_args["retries"] >= 1


def test_etl_load_is_truncate(dagbag) -> None:
    """The BigQuery load uses WRITE_TRUNCATE, not WRITE_APPEND."""
    from airflow.providers.google.cloud.operators.bigquery import (
        BigQueryInsertJobOperator,
    )

    dag = dagbag.dags["etl_orders_to_bigquery"]
    load = dag.get_task("load_to_bigquery")

    assert isinstance(load, BigQueryInsertJobOperator)
    disposition = load.configuration["query"]["writeDisposition"]
    assert disposition == "WRITE_TRUNCATE"


def test_branching_join_uses_none_failed(dagbag) -> None:
    """The join point uses the trigger rule that survives a skipped branch."""
    dag = dagbag.dags["branching_and_xcom"]
    join = dag.get_task("load_complete")

    assert join.trigger_rule in ("none_failed", "none_failed_min_one_success", "all_done")


def test_sensor_uses_reschedule(dagbag) -> None:
    """The long sensor releases its worker slot between checks."""
    dag = dagbag.dags["branching_and_xcom"]
    sensor = dag.get_task("wait_for_upstream_data")

    assert sensor.mode == "reschedule"
    assert sensor.soft_fail is True
