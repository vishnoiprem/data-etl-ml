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

from pipeline_logic import should_run_full_load

print("should_run_full_load(row_count, threshold) -> row_count > threshold\n")
for rows, threshold in (
    (0, 100), (99, 100), (100, 100), (101, 100), (1_000_000, 1_000_000),
):
    print(
        f"  rows={rows:<10} threshold={threshold:<10} -> "
        f"{should_run_full_load(rows, threshold)}"
    )

print()
print("Note the strict inequality: exactly-at-threshold takes the")
print("incremental path. This is a policy decision, and because it is")
print("a pure function, it is testable at the boundary.")
