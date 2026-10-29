# 1.2 — Airflow Architecture and Concepts

> **Section 1 · Composer Fundamentals & Model · Lecture 1.2 · 9:00**

## 🎯 What you will learn

- The five components of an Airflow deployment: scheduler, DAG processor, metadata database, executor, workers
- What each component actually does, and which one is on the critical path of every run
- The scheduler loop, step by step — how a DAG run goes from "scheduled" to "running"
- The DAG run vs task instance distinction, and the state machine each one has
- The metadata database as the single source of truth (and what that implies for XCom)
- Why Airflow 2 is a *hybrid*: a workflow manager bolted onto a data processor
- What Cloud Composer changes about the picture

---

## 🧠 Concept

### The five components

An Airflow deployment has five moving parts. Composer runs all five for
you, but you need to know their names, because the logs you read and the
errors you debug are labelled with them.

```text
┌─────────────────────────────────────────────────────────────────┐
│                        Airflow 2.x                              │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  DAG Processor  (scheduler process)                       │  │
│  │  - scans the dags/ folder                                 │  │
│  │  - imports each .py file                                  │  │
│  │  - writes DAG + task rows to the metadata DB              │  │
│  │  - updates: next_dagrun, next_dagrun_create_after, ...    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │ writes                              │
│                          ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Metadata Database  (Postgres / Cloud SQL in Composer)    │  │
│  │  tables: dag, task, dag_run, task_instance, xcom,         │  │
│  │          job, log, variable, connection, ...              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │ reads/writes                        │
│                          ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Scheduler  (scheduler process)                           │  │
│  │  - the loop: create DagRuns, create TaskInstances,        │  │
│  │    queue runnable tasks, detect SLA misses, heartbeat     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │ queues                              │
│                          ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Executor  (CeleryExecutor in Composer)                   │  │
│  │  - translates "runnable task" into an executable command   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │ dispatches                          │
│                          ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Workers  (Celery workers)                                │  │
│  │  - run `airflow tasks run <dag_id> <task_id> <date>`      │  │
│  │  - import the DAG file, render templates, run the callable│  │
│  │  - push XComs, write logs, report the final state         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Web Server  (Flask + Airflow REST API)                   │  │
│  │  - the UI, trigger DAGs, the REST API, the Triggerer      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

Composer adds the pieces Google manages around it: a GCS bucket holding
your DAG files, a Cloud SQL Postgres instance for the metadata database,
a GCS bucket for task logs, and Cloud Monitoring for metrics.

### The scheduler loop

The scheduler is a single process running a loop. Understanding the loop
explains almost every Airflow behaviour you will find surprising.

```text
   ┌──────────────────────────────────────────────────────────┐
   │                                                          │
   ▼                                                          │
  (1) Heartbeat: update the scheduler's own heartbeat in the    │
   │    metadata DB. If this stops, other schedulers take over.│
   │                                                          │
   ├─▶ (2) DAG-run creation: for every DAG whose               │
   │        next_dagrun_create_after <= now, and whose          │
   │        max_active_runs allows, INSERT a dag_run row.      │
   │                                                          │
   ├─▶ (3) Task-instance creation: for every dag_run that has   │
   │        no TI yet, INSERT task_instance rows for each task, │
   │        computing each task's dependencies from the DAG.   │
   │                                                          │
   ├─▶ (4) Task evaluation: for each task_instance, compute     │
   │        whether its dependencies are met and whether the    │
   │        trigger_rule permits it to run.                     │
   │                                                          │
   ├─▶ (5) Queueing: set queued_by_scheduler on runnable TIs   │
   │        and let the executor pick them up.                 │
   │                                                          │
   ├─▶ (6) SLA check: compare running tasks against their SLA   │
   │        deadline; fire sla_miss_callback.                   │
   │                                                          │
   └─▶ (7) Cleanup: mark finished TIs, update DAG run states,   │
        expire old XComs / logs, commit, sleep, loop.
```

Two properties of this loop matter enormously:

**It is polling, not event-driven.** The scheduler wakes up on a timer
(typically every few seconds) and *re-evaluates* the world. It does not
receive a webhook when a task finishes; it notices. This is why task
state transitions have a small delay, and why a DAG can show a task as
`running` for a few seconds after it actually finished.

**The scheduler does not execute tasks.** It decides *what* should run
and marks it queued. The executor and workers do the running. This is
why you can have many workers but only one (or a few, with HA) scheduler:
the scheduler's work is cheap metadata manipulation, and the workers'
work is arbitrary user code.

### The DAG processor

The DAG processor is the part of the scheduler that reads your Python
files. On every pass it:

1. Lists the files in the `dags/` folder.
2. Imports each `.py` file **as a module** (with a module cache keyed by
   file path and mtime — an unchanged file is not re-imported).
3. Collects the `DAG` objects that the import registered.
4. Serialises DAG and task metadata into the `dag` and `task` tables.
5. Computes `next_dagrun` and `next_dagrun_create_after` from the
   DAG's `schedule` and `start_date`.

Two consequences follow directly.

**Your DAG file is executed as Python, at parse time, on the scheduler.**
Any top-level code in a DAG file runs every time the file is parsed.
That is why top-level code must be cheap and side-effect free — a
`print()` at module scope, or worse a database connection, runs on the
scheduler every cycle. Heavy work belongs inside a task's callable.

**An import error removes the DAG entirely.** If your file raises at
import, the DAG does not appear in the UI at all. In Composer, the parse
error is visible in the DAG file's own detail view.

### The metadata database

Everything Airflow knows lives in Postgres (Cloud SQL in Composer). The
important tables:

| Table | Holds |
|---|---|
| `dag` | one row per DAG: schedule, start_date, catchup, next_dagrun, is_paused, fileloc |
| `task` | one row per task: operator, retries, trigger_rule, dependencies, template_fields |
| `dag_run` | one row per execution: state, execution_date, run_type (scheduled/manual/backfill), conf |
| `task_instance` | one row per (dag_run, task): state, start_date, end_date, try_number |
| `xcom` | key/value pairs pushed between tasks — **this is a table** |
| `job` | scheduler/executor heartbeats |
| `log` | task log lines (in Airflow 2.x; Composer routes these to GCS) |
| `variable` | key/value config |
| `connection` | credentials, with `extra` as a JSON blob |
| `import_error` | files that failed to parse |

The table that catches people out is `xcom`. **XCom values are rows in
this database.** That single fact explains the 48 KB limit, the
performance characteristics, and the rule that XCom is for control data
only. Chapter 1.7 covers it in full.

### Executors and workers

The **executor** is the plugin that decides *how* a queued task becomes a
running process. Airflow 2.x ships several:

| Executor | How it runs tasks | Notes |
|---|---|---|
| `SequentialExecutor` | one at a time, in the scheduler process | for debugging only |
| `LocalExecutor` | a local subprocess | simple, single-machine |
| `CeleryExecutor` | a Celery worker pool | **Composer 2 default** |
| `KubernetesExecutor` | a Kubernetes pod per task | Composer 3 / OSS |
| `KubernetesExecutor` (Argo) | Argo workflows | Composer 3 |

In Composer 2.x, the environment is a managed **CeleryExecutor** setup:
Composer runs a pool of Celery workers that pull tasks from the
metadata database (via the broker) and execute them.

A **worker** is the process that actually runs a task. The command it
runs is effectively:

```bash
airflow tasks run <dag_id> <task_id> <logical_date> --local --job-id <n>
```

The worker:

1. Imports the DAG file (so it can reconstruct the task object).
2. Builds the task context.
3. Renders the templates in `template_fields`.
4. Calls `execute(context)`.
5. Pushes the return value to XCom (unless `do_xcom_push=False`).
6. Writes the log lines and the final state back to the database.

Because the worker re-imports the DAG file, **the DAG file must be
importable in the worker environment**. That is why an import error
breaks execution as well as parsing.

### The task lifecycle

Every task instance moves through this state machine.

```text
                    ┌─────────────────────────────┐
                    │                             │
                    ▼                             │
  (none) ──▶  queued  ──▶  running  ──▶  success │
                    │            │                │
                    │            ├──▶  failed ────┼──▶ (retry) ──▶ queued
                    │            │                │
                    │            ├──▶  skipped    │
                    │            │                │
                    │            └──▶  upstream_failed
                    │                             │
                    └─────────────────────────────┘
                              (never ran)
```

The states, and what they mean in practice:

| State | Meaning | Ran? | Has output? |
|---|---|---|---|
| `queued` | the scheduler decided it should run; waiting for a worker | no | no |
| `running` | a worker picked it up | yes | maybe |
| `success` | completed without raising | yes | yes |
| `failed` | raised an exception and exhausted retries | yes | maybe (partial) |
| `skipped` | deliberately not run — branch not chosen, or ShortCircuit | no | no |
| `upstream_failed` | never started; an upstream task failed | no | no |
| `restarting` | being retried after a failure | yes | maybe |

The distinction between `failed` and `upstream_failed` is the one that
matters most for alerting. `failed` means "something went wrong and it is
your code's fault". `upstream_failed` means "the problem was upstream;
fix the upstream task". And `skipped` means "the pipeline decided this
was not applicable" — a normal outcome, not an error.

Airflow 2.9+ adds `upstream_failed` distinctly; older UI versions
sometimes showed it as `skipped`. Airflow 3 renamed `execution_date` to
`logical_date` in the UI and made the `scheduled`/`backfill` distinction
sharper. The semantics are the same.

### DAG run vs task instance

This is the distinction that makes Airflow's data model coherent.

| | DAG run | Task instance |
|---|---|---|
| **Created by** | the scheduler (or a manual trigger) | the scheduler, one per task per run |
| **Identity** | `(dag_id, execution_date, run_id)` | `(dag_id, task_id, run_id)` |
| **Has** | a state, a conf, a data interval | a state, try_number, start/end dates |
| **Examples** | `scheduled__2026-01-15T00:00:00+00:00` | `scheduled__2026-01-15T00:00:00+00:00` / `aggregate` |

A **DAG run** is one execution of a DAG at one logical date. A **task
instance** is one attempt-state of one task within one DAG run. The
number of task instances in a run equals the number of tasks in the DAG.

```text
dag_run:  etl_to_gcs @ 2026-01-15          (one row)
  ├─ task_instance: read_orders      → success
  ├─ task_instance: transform_orders → success
  ├─ task_instance: aggregate        → success
  └─ task_instance: write_summary    → success
```

Airflow 2.x run types, visible in the run_id:

| run_type / run_id prefix | Meaning |
|---|---|
| `scheduled__<date>` | the scheduler created it on the schedule |
| `manual__<date>` | a human triggered it from the UI or API |
| `backfill__<date>` | created by a backfill job |
| `dataset_triggered__<date>` | created by a Dataset event (2.4+) |

The distinction between a `scheduled__` run and a `manual__` run of the
*same* logical date is important and easy to miss. They are different
rows with different run_ids, and they will both write their outputs. If
a manual run writes to the same destination as the scheduled run, you get
double-written data — which is exactly why idempotent loads matter.

### Why Airflow 2 is a hybrid

Here is the observation that separates people who use Airflow from people
who understand it.

Airflow was born as a **workflow manager**: Airflow 1.x was essentially a
cron replacement with a rich UI. It scheduled jobs, showed their status,
and let you re-run them. It did not itself compute anything.

Then, over Airflow 1.10 through 2.x, Airflow absorbed the responsibilities
of a **data processor**. Specifically:

- **Operators** (`BigQueryInsertJobOperator`, `GKEStartPodOperator`,
  `SparkSubmitOperator`, `S3ToRedshiftOperator`) wrap *data movement* as
  first-class tasks.
- **TaskFlow** (Airflow 2.0+) let you write plain Python functions with
  `@task` and have Airflow wire the dependencies, push XComs and handle
  retries automatically.
- **Datasets and data-aware scheduling** (2.4+) let Airflow react to
  *data arriving*, not just to the clock.
- **Dynamic task mapping** (2.3+) lets one task fan out into N parallel
  tasks at run time.

So Airflow 2 sits in the middle:

```text
   Airflow 1.x                        Airflow 2.x
   ──────────                        ──────────
   workflow manager                   workflow manager
   (cron + UI)                            +
                                     data processor
                                     (operators, TaskFlow,
                                      datasets, dynamic mapping)
```

And this hybrid nature explains a lot of Airflow's design, including its
worst trait: **the DAG file is Python, so every DAG file is a program
that runs on the scheduler.** A workflow manager could have used a
declarative config format. Because Airflow chose Python, it gained
enormous expressiveness and it also inherited all of Python's
sharp edges — import errors, dependency hell, global state, and the fact
that a DAG file's top-level code is not a pure declaration.

### What Composer changes

Composer is *managed* Airflow. You get:

- A pre-configured Airflow environment (web server, scheduler, workers,
  Cloud SQL Postgres, GCS DAG bucket).
- Autoscaling worker pools that scale with the number of queued tasks.
- IAM-based access control instead of Airflow's own RBAC (in Composer 2.x;
  the built-in RBAC was added in Composer 3).
- Environment Versioning, so you can upgrade Airflow without breaking
  your DAGs.
- Google Cloud-native integrations: BigQuery, GCS, Dataproc, Dataflow,
  GKE, Cloud Run.

What it does *not* change:

- Airflow's data model, semantics, or APIs. A DAG that works in OSS
  Airflow 2.x works in Composer 2.x.
- The fact that your DAG file is Python and is imported by the scheduler.
- The metadata database being the source of truth.
- The executor being Celery (in Composer 2.x).

---

## 🛠️ Hands-On

### Step 1: Observe the scheduler's work through `--describe`

The `--describe` flag is the closest thing the local runner has to
"inspect the metadata database":

```bash
python project/local_runner.py --dag all --describe
```

Expected output:

```text
DAG: branching_load
  schedule    : @daily
  start_date  : 2026-01-01
  catchup     : False
  description : Pick a full-load or incremental strategy based on row volume.
  tasks (6):
    - read_orders            deps=(-)
    - transform_orders       deps=(read_orders)
    - choose_strategy        deps=(transform_orders) [branch]
    - full_load              deps=(choose_strategy)
    - incremental_load       deps=(choose_strategy)
    - finalise               deps=(full_load, incremental_load) [rule=none_failed]

DAG: etl_to_gcs
  schedule    : @daily
  start_date  : 2026-01-01
  catchup     : False
  description: Read raw orders, validate them, and write a per-region summary.
  tasks (4):
    - read_orders            deps=(-)
    - transform_orders       deps=(read_orders)
    - aggregate              deps=(transform_orders)
    - write_summary          deps=(aggregate)

DAG: templating_paths
  schedule    : @daily
  start_date  : 2026-01-01
  catchup     : False
  description: Render GCS and BigQuery paths from Jinja templates.
  tasks (4):
    - read_orders            deps=(-)
    - render_paths           deps=(read_orders)
    - transform_orders       deps=(render_paths)
    - aggregate              deps=(transform_orders)

DAG: xcom_pipeline
  schedule    : @daily
  start_date  : 2026-01-01
  catchup     : False
  description: Pass the summary between tasks using XCom.
  tasks (5):
    - read_orders            deps=(-)
    - transform_orders       deps=(read_orders)
    - aggregate              deps=(transform_orders)
    - publish_summary        deps=(aggregate)
    - write_summary          deps=(publish_summary)
```

Compare this with the `dag` and `task` tables in Airflow's metadata DB:
`deps=(...)` is the `task.dependencies` column; `[branch]` and
`[rule=none_failed]` are the `task.trigger_rule` column.

### Step 2: Watch the scheduler loop as an ordered walk

The runner's `run_dag` implements the same loop the Airflow scheduler
runs, in miniature. You can watch it step by step:

```bash
cd project
python3 -c "
from local_runner import DAG, Task, run_dag

dag = DAG('loop_demo', tasks=[
    Task('a', lambda run, context: 'a done'),
    Task('b', lambda run, context: 'b done', dependencies=['a']),
    Task('c', lambda run, context: 'c done', dependencies=['a']),
    Task('d', lambda run, context: 'd done', dependencies=['b', 'c']),
])
run = run_dag(dag, '2026-01-15')
for task_id, state in run.state.items():
    print(f'{task_id:<6} {state}')
"
```

Expected output:

```text
a      success
b      success
c      success
d      success
```

Note the fan-out: `b` and `c` both depend on `a`, so both become
runnable at the same scheduler pass. In a real Airflow environment they
run **in parallel** on different workers. The local runner executes them
sequentially, but the graph semantics are identical.

### Step 3: Reproduce the "never ran" state

The distinction between `failed` and `upstream_failed` is worth
reproducing deliberately, because it is the one most alerting rules get
wrong:

```bash
cd project
python3 -c "
from local_runner import DAG, Task, run_dag

dag = DAG('failure_demo', tasks=[
    Task('extract', lambda run, context: 1/0, dependencies=[]),
    Task('transform', lambda run, context: 'x', dependencies=['extract']),
])
run = run_dag(dag, '2026-01-15')
for task_id, state in run.state.items():
    print(f'{task_id:<12} {state}')
print()
print('error recorded under XCom key \'error\':')
print(run.xcom.pull('extract', 'error').splitlines()[-1])
"
```

Expected output:

```text
extract      failed
transform    upstream_failed

error recorded under XCom key 'error':
ZeroDivisionError: division by zero
```

Two lessons:

1. `transform` shows `upstream_failed`, not `failed`. It never ran. Your
   alert should not say "transform failed".
2. **The traceback is stored as an XCom** under the key `error`. In real
   Airflow the same thing happens — the failure traceback is pushed to
   XCom so you can retrieve it with `ti.xcom_pull(task_ids=..., key='error')`.

### Step 4: Confirm the DAG run aggregates its task instances

The DAG run's state is a roll-up of its task instances. The runner
exposes it:

```bash
cd project
python3 -c "
from local_runner import DAGS, run_dag

dag = DAGS['etl_to_gcs']()
run = run_dag(dag, '2026-01-15')
print('dag_id      :', dag.dag_id)
print('logical_date:', run.logical_date)
print('run states  :', dict(run.state))
print('all success :', all(s == 'success' for s in run.state.values()))
print()
print('XCom namespaces (the metadata DB xcom table, in miniature):')
for task_id in run.xcom.store:
    print(' ', task_id, '->', sorted(run.xcom.store[task_id]))
"
```

Expected output:

```text
dag_id      : etl_to_gcs
logical_date: 2026-01-15
run states  : {'read_orders': 'success', 'transform_orders': 'success', 'aggregate': 'success', 'write_summary': 'success'}
all success : True

XCom namespaces (the metadata DB xcom table, in miniature):
  read_orders -> ['return_value']
  transform_orders -> ['accepted', 'rejected', 'return_value']
  aggregate -> ['return_value', 'summary']
  write_summary -> ['gcs_uri', 'local_path', 'return_value']
```

That last block is the miniature of Airflow's `xcom` table. Note the
namespacing: `aggregate`'s `summary` is invisible to `write_summary`
unless it is pulled by task id. That is exactly how Airflow works, and it
is why `ti.xcom_pull(task_ids=...)` needs to name the task.

### Step 5: Read a real Airflow DAG file as the scheduler would

The DAG processor imports the file. You can approximate that locally
*without* Airflow by reading it, but the closest real equivalent is to
check the file compiles and that the DAG-level configuration is sane:

```bash
python3 -m py_compile project/dags/01_hello_world.py && echo "01 parses"
python3 -m py_compile project/dags/02_templating_and_variables.py && echo "02 parses"
python3 -m py_compile project/dags/03_etl_bigquery.py && echo "03 parses"
python3 -m py_compile project/dags/04_branching_and_xcom.py && echo "04 parses"
```

Expected output:

```text
01 parses
02 parses
03 parses
04 parses
```

This is a cheap smoke test. It does **not** catch an Airflow-specific
import error (you would need Airflow installed for that), but it catches
syntax errors, which are the most common parse failure.

### Step 6: Read the deployed DAG's own logs in Composer

Once you upload `01_hello_world.py` to Composer, the import error (if
any) appears in two places:

- **Browse → DAGs** — the DAG is absent from the list, but the file name
  appears with a red import-error marker.
- **Browse → DAGs → \<file\>** — the full traceback.

And the scheduler's own activity is in **Browse → Logs**, showing the DAG
processor's parse messages.

---

## 🛠️ Common Errors and Fixes

### `airflow.exceptions.DagNotFound: DAG: [etl_to_gcs] not found`

The DAG is not registered. Usually the file failed to import. In the
Composer UI, the DAG's detail page shows the import error traceback.
Common causes:

- `ImportError` on a module that is not in the environment.
- A `Variable` or `Connection` lookup at *module scope* (not inside a
  task), which runs during the parse and raises if the object is missing.
- A syntax error.

```python
# WRONG — runs at parse time, on the scheduler, for every parse
from airflow.models import Variable
BUCKET = Variable.get("source_bucket")

# RIGHT — resolves at run time, inside a task
def read():
    from airflow.models import Variable
    bucket = Variable.get("source_bucket", default_var="")
```

### `airflow.exceptions.DagFileExists: The DAG file ... already exists`

Two files, same `dag_id`. Both fail to register.

```bash
grep -h 'dag_id=' project/dags/*.py | sort | uniq -c | sort -rn
```

### `Task is in the 'upstream_failed' state`

The task never ran because a dependency failed. Look **upstream** — the
UI's grid view shows the failing ancestor. The real cause is never the
`upstream_failed` task itself.

In Airflow 2.x this appears in the UI as a distinct state; in some
older versions it showed as `skipped`.

### `Task is in the 'skipped' state`

The task was deliberately skipped. The usual causes:

1. A `BranchOperator` chose a different path.
2. A `ShortCircuitOperator` returned `False`.
3. A dependency was skipped and the trigger rule was `all_success`.

This is **not an error**. If it is unexpected, the bug is almost always
in the trigger rules — see chapter 1.8.

### `Task failed with exception` + `airflow.exceptions.AirflowException: Could not find expected variables`

A Variable was looked up with `Variable.get()` and did not exist, with no
default supplied. Airflow 2.x raises this for the `get_var` family of
methods.

```python
from airflow.models import Variable

# FAILS if the variable is not set
bucket = Variable.get("source_bucket")

# Safe
bucket = Variable.get("source_bucket", default_var="")

# Also safe — the template equivalent
# "{{ var.value.source_bucket | default('') }}"
```

### `AirflowException: Could not find expected variables` on a **Connection**

The same shape, for connections:

```python
from airflow.hooks.base import BaseHook

conn = BaseHook.get_connection("http_orders_api")   # raises if absent
conn = BaseHook.get_connection("http_orders_api")   # raises if absent
```

Give the connection an `extra` JSON field for anything non-standard:

```json
{"project_id": "demo-project", "location": "US"}
```

then read it back with:

```python
import json
extra = json.loads(conn.extra or "{}")
location = extra.get("location", "US")
```

### `CeleryExecutor` errors: `WorkerLostError` / `celery.exceptions.OperationalError`

The scheduler could not reach the worker pool. In Composer this is
almost always a transient network or quota issue; retry the task. On a
self-managed Airflow, check that the broker (RDBMQ or Redis) is up and
that the worker can reach the metadata database.

### `Cannot read the airflow.cfg` style configuration errors

On a self-managed install, this means the `AIRFLOW_HOME` environment
variable is wrong or `airflow.cfg` is missing or unreadable. On Composer
you will not hit this — the environment is pre-configured. If you are
running Airflow locally, the fix is:

```bash
export AIRFLOW_HOME=~/airflow
airflow db init
```

### `airflow.exceptions.AirflowSkipException`

Raised deliberately by a `ShortCircuitOperator` (or by `task.skip()`) to
mark a task skipped. The task's own log shows the message you passed.
It is a control-flow signal, not a failure — but it *does* mark the
task's state as `skipped`, so downstream `all_success` tasks will skip
too.

---

## 💡 Production Notes

- **Keep DAG files free of import-time side effects.** The scheduler
  imports them repeatedly. A module-level API call or DB connection is a
  latency and failure source on every parse.
- **The metadata database is a single point of contention.** Hundreds of
  DAGs, each with a task every minute, generate a lot of writes. If your
  environment's DB CPU is high, the scheduler slows down — and a slow
  scheduler delays *every* DAG in the environment, not just yours.
- **Task logs are written to the metadata DB by default in OSS Airflow;
  Composer routes them to Cloud Logging.** If a task produces a million
  log lines, that is a cost and a performance problem. Log deliberately.
- **Set `max_active_runs` deliberately.** It is the concurrency control
  for a DAG. `1` for pipelines that write to a fixed destination; higher
  for embarrassingly parallel ones.
- **Use `pool` to control concurrency across DAGs.** A pool caps how many
  tasks of a given slot type run at once — the right tool when several
  DAGs all hit the same rate-limited API.
- **Watch the scheduler heartbeat.** A stalled scheduler means no new
  runs are created, which looks identical to "the DAG is not scheduled"
  and is much more confusing to debug.
- **Upgrade the environment in a versioned environment.** Composer's
  Environment Versioning lets you pin Airflow 2.9.3 while you test 2.10
  on a copy.

---

## 🔑 Key Takeaways

- Five components: **DAG processor, scheduler, metadata database,
  executor, workers** — plus the web server. Composer manages all of them.
- The **scheduler is a polling loop**: create DAG runs → create task
  instances → evaluate → queue → check SLAs → clean up. It decides
  *what* runs; workers decide *how*.
- The **DAG processor imports your Python files**, so top-level code runs
  on the scheduler and an import error removes the DAG entirely.
- The **metadata database is the source of truth** — including XCom,
  which is why XCom is a database, not a dict.
- **DAG run vs task instance**: one run per logical date; one task
  instance per task per run. Both have their own state machines.
- **`failed` ≠ `upstream_failed` ≠ `skipped`**. The first ran and
  raised, the second never ran, the third was deliberately skipped.
- Airflow 2 is a **hybrid**: a workflow manager that grew data-processing
  responsibilities (operators, TaskFlow, datasets, dynamic mapping).
- Composer changes the **operations**, not the **semantics**.

---

## 📚 Practice Exercises

1. **Map the components.** For each of the five components, name one
   concrete symptom of it being broken. (Hint: the scheduler being down
   and the worker pool being down produce very different symptoms.)

2. **Two state machines.** List every state a task instance can be in,
   and every state a DAG run can be in. Which task states can a DAG run
   be in that are not just "the worst task state"?

3. **Reproduce the parser.** Write a DAG file with a deliberate
   `ImportError` at module scope, then reason about exactly what the
   Composer UI would show. Then move the import inside the task
   callable and explain why that fixes it.

4. **Parallel fan-out.** Build a DAG with one task fanning out to four
   parallel tasks, each taking a different simulated duration. Show
   that the graph permits concurrency, and explain what the local runner
   does differently from a real CeleryExecutor.

5. **The XCom table.** The `xcom` table has columns `dag_id`, `task_id`,
   `run_id`, `key`, `value`, `timestamp`. Using the Step 4 output,
   reconstruct the exact rows the `xcom` table would contain for one
   `etl_to_gcs` run.

6. **Reflection.** "Airflow is a hybrid of a workflow manager and a data
   processor." Give one concrete benefit of each half that the other
   half cannot provide, and one concrete cost that the hybrid imposes.

---

## 📖 Further Reading

- Airflow architecture — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/architecture.html
- Airflow DAG runs — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html
- Airflow task instances — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#taskinstances
- Airflow executors — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/index.html
- Airflow database migrations reference — https://airflow.apache.org/docs/apache-airflow/stable/migrations-ref.html
- Google Cloud Composer architecture — https://cloud.google.com/composer/docs/how-to/managing/about
- Airflow 2.0 release blog (the hybrid thesis) — https://airflow.apache.org/blog/apache-airflow-2
