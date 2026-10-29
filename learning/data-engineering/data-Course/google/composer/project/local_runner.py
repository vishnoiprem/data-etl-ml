#!/usr/bin/env python3
"""
local_runner.py — run the course's pipelines locally, with no Airflow installed.

This is the heart of the course's premise. You can learn Cloud Composer
without a local Airflow install, and you can *run and verify* the pipeline
logic without one too.

The runner works in two layers:

    1. **A mini Airflow.** A tiny task graph with dependencies, XCom,
       branching, retries, and a scheduler loop. It implements the subset
       of Airflow's semantics the course needs, so a DAG defined for the
       runner behaves the way it will in Composer.

    2. **The pipelines themselves.** The pure functions in
       ``core/pipeline_logic.py`` do the actual work. The DAG files in
       ``dags/`` are the real, deployable Airflow DAGs; the runner imports
       the *same* core module the DAGs use.

The critical property: **the DAG files in ``dags/`` are the artefact you
deploy to Composer.** The local runner does not reimplement them — it
simulates the orchestration the same way Airflow would, using the same
core functions. What you verify locally is the logic; what you deploy is
the orchestration.

Usage:
    python project/local_runner.py --list
    python project/local_runner.py --dag etl_to_gcs
    python project/local_runner.py --dag etl_to_gcs --date 2026-01-15 --verbose
    python project/local_runner.py --dag all
    python project/local_runner.py --dag etl_to_gcs --interval-days 7
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent
COURSE_ROOT = PROJECT_ROOT.parent
CORE_DIR = PROJECT_ROOT / "core"
DAGS_DIR = PROJECT_ROOT / "dags"

for _path in (str(CORE_DIR), str(DAGS_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

log = logging.getLogger("local_runner")

# --------------------------------------------------------------------------
# The mini Airflow
# --------------------------------------------------------------------------


@dataclass
class XCom:
    """The mini runner's XCom store — one namespace per task.

    Airflow's XCom is a key/value store scoped to a task. A task returns a
    value and it becomes available to downstream tasks as an argument (the
    "XCom push") and via ``ti.xcom_pull`` (the "XCom pull").

    The real Airflow stores these in the metadata database, which is why
    XCom is a *database* and not a dict — and why putting a large payload
    in one is a genuine production mistake (see the XCom chapter).
    """

    store: dict[str, dict[str, Any]] = field(default_factory=dict)

    def push(self, task_id: str, key: str, value: Any) -> None:
        """Store a value for a task.

        Args:
            task_id: The task's identifier.
            key: The key within the task's namespace.
            value: The value to store.
        """
        self.store.setdefault(task_id, {})[key] = value

    def pull(self, task_id: str, key: str = "return_value", default: Any = None) -> Any:
        """Retrieve a value stored by a task.

        Args:
            task_id: The task's identifier.
            key: The key within the task's namespace.
            default: The value returned when the key is absent.

        Returns:
            The stored value, or ``default``.
        """
        return self.store.get(task_id, {}).get(key, default)

    def all_for(self, task_id: str) -> dict[str, Any]:
        """Return everything a task pushed.

        Args:
            task_id: The task's identifier.

        Returns:
            A dict of key -> value.
        """
        return dict(self.store.get(task_id, {}))


class TaskSkip(Exception):
    """Raised to skip a task, like Airflow's ``AirflowSkipException``."""


class BranchException(Exception):
    """Raised to signal a branch decision.

    Mirrors Airflow's ``BranchException``: the downstream tasks named in
    the payload are the ones that should run; the rest are skipped.
    """

    def __init__(self, branches: Sequence[str]) -> None:
        super().__init__(f"branch to: {', '.join(branches)}")
        self.branches = list(branches)


@dataclass
class Task:
    """A single node in the mini DAG.

    Attributes:
        task_id: The task's identifier.
        callable: The Python callable to run.
        dependencies: The task_ids that must succeed first.
        retries: How many times to retry on failure.
        retry_delay: Seconds to wait between retries.
        trigger_rule: ``"all_success"`` (default), ``"none_failed"``,
            ``"all_done"``, or ``"always"``.
        branch: When set, this task returns a list of downstream task_ids
            to run and everything else is skipped.
        params: Keyword arguments passed to the callable.
    """

    task_id: str
    callable: Callable[..., Any]
    dependencies: list[str] = field(default_factory=list)
    retries: int = 0
    retry_delay: float = 0.0
    trigger_rule: str = "all_success"
    branch: bool = False
    params: dict[str, Any] = field(default_factory=dict)


class DAG:
    """A minimal DAG: tasks plus dependency edges.

    This is deliberately small. It implements the parts of Airflow's
    semantics that change *observable behaviour* in a pipeline, and nothing
    else:

    * dependency ordering
    * upstream failure propagation
    * trigger rules (``all_success``, ``none_failed``, ``all_done``)
    * branch fan-out and skip
    * retries with delay
    * XCom push/pull
    """

    def __init__(
        self,
        dag_id: str,
        tasks: list[Task],
        *,
        schedule: str = "@daily",
        start_date: str = "2026-01-01",
        catchup: bool = False,
        max_active_runs: int = 1,
        description: str = "",
    ) -> None:
        """Create a DAG.

        Args:
            dag_id: The DAG's identifier.
            tasks: The tasks in the DAG.
            schedule: The schedule string.
            start_date: The DAG's start date.
            catchup: Whether missed runs should be backfilled.
            max_active_runs: How many runs may overlap.
            description: A human-readable description.
        """
        self.dag_id = dag_id
        self.tasks = {task.task_id: task for task in tasks}
        self.schedule = schedule
        self.start_date = start_date
        self.catchup = catchup
        self.max_active_runs = max_active_runs
        self.description = description
        self._validate()

    def _validate(self) -> None:
        """Check that the dependency graph is acyclic and references exist.

        Raises:
            ValueError: When a dependency is missing or a cycle exists.
        """
        for task in self.tasks.values():
            for dep in task.dependencies:
                if dep not in self.tasks:
                    raise ValueError(
                        f"task {task.task_id!r} depends on unknown task {dep!r}"
                    )

        # Cycle detection via DFS colouring.
        WHITE, GREY, BLACK = 0, 1, 2
        colour = {task_id: WHITE for task_id in self.tasks}

        def visit(node: str, path: list[str]) -> None:
            colour[node] = GREY
            for dep in self.tasks[node].dependencies:
                if colour[dep] == GREY:
                    cycle = " -> ".join(path + [node, dep])
                    raise ValueError(f"cycle detected in DAG {self.dag_id!r}: {cycle}")
                if colour[dep] == WHITE:
                    visit(dep, path + [node])
            colour[node] = BLACK

        for task_id in self.tasks:
            if colour[task_id] == WHITE:
                visit(task_id, [])

    def downstream(self, task_id: str) -> list[str]:
        """Return the task_ids that depend on a task, transitively.

        Args:
            task_id: The task to start from.

        Returns:
            A list of downstream task_ids.
        """
        found: list[str] = []
        frontier = [task_id]
        seen = {task_id}
        while frontier:
            current = frontier.pop()
            for other, task in self.tasks.items():
                if current in task.dependencies and other not in seen:
                    seen.add(other)
                    found.append(other)
                    frontier.append(other)
        return found

    def describe(self) -> str:
        """Return a human-readable description of the DAG.

        Returns:
            A multi-line string describing the DAG.
        """
        lines = [
            f"DAG: {self.dag_id}",
            f"  schedule    : {self.schedule}",
            f"  start_date  : {self.start_date}",
            f"  catchup     : {self.catchup}",
            f"  description : {self.description}",
            f"  tasks ({len(self.tasks)}):",
        ]
        for task_id, task in self.tasks.items():
            deps = ", ".join(task.dependencies) if task.dependencies else "-"
            extra = f" [branch]" if task.branch else ""
            extra += f" [rule={task.trigger_rule}]" if task.trigger_rule != "all_success" else ""
            lines.append(f"    - {task_id:<22} deps=({deps}){extra}")
        return "\n".join(lines)


class DagRun:
    """One execution of a DAG — the runner's execution context."""

    def __init__(
        self,
        dag: DAG,
        logical_date: str,
        *,
        params: dict[str, Any] | None = None,
        variables: dict[str, Any] | None = None,
        connections: dict[str, Any] | None = None,
    ) -> None:
        """Create a run.

        Args:
            dag: The DAG to run.
            logical_date: The run's logical date, ``YYYY-MM-DD``.
            params: DAG-run params.
            variables: Airflow Variables.
            connections: Airflow Connections.
        """
        self.dag = dag
        self.logical_date = logical_date
        self.params = params or {}
        self.variables = variables or {}
        self.connections = connections or {}
        self.xcom = XCom()
        self.state: dict[str, str] = {}
        self.outputs: dict[str, Any] = {}
        self.started_at = datetime.now(timezone.utc)

    def context(self) -> dict[str, Any]:
        """Return the Jinja context for this run.

        Returns:
            The rendering context.
        """
        from templating import build_context

        return build_context(
            dag_id=self.dag.dag_id,
            task_id="__context__",
            logical_date=self.logical_date,
            variables=self.variables,
            connections=self.connections,
            params=self.params,
        )

    def pull(self, task_id: str, key: str = "return_value", default: Any = None) -> Any:
        """Pull an XCom value from a task.

        Args:
            task_id: The task's identifier.
            key: The XCom key.
            default: The value returned when absent.

        Returns:
            The stored value.
        """
        return self.xcom.pull(task_id, key, default)


def run_dag(
    dag: DAG,
    logical_date: str,
    *,
    params: dict[str, Any] | None = None,
    variables: dict[str, Any] | None = None,
    connections: dict[str, Any] | None = None,
    verbose: bool = False,
) -> DagRun:
    """Execute a DAG, honouring dependencies, trigger rules, branches and retries.

    Args:
        dag: The DAG to run.
        logical_date: The run's logical date.
        params: DAG-run params.
        variables: Airflow Variables.
        connections: Airflow Connections.
        verbose: Whether to print each task's result.

    Returns:
        The completed DagRun, whose ``state`` dict holds each task's outcome.

    Raises:
        RuntimeError: If a task fails and no task depends on it — the
            runner surfaces the failure the way Airflow would.
    """
    run = DagRun(
        dag,
        logical_date,
        params=params,
        variables={**DEFAULT_VARIABLES, **(variables or {})},
        connections={**DEFAULT_CONNECTIONS, **(connections or {})},
    )
    context = run.context()

    # Resolve the execution order: a task runs when every dependency is
    # resolved. This is a topological walk, recomputed each pass so that
    # branch skips can unblock downstream tasks.
    pending = set(dag.tasks)
    skipped: set[str] = set()
    branch_targets: set[str] | None = None

    while pending:
        progressed = False
        # Iterate in *dependency order*, not insertion order. Without this,
        # a task that appears earlier in the list than its dependency
        # would be evaluated before the dependency has run — and, worse,
        # a branch's un-chosen child could execute before the branch
        # itself had decided anything.
        ordered = _dependency_order(dag, pending)
        for task_id in ordered:
            task = dag.tasks[task_id]
            # A task may have been skipped earlier in this same pass — for
            # example by a branch that ran before it in the order. The
            # `ordered` list is a snapshot, so re-check the state.
            if task_id in run.state:
                continue
            if not all(dep in run.state for dep in task.dependencies):
                continue

            dep_states = {dep: run.state[dep] for dep in task.dependencies}

            # A task that depends on a *branching* task must wait until
            # that branch has resolved. Otherwise the iteration order
            # could let the un-chosen branch run before the branch task
            # decided anything.
            if any(dag.tasks[dep].branch for dep in task.dependencies):
                if branch_targets is None:
                    continue

            # A dependency that FAILED blocks the task. Airflow reports
            # this as `upstream_failed`, which is a distinct state from
            # `skipped` — the distinction matters when you are reading a
            # failed DAG in the UI. The exception is `all_done` and
            # `always`, which run precisely *because* everything upstream
            # has finished, successfully or not.
            if "failed" in dep_states.values() and task.trigger_rule not in (
                "all_done",
                "always",
            ):
                run.state[task_id] = "upstream_failed"
                pending.discard(task_id)
                progressed = True
                continue

            should_run = _trigger_allows(task.trigger_rule, dep_states)

            if not should_run:
                run.state[task_id] = "skipped"
                skipped.add(task_id)
                pending.discard(task_id)
                progressed = True
                continue

            _execute_task(task, run, context)
            pending.discard(task_id)
            progressed = True

            if task.branch:
                chosen = run.pull(task_id, "branch")
                branch_targets = set(chosen or [])
                # Airflow's BranchOperator marks every *downstream* task as
                # skipped, except the ones it names. Tasks that depend on
                # the skipped branch and use `none_failed` / `all_done`
                # still run — that is the mechanism behind a join point.
                for candidate in dag.downstream(task_id):
                    if candidate in branch_targets or candidate not in pending:
                        continue
                    other = dag.tasks[candidate]
                    if other.trigger_rule in ("none_failed", "all_done", "always"):
                        continue
                    run.state[candidate] = "skipped"
                    skipped.add(candidate)
                    pending.discard(candidate)

        if not progressed:
            # No task could run. Either everything is blocked by failures,
            # or a dependency is stuck.
            break

    # Any task still pending was blocked by an upstream failure.
    for task_id in pending:
        run.state[task_id] = "upstream_failed"

    if verbose:
        _print_summary(run)

    return run


def _dependency_order(dag: DAG, candidates: Iterable[str]) -> list[str]:
    """Order task_ids so that dependencies come before their dependents.

    Args:
        dag: The DAG.
        candidates: The task_ids to order.

    Returns:
        The task_ids in dependency order. Ties are broken by the DAG's
        insertion order, which keeps runs deterministic.
    """
    remaining = list(candidates)
    insertion = {task_id: index for index, task_id in enumerate(dag.tasks)}
    ordered: list[str] = []

    while remaining:
        ready = [
            task_id
            for task_id in remaining
            if all(
                dep not in remaining
                for dep in dag.tasks[task_id].dependencies
            )
        ]
        if not ready:
            # A cycle among the remaining tasks — the DAG constructor
            # already rejects these, so this is a defensive fallback.
            ordered.extend(sorted(remaining, key=lambda t: insertion.get(t, 0)))
            break
        ready.sort(key=lambda t: insertion.get(t, 0))
        ordered.extend(ready)
        remaining = [t for t in remaining if t not in ready]

    return ordered


def _trigger_allows(rule: str, dep_states: dict[str, str]) -> bool:
    """Decide whether a task should run, given its dependencies' states.

    A dependency in the ``failed`` state is handled before this function
    is called — such a task is marked ``upstream_failed`` regardless of
    its trigger rule. Here we only distinguish *skipped* dependencies from
    *successful* ones.

    Args:
        rule: The trigger rule.
        dep_states: A mapping of dependency task_id -> state.

    Returns:
        True when the task should run.
    """
    states = list(dep_states.values())
    if not states:
        return True
    if rule == "all_success":
        return all(state == "success" for state in states)
    if rule == "none_failed":
        # "none failed" means: run unless something failed. A *skipped*
        # dependency is not a failure, so the task still runs.
        return True
    if rule == "all_done":
        return True
    if rule == "always":
        return True
    return all(state == "success" for state in states)


def _execute_task(task: Task, run: DagRun, context: dict[str, Any]) -> None:
    """Run one task, with retries.

    Args:
        task: The task to run.
        run: The run context.
        context: The Jinja context.
    """
    attempt = 0
    while True:
        try:
            result = task.callable(run=run, context=context, **task.params)
            run.state[task.task_id] = "success"
            run.xcom.push(task.task_id, "return_value", result)
            run.outputs[task.task_id] = result
            log.info("  ✓ %-22s success", task.task_id)
            if task.branch and isinstance(result, (list, tuple)):
                run.xcom.push(task.task_id, "branch", list(result))
            return
        except TaskSkip as exc:
            run.state[task.task_id] = "skipped"
            log.info("  ○ %-22s skipped: %s", task.task_id, exc)
            return
        except BranchException as exc:
            run.state[task.task_id] = "success"
            run.xcom.push(task.task_id, "branch", exc.branches)
            run.xcom.push(task.task_id, "return_value", exc.branches)
            log.info("  ⑂ %-22s branched to %s", task.task_id, ", ".join(exc.branches))
            return
        except Exception as exc:  # noqa: BLE001 - the runner must not crash
            attempt += 1
            if attempt <= task.retries:
                log.warning(
                    "  ! %-22s attempt %d/%d failed (%s); retrying in %.1fs",
                    task.task_id,
                    attempt,
                    task.retries + 1,
                    exc,
                    task.retry_delay,
                )
                if task.retry_delay:
                    time.sleep(task.retry_delay)
                continue
            run.state[task.task_id] = "failed"
            run.xcom.push(task.task_id, "error", traceback.format_exc())
            log.error("  ✗ %-22s failed: %s", task.task_id, exc)
            return


def _print_summary(run: DagRun) -> None:
    """Print a run's outcome.

    Args:
        run: The run to summarise.
    """
    print()
    print(f"  Run summary for {run.dag.dag_id} @ {run.logical_date}")
    print("  " + "-" * 52)
    for task_id, state in run.state.items():
        marker = {
            "success": "✓",
            "failed": "✗",
            "skipped": "○",
            "upstream_failed": "⊘",
        }.get(state, "?")
        print(f"    {marker} {task_id:<22} {state}")
    print()


# --------------------------------------------------------------------------
# Environment defaults for the local run
# --------------------------------------------------------------------------

DEFAULT_VARIABLES: dict[str, Any] = {
    "gcp_project_id": "demo-project",
    "source_bucket": "demo-source-bucket",
    "target_bucket": "demo-target-bucket",
    "bq_dataset": "analytics",
    "bq_table": "orders_enriched",
    "source_bq_table": "raw.orders",
    "reject_bq_table": "analytics.orders_rejected",
    "full_load_threshold": 1000000,
    "pipeline_owner": "data-platform",
    "alert_email": "data-oncall@example.com",
}

DEFAULT_CONNECTIONS: dict[str, Any] = {
    "gcp_default": {
        "conn_id": "gcp_default",
        "host": "bigquery.googleapis.com",
        "schema": "analytics",
        "extra": '{"project_id": "demo-project", "location": "US"}',
    },
    "http_orders_api": {
        "conn_id": "http_orders_api",
        "host": "api.example.com",
        "login": "svc_account",
        "password": "not-a-real-secret",
        "extra": '{"timeout": 30, "retries": 3}',
    },
}


# --------------------------------------------------------------------------
# The pipelines
# --------------------------------------------------------------------------


def _sample_dir() -> Path:
    """Return the sample data directory.

    Returns:
        The path to ``sample_data``.
    """
    return COURSE_ROOT / "sample_data"


def _read_orders(run: DagRun, context: dict[str, Any]) -> list[str]:
    """Read the raw order CSV for the run's logical date.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The raw CSV lines.
    """
    path = _sample_dir() / "orders.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Generate it first:\n"
            f"  python resources/sample_data.py --output-dir ./sample_data"
        )
    return path.read_text(encoding="utf-8").splitlines()


def _transform(run: DagRun, context: dict[str, Any]) -> dict[str, Any]:
    """Validate and transform raw orders; push the result via XCom.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A dict with ``accepted`` and ``rejected`` counts.
    """
    from pipeline_logic import transform_orders

    raw = run.pull("read_orders") or []
    accepted, rejected = transform_orders(raw)
    run.xcom.push("transform_orders", "accepted", accepted)
    run.xcom.push("transform_orders", "rejected", rejected)
    log.info("      accepted=%d rejected=%d", len(accepted), len(rejected))
    return {"accepted_count": len(accepted), "rejected_count": len(rejected)}


def _aggregate(run: DagRun, context: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Aggregate the accepted orders per region.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The region summary.
    """
    from pipeline_logic import summarise_by_region

    accepted = run.pull("transform_orders", "accepted") or []
    summary = summarise_by_region(accepted)
    run.xcom.push("aggregate", "summary", summary)
    return summary


def _write_summary(run: DagRun, context: dict[str, Any]) -> str:
    """Write the region summary to a local CSV and a GCS-shaped path.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The path written.
    """
    from pipeline_logic import gcs_object_path, render_summary_csv
    from templating import render_template

    summary = run.pull("aggregate", "summary") or {}
    target = render_template(
        "gs://{{ var.value.target_bucket }}/{{ dag.dag_id }}/{{ ds }}/summary.csv",
        context,
    )
    bucket = context["__variables__"].get("target_bucket", "demo-target-bucket")
    local_path = (
        COURSE_ROOT
        / "out"
        / run.dag.dag_id
        / run.logical_date
        / "summary.csv"
    )
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_text(render_summary_csv(summary), encoding="utf-8")
    run.xcom.push("write_summary", "gcs_uri", target)
    run.xcom.push("write_summary", "local_path", str(local_path))
    log.info("      wrote %s", local_path)
    log.info("      would write %s", target)
    log.info("      gcs_object_path -> %s", gcs_object_path(bucket, "orders", "summary.csv"))
    return str(local_path)


def _branch_on_volume(run: DagRun, context: dict[str, Any]) -> list[str]:
    """Choose between the full-load and incremental paths.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The chosen downstream task_id.
    """
    from pipeline_logic import should_run_full_load

    stats = run.pull("transform_orders") or {}
    accepted = int(stats.get("accepted_count", 0))
    threshold = int(context["__variables__"].get("full_load_threshold", 1000000))
    chosen = "full_load" if should_run_full_load(accepted, threshold) else "incremental_load"
    log.info("      rows=%d threshold=%d -> %s", accepted, threshold, chosen)
    return [chosen]


def _full_load(run: DagRun, context: dict[str, Any]) -> str:
    """The full-load branch.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A description of what was done.
    """
    accepted = run.pull("transform_orders", "accepted") or []
    log.info("      full load: rewriting %d rows", len(accepted))
    return f"full_load: {len(accepted)} rows"


def _incremental_load(run: DagRun, context: dict[str, Any]) -> str:
    """The incremental branch.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A description of what was done.
    """
    from pipeline_logic import partition_for_date

    accepted = run.pull("transform_orders", "accepted") or []
    partition = partition_for_date(run.logical_date)
    log.info("      incremental load: appending %d rows to partition %s", len(accepted), partition)
    return f"incremental_load: {len(accepted)} rows into {partition}"


def _publish_xcom(run: DagRun, context: dict[str, Any]) -> dict[str, Any]:
    """Pull the summary from a downstream task and push it as this task's XCom.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The summary.
    """
    summary = run.pull("aggregate", "summary") or {}
    run.xcom.push("publish_summary", "summary", summary)
    return summary


# --------------------------------------------------------------------------
# DAG definitions
# --------------------------------------------------------------------------


def build_etl_dag() -> DAG:
    """Build the main ETL DAG: read → transform → aggregate → write.

    Returns:
        The DAG.
    """
    return DAG(
        "etl_to_gcs",
        tasks=[
            Task("read_orders", _read_orders, dependencies=[]),
            Task("transform_orders", _transform, dependencies=["read_orders"]),
            Task("aggregate", _aggregate, dependencies=["transform_orders"]),
            Task("write_summary", _write_summary, dependencies=["aggregate"]),
        ],
        schedule="@daily",
        start_date="2026-01-01",
        description="Read raw orders, validate them, and write a per-region summary.",
    )


def build_branching_dag() -> DAG:
    """Build the branching DAG: a volume check chooses the load strategy.

    Returns:
        The DAG.
    """
    return DAG(
        "branching_load",
        tasks=[
            Task("read_orders", _read_orders, dependencies=[]),
            Task("transform_orders", _transform, dependencies=["read_orders"]),
            Task(
                "choose_strategy",
                _branch_on_volume,
                dependencies=["transform_orders"],
                branch=True,
            ),
            Task("full_load", _full_load, dependencies=["choose_strategy"]),
            Task("incremental_load", _incremental_load, dependencies=["choose_strategy"]),
            Task(
                "finalise",
                lambda run, context: (
                    run.pull("full_load") or run.pull("incremental_load") or "nothing"
                ),
                dependencies=["full_load", "incremental_load"],
                trigger_rule="none_failed",
            ),
        ],
        schedule="@daily",
        start_date="2026-01-01",
        description="Pick a full-load or incremental strategy based on row volume.",
    )


def build_xcom_dag() -> DAG:
    """Build the XCom DAG: every task passes a value downstream via XCom.

    Returns:
        The DAG.
    """
    return DAG(
        "xcom_pipeline",
        tasks=[
            Task("read_orders", _read_orders, dependencies=[]),
            Task("transform_orders", _transform, dependencies=["read_orders"]),
            Task("aggregate", _aggregate, dependencies=["transform_orders"]),
            Task("publish_summary", _publish_xcom, dependencies=["aggregate"]),
            Task(
                "write_summary",
                _write_summary,
                dependencies=["publish_summary"],
            ),
        ],
        schedule="@daily",
        start_date="2026-01-01",
        description="Pass the summary between tasks using XCom.",
    )


def build_template_dag() -> DAG:
    """Build the templating DAG: render paths from Jinja templates.

    Returns:
        The DAG.
    """
    from templating import render_template

    def render_paths(run: DagRun, context: dict[str, Any]) -> dict[str, str]:
        """Render every path the DAG needs.

        Args:
            run: The run context.
            context: The Jinja context.

        Returns:
            The rendered paths.
        """
        paths = {
            "source": "gs://{{ var.value.source_bucket }}/{{ ds }}/orders.csv",
            "target": "gs://{{ var.value.target_bucket }}/{{ dag.dag_id }}/{{ ds }}/summary.csv",
            "bigquery": "{{ var.value.bq_dataset }}.{{ var.value.bq_table }}",
            "partition": "{{ ds_nodash }}",
            "previous": "gs://{{ var.value.source_bucket }}/{{ prev_ds }}/orders.csv",
        }
        rendered = {k: render_template(v, context) for k, v in paths.items()}
        for key, value in rendered.items():
            log.info("      %-10s -> %s", key, value)
        return rendered

    return DAG(
        "templating_paths",
        tasks=[
            Task("read_orders", _read_orders, dependencies=[]),
            Task("render_paths", render_paths, dependencies=["read_orders"]),
            Task("transform_orders", _transform, dependencies=["render_paths"]),
            Task("aggregate", _aggregate, dependencies=["transform_orders"]),
        ],
        schedule="@daily",
        start_date="2026-01-01",
        description="Render GCS and BigQuery paths from Jinja templates.",
    )


#: The DAGs the runner knows how to run.
DAGS: dict[str, Callable[[], DAG]] = {
    "etl_to_gcs": build_etl_dag,
    "branching_load": build_branching_dag,
    "xcom_pipeline": build_xcom_dag,
    "templating_paths": build_template_dag,
}


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        argv: The argument list, or None for ``sys.argv``.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dag",
        default="etl_to_gcs",
        help="The DAG to run: " + ", ".join(sorted(DAGS)) + ", or 'all'",
    )
    parser.add_argument(
        "--date",
        default="2026-01-15",
        help="The logical date of the run (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--interval-days", type=int, default=1, help="Width of the data interval in days"
    )
    parser.add_argument(
        "--out-dir", default=None, help="Override the output directory"
    )
    parser.add_argument(
        "--vars",
        default=None,
        help="JSON dict of Airflow Variables to override",
    )
    parser.add_argument(
        "--params",
        default=None,
        help="JSON dict of DAG-run params",
    )
    parser.add_argument("--list", action="store_true", help="List the available DAGs")
    parser.add_argument("--describe", action="store_true", help="Describe the DAG(s)")
    parser.add_argument("--verbose", action="store_true", help="Show each task's result")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the requested DAG(s).

    Args:
        argv: The argument list, or None for ``sys.argv``.

    Returns:
        The process exit code: 0 if every run succeeded, 1 otherwise.
    """
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    if args.list:
        print("Available DAGs:")
        for name in sorted(DAGS):
            print(f"  - {name}")
        return 0

    variables = dict(DEFAULT_VARIABLES)
    if args.vars:
        variables.update(json.loads(args.vars))

    params: dict[str, Any] = {}
    if args.params:
        params.update(json.loads(args.params))

    names = sorted(DAGS) if args.dag == "all" else [args.dag]
    unknown = [name for name in names if name not in DAGS]
    if unknown:
        print(f"Unknown DAG(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"Available: {', '.join(sorted(DAGS))}", file=sys.stderr)
        return 2

    failures = 0
    for name in names:
        dag = DAGS[name]()
        if args.describe:
            print(dag.describe())
            print()
            continue

        print(f"▶ Running {name} @ {args.date}")
        run = run_dag(
            dag,
            args.date,
            params=params,
            variables=variables,
            connections=DEFAULT_CONNECTIONS,
            verbose=True,
        )

        failed = [t for t, state in run.state.items() if state == "failed"]
        if failed:
            failures += 1
            print(f"  ✗ {name} FAILED: {', '.join(failed)}")
            for task_id in failed:
                error = run.xcom.pull(task_id, "error")
                if error:
                    print(error)
        else:
            print(f"  ✓ {name} succeeded")

        summary = run.pull("aggregate", "summary") or run.pull("publish_summary", "summary")
        if summary:
            from pipeline_logic import render_summary_csv

            print()
            print(render_summary_csv(summary))
        print()

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
