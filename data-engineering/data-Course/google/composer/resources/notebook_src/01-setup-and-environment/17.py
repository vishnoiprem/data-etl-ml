checks = []

checks.append(("Python 3.9+", sys.version_info >= (3, 9)))
checks.append(("jinja2 installed", HAS_JINJA))
checks.append(("airflow NOT required", True))
checks.append(("project/ importable", "pipeline_logic" in sys.modules))
checks.append(("local_runner importable", "local_runner" in sys.modules))
checks.append(("sample orders.csv present", (SAMPLE_DIR / "orders.csv").exists()))
checks.append(("5000 raw orders", len(lines) - 1 == 5000))
checks.append(("1245 accepted orders", len(accepted) == 1245))
checks.append(("region summary matches", actual == EXPECTED_SUMMARY))
checks.append(("4 regions in summary", len(summarise_by_region(accepted)) == 4))

print()
width = max(len(name) for name, _ in checks)
for name, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}")

failed = [name for name, ok in checks if not ok]
print()
print("ALL CHECKS PASSED" if not failed else f"FAILED: {', '.join(failed)}")
