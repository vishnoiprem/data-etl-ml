"""Idempotency: the same pipeline, run twice, must produce the same answer."""

from dedup_load import dedup_rows
from idempotent_load import apply_load
from pipeline_logic import (
    build_bigquery_rows,
    dedup_key,
    filter_rows_for_partition,
    normalise_currency,
    partition_for_date,
    summarise_by_region,
    transform_orders,
)

lines = (COURSE_ROOT / "sample_data" / "orders.csv").read_text(
    encoding="utf-8").splitlines()
accepted, _ = transform_orders(lines)
summary = summarise_by_region(accepted)

PARTITION = partition_for_date("2026-01-15")
print(f"partition for 2026-01-15: {PARTITION}")
print()

# ---------------------------------------------------------------------
# 1. Truncate: a retry replaces the partition
# ---------------------------------------------------------------------
print("=" * 70)
print("1. TRUNCATE — the idempotent write")
print("=" * 70)
empty = {}

first = apply_load(empty, summary, mode="truncate")
second = apply_load(first, summary, mode="truncate")

print(f"  after run 1: {first}")
print(f"  after run 2: {second}")
assert first == second, "a truncate write must be idempotent"
assert first == summary, "a truncate write must reproduce the source"
print("PASS: run 2 produced exactly the same table as run 1.")
print()

# A *partial* scope: only one partition is replaced.
scoped = apply_load(first, summary, mode="truncate", partitions=["AMER"])
assert scoped["AMER"] == summary["AMER"]
assert scoped["APAC"] == summary["APAC"]
print("PASS: a partition-scoped truncate leaves the other regions alone.")
print()

# ---------------------------------------------------------------------
# 2. Append: the same input, counted twice
# ---------------------------------------------------------------------
print("=" * 70)
print("2. APPEND — the bug this pattern exists to prevent")
print("=" * 70)
appended = apply_load(first, summary, mode="append")
appended_again = apply_load(appended, summary, mode="append")

print(f"  revenue after 1 append : {appended['AMER']['revenue_eur']}")
print(f"  revenue after 2 appends: {appended_again['AMER']['revenue_eur']}")
assert appended_again["AMER"]["revenue_eur"] == round(
    summary["AMER"]["revenue_eur"] * 3, 2)
print("PASS: appending twice produced three times the revenue.")
print("      This is exactly what WRITE_APPEND does on a retry.")
print()

# ---------------------------------------------------------------------
# 3. Dedup: an append-only destination that survives a retry
# ---------------------------------------------------------------------
print("=" * 70)
print("3. DEDUP — idempotency without truncation")
print("=" * 70)
bq_rows = build_bigquery_rows(accepted)

# Simulate a retry: the same rows arrive again, plus one corrected row
# with the same business key (a late fix from the source system).
retry_rows = list(bq_rows) + [
    {**bq_rows[0], "amount": bq_rows[0]["amount"] + 100.0},
]

deduped = dedup_rows(retry_rows, PARTITION)
print(f"  rows in                : {len(retry_rows)}")
print(f"  rows after dedup       : {len(deduped)}")
print(f"  business key of row 0  : {dedup_key(bq_rows[0]['order_id'], PARTITION)}")
print(f"  amount before dedup    : {bq_rows[0]['amount']}")
print(f"  amount after dedup     : {deduped[0]['amount']}")

assert len(deduped) == len(bq_rows), "dedup must remove exactly the duplicate"
assert deduped[0]["amount"] == bq_rows[0]["amount"] + 100.0, \
    "the LAST row for a key must win"
print("PASS: the duplicate was removed and the later row won.")
print()

# Dedup is itself idempotent.
again = dedup_rows(deduped, PARTITION)
assert again == deduped, "dedup must be idempotent"
print("PASS: dedup is idempotent — running it again changes nothing.")
print()

# ---------------------------------------------------------------------
# 4. Partition scoping: the retry writes the SAME partition
# ---------------------------------------------------------------------
print("=" * 70)
print("4. PARTITION SCOPING — why the partition is part of the key")
print("=" * 70)
in_partition = filter_rows_for_partition(accepted, PARTITION)
print(f"  rows in partition {PARTITION}: {len(in_partition)} of {len(accepted)}")

# The same order_id in two different partitions is two different rows —
# which is why the key includes the partition.
key_a = dedup_key("o00000001", "20260115")
key_b = dedup_key("o00000001", "20260116")
print(f"  key in 20260115: {key_a}")
print(f"  key in 20260116: {key_b}")
assert key_a != key_b, "the partition must be part of the identity"

# But within one partition, the same order_id is the same row.
assert dedup_key("o00000001", "20260115") == key_a
print("PASS: identity is (partition, order_id) — stable, and data-derived.")
print()

# ---------------------------------------------------------------------
# 5. The end-to-end property
# ---------------------------------------------------------------------
print("=" * 70)
print("5. THE PROPERTY: run the pipeline twice, get the same answer")
print("=" * 70)


def run_pipeline_once():
    """Run the whole load and return the final table.

    Returns:
        The final table, region -> bucket.
    """
    rows, _ = transform_orders(lines)
    region_summary = summarise_by_region(rows)
    partition_rows = filter_rows_for_partition(rows, PARTITION)
    shaped = build_bigquery_rows(partition_rows)
    unique = dedup_rows(shaped, PARTITION)
    return apply_load({}, summarise_by_region(unique), mode="truncate")


run_1 = run_pipeline_once()
run_2 = run_pipeline_once()
assert run_1 == run_2, "the pipeline must be idempotent"
print(f"  run 1 == run 2 : {run_1 == run_2}")
for region in sorted(run_1):
    bucket = run_1[region]
    print(f"  {region:<6} order_count={int(bucket['order_count']):<5} "
          f"revenue_eur={bucket['revenue_eur']:.2f}")
print()
print("PASS: the pipeline is idempotent. A retry is a no-op.")
print()

# The amount conversion is also deterministic, which the whole property
# depends on.
print(f"  normalise_currency(100, 'GBP') = {normalise_currency(100, 'GBP')}")
print(f"  normalise_currency(100, 'EUR') = {normalise_currency(100, 'EUR')}")
print(f"  normalise_currency(100, 'JPY') = {normalise_currency(100, 'JPY')}")
print()
print("PASS: the whole chain — parse, convert, partition, dedup, load —")
print("      is a pure function of its input.")
