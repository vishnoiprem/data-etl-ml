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

# A pull with the wrong key returns None.
wrong = run.pull("produce", "partiton")     # note the typo
print(f"pull with a typo'd key -> {wrong!r}  (no exception raised)")

# The safe form: pull with an explicit default.
safe = run.pull("produce", "partiton", default="MISSING")
print(f"pull with a default     -> {safe!r}")

# The safest form: check it.
value = run.pull("produce", "partition")
if value is None:
    raise ValueError("partition was not pushed by 'produce'")
print(f"checked pull            -> {value!r}")
