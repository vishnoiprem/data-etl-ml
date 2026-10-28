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

from local_runner import DAG, Task, TaskSkip


def only_if_enough(run, context):
    """A short-circuit: skip everything downstream if the condition fails."""
    accepted = int((run.pull("transform") or {}).get("accepted_count", 0))
    if accepted < 100:
        raise TaskSkip(f"only {accepted} rows, need at least 100")
    return f"{accepted} rows, proceeding"


short_circuit_dag = DAG(
    "short_circuit_demo",
    tasks=[
        Task("read_orders", read_orders, dependencies=[]),
        Task("transform", transform, dependencies=["read_orders"]),
        Task("check_threshold", only_if_enough, dependencies=["transform"]),
        Task("load", full_load, dependencies=["check_threshold"]),
    ],
)

r = local_runner.run_dag(
    short_circuit_dag,
    logical_date="2026-01-15",
    variables=local_runner.DEFAULT_VARIABLES,
)
print()
print("With 1245 rows (above the threshold):")
for task_id, state in r.state.items():
    print(f"  {task_id:<20} {state}")
