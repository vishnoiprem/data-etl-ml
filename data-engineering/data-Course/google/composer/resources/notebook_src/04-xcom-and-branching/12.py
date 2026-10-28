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

print("Join points and their dependency states:\n")
print(
    f"{'dep1':<12} {'dep2':<16} {'all_success':<14} "
    f"{'none_failed':<14} {'all_done'}"
)
print("-" * 70)
for dep1, dep2 in (
    ("success", "success"),
    ("success", "skipped"),
    ("success", "failed"),
    ("skipped", "skipped"),
):
    states = {"a": dep1, "b": dep2}
    all_success = "run" if all(s == "success" for s in states.values()) else "skip"
    none_failed = "run" if "failed" not in states.values() else "skip"
    all_done = "run"
    print(
        f"{dep1:<12} {dep2:<16} {all_success:<14} "
        f"{none_failed:<14} {all_done}"
    )
