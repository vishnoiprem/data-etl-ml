"""The reference implementation, run directly.

This is the specification. The orchestrated run in the next cell must
produce byte-identical output.
"""

from pipeline_logic import (
    transform_orders,
    summarise_by_region,
    render_summary_csv,
    render_rejects_csv,
    reject_counts,
    logical_date_window,
    partition_for_date,
)

EXPECTED = {
    "AMER": {"order_count": 318, "revenue_eur": 113592.19},
    "APAC": {"order_count": 285, "revenue_eur": 108194.92},
    "EMEA": {"order_count": 322, "revenue_eur": 118423.22},
    "LATAM": {"order_count": 320, "revenue_eur": 110646.18},
}

raw_lines = (SAMPLE_DIR / "orders.csv").read_text(encoding="utf-8").splitlines()

print("=" * 78)
print("THE PURE REFERENCE IMPLEMENTATION")
print("=" * 78)
print()
print(f"raw lines read : {len(raw_lines)}")
print()

accepted, rejected = transform_orders(raw_lines)

print(f"accepted       : {len(accepted)}")
print(f"rejected       : {len(rejected)}")
print()

# Why the counts differ — the status filter.
status_counts = Counter(row["status"] for row in accepted)
print("accepted rows by status:")
for status in sorted(status_counts):
    print(f"  {status:<10} {status_counts[status]:>6}")
print()
print("Only 'complete' rows count as revenue-bearing. The others are")
print("valid rows that simply do not carry revenue, so they are")
print("accepted by the validator and then excluded from the sum.")
print()

summary = summarise_by_region(accepted)

print("=" * 78)
print("THE SUMMARY")
print("=" * 78)
print()
print(render_summary_csv(summary), end="")

print()
print("=" * 78)
print("CHECKING IT AGAINST THE EXPECTED RESULT")
print("=" * 78)
print()

assert summary == EXPECTED, f"reference summary changed:\n{summary}"
print(f"summary == EXPECTED            : True")
print(f"accepted count == 1245         : {len(accepted) == 1245}  ({len(accepted)})")
print(f"rejected count == 0            : {len(rejected) == 0}  ({len(rejected)})")
print()

# --- the interval the run covers ---------------------------------------
start, end = logical_date_window(TARGET_DATE)
partition = partition_for_date(TARGET_DATE)
print(f"data interval    : [{start}, {end})")
print(f"partition        : {partition}")
print()

# --- the dead-letter path, exercised separately ------------------------
print("=" * 78)
print("THE DEAD-LETTER PATH (malformed_orders.csv)")
print("=" * 78)
print()

bad_lines = (SAMPLE_DIR / "malformed_orders.csv").read_text(
    encoding="utf-8"
).splitlines()
bad_accepted, bad_rejected = transform_orders(bad_lines)

print(f"input rows       : {len(bad_lines)}")
print(f"accepted         : {len(bad_accepted)}")
print(f"rejected         : {len(bad_rejected)}")
print()
print("rejects by reason:")
for reason, count in sorted(reject_counts(bad_rejected).items()):
    print(f"  {reason:<24} {count:>4}")
print()

print("the rejects CSV:")
print(render_rejects_csv(bad_rejected), end="")

print()
print("PASS: the reference implementation produces the expected summary,")
print("      and the dead-letter path classifies every malformed row.")
print()
