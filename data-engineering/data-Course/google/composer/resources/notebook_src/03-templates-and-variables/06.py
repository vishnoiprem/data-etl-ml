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

# 1. default rescues a missing Variable.
print(
    "with default    :",
    render_template("{{ var.value.not_set | default('fallback') }}", ctx),
)

# 2. Without default, the same lookup fails.
try:
    render_template("{{ var.value.not_set }}", ctx)
except TemplateRenderError as exc:
    print(
        "without default : TemplateRenderError -",
        str(exc.cause).splitlines()[0],
    )

# 3. var.get() is the programmatic equivalent.
print("var.get()       :", ctx["__variables__"].get("not_set", "fallback"))

# 4. A missing PARAM is still an error, even with default on the wrong object.
try:
    render_template("{{ var.value.bq_dataset | default('analytics') }}", ctx)
    print("bq_dataset      : rendered fine (it exists)")
except TemplateRenderError as exc:
    print("bq_dataset      :", exc)
