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

LAYER = (
    "{{ params.bucket | default(var.value.gcs_bucket | default('hard-coded-bucket')) }}"
)

print("Layer 1 - nothing set:")
ctx = build_context(logical_date="2026-01-15")
print(f"  {render_template(LAYER, ctx)}")
print()

print("Layer 2 - Variable set:")
ctx = build_context(logical_date="2026-01-15", variables={"gcs_bucket": "var-bucket"})
print(f"  {render_template(LAYER, ctx)}")
print()

print("Layer 3 - Variable AND param set (param wins):")
ctx = build_context(
    logical_date="2026-01-15",
    variables={"gcs_bucket": "var-bucket"},
    params={"bucket": "param-bucket"},
)
print(f"  {render_template(LAYER, ctx)}")
