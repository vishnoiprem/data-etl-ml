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

print("The difference in one picture:\n")
print(f"{'logical date':<14} {'catchup=False':<16} {'catchup=True':<16}")
print("-" * 48)

no_catchup = set(
    simulate_schedule("2026-01-01", "@daily", "2026-03-01 12:00", False)
)
all_dates = simulate_schedule(
    "2026-01-01", "@daily", "2026-03-01 12:00", True
)

for date_str in all_dates:
    mark = "  (skipped)" if date_str not in no_catchup else ""
    created = "created" if date_str in no_catchup else "not created"
    print(f"{date_str:<14} {created:<16} {'created':<16}{mark}")

print()
print(f"catchup=False creates {len(no_catchup)} run(s).")
print(f"catchup=True  creates {len(all_dates)} runs.")
