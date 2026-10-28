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

# The same failure for a completely unknown name.
for template in (
    "{{ not_a_real_variable }}",
    "{{ dag.nonexistent_field }}",
    "{{ params.missing_param }}",
):
    try:
        render_template(template, ctx)
    except TemplateRenderError as exc:
        first_line = str(exc.cause).splitlines()[0]
        print(f"{template:<32} -> TemplateRenderError")
        print(f"{'':<32}    {first_line}")
