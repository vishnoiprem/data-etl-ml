**1.**

| Scenario | Trigger rule | Why |
|---|---|---|
| (a) | `NONE_FAILED_MIN_ONE_SUCCESS` | With `all_success` the join never runs when the *un-taken* branch is skipped — the classic "my downstream task silently never runs" bug. With `none_failed` the join runs even if every branch was skipped, producing an empty result. |
| (b) | `all_done` | "Run regardless of what happened upstream" — a skipped or failed dependency does not stop it. |
| (c) | `all_success` (the default) | The whole point is to fail loudly when an upstream did not succeed. |
| (d) | `NONE_FAILED_MIN_ONE_SUCCESS` | Requires at least one success, so an all-skipped join is skipped rather than running with no data. |
| (e) | `one_failed` | Fires on the failure, not on success. |
| (f) | `all_done` | Same as (b): run once every upstream has finished, successful or not. |

The six scenarios reduce to four distinct rules. You only ever need four.

**2.**

The fan-out comes from `regions_to_process(summary)`; the mapped task is `PythonOperator.partial(task_id="load_region", python_callable=load_one_region).expand(region=regions.output)`; the join uses `TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS`.

The key point about the assertions: the join's trigger rule decides whether it runs *at all*. With `NONE_FAILED_MIN_ONE_SUCCESS`, a join whose upstreams are one success and one failure still runs — and receives only the successful instance's return value, because the mapped task's collected list contains only the instances that ran. So the two assertions are:

```python
# one instance fails -> the join still runs, with the partial result
assert run.state["join_regions"] == "success"
assert run.pull("join_regions")["joined"] == 3      # 4 regions, 1 failed

# all instances succeed -> the join runs with the full result
assert run.state["join_regions"] == "success"
assert run.pull("join_regions")["joined"] == 4
```

With the default `all_success` the first assertion fails with `upstream_failed` — which is precisely the bug the trigger rule exists to prevent.

**3.**

The loop version creates **50 task instances in every run**, regardless of data. All 50 appear in the UI, all 50 occupy rows in the metadata database, and all 50 are re-parsed by the scheduler on every parse cycle — for every DAG in the environment, since parsing is per-file but the scheduler holds the resulting graph in memory.

The mapped version creates **4** — the number the data actually implies. Its parse-time cost is constant: one task definition.

So the loop version's scheduler load is proportional to the number of items *in the code*, and it grows every time someone adds an item. The mapped version's is proportional to the number of items *in the data*, and it costs the same parse time either way.

**4.**

(a) The consumer learns the producer's date through dataset **event metadata** (Airflow 2.9+): `outlets=[Metadata(ORDERS_DATASET, extra={"logical_date": "{{ ds }}"})]`. The consumer reads it from the event. The fallback, on older Airflow, is to pass it in `params`. The critical fact is that **the consumer's own logical date is the time it was queued**, not the producer's — a dataset-triggered run is not tied to the producer's date.

(b) The consumer simply **never runs**, and nothing reports it. This is the gap Datasets cannot close: a Dataset has no timeout, because a dataset has no notion of "expected". The answer is a separate monitoring DAG (or a freshness check on the producer's artefact) that alerts when the producer's last successful run is older than it should be — *not* a sensor, because a sensor would reintroduce the polling and the coupling the Dataset was chosen to avoid.

(c) Make the consumer **idempotent** and give it a **deterministic destination** keyed on the producer's logical date. A duplicate trigger then writes the same partition again, and the idempotent write (truncate, or dedup on the business key) makes the second run a no-op. `dedup_key(order_id, partition)` exists for exactly this: the identity is derived from the data, so a re-delivered update resolves to the same row.

**5.**

The symptom is **doubled revenue for one date** — or a partition whose row count is twice the source. The mechanism: the partition decorator is derived from the run's logical date, so two runs with *different* logical dates write to *different* partitions, and the doubling appears when the partition filter used by the aggregate is wider than the partitions actually loaded. The more precise failure is that the aggregate's `WHERE order_ts >= start AND order_ts < end` window can span a partition that a second, concurrent run is still writing to — so the aggregate reads a partially-written partition and the two runs' contributions overlap.

Two settings prevent it: **`max_active_runs=1`** (one date at a time), and a **deterministic, date-derived destination** (`partition = logical_date`) with an **idempotent write** so a retry replaces rather than appends.

Raising `max_active_runs` makes it *more* likely, not less: more concurrent runs means more windows in which two runs overlap on the same aggregate window, and more opportunity for a partial-partition read. The usual intuition — "more parallelism, same result" — holds only when every run touches a disjoint output region *and* the reader never observes a partially-written region. Those two properties are what `max_active_runs=1` and a closed-window read give you.

**6.**

- **`01_hello_world.py`** — linear only; a conditional check plus an SLA. It would also need a *load* pattern and a `max_active_runs` policy.
- **`02_templating_and_variables.py`** — linear; it would need a downstream handoff (a `TriggerDagRunOperator` or a Dataset consumer) and a `params` contract.
- **`03_etl_bigquery.py`** — a linear pipeline with an SLA, a retry policy, an idempotent partitioned load, a dead-letter path and `depends_on_past=False`. It is missing **fan-out** (per-region loads) and a **cross-DAG handoff**. Its aggregate's `WHERE order_ts >= ... AND order_ts < ...` filter is exactly right, which is the hardest thing to get right.
- **`04_branching_and_xcom.py`** — conditional execution, XCom, a sensor, a cross-DAG trigger, and a join with `none_failed`. It is missing **dynamic mapping** (the branch's two fixed tasks could be a mapped task over the load strategies) and a **Dataset-based alternative to the sensor**.

**The biggest gap is `03_etl_bigquery.py`.** It is the production-shaped DAG, and it is the one most likely to be operated on daily — yet it has no fan-out and no cross-DAG handoff, so a late-arriving partition has nowhere to wait and a downstream consumer has to poll for it.

The improvement, in order:

1. Replace the single `load_to_bigquery` with a mapped task over the partitions present in the run, using `expand_kwargs(load_tasks(...))`. The load becomes per-partition, and a failed partition retries on its own instead of re-running the whole load.
2. Add a `GcsObjectSensor` (or a Dataset) at the head of the DAG, so the run waits for the source object rather than proceeding with an empty load. The course's `source_is_ready` is the pure form of the same condition.
3. Give the aggregate a `NONE_FAILED_MIN_ONE_SUCCESS` join after the mapped load, so a partial load still publishes — with the failure visible in the log — instead of silently producing nothing.
4. Split the export into its own DAG triggered by a `TriggerDagRunOperator`, so the downstream consumer of the exported summary is not coupled to the load's internals.
