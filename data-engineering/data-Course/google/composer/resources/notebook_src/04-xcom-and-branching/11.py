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


def explode(run, context):
    """A task that always fails."""
    raise RuntimeError("boom - simulated upstream failure")


def always_runs(run, context):
    return "cleanup ran"


print("Upstream 'explode' fails. What happens downstream?\n")
for rule in ("all_success", "none_failed", "all_done", "always"):
    d = DAG(
        f"fail_{rule}",
        tasks=[
            Task("explode", explode, dependencies=[]),
            Task(
                "downstream",
                always_runs,
                dependencies=["explode"],
                trigger_rule=rule,
            ),
        ],
    )
    r = local_runner.run_dag(d, logical_date="2026-01-15")
    print(
        f"  {rule:<28} explode={r.state['explode']:<8} "
        f"downstream={r.state['downstream']}"
    )
