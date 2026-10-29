# 4.9 — Sensors & Deferrable Operators

> **Section 4 · Advanced Orchestration · Lecture 4.9 · 7:00**

## 🎯 What you will learn

- What a sensor actually is: a task that refuses to finish until a condition is true
- `mode="poke"` versus `mode="reschedule"` — and why the choice is a *capacity* decision, not a style preference
- The three knobs every sensor has: `timeout`, `poke_interval`, `soft_fail`
- Why every sensor is expensive: a sensor holds a **worker slot** for its whole life
- Deferrable operators, the triggerer, and `airflow.exceptions.TaskDeferred`
- `ExternalTaskSensor` — cross-DAG waiting, and why it is more fragile than it looks
- The sensor-as-anti-pattern discussion: when "wait for X" should be a schedule, a dataset, or a callback

---

## 🧠 Concept

### What a sensor is

A normal Airflow task has one job: run the callable, then finish. It succeeds or it fails, and in both cases the task instance reaches a terminal state and the worker slot is released.

A **sensor** breaks that contract. A sensor's callable returns a boolean:

- `True` → the condition is met, the sensor task succeeds, the DAG moves on.
- `False` → the condition is not met. The sensor **does not fail**. It neither succeeds nor fails. It *waits*.

That third outcome is the whole point. Airflow records the task instance in the `running` state and, depending on the mode, either re-invokes the callable later or re-queues the task for later.

```text
sensor.execute(context)
        │
        ├── returns True  ──▶ task succeeds ──▶ downstream runs
        │
        └── returns False ──▶ task stays `running`
                                │
                                ├── poke mode:      re-invoke the callable after poke_interval
                                └── reschedule mode: release the slot, re-queue the task
```

### Poke mode

In `mode="poke"` (the default), the worker **stays occupied** and the callable is called again every `poke_interval` seconds until it returns `True` or the timeout expires.

```python
from airflow.sensors.python import PythonSensor

sensor = PythonSensor(
    task_id="wait_for_upstream_data",
    python_callable=wait_for_upstream_data,
    mode="poke",
    timeout=3600,
    poke_interval=300,
    soft_fail=True,
)
```

This is the mode the course's own `04_branching_and_xcom.py` DAG *mentions* but deliberately does not use — it uses `mode="reschedule"`.

The economics: a sensor in poke mode consumes one worker slot for its entire lifetime. A sensor with `timeout=3600` and `poke_interval=300` holds a slot for up to an hour, calling the callable 12 times, doing approximately nothing 11 times out of 12.

### Reschedule mode

In `mode="reschedule"`, when the callable returns `False`, Airflow sets the task instance back to `scheduled` with a start time of `now + poke_interval`, and **releases the worker slot**. The task is picked up again later by the scheduler, on whatever worker happens to be free.

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

The economics: the sensor holds a slot only for the *duration of one call to the callable*. If the callable is a quick HTTP HEAD request, that is milliseconds.

The trade-off is latency. In reschedule mode, the check granularity is `poke_interval`, and the task can wait for the scheduler to pick it up again. In poke mode, detection is immediate — the callable is called the moment the interval elapses, without a scheduling round-trip.

| | `mode="poke"` | `mode="reschedule"` |
|---|---|---|
| Worker slot | held for the whole wait | held only during each check |
| Detection latency | ~`poke_interval` | ~`poke_interval` + scheduler delay |
| Worker utilisation | wasted while waiting | free while waiting |
| Best for | short waits (< 2–3 min) | long waits (> a few minutes) |
| Risk under load | can exhaust the worker pool | scheduler pressure from re-queued tasks |

**The rule of thumb:** poke for minutes, reschedule for anything longer. And on Composer specifically, reschedule is usually the right default because the worker pool is sized for your DAGs, and a pile of poke-mode sensors is the fastest way to hit the concurrency ceiling.

### The three knobs

Every sensor has the same three parameters, and they are constantly confused with each other.

**`timeout`** — how long the sensor is allowed to wait *in total*, before it gives up and fails. Airflow computes it from the task's start time, not from the number of pokes.

```text
Timeout: 3600.0s
```

That is the literal error message Airflow raises when the timeout elapses:

```text
airflow.exceptions.AirflowSensorTimeout: Timeout: 3600.0s
```

The message is deliberately uninformative: it tells you the total budget was exhausted, and nothing about *how many times it polled* or *what the condition was*. When you see this in the UI, go and read the sensor's log lines, which have the detail.

**`poke_interval`** — how long to wait between checks. It must be smaller than `timeout`, or the sensor may time out before it ever gets a second look.

**`soft_fail`** — what happens when the timeout expires.

| `soft_fail` | On timeout | The DAG |
|---|---|---|
| `True` (default) | the sensor task **succeeds** | downstream tasks run normally |
| `False` | the sensor task **fails** | downstream tasks are `upstream_failed` |

This is the single most misunderstood parameter in Airflow. A `soft_fail=True` sensor that times out does **not** stop the pipeline. It reports success and lets the pipeline continue with whatever data exists.

That is exactly the right behaviour for "wait for yesterday's upstream file, and if it never arrives, carry on with what we have" — and exactly the wrong behaviour for "wait for the reconciliation to complete before we close the books".

The course's `04_branching_and_xcom.py` uses `soft_fail=True`, and the docstring for `wait_for_upstream_data` explains the intent:

```python
def wait_for_upstream_data(**context) -> bool:
    """Poll until the upstream data is ready.

    A sensor *resumes* the task when its condition is met; it does not
    busy-wait in a loop. The Airflow worker is released while the sensor
    waits, and the task is re-evaluated later.
    """
    expected_rows = int(context["params"].get("expected_rows", 0))
    actual_rows = int(context["params"].get("row_count", 0))
    ready = actual_rows >= expected_rows
    log.info("sensor: expected>=%d actual=%d ready=%s", expected_rows, actual_rows, ready)
    return ready
```

### Why sensors are expensive: the worker slot

Here is the fact that decides sensor design.

> **A sensor occupies a concurrency slot for its entire lifetime.**

Airflow's concurrency limit (`max_active_tasks_per_dag`, and the environment-wide `parallelism`) counts *running task instances*. A running sensor is a running task instance. So 50 sensors, each waiting an hour, consume 50 of your slots — even though they are doing nothing but sleeping.

In poke mode this is literally true: the worker process is blocked in a loop.

In reschedule mode it is subtler but still true. The task instance is in `running` state between reschedules in Airflow 2.x's accounting model, and it counts toward concurrency. The worker *process* is released, but the *slot* is not, until the sensor finally succeeds or fails.

The classic failure:

```text
Max number of active tasks allowed (16) reached
```

You will see this in the scheduler log when the DAG's task concurrency limit is hit. On Composer, the environment-wide parallelism is much larger than the per-DAG limit, so the per-DAG `max_active_tasks_per_dag` is what usually bites.

A sensor-heavy DAG can deadlock itself: if task A is a sensor that waits for task B, and B cannot start because A is holding the slot B needs, nothing progresses.

```text
wait_for_upstream_data  (sensor, running, holding slot)
        │
        └──▶ needs upstream_pipeline to finish
              upstream_pipeline needs a slot
              slots: all 16 held by sensors
              → nothing ever runs
```

### Deferrable operators: the real fix

Airflow 2.2 introduced **deferrable operators** and the **triggerer** process. A deferrable operator does not hold a slot while it waits. It *defers*: it tells the scheduler "I am not done, but I need no worker; wake me when X happens", and the worker is released immediately.

Mechanically, deferral works like this:

1. The operator's `execute()` raises `airflow.exceptions.TaskDeferred`.
2. Airflow catches it, sets the task instance to `deferred`, and records a **Trigger** row.
3. The task instance **exits** the running state — the concurrency slot is released.
4. The **triggerer** process runs a coroutine that watches the condition.
5. When the condition is met, the triggerer fires the trigger, and Airflow re-schedules the task instance, which re-runs `execute()` from the top.

```python
from airflow.exceptions import TaskDeferred
from airflow.triggers.base import TriggerEvent
from airflow.utils.trigger_rule import TriggerRule
```

The triggerer is a separate process from the scheduler and from the workers. On Composer it is managed for you — you do not run it. But it is worth understanding that it exists, because "why is my deferred task not running?" is answered by "the triggerer is not running".

**The re-run semantics matter.** Because the task re-runs `execute()` from the top, a deferrable operator must be written so that the second invocation is cheap. The typical shape is a `try/except TaskDeferred` around the actual wait:

```python
from airflow.exceptions import TaskDeferred
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor


class GCSObjectExistenceSensorDeferrable(GCSObjectExistenceSensor):
    """A deferrable version of the GCS object existence sensor."""

    def execute(self, context: Context, **kwargs) -> bool:
        """Defer instead of blocking a worker."""
        try:
            return super().execute(context=context, **kwargs)
        except TaskDeferred:
            raise
        except AirflowException as exc:
            raise TaskDeferred(
                trigger=GCSObjectExistenceTrigger(bucket=self.bucket, object_name=self.object_name),
                trigger_id=f"gcs_exists_{self.bucket}_{self.object_name}_{context['ts']}",
                method_name="execute_complete",
            )

    def execute_complete(self, context: Context, **event: Any) -> bool:
        """Return the trigger's result when the task is resumed."""
        return bool(event.get("exists", False))
```

The `method_name="execute_complete"` argument is what Airflow calls when the trigger fires. `execute_complete` must exist on the operator, and it receives the event payload the trigger emitted.

**Deferrable vs sensor: the comparison that matters.**

| | Blocking sensor | Deferrable operator |
|---|---|---|
| Holds a concurrency slot | yes, for its whole life | no |
| Worker process blocked | yes (poke) | no |
| Needs a triggerer | no | yes (Composer manages it) |
| Requires a provider version | any | Airflow ≥ 2.2 + a deferrable-capable provider |
| Max wait | hours/days | hours/days |
| Poll granularity | `poke_interval` | the trigger's own logic |

On Composer, the practical rule is: **if a provider offers a deferrable variant of the sensor you need, use it.** The Google Cloud provider ships deferrable versions of most of its sensors.

### `ExternalTaskSensor`

`ExternalTaskSensor` waits for a task instance in *another* DAG run to reach a state.

```python
from airflow.sensors.external_task import ExternalTaskSensor

wait_for_upstream = ExternalTaskSensor(
    task_id="wait_for_upstream_pipeline",
    external_dag_id="upstream_pipeline",
    external_task_id="publish_dataset",
    execution_delta=timedelta(hours=0),
    timeout=3600,
    mode="reschedule",
    poke_interval=300,
    allowed_states=["success"],
    failed_states=["failed"],
)
```

The parameters that trip people up:

- **`execution_delta`** — the offset between *this* run's logical date and the *other* run's logical date. `execution_delta=timedelta(hours=-1)` waits for the other DAG's run one hour earlier. `None` means "wait for the run with the same logical date".
- **`execution_date_fn`** — a callable that computes the other run's logical date from this run's context. More expressive than `execution_delta`.
- **`external_task_id`** — the specific task to watch. If you omit it, the sensor waits for the *whole* other DAG run to reach the allowed state.
- **`allowed_states`** / **`failed_states`** — the states that mean success and the states that mean "stop waiting, this will never work".

**The fragility.** `ExternalTaskSensor` depends on the other DAG's *internal structure*: its `dag_id`, its `task_id`, and its logical-date alignment. Rename the task, change the schedule, or shift the start date, and the sensor silently waits for something that will never exist until it times out. There is no compile-time check and no schema.

```text
airflow.exceptions.AirflowSensorTimeout: Timeout: 3600.0s
```

...and then you have to go and discover that the upstream task was renamed last week.

The rule: **use `ExternalTaskSensor` only when you cannot restructure the two DAGs.** If you control both, use `TriggerDagRunOperator` (which *creates* the other run and can wait for it) or a **Dataset** (Airflow 2.4+), which is a declarative dependency with no structural coupling at all.

### The sensor-as-anti-pattern discussion

Sensors are the most over-used feature in Airflow, and the reason is a misunderstanding: people reach for a sensor because the problem *feels* like "wait for something". But "wait for something" has three quite different solutions, and the sensor is the worst one more often than not.

**Situation 1 — the thing arrives on a schedule, and you know the schedule.**

If the upstream job runs at 02:00 and you need its output at 03:00, a sensor is a *lie*. You are not waiting for an event; you are waiting for a clock, and you already know where the clock is. Put the downstream task on the same DAG, or use `ExternalTaskSensor` with a schedule you control, or — best — restructure so the upstream job *pushes* to you.

**Situation 2 — the thing arrives when it arrives, and there is a lot of it.**

If you are waiting for a file that may or may not show up, and may show up at 03:00 or 05:00 or never, then a sensor is defensible — but only in **reschedule mode**, and only with a sensible `timeout` and `soft_fail` policy.

**Situation 3 — the thing is an event, and you want to be notified.**

If a producer completes and you want to run something, the modern answer is a **Dataset** (Airflow 2.4+), not a sensor. A Dataset dependency is declarative: the producer *updates* a dataset, and the consumer DAG is *scheduled* by that update. No polling, no worker slot, no timeout, no coupling to task names.

**The anti-pattern, concretely.**

```python
# The anti-pattern: a 6-hour sensor that holds a slot and polls a bucket.
wait_for_file = GCSObjectExistenceSensor(
    task_id="wait_for_orders",
    bucket="{{ var.value.source_bucket }}",
    object_name="{{ ds }}/orders.csv",
    mode="poke",           # ← holds a worker slot for up to 6 hours
    poke_interval=60,      # ← 360 API calls per wait
    timeout=6 * 3600,      # ← six hours of a slot
)
```

Three things are wrong here. It holds a slot for six hours. It makes 360 GCS API calls per wait, which is a quota problem at scale. And it will *always* wait the full six hours if the file never appears, even though the file for `{{ ds }}` will never arrive at all — the pipeline should have skipped, not waited.

**The better shape for the same requirement:**

```python
# Better: a deferrable sensor releases the slot while it waits.
wait_for_file = GCSObjectExistenceSensor(
    task_id="wait_for_orders",
    bucket="{{ var.value.source_bucket }}",
    object_name="{{ ds }}/orders.csv",
    deferrable=True,       # ← Airflow 2.2+, releases the slot
    timeout=6 * 3600,
    poke_interval=300,
    soft_fail=True,
)
```

And the *best* shape, if the producer can be changed at all:

```text
producer DAG ──▶ updates Dataset("gs://bucket/orders/{{ ds }}")
                         │
                         ▼
consumer DAG is scheduled by the dataset update
```

No sensor. No polling. No slot. No timeout.

**When a sensor is genuinely the right tool.** It is right when *you* do not control the producer, the producer has no push mechanism, the wait is bounded, and a miss must be visible. It is wrong in every other case.

---

## 🛠️ Hands-On

### Step 1 — see the course DAG's sensor configuration

```bash
cd data-engineering/data-Course/google/composer
grep -n "Sensor" -A 12 project/dags/04_branching_and_xcom.py
```

You will see the sensor configured with `mode="reschedule"`, `timeout=3600`, `poke_interval=300`, `soft_fail=True`. Hold that shape in mind — it is the template for the rest of this chapter.

### Step 2 — reproduce a sensor's decision logic locally, without Airflow

The condition a sensor evaluates is business logic, so it belongs in `core/pipeline_logic.py`, not in the DAG file. The course already has the pieces. Let us build a small readiness check on top of them.

```bash
cd data-engineering/data-Course/google/composer
python3 - <<'PY'
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import transform_orders, summarise_by_region

lines = open("sample_data/orders.csv").read().splitlines()
accepted, rejected = transform_orders(lines)
summary = summarise_by_region(accepted)
print(f"accepted={len(accepted)} rejected={len(rejected)}")
for region, bucket in sorted(summary.items()):
    print(region, bucket["order_count"], bucket["revenue_eur"])
PY
```

Expected output:

```text
accepted=1245 rejected=0
AMER 318.0 113592.19
APAC 285.0 108194.92
EMEA 322.0 118423.22
LATAM 320.0 110646.18
```

Now the sensor's condition, written exactly as a `PythonSensor` callable would write it — a pure function returning a boolean:

```python
# project/core/sensor_conditions.py
"""Pure readiness conditions for the course's sensors.

Sensors are orchestration. The *condition* they evaluate is logic, and
logic belongs here, where it can be unit-tested with no Airflow, no
worker, and no timeout.
"""
from __future__ import annotations

from pipeline_logic import transform_orders


def source_is_ready(
    lines: list[str],
    *,
    expected_rows: int = 0,
    reject_threshold: int = 0,
) -> bool:
    """Return True when the source data is complete enough to proceed.

    This is the condition a `PythonSensor` would evaluate. Keeping it
    pure means the "is the data ready?" rule is tested directly, rather
    than being rediscovered every time the sensor times out at 03:00.

    Args:
        lines: The raw source lines.
        expected_rows: The minimum number of accepted rows required.
        reject_threshold: The maximum number of rejected rows tolerated.

    Returns:
        True when the data is ready to process.
    """
    accepted, rejected = transform_orders(lines)
    if len(accepted) < expected_rows:
        return False
    if len(rejected) > reject_threshold:
        return False
    return True
```

Test it locally:

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, "project/core")
from sensor_conditions import source_is_ready

lines = open("sample_data/orders.csv").read().splitlines()

print("ready at 0 expected rows   :", source_is_ready(lines))
print("ready at 1000 expected rows:", source_is_ready(lines, expected_rows=1000))
print("ready at 5000 expected rows:", source_is_ready(lines, expected_rows=5000))
print("ready at 100000 expected   :", source_is_ready(lines, expected_rows=100_000))
PY
```

Expected output:

```text
ready at 0 expected rows   : True
ready at 1000 expected rows: True
ready at 5000 expected rows: False
ready at 100000 expected   : False
```

The sample dataset has 1,245 accepted orders out of 5,000 generated rows (the rest are non-revenue-bearing statuses), which is exactly why "expected rows" must be calibrated against `transform_orders`, not against the raw file.

### Step 3 — the real Airflow sensor, ready to deploy

```python
# project/dags/05_sensors.py
"""
05_sensors.py — waiting for things, without burning a worker.

Demonstrates:
  * `PythonSensor` in poke and reschedule modes
  * `soft_fail` semantics
  * `ExternalTaskSensor` with `execution_delta`
  * a deferrable sensor
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.sensors.python import PythonSensor

log = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


def orders_are_present(**context) -> bool:
    """Return True when the source object for this run's date exists.

    Args:
        context: The Airflow task context.

    Returns:
        True when the condition is satisfied.
    """
    bucket = context["var"].get("source_bucket", "demo-source-bucket")
    object_name = f"{context['ds']}/orders.csv"
    log.info("checking gs://%s/%s", bucket, object_name)
    # In production this would be a GCS API call. The pure decision —
    # "is the row count plausible?" — lives in core/sensor_conditions.py.
    return True


with DAG(
    dag_id="sensors_demo",
    description="Sensor modes, soft_fail, and cross-DAG waiting.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["tutorial", "sensors"],
) as dag:
    # Reschedule mode: the right default for waits longer than a couple
    # of minutes. The worker slot is released between checks.
    wait_long = PythonSensor(
        task_id="wait_for_orders_reschedule",
        python_callable=orders_are_present,
        mode="reschedule",
        timeout=3600,
        poke_interval=300,
        soft_fail=True,
    )

    # Poke mode: for waits of seconds or a couple of minutes. Holds the
    # worker slot for the whole wait.
    wait_short = PythonSensor(
        task_id="wait_for_orders_poke",
        python_callable=orders_are_present,
        mode="poke",
        timeout=120,
        poke_interval=10,
        soft_fail=False,
    )

    # Cross-DAG: wait for another DAG's task. Note how fragile the
    # coupling is — external_dag_id and external_task_id are strings that
    # nothing validates.
    wait_upstream = ExternalTaskSensor(
        task_id="wait_for_upstream_publish",
        external_dag_id="upstream_pipeline",
        external_task_id="publish_dataset",
        execution_delta=timedelta(hours=0),
        timeout=3600,
        mode="reschedule",
        poke_interval=300,
        allowed_states=["success"],
        failed_states=["failed"],
    )

    wait_long >> wait_short >> wait_upstream
```

### Step 4 — run the local runner to confirm the pipeline still works

Sensors are orchestration, so the local runner does not simulate them. But the pipeline the sensor gates must still be correct. Run the ETL DAG and check the summary is unchanged:

```bash
python3 project/local_runner.py --dag etl_to_gcs --date 2026-01-15
```

Expected tail:

```text
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

### Step 5 — reason about the slot cost of the sensor you just wrote

```bash
python3 - <<'PY'
# How many concurrency slots does the demo DAG's sensors hold?
sensors = [
    ("wait_for_orders_reschedule", "reschedule", 3600, 300),
    ("wait_for_orders_poke", "poke", 120, 10),
    ("wait_for_upstream_publish", "reschedule", 3600, 300),
]
for name, mode, timeout, interval in sensors:
    pokes = timeout // interval
    print(f"{name:<30} mode={mode:<11} timeout={timeout:>5}s  "
          f"pokes={pokes:>3}  holds_slot={'yes' if mode == 'poke' else 'transiently'}")
PY
```

Expected output:

```text
wait_for_orders_reschedule     mode=reschedule  timeout= 3600s  pokes= 12  holds_slot=transiently
wait_for_orders_poke           mode=poke        timeout=  120s  pokes= 12  holds_slot=yes
wait_for_upstream_publish       mode=reschedule  timeout= 3600s  pokes= 12  holds_slot=transiently
```

The poke-mode sensor holds a slot for 120 seconds and makes 12 API calls. The reschedule-mode sensor makes the same 12 calls but never holds a slot for more than the duration of one call. This is the whole argument, in numbers.

---

## 🛠️ Common Errors and Fixes

### `airflow.exceptions.AirflowSensorTimeout: Timeout: 3600.0s`

The sensor exhausted its total wait budget without the condition becoming true.

**Cause:** the condition genuinely was not met — the upstream data never arrived, or the sensor is checking the wrong thing.

**Fix, in order:**
1. Read the sensor's log lines. The message itself is uninformative; the log lines have the actual values being polled.
2. Check the `object_name`/`external_task_id` against what actually exists. A renamed upstream task produces exactly this error.
3. If the wait is legitimately long, raise `timeout` and switch to `mode="reschedule"`.
4. If the thing will never arrive, use `soft_fail=True` — but understand that this lets the pipeline continue with incomplete data, which is a *business* decision, not a technical one.

### The pipeline continued even though the sensor never succeeded

**Cause:** `soft_fail=True`. On timeout, the sensor task is marked **success**, not failed.

**Fix:** set `soft_fail=False` if the pipeline must not continue without the data. Verify by checking the sensor task's final state in the UI — a `soft_fail=True` sensor that timed out looks identical to a sensor that succeeded on the first poke, except for the log lines.

### `Max number of active tasks allowed (16) reached`

The DAG hit its `max_active_tasks_per_dag` limit.

**Cause:** usually a pile of sensors holding slots. In poke mode this is literal. In reschedule mode the task instance still occupies a concurrency slot between reschedules.

**Fix:**
- Move every long wait to `mode="reschedule"`.
- Prefer a deferrable operator, which releases the slot entirely.
- Reduce the number of *concurrent* sensor waits by restructuring the DAG to wait once, not five times.
- Raise `max_active_tasks_per_dag` only after confirming the waiters are not the problem.

### The DAG deadlocks: nothing runs and nothing fails

**Cause:** a sensor is waiting for a task that cannot start because the sensor is holding the slot it needs.

**Fix:** this is a structural problem, not a tuning problem. Either:
- Move the wait to *before* the branch point so it does not hold a slot that the awaited work needs, or
- Replace the sensor with a `TriggerDagRunOperator` + `ExternalTaskSensor` chain where the upstream DAG is not part of the same DAG's slot pool, or
- Use a Dataset, which has no slot semantics at all.

### `Task is in the 'upstream_failed' state`

A downstream task did not run because an upstream task failed.

**Cause:** the sensor failed (timeout with `soft_fail=False`), and Airflow marked every downstream task `upstream_failed`.

**Fix:** this state is a *symptom*. Go and look at the actual failure in the upstream task's log, which the UI shows in the task instance's "Task Instance Details" panel. Do not "fix" the downstream task — it is fine.

### `airflow.exceptions.TaskDeferred` propagates as an error instead of deferring

**Cause:** the `TaskDeferred` exception was caught and swallowed by a broad `except` clause in the operator, or the provider version predates 2.2.

**Fix:**
```python
# Wrong — swallows the deferral
try:
    return self.poll()
except Exception:
    return False

# Right — re-raise the deferral explicitly
try:
    return self.poll()
except TaskDeferred:
    raise
except AirflowException:
    raise TaskDeferred(trigger=MyTrigger(...), method_name="execute_complete")
```

Also check that `airflow>=2.2` is installed and that the provider version ships a deferrable variant.

### `AttributeError: 'MySensor' object has no attribute 'execute_complete'`

**Cause:** the trigger was configured with `method_name="execute_complete"` but the operator does not define that method.

**Fix:** add it. The triggerer's event payload is passed as keyword arguments:

```python
def execute_complete(self, context: Context, **event: Any) -> bool:
    """Return the trigger's result when the task is resumed."""
    return bool(event.get("exists", False))
```

### The deferrable task stays in `deferred` forever

**Cause:** the triggerer is not running, or the trigger's condition is never satisfied.

**Fix:** on Composer the triggerer is managed, but it can still be unhealthy. Check the environment's health. On a self-managed Airflow, the triggerer is a separate process:

```bash
airflow triggerer --help
```

A common self-managed mistake is running the scheduler and the workers but forgetting the triggerer entirely.

### `airflow.exceptions.DagNotFound: DAG: [upstream_pipeline] not found`

**Cause:** an `ExternalTaskSensor` (or a `TriggerDagRunOperator`) references a DAG that does not exist in the environment, or the name is misspelled.

**Fix:** check the DAG list in the UI. Note that this error is raised by the *scheduler* when the sensor's `external_dag_id` cannot be resolved — it is a hard failure, not a timeout.

---

## 💡 Production Notes

- **Reschedule mode by default.** Poke mode is only for waits under a couple of minutes. If you are unsure, reschedule.
- **Deferrable where available.** The Google Cloud provider ships deferrable versions of most sensors. `deferrable=True` on a deferrable-capable operator releases the slot completely.
- **A sensor's condition is business logic. Put it in `core/`, not in the DAG.** The course's `core/sensor_conditions.py` shows the shape: a pure function, unit-tested, called by the sensor's callable.
- **Set `timeout` to a business-meaningful number.** "How late can this data be before we give up and proceed without it?" is a business question. "3600" is a guess.
- **Decide `soft_fail` deliberately.** `soft_fail=True` means "proceed without the data". If the data is required, use `False`.
- **Prefer Datasets to sensors whenever the producer is under your control.** A Dataset dependency has no polling, no slot, no timeout, and no coupling to task names.
- **Bound your polling.** `poke_interval=60` for an hour is 60 API calls per wait. At 100 concurrent waits that is 6,000 calls an hour against a service quota.
- **Never use a sensor to wait for a schedule.** If you know when the upstream job runs, use `ExternalTaskSensor` with an `execution_delta`, or restructure so both are in one DAG.
- **Watch for sensor-induced deadlocks.** A sensor waiting on a task in its own DAG can exhaust the concurrency pool and stall the DAG permanently.
- **Alert on sensor timeouts separately from task failures.** A `soft_fail=True` timeout is invisible in a failure dashboard, and the data it allowed through is wrong.

---

## 🔑 Key Takeaways

- A sensor is a task whose callable returns a boolean. `True` succeeds, `False` **waits** — it is not a failure.
- `mode="poke"` holds a worker slot for the whole wait; `mode="reschedule"` releases it between checks. Long waits want reschedule.
- The three knobs are `timeout` (total budget), `poke_interval` (check granularity), and `soft_fail` (whether a timeout succeeds or fails the task).
- **`soft_fail=True` means "carry on without the data".** That is a business decision.
- A sensor occupies a **concurrency slot** for its lifetime. Sensors are the most common cause of `Max number of active tasks allowed (16) reached`.
- Deferrable operators (Airflow 2.2+) raise `TaskDeferred`, release the slot, and rely on the triggerer to resume the task via `execute_complete`.
- `ExternalTaskSensor` couples you to another DAG's `dag_id`, `task_id`, and logical-date alignment — all strings nothing validates.
- The sensor-as-anti-pattern: prefer a Dataset (Airflow 2.4+) when you control the producer, and a schedule when the arrival time is known.
- Keep the *condition* pure and unit-tested; keep the *waiting* in the DAG.

---

## 📚 Practice Exercises

1. **Rewrite the poke sensor as a deferrable one.** Take `wait_for_orders_poke` from chapter 5's DAG and write a deferrable variant using `TaskDeferred` and `GCSObjectExistenceTrigger`. Then explain in writing what happens to the task instance's state and its concurrency slot at each of the three moments: immediately after `execute()` raises, when the trigger fires, and when `execute_complete` returns. *Expected answer:* at the first moment the task instance becomes `deferred` and leaves the running state, releasing the slot; when the trigger fires, the triggerer updates the trigger row and Airflow re-schedules the task instance, which re-runs `execute()` from the top; `execute_complete` then returns the trigger's payload and the task instance succeeds.

2. **Calibrate a timeout from data, not from a guess.** The upstream producer writes its file between 01:40 and 03:20 on a normal day, and about once a month it fails and the file arrives at 07:00. Choose a `timeout`, a `poke_interval`, and a `soft_fail` value, and justify each. *Expected answer:* `timeout` should exceed the worst realistic arrival (07:00) by a margin — 8 hours (28,800s) is defensible if a late file is still usable; `poke_interval` should be 5–15 minutes (300–900s) because the arrival time is not precise and GCS API quota is finite; `soft_fail` should be `False` because the data is required for a downstream reconciliation, and letting the pipeline continue at 04:00 would produce wrong numbers.

3. **Count the slot-minutes.** A DAG has 10 sensors, each in `mode="poke"` with `timeout=3600` and `poke_interval=60`. A second DAG has 10 sensors, each in `mode="reschedule"` with the same settings. Compute the total slot-minutes consumed by each DAG over one run, and the total GCS API calls. *Expected answer:* the poke DAG consumes 10 × 60 = 600 slot-minutes and makes 10 × 60 = 600 API calls; the reschedule DAG makes the same 600 API calls but its *worker-process* occupancy is only 600 × (call duration, say 0.2s) ≈ 2 slot-minutes — a 300× reduction in worker occupancy, at the cost of a scheduler round-trip per check.

4. **Detect the `soft_fail` trap.** Write a sensor with `soft_fail=True` and a condition that can never be true, run it locally with a fake callable, and show that the *task* would be reported as success while the *condition* was never met. Then explain what alert you would add to catch this in production. *Expected answer:* the alert is not on task state (it is `success`) but on the *absence of the expected effect* — e.g. "the downstream target partition was not written", or a custom metric incremented only when the condition is met. The general rule: any `soft_fail=True` sensor needs a separate "did we actually get the data?" check downstream.

5. **Replace a sensor with a Dataset.** Take the `wait_for_upstream_data` sensor in `04_branching_and_xcom.py` and rewrite the DAG so the upstream job publishes a Dataset and the downstream job is scheduled by the Dataset update. Write down exactly what disappears (the slot, the polling, the timeout, the coupling) and what you have to add (a dataset update in the producer, a dataset dependency in the consumer, and a policy for "producer ran but published nothing").

6. **Design the cross-DAG wait properly.** You control three DAGs: `extract`, `transform`, and `publish`. The `transform` DAG must not start until `extract` has succeeded for the same logical date. Write the dependency using (a) `ExternalTaskSensor`, (b) `TriggerDagRunOperator` with `wait_for_completion=True`, and (c) a Dataset. Then say which you would choose and why. *Expected answer:* (c) is best — no polling, no slot, no task-name coupling; (b) is acceptable if you also own the trigger, but `wait_for_completion=True` blocks a slot for the entire duration of the other DAG; (a) is the worst because it couples to `external_task_id` and to logical-date alignment, and a rename upstream becomes a silent six-hour timeout.

---

## 📖 Further Reading

- Airflow sensors documentation — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/sensors.html
- Airflow deferrable operators (the triggerer) — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/deferring.html
- Airflow: task states and deferral — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#taskinstance-states
- Airflow API reference — `airflow.sensors.python.PythonSensor` — https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/sensors/python/index.html
- Airflow API reference — `airflow.sensors.external_task.ExternalTaskSensor` — https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/sensors/external_task/index.html
- Airflow Datasets (data-aware scheduling, 2.4+) — https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/datasets.html
- Google Cloud Composer: deferrable operators — https://cloud.google.com/composer/docs/how-to/managing/deferrable-operators
- Google Cloud Composer: managing DAGs and triggers — https://cloud.google.com/composer/docs/how-to/managing/creating
