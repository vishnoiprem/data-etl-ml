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

from local_runner import DAG, Task

# 1. A typo in a dependency name.
try:
    DAG(
        "typo_dag",
        tasks=[
            Task("read_orders", lambda run, context: None, dependencies=[]),
            Task(
                "transform",
                lambda run, context: None,
                dependencies=["transform_orders"],
            ),
        ],
    )
except ValueError as exc:
    print("REJECTED unknown dependency:")
    print(f"  {exc}")
print()

# 2. A cycle: a -> b -> a
try:
    DAG(
        "cyclic_dag",
        tasks=[
            Task("a", lambda run, context: None, dependencies=["b"]),
            Task("b", lambda run, context: None, dependencies=["a"]),
        ],
    )
except ValueError as exc:
    print("REJECTED cycle:")
    print(f"  {exc}")
