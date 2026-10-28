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

print("The same DAG, four logical dates:\n")
print(f"{'logical date':<14} {'data interval':<34} {'accepted':>9}")
print("-" * 60)

for logical_date in ("2026-01-13", "2026-01-14", "2026-01-15", "2026-01-16"):
    run = local_runner.run_dag(demo, logical_date=logical_date)
    window = logical_date_window(logical_date)
    accepted = run.pull("transform", "accepted") or []
    states = set(run.state.values())
    status = "ok" if states == {"success"} else states
    print(
        f"{logical_date:<14} [{window[0]}, {window[1]}){'':<9} "
        f"{len(accepted):>9}  {status}"
    )

print()
print("Note: the source file is a single day's snapshot, so the accepted")
print("count is identical for every date. In a real DAG the source would")
print("be filtered to the run's data interval - that filter is what makes")
print("the logical date meaningful.")
