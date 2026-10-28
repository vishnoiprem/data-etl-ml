## Exercises

1. **Boundary table.** Write a parametrised test for `should_run_full_load` covering `(0, 100)`, `(100, 100)`, `(101, 100)` and one larger case, and state in one sentence why the `100 == 100` case must be in the table.
2. **Harder — a structure rule.** Extend `validate_dag` with a rule that every task must have at least one downstream task or be an explicit "sink", and write a DAG that violates it. Then explain why `upstream_task_ids == set()` is not by itself an error.
3. **Harder — the CI gate.** Write a test that asserts the ETL DAG's load task uses `WRITE_TRUNCATE` rather than `WRITE_APPEND`. Explain why this assertion belongs in the DAG-structure layer and not in the pure-logic layer.
