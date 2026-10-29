# 5.14 — Orchestration Patterns

> **Section 5 · Engineering Practice · Lecture 5.14 · 8:00**

## 🎯 What you will learn

- The core pattern catalogue: fan-out/fan-in, conditional execution, cross-DAG dependencies, event-driven schedules
- **Dynamic task mapping** (Airflow 2.3+): `.expand()` and `.expand_kwargs()`, and when it beats a loop
- **Datasets** (Airflow 2.4+, formerly data-aware scheduling): declarative event-driven dependencies
- The three cross-DAG mechanisms and when each is the right one
- The "wait for data" pattern, and why a Dataset beats a sensor
- The "fan out then join" pattern, and the trigger rule that makes it work
- Batch + stream hybrid: how Airflow orchestrates a streaming pipeline it does not itself run
- The anti-patterns: task-generating loops, `SubDagOperator`, and the "one giant DAG"

---

## 🧠 Concept

### The pattern catalogue

Orchestration problems repeat. There are perhaps a dozen patterns that cover 95% of what real pipelines do. Knowing them by name — and knowing which one you are actually in — is most of the skill.

| # | Pattern | Shape | Airflow mechanism |
|---|---|---|---|
| 1 | **Linear pipeline** | A → B → C | `>>` |
| 2 | **Fan-out / fan-in** | A → {B, C, D} → E | `>>` to multiple, or dynamic mapping |
| 3 | **Conditional execution** | A → (B \| C) | `BranchOperator`, `ShortCircuitOperator` |
| 4 | **Dynamic fan-out** | A → {B₁…Bₙ} (n unknown at parse time) | **`.expand()` / `.expand_kwargs()`** (2.3+) |
| 5 | **Cross-DAG, push** | DAG₁ → DAG₂ | `TriggerDagRunOperator` |
| 6 | **Cross-DAG, pull** | DAG₂ → DAG₁ | `ExternalTaskSensor` |
| 7 | **Event-driven** | producer updates dataset → consumer scheduled | **Datasets** (2.4+) |
| 8 | **Wait for data** | A waits for a condition | Sensor (reschedule/deferrable) or Dataset |
| 9 | **Batch + stream hybrid** | Stream runs continuously; Airflow runs the batch part | `Sensor`/`Trigger` on a stream's watermark |
| 10 | **Periodic reconciliation** | Every N hours, compare and fix | `schedule="0 */6 * * *"` |

Let us take the interesting ones.

### Fan-out and fan-in

The classic shape: one upstream task, several parallel branches, one join.

```text
                    ┌─▶ transform_emea ──┐
                    │                    │
  read ──▶ validate ┼─▶ transform_amer ──┼──▶ publish
                    │                    │
                    └─▶ transform_apac ──┘
```

**The join is where it goes wrong.** A task that depends on multiple upstream tasks uses the default `trigger_rule="all_success"`. If *any* upstream fails, the join is marked `upstream_failed` and never runs — which is correct if the join needs all the data, and wrong if it can proceed with partial data.

```python
from airflow.utils.trigger_rule import TriggerRule

publish = PythonOperator(
    task_id="publish",
    python_callable=publish_summary,
    trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
)
```

The trigger rules, in full:

| Trigger rule | Runs when | Use for |
|---|---|---|
| `all_success` (default) | every upstream succeeded | the normal case |
| `all_failed` | every upstream failed | a cleanup path |
| `all_done` | every upstream finished, whatever the state | always-run cleanup, or a join after a branch |
| `none_failed` | no upstream failed (skips are fine) | a join after a branch |
| `none_failed_min_one_success` | no upstream failed **and** at least one succeeded | a join after a branch, but only if something ran |
| `one_failed` | at least one upstream failed | an alert-on-failure path |
| `none_skipped` | no upstream was skipped | a strict join |

**`none_failed` vs `none_failed_min_one_success`.** The difference matters when *every* upstream branch is skipped — which happens when a `BranchOperator` chooses a path that does not include the join. `none_failed` would run the join with no data; `none_failed_min_one_success` would skip it. The second is usually what you want.

The course's local runner implements the same distinction, in `_trigger_allows`:

```python
if rule == "none_failed":
    # "none failed" means: run unless something failed. A *skipped*
    # dependency is not a failure, so the task still runs.
    return True
```

### Conditional execution

Two mechanisms, and the difference between them is a common source of confusion.

**`BranchOperator`** — chooses *which downstream task* runs. All other downstream tasks are marked skipped.

```python
from airflow.operators.python import BranchOperator

branch = BranchOperator(
    task_id="choose_strategy",
    python_callable=choose_strategy,   # returns a list of task_ids
)
```

The course's `04_branching_and_xcom.py` uses it, and `choose_strategy` returns a one-element list:

```python
def choose_strategy(**context) -> list[str]:
    """Choose between the full-load and incremental paths.

    The return value is the list of task_ids that should run. Everything
    else downstream is skipped.
    """
    ti = context["ti"]
    row_count = int(ti.xcom_pull(task_ids="count_rows") or 0)
    threshold = int(ti.xcom_pull(task_ids="count_rows", key="threshold") or FULL_LOAD_THRESHOLD)

    force = bool(context["params"].get("force_full_load", False))
    chosen = "full_load" if (row_count > threshold or force) else "incremental_load"

    log.info("row_count=%d threshold=%d force=%s -> %s", row_count, threshold, force, chosen)
    return [chosen]
```

**`ShortCircuitOperator`** — skips *itself* and everything downstream.

```python
from airflow.operators.python import ShortCircuitOperator

skip = ShortCircuitOperator(
    task_id="skip_if_empty",
    python_callable=lambda **ctx: len(ctx["ti"].xcom_pull(task_ids="extract") or []) > 0,
)
```

| | `BranchOperator` | `ShortCircuitOperator` |
|---|---|---|
| Returns | a list of task_ids to run | a boolean |
| The task itself | succeeds | is **skipped** when the condition is false |
| Downstream | the named branches run, the rest are skipped | everything downstream is skipped |
| Use for | "choose a path" | "stop the whole pipeline" |

### Dynamic task mapping (Airflow 2.3+)

This is the single most important Airflow 2.x feature for building DAGs that scale with the data.

**The problem it solves.** Before 2.3, a DAG whose width depends on the data had to be generated at parse time — a loop in the DAG file. That is an anti-pattern (see below). With dynamic task mapping, you write **one** task, and Airflow creates one task instance per element of a list that is only known at run time.

```python
from airflow.operators.python import PythonOperator

regions = PythonOperator(
    task_id="list_regions",
    python_callable=list_regions,
)

process_region = PythonOperator.partial(
    task_id="process_region",
    python_callable=process_one_region,
).expand(region=regions.output)
```

**Two ways to expand.**

`.expand()` — one argument per mapped value, from a `XComArg`:

```python
process_region = PythonOperator.partial(
    task_id="process_region",
    python_callable=process_one_region,
).expand(region=regions.output)
```

`.expand_kwargs()` — multiple arguments at once, from a list of dicts:

```python
process_partition = BigQueryInsertJobOperator.partial(
    task_id="process_partition",
    configuration=LOAD_CONFIG,
).expand_kwargs(load_tasks)
```

where `load_tasks` is a list of dicts:

```python
[{"region": "AMER", "partition": "20260115"},
 {"region": "APAC", "partition": "20260115"}]
```

**The rules.**

1. **You must use `.partial()`.** `PythonOperator.partial(task_id=..., python_callable=...)` creates a *template*; `.expand(...)` turns it into a mapped operator. Calling `PythonOperator(...)` directly with `.expand()` is a `TypeError`.
2. **The mapped arguments must be `XComArg`s** — the output of another task — or literals. You cannot map over an arbitrary Python list; the list must come from a task's return value.
3. **Airflow caps the number of mapped instances.** `max_map_length` defaults to 1024, and is controlled by `[core] max_map_length` in `airflow.cfg`. Mapping 10,000 items fails:

```text
airflow.exceptions.AirflowException: Cannot map over a list with more than 1024 elements.
```

4. **Each mapped instance is a separate task instance** with the same `task_id` and a distinct `map_index`. They show up in the UI as `process_region[0]`, `process_region[1]`, and so on.

5. **The mapped operator's other arguments are shared.** Everything in `.partial()` applies to every instance.

**The output of a mapped task.** When a mapped task returns a value, Airflow collects the returns and pushes them as a list under the *unmapped* task_id. So `ti.xcom_pull(task_ids="process_region")` returns `[value_0, value_1, ...]`.

**Mapping is not free.** Each mapped instance is a separate task instance in the metadata database, with its own state, its own logs, and its own slot. Mapping 10,000 items creates 10,000 task instances. The right granularity is usually "per region", "per customer", "per partition day" — not "per row".

**Mapping and the join.** A downstream task of a mapped task waits for *all* the mapped instances. It gets the list of returns. To join them, use a task that pulls the list:

```python
aggregate = PythonOperator(
    task_id="aggregate_regions",
    python_callable=aggregate_regions,
)

process_region >> aggregate
```

And if one mapped instance fails, the join is `upstream_failed` — unless you give the join `trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS`, in which case it runs with the partial results.

### The task-generating loop anti-pattern

Before dynamic task mapping, the only way to make a data-dependent number of tasks was to write a loop in the DAG file:

```python
# ANTI-PATTERN — never do this
for region in ["AMER", "APAC", "EMEA", "LATAM"]:
    task = PythonOperator(
        task_id=f"process_{region}",
        python_callable=process_region,
        op_kwargs={"region": region},
    )
    read >> task
```

It "works", and it is wrong for several reasons:

1. **The width is fixed at parse time.** The regions are hard-coded. If a fifth region appears, nothing happens — silently.
2. **Every task exists in every run**, even the ones with no data. The DAG looks busy forever.
3. **A DAG file with a loop can generate hundreds of tasks**, which slows down the scheduler's parsing of *every* DAG in the environment.
4. **It cannot be conditional.** Every loop iteration is created whether or not it is needed.

Dynamic task mapping fixes all four. The task count is now determined by the data at run time, and only the instances that are needed are created.

**A loop is still acceptable** when the number of items is genuinely static and small — say, three known environments — and you want each to have its own SLA. Just do not use a loop to express "however many rows there are".

### Cross-DAG dependencies

Three mechanisms, and they are not interchangeable.

**1. `TriggerDagRunOperator` — push.**

```python
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

trigger_next = TriggerDagRunOperator(
    task_id="trigger_downstream_dag",
    trigger_dag_id="branching_and_xcom_child",
    wait_for_completion=False,
    conf={"parent_run_id": "{{ run_id }}"},
)
```

The course's `04_branching_and_xcom.py` uses exactly this. Key parameters:

| Parameter | Meaning |
|---|---|
| `trigger_dag_id` | The DAG to start |
| `wait_for_completion` | If `True`, the task blocks until the other DAG finishes (holding a slot) |
| `conf` | The config dict passed to the other run's `{{ params }}` and `dag_run.conf` |
| `logical_date` | Which logical date to trigger it for |
| `reset_dag_run` | If `True`, clear an existing run and start over |
| `trigger_run_id` | A specific run id to create |
| `wait_for_completion_max_timedelta` | How long to wait when `wait_for_completion=True` |

**The `conf` is how you pass data.** It arrives in the triggered DAG as `{{ dag_run.conf }}` and, if the triggered DAG declares matching `params`, as `{{ params.x }}`.

```python
# In the triggered DAG:
def use_conf(**context) -> dict:
    """Read the config passed by the upstream DAG."""
    conf = context["dag_run"].conf or {}
    return {"parent_run_id": conf.get("parent_run_id", "unknown")}
```

**Caveat:** `conf` must be **JSON-serialisable**. It is stored in the metadata database.

**2. `ExternalTaskSensor` — pull.** Covered in chapter 9. Use it only when you cannot restructure the two DAGs.

**3. Datasets — declarative.** The next section.

### Datasets (Airflow 2.4+)

Datasets were called "data-aware scheduling" before 2.4. They are Airflow's declarative answer to "run this DAG when that data changes".

**How it works.** A dataset has a URI. Any DAG that *updates* that dataset becomes a **producer**. Any DAG that *schedules* on that dataset becomes a **consumer**.

```python
from airflow.datasets import Dataset

ORDERS_DATASET = Dataset("gs://YOUR_BUCKET/orders/{{ ds }}/orders.csv")
```

Hmm — dataset URIs are **not** templated per run. The URI is a static identifier. So you use a stable URI, and the *update* carries the run's context:

```python
from airflow.datasets import Dataset

ORDERS_DATASET = Dataset("gs://YOUR_BUCKET/orders")

publish = PythonOperator(
    task_id="publish_orders",
    python_callable=publish_orders,
    outlets=[ORDERS_DATASET],       # ← this task updates the dataset
)
```

And the consumer:

```python
with DAG(
    dag_id="consume_orders",
    schedule=[ORDERS_DATASET],       # ← this DAG is scheduled by the dataset
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
) as dag:
    consume = PythonOperator(
        task_id="consume_orders",
        python_callable=consume_orders,
    )
```

**The semantics.** When `publish_orders` succeeds, the dataset `gs://YOUR_BUCKET/orders` is recorded as updated. Every DAG scheduled on that dataset is then queued for a run.

**The critical detail:**

> **A dataset-triggered run is not tied to the producer's logical date.** The consumer runs *now*, with its own logical date. If you need the producer's date, you must pass it — through `params`, through an XCom, or by putting it in the dataset's *event* metadata.

Airflow 2.9+ added dataset **events**, which let you attach metadata to the update:

```python
from airflow.datasets import Dataset
from airflow.datasets.metadata import Metadata

publish = PythonOperator(
    task_id="publish_orders",
    python_callable=publish_orders,
    outlets=[
        Metadata(ORDERS_DATASET, extra={"logical_date": "{{ ds }}", "row_count": 1245}),
    ],
)
```

**Why Datasets are better than sensors for "wait for data":**

| | Sensor | Dataset |
|---|---|---|
| Polling | yes, every `poke_interval` | none |
| Worker slot | held (or transiently held) | none |
| Timeout | needed | not needed |
| Coupling to task names | yes (for `ExternalTaskSensor`) | none |
| Missed update detection | the sensor times out | the consumer simply never runs |

The trade-off: **a Dataset cannot time out.** If the producer never runs, the consumer never runs, and there is no built-in "the data did not arrive" signal. That is a real gap, and the answer is a separate alerting DAG or a monitoring check — not a sensor.

**The Composer angle.** On Composer, Datasets are supported and visible in the UI's Datasets tab, with the update history.

### The "wait for data" pattern

There are three variants, and they map to the three mechanisms.

**Variant A — the data arrives on a known schedule.** Don't wait. Schedule the consumer after the producer's known completion time, and use `ExternalTaskSensor` with an `execution_delta` only if you need to *confirm* the producer ran.

```python
# --- snippet: fragment (part of a larger structure) ---
consumer = DAG(
    dag_id="consumer",
    schedule="30 3 * * *",       # 03:30, after the producer's 02:00 run
    ...
)
```

**Variant B — the data arrives when it arrives, and the producer is yours.** Use a **Dataset**. The consumer is scheduled by the update. No polling.

**Variant C — the data arrives when it arrives, and the producer is not yours.** Use a **sensor**, in reschedule mode, with a timeout and a deliberate `soft_fail` policy.

The decision tree:

```text
Do you know when the data arrives?
├── YES → schedule it. (Variant A)
└── NO
    └── Do you control the producer?
        ├── YES → Dataset. (Variant B)
        └── NO  → Sensor, reschedule mode, bounded timeout. (Variant C)
```

### The "fan out then join" pattern, carefully

This is the pattern most often implemented wrong. Let me spell out the correct version.

```text
                     ┌─▶ load[AMER] ──┐
  stage ──▶ fan_out ─┼─▶ load[APAC] ──┼──▶ join
                     └─▶ load[EMEA] ──┘
```

**The implementation with dynamic mapping:**

```python
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

stage = PythonOperator(
    task_id="stage",
    python_callable=stage_partitions,
)

load = PythonOperator.partial(
    task_id="load_partition",
    python_callable=load_one_partition,
).expand_kwargs(stage.output)

join = PythonOperator(
    task_id="join",
    python_callable=join_partitions,
    trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
)

stage >> load >> join
```

**The join's Python:**

```python
def join_partitions(**context) -> dict:
    """Join the loaded partitions into the final table.

    The list of results comes from the mapped task's XCom — Airflow
    collects every mapped instance's return value into one list under
    the unmapped task_id.

    Args:
        context: The Airflow task context.

    Returns:
        A summary of the join.
    """
    results = context["ti"].xcom_pull(task_ids="load_partition") or []
    succeeded = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") != "success"]
    log.info("joined %d partitions (%d failed)", len(succeeded), len(failed))
    return {"joined": len(succeeded), "failed": len(failed)}
```

**The three mistakes people make:**

1. **Forgetting the trigger rule.** With the default `all_success`, one failed partition means the join never runs and the pipeline's final output is missing entirely.
2. **Pulling from the wrong task_id.** `xcom_pull(task_ids="load_partition")` returns the list; `xcom_pull(task_ids="load_partition[0]")` returns one instance's value.
3. **Assuming a fixed width.** The number of partitions changes with the data. A join that assumes four regions will break when there are five.

### Batch + stream hybrid

The most common "modern" architecture, and the one Airflow is best at supporting.

```text
┌─────────────────────────────────────────────────────────────┐
│ Pub/Sub ──▶ Dataflow Streaming ──▶ BigQuery (raw)        │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ continuously writes
                          ▼
              BigQuery raw.orders (partitioned by hour)
                          │
                          │ Airflow runs this every hour
                          ▼
        ┌───────────────────────────────────────┐
        │ Airflow: read the last hour's rows,   │
        │ validate, aggregate, publish          │
        └───────────────────────────────────────┘
```

**Airflow's role** is the batch half: the validation, the aggregation, the reconciliation, the reporting. **Dataflow's role** is the continuous ingest.

**The critical design decision: how does Airflow know a partition is complete?**

A streaming job writing to a BigQuery partition does not tell you it is *done*. If Airflow reads a partition at 14:05 while the stream is still writing to it, it processes a partial partition — and then the next run sees more rows for the same partition, which breaks idempotency (chapter 12).

There are three standard solutions:

**Solution A — a watermark / lateness delay.** Wait a fixed period after the window closes.

```python
wait_for_window = PythonSensor(
    task_id="wait_for_stream_window",
    python_callable=window_is_closed,
    mode="reschedule",
    timeout=3600,
    poke_interval=300,
    soft_fail=False,
)
```

**Solution B — a Dataflow job that reports completion.** Run a bounded (batch) Dataflow job for each window; it writes a marker when it finishes.

```python
from airflow.providers.google.cloud.operators.dataflow import DataflowCreateJobOperator

run_window = DataflowCreateJobOperator(
    task_id="run_window_job",
    job_name="orders-window-{{ ds }}-{{ ts }}",
    gcp_conn_id="google_cloud_default",
    region="us-central1",
    dataflow_config={
        "job_type": "Batch",
        "template_path": "gs://YOUR_BUCKET/templates/orders_batch.py",
        "temp_location": "gs://YOUR_BUCKET/tmp",
        "parameters": {"window_start": "{{ data_interval_start }}"},
    },
    wait_for_completion=True,
)
```

**Solution C — a Dataset.** The bounded Dataflow job updates a Dataset when it finishes; the Airflow DAG is scheduled on that Dataset. This is the cleanest, and it removes the coordination problem entirely.

```python
# --- snippet: fragment (part of a larger structure) ---
ORDERS_WINDOW = Dataset("gs://YOUR_BUCKET/windows/orders")

publish = DataflowCreateJobOperator(
    task_id="run_window_job",
    ...
    outlets=[ORDERS_WINDOW],
)
```

**The rule:** never let Airflow read a partition that a stream might still be writing to, unless the read is scoped to a *closed* window and the stream has a guaranteed lateness bound.

### The anti-patterns

**1. The task-generating loop.** Covered above.

**2. `SubDagOperator`.** Removed in Airflow 2.0. It existed to nest a DAG inside a DAG, and it was confusing enough that Airflow deleted it. Use `TaskGroup` instead:

```python
# --- snippet: fragment (part of a larger structure) ---
from airflow.utils.task_group import TaskGroup

with TaskGroup(group_id="load") as load_group:
    load_amer = PythonOperator(task_id="load_amer", ...)
    load_apac = PythonOperator(task_id="load_apac", ...)
```

A `TaskGroup` is a UI grouping, not a scheduling unit. Its tasks are addressed as `load.load_amer`.

**3. The one giant DAG.** A DAG with 200 tasks that does everything — extract from four sources, transform, load to three destinations, reconcile, report. Problems:
- One failure fails everything downstream.
- The DAG graph is unreadable.
- Retries are all-or-nothing in terms of what re-runs.
- There is no way to run the reconciliation without the extract.

**Split it** into DAGs by *boundary*, not by *layer*. A good boundary is a point where one DAG's output is a well-defined artefact another DAG can depend on. Bad boundaries are "after the extract step" — because the extract is not an artefact, it is a phase.

**4. Using Airflow as a data processing engine.** Covered thoroughly in chapter 15.

**5. Sensors as a substitute for good contracts.** Covered in chapter 9.

---

## 🛠️ Hands-On

### Step 1 — build the fan-out helper

```python
# project/core/fanout.py
"""Fan-out helpers: split work so the DAG can parallelise."""
from __future__ import annotations

from pipeline_logic import summarise_by_region


def regions_to_process(summary: dict[str, dict[str, float]]) -> list[str]:
    """Return the regions that produced revenue, sorted.

    Args:
        summary: The output of `summarise_by_region`.

    Returns:
        A sorted list of region codes.
    """
    return sorted(
        region for region, bucket in summary.items() if bucket["order_count"] > 0
    )


def load_tasks(summary: dict[str, dict[str, float]], partition: str) -> list[dict]:
    """Return one load task per region, ready for `.expand_kwargs()`.

    Args:
        summary: The output of `summarise_by_region`.
        partition: The partition being loaded, e.g. "20260115".

    Returns:
        A list of dicts, each with a `region` and a `partition` key.
    """
    return [
        {"region": region, "partition": partition}
        for region in regions_to_process(summary)
    ]


def region_summary_csv(summary: dict[str, dict[str, float]], region: str) -> str:
    """Render the summary for a single region.

    Args:
        summary: The output of `summarise_by_region`.
        region: The region to render.

    Returns:
        A CSV document with a header and one data row.
    """
    bucket = summary[region]
    return (
        "region,order_count,revenue_eur\n"
        f"{region},{int(bucket['order_count'])},{bucket['revenue_eur']:.2f}\n"
    )
```

### Step 2 — run it against the real sample data

```bash
cd data-engineering/data-Course/google/composer
python3 - <<'PY'
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import transform_orders, summarise_by_region
from fanout import regions_to_process, load_tasks, region_summary_csv

lines = open("sample_data/orders.csv").read().splitlines()
accepted, _ = transform_orders(lines)
summary = summarise_by_region(accepted)

regions = regions_to_process(summary)
print(f"regions ({len(regions)}): {regions}")
print()
print("expand_kwargs payload:")
for task in load_tasks(summary, "20260115"):
    print(f"  {task}")
print()
for region in regions:
    print(region_summary_csv(summary, region), end="")
PY
```

Expected output:

```text
regions (4): ['AMER', 'APAC', 'EMEA', 'LATAM']

expand_kwargs payload:
  {'region': 'AMER', 'partition': '20260115'}
  {'region': 'APAC', 'partition': '20260115'}
  {'region': 'EMEA', 'partition': '20260115'}
  {'region': 'LATAM', 'partition': '20260115'}

region,order_count,revenue_eur
AMER,318,113592.19
region,order_count,revenue_eur
APAC,285,108194.92
region,order_count,revenue_eur
EMEA,322,118423.22
region,order_count,revenue_eur
LATAM,320,110646.18
```

Four regions → four mapped task instances, determined by the data at run time.

### Step 3 — the deployable DAG with dynamic mapping

```python
# --- snippet: fragment (part of a larger structure) ---
# project/dags/09_fanout_patterns.py
"""
09_fanout_patterns.py — the pattern catalogue, in one DAG.

Demonstrates:
  * dynamic task mapping with `.expand()` and `.expand_kwargs()`
  * `BranchOperator` and the join trigger rule
  * `ShortCircuitOperator`
  * a `TaskGroup` for UI grouping
  * `TriggerDagRunOperator` with `conf`
  * a Dataset (Airflow 2.4+) as a cross-DAG dependency
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.datasets import Dataset
from airflow.operators.python import (
    BranchOperator,
    PythonOperator,
    ShortCircuitOperator,
)
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule

log = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

#: A stable URI. Dataset URIs are NOT templated per run — the run's
#: context travels with the update, not in the URI.
ORDERS_DATASET = Dataset("gs://YOUR_BUCKET/datasets/orders")


def read_orders(**context) -> list[str]:
    """Read the raw order lines for this run.

    Args:
        context: The Airflow task context.

    Returns:
        The raw CSV lines.
    """
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "sample_data" / "orders.csv"
    return path.read_text(encoding="utf-8").splitlines()


def summarise(**context) -> dict:
    """Aggregate the accepted orders per region.

    Args:
        context: The Airflow task context.

    Returns:
        The region summary.
    """
    from pipeline_logic import summarise_by_region, transform_orders

    raw = context["ti"].xcom_pull(task_ids="read_orders") or []
    accepted, _ = transform_orders(raw)
    return summarise_by_region(accepted)


def list_regions(**context) -> list[str]:
    """Return the regions to process.

    Args:
        context: The Airflow task context.

    Returns:
        A list of region codes.
    """
    from fanout import regions_to_process

    summary = context["ti"].xcom_pull(task_ids="summarise") or {}
    return regions_to_process(summary)


def build_load_tasks(**context) -> list[dict]:
    """Return one dict per region, for `.expand_kwargs()`.

    Args:
        context: The Airflow task context.

    Returns:
        A list of dicts with `region` and `partition` keys.
    """
    from fanout import load_tasks

    summary = context["ti"].xcom_pull(task_ids="summarise") or {}
    return load_tasks(summary, context["ds_nodash"])


def load_one_region(**context) -> dict:
    """Load one region. This is the mapped task's body.

    Args:
        context: The Airflow task context.

    Returns:
        A dict describing what was loaded.
    """
    region = context["params"]["region"]
    partition = context["params"]["partition"]
    log.info("loading region=%s partition=%s", region, partition)
    return {"status": "success", "region": region, "partition": partition}


def join_regions(**context) -> dict:
    """Join the mapped task's results.

    Airflow collects every mapped instance's return value into one
    list, stored under the *unmapped* task_id.

    Args:
        context: The Airflow task context.

    Returns:
        A summary of the join.
    """
    results = context["ti"].xcom_pull(task_ids="load_region") or []
    log.info("join saw %d mapped instances", len(results))
    return {"joined": len(results), "regions": [r.get("region") for r in results]}


def choose_strategy(**context) -> list[str]:
    """Choose the load strategy.

    Args:
        context: The Airflow task context.

    Returns:
        A one-element list naming the branch to take.
    """
    from pipeline_logic import should_run_full_load

    summary = context["ti"].xcom_pull(task_ids="summarise") or {}
    rows = sum(int(b["order_count"]) for b in summary.values())
    threshold = 1_000_000
    chosen = "full_load" if should_run_full_load(rows, threshold) else "incremental_load"
    log.info("rows=%d -> %s", rows, chosen)
    return [chosen]


def full_load(**context) -> str:
    """The full-load branch.

    Args:
        context: The Airflow task context.

    Returns:
        A description.
    """
    return "full_load"


def incremental_load(**context) -> str:
    """The incremental branch.

    Args:
        context: The Airflow task context.

    Returns:
        A description.
    """
    return f"incremental_load:{context['ds_nodash']}"


with DAG(
    dag_id="fanout_patterns",
    description="Fan-out, dynamic mapping, branching, and cross-DAG dependencies.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["tutorial", "patterns"],
) as dag:
    read = PythonOperator(task_id="read_orders", python_callable=read_orders)
    agg = PythonOperator(task_id="summarise", python_callable=summarise)

    # --- Pattern 2: fan-out / fan-in, statically declared ------------
    with TaskGroup(group_id="static_fanout") as static_group:
        emea = PythonOperator(task_id="load_emea", python_callable=load_one_region)
        amer = PythonOperator(task_id="load_amer", python_callable=load_one_region)
        apac = PythonOperator(task_id="load_apac", python_callable=load_one_region)

    static_join = PythonOperator(
        task_id="static_join",
        python_callable=join_regions,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    # --- Pattern 4: dynamic task mapping -----------------------------
    regions = PythonOperator(task_id="list_regions", python_callable=list_regions)

    mapped = PythonOperator.partial(
        task_id="load_region",
        python_callable=load_one_region,
    ).expand(region=regions.output)

    mapped_kwargs = PythonOperator.partial(
        task_id="load_region_kw",
        python_callable=load_one_region,
    ).expand_kwargs(build_load_tasks)

    mapped_join = PythonOperator(
        task_id="mapped_join",
        python_callable=join_regions,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    # --- Pattern 3: conditional execution ----------------------------
    branch = BranchOperator(task_id="choose_strategy", python_callable=choose_strategy)
    full = PythonOperator(task_id="full_load", python_callable=full_load)
    incremental = PythonOperator(task_id="incremental_load", python_callable=incremental_load)
    branch_join = PythonOperator(
        task_id="branch_join",
        python_callable=lambda **ctx: "joined",
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    # --- Pattern 5: cross-DAG, push -----------------------------------
    trigger_next = TriggerDagRunOperator(
        task_id="trigger_downstream",
        trigger_dag_id="fanout_patterns_child",
        wait_for_completion=False,
        conf={"parent_run_id": "{{ run_id }}", "logical_date": "{{ ds }}"},
    )

    read >> agg >> [emea, amer, apac] >> static_join
    agg >> regions >> mapped >> mapped_join
    agg >> build_load_tasks >> mapped_kwargs
    agg >> branch >> [full, incremental] >> branch_join
    static_join >> trigger_next
```

### Step 4 — the Dataset consumer DAG

```python
# project/dags/10_dataset_consumer.py
"""
10_dataset_consumer.py — a DAG scheduled by a Dataset (Airflow 2.4+).

The producer's DAG updates the dataset; this DAG is queued when that
happens. There is no polling, no sensor, and no slot held while
waiting.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.datasets import Dataset
from airflow.operators.python import PythonOperator

log = logging.getLogger(__name__)

ORDERS_DATASET = Dataset("gs://YOUR_BUCKET/datasets/orders")


def consume(**context) -> dict:
    """Consume the newly-available orders.

    Args:
        context: The Airflow task context.

    Returns:
        A dict describing what was consumed.
    """
    # The dataset-triggered run has its own logical date — it is NOT
    # the producer's logical date. If you need the producer's date,
    # pass it explicitly (via params or an event).
    log.info("consuming orders; logical_date=%s", context["logical_date"])
    return {"consumed": True, "logical_date": str(context["logical_date"])}


with DAG(
    dag_id="dataset_consumer",
    description="Scheduled by a Dataset update, not by a clock.",
    schedule=[ORDERS_DATASET],
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    tags=["tutorial", "datasets"],
) as dag:
    consume_orders = PythonOperator(
        task_id="consume_orders",
        python_callable=consume,
        outlets=[ORDERS_DATASET],
    )
```

### Step 5 — verify the pattern logic locally

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import transform_orders, summarise_by_region
from fanout import regions_to_process, load_tasks

lines = open("sample_data/orders.csv").read().splitlines()
accepted, rejected = transform_orders(lines)
summary = summarise_by_region(accepted)

regions = regions_to_process(summary)
tasks = load_tasks(summary, "20260115")

print(f"mapped instances (expand)    : {len(regions)} -> {regions}")
print(f"mapped instances (expand_kwargs): {len(tasks)} -> {[t['region'] for t in tasks]}")
print()
print("All mapped instances share the same task_id and differ by map_index:")
for i, region in enumerate(regions):
    print(f"  load_region[{i}]  region={region}")
PY
```

Expected output:

```text
mapped instances (expand)    : 4 -> ['AMER', 'APAC', 'EMEA', 'LATAM']
mapped instances (expand_kwargs): 4 -> ['AMER', 'APAC', 'EMEA', 'LATAM']

All mapped instances share the same task_id and differ by map_index:
  load_region[0]  region=AMER
  load_region[1]  region=APAC
  load_region[2]  region=EMEA
  load_region[3]  region=LATAM
```

### Step 6 — verify the existing branch DAG still behaves

The `branching_load` DAG in the local runner already implements the fan-out-then-join pattern with a branch:

```bash
python3 project/local_runner.py --dag branching_load --date 2026-01-15 --vars "{\"full_load_threshold\": 100}"
```

Expected output (excerpt):

```text
INFO       rows=1245 threshold=100 -> full_load
INFO   ✓ full_load                success
INFO   ○ incremental_load         skipped
INFO   ✓ finalise                 success
```

The `finalise` task is the join. It runs with `trigger_rule="none_failed"`, which is exactly the pattern.

### Step 7 — confirm the underlying pipeline output is unchanged

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

---

## 🛠️ Common Errors and Fixes

### `TypeError: unsupported operand type(s) for |: 'XComArg' and 'list'`

**Cause:** trying to use `|` (the pipe operator) with an `XComArg`. The pipe operator is for *operators* in a chain, not for combining task outputs.

**Fix:** use `>>` for dependencies, and `xcom_pull` for data flow:

```python
# Wrong
result = task_a | task_b

# Right
task_a >> task_b
```

### `AttributeError: 'PythonOperator' object has no attribute 'expand'`

**Cause:** calling `.expand()` on a constructed operator instead of on `PythonOperator.partial(...)`.

**Fix:**
```python
# Wrong
task = PythonOperator(task_id="x", python_callable=f).expand(region=regions.output)

# Right
task = PythonOperator.partial(task_id="x", python_callable=f).expand(region=regions.output)
```

### `airflow.exceptions.AirflowException: Cannot map over a list with more than 1024 elements.`

**Cause:** the mapped list is longer than `[core] max_map_length` (default 1024).

**Fix:** raise the limit, or — better — reduce the granularity. Mapping per row is almost always wrong; map per region, per customer, or per partition.

```ini
[core]
max_map_length = 10000
```

### The mapped task's XCom is `None` when pulled

**Cause:** the mapped task returned `None`, or the pull used the wrong task_id.

**Fix:** the pull uses the **unmapped** task_id:

```python
results = ti.xcom_pull(task_ids="load_region")      # the list
one = ti.xcom_pull(task_ids="load_region", map_indexes=0)  # one instance
```

And make sure the mapped task actually returns something.

### The join task never ran, even though most branches succeeded

**Cause:** the default `trigger_rule="all_success"`. One failed upstream means the join is `upstream_failed`.

**Fix:**
```python
trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
```

### The join task ran with no data

**Cause:** `trigger_rule="none_failed"` and *every* upstream branch was skipped — e.g. a `BranchOperator` chose a path that did not include the join.

**Fix:** use `NONE_FAILED_MIN_ONE_SUCCESS` instead. It requires at least one upstream to have succeeded.

### `Task is in the 'upstream_failed' state` after a branch

**Cause:** the join's upstream included a *skipped* branch, and the trigger rule did not permit it.

**Fix:** the same as above. Also check the branch's `python_callable` actually returns the task_ids — a `BranchOperator` whose callable returns `None` skips everything downstream.

### The Dataset consumer never ran

**Cause 1:** the producer task did not declare the dataset in `outlets`.

**Fix:**
```python
publish = PythonOperator(
    task_id="publish_orders",
    python_callable=publish_orders,
    outlets=[ORDERS_DATASET],
)
```

**Cause 2:** the producer's dataset URI and the consumer's URI differ by a single character — a trailing slash, a different bucket.

**Fix:** define the `Dataset` object once, in a shared module, and import it in both DAGs. That way the two URIs cannot drift.

**Cause 3:** the producer task failed, so the dataset was never updated.

### The Dataset consumer ran with the wrong logical date

**Cause:** a dataset-triggered run gets its own logical date (the time it was queued), not the producer's.

**Fix:** pass the producer's date explicitly. In Airflow 2.9+, use dataset event metadata:

```python
from airflow.datasets.metadata import Metadata

outlets=[Metadata(ORDERS_DATASET, extra={"logical_date": "{{ ds }}"})]
```

### `TriggerDagRunOperator` failed with `airflow.exceptions.DagNotFound: DAG: [my_dag] not found`

**Cause:** the target DAG does not exist in the environment, or the name is misspelled.

**Fix:** check the DAG list. Note that a DAG with an import error also appears as "not found" — check the environment's DAG import-error log.

### `TriggerDagRunOperator` failed with a duplicate run id error

**Cause:** a run for that logical date already exists, and `reset_dag_run` is `False`.

**Fix:** set `reset_dag_run=True` if overwriting is intended, or `trigger_run_id` to a unique id.

### `conf` did not arrive in the triggered DAG

**Cause:** the triggered DAG reads `{{ dag_run.conf }}`, but `conf` was passed as a Jinja string that did not render.

**Fix:** confirm the value rendered (check the trigger task's rendered fields in the UI). Also confirm `conf` is JSON-serialisable — a `datetime` object raises:

```text
TypeError: Object of type datetime is not JSON serializable
```

### `SubDagOperator` cannot be imported

**Cause:** it was removed in Airflow 2.0.

**Fix:** use `TaskGroup`. It is a UI grouping rather than a scheduling unit, but it is what `SubDagOperator` was usually being used for.

---

## 💡 Production Notes

- **Prefer dynamic task mapping to task-generating loops.** A loop in a DAG file is fixed at parse time, creates tasks that never run, and slows the parsing of every DAG in the environment.
- **Map at a useful granularity.** Per region, per partition, per customer — not per row. Each mapped instance is a task instance in the metadata database.
- **Watch `max_map_length` (default 1024).** Raising it is a symptom of too-fine granularity.
- **Every join after a branch needs `NONE_FAILED_MIN_ONE_SUCCESS`.** `none_failed` runs the join even when every branch was skipped; `all_success` never runs it when one fails.
- **Use `TaskGroup` for grouping, not for scheduling.** Task groups do not create a scheduling boundary — tasks in a group still run independently.
- **Put `Dataset` objects in a shared module.** Two DAGs that spell the URI differently will never connect, and nothing will tell you.
- **A Dataset cannot time out.** If the producer stops running, the consumer silently stops running. That gap needs a separate monitoring check, not a sensor.
- **Dataset-triggered runs have their own logical date.** If the consumer needs the producer's date, pass it explicitly.
- **Prefer `TriggerDagRunOperator` to `ExternalTaskSensor`** when you control both DAGs: it creates the run rather than polling for it.
- **Keep `conf` small and JSON-serialisable.** It is stored in the metadata database and read by the triggered DAG.
- **In a batch + stream hybrid, never read a partition that a stream may still be writing to.** Use a bounded window plus a completion signal (a bounded Dataflow job, or a Dataset).
- **Split a giant DAG at artefact boundaries**, not at phase boundaries. "After the extract step" is a phase; "after the curated orders table is published" is an artefact.
- **Do not use `SubDagOperator`** — it was removed in Airflow 2.0 and its replacement does not nest scheduling.

---

## 🔑 Key Takeaways

- The pattern catalogue: linear, fan-out/fan-in, conditional, dynamic fan-out, cross-DAG push/pull, event-driven, wait-for-data, batch+stream hybrid, periodic reconciliation.
- **Dynamic task mapping (2.3+)** uses `Operator.partial(...).expand(x=task.output)` or `.expand_kwargs(list_of_dicts)`. It creates one task instance per element, determined at run time.
- **The task-generating loop is an anti-pattern.** Its width is fixed at parse time and it slows every DAG's parsing.
- **A join after a branch needs `TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS`.** `all_success` never runs it after a failure; `none_failed` runs it even when everything was skipped.
- **Cross-DAG, three ways:** `TriggerDagRunOperator` (push), `ExternalTaskSensor` (pull), **Datasets** (declarative).
- **Datasets (2.4+)** are the modern "wait for data" answer: no polling, no slot, no timeout, no coupling — but they also cannot time out, and the consumer's logical date is its own, not the producer's.
- **Wait-for-data decision tree:** known arrival time → schedule it; you control the producer → Dataset; you do not → reschedule-mode sensor.
- **Batch + stream hybrid:** Airflow runs the batch half, the stream runs continuously, and the critical question is *how Airflow knows a window is closed*. Never read a partition a stream may still be writing to.
- **Split giant DAGs at artefact boundaries**, not phase boundaries.

---

## 📚 Practice Exercises

1. **Convert the branching DAG to dynamic mapping.** Take `project/dags/04_branching_and_xcom.py`'s `full_load` / `incremental_load` branch and replace it with a dynamically-mapped `load_region` task that expands over the regions present in the data. Then write the join task with the correct trigger rule, and a test that asserts the join runs when one mapped instance fails and when all of them succeed. *Expected answer:* the fan-out comes from `regions_to_process(summary)`, the mapped task is `PythonOperator.partial(task_id="load_region", python_callable=load_one_region).expand(region=regions.output)`, and the join uses `TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS`. The tests use the local runner's `run_dag` with a DAG where one region raises, asserting `run.state["join"] == "success"` and that the mapped results list contains only the successful regions.

2. **Prove the loop anti-pattern is worse than it looks.** Write a DAG file that generates 50 tasks with a loop, and a second that generates one mapped task. Compare the number of task instances created when the data contains 4 regions, and explain what each DAG's scheduler load looks like at parse time. *Expected answer:* the loop version creates 50 task instances in *every* run regardless of data, all of which show in the UI and all of which occupy a slot in the metadata database; the mapped version creates 4. At parse time the loop version's scheduler work is proportional to 50 (and grows every time someone adds a region), while the mapped version's is constant.

3. **Design a Dataset-based producer/consumer pair.** Write two DAGs: `orders_producer` (which writes a partition and updates the dataset) and `orders_consumer` (scheduled on the dataset). Then answer three questions in writing: (a) how does the consumer learn the producer's logical date? (b) what happens if the producer fails silently for a week? (c) how would you prevent the consumer from running twice for one producer update? *Expected answer:* (a) via dataset event metadata (`Metadata(ORDERS_DATASET, extra={"logical_date": "{{ ds }}"})`, Airflow 2.9+) or by passing it in `params`; (b) the consumer simply never runs, and nothing reports it — this is the gap Datasets cannot close, so it needs a monitoring DAG that checks the producer's last successful run; (c) by making the consumer idempotent (chapter 12) and by using a deterministic destination keyed on the producer's logical date, so a duplicate trigger is a no-op.

4. **Design the batch + stream hybrid coordination.** A Dataflow streaming job writes to `raw.orders` partitioned by hour. Airflow must aggregate each closed hour exactly once. Write the coordination mechanism, in two variants (a completion signal and a Dataset), and explain precisely why the naive approach — read the previous hour's partition at a fixed time — is wrong. *Expected answer:* the naive approach is wrong because the stream may still be writing to the hour's partition when Airflow reads it (lateness), so Airflow processes a partial partition; and when the stream later writes the remaining rows, the partition now has more data than the aggregation accounted for, breaking idempotency — the next run would see a different row count for the same partition. The fix is either a bounded (batch) Dataflow job per window that writes a marker when complete, or a Dataset updated by that job, which queues the Airflow run only after the window is provably closed.

5. **Choose the trigger rule for six join scenarios.** For each, state the correct `trigger_rule` and why: (a) a join after a `BranchOperator` where either branch may be taken; (b) a cleanup task that must run even if the load failed; (c) a join where every upstream must have succeeded and you want to fail loudly otherwise; (d) a join where at least one upstream must have succeeded; (e) an alert task that should fire only if something failed; (f) a task that must run after every upstream has finished, successful or not. *Expected answer:* (a) `NONE_FAILED_MIN_ONE_SUCCESS`; (b) `all_done`; (c) `all_success` (the default); (d) `NONE_FAILED_MIN_ONE_SUCCESS`; (e) `one_failed`; (f) `all_done`.

6. **Audit the course's DAGs against the pattern catalogue.** For each DAG in `project/dags/`, name the patterns it demonstrates, and identify the one pattern each is *missing* that a production version would need. Then pick the DAG with the biggest gap and sketch the improvement. *Expected answer:* `01_hello_world.py` — linear only; it would need a load pattern and an SLA. `02_templating_and_variables.py` — linear; it would need a Dataset consumer or a downstream trigger. `03_etl_bigquery.py` — linear with an SLA, a retry policy, an idempotent partitioned load, and a `depends_on_past=False` policy; it is missing fan-out (per-region loads) and a cross-DAG handoff. `04_branching_and_xcom.py` — conditional execution, XCom, a sensor, a cross-DAG trigger, and a join with `none_failed`; it is missing dynamic mapping (the branch's two fixed tasks could be a mapped task over the load strategies) and a Dataset-based alternative to the sensor.

---

## 📖 Further Reading

- Airflow dynamic task mapping — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dynamic-task-mapping.html
- Airflow Datasets (data-aware scheduling, 2.4+) — https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/datasets.html
- Airflow branching and `trigger_rule` — https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/branches.html
- Airflow `TaskGroup` — https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/taskgroups.html
- Airflow cross-DAG dependencies — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#cross-dag-dependencies
- Airflow deferrable operators — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/deferring.html
- Airflow `TriggerDagRunOperator` API — https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/operators/trigger_dagrun/index.html
- Google Cloud Composer: scheduling DAGs — https://cloud.google.com/composer/docs/scheduling-best-practices
- Google Cloud Composer: Datasets — https://cloud.google.com/composer/docs/datasets
