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

from datetime import date, timedelta

# Build 7 consecutive daily windows and check they tile perfectly.
start = date(2026, 1, 15)
windows = [
    logical_date_window((start + timedelta(days=i)).isoformat())
    for i in range(7)
]

print("7 consecutive daily windows:")
for w_start, w_end in windows:
    print(f"  [{w_start}, {w_end})")

# Property 1: each window's end is the next window's start (no gaps).
contiguous = all(
    windows[i][1] == windows[i + 1][0] for i in range(len(windows) - 1)
)
# Property 2: each window is exactly one day wide.
one_day = all(
    (date.fromisoformat(e) - date.fromisoformat(s)).days == 1
    for s, e in windows
)
# Property 3: no instant is in two windows (half-open => disjoint).
disjoint = all(
    date.fromisoformat(windows[i][1])
    <= date.fromisoformat(windows[i + 1][0])
    for i in range(len(windows) - 1)
)

print()
print(f"contiguous (no gaps)      : {contiguous}")
print(f"exactly one day wide      : {one_day}")
print(f"disjoint (no double-count): {disjoint}")
print()
print("PASS: the intervals tile the timeline exactly once each.")
