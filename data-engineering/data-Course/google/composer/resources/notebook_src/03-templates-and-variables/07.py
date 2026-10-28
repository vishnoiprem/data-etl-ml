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

import dag_config

print("DEFAULT_VARIABLES:")
for key, value in sorted(local_runner.DEFAULT_VARIABLES.items()):
    print(f"  {key:<22} {value!r}")

print()
print("DEFAULT_CONNECTIONS:")
for name, spec in sorted(local_runner.DEFAULT_CONNECTIONS.items()):
    print(f"  {name}:")
    for field, value in sorted(spec.items()):
        print(f"      {field:<12} {value!r}")

print()
print("The layering, as the course's DAG files express it:\n")
for name in (
    "GCP_PROJECT_ID", "SOURCE_BUCKET", "TARGET_BUCKET",
    "BQ_DATASET", "BQ_TABLE", "FULL_LOAD_THRESHOLD",
):
    print(f"  {name:<20} = {getattr(dag_config, name)!r}")

print()
print("Notice: these are TEMPLATE STRINGS, not values. They are rendered")
print("at run time against the context. That is what makes the same DAG")
print("file work in dev and prod without editing.")
