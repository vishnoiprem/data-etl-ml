# 25 — Orchestration and DAGs (Airflow, Dagster, Prefect)

> **Lesson 25 of 30 — Performance & Fault Tolerance**

The orchestrator is the brain of a pipeline. It schedules
tasks, sequences them, retries failures, and reports status.
This lesson is the *what an orchestrator does* and the *three
tools* every interviewer knows.

---

## 1. What an orchestrator does

A pipeline orchestrator manages the lifecycle of a DAG of
tasks:

| Capability | What it does |
|---|---|
| **Scheduling** | Run the DAG on a cron schedule or trigger. |
| **Sequencing** | Run task B after task A, task C after B and A. |
| **Retry** | If a task fails, retry with backoff. |
| **Backfill** | Re-run a task for a past date range. |
| **Alerting** | Page on-call if a task fails after all retries. |
| **Observability** | Show task duration, status, logs. |
| **Lineage** | Track upstream and downstream of each task. |

The senior move: name all seven unprompted. "The orchestrator
schedules, sequences, retries, backfills, alerts, observes,
and tracks lineage."

---

## 2. The DAG as code

A DAG is a directed acyclic graph of tasks. Modern
orchestrators treat it as code:

```python
# Airflow
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

with DAG("daily_orders", start_date=datetime(2024, 1, 1), schedule="@daily") as dag:
    extract = PythonOperator(task_id="extract", python_callable=extract_fn)
    transform = PythonOperator(task_id="transform", python_callable=transform_fn)
    load = PythonOperator(task_id="load", python_callable=load_fn)
    extract >> transform >> load
```

The `>>` operator declares dependencies. The orchestrator
topologically sorts and runs them. The senior move: every DAG
has clear dependencies; no "magic" sequencing.

---

## 3. The three orchestrators

| | Airflow | Dagster | Prefect |
|---|---|---|---|
| **DAG as** | Python file | Python with typed assets | Python with `@flow` / `@task` |
| **Strength** | Mature, huge ecosystem | Strong typing, asset-centric | Pythonic, hybrid execution |
| **Weakness** | DAGs get messy past 100 tasks | Smaller ecosystem | Newer, smaller community |
| **Best for** | Traditional ETL | Asset-driven, modern stacks | Python-first teams |

The senior move: "For most teams I'd default to Airflow. For
modern asset-driven teams I'd use Dagster. For Python-first
small teams I'd use Prefect. All three solve the same
problem."

---

## 4. The DAG patterns

Three patterns every production DAG uses:

**Pattern 1: linear.** Task A → Task B → Task C. The simplest.

**Pattern 2: fanout.** Task A → [B, C, D]. Used to parallelize
independent work after an extract.

**Pattern 3: diamond.** A → B, A → C, (B, C) → D. Used when
two parallel branches must complete before a final step.

```
Linear:    A → B → C

Fanout:    A → B
          A → C
          A → D

Diamond:   A → B → D
          A → C ↗
```

The senior move: name the three patterns. Most production
DAGs are combinations of these.

---

## 5. The scheduler

The orchestrator's scheduler decides *when* to run a DAG.
Three trigger types:

- **Cron.** Run at a specific time. "Every day at 6 AM."
- **Interval.** Run every N minutes. "Every hour."
- **Event.** Run when an upstream event fires. "When the
  CDC stream emits a heartbeat."

The senior move: name the trigger unprompted. "The DAG is
triggered by a 6 AM cron, but we also have a manual trigger
for backfills."

---

## 6. The backfill

A backfill is a re-run of a DAG for a past date range:

```bash
airflow dags backfill --start-date 2024-01-01 --end-date 2024-01-15 daily_orders
```

The orchestrator spawns one DAG run per date, with the
execution date set to that date. The pipeline uses the
execution date to read the correct partition. The senior
move: every DAG must be *idempotent* so backfills don't
produce duplicates.

---

## 7. The sensor pattern

A *sensor* is a task that waits for an external condition:

```python
@task.sensor
def s3_key_exists(key):
    return s3.head_object(Bucket="data", Key=key) is not None
```

Sensors are useful for event-driven pipelines: "wait for the
producer's `_SUCCESS` marker, then run the load." The senior
move: name the sensor pattern. "The DAG is triggered by an
S3 sensor that waits for the producer's marker file."

---

## 8. The failure modes

| Failure | Mitigation |
|---|---|
| Task fails | Retry with backoff; alert after max attempts. |
| Worker dies | Orchestrator reschedules on a different worker. |
| Database down | Connection pool waits; alert on wait time. |
| Backfill too slow | Increase parallelism; use mapped tasks. |
| DAG has cycle | DAG validation rejects cycles. |

The senior move: name the worker-dies failure mode. "If a
worker dies mid-task, the orchestrator reschedules on a
different worker. The task is idempotent so the retry is
safe."

---

## 9. The code: `code/orchestrator.py`

The course provides a tiny DAG runner:

```python
from data_pipeline_design.06_performance.code.orchestrator import Dag

dag = Dag("daily_orders")
dag.add_task("extract", extract_fn)
dag.add_task("transform", transform_fn, depends_on=["extract"])
dag.add_task("load", load_fn, depends_on=["transform"])
result = dag.run()
```

The test in `tests/test_perf.py` exercises a 5-task diamond
DAG and asserts the correct execution order.

---

## 10. The interview answer

> "I'd use Airflow for most ETL DAGs, Dagster for
> asset-driven modern stacks, or Prefect for Python-first
> teams. The DAG has clear dependencies (`>>`), the trigger
> is a cron plus a sensor for event-driven, and every task
> is idempotent so backfills are safe. The orchestrator
> handles retry with backoff, alerting, and lineage. The
> deep dive would be the failure modes — worker dies, task
> fails, backfill is too slow — and the mitigations."

That single paragraph covers: tool choice, DAG mechanics,
trigger types, idempotency, failure modes. Senior answer in
30 seconds.

---

## Try it

Look at the most recent DAG you've worked on. Is it linear,
fanout, or diamond? Is the trigger a cron or an event? Is
every task idempotent? Is there a sensor for the producer's
marker? If any is "no," the DAG is fragile.
