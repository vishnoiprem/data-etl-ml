from idempotent_load import apply_load

# A destination table that already holds yesterday's totals.
existing = {
    "AMER": {"order_count": 300.0, "revenue_eur": 100000.0},
    "APAC": {"order_count": 250.0, "revenue_eur": 90000.0},
}

incoming = {
    "AMER": {"order_count": 318.0, "revenue_eur": 113592.19},
    "APAC": {"order_count": 285.0, "revenue_eur": 108194.92},
}


def show(table, label):
    print(label)
    for region in sorted(table):
        bucket = table[region]
        print(f"  {region:<6} count={bucket['order_count']:>7.1f}  revenue={bucket['revenue_eur']:>12.2f}")
    print()


# --- append ---------------------------------------------------------------
appended = apply_load(existing, incoming, mode="append")
appended_twice = apply_load(appended, incoming, mode="append")
show(appended, "append, once:")
show(appended_twice, "append, twice:")

doubled = appended_twice["AMER"]["revenue_eur"] / appended["AMER"]["revenue_eur"]
print(f"revenue multiplier after one extra run: {doubled:.2f}x")
print("Append is NOT idempotent: a retry silently doubles the revenue.")
print()

# --- truncate -------------------------------------------------------------
truncated = apply_load(existing, incoming, mode="truncate")
truncated_twice = apply_load(truncated, incoming, mode="truncate")
show(truncated, "truncate, once:")
show(truncated_twice, "truncate, twice:")

print("truncate is idempotent:", truncated == truncated_twice)
