print("Available DAGs:\n")
for name in sorted(local_runner.DAGS):
    print(f"  - {name}")
print()
print("=" * 70)
print(local_runner.DAGS["etl_to_gcs"]().describe())
