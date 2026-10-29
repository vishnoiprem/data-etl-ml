from __future__ import annotations
import pytest
from local_runner import DAGS, run_dag

def test_etl_dag_succeeds_and_produces_the_expected_summary() -> None:
    run = run_dag(DAGS["etl_to_gcs"](), "2026-01-15")
    assert all(state == "success" for state in run.state.values())
    assert run.pull("transform_orders")["accepted_count"] == 1245
    assert run.pull("transform_orders")["rejected_count"] == 0
    summary = run.pull("aggregate", "summary")
    assert summary["AMER"] == {"order_count": 318, "revenue_eur": 113592.19}
    assert summary["EMEA"] == {"order_count": 322, "revenue_eur": 118423.22}

def test_branch_takes_full_load_above_threshold() -> None:
    run = run_dag(DAGS["branching_load"](), "2026-01-15", variables={"full_load_threshold": 100})
    assert run.state["full_load"] == "success"
    assert run.state["incremental_load"] == "skipped"
    assert run.state["finalise"] == "success"

def test_branch_takes_incremental_below_threshold() -> None:
    run = run_dag(DAGS["branching_load"](), "2026-01-15", variables={"full_load_threshold": 1_000_000})
    assert run.state["incremental_load"] == "success"
    assert run.state["full_load"] == "skipped"
    assert run.state["finalise"] == "success"

def test_join_point_runs_even_when_a_branch_is_skipped() -> None:
    run = run_dag(DAGS["branching_load"](), "2026-01-15", variables={"full_load_threshold": 100})
    assert run.state["incremental_load"] == "skipped"
    assert run.state["finalise"] == "success"
