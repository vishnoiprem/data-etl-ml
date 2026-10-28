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

# Cross-check: the templated path equals the programmatically-built path.
templated = rendered["target"]
programmatic = gcs_object_path(
    local_runner.DEFAULT_VARIABLES["target_bucket"],
    "etl_to_gcs",
    f"{run.logical_date}/summary.csv",
)

print(f"  templated     : {templated}")
print(f"  programmatic  : {programmatic}")
print(f"  agree?        : {templated == programmatic}")
print()
print("The two builders compose the path differently: the templated form")
print("puts the date as its own path segment, while gcs_object_path treats")
print("the prefix as one path. That is exactly why you test such pairs")
print("rather than assume they agree.")
print()
print(f"  templated target    : {rendered['target']}")
print(f"  templated partition : {rendered['partition']}")
print(f"  templated source    : {rendered['source']}")
