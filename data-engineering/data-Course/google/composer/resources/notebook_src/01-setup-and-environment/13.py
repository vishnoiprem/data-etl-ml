import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

run = local_runner.run_dag(
    local_runner.DAGS["etl_to_gcs"](),
    logical_date="2026-01-15",
    variables=local_runner.DEFAULT_VARIABLES,
    connections=local_runner.DEFAULT_CONNECTIONS,
    verbose=True,
)

print()
print("Task states:")
for task_id, state in run.state.items():
    print(f"  {task_id:<22} {state}")
