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

# How much data actually fits in 48 KB?
def rows_that_fit(sample_row, limit=LIMIT_BYTES):
    """Estimate how many rows of this shape fit in the limit."""
    per_row = payload_size(sample_row)
    return limit // per_row


order_row = {
    "order_id": "o00000000",
    "customer_id": "c000914",
    "order_ts": "2026-01-15T00:54:38+00:00",
    "region": "AMER",
    "channel": "web",
    "currency": "GBP",
    "status": "complete",
    "amount": 700.97,
    "product_id": "p0173",
}

print(f"One realistic order row: {payload_size(order_row):,} bytes")
print(f"Rows that fit in 48 KB    : ~{rows_that_fit(order_row):,}")
print()
print("Our sample has 1245 accepted orders:")
print(
    "  as a full XCom payload  : "
    f"{payload_size([dict(order_row, order_id=f'o{n:08d}') for n in range(1245)]):,} bytes"
)
print()
print("So the entire accepted dataset for one day does NOT fit in one XCom.")
print("It has to go through Cloud Storage or BigQuery, with only the")
print("REFERENCE (the path) travelling via XCom.")
print()
print("Real Airflow behaviour: a value over the limit raises")
print("AirflowXComSizeLimitExceeded and the task FAILS - it does not")
print("silently truncate. That is the safe failure mode.")
