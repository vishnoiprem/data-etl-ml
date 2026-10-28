from pathlib import Path
import sys

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent
sys.path.insert(0, str(COURSE_ROOT / "project" / "core"))
sys.path.insert(0, str(COURSE_ROOT / "project"))

# The branching DAG's shape, reconstructed from the deployable definition.
tasks = [
    BaseOperator("wait_for_upstream_data", trigger_rule="all_success", retries=3),
    BaseOperator("branch_on_volume", upstream_task_ids=["wait_for_upstream_data"]),
    BaseOperator("full_load", upstream_task_ids=["branch_on_volume"]),
    BaseOperator("incremental_load", upstream_task_ids=["branch_on_volume"]),
    BaseOperator("load_complete", upstream_task_ids=["full_load", "incremental_load"],
                 trigger_rule="none_failed"),
]

dag = DAG("branching_and_xcom", tasks, catchup=False, max_active_runs=1,
          default_args={"owner": "data-platform", "retries": 2})

# --- structure assertions ------------------------------------------------
assert dag.get_task("load_complete").trigger_rule in (
    "none_failed", "none_failed_min_one_success", "all_done"
), "the join point must survive a skipped branch"

assert dag.get_task("full_load").upstream_task_ids == {"branch_on_volume"}
assert dag.get_task("incremental_load").upstream_task_ids == {"branch_on_volume"}
assert dag.get_task("branch_on_volume").upstream_task_ids == {"wait_for_upstream_data"}
assert dag.get_task("wait_for_upstream_data").upstream_task_ids == set()

assert dag.catchup is False
assert dag.max_active_runs == 1
assert dag.default_args["retries"] >= 1

print("Structure assertions on the branching DAG:")
for task in dag.tasks:
    upstream = ", ".join(sorted(task.upstream_task_ids)) or "-"
    print(f"  {task.task_id:<24} <- {upstream:<24} trigger={task.trigger_rule}")
print()
print("PASS: join point uses 'none_failed' and survives a skipped branch.")
