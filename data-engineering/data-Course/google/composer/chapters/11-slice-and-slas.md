# 4.11 — SLAs, SLOs & Timeliness

> **Section 4 · Advanced Orchestration · Lecture 4.11 · 7:00**

## 🎯 What you will learn

- The five timing knobs Airflow gives you, and why they are constantly confused
- `sla` vs `execution_timeout` vs `retries` vs `retry_delay` vs `delay` — a precise comparison
- What Airflow's SLA is actually measured *against*: the end of the data interval
- `sla_miss_callback`: what it is for, and why it is not an alerting system
- Task-level SLAs, DAG-level SLAs, and the difference between them
- What an SLA miss means operationally — and why it is not the same as a failure
- SLA vs SLO: the distinction that keeps a 99.9% promise from becoming a 100% engineering effort

---

## 🧠 Concept

### The five timing knobs

Airflow gives you five independent controls over time. They are related but they are not interchangeable, and nearly every Airflow confusion in this area comes from mixing them up.

| Knob | Scope | What it bounds | What happens when it is exceeded |
|---|---|---|---|
| **`sla`** | task or DAG | How long the task/DAG may take *from the reference point* | SLA is **missed**. A callback fires. The task keeps running. |
| **`execution_timeout`** | task | How long the task's callable may execute | The task **fails** with `AirflowTaskTimeout` |
| **`retries`** | task | How many times to retry after a failure | — (configures the count) |
| **`retry_delay`** | task | How long to wait between retry attempts | — (configures the wait) |
| **`delay`** | task | How long before the task may *start* | The task stays `scheduled` |

Let us take them one at a time, because the distinctions are worth internalising.

### `execution_timeout` — the hard kill switch

`execution_timeout` bounds the wall-clock time of the callable itself. When it elapses, Airflow kills the task and marks it `failed`.

```python
from airflow.exceptions import AirflowTaskTimeout

load = BigQueryInsertJobOperator(
    task_id="load_to_bigquery",
    execution_timeout=timedelta(minutes=30),
    # ...
)
```

The task fails with:

```text
airflow.exceptions.AirflowTaskTimeout: Task timed out after 0:30:00
```

This is a **resource guard**. Its purpose is to stop a task from hanging forever and holding a worker slot. It says nothing about whether the data arrived on time.

### `retries` and `retry_delay` — the resilience knobs

```python
DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}
```

This is the course's own `default_args`, in `project/dags/dag_config.py` and in every DAG file.

- `retries=2` means the task is attempted **up to three times** in total (one initial attempt plus two retries).
- `retry_delay=timedelta(minutes=5)` means Airflow waits 5 minutes between attempts. It is a *fixed* delay, not exponential backoff. For exponential backoff you use `retry_delay` as a callable that receives the attempt number:

```python
def exponential_backoff(attempt_number: int, **context) -> timedelta:
    """Return a delay that grows with the attempt number.

    Args:
        attempt_number: 1 for the first retry, 2 for the second, and so on.
        **context: The Airflow task context.

    Returns:
        The delay before the next attempt.
    """
    return timedelta(minutes=2 ** attempt_number)


load = BigQueryInsertJobOperator(
    task_id="load_to_bigquery",
    retries=3,
    retry_delay=exponential_backoff,
    # ...
)
```

Note the interaction with `execution_timeout`: the timeout applies **per attempt**, not to the task as a whole. A task with `execution_timeout=30min` and `retries=2` can occupy a worker for up to 90 minutes plus retry delays. This is a real cost trap.

### `delay` — the start offset

`delay` holds a task back from the start of its DAG run.

```python
stage = PythonOperator(
    task_id="validate_and_stage",
    python_callable=validate_and_stage,
    delay=timedelta(minutes=30),
)
```

It exists for one reason: **staggering load on a downstream system.** If five DAGs all land at 02:00 and each fires a heavy load, the target system sees a thundering herd. `delay` spreads them out.

The course's `03_etl_bigquery.py` uses a different mechanism for the same class of problem — `schedule="@daily"` with `start_date=datetime(2026, 1, 1, tzinfo=timezone.utc)` — and the downstream BigQuery aggregate query filters on the data interval rather than on arrival time.

### `sla` — the deadline

`sla` is the one that is about **business timeliness**, and it is the one with the most surprising mechanics.

The critical detail:

> **Airflow's SLA is measured from the end of the data interval, not from the start of the DAG run.**

For a daily DAG with a logical date of `2026-01-15`, the data interval is `[2026-01-15, 2026-01-16)`. The SLA deadline is `2026-01-16 00:00` plus the SLA duration. It is **not** measured from when the task happened to start.

```text
DAG: etl_orders_to_bigquery
  data interval : [2026-01-15T00:00:00+00:00, 2026-01-16T00:00:00+00:00)
  sla           : 2 hours
  deadline      : 2026-01-16T02:00:00+00:00
  actual start  : 2026-01-16T01:30:00+00:00   ← the run started LATE
  actual finish : 2026-01-16T01:45:00+00:00

  Did it miss the SLA?  NO.
  Why? 15 minutes of headroom remained against the 02:00 deadline.
```

This is exactly what the course's `03_etl_bigquery.py` documents:

```python
#: The SLA is measured from the **end of the data interval**, not from the
#: wall-clock start of the run. A 02:00 run whose interval ended at 00:00
#: has two hours of SLA headroom, regardless of when it actually started.
DAG_SLA = timedelta(hours=2)
```

The logic behind it is sound: the SLA is a promise about *data freshness*, not about *scheduler punctuality*. If the 2026-01-15 data is summarised and available by 2026-01-16 02:00, the business is satisfied — regardless of whether the pipeline started at 00:00, 00:30, or 01:30.

### The full picture

```text
data interval ends                                      ──┐
                                                        │◀──── SLA is measured from here
  ┌─────────────────────────────────────────────────────┼──────────────────────────┐
  │  delay        task runtime      retry delays        │◀── execution_timeout ──▶│
  │◀────▶│◀──────────────────────────▶│◀──────▶│        │                          │
  │                                                     │                          │
  ├──── run starts ─────────────────────────────────────┴──── SLA deadline ───────┤
  │                                                                               │
  │◀───────────────────── SLA measured against the interval end ────────────────▶│
  └───────────────────────────────────────────────────────────────────────────────┘
```

| | SLA | `execution_timeout` |
|---|---|---|
| Reference point | end of the data interval | start of the task's execution |
| Bounds | the *deadline* | the *duration* |
| On breach | missed SLA + callback; task keeps running | task **fails** |
| Failure state | none (the task can still succeed) | `failed` |
| Business meaning | "was the data fresh enough?" | "is this task stuck?" |

### `sla_miss_callback`

When the SLA is missed, Airflow calls `sla_miss_callback`.

```python
def on_sla_miss(context, **kwargs) -> None:
    """Called when a DAG run misses its SLA.

    Args:
        context: The Airflow task context.
        kwargs: Extra keyword arguments passed by Airflow.
    """
    log.error("DAG %s missed its SLA at %s", context["dag"].dag_id, context["logical_date"])
    log.error("downstream data may be late; alert the owner")
```

This is the course's `03_etl_bigquery.py` callback, and it is a reasonable starting shape: log an error naming the DAG and the logical date.

**What the callback is for.** It runs in the **scheduler process**, not on a worker. That has three consequences:

1. **It must be fast.** It runs inside the scheduler loop. A callback that sleeps for 30 seconds slows down *every* DAG in the environment.
2. **It must not raise.** An exception in the callback is logged by Airflow, but it can destabilise the scheduler's SLA-processing loop. Wrap risky work in a `try/except`.
3. **It is not a retry mechanism.** It cannot fix the miss; it can only report it.

**What the callback is not.** It is **not** an alerting system. There is no built-in retry, no escalation, no delivery guarantee. Airflow does call the callback once per missed SLA, and if the DAG succeeds before the deadline, the callback never fires.

A production-grade callback sends a message to somewhere durable:

```python
def on_sla_miss(context, **kwargs) -> None:
    """Publish an SLA-miss event to Pub/Sub for the alerting pipeline."""
    import json

    from google.cloud import pubsub_v1

    publisher = pubsub_v1.PublisherClient()
    topic = publisher.topic_path(
        context["var"].get("gcp_project_id", "YOUR_PROJECT_ID"),
        context["var"].get("sla_topic", "airflow-sla-misses"),
    )
    payload = json.dumps({
        "dag_id": context["dag"].dag_id,
        "task_id": context.get("task_id"),
        "logical_date": str(context["logical_date"]),
        "run_id": context["run_id"],
        "sla": str(context.get("sla")),
    }).encode("utf-8")
    future = publisher.publish(topic, payload)
    future.result(timeout=10)
```

Note the `future.result(timeout=10)` — a bounded wait, because the callback runs in the scheduler. And in production you would wrap the whole thing in a `try/except Exception` so a Pub/Sub outage never breaks the scheduler.

### Task-level versus DAG-level SLA

```python
with DAG(
    dag_id="etl_orders_to_bigquery",
    sla=DAG_SLA,              # ← DAG-level: the whole run
    sla_miss_callback=on_sla_miss,
    default_args=DEFAULT_ARGS,
) as dag:
    stage = PythonOperator(
        task_id="validate_and_stage",
        sla=timedelta(minutes=30),   # ← task-level: this task alone
        python_callable=validate_and_stage,
    )
```

**DAG-level SLA** — the whole run, from the interval end to the run's completion. This is the one that maps to a business promise: "yesterday's numbers are ready by 06:00."

**Task-level SLA** — one task, from the interval end to that task's completion. This is the one that tells you *which* part of the pipeline is late.

The two answer different questions:

| | DAG-level SLA | Task-level SLA |
|---|---|---|
| Answers | "was the data ready on time?" | "which step is late?" |
| Fires when | the run as a whole is late | that specific task is late |
| Good for | business-facing alerts | internal diagnostics |
| Needs a callback | **yes** | optional |

A task-level SLA without a callback is nearly useless — you get a record in the metadata database and nothing else. If you set task-level SLAs, give each one a callback that names the task.

```python
def on_task_sla_miss(context, **kwargs) -> None:
    """Log which task missed its SLA."""
    import logging

    logging.getLogger(__name__).error(
        "task %s in DAG %s missed its SLA for logical date %s",
        context.get("task_id"),
        context["dag"].dag_id,
        context["logical_date"],
    )
```

### What an SLA miss actually means operationally

This is the part people get wrong in both directions.

**An SLA miss is not a failure.** The task may still succeed. The data may still arrive. What has happened is that a *promise* was broken — the data was not fresh enough by the deadline.

The operational consequences depend on what consumes the data:

| Consumer | Effect of an SLA miss |
|---|---|
| A dashboard | Shows stale numbers; usually tolerable |
| A downstream DAG | Starts late, or misses its own window, cascading |
| An SLA-based invoice | You owe a service credit |
| A machine learning feature pipeline | The model's features are from the wrong window; this is a *correctness* problem |
| A regulatory report | You filed late. This is the severe case. |

**An SLA miss with no failure is often a scheduling problem, not a data problem.** The pipeline is fine; it started late. That points at the scheduler's backlog, a `max_active_runs` limit, a `delay`, or the previous run's overrun — a completely different set of fixes from a data-quality failure.

**Conversely, a failure with no SLA miss is fine.** The task failed, the retry succeeded, the data landed before the deadline. Nothing was broken. This is exactly why `retries` and SLA are independent: the whole point of the retry policy is to keep a transient failure from becoming an SLA miss.

### SLA vs SLO

The distinction is worth being precise about, because it changes what you build.

| | SLA (Service Level **Agreement**) | SLO (Service Level **Objective**) |
|---|---|---|
| Nature | A **contract** | A **target** |
| External | Yes — usually with a customer | No — internal to the team |
| Consequence of a miss | Credits, penalties, escalation | Engineering work, alerting, a ticket |
| Specificity | Usually about *outcomes* | Often about *outcomes*, sometimes about causes |
| Example | "The daily orders report is delivered by 06:00 UTC, 99.5% of days, with a 1-hour service credit for each miss." | "99% of daily runs complete within 2 hours of the data interval end." |

The practical engineering consequence:

> **An SLA is a business artefact; an SLO is an engineering artefact. You engineer to the SLO, and you negotiate the SLA.**

If your SLA says 99.5% and your SLO says 99%, the gap between them is the **error budget** you spend on reliability work. A 100% SLA is not an engineering goal — it is a pricing decision that makes an SLO of 100% impossible in practice.

**In Airflow terms.** Airflow's `sla` parameter is an SLO mechanism. It records whether the deadline was met and lets you fire a callback. Turning that into an SLA — the contractual artefact with credits and escalation — is an organisational process on top of it: you export the SLA-miss events (chapter 10's Pub/Sub callback), aggregate them over a period, compute the percentage of on-time runs, and compare it against the contractual number.

```text
on-time runs / total runs  ≥  99.5%   ← SLA, checked monthly against the contract
on-time runs / total runs  ≥  99%     ← SLO, checked continuously, drives engineering work
```

**Do not put an SLA number directly in a DAG.** Put the SLO in the DAG (`sla=timedelta(hours=2)`), and compute the SLA compliance externally from the recorded misses.

### How the SLA is measured against the data interval — worked example

The course's ETL DAG runs `@daily` with `sla=timedelta(hours=2)`.

```text
logical date       : 2026-01-15
data interval      : [2026-01-15T00:00:00+00:00, 2026-01-16T00:00:00+00:00)
interval end       : 2026-01-16T00:00:00+00:00
sla                : 2 hours
SLA deadline       : 2026-01-16T02:00:00+00:00
```

| Scenario | Run started | Run finished | SLA met? |
|---|---|---|---|
| On time | 2026-01-16 00:05 | 2026-01-16 00:40 | Yes — 1h20m of headroom |
| Late start | 2026-01-16 01:30 | 2026-01-16 01:45 | Yes — 15m of headroom |
| Slow | 2026-01-16 00:05 | 2026-01-16 02:30 | **No** — missed by 30m |
| Very slow | 2026-01-16 00:05 | 2026-01-16 05:00 | **No** — missed by 3h |

Note row 2: the run started 85 minutes later than row 1 and *still* met its SLA, because the SLA is not measured from the start. This surprises people every time, and it is the entire reason the SLA is anchored to the data interval.

**A caveat about the interval end for non-daily schedules.** For a `@daily` DAG, the interval end is midnight after the logical date, and the DAG typically runs *after* midnight — so the SLA window is naturally in the small hours. For an hourly DAG (`schedule="0 * * * *"`) with a 2-hour SLA, the interval end is on the hour, so the deadline is two hours after that hour — and the run for that hour typically starts at or after the top of the hour. The same logic applies; just recompute the arithmetic.

---

## 🛠️ Hands-On

### Step 1 — read the course's SLA configuration

```bash
cd data-engineering/data-Course/google/composer
grep -n "SLA\|sla" project/dags/03_etl_bigquery.py
```

Expected output:

```text
56:DAG_SLA = timedelta(hours=2)
59:def on_sla_miss(context, **kwargs) -> None:
106:    sla=DAG_SLA,
107:    sla_miss_callback=on_sla_miss,
```

### Step 2 — compute the SLA deadline for every run, using the course's own code

The course's `core/pipeline_logic.py` already has the interval arithmetic in `logical_date_window`. That is the same arithmetic Airflow uses to anchor the SLA.

```bash
python3 - <<'PY'
import sys
from datetime import datetime, timedelta, timezone
sys.path.insert(0, "project/core")
from pipeline_logic import logical_date_window

SLA = timedelta(hours=2)

for ds in ("2026-01-14", "2026-01-15", "2026-01-16"):
    start, end = logical_date_window(ds)
    interval_end = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
    deadline = interval_end + SLA
    print(f"logical_date={ds}  interval=[{start}, {end})  sla_deadline={deadline.isoformat()}")
PY
```

Expected output:

```text
logical_date=2026-01-14  interval=[2026-01-14, 2026-01-15)  sla_deadline=2026-01-15T02:00:00+00:00
logical_date=2026-01-15  interval=[2026-01-15, 2026-01-16)  sla_deadline=2026-01-16T02:00:00+00:00
logical_date=2026-01-16  interval=[2026-01-16, 2026-01-17)  sla_deadline=2026-01-17T02:00:00+00:00
```

### Step 3 — test the SLA met / missed decision as a pure function

This is the pattern to follow for anything SLA-related: **the decision is logic, so it lives in `core/` and is unit-tested.**

```python
# project/core/sla_logic.py
"""Pure SLA arithmetic, so the rules can be tested without Airflow."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from pipeline_logic import logical_date_window


def sla_deadline(logical_date: str, sla: timedelta) -> datetime:
    """Return the SLA deadline for a run.

    Airflow anchors the SLA to the **end of the data interval**, not to
    the start of the run. This function reproduces that arithmetic.

    Args:
        logical_date: The run's logical date, e.g. "2026-01-15".
        sla: The SLA duration.

    Returns:
        The timezone-aware UTC deadline.
    """
    _, end = logical_date_window(logical_date)
    interval_end = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return interval_end + sla


def sla_met(
    logical_date: str,
    sla: timedelta,
    finished_at: datetime,
) -> bool:
    """Return True when a run finished before its SLA deadline.

    Args:
        logical_date: The run's logical date.
        sla: The SLA duration.
        finished_at: When the run finished.

    Returns:
        True when the SLA was met.
    """
    if finished_at.tzinfo is None:
        finished_at = finished_at.replace(tzinfo=timezone.utc)
    return finished_at <= sla_deadline(logical_date, sla)
```

Now test it against the four scenarios from the table:

```bash
python3 - <<'PY'
import sys
from datetime import datetime, timedelta, timezone
sys.path.insert(0, "project/core")
from sla_logic import sla_deadline, sla_met

SLA = timedelta(hours=2)
DS = "2026-01-15"

scenarios = [
    ("on time",       "2026-01-16T00:40:00+00:00"),
    ("late start",   "2026-01-16T01:45:00+00:00"),
    ("slow",         "2026-01-16T02:30:00+00:00"),
    ("very slow",    "2026-01-16T05:00:00+00:00"),
]

print(f"deadline for {DS}: {sla_deadline(DS, SLA).isoformat()}\n")
for name, ts in scenarios:
    finished = datetime.fromisoformat(ts)
    ok = sla_met(DS, SLA, finished)
    margin = (sla_deadline(DS, SLA) - finished).total_seconds() / 3600
    print(f"{name:<12} finished={ts}  met={ok!s:<5} margin={margin:+.2f}h")
PY
```

Expected output:

```text
deadline for 2026-01-15: 2026-01-16T02:00:00+00:00

on time      finished=2026-01-16T00:40:00+00:00  met=True   margin=+1.33h
late start  finished=2026-01-16T01:45:00+00:00  met=True   margin=+0.25h
slow        finished=2026-01-16T02:30:00+00:00  met=False  margin=-0.50h
very slow   finished=2026-01-16T05:00:00+00:00  met=False  margin=-3.00h
```

The "late start" row is the one to internalise: the run started 85 minutes later than the "on time" run and **still met its SLA**.

### Step 4 — build a real SLA-miss recorder that uses the pure logic

```python
# project/core/sla_tracker.py
"""Track SLA outcomes across runs, so compliance can be computed later."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sla_logic import sla_deadline, sla_met


class SlaTracker:
    """Record SLA outcomes for a DAG and compute a compliance rate.

    This is the shape of the thing you build *outside* Airflow: Airflow
    gives you the events, and you aggregate them over a period to check
    the contractual number.

    Attributes:
        sla: The SLA duration being tracked.
        outcomes: A mapping of logical_date -> True/False.
    """

    def __init__(self, sla: timedelta) -> None:
        """Create a tracker.

        Args:
            sla: The SLA duration.
        """
        self.sla = sla
        self.outcomes: dict[str, bool] = {}

    def record(self, logical_date: str, finished_at: datetime) -> bool:
        """Record one run's outcome.

        Args:
            logical_date: The run's logical date.
            finished_at: When the run finished.

        Returns:
            True when the SLA was met.
        """
        met = sla_met(logical_date, self.sla, finished_at)
        self.outcomes[logical_date] = met
        return met

    def compliance(self) -> float:
        """Return the fraction of runs that met their SLA.

        Returns:
            A number between 0.0 and 1.0, or 1.0 when nothing is recorded.
        """
        if not self.outcomes:
            return 1.0
        met = sum(1 for ok in self.outcomes.values() if ok)
        return met / len(self.outcomes)

    def report(self) -> str:
        """Return a human-readable compliance report.

        Returns:
            A multi-line report.
        """
        lines = [
            f"SLA: {self.sla} (deadline = interval end + SLA)",
            f"runs recorded : {len(self.outcomes)}",
            f"on time       : {sum(1 for ok in self.outcomes.values() if ok)}",
            f"missed        : {sum(1 for ok in self.outcomes.values() if not ok)}",
            f"compliance    : {self.compliance():.4%}",
        ]
        return "\n".join(lines)
```

Exercise it:

```bash
python3 - <<'PY'
import sys
from datetime import datetime, timedelta
sys.path.insert(0, "project/core")
from sla_tracker import SlaTracker

tracker = SlaTracker(timedelta(hours=2))

runs = [
    ("2026-01-10", "2026-01-11T00:30:00+00:00"),
    ("2026-01-11", "2026-01-12T00:45:00+00:00"),
    ("2026-01-12", "2026-01-13T03:15:00+00:00"),  # missed
    ("2026-01-13", "2026-01-14T01:10:00+00:00"),
    ("2026-01-14", "2026-01-15T04:00:00+00:00"),  # missed
    ("2026-01-15", "2026-01-16T01:45:00+00:00"),
]

for ds, finished in runs:
    met = tracker.record(ds, datetime.fromisoformat(finished))
    print(f"{ds}  finished={finished}  met={met}")

print()
print(tracker.report())
print()
print("SLA at 99.5%? ", "YES" if tracker.compliance() >= 0.995 else "NO")
print("SLO at 99.0%? ", "YES" if tracker.compliance() >= 0.99 else "NO")
PY
```

Expected output:

```text
2026-01-10  finished=2026-01-11T00:30:00+00:00  met=True
2026-01-11  finished=2026-01-12T00:45:00+00:00  met=True
2026-01-12  finished=2026-01-13T03:15:00+00:00  met=False
2026-01-13  finished=2026-01-14T01:10:00+00:00  met=True
2026-01-14  finished=2026-01-15T04:00:00+00:00  met=False
2026-01-15  finished=2026-01-16T01:45:00+00:00  met=True

SLA: 2:00:00 (deadline = interval end + SLA)
runs recorded : 6
on time       : 4
missed        : 2
compliance    : 66.6667%

SLA at 99.5%?  NO
SLO at 99.0%?  NO
```

### Step 5 — wire an SLA into a deployable DAG

```python
# project/dags/06_sla.py
"""
06_sla.py — declaring and reporting SLAs.

Demonstrates:
  * DAG-level and task-level `sla`
  * `sla_miss_callback`
  * the difference between `sla` and `execution_timeout`
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator

log = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

#: The DAG-level SLA: the whole run must be fresh 2 hours after the
#: data interval ends.
DAG_SLA = timedelta(hours=2)


def on_sla_miss(context, **kwargs) -> None:
    """Report a missed SLA.

    Runs in the scheduler process, so it must be fast and must not raise.

    Args:
        context: The Airflow task context.
        kwargs: Extra keyword arguments passed by Airflow.
    """
    try:
        log.error(
            "DAG %s missed its SLA at %s",
            context["dag"].dag_id,
            context["logical_date"],
        )
    except Exception as exc:  # noqa: BLE001 - never break the scheduler
        log.error("sla_miss_callback failed: %s", exc)


def on_task_sla_miss(context, **kwargs) -> None:
    """Report which task missed its SLA.

    Args:
        context: The Airflow task context.
        kwargs: Extra keyword arguments passed by Airflow.
    """
    try:
        log.error(
            "task %s in DAG %s missed its SLA for logical date %s",
            context.get("task_id"),
            context["dag"].dag_id,
            context["logical_date"],
        )
    except Exception as exc:  # noqa: BLE001
        log.error("sla_miss_callback failed: %s", exc)


def build_summary(**context) -> dict:
    """Do the work the SLA is protecting.

    Args:
        context: The Airflow task context.

    Returns:
        A small dict, pushed to XCom.
    """
    partition = context["ds_nodash"]
    log.info("building summary for partition %s", partition)
    return {"partition": partition, "status": "complete"}


with DAG(
    dag_id="sla_demo",
    description="SLA declarations, callbacks, and the difference from timeout.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    sla=DAG_SLA,
    sla_miss_callback=on_sla_miss,
    tags=["tutorial", "sla"],
) as dag:
    build = PythonOperator(
        task_id="build_summary",
        python_callable=build_summary,
        sla=timedelta(minutes=45),          # task-level SLA
        sla_miss_callback=on_task_sla_miss,  # and its own callback
        execution_timeout=timedelta(minutes=30),  # hard kill, per attempt
        retries=2,
        retry_delay=exponential_backoff,
    )
```

### Step 6 — confirm the pipeline itself is unaffected

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

An SLA is a *measurement*. Adding one must not change a single row of output. If it does, you have accidentally changed the pipeline rather than instrumented it.

---

## 🛠️ Common Errors and Fixes

### `airflow.exceptions.AirflowTaskTimeout: Task timed out after 0:30:00`

The task's callable ran longer than `execution_timeout`.

**Cause:** the task is stuck, or genuinely slow.

**Fix:** raise `execution_timeout` if the task is legitimately slow. If it is stuck, find out why — a `execution_timeout` is a guard, and a task that routinely hits it should be redesigned, not given more time. Remember that the timeout applies **per attempt**: with `retries=2`, the task can occupy a worker for 3 × the timeout.

### The SLA was missed but the task succeeded, and nobody was told

**Cause:** no `sla_miss_callback` was set, or the callback only logged and nothing monitors the logs.

**Fix:** Airflow records the miss in the metadata database and calls the callback — but the callback must *do* something. Publish to Pub/Sub, write to a table, or call an alerting API. A callback that only writes to the scheduler's log is invisible.

### The SLA was missed but the callback never fired

**Cause 1:** the DAG finished before the deadline — the "miss" was computed against a different run.

**Cause 2:** the callback raised an exception. Airflow logs it, but the callback does not fire again.

**Cause 3:** the SLA is measured against the *interval end*, and the run's logical date is not what you assumed. Check the actual `data_interval_end` in the task instance's details.

**Fix:** wrap the callback body in `try/except` and log the exception, so the callback never fails silently.

### The SLA callback slowed the whole environment down

**Cause:** the callback does slow work — an HTTP call with a long timeout, a `time.sleep`, a synchronous API call — and it runs **in the scheduler process**.

**Fix:** make the callback fast and bounded. Publish to Pub/Sub with `future.result(timeout=10)`, or hand the work to a task. Never make an unbounded network call from the scheduler's SLA callback.

### "My DAG always misses its SLA but it usually runs in 20 minutes"

**Cause:** the SLA is measured from the *interval end*, and the DAG runs at, say, 04:00 — well past the midnight interval end.

**Fix:** either move the schedule earlier (so the run happens closer to the interval end) or increase the SLA to cover the gap. The SLA duration is "time after the interval end", not "time after the run starts". A daily DAG that runs at 04:00 with a 2-hour SLA misses it every single day, no matter how fast the DAG itself is.

### I set `sla` but the task still has no deadline enforcement

**Cause:** `sla` is not enforcement. It records a miss and fires a callback; it does **not** fail the task and it does **not** stop the DAG.

**Fix:** if you need the task to actually stop, use `execution_timeout` (which fails the task) or a sensor with `soft_fail=False`. `sla` and `execution_timeout` solve different problems.

### My retry policy is not using exponential backoff

**Cause:** `retry_delay=timedelta(minutes=5)` is a fixed delay. Exponential backoff requires a callable.

**Fix:**
```python
def exponential_backoff(attempt_number: int, **context) -> timedelta:
    """Return a growing delay between retry attempts."""
    return timedelta(minutes=2 ** attempt_number)
```

And pass it as `retry_delay=exponential_backoff` (not called — Airflow calls it).

### The SLA miss percentage is higher than expected because catchup runs count

**Cause:** backfill runs are recorded as SLA misses if they finish outside the deadline, and a backfill of 30 days finishes all at once, long after the original deadlines.

**Fix:** exclude catchup runs from compliance calculations, or compute compliance per logical date and report the *eventual* on-time rate. A backfill run is a recovery, and treating it as a fresh miss corrupts the metric.

### `context["task_instance"]` is missing in `sla_miss_callback`

**Cause:** the callback's context is the Airflow task context, and the key is `ti` in some contexts and `task_instance` in others depending on the Airflow version.

**Fix:** use `context.get("task_instance")` and `context.get("task_id")` defensively, and prefer `context["dag"].dag_id` and `context["logical_date"]`, which are stable across versions.

---

## 💡 Production Notes

- **`sla` is measured from the end of the data interval.** Always sanity-check this against your actual run times before you trust an SLA number. A daily DAG that runs at 04:00 with a 2-hour SLA misses every day.
- **`sla` records; `execution_timeout` fails.** Never use one in place of the other. If the data must be fresh, that is `sla`. If a task must not hang, that is `execution_timeout`.
- **`execution_timeout` is per attempt.** With `retries=2`, a task can hold a worker for 3× the timeout. Budget for that when you size worker pools.
- **`sla_miss_callback` runs in the scheduler.** Keep it fast, keep it bounded, and wrap it in `try/except`. A slow callback is a platform-wide outage.
- **An SLA miss is not a failure.** It means a promise was broken, not that the data is wrong. A late-but-correct report and an on-time-but-wrong report are different incidents and need different alerts.
- **Set task-level SLAs only where you will act on them.** A task-level SLA without a callback is noise. Where you want diagnosis, use `execution_timeout` or `execution_timeout` plus a task-level SLA with a callback that names the task.
- **Track compliance over a period, not per run.** Per-run SLA reporting produces noise and produces no information. Aggregate into a percentage over a window.
- **Separate SLO from SLA.** Put the SLO in the DAG; compute the SLA externally from the recorded misses. A 99.5% contractual SLA needs an internal 99% SLO to leave room for the error budget.
- **Exclude catchup runs from compliance metrics.** A backfill is a recovery, not a fresh miss.
- **Alert on SLA misses through the same pipeline as everything else.** The callback publishes an event; a Cloud Function or a second DAG turns the event into a page. Do not build a bespoke alerting path inside the callback.

---

## 🔑 Key Takeaways

- Five knobs, five different jobs: **`sla`** (deadline), **`execution_timeout`** (hard kill), **`retries`**/**`retry_delay`** (resilience), **`delay`** (start offset).
- **`execution_timeout` fails the task; `sla` only records a miss and fires a callback.** The task keeps running when the SLA is breached.
- **The SLA is anchored to the end of the data interval, not the start of the run.** A late-started run can still meet its SLA.
- The SLA deadline for a daily run is `interval_end + sla` — for the course's 2-hour SLA and the 2026-01-15 run, that is `2026-01-16T02:00:00+00:00`.
- **`sla_miss_callback` runs in the scheduler process.** Fast, bounded, and it must never raise.
- **DAG-level SLA** answers "was the data fresh on time?"; **task-level SLA** answers "which step is late?" and needs its own callback to be useful.
- An SLA miss is a **broken promise**, not a wrong answer. The two demand different alerts and different fixes.
- **SLA is a contract; SLO is an engineering target.** Engineer to the SLO, negotiate the SLA, and spend the error budget deliberately.
- `execution_timeout` applies per attempt; `retries` multiply the total worker occupancy.

---

## 📚 Practice Exercises

1. **Recompute the SLA deadline for every run of a weekly DAG.** A DAG runs `schedule="0 2 * * 1"` (Mondays at 02:00) with `sla=timedelta(hours=6)`. Using `logical_date_window` from `core/pipeline_logic.py`, compute the SLA deadline for the runs with logical dates `2026-01-05`, `2026-01-12`, and `2026-01-19`. Then state what a scheduler that starts the run 30 minutes late would need to do to still meet the SLA. *Expected answer:* for a weekly cron the data interval spans seven days, so `logical_date_window("2026-01-05")` returns `('2026-01-05', '2026-01-12')` and the interval end is `2026-01-12T00:00:00+00:00`; the deadline is `2026-01-12T06:00:00+00:00`. Likewise `2026-01-12` → deadline `2026-01-19T06:00:00+00:00`, and `2026-01-19` → deadline `2026-01-26T06:00:00+00:00`. A 30-minute-late start (02:30) still has 5.5 hours of headroom, so it easily meets a 6-hour SLA.

2. **Build an SLA-miss alerting callback that publishes to Pub/Sub.** Write a `sla_miss_callback` that publishes a JSON event containing `dag_id`, `logical_date`, `run_id`, and the SLA duration, using `google.cloud.pubsub_v1.PublisherClient`. Then explain what happens if Pub/Sub is unreachable, and how you make sure the callback never takes the scheduler down. *Expected answer:* wrap the entire body in `try/except Exception`, log the exception, and never re-raise; bound the publish with `future.result(timeout=10)` so a hanging network call cannot block the scheduler loop; and, ideally, emit the event to a local file or log line as a fallback so the miss is not lost.

3. **Distinguish the three failure shapes.** Write three scenarios and, for each, say which of `sla`, `execution_timeout`, `retries` is the right tool: (a) a BigQuery load that occasionally returns a 500 error, (b) a task that hangs on a network socket forever, (c) a nightly report that must be on the CEO's screen by 07:00. *Expected answer:* (a) → `retries` with `retry_delay` (ideally exponential backoff); (b) → `execution_timeout` (it fails the task and frees the worker) plus `retries` so it can recover; (c) → `sla` with an `sla_miss_callback` that pages. Note that (c) should *also* have `execution_timeout`, because a SLA does not stop a hung task.

4. **Compute an SLO from a month's SLA events.** Using the `SlaTracker` from the hands-on, record 30 daily runs where 27 met their SLA. Compute the compliance rate, and state whether it meets a 99% SLO, a 99.5% SLA, and a 99.9% SLA. Then explain what the engineering response should be in each case. *Expected answer:* 27/30 = 90%. It fails all three targets. The 99% SLO means roughly 0.3 misses per month are acceptable, so 3 misses is 10× the budget — this is a real reliability problem, and the response is to find the dominant cause (late scheduler backlog? retry storms? a slow upstream?) and fix it. The 99.5% and 99.9% contractual SLAs are simply not achievable at this rate and must be renegotiated or the pipeline must be materially improved.

5. **Instrument the course DAG with an SLA and prove it changes nothing.** Add `sla=timedelta(hours=2)` and an `sla_miss_callback` to `etl_orders_to_bigquery`, then run the local runner's `etl_to_gcs` DAG before and after. Verify the summary output is byte-identical. Then write down why the local runner cannot exercise the SLA path, and what you would need to test it. *Expected answer:* the output is identical, because an SLA is instrumentation, not behaviour. The local runner does not simulate Airflow's scheduler, so it has no notion of the interval-end anchor or of SLA callbacks — to test it you need a real Airflow environment (or `dag.test()` in Airflow 2.5+ with a controlled `logical_date`, which still does not exercise the scheduler's SLA processing).

6. **Design an SLO and an SLA for the course's ETL pipeline.** Write down: the SLO (target, measurement window, how it is computed), the SLA (contractual number, what a miss costs, what the escalation is), the error budget, and the three alerts. Then explain which of the alerts fires on an SLA miss and which fires on a data-quality failure. *Expected answer:* for example SLO "99% of daily runs complete within 2 hours of the interval end, measured over a rolling 30-day window"; SLA "the daily orders summary is available by 06:00 UTC on 99.5% of days, with a 1-hour service credit per miss"; error budget "0.3 misses per 30 days". Alerts: (1) DAG run failed → page (this is a failure, not an SLA miss); (2) SLA miss → ticket if within the error budget, page if it burns budget fast; (3) output row count outside the expected band → page (this is the data-quality failure, and it will *not* fire the SLA alert because the run finished on time). The third alert is the one that catches silent corruption, which SLA monitoring never will.

---

## 📖 Further Reading

- Airflow SLA documentation — https://airflow.apache.org/docs/apache-airflow/stable/concepts/sla.html
- Airflow task execution and timeouts — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html
- Airflow configuration reference (`sla`, `execution_timeout`, `retries`, `delay`) — https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html
- Airflow: monitoring DAGs — https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/monitoring.html
- Google SRE Book: Service Level Objectives — https://sre.google/sre-book/service-level-objectives/
- Google SRE Book: SLIs, SLOs, and SLAs — https://sre.google/workbook/slo-document/
- Google Cloud Composer: monitoring and logging — https://cloud.google.com/composer/docs/how-to/monitoring/logging
- Google Cloud Monitoring: alerting policies — https://cloud.google.com/monitoring/alerts
