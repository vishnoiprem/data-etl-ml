# 1.3 — DAGs and Scheduling

> **Section 1 · Composer Fundamentals & Model · Lecture 1.3 · 9:30**

## 🎯 What you will learn

- The anatomy of a `DAG` object — every parameter and what it actually controls
- `start_date`, `schedule`, `catchup`, `max_active_runs` — and the interactions between them
- The schedule formats: `@daily`, cron expressions, `timedelta`, and Datasets
- Logical date vs execution date vs data interval — the three dates Airflow gives you and which one to use
- The half-open interval convention `[start, end)` and the off-by-one it prevents
- Why `catchup=True` is dangerous, and how to backfill safely
- Version differences: `schedule` vs the deprecated `schedule_interval`

---

## 🧠 Concept

### The DAG object

Everything about a DAG's *behaviour* comes from its constructor. Here is
the full anatomy, using the course's `01_hello_world.py` as the anchor:

```python
with DAG(
    dag_id="hello_world",
    description="The smallest useful DAG — verify your Composer environment.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["tutorial", "composer"],
    params={"audience": "data-engineers"},
) as dag:
    ...
```

| Parameter | Meaning | Default | Notes |
|---|---|---|---|
| `dag_id` | unique identifier | required | must be unique across the environment |
| `schedule` | when to create runs | `None` | cron / timedelta / dataset / `None` |
| `start_date` | earliest logical date to consider | required | timezone-aware, strongly recommended |
| `catchup` | create runs for missed intervals | `False` | the dangerous one |
| `max_active_runs` | concurrent runs of this DAG | `16` | `1` for fixed-destination pipelines |
| `max_active_tasks` | concurrent tasks across all runs | `16` | rarely changed |
| `default_args` | default kwargs for every task | `{}` | owner, retries, retry_delay, depends_on_past |
| `params` | DAG-run parameters with defaults | `{}` | overridable per run |
| `sla` | time allowed after the data interval ends | `None` | measured from interval end |
| `sla_miss_callback` | called on SLA miss | `None` | receives the task context |
| `tags` | labels for the UI | `[]` | filterable in the UI |
| `description` | human description | `None` | shown in the UI |
| `dagrun_timeout` | max seconds a run may take | `None` | kills the whole run |
| `on_failure_callback` / `on_success_callback` | run-level callbacks | `None` | for alerting |
| `concurrency` | alias for `max_active_runs` | | deprecated in 2.x |
| `schedule_interval` | **old name for `schedule`** | | deprecated since 2.4 |

### `start_date`

`start_date` is the **earliest logical date Airflow will consider**. It
is not "when the DAG was created" and it is not "when the first run
happens".

Three rules:

1. **It should be timezone-aware.** Use
   `datetime(2026, 1, 1, tzinfo=timezone.utc)`. A naive datetime is
   interpreted in the Airflow server's local timezone, which differs
   between your laptop, a self-hosted server, and Composer. The course
   always uses UTC.
2. **It is a floor, not a trigger.** Setting `start_date` to
   `2026-01-01` does not create 20 runs for January. It says: *if* runs
   are to be created for dates on or after 2026-01-01, this DAG is
   eligible.
3. **Changing it retroactively can create history.** If you lower
   `start_date` and `catchup=True`, the scheduler will want to create
   runs for the newly-eligible interval.

### `schedule`

`schedule` decides *when a run is created*. It does not decide when a
task runs, and it does not decide what data the run processes — that is
the logical date's job.

| Form | Example | Meaning |
|---|---|---|
| **Preset** | `"@daily"` | once a day, at midnight UTC |
| | `"@hourly"` | once an hour, on the hour |
| | `"@weekly"` | Mondays at midnight UTC |
| | `"@monthly"` | 1st of the month at midnight UTC |
| | `"@yearly"` / `"@annually"` | 1 January at midnight UTC |
| | `"@reboot"` | once, when the scheduler starts |
| **Cron** | `"0 6 * * *"` | 06:00 every day (UTC) |
| | `"30 2 * * 0"` | 02:30 every Sunday |
| | `"0 */4 * * *"` | every four hours |
| **Timedelta** | `timedelta(hours=6)` | every six hours from `start_date` |
| **Dataset** | `[orders_dataset]` | when the dataset is updated (Airflow 2.4+) |
| **None** | `None` | never scheduled; manual trigger only |

Two Airflow-version notes that matter in practice:

- **`schedule_interval` → `schedule`.** The parameter was renamed in
  Airflow 2.4. `schedule_interval` still works but is deprecated and
  emits a `DeprecationWarning`. **Use `schedule`.** If you maintain an
  older DAG you will see `schedule_interval="@daily"` — treat it as a
  to-do, not a style choice.
- **Cron is evaluated in UTC** by default in Airflow 2.x. A `0 6 * * *`
  cron fires at 06:00 UTC, not 06:00 local. Composer does not change
  this.

The `timedelta` form is underused and worth knowing:

```python
DAG(
    dag_id="hourly_ingest",
    schedule=timedelta(hours=6),
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
)
```

With a `timedelta` schedule the logical date is still the *interval
start*, but the interval itself is six hours wide.

### The presets, expanded

`@daily` is not magic — it is exactly `"0 0 * * *"`. `@hourly` is
`"0 * * * *"`. `@weekly` is `"0 0 * * 0"` (Sunday). Knowing this lets
you write the cron you actually want.

Airflow also accepts the extended cron syntax with year and day-of-week
ranges (`0 0 1 1 *` for 1 January), though the UI does not always render
it helpfully.

### `catchup`

`catchup=True` tells the scheduler: **"for every scheduled interval
between `start_date` and now that has no run, create one."**

```python
DAG(
    dag_id="backfill_danger",
    schedule="@daily",
    start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
    catchup=True,     # ← two years of runs
)
```

The moment this DAG is deployed, the scheduler creates ~730 DAG runs.
Each one creates task instances. Each one can consume a BigQuery load
quota, a GCS write budget, or an API rate limit. If the pipeline is not
idempotent, you have just corrupted two years of data.

**The default reason catchup is dangerous is that historical data often
does not exist in the form the pipeline expects.** A pipeline written in
2026 may reference a column added in 2026; backfilling to 2024 fails on
every run. A pipeline that reads from a partner API may find that the
partner only retains 90 days of history.

**The correct default is `catchup=False`**, which is why every DAG in
this course sets it explicitly:

```python
catchup=False,
```

and why the local runner's `DAG` class defaults to `catchup=False`
too.

When you *do* want to backfill, you do it deliberately with a **backfill
job** (the `airflow dags backfill` CLI in OSS, the **Run → Backfill**
button in Composer), not by flipping `catchup` and waiting.

### `max_active_runs`

`max_active_runs` caps how many runs of the same DAG may be in flight at
once.

```text
max_active_runs=1:
  run(Jan 1) ──────────────▶ done
       run(Jan 2) ──────────────────────▶ done
            run(Jan 3) ───────────────────────────▶ done

max_active_runs=3:
  run(Jan 1) ──────────────▶ done
  run(Jan 2) ───────▶ done
  run(Jan 3) ─────▶ done
```

Set it to `1` when:

- The pipeline writes to a **fixed destination** (one BigQuery table, one
  GCS prefix). Two concurrent runs interleave their writes.
- The pipeline reads a **mutable source** and must see a consistent
  snapshot.
- The pipeline is expensive and you want to serialise the cost.

Set it higher when:

- The runs are **independent** — each writes to its own date partition
  and reads its own date's data.
- You want to catch up quickly after an outage.

`max_active_tasks` is the other half: it caps concurrent *tasks* across
all runs of the DAG. It is a blunt instrument; use a **pool** for
cross-DAG concurrency control.

### Logical date vs execution date vs data interval

This is the most important section in the chapter. Airflow gives you
several dates, and confusing them is the source of an entire class of
production bugs.

| Name | What it is | Value for the 2026-01-15 daily run |
|---|---|---|
| **Logical date** | the *label* on the run; the start of the data it processes | `2026-01-15T00:00:00+00:00` |
| **Execution date** | the old name for logical date | same value |
| **Data interval** | `[logical_date, next_schedule)` | `[2026-01-15, 2026-01-16)` |
| **Wall-clock start** | when the scheduler actually created the run | `2026-01-16T00:05:00+00:00` |
| **End date** | when the run finished | varies |

Read that table again and note the critical fact: **the logical date is
`2026-01-15`, but the run happened on `2026-01-16`.** The run is
labelled with the day of data it processes, not the day it executed.

This is why Airflow renamed `execution_date` to `logical_date` in
Airflow 2.2 (and made the rename complete in the UI in Airflow 2.x /
Airflow 3). "Execution date" was actively misleading: it is not when the
DAG executed.

The `run_id` encodes the same thing:

```text
scheduled__2026-01-15T00:00:00+00:00
         └──────┬──────┘
        the logical date, not the wall clock
```

### The half-open interval convention

Airflow's data interval is **half-open**: `[start, end)`.

```text
        data_interval_start                    data_interval_end
                │                                      │
   ─────────────┼──────────────────────────────────────┼─────────────▶
                ▼                                      ▼
        2026-01-15T00:00:00                    2026-01-16T00:00:00
                │                              │
                └──── included ──────────────────┘
                        excluded
```

The interval *includes* its start and *excludes* its end. This is the
correct convention for partitioning, because it guarantees that every
instant belongs to **exactly one** interval.

The alternative — a closed interval `[start, end]` — double-counts the
boundary:

```text
Jan 15's interval: [2026-01-15, 2026-01-16]   ← includes Jan 16 00:00
Jan 16's interval: [2026-01-16, 2026-01-17]   ← also includes Jan 16 00:00
                          ▲
                   counted twice
```

The boundary row — an order placed at exactly `2026-01-16T00:00:00Z` —
lands in both days. The monthly totals are then wrong by one row, and
nobody notices for a month.

The course's `logical_date_window()` implements the convention, with an
escape hatch for systems whose filters are inclusive:

```python
from pipeline_logic import logical_date_window

logical_date_window("2026-01-15")
# ('2026-01-15', '2026-01-16')       ← half-open, the default

logical_date_window("2026-01-15", include_end=True)
# ('2026-01-15', '2026-01-15')       ← inclusive end for legacy systems
```

And the BigQuery filter in `03_etl_bigquery.py` matches it exactly:

```sql
WHERE order_ts >= '{{ data_interval_start }}'
  AND order_ts <  '{{ data_interval_end }}'
```

Note the asymmetry: `>=` on the left, `<` on the right. That asymmetry
*is* the convention. Writing `<=` on the right is the classic bug.

### Datasets — scheduling on data, not on the clock

Airflow 2.4 introduced **Datasets** (called *data-aware scheduling*,
originally "schedule datasets"). Instead of "run at 02:00", you say
"run when the upstream dataset has been updated".

```python
from airflow.datasets import Dataset

orders_dataset = Dataset("gs://demo-source-bucket/orders/")

with DAG(
    dag_id="etl_orders_to_bigquery",
    schedule=[orders_dataset],
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
) as dag:
    ...
```

The upstream DAG declares that it *updates* the dataset:

```python
with DAG(
    dag_id="ingest_orders",
    schedule="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
) as dag:
    ingest >> UpdateDatasetOperator(
        dataset_id="orders_dataset",
        dataset_update_outlets=[orders_dataset],
    )
```

When the ingest DAG completes and the dataset is updated, the downstream
DAG is triggered — with **no run yet until the data is actually there**.

Dataset advantages:

- No arbitrary cron time to tune.
- No wasted runs when the upstream is late (the "did it land yet?"
  problem is solved by construction).
- Dependencies on data, expressed as data.

Dataset limitations:

- The trigger fires on *dataset update*, not on *data correctness*.
- You still need a fallback: a dataset that never gets updated means the
  downstream never runs. Pair it with a sensor or a scheduled safety net.
- Dataset support in Composer depends on the Airflow version in your
  environment; Composer 2.x environments on Airflow 2.4+ support it.

### Scheduling summary

```text
                    ┌──────────────────────────────┐
   start_date ────▶ │  intervals eligible to run    │
                    │  [start_date, now]            │
                    └──────────────┬───────────────┘
                                   │
                       catchup?    │
                     ┌─────────────┴─────────────┐
                   False                       True
                     │                           │
        only the current                 create a run for every
        (latest) interval                missed interval too
                     │                           │
                     └─────────────┬─────────────┘
                                   │
                          schedule (cron/timedelta)
                                   │
                                   ▼
                          creates a DAG run per
                          interval, each with its
                          own logical date
                                   │
                          max_active_runs limits
                          how many overlap
```

---

## 🛠️ Hands-On

### Step 1: See the DAG's scheduling configuration

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

In the Airflow UI, the same four values are shown on the DAG's
**Info** tab: Schedule, Start Date, End Date, Catchup, Max Active Runs.

### Step 2: Compute the data interval yourself

The half-open convention is the thing to internalise, so compute it
directly rather than trusting a screenshot.

```bash
cd project/core
python3 -c "
from pipeline_logic import logical_date_window

start, end = logical_date_window('2026-01-15')
print('run date      :', '2026-01-15')
print('interval start:', start)
print('interval end  :', end, '(excluded)')
print()
start, end = logical_date_window('2026-01-15', data_interval_days=7)
print('weekly window :', start, '->', end)
start, end = logical_date_window('2026-01-15', include_end=True)
print('inclusive end :', start, '->', end)
"
```

Expected output:

```text
run date      : 2026-01-15
interval start: 2026-01-15
interval end  : 2026-01-16 (excluded)

weekly window : 2026-01-15 -> 2026-01-22
inclusive end : 2026-01-15 -> 2026-01-15
```

### Step 3: Use the interval to build a partition decorator

This is exactly what the real BigQuery DAG does with `ds_nodash`:

```bash
cd project/core
python3 -c "
from pipeline_logic import logical_date_window, partition_for_date

partition = partition_for_date('2026-01-15')
print('partition decorator:', partition)
start, end = logical_date_window('2026-01-15')
print()
print('The load must target exactly this partition:')
print(f'  analytics.orders_enriched\${partition}')
print()
print('And the filter that selects exactly this data:')
print(f\"  WHERE order_ts >= '{start}' AND order_ts < '{end}'\")
"
```

Expected output:

```text
partition decorator: 20260115

The load must target exactly this partition:
  analytics.orders_enriched$20260115

And the filter that selects exactly this data:
  WHERE order_ts >= '2026-01-15' AND order_ts < '2026-01-16'
```

That asymmetry — `>=` then `<` — is the entire point. A filter written
as `<= '2026-01-15'` double-counts the midnight row.

### Step 4: Run the DAG on a different logical date

The logical date is the run's identity. Change it and the run is
different — even though the sample data does not change.

```bash
python project/local_runner.py --dag etl_to_gcs --date 2026-02-01 --verbose
```

Expected output:

```text
▶ Running etl_to_gcs @ 2026-02-01

  Run summary for etl_to_gcs @ 2026-02-01
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

The numbers are identical — the sample CSV is fixed — but the **paths
change**, because they are templated on the logical date:

```text
would write gs://demo-target-bucket/etl_to_gcs/2026-02-01/summary.csv
```

Two runs of the same DAG at two logical dates are two different runs.
This is why a `scheduled__2026-01-15` run and a `manual__2026-01-15`
run are also two different runs.

### Step 5: Render a whole week of intervals

```bash
cd project/core
python3 -c "
from datetime import date, timedelta
from pipeline_logic import logical_date_window

d = date(2026, 1, 15)
for i in range(7):
    day = d + timedelta(days=i)
    start, end = logical_date_window(day.isoformat())
    print(f'run {day}  ->  [{start}, {end})')
"
```

Expected output:

```text
run 2026-01-15  ->  [2026-01-15, 2026-01-16)
run 2026-01-16  ->  [2026-01-16, 2026-01-17)
run 2026-01-17  ->  [2026-01-17, 2026-01-18)
run 2026-01-18  ->  [2026-01-18, 2026-01-19)
run 2026-01-19  ->  [2026-01-19, 2026-01-20)
run 2026-01-20  ->  [2026-01-20, 2026-01-21)
run 2026-01-21  ->  [2026-01-21, 2026-01-22)
```

Every instant is in exactly one interval. No gaps, no overlaps. That is
the property the half-open convention buys, and it is what makes
partitioned daily loads safe.

### Step 6: Use a `timedelta` schedule

The local runner's `DAG` class accepts any schedule string; the point
here is the concept, so exercise it directly:

```bash
cd project
python3 -c "
from datetime import timedelta
from local_runner import DAG, Task, run_dag

dag = DAG(
    'six_hourly',
    tasks=[Task('tick', lambda run, context: run.logical_date)],
    schedule=str(timedelta(hours=6)),
    start_date='2026-01-15',
)
print('schedule:', dag.schedule)
print('run     :', run_dag(dag, '2026-01-15').pull('tick'))
"
```

Expected output:

```text
schedule: 6:00:00
run     : 2026-01-15
```

And with a seven-day data interval — what the runner's `--interval-days`
flag drives:

```bash
python project/local_runner.py --dag etl_to_gcs --interval-days 7 --verbose 2>&1 | grep -E 'Run summary|@ 2026'
```

Expected output:

```text
  Run summary for etl_to_gcs @ 2026-01-15
```

The runner passes `data_interval_days` into the templating context, so
`{{ data_interval_end }}` becomes `2026-01-22T00:00:00+00:00` instead
of `2026-01-16T00:00:00+00:00`.

### Step 7: See the logical date in the rendered context

```bash
cd project/core
python3 -c "
from templating import build_context, render_template

ctx = build_context(dag_id='etl_to_gcs', task_id='aggregate', logical_date='2026-01-15')
for name in ['ds','ts','ds_nodash','prev_ds','next_ds','data_interval_start','data_interval_end','run_id']:
    print(f'{name:<20} {render_template(\"{{ \" + name + \" }}\", ctx)}')
"
```

Expected output:

```text
ds                   2026-01-15
ts                   2026-01-15T00:00:00+00:00
ds_nodash            20260115
prev_ds              2026-01-14
next_ds              2026-01-16
data_interval_start  2026-01-15T00:00:00+00:00
data_interval_end    2026-01-16T00:00:00+00:00
run_id               manual__2026-01-15T00:00:00+00:00
```

Every one of these is derived from the logical date. Nothing here
reflects wall-clock time.

---

## 🛠️ Common Errors and Fixes

### The DAG runs but processes the wrong day's data

Almost always an off-by-one on the interval. Check three things:

1. Is the filter half-open? `>= start AND < end` — never `<=`.
2. Are you using `ds` (the logical date) or `data_interval_start`? They
   agree for daily schedules; for non-daily schedules they may not.
3. Are you using `prev_ds` where you meant `ds`? `prev_ds` is the
   previous interval's start — a common cause of "the data is one day
   stale".

### The DAG is not running at all

In order of likelihood:

1. **The DAG is paused.** The UI shows a toggle in the top-left of the
   graph view. A paused DAG gets no new runs but *does* still get its
   existing runs scheduled.
2. **`catchup=False` and the start date is in the future.** With
   `catchup=False`, only the *latest* interval is created, and only if
   it has passed.
3. **The schedule is wrong.** `0 6 * * *` is 06:00 UTC. If you expected
   local time, you have a bug.
4. **`start_date` is in the future.**
5. **The DAG failed to parse** — check for the import-error marker.

### Hundreds of DAG runs appear at once

`catchup=True` with an old `start_date`. The scheduler created a run per
missed interval. Mitigations:

- **Pause the DAG immediately** in the UI. Runs already created are not
  destroyed, but new ones stop.
- **Delete the unwanted runs** in bulk from the DAG's **Runs** tab.
- **Set `catchup=False`** and use a deliberate backfill job instead.
- If the DAG writes to a fixed destination, verify idempotency *before*
  letting the remaining runs execute.

The lesson is not "catchup is forbidden" — it is "catchup is a decision
you make on purpose, in a backfill job, with an idempotent load".

### `Task is in the 'skipped' state` right after deployment

If you set `catchup=False` and the DAG was deployed *after* the
scheduled time, the run for the current interval may already exist (or
not). More commonly: a `BranchOperator` chose a different path. See
chapter 1.8.

### `TypeError: DAG.__init__() got an unexpected keyword argument 'schedule_interval'`

You are on Airflow 2.4+ and the parameter was removed in Airflow 3. Use
`schedule`:

```python
# OLD (deprecated since 2.4, removed in Airflow 3)
DAG(dag_id="x", schedule_interval="@daily", start_date=start_date)

# CURRENT
DAG(dag_id="x", schedule="@daily", start_date=start_date)
```

Conversely, on Airflow 2.0–2.3 `schedule` does not exist — use
`schedule_interval` there.

### `ValueError: Invalid timezone` / naive `start_date`

```python
# WRONG — interpreted in the server's local timezone
start_date=datetime(2026, 1, 1)

# RIGHT
start_date=datetime(2026, 1, 1, tzinfo=timezone.utc)
```

### `airflow.exceptions.DagNotFound: DAG: [x] not found` when triggering

You triggered a `dag_id` that is not registered. `airflow dags list` in
OSS, or the UI's DAG list in Composer, shows the registered ids.

### Cron fires at the wrong hour

Airflow cron is UTC. If you need a local-time schedule, either convert
the hour yourself (and document it) or use a `timedelta` schedule
anchored at a UTC time that maps to your local slot.

### The run appears twice for the same date

You have one `scheduled__` run and one `manual__` run for the same
logical date. Both execute. Both write. Check the **Runs** tab and look
at the run_id prefix.

---

## 💡 Production Notes

- **Always set `catchup=False` explicitly.** Rely on the default if you
  like, but make it a conscious choice in the file — it documents intent
  to the next reader.
- **Use UTC everywhere.** `tzinfo=timezone.utc` on every `start_date`,
  every cron (implicitly), and every comparison. A timezone bug in a
  daily pipeline is a bug that appears only on two days a year.
- **Align the schedule with the data's arrival, not with your
  preferences.** If the upstream lands at 03:00, schedule for 04:00, or
  use a Dataset.
- **Prefer `schedule` over `schedule_interval`.** The latter is
  deprecated from 2.4 and removed in Airflow 3.
- **Set `max_active_runs=1` for pipelines with a fixed destination.** It
  is the cheapest insurance against double-writes.
- **Make loads idempotent so backfills are safe.** The course's
  `dedup_key()` shows the principle — derive identity from the *data*,
  never from arrival time:

  ```python
  from pipeline_logic import dedup_key
  dedup_key("o00000042", "20260115")   # '20260115:o00000042'
  ```

- **Use `sla` measured from the data interval end**, not from the
  wall-clock start. `03_etl_bigquery.py` sets `DAG_SLA =
  timedelta(hours=2)`, and `sla_miss_callback` fires when the run has
  not completed two hours after the interval closed.
- **Do not backfill through `catchup`.** Use a backfill job with
  `max_active_runs` limited, so the backfill does not starve live runs.
- **Prefer Datasets when the dependency is real.** A scheduled trigger
  encodes a guess about arrival time; a Dataset encodes the dependency.

---

## 🔑 Key Takeaways

- The `DAG` object is **declarative configuration**: `schedule`,
  `start_date`, `catchup`, `max_active_runs`, `default_args`, `params`.
- `schedule` decides **when a run is created**; `start_date` is the
  **earliest eligible logical date**; `catchup` decides **whether missed
  intervals are created**; `max_active_runs` decides **how many overlap**.
- The schedule formats: **presets** (`@daily`), **cron** (UTC), **`timedelta`**, **Datasets** (Airflow 2.4+), and **`None`** for manual-only.
- **Logical date = the label of the data being processed**, not when the
  run happened. A 2026-01-15 run typically executes on 2026-01-16.
- The data interval is **half-open `[start, end)`** — `>=` on the left,
  `<` on the right. That asymmetry prevents double-counting the
  boundary row.
- **`catchup=True` is dangerous** because it creates runs for intervals
  whose data may not exist or may not load correctly. Default to
  `False`; backfill deliberately.
- `schedule_interval` is **deprecated since Airflow 2.4** and removed in
  Airflow 3. Use `schedule`.

---

## 📚 Practice Exercises

1. **Interval arithmetic.** For a DAG scheduled at `"30 2 * * *"` starting
   `2026-01-01`, list the logical dates of the first five runs and the
   data interval of each. Then use `logical_date_window()` to confirm
   each interval.

2. **The boundary bug.** Write the SQL filter that a naive developer
   would write for a daily load, and show which row it double-counts.
   Then write the correct one and prove the difference with
   `filter_rows_for_partition()` from `pipeline_logic.py`.

3. **Partition round-trip.** Use `partition_for_date()` and
   `filter_rows_for_partition()` to take the accepted orders and split
   them by partition. Confirm the partitions cover every accepted row
   exactly once.

4. **Catchup simulation.** With `catchup=True` and `start_date =
   2026-01-01`, how many runs would the scheduler create on 2026-03-01
   for an `@daily` DAG? Now explain what could go wrong, in three
   specific scenarios.

5. **max_active_runs reasoning.** Your DAG writes to
   `analytics.orders_enriched` partitioned by date. Why is
   `max_active_runs=1` the safe setting? What would go wrong at 3?
   Under what circumstance would 3 be correct?

6. **Dataset design.** Convert `03_etl_bigquery.py` to use a Dataset
   trigger instead of `@daily`. Identify the one failure mode a Dataset
   introduces that a cron schedule does not, and how you would mitigate
   it.

7. **Reflection.** A colleague says: "Our daily job runs at 02:00 and
   it processes yesterday's data — shouldn't the logical date be
   today?" Explain why the logical date is yesterday, and what would
   break if you changed it.

---

## 📖 Further Reading

- Airflow DAG runs — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html
- Airflow scheduling — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#scheduling
- Airflow data intervals — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html#data-interval
- Airflow templates reference (`ds`, `ts`, `prev_ds`, …) — https://airflow.apache.org/docs/apache-airflow/stable/templates-ref.html
- Airflow Datasets — https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/datasets.html
- Airflow 2.4 release notes (Datasets, `schedule` rename) — https://airflow.apache.org/docs/apache-airflow/stable/release_notes.html
- Google Cloud Composer scheduling — https://cloud.google.com/composer/docs/how-to/creating/dag-scheduling
