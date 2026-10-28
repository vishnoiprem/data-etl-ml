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

from templating import build_context

print("How prev_ds relates to the schedule cadence:")
print()
for days in (1, 7):
    ctx = build_context(logical_date="2026-01-15", data_interval_days=days)
    print(f"  data_interval_days={days}")
    print(f"    ds                  = {ctx['ds']}")
    print(f"    prev_ds             = {ctx['prev_ds']}")
    print(f"    data_interval_start = {ctx['data_interval_start']}")
    print(f"    data_interval_end   = {ctx['data_interval_end']}")
    print()

# The half-open window is directly visible in the context.
ctx = build_context(logical_date="2026-01-15")
print("Half-open interval, straight from the context:")
print(f"  [{ctx['data_interval_start']}, {ctx['data_interval_end']})")
print()
print("  start is INCLUDED, end is EXCLUDED.")
