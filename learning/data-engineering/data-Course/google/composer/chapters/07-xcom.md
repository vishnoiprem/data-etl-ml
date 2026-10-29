# 1.7 — XCom

> **Section 1 · Composer Fundamentals & Model · Lecture 1.7 · 8:30**

## 🎯 What you will learn

- What XCom is: a **key/value store in the metadata database**, scoped to (dag_id, task_id, run_id)
- The two halves — **push** and **pull** — and the automatic push of a task's return value
- `xcom_push` / `xcom_pull`, `ti.xcom_pull(task_ids=..., key=...)`, and the `key` parameter
- The 48 KB soft limit, and why pushing bulk data through XCom is a genuine production mistake
- **XCom is control data, not bulk data** — the rule, and the alternative
- XCom backends: the database, custom backends, and object storage
- The XComArg / TaskFlow equivalent, and when to use which

---

## 🧠 Concept

### What XCom actually is

XCom is Airflow's mechanism for passing values between tasks. The name
is historical — "XCom" for "cross-communication".

The critical thing to internalise is the **storage model**:

> **XCom values are rows in the metadata database.**

They are not an in-memory dict. They are not a message queue. They are
not a file on disk. Every push is an `INSERT` into the `xcom` table;
every pull is a `SELECT`.

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

Everything else in this chapter follows from that one fact.

- **It is durable.** A value pushed by a task survives the task, the
  worker, the pod, and the run. You can pull it days later.
- **It is scoped.** The natural key is
  `(dag_id, task_id, run_id, key)`. A value pushed in one run is not
  visible in another.
- **It is namespaced by task.** Task `aggregate`'s `summary` is
  invisible to task `write_summary` unless the pull names the task.
- **It is slow at scale.** It is a database table, in the same database
  that runs the scheduler. Writing megabytes into it slows down
  *every* DAG in the environment.

### Push and pull

**Push** stores a value under a task's namespace:

```python
def transform_orders(**context) -> dict:
    ti = context["ti"]
    accepted, rejected = transform_orders(lines)

    ti.xcom_push(key="accepted", value=accepted)
    ti.xcom_push(key="rejected", value=rejected)

    return {"accepted_count": len(accepted), "rejected_count": len(rejected)}
```

**Pull** retrieves it:

```python
def aggregate(**context) -> dict:
    ti = context["ti"]
    accepted = ti.xcom_pull(task_ids="transform_orders", key="accepted")
    rejected = ti.xcom_pull(task_ids="transform_orders", key="rejected")
    ...
```

Two parameters matter:

- **`task_ids`** — a task id or a list of task ids. **Without it,
  `xcom_pull` looks in the current task's own namespace**, which is
  almost never what you want when reading from an upstream task.
- **`key`** — the key within that namespace. Defaults to
  `"return_value"`.

### The automatic push

This is the detail that surprises people. **Any task that returns a
value has that value pushed automatically under the key
`return_value`.**

```python
def aggregate(**context) -> dict:
    ...
    return summary      # ← automatically pushed as key "return_value"
```

So the two equivalent ways to pass a value downstream:

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

The course's runner models this exactly. In `local_runner.py`:

```python
result = task.callable(run=run, context=context, **task.params)
run.state[task.task_id] = "success"
run.xcom.push(task.task_id, "return_value", result)   # ← the automatic push
run.outputs[task.task_id] = result
```

And `transform_orders` pushes two extra keys on top:

```python
run.xcom.push("transform_orders", "accepted", accepted)
run.xcom.push("transform_orders", "rejected", rejected)
```

So the `transform_orders` task has **three** XCom entries: `accepted`,
`rejected`, and `return_value`.

Set `do_xcom_push=False` on the operator to suppress the automatic push
(this is worth doing for tasks that return large objects you do not want
stored).

### Multiple values across tasks

`ti.xcom_pull` accepts a list of task ids and returns a **list** of
values, in the order given:

```python
values = ti.xcom_pull(task_ids=["extract_a", "extract_b"])
# -> [value_from_a, value_from_b]
```

This is the fan-in primitive. Airflow 2.x also has
`ti.xcom_pull(..., map_indexes=...)` for reading mapped task outputs
(see dynamic task mapping in chapter 1.8).

### Pulling inside a template

XCom can be pulled from a **template**, not just from Python. This is
the mechanism `03_etl_bigquery.py` uses:

```python
# --- snippet: fragment (part of a larger structure) ---
"query": (
    "SELECT order_id, customer_id, order_ts, region, channel, "
    "currency, status, amount, product_id, "
    "CURRENT_TIMESTAMP() AS load_ts, "
    "'{{ ds }}' AS run_date "
    "FROM `{{ ti.xcom_pull(task_ids='validate_and_stage', key='staging_table') }}` "
    "WHERE run_date = '{{ ds }}'"
)
```

The template is rendered *before* the task body runs, but *after* the
upstream task has finished (because that is a dependency). So the XCom
is available.

This is the **preferred** way to use XCom in a templated field, because
the rendered value shows up in the UI's "Rendered Template" view —
exactly what you want when debugging.

### The 48 KB soft limit

Airflow's `xcom` table has a `value` column of type `BYTEA` in
Airflow 2.x, and the metadata database's configuration historically
limited values to **48 KB** (`BaseXCom` / the `xcom` table's
`LargeBinary` column with a 48 KiB limit on the value stored by the
default ORM path).

Airflow 2.x will warn rather than hard-fail in most configurations:

```text
[WARNING] Could not create XCom with value ... (too large)
```

But "warn" is not "safe". The real problems with a large XCom are:

1. **Metadata database bloat.** The rows stay until they expire.
   Millions of large XCom rows will fill your Cloud SQL instance.
2. **Scheduler slowdown.** The scheduler queries the `xcom` table. A
   bloated table slows the scheduler, which slows *every* DAG in the
   environment — not just the one that pushed the big value.
3. **Slow pulls.** Fetching a megabyte of JSON out of Postgres, and
   deserialising it, is slow. You pay that cost on every retry.
4. **Serialization cost.** The value is pickled on push and unpickled on
   pull. For a large list of dicts, that is seconds of CPU per
   boundary.

The limit is on the *serialised* value, so it depends on the shape of
your data. A list of 500 order dicts is roughly 100–200 KB of pickled
JSON — over the limit. A summary of four regions is a few hundred
bytes.

### XCom is control data, not bulk data

This is the single rule to take away.

**XCom is for the small, decision-shaped values that flow between
tasks:**

| Good XCom | Bad XCom |
|---|---|
| A row count (`1245`) | The 1245 rows |
| A partition name (`20260115`) | The whole day's dataset |
| A table name (`analytics.orders_enriched_staging`) | The table's contents |
| A boolean decision (`True`) | A list of every rejected row |
| A GCS URI (`gs://bucket/path`) | The file |
| A threshold (`1000000`) | The configuration dump |

The test: **could this value be written to a file, and would the file be
bigger than a few kilobytes?** If yes, it does not belong in an XCom.

The correct pattern for bulk data:

```text
   Task A                        Task B
     │                             │
     ├── writes 5000 rows ───────▶│
     │   to gs://bucket/x.csv      │
     │   (or BigQuery)             │
     │                             │
     └── pushes "gs://bucket/x.csv" ──▶ XCom
         (the reference, ~40 bytes)
```

The XCom carries **the pointer**, not the payload. The pointer is small,
stable, and tells Task B exactly where the data is.

In the course's runner, `write_summary` does exactly this — it pushes
the *path*, not the CSV:

```python
run.xcom.push("write_summary", "gcs_uri", target)
run.xcom.push("write_summary", "local_path", str(local_path))
```

### The `xcom_pull` that returns nothing

When a task is skipped or fails, its XCom is absent. `xcom_pull`
returns `None` by default:

```python
value = ti.xcom_pull(task_ids="maybe_skipped")   # -> None
```

This is why defensive code uses a default:

```python
accepted = ti.xcom_pull(task_ids="transform_orders", key="accepted") or []
```

Note the `or []`: it turns both `None` and an empty list into `[]`.
That is exactly the pattern in `local_runner.py`:

```python
accepted = run.pull("transform_orders", "accepted") or []
```

and it is why the runner does not crash when a branch skipped the
upstream task.

### XCom backends

In Airflow 2.x, XCom storage is pluggable via the `xcom_backend`
configuration option.

| Backend | Where values live | When to use |
|---|---|---|
| **Database** (default) | the metadata DB's `xcom` table | almost always |
| **Custom** | your own class implementing `BaseXCom` | large values, or a special store |
| **Object storage** (via a provider / custom) | GCS, S3 | large values, high volume |
| **No-op / disabled** | nowhere | DAGs that must not persist values |

A custom backend in Airflow 2.x looks like:

```python
from airflow.models.xcom import BaseXCom


class GCSXComBackend(BaseXCom):
    """Store XCom values as objects in Cloud Storage.

    Args:
        bucket: The GCS bucket.
        prefix: The key prefix.
    """

    def __init__(self, bucket: str = "", prefix: str = "xcom"):
        self.bucket = bucket
        self.prefix = prefix

    def serialize_value(self, value, **kwargs):
        import json
        return json.dumps(value, default=str).encode("utf-8")

    def deserialize_value(self, serialized_value, **kwargs):
        import json
        return json.loads(serialized_value.decode("utf-8"))

    def orm_deserialize_value(self):
        ...
```

The important operational point: **switching XCom backends is a
per-environment configuration change**, and the values written by the
old backend are not readable by the new one. Treat it as a migration,
not a toggle.

In Composer, the default is the database. Composer 3 environments
support object-storage-backed XCom for large values; Composer 2
environments use the database.

### The TaskFlow equivalent: `XComArg`

When you use `@task`, the return value is not a plain Python object —
it is an **`XComArg`**, a promise that a value will exist at run time.

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

The resolution happens because `transform` is annotated with
`rows: list[str]` — the annotation tells TaskFlow that `rows` is an
XCom reference to be pulled from the upstream task's XCom.

Behind the scenes, TaskFlow does exactly what the classic API does:
it pushes the return value under `return_value` and pulls it by task
id. The difference is that the *dependency* is inferred from the call
graph, and the *resolution* is inferred from the annotations.

If you want to read a specific key in TaskFlow, use
`task.output["key"]`:

```python
@task(multiple_outputs=True)
def split():
    return {"accepted": [...], "rejected": [...]}

@task
def consume(result):
    accepted = result["accepted"]
```

### XCom and the "48 KB" myth

To be precise about what is and is not a hard limit:

- The `xcom.value` column in Airflow 2.x is `BYTEA` (unbounded) in
  most configurations, so a *very* large value may be stored without a
  database error.
- The **48 KB** figure is the historical default limit that Airflow
  *warns* about (and which some managed configurations enforce). It is
  a **soft limit** — a guardrail, not a hard constraint.
- The reason to respect it is not the limit itself. It is that the
  metadata database is a shared, latency-sensitive resource, and
  stuffing it with bulk payloads degrades the scheduler for everyone.

That distinction matters: "XCom has a 48 KB limit" is the popular
misstatement. "XCom is a database and bulk data does not belong in it" is
the true one.

---

## 🛠️ Hands-On

### Step 1: Run the XCom pipeline

```bash
python project/local_runner.py --dag xcom_pipeline --verbose
```

Expected output:

```text
▶ Running xcom_pipeline @ 2026-01-15

  Run summary for xcom_pipeline @ 2026-01-15
  ----------------------------------------------------
    ✓ read_orders            success
    ✓ transform_orders       success
    ✓ aggregate              success
    ✓ publish_summary        success
    ✓ write_summary          success

  ✓ xcom_pipeline succeeded

region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

The `publish_summary` task is the pure-XCom hop: it pulls the summary
from `aggregate` and pushes it under its own namespace.

### Step 2: Inspect the XCom store

```bash
cd project
python3 -c "
from local_runner import DAGS, run_dag

run = run_dag(DAGS['xcom_pipeline'](), '2026-01-15')
for task_id, namespace in run.xcom.store.items():
    print(f'{task_id}:')
    for key, value in namespace.items():
        rendered = repr(value)
        if len(rendered) > 70:
            rendered = rendered[:67] + '...'
        print(f'    {key:<14} {rendered}')
"
```

Expected output:

```text
read_orders:
    return_value   ['order_id,customer_id,order_ts,region,channel,currency,status,amou...
transform_orders:
    accepted       [{'order_id': 'o00000000', 'customer_id': 'c000914', 'order_ts': '2...
    rejected       []
    return_value   {'accepted_count': 1245, 'rejected_count': 0}
aggregate:
    summary        {'AMER': {'order_count': 318.0, 'revenue_eur': 113592.19}, 'APAC': ...
    return_value   {'AMER': {'order_count': 318.0, 'revenue_eur': 113592.19}, 'APAC': ...
publish_summary:
    summary        {'AMER': {'order_count': 318.0, 'revenue_eur': 113592.19}, 'APAC': ...
    return_value   {'AMER': {'order_count': 318.0, 'revenue_eur': 113592.19}, 'APAC': ...
write_summary:
    gcs_uri        'gs://demo-target-bucket/xcom_pipeline/2026-01-15/summary.csv'
    local_path     '/Users/pvishnoi/PycharmProjects/data-etl-ml/data-engineering/...
    return_value   '/Users/pvishnoi/PycharmProjects/data-etl-ml/data-engineering/...
```

Read this table carefully. It is the miniature of Airflow's `xcom`
table, and it shows:

- **`read_orders` returns the whole file's lines** — a large value. That
  is the *wrong* pattern, and the chapter explains why below.
- **`transform_orders` pushes the accepted rows** — 1245 dicts. Also the
  wrong pattern in production.
- **`aggregate` pushes a 4-region summary** — small, correct.
- **`write_summary` pushes a URI** — small, correct. This is the shape
  you want.

The runner deliberately does the "wrong" thing in the first two tasks
because it is a teaching model of the *mechanism*; the aggregate and
write tasks show the correct *shape*.

### Step 3: Measure the sizes

```bash
cd project
python3 -c "
import pickle
from local_runner import DAGS, run_dag

run = run_dag(DAGS['xcom_pipeline'](), '2026-01-15')
print(f'{\"task\":<18} {\"key\":<14} {\"bytes\":>8}')
print('-' * 44)
for task_id, namespace in run.xcom.store.items():
    for key, value in namespace.items():
        size = len(pickle.dumps(value))
        flag = '  <-- OVER 48KB' if size > 48 * 1024 else ''
        print(f'{task_id:<18} {key:<14} {size:>8}{flag}')
"
```

Expected output (exact sizes for the 5000-row sample dataset):

```text
task               key               bytes
--------------------------------------------
read_orders        return_value     412350  <-- OVER 48KB
transform_orders   accepted         201679  <-- OVER 48KB
transform_orders   rejected              5
transform_orders   return_value         55
aggregate          summary             173
aggregate          return_value        173
publish_summary    summary             173
publish_summary    return_value        173
write_summary      gcs_uri              75
write_summary      local_path          144
write_summary      return_value        144
```

Two tasks are over 48 KB — `read_orders` (the raw CSV lines) and
`transform_orders` (the 1245 accepted dicts). Those are the production
mistakes, right there in the course's own code.

Compare them with `aggregate`'s `summary` at **173 bytes**, and
`write_summary`'s `gcs_uri` at **75 bytes**. Those are the correct
shape: a few dozen bytes of control data, whether the pipeline handles
500 rows or 500 million.

The contrast is the lesson. The two *good* values would be the same
size whether the dataset were 10× bigger or 100× smaller. The two
*bad* values grow with the data, and so does the cost of every pull.

### Step 4: Push and pull explicitly

```bash
cd project
python3 -c "
from local_runner import DAG, Task, run_dag

def producer(run, context):
    run.xcom.push('producer', 'greeting', 'hello')
    run.xcom.push('producer', 'count', 42)
    return 'the return value'

def consumer(run, context):
    greeting = run.pull('producer', 'greeting')
    count = run.pull('producer', 'count')
    ret = run.pull('producer')
    print('  pulled greeting :', greeting)
    print('  pulled count    :', count)
    print('  pulled return   :', ret)
    return 'consumed'

dag = DAG('xcom_demo', tasks=[
    Task('producer', producer, dependencies=[]),
    Task('consumer', consumer, dependencies=['producer']),
])
run_dag(dag, '2026-01-15', verbose=True)
"
```

Expected output:

```text
  pulled greeting : hello
  pulled count    : 42
  pulled return   : the return value
```

Three distinct keys, one namespace per task.

### Step 5: The namespace rule — pulling from the wrong task

```bash
cd project
python3 -c "
from local_runner import DAG, Task, run_dag

def producer(run, context):
    run.xcom.push('producer', 'greeting', 'hello')
    return 'return value'

def wrong_pull(run, context):
    print('  pull from own namespace   :', run.pull('wrong_pull'))
    print('  pull from producer        :', run.pull('producer'))
    print('  pull key=greeting         :', run.pull('producer', 'greeting'))
    print('  pull a key that does not exist:', run.pull('producer', 'nope'))
    return None

dag = DAG('namespace_demo', tasks=[
    Task('producer', producer, dependencies=[]),
    Task('wrong_pull', wrong_pull, dependencies=['producer']),
])
run_dag(dag, '2026-01-15', verbose=True)
"
```

Expected output:

```text
  pull from own namespace   : None
  pull from producer        : return value
  pull key=greeting         : hello
  pull a key that does not exist: None
```

The first line is the important one: pulling without naming a task
looks in the **current task's** namespace and finds nothing. This is
exactly why `ti.xcom_pull(task_ids=...)` needs the `task_ids` argument
in real Airflow.

### Step 6: The XCom shape you should actually use

The correct pattern: push a **reference**, not the payload.

```bash
cd project
python3 -c "
from local_runner import DAG, Task, run_dag

def write_data(run, context):
    # The payload goes to storage, NOT to the XCom.
    path = 'gs://demo-target-bucket/orders/2026-01-15/orders.csv'
    print('  wrote 1245 rows to', path)
    # The XCom carries the pointer.
    run.xcom.push('write_data', 'uri', path)
    run.xcom.push('write_data', 'row_count', 1245)
    return path

def read_data(run, context):
    uri = run.pull('write_data', 'uri')
    count = run.pull('write_data', 'row_count')
    print('  downstream reads from', uri)
    print('  downstream knows there are', count, 'rows')
    return count

dag = DAG('reference_pattern', tasks=[
    Task('write_data', write_data, dependencies=[]),
    Task('read_data', read_data, dependencies=['write_data']),
])
run_dag(dag, '2026-01-15', verbose=True)
"
```

Expected output:

```text
  wrote 1245 rows to gs://demo-target-bucket/orders/2026-01-15/orders.csv
  downstream reads from gs://demo-target-bucket/orders/2026-01-15/orders.csv
  downstream knows there are 1245 rows
```

Compare the two XCom values: a ~70-byte URI and an integer. The
downstream task knows everything it needs, and the XCom stayed tiny.

### Step 7: Pulling from a template

```bash
cd project/core
python3 -c "
from templating import build_context, render_template

ctx = build_context(dag_id='etl_to_gcs', task_id='load_to_bigquery', logical_date='2026-01-15')
# In real Airflow, ti.xcom_pull is available in the template context.
# Here we simulate the value the upstream task pushed.
ctx['staging_table'] = 'analytics.orders_enriched_staging'
print('SELECT * FROM \`{{ staging_table }}\`')
print()
print('with a simulated pull:')
print('SELECT * FROM \`analytics.orders_enriched_staging\`')
"
```

In real Airflow the template is literally:

```jinja
FROM `{{ ti.xcom_pull(task_ids='validate_and_stage', key='staging_table') }}`
```

and it renders to:

```sql
FROM `analytics.orders_enriched_staging`
```

### Step 8: `xcom_pull` with `default=None`

```bash
cd project
python3 -c "
from local_runner import DAG, Task, run_dag

def maybe_skipped(run, context):
    from local_runner import TaskSkip
    raise TaskSkip('nothing to do')

def downstream(run, context):
    value = run.pull('maybe_skipped', 'data')
    print('  pulled from a skipped task:', value)
    print('  with or [] fallback       :', run.pull('maybe_skipped', 'data') or [])
    return 'ok'

dag = DAG('skipped_xcom', tasks=[
    Task('maybe_skipped', maybe_skipped, dependencies=[]),
    Task('downstream', downstream, dependencies=['maybe_skipped']),
])
run = run_dag(dag, '2026-01-15', verbose=True)
print('  states:', dict(run.state))
"
```

Expected output:

```text
  pulled from a skipped task: None
  with or [] fallback       : []
  states: {'maybe_skipped': 'skipped', 'downstream': 'skipped'}
```

Two things to notice:

1. The pull returns `None` because the upstream task never ran — the
   `or []` fallback turns that into an empty list instead of a crash.
2. **`downstream` is `skipped`, not `success`.** Its dependency was
   skipped, and the default trigger rule is `all_success`, which
   requires every dependency to have *succeeded*. This is exactly the
   skip-propagation semantics that chapter 1.8 is about — and it is
   why `xcom_pull` needs a defensive default.

To make the downstream run despite the skip, give it
`trigger_rule="none_failed"`:

```python
Task('downstream', downstream, dependencies=['maybe_skipped'],
     trigger_rule='none_failed')
```

---

## 🛠️ Common Errors and Fixes

### `KeyError: 'return_value'` / `airflow.exceptions.AirflowException: Could not find expected XCom`

Two common causes:

1. **The upstream task did not push that key.** A task that returns
   `None` pushes `None` under `return_value` — a key exists with a null
   value, so this is not usually it.
2. **The upstream task was skipped or failed.** No XCom was ever
   written. `xcom_pull` returns `None`; the error surfaces where you
   index into the result.

The real error in Airflow 2.x for a missing XCom looks like:

```text
Task failed with exception
airflow.exceptions.AirflowException: Could not find expected XCom reference: task_id='aggregate', key='summary'
```

### The pull returns `None` and you did not expect it

Almost always one of:

- The task id is misspelled. Task ids are **case-sensitive**.
- The key is wrong. The automatic push uses `"return_value"`.
- The upstream task was **skipped** (branch or ShortCircuit).
- The upstream task **failed** and the downstream is `upstream_failed`.
- You are pulling from a **different run**. XCom is scoped by `run_id`.

### `ValueError: The 'xcom' table is full` / database errors on large values

The metadata database cannot accept the value. Reduce the payload — the
fix is always to push a reference instead of the data.

### `TypeError: unhashable type: 'dict'` when using `xcom_pull` results as a set key

Not an XCom problem — a data structure problem. XCom values are
deserialised exactly as they were pushed, so a dict stays a dict.

### The XCom value is stale — it is the *previous* run's value

XCom is scoped by `run_id`. If you are pulling from a task id without
naming a run, you get the current run's value. But if you look at the
**UI's XCom tab** and pick a run from the dropdown, you may be looking
at a different run's values. Always check the run id.

### The value is `None` but the task succeeded

The task returned `None` explicitly, or `do_xcom_push=False` was set.
In the latter case the key does not exist at all.

### `AirflowSkipException` when pushing to XCom

Not possible — XCom pushes cannot skip. But a task that calls
`task.skip()` after pushing leaves the XCom in place, and downstream
tasks are marked `skipped`. Defensive pulls still matter.

### `pickle.UnpicklingError` / `TypeError: cannot load 'XCom'`

An XCom was written by a different Airflow version, or the
serialisation format changed. This happens when you change the
`xcom_backend` mid-flight. Clear the XComs for that task and re-run.

### Memory blow-up on pull

A large XCom is deserialised fully into memory in the worker. If the
worker OOMs, the symptom is a task failure with an OOM kill rather than
an XCom error. The fix is the same: stop pushing bulk data.

---

## 💡 Production Notes

- **XCom is the metadata database.** Treat every push as a database
  write on a shared, latency-sensitive resource.
- **Push the reference, not the payload.** A URI, a partition name, a
  count, a table name. Never the rows.
- **The 48 KB figure is a soft limit; the real rule is "control data
  only".** Even a 10 KB XCom pushed on every task of every run of every
  DAG adds up.
- **Use `do_xcom_push=False`** for tasks whose return value you do not
  need. It saves a row and a serialisation.
- **Use `key=` for anything other than the return value.** Unnamed keys
  make the XCom table unreadable and cause accidental collisions.
- **Never push a credential through XCom.** XCom values are stored in
  the database and visible to anyone with database or UI access.
- **Set `xcom_backend` deliberately if you need large values.** Treat it
  as a migration, not a toggle, and measure the effect on the scheduler.
- **Clean up expired XComs.** Airflow's `cleanup_xcom` / `xcom_cleanup`
  (in Airflow 2.x, the `xcom` table has a retention setting) and
  Composer's retention configuration keep the table bounded.
- **In TaskFlow, the return value is an `XComArg`.** You cannot use it
  as a plain Python value at DAG-definition time — that is why the
  annotation-based resolution exists.

---

## 🔑 Key Takeaways

- **XCom values are rows in the metadata database**, keyed by
  `(dag_id, task_id, run_id, key)`. Durable, scoped, and a shared,
  latency-sensitive resource.
- **Push** with `ti.xcom_push(key=..., value=...)`; **pull** with
  `ti.xcom_pull(task_ids=..., key=...)`. The `task_ids` argument is what
  crosses the task boundary.
- A task's **return value is pushed automatically** under
  `"return_value"`. `do_xcom_push=False` suppresses it.
- **XCom is control data, not bulk data.** Push a URI, a count, a
  partition name — never the rows.
- The **48 KB** figure is a soft guardrail; the reason to respect it is
  that the metadata database runs the scheduler.
- **`xcom_pull` returns `None`** when the value is missing — use
  `or []` or an explicit default.
- **XCom backends are pluggable** in Airflow 2.x, but switching is a
  migration.
- **TaskFlow's `XComArg`** is the modern equivalent: the return value is
  a promise, resolved from XCom at run time using type annotations.

---

## 📚 Practice Exercises

1. **Instrument the store.** Extend the Step 3 sizing script to print
   the size of every XCom value in all four DAGs. Which task produces
   the largest value in each, and by how much?

2. **Fix the bad shape.** The `transform_orders` task in the runner
   pushes 1245 accepted rows. Rewrite it (in a scratch copy) to push
   only the count and the GCS URI of a written file. Confirm the
   downstream `aggregate` task still produces the same summary.

3. **Prove the namespace rule.** Write a task that pulls a key from
   three different upstream tasks, each of which pushed a different
   value under the same key name. Show that the pulls are correctly
   isolated.

4. **Template pull.** Write a BashOperator whose `bash_command` uses
   `{{ ti.xcom_pull(task_ids='transform_orders', key='accepted_count') }}`.
   In the runner, simulate this by pushing `accepted_count` and rendering
   the command with `render_template`.

5. **The 48 KB boundary.** Find the number of order dicts that pushes a
   serialised XCom over 48 KB. Then calculate how many rows the
   *correct* pattern (URI + count) would need to exceed it. Comment on
   the difference.

6. **Custom backend.** Write a `BaseXCom` subclass that serialises
   values to JSON (rather than pickle) and stores them in a dict
   instead of the database. Then explain, in two paragraphs, what a
   production object-storage-backed XCom would need to add.

7. **Reflection.** "XCom is a database, not a dict." Explain to a
   colleague who thinks of XCom as an Airflow convenience why this
   distinction should change how they design a pipeline's data flow.

---

## 📖 Further Reading

- Airflow XCom — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcom.html
- Airflow XCom API (`BaseXCom`, `xcom_backend`) — https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/models/xcom/index.html
- Airflow templates reference (`ti`, `ti.xcom_pull`) — https://airflow.apache.org/docs/apache-airflow/stable/templates-ref.html
- Airflow TaskFlow — https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html
- Airflow best practices (minimise XCom usage) — https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html
- Google Cloud Composer: XCom — https://cloud.google.com/composer/docs/how-to/managing/xcom
