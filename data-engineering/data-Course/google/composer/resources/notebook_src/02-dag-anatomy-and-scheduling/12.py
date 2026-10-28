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

# A child DAG with no schedule - manual/event triggered only.
child = DAG(
    "child_pipeline",
    tasks=[
        Task("read_orders", read_orders, dependencies=[]),
        Task("transform", transform, dependencies=["read_orders"]),
    ],
    schedule=None,
    start_date="2026-01-15",
    description="Triggered by the parent, not by the clock.",
)

print(f"schedule    : {child.schedule}")
print(f"auto-runs?  : {child.schedule is not None}")
print()
print("In Composer this DAG appears in the list but has no 'Next Run' column")
print("value - it is only ever started by an explicit trigger.")
