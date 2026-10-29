"""Run both fan-out DAGs and compare their results."""

from local_runner import run_dag

LOGICAL_DATE = "2026-01-15"

print("=" * 70)
print("STATIC FAN-OUT")
print("=" * 70)
static_run = run_dag(STATIC_FANOUT_DAG, LOGICAL_DATE, verbose=True)
print("join result:", static_run.pull("join_regions"))
print()

print("=" * 70)
print("DYNAMIC (MAPPED) FAN-OUT")
print("=" * 70)
mapped_run = run_dag(MAPPED_DAG, LOGICAL_DATE, verbose=True)
print("join result:", mapped_run.pull("join_regions"))
print()

# --- the two must agree -----------------------------------------------
static_join = static_run.pull("join_regions")
mapped_join = mapped_run.pull("join_regions")
assert static_join == mapped_join, f"static {static_join} != mapped {mapped_join}"
assert mapped_join["joined"] == 4, f"expected 4 regions, got {mapped_join}"
print("PASS: static and dynamic fan-out produce identical joins.")
print()

# --- the mapped task's instances ---------------------------------------
elements = mapped_run.pull("build_load_tasks")
print(f"mapped instances created at run time: {len(elements)}")
for index, element in enumerate(elements):
    print(f"  transform_region[{index}]  {element}")
print()
print("In Airflow these appear in the UI as transform_region[0], [1], ...")
print("Each is a separate task instance with its own state and logs.")
