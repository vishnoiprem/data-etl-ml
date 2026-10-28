orders_path = SAMPLE_DIR / "orders.csv"
lines = orders_path.read_text(encoding="utf-8").splitlines()

print(f"orders.csv: {len(lines)} lines (1 header + {len(lines) - 1} data rows)\n")
print("header:")
print("  " + lines[0])
print()
print("first three data rows:")
for line in lines[1:4]:
    print("  " + line)
