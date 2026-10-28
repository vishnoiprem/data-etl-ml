from pathlib import Path
import sys

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent
sys.path.insert(0, str(COURSE_ROOT / "project" / "core"))
sys.path.insert(0, str(COURSE_ROOT / "project"))

print("COURSE_ROOT =", COURSE_ROOT)
print("project/ present:", (COURSE_ROOT / "project").exists())
print("core/ present:", (COURSE_ROOT / "project" / "core").exists())

import local_runner
print("local_runner loaded from:", local_runner.__file__)

from pipeline_logic import transform_orders, summarise_by_region, partition_for_date
from local_runner import DAG, Task


def read_orders(run, context):
    path = COURSE_ROOT / "sample_data" / "orders.csv"
    return path.read_text(encoding="utf-8").splitlines()


def transform(run, context):
    raw = run.pull("read_orders") or []
    accepted, rejected = transform_orders(raw)
    run.xcom.push("transform", "accepted", accepted)
    return {"accepted_count": len(accepted), "rejected_count": len(rejected)}


def choose_strategy(run, context):
    """The branch task: returns the list of task_ids that should run."""
    from pipeline_logic import should_run_full_load
    stats = run.pull("transform") or {}
    accepted = int(stats.get("accepted_count", 0))
    threshold = int(context["__variables__"].get("full_load_threshold", 1_000_000))
    chosen = (
        "full_load"
        if should_run_full_load(accepted, threshold)
        else "incremental_load"
    )
    return [chosen]


def full_load(run, context):
    accepted = run.pull("transform", "accepted") or []
    return f"full_load: rewrote {len(accepted)} rows"


def incremental_load(run, context):
    accepted = run.pull("transform", "accepted") or []
    partition = partition_for_date(run.logical_date)
    return f"incremental_load: appended {len(accepted)} rows to {partition}"


def finalise(run, context):
    """The join point - depends on BOTH branches."""
    return run.pull("full_load") or run.pull("incremental_load") or "nothing"


branch_dag = DAG(
    "branching_demo",
    tasks=[
        Task("read_orders", read_orders, dependencies=[]),
        Task("transform", transform, dependencies=["read_orders"]),
        Task(
            "choose_strategy",
            choose_strategy,
            dependencies=["transform"],
            branch=True,
        ),
        Task("full_load", full_load, dependencies=["choose_strategy"]),
        Task("incremental_load", incremental_load, dependencies=["choose_strategy"]),
        Task(
            "finalise",
            finalise,
            dependencies=["full_load", "incremental_load"],
            trigger_rule="none_failed",
        ),
    ],
)

run = local_runner.run_dag(
    branch_dag,
    logical_date="2026-01-15",
    variables=local_runner.DEFAULT_VARIABLES,
)
print()
print("States:")
for task_id, state in run.state.items():
    print(f"  {task_id:<20} {state}")
print()
print("finalise ->", run.pull("finalise"))
