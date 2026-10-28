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

print("logical_date_window('2026-01-15')")
print("  ->", logical_date_window("2026-01-15"))
print()
print("The window is half-open: start is INCLUDED, end is EXCLUDED.\n")

for days in (1, 7, 30):
    start, end = logical_date_window("2026-01-15", data_interval_days=days)
    print(f"  interval_days={days:<3} -> [{start}, {end})")

print()
print("An inclusive variant exists for systems whose filters are inclusive:")
print(
    "  include_end=True ->",
    logical_date_window("2026-01-15", include_end=True),
)
print(
    "  include_end=True ->",
    logical_date_window("2026-01-15", data_interval_days=7, include_end=True),
)
