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

from templating import build_context

context = build_context(
    dag_id="etl_to_gcs",
    task_id="aggregate",
    logical_date="2026-01-15",
)

print(f"context for dag={context['dag']['dag_id']} task={context['task']['task_id']}")
print(f"logical_date={context['logical_date']}\n")

print("--- Date / time templates ---")
for key in (
    "ds", "ts", "ds_nodash", "prev_ds", "next_ds",
    "data_interval_start", "data_interval_end", "logical_date", "run_id",
):
    print(f"  {key:<22} {context[key]}")

print()
print("--- Object graph ---")
for key in ("dag", "task", "ti"):
    print(f"  {key:<22} {context[key]}")
