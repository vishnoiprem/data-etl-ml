from idempotent_load import apply_load

SUMMARY = {
    "AMER": {"order_count": 318.0, "revenue_eur": 113592.19},
    "APAC": {"order_count": 285.0, "revenue_eur": 108194.92},
    "EMEA": {"order_count": 322.0, "revenue_eur": 118423.22},
    "LATAM": {"order_count": 320.0, "revenue_eur": 110646.18},
}


def validate_load(destination, source, *, tolerance=0.01):
    """Check that the destination matches the source exactly.

    Args:
        destination: What is actually in the table.
        source: What the pipeline computed.
        tolerance: Allowed absolute difference per region.

    Returns:
        A list of human-readable violations; empty means valid.
    """
    violations = []
    for region, expected in source.items():
        actual = destination.get(region)
        if actual is None:
            violations.append(f"{region}: missing from destination")
            continue
        if abs(actual["revenue_eur"] - expected["revenue_eur"]) > tolerance:
            violations.append(
                f"{region}: revenue {actual['revenue_eur']:.2f} != {expected['revenue_eur']:.2f}"
            )
        if abs(actual["order_count"] - expected["order_count"]) > tolerance:
            violations.append(
                f"{region}: count {actual['order_count']:.1f} != {expected['order_count']:.1f}"
            )
    return violations


# --- the failure mode: append --------------------------------------------
destination = apply_load({}, SUMMARY, mode="append")
destination = apply_load(destination, SUMMARY, mode="append")   # the retry

violations = validate_load(destination, SUMMARY)
print("APPEND path after a retry:")
print(f"  AMER revenue in table: {destination['AMER']['revenue_eur']:.2f}")
print(f"  AMER revenue expected: {SUMMARY['AMER']['revenue_eur']:.2f}")
print(f"  invariant violations : {len(violations)}")
for violation in violations:
    print(f"    - {violation}")
print()
print("The DAG would have reported SUCCESS with wrong numbers.")
print()

# --- the fix: truncate ---------------------------------------------------
destination = apply_load({}, SUMMARY, mode="truncate")
destination = apply_load(destination, SUMMARY, mode="truncate")  # the retry

violations = validate_load(destination, SUMMARY)
print("TRUNCATE path after a retry:")
print(f"  AMER revenue in table: {destination['AMER']['revenue_eur']:.2f}")
print(f"  invariant violations : {len(violations)}")
print()
print("Identical state after one run or two. That is idempotency.")
