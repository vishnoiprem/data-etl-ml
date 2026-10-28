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
print("core/ present:", (COURSE_ROOT / "project" / "core").exists())

import importlib.util

for name in ("airflow", "google.cloud.bigquery"):
    found = importlib.util.find_spec(name) is not None
    print(f"{name:<28} importable: {found}")

print()
print("This notebook models sensor semantics in plain Python.")
print("No Airflow import is required, and none is attempted.")
