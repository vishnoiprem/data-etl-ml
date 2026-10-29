"""
test_local_runner.py — tests for the mini Airflow and the DAG definitions.

These tests exercise the runner's orchestration semantics — dependencies,
trigger rules, branching, XCom, retries — without Airflow installed.

They are worth having because they pin down the *semantics* the course
teaches. If the runner's idea of branching ever diverged from Airflow's,
the local runs would teach the wrong thing.
"""
from __future__ import annotations

import pytest

from local_runner import (
    BranchException,
    DAG,
    Task,
    TaskSkip,
    build_etl_dag,
    build_branching_dag,
    build_template_dag,
    build_xcom_dag,
    run_dag,
)

LOGICAL_DATE = "2026-01-15"


# --------------------------------------------------------------------------
# The mini Airflow
# --------------------------------------------------------------------------


class TestDAGValidation:
    """Tests for the DAG's structural checks."""

    def test_unknown_dependency_raises(self):
        with pytest.raises(ValueError, match="unknown task"):
            DAG("d", [Task("a", lambda **kw: None, dependencies=["ghost"])])

    def test_cycle_is_detected(self):
        tasks = [
            Task("a", lambda **kw: None, dependencies=["c"]),
            Task("b", lambda **kw: None, dependencies=["a"]),
            Task("c", lambda **kw: None, dependencies=["b"]),
        ]
        with pytest.raises(ValueError, match="cycle detected"):
            DAG("d", tasks)

    def test_self_cycle_is_detected(self):
        with pytest.raises(ValueError, match="cycle detected"):
            DAG("d", [Task("a", lambda **kw: None, dependencies=["a"])])

    def test_downstream_is_transitive(self):
        tasks = [
            Task("a", lambda **kw: None),
            Task("b", lambda **kw: None, dependencies=["a"]),
            Task("c", lambda **kw: None, dependencies=["b"]),
        ]
        dag = DAG("d", tasks)
        assert set(dag.downstream("a")) == {"b", "c"}


class TestExecution:
    """Tests for task execution order and state."""

    def test_tasks_run_in_dependency_order(self):
        order = []
        tasks = [
            Task("a", lambda **kw: order.append("a")),
            Task("b", lambda **kw: order.append("b"), dependencies=["a"]),
            Task("c", lambda **kw: order.append("c"), dependencies=["b"]),
        ]
        run_dag(DAG("d", tasks), LOGICAL_DATE)
        assert order == ["a", "b", "c"]

    def test_independent_tasks_both_run(self):
        ran = []
        tasks = [
            Task("a", lambda **kw: ran.append("a")),
            Task("b", lambda **kw: ran.append("b")),
        ]
        run_dag(DAG("d", tasks), LOGICAL_DATE)
        assert sorted(ran) == ["a", "b"]

    def test_failure_marks_dependents_upstream_failed(self):
        def boom(**kwargs):
            raise RuntimeError("boom")

        tasks = [
            Task("a", boom),
            Task("b", lambda **kw: None, dependencies=["a"]),
        ]
        run = run_dag(DAG("d", tasks), LOGICAL_DATE)
        assert run.state["a"] == "failed"
        assert run.state["b"] == "upstream_failed"

    def test_retry_succeeds_on_second_attempt(self):
        attempts = {"n": 0}

        def flaky(**kwargs):
            attempts["n"] += 1
            if attempts["n"] < 2:
                raise RuntimeError("transient")
            return "ok"

        tasks = [Task("a", flaky, retries=2)]
        run = run_dag(DAG("d", tasks), LOGICAL_DATE)
        assert attempts["n"] == 2
        assert run.state["a"] == "success"

    def test_task_skip_is_recorded(self):
        def skipper(**kwargs):
            raise TaskSkip("not applicable")

        tasks = [Task("a", skipper)]
        run = run_dag(DAG("d", tasks), LOGICAL_DATE)
        assert run.state["a"] == "skipped"

    def test_xcom_pull_returns_the_return_value(self):
        tasks = [
            Task("a", lambda **kw: 42),
            Task("b", lambda run, **kw: run.pull("a"), dependencies=["a"]),
        ]
        run = run_dag(DAG("d", tasks), LOGICAL_DATE)
        assert run.pull("b") == 42

    def test_xcom_push_uses_a_named_key(self):
        def pusher(run, **kwargs):
            run.xcom.push("a", "custom", "value")
            return "ret"

        tasks = [Task("a", pusher)]
        run = run_dag(DAG("d", tasks), LOGICAL_DATE)
        assert run.pull("a", "custom") == "value"
        assert run.pull("a") == "ret"


class TestTriggerRules:
    """Tests for trigger rules."""

    def test_none_failed_runs_when_a_dependency_is_skipped(self):
        """The rule that makes a join point after a branch work."""
        def skipper(**kwargs):
            raise TaskSkip("skipped")

        tasks = [
            Task("a", skipper),
            Task("b", lambda **kw: "ran", dependencies=["a"], trigger_rule="none_failed"),
        ]
        run = run_dag(DAG("d", tasks), LOGICAL_DATE)
        assert run.state["a"] == "skipped"
        assert run.state["b"] == "success"

    def test_all_success_skips_when_a_dependency_is_skipped(self):
        def skipper(**kwargs):
            raise TaskSkip("skipped")

        tasks = [
            Task("a", skipper),
            Task("b", lambda **kw: "ran", dependencies=["a"]),
        ]
        run = run_dag(DAG("d", tasks), LOGICAL_DATE)
        assert run.state["b"] == "skipped"

    def test_all_done_runs_even_after_a_failure(self):
        def boom(**kwargs):
            raise RuntimeError("boom")

        tasks = [
            Task("a", boom),
            Task("b", lambda **kw: "ran", dependencies=["a"], trigger_rule="all_done"),
        ]
        run = run_dag(DAG("d", tasks), LOGICAL_DATE)
        assert run.state["b"] == "success"

    def test_none_failed_does_not_run_after_a_failure(self):
        def boom(**kwargs):
            raise RuntimeError("boom")

        tasks = [
            Task("a", boom),
            Task("b", lambda **kw: "ran", dependencies=["a"], trigger_rule="none_failed"),
        ]
        run = run_dag(DAG("d", tasks), LOGICAL_DATE)
        assert run.state["b"] == "upstream_failed"


class TestBranching:
    """Tests for branch behaviour."""

    def test_branch_runs_the_chosen_task_only(self):
        """A BranchOperator skips every downstream task it does not name."""

        def brancher(**kwargs):
            return ["left"]

        tasks = [
            Task("branch", brancher, branch=True),
            Task("left", lambda **kw: "L", dependencies=["branch"]),
            Task("right", lambda **kw: "R", dependencies=["branch"]),
        ]
        run = run_dag(DAG("d", tasks), LOGICAL_DATE)
        assert run.state["left"] == "success"
        assert run.state["right"] == "skipped"

    def test_join_point_runs_after_a_branch(self):
        """A task depending on both branches needs `none_failed`."""

        def brancher(**kwargs):
            return ["left"]

        tasks = [
            Task("branch", brancher, branch=True),
            Task("left", lambda **kw: "L"),
            Task("right", lambda **kw: "R"),
            Task("join", lambda **kw: "J", dependencies=["left", "right"], trigger_rule="none_failed"),
        ]
        run = run_dag(DAG("d", tasks), LOGICAL_DATE)
        assert run.state["join"] == "success"

    def test_branch_exception_is_honoured(self):
        def brancher(**kwargs):
            raise BranchException(["right"])

        tasks = [
            Task("branch", brancher, branch=True),
            Task("left", lambda **kw: "L", dependencies=["branch"]),
            Task("right", lambda **kw: "R", dependencies=["branch"]),
        ]
        run = run_dag(DAG("d", tasks), LOGICAL_DATE)
        assert run.state["right"] == "success"
        assert run.state["left"] == "skipped"


# --------------------------------------------------------------------------
# The course DAGs
# --------------------------------------------------------------------------


class TestCourseDags:
    """Tests that the course DAGs are well-formed and run."""

    @pytest.mark.parametrize(
        "builder",
        [build_etl_dag, build_branching_dag, build_template_dag, build_xcom_dag],
    )
    def test_dag_builds_without_cycles(self, builder):
        dag = builder()
        assert dag.tasks

    def test_etl_dag_succeeds(self, tmp_path):
        dag = build_etl_dag()
        run = run_dag(dag, LOGICAL_DATE)
        assert all(state == "success" for state in run.state.values())

    def test_etl_dag_produces_the_expected_summary(self):
        run = run_dag(build_etl_dag(), LOGICAL_DATE)
        summary = run.pull("aggregate", "summary")
        assert summary["EMEA"] == {"order_count": 322, "revenue_eur": 118423.22}

    def test_branching_dag_takes_the_incremental_path(self):
        run = run_dag(build_branching_dag(), LOGICAL_DATE)
        assert run.state["incremental_load"] == "success"
        assert run.state["full_load"] == "skipped"
        assert run.state["finalise"] == "success"

    def test_branching_dag_takes_the_full_path_above_the_threshold(self):
        from local_runner import DEFAULT_VARIABLES

        variables = dict(DEFAULT_VARIABLES)
        variables["full_load_threshold"] = 10
        run = run_dag(build_branching_dag(), LOGICAL_DATE, variables=variables)
        assert run.state["full_load"] == "success"
        assert run.state["incremental_load"] == "skipped"

    def test_templating_dag_renders_expected_paths(self):
        run = run_dag(build_template_dag(), LOGICAL_DATE)
        paths = run.pull("render_paths")
        assert paths["source"] == "gs://demo-source-bucket/2026-01-15/orders.csv"
        assert paths["partition"] == "20260115"
        assert paths["previous"].endswith("2026-01-14/orders.csv")

    def test_xcom_dag_passes_the_summary_downstream(self):
        run = run_dag(build_xcom_dag(), LOGICAL_DATE)
        assert run.pull("publish_summary", "summary") == run.pull("aggregate", "summary")
