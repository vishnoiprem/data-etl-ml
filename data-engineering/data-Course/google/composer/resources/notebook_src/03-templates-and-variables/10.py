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

from templating import build_context, render_template

ctx = build_context(
    dag_id="etl_to_gcs",
    logical_date="2026-01-15",
    connections=local_runner.DEFAULT_CONNECTIONS,
)

TEMPLATES = [
    "{{ conn.gcp_default.host }}",
    "{{ conn.gcp_default.schema }}",
    "{{ conn.http_orders_api.host }}",
    "{{ conn.http_orders_api.login }}",
    "{{ conn.http_orders_api.extra_dejson.timeout }}",
    "{{ conn.http_orders_api.extra_dejson.retries }}",
    "{{ conn.gcp_default.extra_dejson.location }}",
]

for template in TEMPLATES:
    print(f"  {template:<52} -> {render_template(template, ctx)}")
print()
print("Note: conn.http_orders_api.password renders too, which is exactly")
print("why you must not put it in a log line or a templated bash command.")
