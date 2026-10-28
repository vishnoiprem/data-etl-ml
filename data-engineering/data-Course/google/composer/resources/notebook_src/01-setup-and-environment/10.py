from pipeline_logic import (
    transform_orders,
    summarise_by_region,
    render_summary_csv,
    reject_counts,
)

accepted, rejected = transform_orders(lines)

print(f"raw lines        : {len(lines) - 1}")
print(f"accepted orders  : {len(accepted)}")
print(f"rejected rows    : {len(rejected)}")
print()
print("region summary:")
print(render_summary_csv(summarise_by_region(accepted)))

EXPECTED_ACCEPTED = 1245
EXPECTED_SUMMARY = (
    "region,order_count,revenue_eur\n"
    "AMER,318,113592.19\n"
    "APAC,285,108194.92\n"
    "EMEA,322,118423.22\n"
    "LATAM,320,110646.18\n"
)

actual = render_summary_csv(summarise_by_region(accepted))
print(f"accepted == {EXPECTED_ACCEPTED} : {len(accepted) == EXPECTED_ACCEPTED}")
print(f"summary matches expected      : {actual == EXPECTED_SUMMARY}")
if actual != EXPECTED_SUMMARY:
    print("--- expected ---")
    print(EXPECTED_SUMMARY)
    print("--- actual ---")
    print(actual)
