# 1.1 — What Is Orchestration and Why Airflow

> **Section 1 · Composer Fundamentals & Model · Lecture 1.1 · 8:00**

## 🎯 What you will learn

- Why orchestration exists, and the failure mode it removes from a data platform
- What a *data pipeline* does versus what an *orchestrator* does — and why mixing them is expensive
- The DAG mental model: nodes, edges, and why "directed acyclic" is a feature, not a limitation
- Task vs workflow, and why the distinction decides who owns retry logic
- The 3am question — *"did today's data land?"* — and how a scheduler turns it into a query
- How Airflow fits alongside Spark and Beam: the orchestrator is not the engine

---

## 🧠 Concept

### The problem: pipelines multiply, coordination does not

Start with one pipeline. A cron job copies yesterday's orders out of a
database, cleans them, and writes a CSV. It works. Nobody is paged.

Then the business asks for six more things: regional revenue rollups, a
live dashboard, a fraud score, a daily email, a partner feed, and a
month-end finance close. Each is a script. Each has its own scheduler.
Each reads from the same source tables.

Now count the dependencies. The fraud score needs cleaned orders *and* the
customer segment table. The dashboard needs the fraud score. The partner
feed needs the regional rollup. The finance close needs everything, and it
must run at 02:00 local time on the first of the month, after the nightly
rollup has finished, even if the nightly rollup took eleven hours.

You now have a **distributed system**. It has no scheduler, no retry
policy, no alerting, no way to answer "what state is the March 3rd run in?"
except by reading seven log files on seven machines. One script fails at
02:14. Three downstream scripts start anyway and produce partial results.
Nobody notices until the morning dashboard shows a number that is wrong by
eleven percent.

The failure mode is not "the script crashed." It is **"the pipeline
crashed, and half the system kept going."** That is the problem
orchestration solves.

### What a pipeline does vs what an orchestrator does

These are two different jobs, and conflating them is the single most
common architectural mistake in data engineering.

| | A data pipeline | An orchestrator |
|---|---|---|
| **Job** | transform data | decide *when* and *in what order* |
| **Granularity** | one computation over a dataset | many tasks, many datasets |
| **State** | usually stateless | rich: run history, task states, retries |
| **Failure** | exception | exception *plus* retry, skip, alert, backfill |
| **Interface** | function, script, SQL | DAG of tasks with dependencies |
| **Example** | `transform_orders()` | the `etl_to_gcs` DAG |

The pipeline is the **engine**. The orchestrator is the **control plane**.

In Airflow terms: `transform_orders()` in `project/core/pipeline_logic.py`
is a pipeline. The DAG file that calls it and says "run this after that"
is the orchestrator. Airflow itself is the orchestrator — it does not
transform anything. It runs your transformations, in the right order, on
the right date, and it knows what happened.

This is why the course splits the project in two:

```text
project/core/pipeline_logic.py   ← the pipeline (pure, testable, no Airflow)
project/dags/03_etl_bigquery.py  ← the orchestration (Airflow import, DAG object)
```

The business rules live in the first file. The second file is thin: it
declares dependencies, sets policies, and calls into the first. You can
unit-test the first in milliseconds with no Airflow installed, and you
can read the second in five seconds and understand the shape of the
workflow.

### The DAG mental model

A **DAG** is a Directed Acyclic Graph. Stripped down:

- **Nodes** are tasks — a unit of work with a defined outcome.
- **Edges** are dependencies — "this must finish before that starts."
- **Directed** means the edges have an order: A → B means A first.
- **Acyclic** means there is no loop. No cycles means there is always a
  topological order, so the graph is always schedulable.

Here is the course's main pipeline as a graph:

```text
        ┌──────────────┐
        │ read_orders  │
        └──────┬───────┘
               │
        ┌──────▼───────────┐
        │ transform_orders │  ← validation happens here
        └──────┬───────────┘
               │
        ┌──────▼────────┐
        │   aggregate   │  ← summarise_by_region()
        └──────┬────────┘
               │
        ┌──────▼────────────┐
        │   write_summary  │  ← render_summary_csv() → GCS
        └───────────────────┘
```

In Airflow you write the edges with `>>`:

```python
read >> transform >> aggregate >> write
```

or, more commonly, in a `with DAG(...)` block:

```python
read_orders >> transform_orders >> aggregate >> write_summary
```

The critical insight: **the graph describes order, not time.** Nothing in
the DAG says "the aggregate waits 30 minutes for the transform." The DAG
says "the aggregate runs after the transform *succeeds*." Timing is the
scheduler's job; ordering is the graph's job. Keeping those separate is
what makes a DAG portable across environments with wildly different
throughput.

#### Why acyclic is a feature

A cycle would mean "A waits for B, B waits for A." There is no
well-defined first task, so no execution order exists. Airflow rejects
cycles at parse time — your DAG simply does not appear in the UI.

More importantly, acyclicity buys you something subtle: **a DAG can be
analysed as a whole.** You can ask "what are the upstream dependencies of
this table?", "which tasks are on the critical path?", "if this task
fails, what else is affected?". With cycles, those questions have no
well-defined answers.

The cost of acyclicity is that **looping must be expressed as repetition,
not as a graph edge**. "Process each of the 500 customer files" is 500
runs of the same DAG (or one DAG with a dynamic task mapping), not a task
that points at itself. This is a deliberate design decision, and it is
the right one — it turns "loop until done" into "a set of independently
retriable, independently observable runs."

### Task vs workflow

| | Task | Workflow |
|---|---|---|
| **Definition** | one node in a DAG | the whole DAG |
| **Identity** | `task_id` | `dag_id` |
| **State** | one of `success` / `failed` / `skipped` / `upstream_failed` / `running` / `queued` | one of `success` / `failed` / `running` / `queued` |
| **Retries** | per task | per DAG (via `default_args`) |
| **Runs** | one instance per DAG run | many runs, one per logical date |
| **Example** | `aggregate` | `etl_to_gcs` |

The vocabulary matters because Airflow has **two nested state machines**:

```text
DAG run  (one per logical date)
  ├── Task instance: read_orders        → success
  ├── Task instance: transform_orders   → success
  ├── Task instance: aggregate          → success
  └── Task instance: write_summary      → failed
        └── retries: 1 of 2 remaining
```

The DAG run's state is derived from its task instances' states. The
scheduler asks a different question for each level:

- **At the task level:** "Are all my dependencies successful, and has the
  scheduler given me a worker?" → run me.
- **At the DAG level:** "Have all my task instances reached a terminal
  state?" → the DAG run is done.

### The 3am question

*"Did today's data land?"*

This is the question an orchestrator exists to answer, and it is worth
being precise about why it is hard without one.

To answer it you need to know, for a given **date**:

1. Did the pipeline **run**? (Was it even scheduled? Did the scheduler see it?)
2. Did it **succeed**? (Did every task succeed, or did some fail and get retried?)
3. Did it produce the **right data**? (Did it load *yesterday's* partition, or *today's*?)

Point 3 is the one that bites. The subtlety is that Airflow's **logical
date** is not the wall-clock time the task ran. A daily DAG scheduled at
`02:00` runs *after* midnight but processes *yesterday's* data. Its
logical date is yesterday. The distinction is deliberate and is the
subject of chapter 1.3; the point here is that a system that logs
"02:00 job started, finished OK" cannot answer point 3, because it never
recorded which data it was supposed to be processing.

Airflow records the logical date on the run, the task instances, and
every log line, every XCom, and every rendered template. It is the
primary key of "which run am I talking about."

That is the 3am answer, and it is a *single lookup* rather than a forensic
investigation across seven machines.

### How Airflow fits vs Spark and Beam

This is the question that trips up people coming from Spark or Beam, and
it deserves a crisp answer.

| | Airflow | Spark | Beam |
|---|---|---|---|
| **Category** | orchestrator | compute engine | compute model |
| **Unit of work** | task in a DAG | RDD/DataFrame | PCollection/PTransform |
| **Data processing** | *no* — it runs your code | yes | yes (via a runner) |
| **Scheduling** | yes — its main job | no (Spark on Databricks/YARN schedules it) | no (Dataflow / Dataflow Streaming schedule it) |
| **Dependencies between jobs** | yes — first-class | no (use Airflow) | no (use Airflow) |
| **Retries, alerting, backfill** | yes | no | no |
| **Scale** | thousands of tasks per day | billions of rows | billions of rows |

The rule: **Airflow is not a replacement for Spark or Beam; it is what
sits above them.**

```text
┌──────────────────────────────────────────────┐
│  Airflow / Composer                          │  ← WHEN, IN WHAT ORDER
│  ┌────────┐  ┌────────┐  ┌────────┐         │
│  │ extract│→ │transform│→ │  load  │         │  ← WHAT
│  └────────┘  └────────┘  └────────┘         │
│      │           │            │             │
│      └───────────┴────────────┘             │
│                  │                          │
│            ┌─────▼──────┐                   │
│            │ Spark job  │                   │  ← HOW (the engine)
│            │ Beam on    │                   │
│            │ Dataflow   │                   │
│            └────────────┘                   │
└──────────────────────────────────────────────┘
```

A realistic Composer DAG runs a Spark submit, a Dataflow template, or a
BigQuery job as *one task inside* a larger workflow. The point of the
orchestrator is not to be fast at transforming data — it is to be
reliable at coordinating many transformations that depend on each other.

Two corollaries worth internalising:

1. **If your pipeline is one big Spark job and nothing depends on
   anything else, you do not need Airflow.** A cron job is fine. This is
   a real and valid architecture for simple batch work.
2. **The moment you have a dependency, a retry policy, a backfill
   requirement, or someone asking "why did Tuesday fail?", you need an
   orchestrator.** Airflow is the most common one, and Google Cloud
   Composer is the managed version of it.

### Where Composer fits

Google Cloud Composer is a managed Apache Airflow service. You upload
Python DAG files; Google runs the scheduler, the web server, the workers,
and the metadata database for you.

```text
Your laptop                Google Cloud
───────────                ────────────
DAG files  ──── upload ───▶  Composer environment
                              ├─ Airflow scheduler
                              ├─ Airflow web server (UI + REST API)
                              ├─ Airflow workers (Celery executor)
                              ├─ Airflow metadata DB (Cloud SQL)
                              └─ GCS-backed DAG storage
```

Two consequences for this course:

- **You do not need a local Airflow install.** Composer is the runtime.
  Everything in `project/core/` is pure Python precisely so you can
  learn, test and verify without one.
- **The DAG files are the deployable artefact.** `project/dags/*.py` are
  real Airflow 2.x DAGs. They are what you upload to Composer. The
  local runner is a teaching aid that runs the *same core functions* with
  a miniature scheduler.

---

## 🛠️ Hands-On

### Step 1: Generate the sample dataset

The dataset is deterministic — same seed, same bytes, every time. That
is what lets this course print exact expected outputs.

```bash
cd data-engineering/data-Course/google/composer
python resources/sample_data.py --output-dir ./sample_data
```

Expected output:

```text
INFO wrote sample_data/orders.csv (5000 rows)
INFO wrote sample_data/orders.ndjson (5000 rows)
INFO wrote sample_data/malformed_orders.csv (5 lines)
INFO wrote sample_data/product_reference.ndjson (50 rows)
INFO sample data ready in .../composer/sample_data
INFO summary: {'orders': 5000, 'malformed_rows': 5, 'reference_rows': 50, 'target_date': '2026-01-15'}
```

### Step 2: See what the runner knows about

```bash
python project/local_runner.py --list
```

Expected output:

```text
Available DAGs:
  - branching_load
  - etl_to_gcs
  - templating_paths
  - xcom_pipeline
```

Four DAGs, four different orchestration patterns. They are the executable
version of this chapter's ideas.

### Step 3: Describe the graph before running it

```bash
python project/local_runner.py --dag etl_to_gcs --describe
```

Expected output:

```text
DAG: etl_to_gcs
  schedule    : @daily
  start_date  : 2026-01-01
  catchup     : False
  description : Read raw orders, validate them, and write a per-region summary.
  tasks (4):
    - read_orders            deps=(-)
    - transform_orders       deps=(read_orders)
    - aggregate              deps=(transform_orders)
    - write_summary          deps=(aggregate)
```

Read that as a graph: four nodes, four edges, one chain. `deps=(-)` means
no dependencies. This is the `>>` operator, printed.

### Step 4: Run it and watch the state machine

```bash
python project/local_runner.py --dag etl_to_gcs --verbose
```

Expected output (trimmed):

```text
▶ Running etl_to_gcs @ 2026-01-15

  Run summary for etl_to_gcs @ 2026-01-15
  ----------------------------------------------------
    ✓ read_orders            success
    ✓ transform_orders       success
    ✓ aggregate              success
    ✓ write_summary          success

  ✓ etl_to_gcs succeeded

region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

And the validation counters are:

```text
accepted=1245 rejected=0
```

Keep those two blocks in your head. Every chapter in this course that
touches the data pipeline asserts against them.

### Step 5: Separate the pipeline from the orchestration

This is the most important exercise in the chapter. Run the *business
logic* directly, with no runner and no Airflow:

```bash
cd project/core
python3 -c "
from pipeline_logic import transform_orders, summarise_by_region, render_summary_csv
lines = open('../../sample_data/orders.csv').read().splitlines()
accepted, rejected = transform_orders(lines)
print('accepted', len(accepted), 'rejected', len(rejected))
print(render_summary_csv(summarise_by_region(accepted)))
"
```

Expected output:

```text
accepted 1245 rejected 0
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

Identical to the orchestrated run. That is the whole point: **the
orchestration added ordering, state tracking and reporting — and changed
nothing about the data.** If a DAG change alters the numbers, the bug is
in the logic or in the ordering, and you now have a way to tell them
apart.

### Step 6: See the workflow (not just the task) fail

Force a task to fail and watch how the *downstream* tasks are affected.
The runner's `_execute_task` marks a task `failed`; everything downstream
becomes `upstream_failed`.

```bash
cd project
python3 -c "
from local_runner import DAG, Task, run_dag

def boom(run, context):
    raise RuntimeError('upstream API returned 500')

dag = DAG(
    'demo_failure',
    tasks=[
        Task('extract', boom, dependencies=[]),
        Task('transform', lambda run, context: 'never runs', dependencies=['extract']),
        Task('load', lambda run, context: 'never runs', dependencies=['transform']),
    ],
)
run = run_dag(dag, '2026-01-15', verbose=True)
"
```

Expected output:

```text
  Run summary for demo_failure @ 2026-01-15
  ----------------------------------------------------
    ✗ extract                failed
    ⊘ transform              upstream_failed
    ⊘ load                   upstream_failed
```

Two states, two meanings:

- `failed` — this task ran and raised.
- `upstream_failed` — this task **never ran**; a dependency failed.

Airflow's UI renders them differently for exactly this reason. A task
that never ran has no output; a task that failed may have written partial
data before dying. Conflating them in your alerting produces false
"task failed" pages for tasks that never started.

### Step 7: Check the DAG files you will deploy

The DAG files in `project/dags/` are real Airflow 2.x DAGs. Read one:

```bash
head -40 project/dags/01_hello_world.py
```

The structure is:

```python
with DAG(
    dag_id="hello_world",
    schedule="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["tutorial", "composer"],
    params={"audience": "data-engineers"},
) as dag:
    greet = PythonOperator(task_id="say_hello", python_callable=say_hello)
    print_date = BashOperator(task_id="print_date", bash_command="echo 'Run date: {{ ds }}'")
    greet >> print_date
```

That `with DAG(...)` block is the graph. The `>>` at the bottom is the
edge. Nothing else in the file is orchestration.

---

## 🛠️ Common Errors and Fixes

### `airflow.exceptions.DagNotFound: DAG: [my_dag] not found`

You referenced a DAG id that does not exist. Common causes:

1. **Typo in the `dag_id`** — check the DAG list in the Composer UI.
2. **The file failed to import.** A DAG whose Python file raises at import
   time never registers. Look for the parse error in the Airflow UI under
   **Browse → DAGs → \<filename\>** — it shows the traceback.
3. **The file is not in the `dags/` bucket.** Composer only parses files
   under the configured DAGs folder.
4. **You edited a DAG but the scheduler has not re-parsed it.** Composer
   re-parses on a timer (typically 1–3 minutes). Force it from the UI or
   wait.

```bash
# Locally-equivalent check: does the DAG id exist in the runner?
python project/local_runner.py --list
```

### `airflow.exceptions.DagFileExists: The DAG file ... already exists`

Two DAG files declare the same `dag_id`. In Airflow 2.x this is an import
error and **neither** DAG registers — which is worse than a duplicate
that merely overwrites, because you get no DAG at all.

```bash
# Find duplicate dag_ids across your DAG files
grep -h 'dag_id=' project/dags/*.py | sort | uniq -c | sort -rn
```

The fix: give each DAG a unique id. Convention is
`<domain>_<subject>` — `etl_orders_to_bigquery`, not `my_dag`.

### `ImportError: cannot import name 'transform_orders' from 'pipeline_logic'`

The DAG file cannot see the core module. In Composer the DAGs folder and
the core module must be **siblings in the same uploaded package** (or the
core module must be installed into the environment):

```text
dags/
  dag_config.py
  pipeline_logic.py
  03_etl_bigquery.py
```

Locally, the runner handles this with `sys.path` insertion. When you
deploy, you either upload the whole `dags/` tree or add the path in the
DAG:

```python
import sys
sys.path.append("/opt/airflow/dags/your_package")
```

### `FileNotFoundError: .../sample_data/orders.csv not found`

The local runner needs the sample data. Generate it:

```bash
python resources/sample_data.py --output-dir ./sample_data
```

The runner's own error message says exactly this:

```text
.../sample_data/orders.csv not found. Generate it first:
  python resources/sample_data.py --output-dir ./sample_data
```

### `ModuleNotFoundError: No module named 'airflow'`

Expected — and fine. This course's premise is that you learn Composer
*without* a local Airflow install. The pure core runs without it:

```bash
cd project/core && python3 -c "import pipeline_logic; print('ok')"
```

If you *do* want Airflow locally for experimentation:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install "apache-airflow==2.9.3" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.12.txt"
```

### The DAG "succeeds" but the output is empty

The task ran and returned nothing, but nothing consumed it. In Airflow, a
task's return value goes to XCom — it does **not** write files or tables
by itself. If your task is supposed to write to BigQuery, it must do so
explicitly (or use `BigQueryInsertJobOperator`).

Check what the task actually returned:

```python
run.outputs["aggregate"]
```

### `Task failed with exception` + a traceback

The general shape of a real task failure in Airflow 2.x:

```text
*** Task failed with exception
Traceback (most recent call last):
  File "/usr/local/lib/python3.11/site-packages/airflow/models/taskinstance.py", line 1162, in _execute_task
    result = _execute_callable(context=context, **execute_callable_kwargs)
  File "/opt/airflow/dags/dags/03_etl_bigquery.py", line 71, in validate_and_stage
    bq_dataset = context["var"].get("bq_dataset", "analytics")
  File "/usr/local/lib/python3.11/site-packages/airflow/models/variable.py", line 222, in get
    raise AirflowException(f"Could not find expected variables")
airflow.exceptions.AirflowException: Could not find expected variables
```

Read the traceback **bottom-up**: the last line is the exception, the
lines above it are the call stack that got you there. The Airflow
framework frames (`_execute_callable`, `_execute_task`) are noise; the
frame in your DAG file is the culprit.

---

## 💡 Production Notes

- **Separate the pipeline from the orchestration, always.** Put business
  logic in pure modules with no Airflow import; keep DAG files thin. You
  get fast tests and a readable graph.
- **A DAG file is not a test.** If your logic cannot be imported without
  Airflow, you cannot unit-test it. `project/core/pipeline_logic.py`
  imports nothing from Airflow for exactly this reason.
- **One DAG per business process, not one DAG per team.** The DAG should
  map to something a stakeholder can name — "daily order revenue" — not
  to a technical decomposition.
- **Always set `retries` and `retry_delay` for anything touching a
  remote system.** Transient network errors are the normal case, not the
  exception.
- **Always set `catchup=False` unless you genuinely want backfills.**
  Chapter 1.3 covers why this is dangerous.
- **Give every DAG a `description` and `tags`.** They show in the UI and
  are how people find your DAG when they need to.
- **Use `max_active_runs=1` for pipelines that write to the same
  destination.** Two concurrent runs can interleave and double-write.
- **Start DAGs with a small `start_date`, not today's date.** The
  `start_date` is the earliest logical date Airflow will consider.

---

## 🔑 Key Takeaways

- Orchestration exists because **pipelines multiply but coordination does
  not** — and a half-failed pipeline that keeps running is worse than
  one that stops.
- A **pipeline** transforms data; an **orchestrator** decides when and in
  what order. Airflow is the orchestrator, not the engine.
- The **DAG** is nodes (tasks) plus edges (dependencies). Acyclic means
  always schedulable; loops must be expressed as repeated runs.
- **Task vs workflow**: a task is one node with its own state and retry
  policy; a workflow is the whole graph, run once per logical date.
- The **3am question** — "did today's data land?" — is answerable in one
  lookup only because Airflow records the *logical date* on every run,
  task, log line and XCom.
- Airflow does **not** replace Spark or Beam. It sits above them and
  orchestrates them.
- The **local runner** lets you verify orchestration locally, with no
  Airflow install, against the same pure core the DAGs deploy.

---

## 📚 Practice Exercises

1. **Prove the separation.** Add a new pure function to
   `project/core/pipeline_logic.py` that renders the summary as JSON.
   Verify it from a plain `python3 -c` call (no runner) and then verify
   the DAG still produces the same numbers. Why does the second check
   pass trivially?

2. **Map the graph.** Rewrite `etl_to_gcs` as an explicit adjacency list
   (a dict of task_id → list of upstream task_ids) in a scratch file, and
   print the topological order. Confirm it matches
   `read_orders → transform_orders → aggregate → write_summary`.

3. **Build a diamond.** Construct a DAG in the runner with
   `read → [transform_a, transform_b] → join`, where `join` depends on
   both. Run it and print the states. Then change `join`'s
   `trigger_rule` to `"none_failed"` and re-run. What changed, and which
   chapter explains why?

4. **Count the edges.** Using `project/local_runner.py --describe`, count
   the tasks and dependency edges in each of the four DAGs. Which DAG has
   more edges than tasks? What does that imply about its shape?

5. **The 3am question.** In plain English, explain why "the task logged
   success at 02:04" is not an answer to "did today's data land?" What
   extra piece of information does Airflow record that closes the gap?

6. **Engine or orchestrator.** A teammate says: "We should rewrite our
   Spark job as an Airflow DAG so Airflow can do the joins faster."
   Write a two-paragraph response explaining why that is the wrong use of
   Airflow, and what the right architecture is.

7. **Reflection.** Explain the statement "the graph describes order, not
   time" to someone who has only written cron jobs. Give one concrete
   scenario where the difference matters.

---

## 📖 Further Reading

- Apache Airflow documentation — https://airflow.apache.org/docs/apache-airflow/stable/index.html
- Apache Airflow Core concepts (DAGs, tasks, scheduling) — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html
- Airflow best practices — https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html
- Google Cloud Composer overview — https://cloud.google.com/composer/docs/how-to/managing/about
- Airflow architecture (scheduler, executor, workers) — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/architecture.html
- "Airflow: A Platform to Programmatically Author, Schedule and Monitor Data Pipelines" (the paper) — https://airflow.apache.org/paper.html
