"""Run the branch DAG three ways and the short-circuit DAG twice."""

from local_runner import run_dag

LOGICAL_DATE = "2026-01-15"

# ---------------------------------------------------------------------
# 1. The incremental path (threshold above the row count)
# ---------------------------------------------------------------------
print("=" * 70)
print("BRANCH: incremental path (threshold = 1,000,000)")
print("=" * 70)
inc_run = run_dag(BRANCH_DAG, LOGICAL_DATE,
                  variables={"full_load_threshold": 1_000_000}, verbose=True)
print("join result:", inc_run.pull("join_branches"))
assert inc_run.state["full_load"] == "skipped", inc_run.state
assert inc_run.state["incremental_load"] == "success", inc_run.state
assert inc_run.state["join_branches"] == "success", inc_run.state
print("PASS: the un-chosen branch was skipped and the join still ran.")
print()

# ---------------------------------------------------------------------
# 2. The full-load path (threshold below the row count)
# ---------------------------------------------------------------------
print("=" * 70)
print("BRANCH: full-load path (threshold = 100)")
print("=" * 70)
full_run = run_dag(BRANCH_DAG, LOGICAL_DATE,
                   variables={"full_load_threshold": 100}, verbose=True)
print("join result:", full_run.pull("join_branches"))
assert full_run.state["full_load"] == "success", full_run.state
assert full_run.state["incremental_load"] == "skipped", full_run.state
assert full_run.state["join_branches"] == "success", full_run.state
print("PASS: the other branch was skipped and the join still ran.")
print()

# ---------------------------------------------------------------------
# 3. The join without a resilient trigger rule — the classic bug
# ---------------------------------------------------------------------
print("=" * 70)
print("BRANCH: the same DAG with trigger_rule='all_success' (the bug)")
print("=" * 70)
from local_runner import DAG, Task  # noqa: E402  (needed for the broken copy)

buggy = DAG(
    "patterns_branch_buggy",
    tasks=[
        Task("read_orders", read_orders),
        Task("count_rows", count_rows, dependencies=["read_orders"]),
        Task("choose_strategy", choose_strategy, dependencies=["count_rows"],
             branch=True),
        Task("full_load", full_load, dependencies=["choose_strategy"]),
        Task("incremental_load", incremental_load, dependencies=["choose_strategy"]),
        # The bug: the default trigger rule.
        Task("join_branches", join_branches,
             dependencies=["full_load", "incremental_load"]),
    ],
)
buggy_run = run_dag(buggy, LOGICAL_DATE,
                    variables={"full_load_threshold": 100}, verbose=True)
print("join result:", buggy_run.pull("join_branches"))
assert buggy_run.state["join_branches"] == "skipped", buggy_run.state
print("PASS: the join never ran. That is the 'my downstream task silently")
print("      never runs' bug — the DAG looks correct and does nothing.")
print()

# ---------------------------------------------------------------------
# 4. Short circuit: the pipeline stops when there is nothing to do
# ---------------------------------------------------------------------
print("=" * 70)
print("SHORT CIRCUIT: with data")
print("=" * 70)
sc_run = run_dag(SHORT_CIRCUIT_DAG, LOGICAL_DATE, verbose=True)
assert sc_run.state["check_not_empty"] == "success", sc_run.state
assert sc_run.state["publish"] == "success", sc_run.state
print("PASS: the pipeline continued.")
print()

print("=" * 70)
print("SHORT CIRCUIT: without data")
print("=" * 70)


def read_nothing(run, context):
    """Read zero rows, so the short circuit fires.

    Args:
        run: The run context.
        context: The Jinja context.

    Returns:
        An empty list.
    """
    return []


empty_dag = DAG(
    "patterns_shortcircuit_empty",
    tasks=[
        Task("read_orders", read_nothing),
        Task("count_rows", count_rows, dependencies=["read_orders"]),
        Task("check_not_empty", short_circuit, dependencies=["count_rows"]),
        Task("publish", after_short_circuit, dependencies=["check_not_empty"]),
    ],
)
empty_run = run_dag(empty_dag, LOGICAL_DATE, verbose=True)
assert empty_run.state["check_not_empty"] == "skipped", empty_run.state
assert empty_run.state["publish"] == "skipped", empty_run.state
print()
print("PASS: the short circuit skipped itself AND everything downstream.")
print("      Compare with the branch: a branch skips its *siblings*, not itself.")
