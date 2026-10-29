"""Idempotency and backfill safety, proven end to end.

Three scenarios:

  1. Run the pipeline twice -> the same table.
  2. Backfill a date -> the same table as the original run.
  3. Use the wrong write mode -> plausible-looking wrong numbers.

Scenario 3 is the reason scenario 1 is worth testing.
"""

from idempotent_load import apply_load
from dedup_load import dedup_rows
from pipeline_logic import dedup_key, partition_for_date

PARTITION = partition_for_date(TARGET_DATE)
BACKFILL_DATES = ["2026-01-08", "2026-01-09", "2026-01-10", "2026-01-11"]

print("=" * 78)
print("SCENARIO 1: RUN IT TWICE")
print("=" * 78)
print()

# The BigQuery table, modelled as a dict of partitions -> rows.
table: dict[str, list[dict]] = {}

run_one = apply_load(table, accepted, mode="truncate", partitions=[PARTITION])
table = run_one
summary_one = summarise_by_region(table[PARTITION])

print(f"partition          : {PARTITION}")
print(f"rows after run 1   : {len(table[PARTITION])}")
print(render_summary_csv(summary_one), end="")

run_two = apply_load(table, accepted, mode="truncate", partitions=[PARTITION])
summary_two = summarise_by_region(run_two[PARTITION])

print(f"rows after run 2   : {len(run_two[PARTITION])}")
print(render_summary_csv(summary_two), end="")

assert summary_one == summary_two, "the second run changed the table"
assert summary_one == EXPECTED, "the table does not match the expected summary"
print()
print("PASS: run 2 produced exactly the same table as run 1.")
print()

# --------------------------------------------------------------------------
print("=" * 78)
print("SCENARIO 2: THE BACKFILL")
print("=" * 78)
print()

backfill_table: dict[str, list[dict]] = {}

print(f"{'date':<14} {'partition':<12} {'rows':>6} {'summary matches the original':>28}")
print("-" * 66)

for date in BACKFILL_DATES:
    part = partition_for_date(date)
    backfill_table = apply_load(
        backfill_table, accepted, mode="truncate", partitions=[part]
    )
    part_summary = summarise_by_region(backfill_table[part])
    matches = part_summary == EXPECTED
    print(f"{date:<14} {part:<12} {len(backfill_table[part]):>6} "
          f"{str(matches):>28}")
    assert matches, f"backfill of {date} produced a different summary"

assert len(backfill_table) == len(BACKFILL_DATES)
print()
print("PASS: every backfilled date produced the same summary, and each")
print("      date wrote to its OWN partition.")
print()
print("The partitions are distinct:")
for part in sorted(backfill_table):
    print(f"  {part}  {len(backfill_table[part])} rows")
print()
print("That is the property that makes a backfill safe: a re-run of the")
print("10th replaces the 10th's partition and touches nothing else.")
print()

# --------------------------------------------------------------------------
print("=" * 78)
print("SCENARIO 3: THE WRONG WRITE MODE")
print("=" * 78)
print()

# The same data, loaded in append mode, three times: the original run,
# plus two backfills that also append.
append_table: dict[str, list[dict]] = {}
append_table = apply_load(append_table, accepted, mode="append",
                          partitions=[PARTITION])
append_table = apply_load(append_table, accepted, mode="append",
                          partitions=[PARTITION])
append_table = apply_load(append_table, accepted, mode="append",
                          partitions=[PARTITION])

append_summary = summarise_by_region(append_table[PARTITION])
correct_summary = summarise_by_region(
    apply_load({}, accepted, mode="truncate", partitions=[PARTITION])[PARTITION]
)

print("after three appends:")
for region in sorted(append_summary):
    got = append_summary[region]
    want = correct_summary[region]
    print(f"  {region:<8} count={int(got['order_count']):>5} "
          f"revenue={got['revenue_eur']:>12,.2f}   "
          f"(correct: {int(want['order_count']):>4} / {want['revenue_eur']:>10,.2f})")
print()

ratio = append_summary["AMER"]["revenue_eur"] / correct_summary["AMER"]["revenue_eur"]
print(f"revenue ratio: {ratio:.2f}x")
assert abs(ratio - 3.0) < 1e-9, ratio

print()
print("The numbers are 3x too large — and they still look plausible.")
print("3x is a big enough error to be noticed. 1.02x is not.")
print()
print("Now the same three writes with WRITE_TRUNCATE:")
truncate_table: dict[str, list[dict]] = {}
for _ in range(3):
    truncate_table = apply_load(truncate_table, accepted, mode="truncate",
                                partitions=[PARTITION])
truncate_summary = summarise_by_region(truncate_table[PARTITION])

assert truncate_summary == correct_summary, "truncate was not idempotent"
print(render_summary_csv(truncate_summary), end="")
print()
print("PASS: truncate is idempotent; append is not.")
print()

# --------------------------------------------------------------------------
print("=" * 78)
print("THE DEDUP PATH — idempotency without truncation")
print("=" * 78)
print()

# A dataset with one duplicated order — the shape you get when a producer
# replays a file.
rows_with_duplicate = list(accepted)
duplicate = dict(accepted[0])
duplicate["amount_eur"] = round(duplicate["amount_eur"] + 100.0, 2)
rows_with_duplicate.append(duplicate)

print(f"rows in                : {len(rows_with_duplicate)}")
deduped = dedup_rows(rows_with_duplicate, PARTITION)
print(f"rows after dedup       : {len(deduped)}")
print(f"the duplicate's key    : {dedup_key(accepted[0]['order_id'], PARTITION)}")
print()

assert len(deduped) == len(accepted), "dedup removed the wrong number of rows"

# Dedup keeps the LAST row for a key.
by_key = {r["order_id"]: r for r in deduped}
assert by_key[accepted[0]["order_id"]]["amount_eur"] == duplicate["amount_eur"], \
    "dedup did not keep the later row"

deduped_again = dedup_rows(deduped, PARTITION)
assert len(deduped_again) == len(deduped), "dedup is not idempotent"

print("PASS: dedup removed the duplicate, kept the later row, and is")
print("      itself idempotent.")
print()

# The key must be partition-scoped, or a backfill would delete a
# legitimate row from a different day.
key_jan_15 = dedup_key("o00000001", "20260115")
key_jan_16 = dedup_key("o00000001", "20260116")
print(f"key in partition 20260115: {key_jan_15}")
print(f"key in partition 20260116: {key_jan_16}")
assert key_jan_15 != key_jan_16
print()
print("PASS: the identity is (partition, order_id) — stable, and")
print("      data-derived. A load-time timestamp would make a retry")
print("      produce different rows, which defeats deduplication.")
print()

# --------------------------------------------------------------------------
print("=" * 78)
print("THE WHOLE CHAIN, TWICE")
print("=" * 78)
print()

chain_table: dict[str, list[dict]] = {}
results = []
for attempt in (1, 2):
    staged = apply_load({}, accepted, mode="truncate", partitions=[PARTITION])
    final = apply_load(chain_table, staged[PARTITION], mode="truncate",
                       partitions=[PARTITION])
    chain_table = final
    results.append(summarise_by_region(chain_table[PARTITION]))

assert results[0] == results[1], "the chain is not idempotent"
assert results[0] == EXPECTED

print("run 1 == run 2 :", results[0] == results[1])
for region in sorted(results[0]):
    bucket = results[0][region]
    print(f"  {region:<8} order_count={int(bucket['order_count']):<6} "
          f"revenue_eur={bucket['revenue_eur']:.2f}")
print()
print("PASS: the pipeline is idempotent. A retry is a no-op, and a")
print("      backfill is safe.")
print()
