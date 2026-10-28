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


def make_dag(rule):
    return DAG(
        f"rule_{rule}",
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
            Task(
                "finalise",
                finalise,
                dependencies=["full_load", "incremental_load"],
                trigger_rule=rule,
            ),
        ],
    )


print(f"{'trigger_rule':<28} {'finalise state':<18} {'finalise output'}")
print("-" * 78)

for rule in ("all_success", "none_failed", "all_done", "always"):
    r = local_runner.run_dag(
        make_dag(rule),
        logical_date="2026-01-15",
        variables=local_runner.DEFAULT_VARIABLES,
    )
    print(
        f"{rule:<28} {r.state.get('finalise', '?'):<18} {r.pull('finalise')!r}"
    )
