from pathlib import Path
import sys

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent
sys.path.insert(0, str(COURSE_ROOT / "project" / "core"))
sys.path.insert(0, str(COURSE_ROOT / "project"))

from pipeline_logic import transform_orders, summarise_by_region

SAMPLE_DIR = COURSE_ROOT / "sample_data"
orders = (SAMPLE_DIR / "orders.csv").read_text(encoding="utf-8").splitlines()
malformed = (SAMPLE_DIR / "malformed_orders.csv").read_text(encoding="utf-8").splitlines()

# --- the happy path: exact equality, not "close enough" --------------------
accepted, rejected = transform_orders(orders)
summary = summarise_by_region(accepted)

EXPECTED_SUMMARY = {
    "AMER": {"order_count": 318, "revenue_eur": 113592.19},
    "APAC": {"order_count": 285, "revenue_eur": 108194.92},
    "EMEA": {"order_count": 322, "revenue_eur": 118423.22},
    "LATAM": {"order_count": 320, "revenue_eur": 110646.18},
}

assert summary == EXPECTED_SUMMARY, f"summary changed: {summary}"
assert len(accepted) == 1245
assert len(rejected) == 0
print("PASS: summary matches the expected value exactly.")
print()

# --- the unhappy path: assert on the reason codes ------------------------
accepted_bad, rejected_bad = transform_orders(malformed)
reasons = [row["reason"] for row in rejected_bad]

print(f"malformed rows rejected: {len(rejected_bad)}")
for row in rejected_bad:
    print(f"  reason={row['reason']:<20} detail={row['detail']}")

assert len(rejected_bad) == len(malformed) - 1
assert all(reason for reason in reasons), "every rejection needs a reason"
assert len(set(reasons)) == len(reasons), "each malformed row has a distinct reason"

print()
print("PASS: every rejection carries a specific reason code.")
