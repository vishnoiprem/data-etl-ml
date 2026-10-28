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

from templating import render_template, TemplateRenderError

ctx = build_context(
    dag_id="etl_to_gcs",
    logical_date="2026-01-15",
    variables=variables,
)

# A typo in a Variable name.
bad_template = "gs://{{ var.value.source_bukcet }}/{{ ds }}/orders.csv"

try:
    render_template(bad_template, ctx)
except TemplateRenderError as exc:
    print("TemplateRenderError raised.\n")
    print(f"  template : {exc.template}")
    print(f"  cause    : {type(exc.cause).__name__}")
    print()
    print("The underlying Jinja error:")
    print("  " + str(exc.cause))
