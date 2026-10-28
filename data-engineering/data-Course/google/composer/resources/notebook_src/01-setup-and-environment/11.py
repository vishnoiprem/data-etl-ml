# Count how the raw rows distribute across status and validity.
from collections import Counter

from pipeline_logic import classify_row, try_parse_order_line, REVENUE_STATUSES

status_counts = Counter()
validity_counts = Counter()

for line in lines[1:]:
    row = try_parse_order_line(line)
    if row is None:
        validity_counts["unparseable"] += 1
        continue
    status_counts[row["status"]] += 1
    validity_counts[classify_row(row)] += 1

print("status distribution (all parseable rows):")
for status, count in sorted(status_counts.items()):
    revenue = (
        "revenue-bearing"
        if status in REVENUE_STATUSES
        else "excluded from revenue"
    )
    print(f"  {status:<12} {count:>5}   {revenue}")

print()
print("validity classification:")
for verdict, count in sorted(validity_counts.items()):
    print(f"  {verdict:<12} {count:>5}")
