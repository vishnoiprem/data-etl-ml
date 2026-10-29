# 1.4 — Tasks and Operators

> **Section 1 · Composer Fundamentals & Model · Lecture 1.4 · 9:00**

## 🎯 What you will learn

- The difference between an **operator** and a **sensor**, and why the distinction matters for cost
- The operators you will actually use: Python, Bash, BigQuery, GCS, Dummy, Empty
- The parameters every task shares, and how `default_args` cascades
- How to choose an operator — a decision procedure, not a preference list
- The `@task` decorator (TaskFlow) vs classic operators, honestly compared
- How `template_fields`, `do_xcom_push`, `retries` and `depends_on_past` work under the hood

---

## 🧠 Concept

### Operator vs sensor

Both are tasks. Both are nodes in the DAG. The difference is what they
do with time.

| | **Operator** | **Sensor** |
|---|---|---|
| **Purpose** | do work | wait for a condition |
| **Time** | finishes when the work is done | finishes when the condition is met |
| **Occupies a worker** | for the duration of the work | **no**, if `mode="reschedule"` |
| **Returns** | usually nothing (or an XCom) | `True` / `False` |
| **Fails on timeout** | n/a | yes, after `timeout` seconds |
| **Example** | `BigQueryInsertJobOperator` | `GCSObjectExistenceSensor` |

An operator does the thing. A sensor *asks whether the thing has
happened yet*, and Airflow re-checks later.

The critical implementation detail is the sensor's **mode**:

```python
from airflow.sensors.python import PythonSensor

sensor = PythonSensor(
    task_id="wait_for_upstream_data",
    python_callable=wait_for_upstream_data,
    mode="reschedule",     # ← releases the worker slot while waiting
    timeout=3600,
    poke_interval=300,
    soft_fail=True,
)
```

- **`mode="poke"`** — the worker stays occupied and the callable is
  called every `poke_interval` seconds. It responds quickly and consumes
  a worker slot the whole time.
- **`mode="reschedule"`** — the task is put back to `scheduled` and the
  worker slot is released. Airflow re-runs it later. Slow to respond
  (up to one scheduler cycle) but does not hold a slot.

The rule of thumb: **`reschedule` for anything over a few minutes**,
`poke` for quick checks. A sensor waiting an hour in `poke` mode holds
a Composer worker for an hour — and in a Composer environment with a
small worker pool, that is a denial of service against your own
pipelines.

A `soft_fail=True` sensor that never becomes true does **not** fail the
task; it is marked `skipped`. `soft_fail=False` (the default) fails the
task after `timeout`.

### The common operators

#### PythonOperator — the workhorse

```python
from airflow.operators.python import PythonOperator

validate = PythonOperator(
    task_id="validate_and_stage",
    python_callable=validate_and_stage,
)
```

The callable receives the Airflow context as keyword arguments if it
declares `**context`:

```python
def validate_and_stage(**context) -> dict:
    ds = context["ds"]
    partition = context["ds_nodash"]
    bq_dataset = context["var"].get("bq_dataset", "analytics")
    ...
    return {"staging_table": staging_table, "partition": partition}
```

The **return value is automatically pushed to XCom** under the key
`return_value`. Set `do_xcom_push=False` to suppress that.

`PythonOperator` accepts `templates_dict` for extra template fields:

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

The rendered values are available in the callable as
`context["templates_dict"]["source_path"]`.

#### BashOperator — glue, not logic

```python
from airflow.operators.bash import BashOperator

print_date = BashOperator(
    task_id="print_date",
    bash_command="echo 'Run date: {{ ds }} (previous: {{ prev_ds }})'",
)
```

Templates are rendered **before** the shell sees the command, so `{{ ds }}`
is substituted into the command string first.

BashOperator is excellent for: calling a CLI (`gcloud`, `gsutil`,
`bq`), running a small script, doing an `if/else` on a shell condition.
It is bad for: anything with real logic. A 40-line bash block in a DAG
is a testability problem and a quoting problem.

Two useful parameters:

```python
BashOperator(
    task_id="check_source_exists",
    bash_command="gsutil ls gs://bucket/{{ ds }}/orders.csv",
    do_xform_check=True,     # run `bash -n` first to catch syntax errors
    env={"KEY": "{{ var.value.key }}"},   # env vars for the command
)
```

`do_xform_check=True` parses the command before running it, turning a
silent shell syntax error into a task failure with a clear message.

#### BigQuery operators

```python
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryExecuteQueryOperator,
    BigQueryInsertJobOperator,
    BigQueryToGCSOperator,
)
```

| Operator | Does |
|---|---|
| `BigQueryExecuteQueryOperator` | runs a SQL query (the result is discarded unless you use a hook) |
| `BigQueryInsertJobOperator` | runs *any* BigQuery job — load, extract, query, copy |
| `BigQueryToGCSOperator` | exports a table to Cloud Storage |
| `BigQueryInsertJobOperator` with `configuration` | the general form |

The `BigQueryInsertJobOperator` is the one that matters, because
`writeDisposition` lives there and idempotency depends on it:

```python
load = BigQueryInsertJobOperator(
    task_id="load_to_bigquery",
    configuration={
        "query": {
            "query": "SELECT ... FROM `{{ ti.xcom_pull(task_ids='validate_and_stage', key='staging_table') }}` WHERE run_date = '{{ ds }}'",
            "destinationTable": {
                "projectId": "{{ var.value.gcp_project_id }}",
                "datasetId": "{{ params.target_dataset }}",
                "tableId": "{{ params.target_table }}",
            },
            "writeDisposition": "WRITE_TRUNCATE",
            "createDisposition": "CREATE_IF_NEEDED",
        }
    },
    retries=3,
    retry_delay=timedelta(minutes=10),
)
```

**`WRITE_TRUNCATE` against a partition decorator is what makes a retry
safe.** The load replaces the partition instead of appending to it. With
`WRITE_APPEND`, every retry appends a second copy of the same rows and
the totals double.

Note also the templated `ti.xcom_pull(...)` in the SQL: the destination
table name is decided by the previous task and passed through XCom.
This is control data, not bulk data — the right use of XCom.

#### GCS operators

```python
from airflow.providers.google.cloud.operators.gcs import (
    GCSListObjectsOperator,
    GCSCopyObjectOperator,
    GCSUploadOperator,
)
```

| Operator | Does |
|---|---|
| `GCSListObjectsOperator` | lists objects matching a prefix (often used as a quasi-sensor) |
| `GCSCopyObjectOperator` | copies an object, often with `source_object_generation` for idempotency |
| `GCSUploadOperator` | uploads a local file |
| `GCSDeleteObjectsOperator` | deletes objects (use with care) |
| `GCSObjectExistenceSensor` | waits for an object to appear — a *sensor* |

For idempotent copies, pin the source generation:

```python
GCSCopyObjectOperator(
    task_id="publish",
    source_object_name="raw/orders/{{ ds }}.csv",
    destination_bucket_name="{{ var.value.target_bucket }}",
    destination_object_name="orders/{{ ds }}.csv",
    source_object_generation=0,   # 0 = "whatever is current"
)
```

#### DummyOperator vs EmptyOperator

This is a genuinely confusing pair, and the confusion has a history.

**`DummyOperator`** (deprecated in Airflow 2.x, removed in Airflow 3)
does nothing at all. Its only purpose was to be a dependency target —
something you could point at to express "wait for these to finish"
without doing work.

**`EmptyOperator`** is its replacement. Same behaviour, non-deprecated
name, and it lives in `airflow.operators.empty`:

```python
from airflow.operators.empty import EmptyOperator

join = EmptyOperator(
    task_id="load_complete",
    trigger_rule="none_failed",
)
```

Both `DummyOperator` and `EmptyOperator` succeed instantly and push
`None` to XCom. They exist to express **join points** in the graph.

There is also `StartOperator`/`EmptyOperator` in older code and
`SkipOperator` (in `airflow.operators.empty`) which skips itself. The
name `Empty` is the one to use today.

### Task parameters

Every task accepts a common set of parameters. In Airflow 2.x, you set
them once in `default_args` and override per task.

```python
DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}
```

| Parameter | Meaning | Notes |
|---|---|---|
| `task_id` | unique within the DAG | required |
| `owner` | owner, used for SLA alerts | usually from `default_args` |
| `retries` | attempts after the first failure | `0` = one attempt total |
| `retry_delay` | delay between attempts | a `timedelta` |
| `retry_exponential_backoff` | exponential delay | for flaky APIs |
| `max_retry_delay` | cap on the backoff | |
| `depends_on_past` | must the previous run of *this task* succeed? | for append-only pipelines |
| `trigger_rule` | when to run given dependency states | see chapter 1.8 |
| `pool` / `pool_slots` | concurrency control | cross-DAG |
| `sla` | deadline for *this task* | measured from interval end |
| `execution_timeout` | hard wall-clock limit | kills the task |
| `do_xcom_push` | push the return value to XCom | `True` by default |
| `template_fields` | which attributes get templated | inherited from the operator class |
| `wait_for_downstream` | DAG is not "done" until downstream finishes | advanced |
| `on_failure_callback` | called on failure | for alerting |
| `multiple_outputs` | resolve an XCom as multiple values | TaskFlow |

#### `depends_on_past`

```python
PythonOperator(task_id="append", python_callable=append, depends_on_past=True)
```

The task runs only if the **previous run of the same task** succeeded.
This is right for a pipeline that appends to a table: you do not want
Tuesday's append to proceed if Monday's append failed halfway.

It is wrong for an idempotent pipeline that writes partitions by date —
there, a failed Monday should not block Tuesday.

#### `retries` and `retry_delay`

`retries=2` means **three total attempts** (the original plus two
retries). This trips people up constantly.

`retry_delay=timedelta(minutes=5)` sleeps 5 minutes between attempts.
With `retry_exponential_backoff=True`, the delays become roughly
1×, 2×, 4× the base.

A DAG that retries tasks which are *not* idempotent will corrupt data.
Retries and idempotency are two halves of one decision.

### How to choose an operator

Here is a decision procedure. Work down it.

```text
Is the work "call one API / one SQL statement / one file operation"?
  │
  ├─ YES ─▶ Is there a provider operator for it?
  │           │
  │           ├─ YES ─▶ use it (BigQueryInsertJobOperator, GCSCopyObjectOperator, ...)
  │           │
  │           └─ NO  ─▶ BashOperator if it's a CLI, else PythonOperator
  │
  └─ NO  ─▶ Is it "wait for something to happen"?
            │
            ├─ YES ─▶ a Sensor (GCSObjectExistenceSensor, HttpSensor, BigQueryTableExistenceSensor)
            │
            └─ NO  ─▶ PythonOperator, or TaskFlow @task
```

Then apply these tie-breakers:

1. **Prefer the provider operator over a generic one.** It has better
   logging, XCom integration, and connection handling.
2. **Prefer PythonOperator over BashOperator for logic.** Bash is for
   calling a CLI, not for computation.
3. **Prefer a sensor over a `sleep` loop.** A sensor releases the worker
   and integrates with the scheduler.
4. **Prefer `EmptyOperator` over a no-op Python function** for join
   points.
5. **If there is no operator and the logic is non-trivial, write one** —
   a `BaseOperator` subclass. More on that below.

### Custom operators

An operator is a class that wraps a piece of work, declares which
attributes are templatable, and returns an XCom.

```python
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults


class SummaryOperator(BaseOperator):
    """Write the per-region summary to GCS.

    Args:
        bucket: The target bucket.
        prefix: The path prefix.
        template_fields: ("bucket", "prefix") — these get Jinja-rendered.
    """

    template_fields = ("bucket", "prefix")

    def __init__(self, bucket: str, prefix: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bucket = bucket
        self.prefix = prefix

    def execute(self, context):
        from pipeline_logic import summarise_by_region, render_summary_csv
        ...
        return gcs_uri
```

Rules for a custom operator:

- `template_fields` must list the attributes you want templated. This is
  the *entire* mechanism — an attribute not listed is never rendered.
- Use `apply_defaults` (Airflow 2.x) to get the common parameters.
- `execute(self, context)` receives the context; the return value is
  pushed to XCom.
- **Do not do heavy work in `__init__`.** `__init__` runs at parse time
  on the scheduler. Do I/O in `execute`.

### TaskFlow: the `@task` decorator

Airflow 2.0 introduced **TaskFlow** — a decorator-based way to write
DAGs that looks like ordinary Python.

```python
from airflow.decorators import dag, task


@dag(
    dag_id="taskflow_orders",
    schedule="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
)
def taskflow_orders():
    @task
    def read_orders() -> list[str]:
        ...

    @task
    def transform_orders(lines: list[str]) -> dict:
        ...

    @task
    def summarise(rows: dict) -> dict:
        ...

    lines = read_orders()
    rows = transform_orders(lines)
    summarise(rows)


taskflow_orders()
```

The magic: **the dependency graph is inferred from the function calls.**
`transform_orders(lines)` depends on `read_orders()` because `lines` is
its return value. You never write `>>`.

Under the hood, TaskFlow:

1. Wraps each function in a `_PythonDecoratedOperator` — a real
   `PythonOperator` with `multiple_outputs` support.
2. **Auto-pushes** the return value to XCom.
3. **Auto-pulls** arguments from XCom when the decorated function is
   called, based on the type annotations.
4. Supports `.override()` to change a task's parameters (retries, pool,
   trigger rule) without redefining the function.
5. Supports `multiple_outputs=True` to return a dict and unpack it.

#### TaskFlow vs classic operators — honestly

| | Classic operators | TaskFlow `@task` |
|---|---|---|
| **Readability** | verbose, but explicit | clean, Pythonic |
| **Dependency definition** | `>>` chains | inferred from calls |
| **XCom** | manual `ti.xcom_push` / `xcom_pull` | automatic |
| **Boilerplate** | high | low |
| **Verbosity at the edges** | low | high — you hit a non-decorated operator |
| **Customisation** | full control over the operator | via `.override()` |
| **Debugging** | you know exactly which operator ran | one more layer of magic |
| **Airflow version** | 1.10+ | 2.0+ |

**The real trade-off is not "old vs new" — it is "explicit vs
implicit".**

Classic operators make the data flow visible. When you look at
`03_etl_bigquery.py`, you can see exactly which task produces the
`staging_table` value that the load query pulls from XCom. That
visibility is worth something when you are debugging at 3am.

TaskFlow removes that boilerplate and, in exchange, hides the XCom
plumbing. For a DAG with simple data flow, TaskFlow is clearly better.
For a DAG with subtle data flow, the explicitness of classic operators
can be worth the verbosity.

**You can mix them.** That is the normal answer in production:

```python
@dag(dag_id="mixed", schedule="@daily", start_date=start_date, catchup=False)
def mixed():
    @task
    def prepare() -> dict:
        return {"staging_table": "analytics.orders_enriched_staging"}

    info = prepare()
    load = BigQueryInsertJobOperator(
        task_id="load_to_bigquery",
        configuration={"query": {"query": "SELECT * FROM `{{ ti.xcom_pull(task_ids='prepare') }}`"}},
    )
    info >> load
```

The `@task` handles the simple part; the classic operator handles the
part where you need full control.

**A note on the TaskFlow XCom inference:** it relies on **type
annotations**. If a decorated function's parameter has no annotation,
TaskFlow cannot tell whether it is an XCom reference or a literal value
and will pass it literally. Annotate every parameter and return type.

### Multiple outputs

```python
@task(multiple_outputs=True)
def split():
    return {"accepted": [...], "rejected": [...]}

@task
def consume(result):
    accepted = result["accepted"]
    ...
```

The upstream task's XCom is the dict itself, and `result["accepted"]`
resolves to the sub-key. This is the TaskFlow equivalent of what the
course's runner does with `run.xcom.push("transform_orders", "accepted", …)`.

---

## 🛠️ Hands-On

### Step 1: Read the deployed DAG files

The four DAG files in `project/dags/` use every operator category in this
chapter. Read them in order:

```bash
sed -n '1,40p' project/dags/01_hello_world.py
```

The key structural lines:

```python
greet = PythonOperator(task_id="say_hello", python_callable=say_hello)
print_date = BashOperator(task_id="print_date", bash_command="echo 'Run date: {{ ds }}'")
greet >> print_date
```

### Step 2: Reproduce a PythonOperator task locally

The local runner's task callables mirror `PythonOperator`s. Run the
validation step and inspect its result:

```bash
cd project/core
python3 -c "
from pipeline_logic import transform_orders, reject_counts
lines = open('../../sample_data/orders.csv').read().splitlines()
accepted, rejected = transform_orders(lines)
print('return_value equivalent:', {'accepted_count': len(accepted), 'rejected_count': len(rejected)})
print('rejected by reason      :', reject_counts(rejected))
"
```

Expected output:

```text
return_value equivalent: {'accepted_count': 1245, 'rejected_count': 0}
rejected by reason      : {}
```

The `{'accepted_count': ..., 'rejected_count': ...}` dict is exactly what
`_transform` in `local_runner.py` returns — and it becomes the task's
XCom `return_value`.

### Step 3: See the BashOperator's templating in action

`BashOperator` renders `template_fields` before the shell runs. The
local equivalent:

```bash
cd project/core
python3 -c "
from templating import build_context, render_template

ctx = build_context(dag_id='hello_world', task_id='print_date', logical_date='2026-01-15')
command = \"echo 'Run date: {{ ds }} (previous: {{ prev_ds }})'\"
print(render_template(command, ctx))
"
```

Expected output:

```text
echo 'Run date: 2026-01-15 (previous: 2026-01-14)'
```

That string — not the template — is what bash receives. This is exactly
what `01_hello_world.py` does.

### Step 4: Verify the return value is auto-pushed to XCom

```bash
cd project
python3 -c "
from local_runner import DAGS, run_dag

run = run_dag(DAGS['etl_to_gcs'](), '2026-01-15')
print('aggregate return_value:')
print(run.pull('aggregate'))
print()
print('aggregate pushed keys:', sorted(run.xcom.store['aggregate']))
"
```

Expected output:

```text
aggregate return_value:
{'AMER': {'order_count': 318.0, 'revenue_eur': 113592.19}, 'APAC': {'order_count': 285.0, 'revenue_eur': 108194.92}, 'EMEA': {'order_count': 322.0, 'revenue_eur': 118423.22}, 'LATAM': {'order_count': 320.0, 'revenue_eur': 110646.18}}

aggregate pushed keys: ['return_value', 'summary']
```

Two things: the return value is pushed automatically under
`return_value`, and an explicit `xcom_push` adds a second key
(`summary`). Chapter 1.7 covers the storage model.

### Step 5: See a task failure and the auto-push of the error

```bash
cd project
python3 -c "
from local_runner import DAG, Task, run_dag

def failing(run, context):
    raise RuntimeError('BigQuery job failed: quota exceeded')

dag = DAG('operator_failure', tasks=[
    Task('load', failing, dependencies=[]),
    Task('notify', lambda run, context: 'paged', dependencies=['load']),
])
run = run_dag(dag, '2026-01-15')
print('states:', dict(run.state))
print()
print('the traceback was auto-pushed under key \'error\':')
print(run.xcom.pull('load', 'error').splitlines()[-1])
"
```

Expected output:

```text
states: {'load': 'failed', 'notify': 'upstream_failed'}

the traceback was auto-pushed under key 'error':
RuntimeError: BigQuery job failed: quota exceeded
```

### Step 6: Compare the operators side by side

Here is a compact reference table you can paste into your own notes.

| Operator | Import | Templated fields | Pushes XCom | Use for |
|---|---|---|---|---|
| `PythonOperator` | `airflow.operators.python` | `op_args`, `op_kwargs`, `templates_dict` | yes (return value) | business logic |
| `BashOperator` | `airflow.operators.bash` | `bash_command`, `env` | no | CLI calls |
| `EmptyOperator` | `airflow.operators.empty` | — | yes (`None`) | join points |
| `BigQueryExecuteQueryOperator` | `airflow.providers.google.cloud.operators.bigquery` | `sql`, `impersonation_chain` | yes | running SQL |
| `BigQueryInsertJobOperator` | same | `configuration`, `impersonation_chain` | yes | any BQ job |
| `BigQueryToGCSOperator` | same | `bucket`, `destination_prefix` | yes | exporting a table |
| `GCSCopyObjectOperator` | `airflow.providers.google.cloud.operators.gcs` | `bucket`, `source_object_name`, … | yes | copying objects |
| `GCSObjectExistenceSensor` | `airflow.providers.google.cloud.sensors.gcs` | `bucket`, `object_name` | no | waiting for an object |
| `PythonSensor` | `airflow.sensors.python` | `templates_dict` | yes | waiting for a condition |
| `BranchOperator` | `airflow.operators.python` | `templates_dict` | yes (the branch list) | choosing a path |
| `ShortCircuitOperator` | `airflow.operators.python` | `templates_dict` | yes | skipping downstream |
| `TriggerDagRunOperator` | `airflow.operators.trigger_dagrun` | `conf`, `logical_date` | yes | chaining DAGs |

### Step 7: Check the sensor's timeout and soft-fail semantics

```bash
cd project
python3 -c "
from local_runner import DAG, Task, run_dag

def never_ready(run, context):
    return False   # a sensor whose condition never becomes true

dag = DAG('sensor_demo', tasks=[
    Task('wait', never_ready, dependencies=[]),
    Task('after', lambda run, context: 'ran', dependencies=['wait']),
])
run = run_dag(dag, '2026-01-15')
print('states:', dict(run.state))
"
```

Expected output:

```text
states: {'wait': 'success', 'after': 'success'}
```

The local runner treats a `False` return as a successful task — the
*sensor* semantics (poll until true) live in the runner's task model
only in a simplified form. In real Airflow, a `PythonSensor` returning
`False` re-polls until `timeout`, then **fails** the task (or skips it
with `soft_fail=True`).

This is worth being explicit about: **the local runner is a teaching
model, not a simulator of every Airflow behaviour.** Chapters 1.7 and 1.8
depend on the runner's XCom and branch semantics being faithful, and
they are — but sensors and timeouts are not modelled.

---

## 🛠️ Common Errors and Fixes

### `TypeError: PythonOperator.__init__() got an unexpected keyword argument 'op_kwargs'`

`op_kwargs` is a `PythonOperator` argument; most other operators take
positional/keyword arguments directly:

```python
# PythonOperator
PythonOperator(task_id="t", python_callable=f, op_kwargs={"x": 1})

# BigQueryInsertJobOperator
BigQueryInsertJobOperator(task_id="t", configuration={...})
```

### `TypeError: 'NoneType' object is not iterable` on `>>`

One side of the `>>` is `None` — usually because an operator
constructor returned `None` instead of an object, or because you wrote

```python
task_a >> task_b   # ok
task_a >> some_function()   # ← not an operator
```

### `AttributeError: 'PythonOperator' object has no attribute 'xcom_push'`

`xcom_push` lives on the **TaskInstance**, not the operator. Inside a
callable, get it from the context:

```python
def my_task(**context):
    context["ti"].xcom_push(key="threshold", value=1000)
```

### `ImportError: cannot import name 'DummyOperator' from 'airflow.operators.dummy'`

`DummyOperator` is deprecated in Airflow 2.x and removed in Airflow 3.
Use `EmptyOperator`:

```python
from airflow.operators.empty import EmptyOperator
```

### `ImportError: cannot import name 'GCSOperator' from 'airflow.providers.google.cloud.operators.gcs'`

`GCSOperator` was renamed. In Airflow 2.x use `GCSUploadOperator` (for
uploading) or `GCSCopyObjectOperator` (for copying). `GCSOperator` was a
deprecated alias.

### `airflow.exceptions.AirflowNotFoundException: Could not find expected connection`

An operator needed a Connection that does not exist. Create it in the
Composer UI under **Admin → Connections**, or in the DAG:

```python
from airflow.hooks.base import BaseHook
conn = BaseHook.get_connection("my_conn")
```

### The task succeeded but downstream got nothing

The upstream task's return value was not pushed. Either:

- The task returned `None` (which is pushed as `None`), or
- `do_xcom_push=False` was set, or
- The downstream pulled with the wrong key or the wrong `task_ids`.

The downstream pull must name the task:

```python
value = ti.xcom_pull(task_ids="aggregate", key="summary")
```

### The task runs in the DAG but not on the worker

You put side-effecting code in the DAG file's top level instead of in
`execute`. Top-level code runs at *parse* time, in the scheduler
process, not on a worker. This also explains mysterious "my API call
happened 400 times" bugs.

### `Task failed with exception` — `NameError: name 'logical_date' is not defined`

You used a template variable outside a templated field. In a Python
callable, the context values are accessed via `context["logical_date"]`,
not as bare names.

### `AirflowSkipException` from a task you did not expect to skip

A `ShortCircuitOperator` returned `False`, or a branch chose a different
path. Check the upstream task's log for the skip message. Chapter 1.8.

### `KeyError: 'airflow.task'`

A `BaseOperator` subclass missing `apply_defaults`:

```python
from airflow.utils.decorators import apply_defaults

class MyOperator(BaseOperator):
    @apply_defaults
    def __init__(self, foo, **kwargs):
        super().__init__(**kwargs)
        self.foo = foo
```

---

## 💡 Production Notes

- **Put the logic in `execute`, not in `__init__`.** `__init__` runs on
  the scheduler at parse time.
- **Always set `template_fields` on a custom operator** if any attribute
  should be templated. It is the entire mechanism.
- **Retries require idempotency.** Every retried task must be safe to
  run twice. `WRITE_TRUNCATE` against a partition decorator is the
  pattern; `WRITE_APPEND` without a dedup key is not.
- **Prefer `mode="reschedule"` for long sensors.** A `poke` sensor holds
  a Composer worker slot for the whole wait.
- **Give sensors a `timeout`.** Without one, a sensor waits forever and
  the DAG run never completes.
- **Use `soft_fail=True` only when "not ready" is a normal outcome.**
  Otherwise you will silently skip a step that should have alerted.
- **TaskFlow for simple flow, classic operators at the edges.** The
  provider operators (`BigQueryInsertJobOperator`, `GCSCopyObjectOperator`)
  have better logging and connection handling than anything you would
  write yourself — do not reimplement them in a `@task`.
- **Annotate every TaskFlow function parameter.** Unannotated
  parameters are not resolved from XCom.
- **Use `pool` to control concurrency across DAGs**, not
  `max_active_runs`. A pool of 5 slots named `bigquery_loads` lets five
  DAGs share one BigQuery concurrency budget.
- **Set `execution_timeout` on tasks that call external systems.** It
  prevents a hung HTTP call from occupying a worker forever.

---

## 🔑 Key Takeaways

- An **operator does the work**; a **sensor waits for a condition** and
  ideally releases its worker slot while waiting (`mode="reschedule"`).
- The common operators: **PythonOperator, BashOperator,
  BigQueryExecuteQueryOperator, BigQueryInsertJobOperator,
  BigQueryToGCSOperator, GCSCopyObjectOperator, EmptyOperator**, and the
  sensors.
- **EmptyOperator** is the modern join point; `DummyOperator` is
  deprecated (Airflow 2.x) and removed in Airflow 3.
- `default_args` cascades to every task; per-task overrides win.
- `retries=2` means **three total attempts**.
- **Idempotency and retries are one decision.** `WRITE_TRUNCATE` against
  a partition decorator is the idempotent-load pattern.
- Choose an operator by decision procedure: *one API call?* → provider
  operator. *Waiting?* → sensor. *Real logic?* → PythonOperator.
- **TaskFlow (`@task`) infers dependencies from function calls** and
  auto-manages XCom. It is cleaner but hides the data flow; classic
  operators are explicit. **Mixing them is normal and correct.**

---

## 📚 Practice Exercises

1. **Operator selection.** For each of these, name the operator you
   would use and justify it: (a) copy yesterday's CSV from one GCS
   bucket to another; (b) run a `CREATE TABLE AS SELECT`; (c) wait for a
   partner's file to appear; (d) compute a per-region total from a
   200MB list; (e) express "wait for these three tasks, then continue".

2. **Custom operator.** Write a `SummaryOperator(BaseOperator)` that
   writes the per-region summary to GCS, with `template_fields =
   ("bucket", "prefix")`. Its `execute` must call
   `summarise_by_region()` and `render_summary_csv()` from
   `pipeline_logic.py`. Confirm the rendered bucket by printing it.

3. **XCom auto-push.** In the local runner, `write_summary` returns a
   path string and also pushes `gcs_uri` and `local_path`. Reproduce
   this with `ti.xcom_push` in a `PythonOperator` and explain what
   `do_xcom_push=False` would change about the return value's
   visibility.

4. **Sensor modes.** Write the same wait-for-a-file condition twice —
   once as a `PythonSensor` with `mode="poke"` and once with
   `mode="reschedule"` — and explain, in terms of worker slots held,
   what differs. Then decide which you would use for a 6-hour wait.

5. **TaskFlow conversion.** Convert `etl_to_gcs` to TaskFlow using
   `@dag` and `@task`, keeping the same four steps. Then convert it back.
   Which version would you rather debug at 3am, and why?

6. **`depends_on_past`.** Your DAG appends to a single growing table.
   Should the append task have `depends_on_past=True`? What breaks if
   it does, and what breaks if it does not?

7. **Reflection.** Explain the difference between "the task's return
   value" and "the task's XCom" to someone new to Airflow. Why does
   Airflow make them the same thing by default?

---

## 📖 Further Reading

- Airflow operators — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/operators.html
- Airflow TaskFlow — https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html
- Airflow sensors — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/sensors.html
- Airflow task parameters (`BaseOperator`) — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/operators.html#baseoperator
- Airflow custom operators — https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/custom-operator.html
- Google Cloud Composer operators — https://cloud.google.com/composer/docs/how-to/using/operators
- Apache Airflow provider: Google — https://airflow.apache.org/docs/apache-airflow-providers-google/stable/index.html
