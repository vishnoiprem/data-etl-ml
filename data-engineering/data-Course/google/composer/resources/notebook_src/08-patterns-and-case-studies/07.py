"""Measure the loop anti-pattern against dynamic task mapping.

The loop version's width is fixed at parse time and grows with the code.
The mapped version's width is decided by the data at run time.
"""

from fanout import load_tasks, regions_to_process
from pipeline_logic import summarise_by_region, transform_orders

lines = (COURSE_ROOT / "sample_data" / "orders.csv").read_text(
    encoding="utf-8").splitlines()
accepted, _ = transform_orders(lines)
summary = summarise_by_region(accepted)

# --- the loop version: width fixed at parse time ------------------------
LOOP_REGIONS = ["AMER", "APAC", "EMEA", "LATAM"]
loop_width = len(LOOP_REGIONS)

# --- the mapped version: width decided by the data ----------------------
mapped_width = len(load_tasks(summary, "20260115"))

print(f"regions in the data         : {regions_to_process(summary)}")
print(f"loop version width          : {loop_width} tasks (fixed at parse time)")
print(f"mapped version width        : {mapped_width} tasks (decided at run time)")
print()

# --- what happens when a fifth region appears --------------------------
HYPOTHETICAL = ["AMER", "APAC", "EMEA", "LATAM", "ANTARCTICA"]
loop_after = len(HYPOTHETICAL)
mapped_after = len(HYPOTHETICAL)
print("Scenario: a fifth region appears in the source data.")
print(f"  loop version   : {loop_after} tasks — but only if someone edits the DAG file")
print(f"  mapped version : {mapped_after} tasks — automatically, from the data")
print()

# --- the metadata-database cost ---------------------------------------
# Each mapped instance is a task instance with its own row, state and logs.
print("Task instances in the metadata database per run:")
print(f"  loop version   : {loop_width} (every run, whether or not it is needed)")
print(f"  mapped version : {mapped_width} (only the ones the data needs)")
print()

# --- the max_map_length ceiling ---------------------------------------
MAX_MAP_LENGTH = 1024
print(f"Airflow's max_map_length is {MAX_MAP_LENGTH}.")
print(f"  mapping {mapped_width} regions is fine.")
print(f"  mapping per *row* over {len(accepted)} rows would be "
      f"{'OVER' if len(accepted) > MAX_MAP_LENGTH else 'under'} the limit "
      f"and is wrong anyway — map per region, not per row.")
print()

# --- the payload .expand_kwargs() consumes -----------------------------
payload = load_tasks(summary, "20260115")
print("The .expand_kwargs() payload:")
for item in payload:
    print(f"  {item}")

# A payload for .expand_kwargs() must be a list of dicts, and every dict
# must have the same keys — otherwise the mapping fails at run time.
assert isinstance(payload, list)
assert all(isinstance(item, dict) for item in payload)
assert all(set(item) == {"region", "partition"} for item in payload)
assert mapped_width == loop_width, "the sample data has the same four regions"

print()
print("PASS: the payload is a list of uniform dicts, ready for .expand_kwargs().")
