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

from templating import build_context

ctx = build_context(
    dag_id="etl_to_gcs",
    task_id="aggregate",
    logical_date="2026-01-15",
    run_id="scheduled__2026-01-15T00:00:00+00:00",
    variables=local_runner.DEFAULT_VARIABLES,
    connections=local_runner.DEFAULT_CONNECTIONS,
    params={"audience": "data-engineers"},
)

print("Every key in the context:\n")
for key in sorted(ctx):
    value = ctx[key]
    if key.startswith("__"):
        print(f"  {key:<22} <internal: {len(value)} entries>")
    elif isinstance(value, dict):
        print(f"  {key:<22} {value}")
    else:
        print(f"  {key:<22} {value!r}")
