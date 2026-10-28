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

import importlib.util
print("pytest importable:", importlib.util.find_spec("pytest") is not None)
print("airflow importable:", importlib.util.find_spec("airflow") is not None)
print()

# The modules under test. None of them import Airflow.
import pipeline_logic
import templating
import fanout
import sla_logic
import sla_tracker
import sensor_conditions
import idempotent_load
import dedup_load

for module in (pipeline_logic, templating, fanout, sla_logic, sla_tracker,
               sensor_conditions, idempotent_load, dedup_load):
    print(f"  {module.__name__:<20} {module.__file__}")
