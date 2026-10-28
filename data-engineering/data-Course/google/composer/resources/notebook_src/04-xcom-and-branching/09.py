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

from local_runner import DAG, Task

# Rebuild the same DAG but with the default trigger rule on the join.
buggy = DAG(
    "branching_bug",
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
        # NOTE: trigger_rule left at the default "all_success".
        Task(
            "finalise",
            finalise,
            dependencies=["full_load", "incremental_load"],
        ),
    ],
)

run_buggy = local_runner.run_dag(
    buggy,
    logical_date="2026-01-15",
    variables=local_runner.DEFAULT_VARIABLES,
)
print()
print("With the DEFAULT trigger rule:")
for task_id, state in run_buggy.state.items():
    print(f"  {task_id:<20} {state}")
print()
print("finalise ->", run_buggy.pull("finalise"))
print()
print("THE BUG: one branch was skipped, so 'all_success' was not met,")
print("so finalise was skipped too. The pipeline does nothing and the")
print("DAG still reports success. This is the most common branching bug.")
