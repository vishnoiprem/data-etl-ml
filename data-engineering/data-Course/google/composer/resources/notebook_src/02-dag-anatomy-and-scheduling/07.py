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

dag = local_runner.DAGS["etl_to_gcs"]()

print(f"dag_id          : {dag.dag_id}")
print(f"schedule        : {dag.schedule}")
print(f"start_date      : {dag.start_date}")
print(f"catchup         : {dag.catchup}")
print(f"max_active_runs : {dag.max_active_runs}")
print(f"description     : {dag.description}")
print(f"tasks           : {len(dag.tasks)}")

print()
print("Downstream of 'transform_orders':")
for task_id in dag.downstream("transform_orders"):
    print(f"  -> {task_id}")
