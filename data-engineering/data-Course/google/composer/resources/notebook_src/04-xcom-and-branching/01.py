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

import inspect

print("XCom interface in the mini-runner:\n")
for name in ("push", "pull", "all_for"):
    method = getattr(local_runner.XCom, name)
    params = ", ".join(p for p in inspect.signature(method).parameters if p != "self")
    print(f"  {name}({params})")

print()
print("DagRun.pull:")
print(f"  {inspect.signature(local_runner.DagRun.pull)}")
print()
print("Note the default: key='return_value', default=None.")
print("That default is the single most common XCom bug - a pull with the")
print("wrong key returns None, not an error, and the failure surfaces")
print("somewhere else entirely.")
