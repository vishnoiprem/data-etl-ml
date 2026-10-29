"""The path preamble and the course tree.

Every notebook in this course starts here. It finds the course root no
matter which directory Jupyter was launched from, and puts the two
directories that matter on `sys.path`:

    project/core   — the pure business logic
    project        — the local runner
"""

from pathlib import Path
import sys

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent
sys.path.insert(0, str(COURSE_ROOT / "project" / "core"))
sys.path.insert(0, str(COURSE_ROOT / "project"))

print(f"COURSE_ROOT = {COURSE_ROOT}")
print()

# The modules this notebook uses. Importing them here — once — proves
# that they are importable with no Airflow installed and no credentials.
import pipeline_logic
import fanout
import sensor_conditions
import idempotent_load
import dedup_load
import templating
import local_runner

for module in (
    pipeline_logic,
    fanout,
    sensor_conditions,
    idempotent_load,
    dedup_load,
    templating,
    local_runner,
):
    print(f"  {module.__name__:<20} {Path(module.__file__).relative_to(COURSE_ROOT)}")

print()
print("Airflow is not installed and is not needed:")
print("  * core/*.py imports nothing from Airflow")
print("  * dags/*.py is the artefact you deploy; it is never imported here")
print()
