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

from pipeline_logic import gcs_object_path

dag = local_runner.DAGS["templating_paths"]()
run = local_runner.run_dag(
    dag,
    logical_date="2026-01-15",
    variables=local_runner.DEFAULT_VARIABLES,
    connections=local_runner.DEFAULT_CONNECTIONS,
)

rendered = run.pull("render_paths")
print("Rendered by the templating DAG:")
for key, value in rendered.items():
    print(f"  {key:<10} {value}")
print()
print("States:", run.state)
