from pathlib import Path
import sys

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent
sys.path.insert(0, str(COURSE_ROOT / "project" / "core"))
sys.path.insert(0, str(COURSE_ROOT / "project"))

RESILIENT_TRIGGER_RULES = {"none_failed", "none_failed_min_one_success", "all_done"}


def validate_dag(dag, *, require_schedule=False, max_retries=5):
    """Check a DAG against a set of structural rules.

    Args:
        dag: The DAG to validate.
        require_schedule: Whether the DAG must have a schedule.
        max_retries: The highest acceptable retry count.

    Returns:
        A list of problem strings; empty means the DAG is valid.
    """
    problems = []

    # Rule 3: joins must survive a skipped upstream.
    for task in dag.tasks:
        if len(task.upstream_task_ids) > 1 and task.trigger_rule == "all_success":
            problems.append(
                f"task '{task.task_id}' joins {sorted(task.upstream_task_ids)} "
                f"with trigger_rule='all_success' - it will be skipped if "
                f"one branch is skipped"
            )

    # Rule 4/5: bounded timeouts and retries.
    for task in dag.tasks:
        if task.timeout is None:
            problems.append(f"task '{task.task_id}' has no timeout")
        if task.retries > max_retries:
            problems.append(
                f"task '{task.task_id}' retries {task.retries} times "
                f"(max {max_retries})"
            )

    # Rule 6: schedule.
    if require_schedule and dag.schedule is None:
        problems.append("DAG has no schedule")

    return problems


# A healthy DAG.
good = DAG(
    "good_dag",
    [
        BaseOperator("extract", timeout=600, retries=2),
        BaseOperator("transform", upstream_task_ids=["extract"], timeout=600, retries=2),
        BaseOperator("load", upstream_task_ids=["transform"], timeout=1800, retries=1),
    ],
    schedule="@daily",
)

# A broken DAG: a fragile join, no timeout, absurd retries, no schedule.
bad = DAG(
    "bad_dag",
    [
        BaseOperator("branch", timeout=300, retries=0),
        BaseOperator("path_a", upstream_task_ids=["branch"], timeout=300, retries=0),
        BaseOperator("path_b", upstream_task_ids=["branch"], timeout=300, retries=0),
        BaseOperator("join", upstream_task_ids=["path_a", "path_b"],
                     trigger_rule="all_success", retries=99),
        BaseOperator("no_timeout", upstream_task_ids=["join"]),
    ],
)

print("good_dag problems:", validate_dag(good, require_schedule=True) or "none")
print()
print("bad_dag problems:")
for problem in validate_dag(bad, require_schedule=True):
    print(f"  - {problem}")
