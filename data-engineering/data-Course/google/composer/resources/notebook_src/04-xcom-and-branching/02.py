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


def produce(run, context):
    """Push several keys and return a value."""
    run.xcom.push("produce", "threshold", 1_000_000)
    run.xcom.push("produce", "partition", "20260115")
    run.xcom.push("produce", "rows", [{"order_id": "o1"}, {"order_id": "o2"}])
    return 42                      # becomes key "return_value"


def consume(run, context):
    """Pull them back."""
    returned = run.pull("produce")                      # return_value
    threshold = run.pull("produce", "threshold")
    partition = run.pull("produce", "partition")
    rows = run.pull("produce", "rows")
    return {
        "return_value": returned,
        "threshold": threshold,
        "partition": partition,
        "row_count": len(rows),
    }


demo = DAG(
    "xcom_demo",
    tasks=[
        Task("produce", produce, dependencies=[]),
        Task("consume", consume, dependencies=["produce"]),
    ],
)

run = local_runner.run_dag(demo, logical_date="2026-01-15")
print("States:", run.state)
print()
print("Consume result:", run.pull("consume"))
print()
print("Everything 'produce' pushed:")
for key, value in run.xcom.all_for("produce").items():
    print(f"  {key:<14} {value!r}")
