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

signature = inspect.signature(local_runner.DAG.__init__)
print("DAG.__init__ parameters:\n")
for name, param in signature.parameters.items():
    if name == "self":
        continue
    default = (
        param.default
        if param.default is not inspect.Parameter.empty
        else "(required)"
    )
    print(f"  {name:<18} default={default}")
