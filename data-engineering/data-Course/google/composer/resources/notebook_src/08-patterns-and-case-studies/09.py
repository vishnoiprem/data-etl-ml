"""Conditional execution, run in the mini-runner.

Two DAGs are built:

  * `patterns_branch` — a BranchOperator that chooses between two paths,
    with a join that survives a skipped branch.
  * `patterns_shortcircuit` — a ShortCircuitOperator that stops the whole
    pipeline when there is nothing to do.
"""

from local_runner import DAG, Task, TaskSkip

#: The branch decision, from project/core/pipeline_logic.py.
from pipeline_logic import should_run_full_load


def count_rows(run, context):
    """Count the rows available for this run.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The row count.
    """
    raw = run.pull("read_orders") or []
    accepted, _ = transform_orders(raw)
    return len(accepted)


def choose_strategy(run, context):
    """Choose between the full-load and incremental paths.

    The return value is the list of task_ids that should run. Everything
    else downstream is skipped — that is the branch's whole contract.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A one-element list naming the task to run.
    """
    row_count = int(run.pull("count_rows") or 0)
    threshold = int(context["__variables__"].get("full_load_threshold", 1_000_000))
    force = bool(context["params"].get("force_full_load", False))
    chosen = "full_load" if (should_run_full_load(row_count, threshold) or force) \
        else "incremental_load"
    print(f"      rows={row_count} threshold={threshold} force={force} -> {chosen}")
    return [chosen]


def full_load(run, context):
    """The full-load branch.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A description of what was done.
    """
    return "full_load"


def incremental_load(run, context):
    """The incremental branch.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A description of what was done.
    """
    return f"incremental_load:{context['ds_nodash']}"


def join_branches(run, context):
    """The join after the branch.

    `trigger_rule="none_failed"` is what makes this work: a *skipped*
    dependency is not a failure, so the join still runs.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        The chosen branch's result.
    """
    return run.pull("full_load") or run.pull("incremental_load") or "nothing"


def short_circuit(run, context):
    """Stop the pipeline when there is nothing to process.

    A `ShortCircuitOperator` skips *itself* and everything downstream.
    Returning False raises `TaskSkip` — the mini-runner's equivalent of
    Airflow's `AirflowSkipException`.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        True when the pipeline should continue.

    Raises:
        TaskSkip: When the pipeline should stop.
    """
    row_count = int(run.pull("count_rows") or 0)
    if row_count == 0:
        print("      no rows — short-circuiting the rest of the DAG")
        raise TaskSkip("no rows to process")
    return True


def after_short_circuit(run, context):
    """A task that only runs when the short circuit did not fire.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        A description.
    """
    return "published"


def build_branch_dag():
    """Build the branching DAG.

    Returns:
        The DAG.
    """
    return DAG(
        "patterns_branch",
        tasks=[
            Task("read_orders", read_orders),
            Task("count_rows", count_rows, dependencies=["read_orders"]),
            Task("choose_strategy", choose_strategy, dependencies=["count_rows"],
                 branch=True),
            Task("full_load", full_load, dependencies=["choose_strategy"]),
            Task("incremental_load", incremental_load, dependencies=["choose_strategy"]),
            # The join survives a skipped branch.
            Task("join_branches", join_branches,
                 dependencies=["full_load", "incremental_load"],
                 trigger_rule="none_failed"),
        ],
        schedule="@daily",
        start_date="2026-01-01",
        description="A branch with a resilient join.",
    )


def build_short_circuit_dag():
    """Build the short-circuit DAG.

    Returns:
        The DAG.
    """
    return DAG(
        "patterns_shortcircuit",
        tasks=[
            Task("read_orders", read_orders),
            Task("count_rows", count_rows, dependencies=["read_orders"]),
            Task("check_not_empty", short_circuit, dependencies=["count_rows"]),
            Task("publish", after_short_circuit, dependencies=["check_not_empty"]),
        ],
        schedule="@daily",
        start_date="2026-01-01",
        description="A short circuit that stops the pipeline when idle.",
    )


BRANCH_DAG = build_branch_dag()
SHORT_CIRCUIT_DAG = build_short_circuit_dag()
print(BRANCH_DAG.describe())
print()
print(SHORT_CIRCUIT_DAG.describe())
