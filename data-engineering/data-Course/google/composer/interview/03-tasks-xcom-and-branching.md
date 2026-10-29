# Module 3 — Tasks, XCom & Branching

> **14 questions · Module 3 · Operators, task dependencies, XCom, trigger rules, branching, dynamic task mapping, sensors**

---

## Operators and dependencies

### 1. What is the difference between an operator and a sensor, and why does the difference have a cost rather than being a style choice?

**An operator does the work. A sensor asks whether the thing has happened yet, and finishes only when the condition is met.** Both are tasks and both are nodes in the DAG.

| | **Operator** | **Sensor** |
|---|---|---|
| Purpose | do work | wait for a condition |
| Time | finishes when the work is done | finishes when the condition is met |
| Occupies a worker | for the duration of the work | **for its whole life**, unless deferrable |
| Returns | usually nothing (or an XCom) | `True` / `False` |
| Fails on timeout | n/a | yes, after `timeout` seconds |

The cost comes from the sensor's implementation. In `mode="poke"` the worker stays occupied and the callable is called every `poke_interval` seconds — so a sensor with `timeout=3600` and `poke_interval=300` holds a worker for an hour, doing approximately nothing 11 times out of 12.

In `mode="reschedule"` the callable returns `False`, Airflow sets the task instance back to `scheduled` with a start time of `now + poke_interval`, and **releases the worker slot**. The slot is held only for the duration of one call.

The rule of thumb: **poke for minutes, reschedule for anything longer.** On Composer specifically, reschedule is usually the right default because the worker pool is sized for your DAGs and a pile of poke-mode sensors is the fastest way to hit the concurrency ceiling.

**The failure story:** 12 sensors in `mode="poke"` with `timeout=3600` on a 4-worker environment. Each held a worker for up to an hour. Every other DAG in the environment queued for 55 minutes with no errors anywhere — the classic executor-starvation signature, where the symptom is "tasks are queued but not running". The fix was `mode="reschedule"`.

### 2. Walk me through what a `PythonOperator` does when it runs, and what the `**context` argument actually contains.

**The worker imports the DAG file, builds the context, renders the templates, calls your callable with the context, then pushes the return value to XCom.** The `**context` keyword argument is how the callable receives it.

```python
def validate_and_stage(**context) -> dict:
    ds = context["ds"]
    partition = context["ds_nodash"]
    bq_dataset = context["var"].get("bq_dataset", "analytics")
    ...
    return {"staging_table": staging_table, "partition": partition}
```

The context contains `ds`, `ts`, `ds_nodash`, `prev_ds`, `data_interval_start`/`_end`, `logical_date`, `run_id`, `dag`, `task`, `ti`, `var`, `conn`, `params`, and `macros` — the same names as the Jinja context, because they are the same dict.

The alternative is `from airflow.operators.python import get_current_context`, which returns the context from inside any function rather than by parameter injection. Use it when you cannot change the callable's signature (a library function, a `PythonOperator` wrapping a third-party callable).

Two details that bite:

- **The return value is automatically pushed to XCom** under the key `return_value`. Set `do_xcom_push=False` to suppress it.
- **`templates_dict`** gives you extra template fields for a `PythonOperator`:

```python
PythonOperator(
    task_id="render_paths",
    python_callable=render_paths,
    templates_dict={
        "source_path": "gs://{{ var.value.source_bucket }}/{{ ds }}/orders.csv",
        "target_path": "gs://{{ var.value.target_bucket }}/{{ ds }}/summary.csv",
    },
)
```

The rendered values reach the callable as `context["templates_dict"]["source_path"]`.

**The failure story:** a callable was defined as `def transform(context):` (positional, not `**context`). Airflow calls the callable with keyword arguments, so the task failed with `TypeError: transform() got an unexpected keyword argument 'log'` — and the traceback pointed at Airflow's `_execute_callable` frame, not at the DAG file. The fix was `**context`.

### 3. `default_args` cascade: what does it actually apply to, and what does it *not* apply to?

**`default_args` supplies default kwargs for every task in the DAG**, and any individual task can override them. The course's:

```python
DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}
```

The critical semantics:

- **`retries=2` means up to three attempts** — one initial attempt plus two retries.
- **`retry_delay` is a fixed delay**, not exponential backoff. For backoff, pass a callable:

```python
def exponential_backoff(attempt_number: int, **context) -> timedelta:
    return timedelta(minutes=2 ** attempt_number)
```

- **`retries` applies per task, per task instance.** A DAG with 4 tasks and `retries=2` can make 12 task attempts in a run where everything fails.
- **DAG-level parameters in `default_args`** (like `depends_on_past`) apply to tasks; DAG-level parameters that belong on the `DAG` constructor (like `sla`, `schedule`) do not.

What it does **not** apply to: `sla` on the DAG (that goes on the `DAG()` constructor), and `trigger_rule` inheritance is *not* a thing — `trigger_rule` defaults to `all_success` per task regardless.

The course's `03_etl_bigquery.py` shows the override pattern: the DAG default is 2 retries / 5 min, but `load_to_bigquery` uses `retries=3, retry_delay=timedelta(minutes=10)` because a BigQuery load job that fails transiently needs longer backoff.

**The failure story:** a team set `retries=5` in `default_args` because "BigQuery is flaky". The `send_daily_digest` task then retried 5 times on a malformed recipient address, and each retry fired a partial-digest email — 6 emails a day for 11 days. The fix was per-task retry policy, and the rule became: **`retries > 0` only on tasks that are demonstrably idempotent.**

### 4. `>>` and the `with DAG(...)` block: what exactly is a dependency, and what does Airflow do about a task with no dependencies?

**A dependency means "this task may only run after that task has reached a terminal state that the trigger rule permits."** It is an edge in the graph, not a timing constraint.

```python
with DAG(dag_id="etl_to_gcs", ...) as dag:
    read = PythonOperator(task_id="read_orders", ...)
    transform = PythonOperator(task_id="transform_orders", ...)
    aggregate = PythonOperator(task_id="aggregate", ...)
    write = PythonOperator(task_id="write_summary", ...)
    read >> transform >> aggregate >> write
```

A task with **no** dependencies is a root node — it becomes runnable as soon as the DAG run exists. That is exactly how `read_orders` works in the course's `etl_to_gcs`: `deps=(-)` in the runner's `--describe` output.

The `>>` operator returns the right-hand operand, so `read >> transform >> aggregate >> write` is a chain of three edges. `transform >> [a, b]` is a fan-out; `[a, b] >> transform` is a fan-in.

**What Airflow does *not* do:** it does not enforce that a dependency's *side effect* is visible to the dependent task. If task A writes a GCS file and task B reads it, and A's write is not atomic, B can read a partial file. The dependency guarantees A *finished*, not that its output is *consistent*.

**The failure story:** a DAG had `write_orders` >> `publish_report`, where `publish_report` read `gs://bucket/orders.csv` that `write_orders` had just written with a 5000-row loop appending row by row. The dependency was satisfied — `write_orders` had succeeded — but the report read the file 400 ms before the last flush. The report was short by 180 rows. The fix was to make the write atomic: write to a temp path and `gsutil mv` it into place, so readers see either the old file or the complete new one.

---

## XCom

### 5. What is XCom's storage model, and what follows from "it is a table in the metadata database"?

**Every push is an `INSERT` into the `xcom` table; every pull is a `SELECT`.** The natural key is `(dag_id, task_id, run_id, key)`.

```text
┌──────────────────────────────────────────────┐
│                  xcom table                   │
├──────────────────────────────────────────────┤
│ dag_id | task_id  | run_id | key  | value    │
├──────────────────────────────────────────────┤
│ etl    | aggregate| run_1  | return_value | … │
│ etl    | aggregate| run_1  | summary      | … │
│ etl    | transform| run_1  | accepted     | … │
│ etl    | transform| run_1  | rejected     | … │
└──────────────────────────────────────────────┘
```

Five properties follow:

1. **Durable.** A value survives the task, the worker, the pod, the run. You can pull it days later.
2. **Scoped.** A value pushed in one run is not visible in another.
3. **Namespaced by task.** `aggregate`'s `summary` is invisible to `write_summary` unless the pull names the task.
4. **Slow at scale.** It is the same database the scheduler uses. Writing megabytes into it slows down *every* DAG in the environment.
5. **Pickled.** Push serialises, pull deserialises — seconds of CPU per boundary for a large list of dicts.

The course's runner models this exactly:

```python
run.xcom.push(task.task_id, "return_value", result)   # ← the automatic push
```

**The 48 KB number, precisely:** the `xcom.value` column in Airflow 2.x is `BYTEA` (unbounded) in most configurations, so a very large value may store without a database error. The 48 KB figure is the **historical default limit Airflow warns about**, and some managed configurations enforce it. It is a soft limit — a guardrail. The real reason to respect it is not the limit; it is that the metadata DB is a shared, latency-sensitive resource.

**The failure story:** a task pushed a list of 500 order dicts — roughly 100–200 KB of pickled JSON — through XCom. The scheduler's write latency on the shared Cloud SQL instance doubled for all DAGs, and the whole team's DAGs started missing their scheduled start times. The offending DAG's own task ran in 4 seconds. The fix: write to GCS, push the URI (~40 bytes).

### 6. Why does Airflow push a task's return value automatically, and what breaks if you rely on that?

**Because TaskFlow's data-passing model is built on it.** When you write `@task` functions, the return value of one becomes the *argument* of the next. Under the hood, TaskFlow pushes the return value under `return_value` and pulls it by task id. The automatic push is what makes the classic API and the TaskFlow API share one storage mechanism.

The two equivalent ways to pass a value downstream:

```python
# 1. The return value (implicit push under "return_value")
def aggregate(**context):
    return summary

summary = ti.xcom_pull(task_ids="aggregate")

# 2. An explicit push under a custom key
def aggregate(**context):
    ti.xcom_push(key="summary", value=summary)
    return summary

summary = ti.xcom_pull(task_ids="aggregate", key="summary")
```

**What breaks if you rely on it:**

- **It only works for a single value.** A function returning a tuple is pushed as one object — `ti.xcom_pull` returns the tuple, but `xcom_pull(task_ids=["a","b"])` returns a *list* of values, and the two are easy to confuse.
- **`do_xcom_push=False` suppresses it.** A task that returns a large object with the default setting silently writes it to the metadata DB.
- **The push happens even when nobody pulls it.** A task whose return value is 50 MB and whose downstream ignores it still paid the full write cost.
- **In TaskFlow, `multiple_outputs=True`** changes the shape: the dict's keys become separate XCom entries.

**The failure story:** a `PythonOperator` returned a list of 500 order dicts "just to be safe" — the author expected it to be ignored because the downstream task read from BigQuery instead. It was not ignored. It was pickled and inserted into the `xcom` table. The task took 4 seconds; the insert took 9 and slowed the shared scheduler for 20 minutes. The fix was `do_xcom_push=False`.

### 7. `xcom_pull` returned `None` and my downstream task blew up. What are the three possible causes?

**Three causes, in order of likelihood.**

1. **The upstream task was skipped or failed.** When a task is skipped or fails, its XCom is absent, and `xcom_pull` returns `None` by default. This is the classic branch bug: a task downstream of a `BranchOperator` on the *skipped* path pulls `None`.
2. **You forgot `task_ids`.** Without it, `xcom_pull` looks in the **current task's own namespace** — almost never what you want when reading from upstream.
3. **The key is wrong.** The `key` parameter defaults to `"return_value"`. If the upstream pushed under `"summary"`, pulling with the default key returns `None`.

The defensive pattern for all three:

```python
accepted = ti.xcom_pull(task_ids="transform_orders", key="accepted") or []
```

The `or []` turns both `None` and an empty list into `[]`. That is exactly the pattern in `local_runner.py`:

```python
accepted = run.pull("transform_orders", "accepted") or []
```

and it is why the runner does not crash when a branch skipped the upstream task.

Note that `or []` is also how you hide a real bug: a `None` that means "upstream failed" becomes an empty list that means "no data", and the pipeline continues green with zero rows. The better production form distinguishes the two:

```python
accepted = ti.xcom_pull(task_ids="transform_orders", key="accepted")
if accepted is None:
    raise ValueError("transform_orders produced no XCom — it was skipped or failed")
```

**The failure story:** a join task downstream of a branch pulled `None` from the skipped branch, treated it as an empty list, and published an empty summary. The DAG went green. The dashboard showed zero revenue for the day — and because the dashboard's health check was "did the DAG go green", the outage was invisible for 5 hours. The fix was to raise rather than default.

### 8. When is an XCom backend other than the database the right answer, and what breaks when you switch?

**Airflow 2.x makes XCom storage pluggable via the `xcom_backend` configuration option.**

| Backend | Where values live | When to use |
|---|---|---|
| **Database** (default) | the metadata DB's `xcom` table | almost always |
| **Custom** | your own class implementing `BaseXCom` | large values, or a special store |
| **Object storage** | GCS, S3 | large values, high volume |
| **No-op / disabled** | nowhere | DAGs that must not persist values |

In **Composer**, the default is the database. **Composer 3** environments support object-storage-backed XCom for large values; **Composer 2** environments use the database.

The operational point: **switching XCom backends is a per-environment configuration change, and values written by the old backend are not readable by the new one.** Treat it as a migration, not a toggle — you need to drain the old values first, or accept that historical XComs become unreadable.

**When the alternative wins:** the real fix for large payloads is usually not a different backend but **not putting the payload in XCom at all**. Write to GCS/BigQuery, push the reference. A custom XCom backend is the right answer when the value is genuinely a control-plane artifact you need to share across many DAGs and the metadata DB is measurably the bottleneck.

**The failure story:** a team migrated a Composer 2 environment to Composer 3 to get object-storage-backed XCom. The environment upgrade succeeded, and then 14 DAGs failed on their next run with `airflow.exceptions.NotFound: XCom not found`. The tasks that pulled `staging_table` from a previous task's XCom were fine — those were within the same run — but three DAGs used `ExternalTaskSensor` and pulled a *cross-run* XCom from the prior day's run, which was in the old database backend and no longer readable. The fix was a migration script that copied the prior 30 days of XCom rows into the new backend before switching, and changing the cross-run pattern to not use XCom at all.

### 9. What is TaskFlow's `XComArg`, and how does the dependency get inferred?

**With `@task`, the return value is not a plain Python object — it is an `XComArg`, a promise that a value will exist at run time.**

```python
@task
def extract() -> list[str]:
    return [...]

@task
def transform(rows: list[str]) -> dict:
    ...

@task
def load(result: dict) -> None:
    ...

rows = extract()          # rows is an XComArg, not a list
result = transform(rows)  # Airflow resolves rows from XCom at run time
load(result)
```

Two mechanisms: the **dependency** is inferred from the call graph (calling `transform(rows)` where `rows` is an `XComArg` creates the edge), and the **resolution** is inferred from the **type annotations** — `rows: list[str]` tells TaskFlow that `rows` is an XCom reference to be pulled from the upstream task's XCom.

To read a specific key, use `task.output["key"]`:

```python
@task(multiple_outputs=True)
def split():
    return {"accepted": [...], "rejected": [...]}

@task
def consume(result):
    accepted = result["accepted"]
```

**When the classic API wins:** when you need explicit control over `template_fields`, `do_xcom_push`, `trigger_rule`, `on_execute_callback`, or when you are migrating an existing DAG and want minimal diff. TaskFlow is clearly better for *new* DAGs with simple data flow; it is worse when you need to reach into the operator's internals.

**The failure story:** a team wrote a TaskFlow DAG where a function returned a dict but the consumer was annotated `def consume(result: dict) -> None:` and then did `result["accepted"]`. It worked. Then someone removed `multiple_outputs=True` from the producer — the dict became a single `return_value` XCom instead of two keys — and the consumer's `result["accepted"]` raised `KeyError: 'accepted'`. The annotation did not change; the shape did. The fix was to make `multiple_outputs=True` part of the producer's contract and assert the key set in a test.

---

## Trigger rules and branching

### 10. What are the trigger rules, and how do `skipped` and `failed` interact with each of them?

**The trigger rule decides whether a task runs, given the states of its dependencies.**

| Rule | Runs when | Use for |
|---|---|---|
| `all_success` (default) | every upstream succeeded | the normal case |
| `none_failed` | no upstream **failed** (skipped is OK) | a join after a branch |
| `none_failed_min_one_success` | no upstream failed **and** at least one succeeded | a join after a branch |
| `none_skipped` | no upstream was skipped | a strict join |
| `all_done` | all upstream finished, whatever the state | always-run cleanup |
| `always` | always | alerting, cleanup |

The interaction table that matters:

```text
Dependency state    all_success   none_failed   none_failed_min_one_success   none_skipped   all_done   always
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
success            ✓ runs        ✓ runs        ✓ runs                        ✓ runs         ✓ runs     ✓ runs
failed             ✗ upstream_failed  ✗ upstream_failed  ✗ upstream_failed      ✗ upstream_failed  ✓ runs  ✓ runs
skipped            ✗ skipped     ✓ runs        ✗ unless another succeeded    ✗ skipped     ✓ runs     ✓ runs
```

Two things to internalise:

- **A failed dependency is not a trigger-rule question.** It produces `upstream_failed` regardless of the rule (except `all_done` and `always`, which run *precisely because* everything upstream has finished, successfully or not). This is why `failed` and `upstream_failed` are distinct states: the first ran and raised; the second never ran.
- **`none_failed` vs `none_failed_min_one_success`** differs when *every* upstream branch is skipped. `none_failed` would run the join with no data; `none_failed_min_one_success` would skip it. The second is usually what you want.

The course's `local_runner.py` implements this in `_trigger_allows`:

```python
if rule == "none_failed":
    # "none failed" means: run unless something failed. A *skipped*
    # dependency is not a failure, so the task still runs.
    return True
```

**The failure story:** a cleanup task after a branch used `none_failed_min_one_success`, and the team assumed it always ran. When a branch chose a path that did not include the join, *both* branches were skipped and the join was skipped too — so the cleanup that removes stale staging tables **never ran for those days**. Staging tables accumulated: 40 tables in 3 weeks, then 400 in 6 months. The fix was `all_done` for the cleanup, which runs regardless of upstream state.

### 11. `BranchOperator` returns a list of task ids. What exactly gets skipped, and what does the branch task itself do?

**The branch task itself succeeds. It does not skip itself. Its downstream tasks are the ones that get skipped.**

```python
def choose_strategy(**context) -> list[str]:
    ti = context["ti"]
    row_count = int(ti.xcom_pull(task_ids="count_rows") or 0)
    threshold = int(ti.xcom_pull(task_ids="count_rows", key="threshold") or FULL_LOAD_THRESHOLD)
    force = bool(context["params"].get("force_full_load", False))
    chosen = "full_load" if (row_count > threshold or force) else "incremental_load"
    return [chosen]
```

The mental model:

```text
                    ┌──────────────┐
                    │ count_rows   │
                    └──────┬───────┘
                           │
                    ┌──────▼────────┐
                    │ choose_strategy│  ← returns ["incremental_load"]
                    └──────┬────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
     ┌────────▼────────┐       ┌────────▼────────┐
     │   full_load     │       │ incremental_load│
     │   → SKIPPED     │       │   → RUNS        │
     └────────┬────────┘       └────────┬────────┘
              │                         │
              └────────────┬────────────┘
                           │
                    ┌──────▼────────┐
                    │ load_complete │  ← needs trigger_rule!
                    └───────────────┘
```

**The classic branch bug:** a task that depends on *both* branches must use `trigger_rule="none_failed"` or `"all_done"`. With the default `all_success`, it is skipped too — because one of its dependencies was skipped. The result is a DAG that looks correct and **quietly does nothing**.

The course's `branching_load` DAG gets this right:

```python
finalise = PythonOperator(
    task_id="finalise",
    ...
    dependencies=["full_load", "incremental_load"],
    trigger_rule="none_failed",
)
```

**The failure story:** a team deployed a branch DAG with a join task that used the default `all_success`. The branch chose `incremental_load` on 180 of 181 days, and `full_load` once. The join ran exactly once, in 6 weeks. The DAG was green every day. The dashboard — which was fed by the join task — was **empty for 180 days**, and the daily report email (sent by the join) went out once. The catch was a stakeholder asking why the dashboard had no data for half a year.

### 12. `ShortCircuitOperator` vs `BranchOperator` — when do you use which, and what does `ignore_downstream_trigger_rules` do?

**`BranchOperator` chooses among several paths. `ShortCircuitOperator` has one outcome: skip everything downstream, or nothing.**

```python
short = ShortCircuitOperator(
    task_id="check_enabled",
    python_callable=check,                                # returns bool
    ignore_downstream_trigger_rules=True,
)
```

- `True` → the task succeeds and everything downstream runs normally.
- `False` → the task is marked `skipped` and **all downstream tasks are skipped**, except those with `ignore_downstream_trigger_rules=True`.

`ignore_downstream_trigger_rules=True` means downstream tasks are skipped *regardless of their own trigger rules*. Leave it `False` (the default) if you want a downstream `always` task (cleanup, notification) to still run.

**When each wins:**

| Need | Tool |
|---|---|
| "If the row count is under the threshold, do the cheap path; otherwise do the expensive path" | `BranchOperator` |
| "If this feature flag is off, skip the whole feature's subtree" | `ShortCircuitOperator` |
| "If the source file is missing, skip the run and send a notification" | `ShortCircuitOperator` + an `always` notifier |

**The failure story:** a team used `ShortCircuitOperator` with `ignore_downstream_trigger_rules=True` to skip a feature subtree when a flag was off. The flag was off for 3 days. The team's *error-notification* task was in that subtree — it was skipped, so the 3 days of errors were **never reported**. The flag was off precisely because the feature was broken, and the notification was disabled along with it. The fix: put the notifier *outside* the skipped subtree, and leave `ignore_downstream_trigger_rules=False` so an `always` notifier still runs.

### 13. How does dynamic task mapping work, and when does it beat a loop over files?

**Dynamic task mapping (Airflow 2.3+) fans a task out over a list whose size is only known at run time.** You use `.expand()` or `.expand_kwargs()`:

```python
from airflow.operators.python import PythonOperator

load_region = PythonOperator(
    task_id="load_region",
    python_callable=load_region_rows,
)

load_region.expand_kwargs(load_tasks(summary, partition))
```

where `load_tasks` returns a list of dicts — the course's `core/fanout.py` produces exactly this:

```python
def load_tasks(summary, partition) -> list[dict]:
    return [{"region": region, "partition": partition}
            for region in regions_to_process(summary)]
```

For the course's dataset that is **4 mapped task instances** (AMER, APAC, EMEA, LATAM). Airflow creates one task instance per item, each with its own `map_index`, each independently retriable and independently observable.

**`.expand()`** takes positional args: `.expand(x=list_a, y=list_b)` — the lists must be the same length (it is a cross-product by index). **`.expand_kwargs()`** takes a list of dicts, one per mapped instance.

**When it beats a loop:** it always should, for a *task* loop. A `PythonOperator` with a `for` loop over 500 files has one task instance, one retry granularity, one log stream, and no parallelism. A mapped task has 500 task instances, each independently retriable, each with its own log line in the UI, and each running concurrently up to `max_active_tasks`.

**When a loop is still right:** when the work is trivial (a handful of files), when you need the iterations to be *sequential* and ordered, or when the "loop" is not over independent units — e.g. a retry-with-backoff loop inside a single call.

**The failure story:** a team had a `PythonOperator` that looped over 1,200 customer files and uploaded each to GCS. The task failed at file 900 because of a transient 503. The retry restarted at file 1 — 900 uploads redone. And the whole 40-minute task held one worker slot the entire time. Converting to `.expand_kwargs` gave 1,200 task instances: the retry touched only the failed one, the UI showed exactly which customer failed, and `max_active_tasks=20` parallelised it to 6 minutes.

---

## Sensors

### 14. A sensor times out with `airflow.exceptions.AirflowSensorTimeout: Timeout: 3600.0s`. What does that message tell you, what does it not, and what are the three knobs?

**It tells you the total budget was exhausted and nothing else.** The message is deliberately uninformative — it does not say how many times it polled, or what the condition was, or whether the condition was *almost* met. When you see it, go and read the sensor's **log lines**, which have the detail.

The three knobs, which are constantly confused with each other:

| Knob | Meaning |
|---|---|
| **`timeout`** | total wall-clock budget, computed from the task's **start time**, not from the number of pokes |
| **`poke_interval`** | how long to wait between checks; must be smaller than `timeout` |
| **`soft_fail`** | what happens when the timeout expires |

The `soft_fail` table is the single most misunderstood parameter in Airflow:

| `soft_fail` | On timeout | The DAG |
|---|---|---|
| `True` (default) | the sensor task **succeeds** | downstream tasks run normally |
| `False` | the sensor task **fails** | downstream tasks are `upstream_failed` |

So a `soft_fail=True` sensor that times out **does not stop the pipeline** — it reports success and lets the pipeline continue with whatever data exists. That is exactly right for "wait for yesterday's upstream file, and if it never arrives, carry on with what we have", and exactly wrong for "wait for the reconciliation to complete before we close the books".

**The deeper cost, which decides sensor design:** *a sensor occupies a concurrency slot for its entire lifetime.* Airflow's concurrency limit counts **running task instances**, and a running sensor is a running task instance. So 50 sensors each waiting an hour consume 50 slots — even though they are doing nothing but sleeping. In `mode="reschedule"` the worker *process* is released, but the slot is not, until the sensor finally terminates.

The course's `04_branching_and_xcom.py` uses the right configuration:

```python
sensor = PythonSensor(
    task_id="wait_for_upstream_data",
    python_callable=wait_for_upstream_data,
    mode="reschedule",
    timeout=3600,
    poke_interval=300,
    soft_fail=True,
)
```

**The failure story:** a reconciliation DAG used a `soft_fail=True` sensor to wait for the upstream month-end close. When the close took longer than 4 hours, the sensor "succeeded" and the reconciliation proceeded against a half-closed ledger — producing a variance report with $4.2M of unexplained variance. The fix was `soft_fail=False`, so the sensor failed and the reconciliation did not run on incomplete data.

**And when a sensor is the wrong tool entirely:** "wait for data" is better expressed as a **Dataset** (Airflow 2.4+) when the producer updates a dataset, as a **schedule** when the timing is known, or as a **deferrable operator** (Airflow 2.2+) when the wait is long and the triggerer can hold the state — deferrable sensors release the worker entirely, rather than merely the worker process.

---

## Next module

→ [Module 4 — Reliability & Production](04-reliability-and-production.md)

---

## Related chapters

| Module section | Chapter |
|---|---|
| Operators, sensors, `default_args` (1–4) | [04-tasks-and-operators](../chapters/04-tasks-and-operators.md) |
| XCom (5–9) | [07-xcom](../chapters/07-xcom.md) |
| Trigger rules, branching, dynamic mapping (10–13) | [08-branching-and-dynamic-tasks](../chapters/08-branching-and-dynamic-tasks.md) |
| Sensors and deferrable operators (14) | [09-sensors-and-deferrable-operators](../chapters/09-sensors-and-deferrable-operators.md) |
