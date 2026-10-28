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

import json

# Measure the serialised size of progressively larger XCom payloads.
LIMIT_BYTES = 48 * 1024


def payload_size(value):
    """Return the UTF-8 byte size of a value as Airflow would store it."""
    return len(json.dumps(value, default=str).encode("utf-8"))


print(
    f"Airflow's commonly-quoted XCom limit: {LIMIT_BYTES:,} bytes "
    f"({LIMIT_BYTES // 1024} KB)\n"
)
print(f"{'payload':<34} {'rows':>8} {'bytes':>10}  {'over limit?':>12}")
print("-" * 70)

cases = [
    ("a single count", 1),
    ("a partition name", 1),
    ("a list of 100 order ids", 100),
    ("a list of 1,000 order ids", 1000),
    ("a list of 5,000 order ids", 5000),
    ("a list of 20,000 order ids", 20000),
]

for label, count in cases:
    if "count" in label or "partition" in label:
        value = 1245 if "count" in label else "20260115"
        rows = 1
    else:
        value = [
            {"order_id": f"o{n:08d}", "amount": 123.45} for n in range(count)
        ]
        rows = count
    size = payload_size(value)
    over = "YES" if size > LIMIT_BYTES else "no"
    print(f"{label:<34} {rows:>8} {size:>10,}  {over:>12}")
