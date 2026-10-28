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

from pipeline_logic import (
    transform_orders,
    summarise_by_region,
    render_summary_csv,
    render_rejects_csv,
    reject_counts,
    logical_date_window,
    partition_for_date,
)

from local_runner import DAG, Task, _dependency_order

# A DAG written in the WRONG textual order: write_summary is declared first.
reversed_dag = DAG(
    "reversed",
    tasks=[
        Task("write_summary", lambda run, context: None, dependencies=["aggregate"]),
        Task("aggregate", lambda run, context: None, dependencies=["transform_orders"]),
        Task("transform_orders", lambda run, context: None, dependencies=["read_orders"]),
        Task("read_orders", lambda run, context: None, dependencies=[]),
    ],
)

order = _dependency_order(reversed_dag, set(reversed_dag.tasks))
print("Declaration order :", list(reversed_dag.tasks))
print("Execution order   :", order)
print()
print("Dependencies always come first, regardless of declaration order.")
print("Ties are broken by declaration order, so runs are deterministic.")
