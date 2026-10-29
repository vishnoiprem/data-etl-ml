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

# The pure modules this notebook builds on. None of them import Airflow.
import pipeline_logic
import fanout
import sensor_conditions
import idempotent_load
import dedup_load
import local_runner

for module in (pipeline_logic, fanout, sensor_conditions, idempotent_load,
               dedup_load, local_runner):
    print(f"  {module.__name__:<20} {module.__file__}")

print()
print("The mini-runner knows these DAGs:")
for name in sorted(local_runner.DAGS):
    print(f"  - {name}")
