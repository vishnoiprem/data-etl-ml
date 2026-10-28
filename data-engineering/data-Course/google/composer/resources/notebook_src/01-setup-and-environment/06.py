import inspect

import local_runner

print(f"local_runner.py — {len(inspect.getsource(local_runner).splitlines())} lines\n")

# The classes that model Airflow's core objects.
for name in ("DAG", "Task", "DagRun", "XCom", "TaskSkip", "BranchException"):
    cls = getattr(local_runner, name)
    doc = (cls.__doc__ or "").strip().splitlines()[0]
    print(f"{name:<16} {doc}")

print()
print("Public functions:")
for name in sorted(
    n for n in dir(local_runner)
    if not n.startswith("_") and callable(getattr(local_runner, n))
):
    if name in ("DAG", "Task", "DagRun", "XCom"):
        continue
    print(f"  {name}()")
