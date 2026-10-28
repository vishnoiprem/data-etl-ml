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


def choose_strategy_with_override(run, context):
    """The branch task, with an operator override."""
    from pipeline_logic import should_run_full_load
    stats = run.pull("transform") or {}
    accepted = int(stats.get("accepted_count", 0))
    threshold = int(context["__variables__"].get("full_load_threshold", 1_000_000))
    force = bool(context["params"].get("force_full_load", False))
    if force or should_run_full_load(accepted, threshold):
        return ["full_load"]
    return ["incremental_load"]


override_dag = DAG(
    "branching_override",
    tasks=[
        Task("read_orders", read_orders, dependencies=[]),
        Task("transform", transform, dependencies=["read_orders"]),
        Task(
            "choose_strategy",
            choose_strategy_with_override,
            dependencies=["transform"],
            branch=True,
        ),
        Task("full_load", full_load, dependencies=["choose_strategy"]),
        Task("incremental_load", incremental_load, dependencies=["choose_strategy"]),
        Task(
            "finalise",
            finalise,
            dependencies=["full_load", "incremental_load"],
            trigger_rule="none_failed",
        ),
    ],
)

for label, params in (
    ("automatic (1245 < 1M threshold)", {}),
    ("forced full load", {"force_full_load": True}),
):
    r = local_runner.run_dag(
        override_dag,
        logical_date="2026-01-15",
        params=params,
        variables=local_runner.DEFAULT_VARIABLES,
    )
    chosen = [
        t
        for t, s in r.state.items()
        if s == "success" and t in ("full_load", "incremental_load")
    ]
    print(
        f"{label:<36} -> {chosen[0]:<18} finalise={r.state['finalise']}"
    )
