from dedup_load import dedup_rows
from pipeline_logic import dedup_key, transform_orders
from pathlib import Path

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent

SAMPLE_DIR = COURSE_ROOT / "sample_data"
lines = (SAMPLE_DIR / "orders.csv").read_text(encoding="utf-8").splitlines()
accepted, _ = transform_orders(lines)

print("dedup_key('ORD-00042', '20260115') =", dedup_key("ORD-00042", "20260115"))
print()

partition = "20260115"
rows = [
    {"order_id": "ORD-1", "amount_eur": 100.0, "version": 1},
    {"order_id": "ORD-2", "amount_eur": 200.0, "version": 1},
    {"order_id": "ORD-1", "amount_eur": 150.0, "version": 2},
]

result = dedup_rows(rows, partition)
print(f"input rows : {len(rows)}")
print(f"output rows: {len(result)}")
for row in result:
    print(f"  {row}")
print()

print("The duplicate ORD-1 collapsed to its LAST version.")
print("Keys are stable, so running dedup_rows again changes nothing:")
print("  idempotent:", dedup_rows(result, partition) == result)
