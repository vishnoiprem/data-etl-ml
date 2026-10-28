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

from templating import TemplateRenderError

ctx = build_context(
    dag_id="etl_to_gcs",
    logical_date="2026-01-15",
    connections=local_runner.DEFAULT_CONNECTIONS,
)

# A missing connection raises, like everything else.
try:
    render_template("{{ conn.no_such_conn.host }}", ctx)
except TemplateRenderError as exc:
    print("Missing connection -> TemplateRenderError")
    print("  " + str(exc.cause).splitlines()[0])

# A missing FIELD on an existing connection also raises.
try:
    render_template("{{ conn.gcp_default.password }}", ctx)
except TemplateRenderError as exc:
    print()
    print("Missing field on an existing connection -> TemplateRenderError")
    print("  " + str(exc.cause).splitlines()[0])
