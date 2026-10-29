#! number: 08
#! title: Patterns & Case Studies
#! module: Module 3 · Orchestration Patterns
#! lecture: Lecture 3.1
- Build a fan-out / fan-in pipeline and run it in the mini-runner
- Use **dynamic task mapping** (`.expand()` / `.expand_kwargs()`) and model it with `project/core/fanout.py`
- Compare **conditional execution** — `BranchOperator` vs `ShortCircuitOperator` — and pick the right trigger rule for every join
- Wire up the three **cross-DAG mechanisms**: `TriggerDagRunOperator`, `ExternalTaskSensor`, and Datasets
- Implement the **"wait for data"** pattern with `project/core/sensor_conditions.py`
- Work through three case studies: a daily orders ETL, a backfill, and a multi-DAG dependency chain
- Make every pattern **idempotent** with `idempotent_load.py` and `dedup_load.py`
