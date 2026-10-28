from sensor_conditions import source_is_ready

from pathlib import Path

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent

SAMPLE_DIR = COURSE_ROOT / "sample_data"

orders = (SAMPLE_DIR / "orders.csv").read_text(encoding="utf-8").splitlines()
malformed = (SAMPLE_DIR / "malformed_orders.csv").read_text(encoding="utf-8").splitlines()

print(f"orders.csv lines          : {len(orders)}")
print(f"malformed_orders.csv lines: {len(malformed)}")
print()

# The readiness condition, evaluated against real data.
print("source_is_ready(orders, expected_rows=1245, reject_threshold=0) ->",
      source_is_ready(orders, expected_rows=1245, reject_threshold=0))
print("source_is_ready(orders, expected_rows=2000, reject_threshold=0) ->",
      source_is_ready(orders, expected_rows=2000, reject_threshold=0))
print("source_is_ready(malformed, expected_rows=0, reject_threshold=0) ->",
      source_is_ready(malformed, expected_rows=0, reject_threshold=0))
print("source_is_ready(malformed, expected_rows=0, reject_threshold=1) ->",
      source_is_ready(malformed, expected_rows=0, reject_threshold=1))
