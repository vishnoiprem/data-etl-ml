"""Generate the sample dataset and inspect it.

The generator lives in `resources/sample_data.py`. We import its
functions directly so the notebook is self-contained — but the script
is the canonical entry point, and it is the same code either way.

Everything here is deterministic: the generator is seeded with 42, so
the dataset is byte-identical on every run and the expected numbers in
this notebook stay correct.
"""

import importlib.util
import json
import random
from collections import Counter
from datetime import date, datetime
from pathlib import Path

# --- import resources/sample_data.py without making it a package --------
_RESOURCE_PATH = COURSE_ROOT / "resources" / "sample_data.py"
_spec = importlib.util.spec_from_file_location("sample_data", _RESOURCE_PATH)
sample_data = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sample_data)

SAMPLE_DIR = COURSE_ROOT / "sample_data"
TARGET_DATE = "2026-01-15"

print("=" * 78)
print("GENERATING THE SAMPLE DATA")
print("=" * 78)
print()

target = datetime.strptime(TARGET_DATE, "%Y-%m-%d").date()
rng = random.Random(sample_data.SEED)

orders = sample_data.generate_orders(5000, target, rng=rng)
malformed = sample_data.generate_malformed_rows(5)

print(f"orders generated       : {len(orders)}")
print(f"malformed rows         : {len(malformed)}")
print(f"target date            : {target.isoformat()}")
print(f"regions                : {sample_data.REGIONS}")
print(f"currencies             : {sample_data.CURRENCIES}")
print(f"statuses               : {sample_data.STATUSES}")
print()
print("The first three orders:")
for row in orders[:3]:
    print(f"  {row['order_id']}  {row['order_ts']}  {row['region']:<6} "
          f"{row['currency']}  {row['status']:<10} {row['amount']:>8.2f}")
print()

# --- the distribution, which is what the aggregation actually measures ---
print("=" * 78)
print("THE DISTRIBUTION")
print("=" * 78)
print()

region_counts = Counter(r["region"] for r in orders)
status_counts = Counter(r["status"] for r in orders)
currency_counts = Counter(r["currency"] for r in orders)

print("orders by region:")
for region in sorted(region_counts):
    print(f"  {region:<8} {region_counts[region]:>6}")
print()
print("orders by status:")
for status in sorted(status_counts):
    print(f"  {status:<10} {status_counts[status]:>6}")
print()
print("orders by currency:")
for currency in sorted(currency_counts):
    print(f"  {currency:<5} {currency_counts[currency]:>6}")
print()

# --- every timestamp falls inside one half-open interval ---------------
timestamps = [r["order_ts"] for r in orders]
print("timestamp range:")
print(f"  earliest : {min(timestamps)}")
print(f"  latest   : {max(timestamps)}")
print(f"  all on {target.isoformat()}: "
      f"{all(ts.startswith(target.isoformat()) for ts in timestamps)}")
print()
print("That matters: the whole dataset falls inside the data interval")
print(f"  [{target.isoformat()}, 2026-01-16)")
print("so the daily filter keeps every row, and the half-open boundary")
print("never splits a row between two days.")
print()

# --- the malformed rows: one per reject reason -------------------------
print("=" * 78)
print("THE MALFORMED ROWS")
print("=" * 78)
print()
for index, line in enumerate(malformed, start=1):
    print(f"  {index}. {line}")
print()
print("Each one triggers a different reject reason code. The dead-letter")
print("path is only testable if there is something to reject.")
print()

# --- write the files, exactly as the script does -----------------------
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
sample_data.write_csv(orders, SAMPLE_DIR / "orders.csv", sample_data.ORDER_FIELDS)
sample_data.write_ndjson(orders, SAMPLE_DIR / "orders.ndjson")
sample_data.write_text_lines(
    malformed, SAMPLE_DIR / "malformed_orders.csv"
)
sample_data.write_ndjson(
    list(sample_data.generate_reference_data().values()),
    SAMPLE_DIR / "product_reference.ndjson",
)

manifest = {
    "orders": len(orders),
    "malformed_rows": len(malformed),
    "reference_rows": len(sample_data.generate_reference_data()),
    "target_date": TARGET_DATE,
}
(SAMPLE_DIR / "summary.json").write_text(
    json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
)

print("files written:")
for path in sorted(SAMPLE_DIR.iterdir()):
    if path.is_file():
        print(f"  {path.name:<28} {path.stat().st_size:>9,} bytes")
print()
print("manifest:", manifest)
print()
