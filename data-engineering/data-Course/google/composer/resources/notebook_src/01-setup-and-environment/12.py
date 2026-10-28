malformed = (
    (SAMPLE_DIR / "malformed_orders.csv").read_text(encoding="utf-8").splitlines()
)
print("malformed_orders.csv:\n")
for line in malformed:
    print("  " + line)

print()
accepted_m, rejected_m = transform_orders(malformed)
print(f"accepted: {len(accepted_m)}   rejected: {len(rejected_m)}")
print()
print("reject reasons:")
for reason, count in sorted(reject_counts(rejected_m).items()):
    print(f"  {reason:<26} {count}")
