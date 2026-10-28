from pipeline_logic import partition_for_date, filter_rows_for_partition
from idempotent_load import apply_load

for logical_date in ("2026-01-15", "2026-01-16", "2026-02-01"):
    print(f"{logical_date} -> partition decorator {partition_for_date(logical_date)}")

print()

# A destination holding three daily partitions.
existing = {
    "AMER": {"order_count": 318.0, "revenue_eur": 113592.19},
    "APAC": {"order_count": 285.0, "revenue_eur": 108194.92},
}

incoming = {
    "AMER": {"order_count": 300.0, "revenue_eur": 101000.00},
    "APAC": {"order_count": 260.0, "revenue_eur": 99000.00},
}

# Scoped replace: only the regions in this partition's scope are touched.
scoped = apply_load(existing, incoming, mode="truncate", partitions=["AMER"])
print("after a scoped replace of AMER only:")
for region in sorted(scoped):
    b = scoped[region]
    print(f"  {region:<6} count={b['order_count']:>7.1f}  revenue={b['revenue_eur']:>12.2f}")
print()
print("APAC survived because it was outside the scope.")
print("That is the whole point of a partition-scoped truncate.")
