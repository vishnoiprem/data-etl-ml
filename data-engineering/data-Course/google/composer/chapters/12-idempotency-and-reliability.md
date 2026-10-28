# 4.12 — Idempotency & Reliability

> **Section 4 · Advanced Orchestration · Lecture 4.12 · 7:30**

## 🎯 What you will learn

- What "idempotent" means for an Airflow task, and why the word means something different here than in HTTP
- Retry semantics: what a retry re-does, what it does *not* undo, and why at-least-once is a promise, not a bug
- The double-count failure story — how a harmless-looking retry silently corrupts a revenue table
- `WRITE_TRUNCATE` vs `WRITE_APPEND` in BigQuery, and how to pick with a partition decorator
- Deterministic task IDs: the one line of code that prevents an entire class of corruption
- `depends_on_past` and what it really guarantees
- How to make a DAG re-runnable, and how to make a backfill safe

---

## 🧠 Concept

### What idempotent means for a task

A task is **idempotent** if running it *N* times produces the same result as running it once.

That is the entire definition, and it is the property that makes Airflow's retry, backfill, and re-run features safe.

For an HTTP request, idempotency is about the *verb*: `GET` is idempotent, `POST` is not (unless it carries an idempotency key). For an Airflow task, the same idea applies — but the unit is the task, and the "verb" is whatever side effect the task's code performs.

| Task | Idempotent? | Why |
|---|---|---|
| `SELECT count(*) FROM raw.orders` | yes | reads only |
| `INSERT INTO orders_enriched SELECT ... ` | **no** | a second run adds the rows again |
| `MERGE INTO orders_enriched USING ... ` | yes | keyed upsert, second run is a no-op |
| `CREATE OR REPLACE TABLE summary AS SELECT ...` | yes | replaces |
| `BigQueryInsertJobOperator` with `WRITE_TRUNCATE` + partition decorator | yes | replaces the same partition |
| `BigQueryInsertJobOperator` with `WRITE_APPEND` | **no** | appends again |
| Writing to `gs://bucket/{{ ds }}/summary.csv` | yes | same path, overwritten |
| Writing to `gs://bucket/{{ run_id }}/summary.csv` | **no** | new path each time |
| `ti.xcom_push(key="count", value=n)` | yes | same key, overwritten |
| Sending an email | **no** | a second run sends a second email |
| Posting to a webhook | **no** | same |

**The test to apply to any Airflow task:** if this task fails halfway and Airflow retries it in five minutes, what is in the target? If the answer is "more than before", the task is not idempotent and you have a bug waiting for a bad day.

### Retry semantics

Airflow's retry model:

```python
DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}
```

- The task is attempted. On failure, it enters the `upstream_failed`... no — it enters the **`retry`** state, scheduled for `now + retry_delay`.
- On the next attempt, it runs again **from the beginning**. Airflow does not checkpoint inside your callable; it does not resume a partially-completed function.
- Each attempt gets a fresh `try_number`. `context["ti"].try_number` tells you which attempt you are on.
- After the final attempt fails, the task is `failed`, and downstream tasks become `upstream_failed`.

```text
attempt 1 ──fail──▶ wait 5 min ──▶ attempt 2 ──fail──▶ wait 5 min ──▶ attempt 3 ──fail──▶ task failed
                                                                                                   │
                                                                                    downstream: upstream_failed
```

**The critical asymmetry:**

> A retry re-executes the task's code. It does **not** undo what the task already did.

If your task wrote 800 of 1,000 rows to BigQuery and then failed, the retry writes all 1,000 rows again. Those 800 are now duplicated — unless the write is idempotent.

This is why `retries` is simultaneously the most valuable and the most dangerous parameter in Airflow. It turns transient failures into successes, and it turns non-idempotent tasks into corruption engines.

### At-least-once execution

The formal model:

> **Airflow guarantees at-least-once execution of a task instance, and offers no guarantee of exactly-once.**

Every mechanism that can cause a task to run twice:

| Mechanism | Why it runs twice |
|---|---|
| `retries` | The first attempt failed *after* the side effect but before the result was recorded |
| Worker pre-emption | The worker died mid-task; the task is requeued |
| KubernetesExecutor pod eviction | The pod was evicted; a new pod re-runs the task |
| Scheduler restart | The task was queued but the "running" state was lost |
| Manual re-run of a task | Obviously |
| `airflow tasks clear` + re-run | Obviously |
| Backfill overlapping a live run | Two runs of the same logical date |

And the honest truth about exactly-once: it is not achievable in general, because the side effect (a BigQuery load) and the state record (the Airflow metadata database) are **two different systems**. There is no transaction spanning both. You can get "effectively once" with an idempotent write; you cannot get "literally once" without a distributed transaction.

**Exactly-once is the wrong goal. Idempotency is the right one.**

```text
exactly-once:  "the side effect happened one time, guaranteed"      ← not achievable
idempotent:    "if the side effect happened three times, the result
                 is indistinguishable from it happening once"      ← achievable, and sufficient
```

### The double-count failure story

Here is the bug, in full, because it is the single most instructive failure in data engineering.

**The setup.** A daily ETL pipeline loads yesterday's orders into a BigQuery table:

```text
gs://source-bucket/2026-01-15/orders.csv
        │
        ▼
   validate + transform
        │
        ▼
   BigQuery: analytics.orders_enriched
```

**The code that looks right:**

```python
load = BigQueryInsertJobOperator(
    task_id="load_to_bigquery",
    configuration={
        "query": {
            "query": "SELECT ... FROM `analytics.orders_staging`",
            "destinationTable": {
                "projectId": "{{ var.value.gcp_project_id }}",
                "datasetId": "{{ params.target_dataset }}",
                "tableId": "{{ params.target_table }}",
            },
            "writeDisposition": "WRITE_APPEND",
            "createDisposition": "CREATE_IF_NEEDED",
        }
    },
    retries=3,
    retry_delay=timedelta(minutes=10),
)
```

**What happens.**

| Day | Event | Rows in table | Correct? |
|---|---|---|---|
| 1 Jan | First run succeeds | 1,245 | yes |
| 2 Jan | First run **times out** after the load completed | 2,490 | **no** — doubled |
| 2 Jan | Retry 1 appends again | 3,735 | **no** |
| 2 Jan | Retry 2 appends again | 4,980 | **no** |
| 2 Jan | Retry 3 succeeds, task marked success | 4,980 | **no** |

**Why it is so hard to catch.**

1. The task state is `success`. Nothing is red in the UI.
2. The row count is 4× the expected 1,245, and a row-count check that says "more than zero" passes.
3. The aggregation *still produces a number*, and that number is 4× the revenue for that day.
4. The corruption is **per-partition**. Today's dashboard (which reads yesterday's partition) is fine until you look back a week.
5. It surfaces weeks later, in a month-end close, as "revenue is up 40%".

**And this is the version that is even worse:**

```python
"writeDisposition": "WRITE_APPEND",
```

…with a query that filters on the *current* date rather than a fixed partition:

```sql
SELECT * FROM `analytics.orders_staging` WHERE order_ts >= '{{ data_interval_start }}'
```

If the staging table holds 30 days of data, every run appends 30 days' worth, and the table grows quadratically. The fix — filtering to a fixed partition — is a one-line change that prevents the *worst* version of the bug, but does not fix the retry-duplication version. You need both.

**The general rule:**

> **Any Airflow task that writes to a shared, cumulative destination must either (a) write to a partition derived deterministically from the data, or (b) be a keyed upsert.** Otherwise `retries` is a corruption feature.

### `WRITE_TRUNCATE` vs `WRITE_APPEND`

BigQuery's `writeDisposition` determines what happens to the destination when a load job runs.

| Disposition | Effect on the destination | Idempotent? |
|---|---|---|
| `WRITE_APPEND` | Adds rows to the table | **no** |
| `WRITE_TRUNCATE` | **Clears the whole table**, then writes | only if the query selects the whole table |
| `WRITE_EMPTY` | Writes into an empty table; fails if not empty | only in a special case |

**The key insight:** `WRITE_TRUNCATE` is only idempotent if it truncates *the same scope* that the query writes. That is why the partition decorator matters.

**Without a partition decorator** — truncating the entire table:

```python
"destinationTable": {
    "projectId": "{{ var.value.gcp_project_id }}",
    "datasetId": "{{ params.target_dataset }}",
    "tableId": "{{ params.target_table }}",
},
"writeDisposition": "WRITE_TRUNCATE",
```

A retry truncates and rewrites the whole table. Idempotent — but it also means the DAG can only ever load one day of data, and a backfill of 30 days would leave only the last day.

**With a partition decorator** — the correct pattern for a daily DAG:

```python
"destinationTable": {
    "projectId": "{{ var.value.gcp_project_id }}",
    "datasetId": "{{ params.target_dataset }}",
    "tableId": "{{ params.target_table }}",
    "partitionDecorator": "20260115",     # ← {{ ds_nodash }}
},
"writeDisposition": "WRITE_TRUNCATE",
```

Now `WRITE_TRUNCATE` clears only the `20260115` partition and rewrites it. A retry replaces the same partition with the same rows. A backfill of 30 days fills 30 partitions, each independently. And the other 29 days' data is untouched.

This is exactly what the course's `03_etl_bigquery.py` does, and the comment says why:

```python
# 3. Load the staged data into the target table. The write disposition
#    is WRITE_TRUNCATE against a partition decorator, which makes the
#    load idempotent — a retry replaces the partition instead of
#    appending to it. WRITE_APPEND here would double-count on every
#    retry.
```

**The decision table:**

| Situation | Write disposition | Idempotent? |
|---|---|---|
| Daily load into a partitioned table | `WRITE_TRUNCATE` + partition decorator | **yes** |
| Whole-table rebuild | `WRITE_TRUNCATE` | yes (whole table is the scope) |
| Streaming append of genuinely new rows | `WRITE_APPEND` | only if the rows are new |
| Upsert of possibly-changed rows | `MERGE` on a business key | yes |
| Full refresh of a small dimension table | `WRITE_TRUNCATE` | yes |

**The `MERGE` option**, when rows can *change* rather than merely arrive:

```sql
MERGE `{{ var.value.gcp_project_id }}.{{ params.target_dataset }}.{{ params.target_table }}` T
USING `{{ params.target_dataset }}.{{ params.target_table }}_staging` S
ON T.order_id = S.order_id AND T.run_date = S.run_date
WHEN MATCHED THEN
    UPDATE SET amount = S.amount, amount_eur = S.amount_eur, status = S.status
WHEN NOT MATCHED THEN
    INSERT (order_id, customer_id, order_ts, region, channel, currency, status, amount, amount_eur, product_id, run_date)
    VALUES (S.order_id, S.customer_id, S.order_ts, S.region, S.channel, S.currency, S.status, S.amount, S.amount_eur, S.product_id, S.run_date)
```

`MERGE` is idempotent by construction: running it twice against the same source produces the same table.

### Deterministic task IDs

This is the smallest and most under-used reliability technique in Airflow.

The problem: a task's identity in Airflow is `(dag_id, task_id, logical_date, map_index)`. If the *destination* of a task is derived from something that varies between attempts — a timestamp, a random ID, a UUID, `run_id` — then a retry writes somewhere new, and the original output is orphaned.

```python
# BAD — the path changes on every attempt
def write_summary(**context) -> str:
    """Write the summary to a run-specific path."""
    path = f"gs://bucket/summaries/{context['run_id']}/summary.csv"
    ...
```

```python
# GOOD — the path is derived from the data
def write_summary(**context) -> str:
    """Write the summary to a date-derived path."""
    path = f"gs://bucket/summaries/{context['ds']}/summary.csv"
    ...
```

**Deterministic task IDs go further.** They make the *task instance* identity stable, so a retry is literally the same logical operation.

```python
from airflow.utils.task_group import TaskGroup

with TaskGroup(group_id="region_20260115") as region_group:
    ...
```

More practically, deterministic IDs matter when you build a task ID out of a dynamic value:

```python
# BAD — the task_id depends on when the DAG was parsed
task_id = f"load_{datetime.now().strftime('%H%M%S')}"
```

```python
# GOOD — the task_id depends only on the data
task_id = f"load_{context['ds_nodash']}"     # or a templated field
```

Airflow 2.3+ supports **templated `task_id`** — but only for the `dag_id`/`task_id` fields that are in `template_fields`. In practice, the robust approach is to keep task IDs static and let the *data* be dynamic.

**The general principle:**

> **Every identifier that determines where a side effect lands must be a pure function of the logical date and the data — never of the attempt, the wall clock, or a random source.**

The course's `core/pipeline_logic.py` encodes this in `dedup_key`:

```python
def dedup_key(order_id: str, partition: str) -> str:
    """Return the deterministic identity of a row for idempotent loads.

    The identity must be derived from the data, never from arrival time.
    A load-time timestamp would make a retry produce *different* rows rather
    than the same rows, which defeats deduplication entirely.
    """
    return f"{partition}:{order_id}"
```

That function is the row-level version of the same rule.

### `depends_on_past`

```python
DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}
```

`depends_on_past=True` makes a task instance wait until the **previous run of the same task** succeeded. For a task with logical date `2026-01-15`, that means the run with logical date `2026-01-14` must have succeeded first.

**What it guarantees:**
- The task does not run if yesterday's version of itself failed.
- The pipeline processes data in order.

**What it does NOT guarantee:**
- It does not make the task idempotent.
- It does not prevent a *backfill* from racing a *live* run — both have the same logical dates, and `depends_on_past` only orders runs by logical date within the DAG's own history.
- It does not survive a task that is `cleared` and re-run.

**Where it helps:** a pipeline where each day depends on the previous day's output — a cumulative state, a running total, an incrementally-maintained dimension.

**Where it hurts:** a daily batch that reads an independent slice of data. For that, `depends_on_past=False` (the course's default) is correct, because it allows a backfill to run 30 days in parallel instead of serially.

**The `depends_on_past` + `max_active_runs` interaction.** With `depends_on_past=True` and `max_active_runs=1`, the runs are serialised by construction. With `max_active_runs=5`, five days can be in flight, and `depends_on_past` orders them.

**The dangerous combination:** `depends_on_past=True` on a task that *appends* to a cumulative table. Then a retry of day N re-appends day N's rows, and day N+1 (which is waiting on it) proceeds happily. The pipeline "works" and the table is corrupt.

### How to make a DAG re-runnable

A re-runnable DAG is one where clearing and re-running any task produces the same final state. There are four requirements.

**1. Every write is scoped to a deterministic destination.** Partitions, not appends. `WRITE_TRUNCATE` + partition decorator, or `MERGE` on a business key, or a path derived from `{{ ds }}`.

**2. Every read is scoped to the same interval.** The query's filter must match Airflow's half-open data interval exactly:

```sql
WHERE order_ts >= '{{ data_interval_start }}'
  AND order_ts <  '{{ data_interval_end }}'
```

The course's `03_etl_bigquery.py` aggregate task does exactly this, and the file's docstring explains the failure mode:

```text
Airflow's data interval for the 2026-01-15 run is [2026-01-15, 2026-01-16)

so the filter is `order_ts >= '2026-01-15' AND order_ts < '2026-01-16'`.
A filter written as `<= '2026-01-15'` double-counts the midnight row, and
one written with a `BETWEEN` loads the boundary row into two days.
```

**3. Intermediate state is either absent or reset.** If a task writes to a staging table, the staging table must be scoped to the run — otherwise a retry reads yesterday's staging data mixed with today's.

**4. No external side effects that are not idempotent.** Emails, webhooks, PagerDuty calls, and Slack messages all need a deduplication key.

```python
def notify(**context) -> None:
    """Send a notification, at most once per logical date.

    Args:
        context: The Airflow task context.
    """
    import json

    from google.cloud import storage

    client = storage.Client()
    bucket = client.bucket(context["var"].get("state_bucket", "YOUR_PROJECT_ID-airflow-state"))
    marker = bucket.blob(f"notified/{context['dag'].dag_id}/{context['ds']}")

    if marker.exists():
        # Already notified for this logical date — do not send again.
        return

    send_slack_message(context["params"].get("channel", "#data-alerts"))
    marker.upload_from_string(json.dumps({"run_id": context["run_id"]}))
```

The marker write is itself non-atomic with the notification, so there is a tiny race window — but for a daily pipeline it reduces the problem to "essentially never". For a high-frequency one, use a conditional insert with an existence precondition, which BigQuery and GCS both support.

### Backfill safety

A backfill is the ultimate stress test of idempotency: it re-runs the same logical dates, in a different order, at a different time, possibly while the live schedule is also running.

**The dangerous backfill scenario:**

```text
Live schedule fires the 2026-01-15 run at 02:00.
You backfill 2026-01-10 .. 2026-01-14 at 14:00.
The backfill's last day writes to the same partition the live run just wrote.
Or: the backfill's `MERGE` and the live run's `MERGE` interleave.
```

**The rules for a safe backfill:**

1. **Turn off the schedule** while backfilling, or set `max_active_runs=1` on the backfill and confirm the live run has finished.
2. **Backfill into the same partitioned destination.** Then `WRITE_TRUNCATE` per partition means each backfilled day replaces only its own partition. The live run's partition is untouched.
3. **Never backfill into a table that the live schedule also appends to without a partition scope.** This is the `WRITE_APPEND` catastrophe.
4. **Use `depends_on_past=False`** unless the pipeline genuinely accumulates state — otherwise the backfill is serialised and takes 30 days' worth of runtime.
5. **Backfill with `max_active_runs` low enough that the backfill does not starve the live schedule.**
6. **Know your idempotency story before you start.** "If I run this twice, what happens?" must have an answer.

Airflow's `airflow dags backfill` command (Airflow 2.x) and the UI's "Create backfill" both respect `max_active_runs` and the DAG's own settings. On Composer, use the UI's backfill feature or `gcloud composer environments run backfill`.

### A reliability checklist

Before you call a DAG "reliable", walk this list:

- [ ] Every write is scoped to a deterministic destination (partition or keyed upsert)
- [ ] Every read filter matches the half-open data interval exactly
- [ ] `retries > 0` is set only on tasks that are idempotent
- [ ] Every path/identifier is derived from `{{ ds }}` or the data, never from `run_id` or `now()`
- [ ] `depends_on_past` is `True` only where the pipeline genuinely accumulates
- [ ] The task's output row count is checked against an expected value
- [ ] A backfill of any date range produces the same result as 30 sequential runs
- [ ] External notifications are deduplicated

---

## 🛠️ Hands-On

### Step 1 — watch the corruption happen, safely, in a local simulation

Before writing the fix, reproduce the bug. We will do it against an in-memory list, using the course's real functions.

```bash
cd data-engineering/data-Course/google/composer
python3 - <<'PY'
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import transform_orders, summarise_by_region, render_summary_csv

lines = open("sample_data/orders.csv").read().splitlines()
accepted, rejected = transform_orders(lines)
summary = summarise_by_region(accepted)
print(render_summary_csv(summary))
PY
```

Expected output:

```text
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

Now simulate a `WRITE_APPEND` load that is retried after a late failure:

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import transform_orders, summarise_by_region

lines = open("sample_data/orders.csv").read().splitlines()
accepted, _ = transform_orders(lines)
summary = summarise_by_region(accepted)

def append_load(table: dict[str, float], region: str, bucket: dict) -> None:
    """Emulate a WRITE_APPEND load job for one region."""
    table[region] = table.get(region, 0.0) + bucket["revenue_eur"]

def truncate_load(table: dict[str, float], region: str, bucket: dict) -> None:
    """Emulate a WRITE_TRUNCATE load job scoped to one region."""
    table[region] = bucket["revenue_eur"]

for name, loader in (("WRITE_APPEND", append_load), ("WRITE_TRUNCATE (per-partition)", truncate_load)):
    table: dict[str, float] = {}
    for attempt in (1, 2, 3):          # three attempts: the task failed twice
        for region, bucket in sorted(summary.items()):
            loader(table, region, bucket)
    print(f"{name:<30} AMER revenue = {table['AMER']:.2f}  (correct: {summary['AMER']['revenue_eur']:.2f})")
PY
```

Expected output:

```text
WRITE_APPEND                    AMER revenue = 340776.57  (correct: 113592.19)
WRITE_TRUNCATE (per-partition)  AMER revenue = 113592.19  (correct: 113592.19)
```

The append version is **exactly 3×** the correct revenue — three attempts, three appends. And the task state would be `success`, because the third attempt succeeded.

### Step 2 — build the idempotent loader and prove it

```python
# project/core/idempotent_load.py
"""Idempotent load semantics, modelled without BigQuery.

The point of this module is that the *rule* — "a retry must not change
the destination" — is a pure decision, and can be tested exactly like
every other rule in this course.
"""
from __future__ import annotations

from typing import Iterable, Mapping


def apply_load(
    existing: Mapping[str, Mapping[str, float]],
    incoming: Mapping[str, Mapping[str, float]],
    *,
    mode: str = "truncate",
    partitions: Iterable[str] | None = None,
) -> dict[str, dict[str, float]]:
    """Apply a load to a table, honouring the write disposition.

    Args:
        existing: The current contents of the destination table.
        incoming: The rows the load job would write.
        mode: Either ``"append"`` or ``"truncate"``.
        partitions: The partitions the load touches. When given, a
            truncate is scoped to these partitions only, which is what
            makes a daily load idempotent.

    Returns:
        The new contents of the destination table.
    """
    table = {region: dict(bucket) for region, bucket in existing.items()}

    if mode == "append":
        for region, bucket in incoming.items():
            current = table.setdefault(region, {"order_count": 0.0, "revenue_eur": 0.0})
            current["order_count"] += bucket["order_count"]
            current["revenue_eur"] = round(current["revenue_eur"] + bucket["revenue_eur"], 2)
        return table

    if mode == "truncate":
        scope = set(partitions) if partitions is not None else set(incoming)
        for region in scope:
            if region in incoming:
                table[region] = dict(incoming[region])
            else:
                table.pop(region, None)
        return table

    raise ValueError(f"unknown write mode: {mode!r}")
```

Test it three times and show the result does not change:

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import transform_orders, summarise_by_region
from idempotent_load import apply_load

lines = open("sample_data/orders.csv").read().splitlines()
accepted, _ = transform_orders(lines)
summary = summarise_by_region(accepted)

print("mode                      after 1 load   after 2 loads  after 3 loads   idempotent?")
print("-" * 92)
for mode, partitions in (
    ("append", None),
    ("truncate", ["AMER", "APAC", "EMEA", "LATAM"]),
):
    table = {}
    results = []
    for _ in range(3):
        table = apply_load(table, summary, mode=mode, partitions=partitions)
        results.append(table["AMER"]["revenue_eur"])
    same = len(set(results)) == 1
    print(f"{mode:<25} {results[0]:>11.2f}   {results[1]:>12.2f}  {results[2]:>12.2f}   {same}")
PY
```

Expected output:

```text
mode                      after 1 load   after 2 loads  after 3 loads   idempotent?
----------------------------------------------------------------------------------------
append                       113592.19       227184.38       340776.57   False
truncate                     113592.19        113592.19        113592.19   True
```

### Step 3 — the deduplication key, in use

The course's `dedup_key` gives every row a stable identity. Let us use it to build a deduplicating load — the third option, for when rows can change rather than merely arrive.

```python
# project/core/dedup_load.py
"""Deduplicate rows by their deterministic key."""
from __future__ import annotations

from typing import Iterable, Mapping

from pipeline_logic import dedup_key


def dedup_rows(
    rows: Iterable[Mapping[str, object]],
    partition: str,
) -> list[dict[str, object]]:
    """Keep the last row for each business key.

    A row's identity is derived from the data (``partition:order_id``),
    never from when it arrived. That is what makes the deduplication
    work on a retry: the same input produces the same keys, and the
    same keys resolve to the same surviving row.

    Args:
        rows: The candidate rows.
        partition: The partition the rows belong to.

    Returns:
        The deduplicated rows, in first-seen order.
    """
    seen: dict[str, dict[str, object]] = {}
    order: list[str] = []

    for row in rows:
        key = dedup_key(str(row.get("order_id", "")), partition)
        if key not in seen:
            order.append(key)
        seen[key] = dict(row)

    return [seen[key] for key in order]
```

Test it — including the critical case of the *same* rows arriving twice:

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import transform_orders, dedup_key
from dedup_load import dedup_rows

lines = open("sample_data/orders.csv").read().splitlines()
accepted, _ = transform_orders(lines)

partition = "20260115"
print("dedup_key example:", dedup_key("o00000000", partition))

once = dedup_rows(accepted, partition)
twice = dedup_rows(accepted + accepted, partition)   # the retry scenario

print(f"accepted rows         : {len(accepted)}")
print(f"after 1 dedup         : {len(once)}")
print(f"after loading twice   : {len(twice)}")
print(f"identical?            : {once == twice}")
PY
```

Expected output:

```text
dedup_key example: 20260115:o00000000
accepted rows         : 1245
after 1 dedup         : 1245
after loading twice   : 1245
identical?            : True
```

The second load added nothing, because every row's key was already present. That is idempotency expressed at the row level.

### Step 4 — the deployable DAG, with the fix

```python
# project/dags/07_idempotent_load.py
"""
07_idempotent_load.py — a DAG that is safe to retry, re-run, and backfill.

Demonstrates:
  * `WRITE_TRUNCATE` with a partition decorator
  * `MERGE` for rows that can change
  * a deterministic destination path
  * a row-count assertion against the source
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryExecuteQueryOperator,
    BigQueryInsertJobOperator,
)

log = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def count_source_rows(**context) -> int:
    """Count the source rows for this run's partition.

    Args:
        context: The Airflow task context.

    Returns:
        The number of rows in the source partition.
    """
    import json

    from google.cloud import storage

    client = storage.Client()
    bucket_name = context["var"].get("source_bucket", "YOUR_SOURCE_BUCKET")
    blob = client.bucket(bucket_name).blob(f"{context['ds']}/orders.csv")
    count = sum(1 for _ in blob.open("r")) - 1   # minus the header
    log.info("source rows for %s: %d", context["ds"], count)
    return count


def verify_row_count(**context) -> None:
    """Fail the task if the loaded row count does not match the source.

    This is the check that catches a partially-applied load. It is the
    safety net behind the idempotent write disposition.

    Args:
        context: The Airflow task context.
    """
    from google.cloud import bigquery

    expected = int(context["ti"].xcom_pull(task_ids="count_source_rows") or 0)
    client = bigquery.Client()
    project = context["var"].get("gcp_project_id", "YOUR_PROJECT_ID")
    dataset = context["var"].get("bq_dataset", "analytics")
    table = context["var"].get("bq_table", "orders_enriched")
    partition = context["ds_nodash"]

    query = (
        f"SELECT COUNT(*) FROM `{project}.{dataset}.{table}` "
        f"WHERE DATE(_PARTITIONTIME) = DATE('{context['ds']}')"
    )
    actual = int(list(client.query(query).result())[0][0])
    log.info("expected=%d actual=%d", expected, actual)

    if actual != expected:
        raise ValueError(
            f"row count mismatch for partition {partition}: "
            f"expected {expected}, found {actual}"
        )


with DAG(
    dag_id="idempotent_load",
    description="A daily load that is safe to retry, re-run, and backfill.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["production", "bigquery", "reliability"],
) as dag:
    count = PythonOperator(
        task_id="count_source_rows",
        python_callable=count_source_rows,
    )

    # WRITE_TRUNCATE against a PARTITION decorator. A retry replaces
    # the same partition with the same rows. A backfill fills each
    # partition independently. WRITE_APPEND here would double-count on
    # every retry.
    load = BigQueryInsertJobOperator(
        task_id="load_partition",
        configuration={
            "query": {
                "query": (
                    "SELECT order_id, customer_id, order_ts, region, channel, "
                    "currency, status, amount, product_id, "
                    "'{{ ds }}' AS run_date "
                    "FROM `{{ var.value.gcp_project_id }}."
                    "{{ var.value.bq_dataset }}.{{ var.value.bq_table }}_staging` "
                    "WHERE run_date = '{{ ds }}'"
                ),
                "destinationTable": {
                    "projectId": "{{ var.value.gcp_project_id }}",
                    "datasetId": "{{ var.value.bq_dataset }}",
                    "tableId": "{{ var.value.bq_table }}",
                    "partitionDecorator": "{{ ds_nodash }}",   # ← deterministic scope
                },
                "writeDisposition": "WRITE_TRUNCATE",            # ← idempotent
                "createDisposition": "CREATE_IF_NEEDED",
            }
        },
        retries=3,
        retry_delay=timedelta(minutes=10),
    )

    verify = PythonOperator(
        task_id="verify_row_count",
        python_callable=verify_row_count,
    )

    count >> load >> verify
```

### Step 5 — verify the pipeline output is unchanged

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

Reliability changes are supposed to be invisible in the output. If the numbers moved, you changed the pipeline rather than made it safer.

### Step 6 — simulate a backfill and prove it is safe

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import transform_orders, summarise_by_region, partition_for_date

lines = open("sample_data/orders.csv").read().splitlines()
accepted, _ = transform_orders(lines)
summary = summarise_by_region(accepted)

# A partitioned table is keyed by (partition, region). A WRITE_TRUNCATE
# with a partitionDecorator replaces one partition's rows and leaves
# every other partition alone.
table: dict[tuple[str, str], dict] = {}

def load_partition(ds: str) -> None:
    """Write one day's data, scoped to its own partition."""
    part = partition_for_date(ds)
    for region, bucket in summary.items():
        table[(part, region)] = dict(bucket)   # truncate semantics: replace

# The live run for 2026-01-15, then a backfill of two earlier dates.
load_partition("2026-01-15")
load_partition("2026-01-13")
load_partition("2026-01-14")

def snapshot() -> dict:
    """Return a comparable view of the table."""
    return {k: dict(v) for k, v in table.items()}

after_first = snapshot()

# Re-run the backfill — a backfill that is run twice.
load_partition("2026-01-13")
load_partition("2026-01-14")

parts = sorted({p for p, _ in table})
print("partitions after backfill:", parts)
for part in parts:
    rows = sum(int(table[(part, r)]["order_count"]) for r in ("AMER","APAC","EMEA","LATAM"))
    print(f"  {part}: order_count={rows}")
print()
print("backfill twice == backfill once:", snapshot() == after_first)
PY
```

Expected output:

```text
partitions after backfill: ['20260113', '20260114', '20260115']
  20260113: order_count=1245
  20260114: order_count=1245
  20260115: order_count=1245

backfill twice == backfill once: True
```

Three partitions, each with 1,245 orders, and running the backfill again changed nothing.

---

## 🛠️ Common Errors and Fixes

### The revenue is 3× or 4× what it should be

**Cause:** a non-idempotent write combined with `retries`. The task appended on every attempt.

**Fix:** change `writeDisposition` to `WRITE_TRUNCATE` and add a `partitionDecorator` derived from `{{ ds_nodash }}`. Then repair the corrupted partitions by re-running the load for each affected logical date — the truncate will replace them.

**Prevention:** add the row-count verification task from step 4. It turns a silent corruption into a failed task.

### The task succeeded but the table has too many rows

**Cause:** exactly the above. A successful task state means the *last attempt* returned successfully. It says nothing about what the earlier attempts did.

**Fix:** never trust task state alone to mean "the data is right". Check the data.

### `ValueError: unknown write mode: 'upsert'`

**Cause (in the course's simulation):** the `apply_load` helper supports `append` and `truncate`. In BigQuery, an upsert is a `MERGE` *query*, not a `writeDisposition` — you cannot ask a load job to merge.

**Fix:** use `BigQueryExecuteQueryOperator` with a `MERGE` statement, as shown in the concept section.

### `WRITE_TRUNCATE` wiped yesterday's data

**Cause:** the `destinationTable` has no `partitionDecorator`, so the truncate cleared the *whole table* — including every other partition.

**Fix:** add `"partitionDecorator": "{{ ds_nodash }}"` to the `destinationTable` configuration. Then re-run the affected dates to restore them.

### The backfill and the live schedule collided

**Cause:** both wrote the same logical date concurrently. With `WRITE_APPEND`, the result is a doubled partition. With `WRITE_TRUNCATE` + partition decorator, the result is a race whose winner is whichever job finished last — both wrote the same rows, so the *data* is fine, but the *task states* are confusing.

**Fix:** before backfilling, check whether the live schedule has a run in flight for the dates you are about to backfill. Either wait for it, or turn the DAG's schedule off temporarily (`airflow dags pause` / the Composer UI).

### `depends_on_past=True` made the backfill take a month

**Cause:** `depends_on_past=True` forces each logical date to wait for the previous one, so a 30-day backfill runs serially.

**Fix:** set `depends_on_past=False` for tasks that read an independent slice of data. Keep it `True` only for tasks that genuinely accumulate state — and if they accumulate, make them idempotent too, because `depends_on_past` does not prevent a retry from double-appending.

### `Task is in the 'upstream_failed' state` after a retry storm

**Cause:** all retries were exhausted. The final attempt failed, so the task is `failed`, and every downstream task is `upstream_failed`.

**Fix:** read the *upstream* task's log — that is where the actual error is. `upstream_failed` is a consequence, not a cause. If the root cause is a transient outage that lasted longer than `retries × retry_delay`, increase the retry budget or use a longer backoff.

### The email went out three times

**Cause:** a non-idempotent external side effect. The task failed *after* sending but before recording success, and the retry sent again.

**Fix:** deduplicate with a marker (the pattern in step 2 of the concept section). In practice, make the *notification* a separate task whose own side effect is guarded, and set `retries=0` on it — a notification that fails should be retried by the alerting system, not by re-sending.

### `exactly-once` semantics were expected but `MERGE` still duplicated rows

**Cause:** the `MERGE`'s join key was not unique in the source. `MERGE` with multiple source rows matching one target row is an error in BigQuery; with a non-unique key you can still get unexpected results.

**Fix:** deduplicate the source first, using a deterministic key — the course's `dedup_key(order_id, partition)` — and only then `MERGE`. The `MERGE` guarantees idempotency *given* a deterministic source.

---

## 💡 Production Notes

- **Design every write to be idempotent before you add `retries`.** Retries on a non-idempotent task are a corruption feature with a delay.
- **At-least-once is the promise. Idempotency is the answer.** Do not chase exactly-once; there is no transaction spanning BigQuery and Airflow's metadata database.
- **`WRITE_TRUNCATE` + partition decorator is the default answer for a daily load.** It makes retries free, backfills independent, and repairs trivial.
- **Use `MERGE` when rows can change**, not just arrive. Deduplicate the source with a deterministic key first.
- **Derive every destination from the logical date.** `{{ ds }}`, `{{ ds_nodash }}`, `{{ data_interval_start }}`. Never from `run_id`, `now()`, or a UUID.
- **A `success` task state does not mean the data is right.** It means the last attempt returned. Add a row-count assertion and a value-range check.
- **The half-open interval filter is part of idempotency.** `>= data_interval_start AND < data_interval_end` — never `BETWEEN`, never `<= end`.
- **`depends_on_past` is about ordering, not about correctness.** It does not make a task safe to retry.
- **Backfills are a concurrency event.** Pause the DAG or confirm the live run has finished before you backfill the same dates.
- **Exclude catchup runs from compliance metrics** (chapter 11) — a backfill finishing after the deadline is a recovery, not a fresh miss.
- **Dedup your notifications.** Paging on-call three times for one incident is how alerts get ignored.

---

## 🔑 Key Takeaways

- **Idempotent = running the task N times has the same effect as running it once.** That is what makes retries, re-runs, and backfills safe.
- **Airflow guarantees at-least-once execution.** Exactly-once is not achievable across two systems; idempotency is the achievable substitute.
- **A retry re-executes your code; it does not undo what your code already did.** That is the entire source of the double-count bug.
- The double-count story: `WRITE_APPEND` + `retries=3` + a load that succeeded before the timeout = **exactly 3× the revenue, with a `success` task state**.
- **`WRITE_TRUNCATE` is idempotent only if it truncates the same scope it writes** — hence the partition decorator.
- **`WRITE_TRUNCATE` + `partitionDecorator: "{{ ds_nodash }}"`** is the default answer for a daily load. `MERGE` on a business key is the answer when rows can change.
- **Deterministic task and destination IDs** are derived from the logical date and the data — never from the attempt, the clock, or a random source. `dedup_key` is the row-level expression of this rule.
- **`depends_on_past` orders runs; it does not make a task idempotent** and does not prevent a backfill from racing a live run.
- **A successful task is not proof of correct data.** Assert the row count against the source.

---

## 📚 Practice Exercises

1. **Prove the append bug arithmetic.** The course's sample yields 1,245 accepted orders and AMER revenue of 113,592.19. Write a script that applies a `WRITE_APPEND` load three times and an idempotent `WRITE_TRUNCATE`-per-partition load three times, and print the AMER revenue after each. Then explain, in terms of Airflow's state machine, why the task state after the third attempt is `success` in the append case. *Expected answer:* append gives 113,592.19, 227,184.38, 340,776.57; truncate gives 113,592.19 three times. The task state is `success` because Airflow records the *outcome of the final attempt* — the earlier attempts' side effects are invisible to the state machine, because the side effect happened in BigQuery and the state lives in Airflow's metadata database.

2. **Design a partitioned table and prove backfill safety.** Write the BigQuery DDL for a partitioned `orders_enriched` table (partitioned by `order_ts`, clustered by `region`), plus the `BigQueryInsertJobOperator` configuration that loads one day idempotently. Then describe exactly what happens when you backfill `2026-01-10` through `2026-01-20` while the live schedule is running, under (a) `WRITE_TRUNCATE` + partition decorator and (b) `WRITE_APPEND`. *Expected answer:* (a) each date's load truncates and rewrites only its own partition, so a backfill and a live run touching the same date write identical data — the final state is correct whichever finishes last, though the two task runs may report different states; (b) the partition for any date touched by both the backfill and a live run is doubled, and a backfill that overlaps a live schedule will silently double-count.

3. **Find the non-deterministic identifiers in a DAG.** Take `project/dags/03_etl_bigquery.py` and `04_branching_and_xcom.py` and list every identifier derived from something other than the logical date or the data — `run_id`, `now()`, UUIDs, wall-clock timestamps. For each, state whether it is a correctness problem, and if so produce a fix. *Expected answer:* `04_branching_and_xcom.py` pushes `{"parent_run_id": "{{ run_id }}"}` as the `conf` to a `TriggerDagRunOperator` — that is a *reference*, not a destination, so it is not a correctness problem; but any `gs://bucket/{{ run_id }}/...` path would be. `03_etl_bigquery.py` uses `CURRENT_TIMESTAMP() AS load_ts` as a *column value*, which is non-deterministic but harmless (it does not affect deduplication, since the business key is `order_id` + partition) — though it does make the table's contents differ between a fresh run and a retry, which matters if you have a `MERGE` that compares `load_ts`.

4. **Build a deduplicating loader and test it.** Using `dedup_key` and `dedup_rows` from the hands-on, write a loader that accepts a list of order dicts and returns the deduplicated set for a given partition. Test it with (a) the sample data loaded once, (b) the sample data loaded twice, (c) the sample data with one row's `amount` changed between the two loads. Explain what case (c) tells you about deduplication versus upsert. *Expected answer:* (a) 1,245 rows; (b) 1,245 rows, identical to (a); (c) 1,245 rows with the changed amount retained, because the "last one wins" policy replaces the earlier row for the same key. Case (c) shows deduplication is not the same as upsert: deduplication drops the earlier version entirely, while a `MERGE` upsert updates the existing row's non-key columns and keeps the row's identity. For a warehouse where rows change, use `MERGE`; for a stream where duplicates are pure noise, use deduplication.

5. **Audit the course's DAGs against the reliability checklist.** Walk every task in `project/dags/01_hello_world.py` through `03_etl_bigquery.py` and `04_branching_and_xcom.py` and mark each as idempotent or not, with a one-line justification. Then identify the single highest-risk task in the set and propose a concrete change. *Expected answer:* `01_hello_world.py` — both tasks are idempotent (a log line and an `echo`). `02_templating_and_variables.py` — idempotent (it only reads config and logs). `03_etl_bigquery.py` — `check_source_exists` is idempotent (a `gsutil ls`); `validate_and_stage` is idempotent (it returns a table name); `load_to_bigquery` **is idempotent as written**, because it uses `WRITE_TRUNCATE` — but only because its `destinationTable` has no `partitionDecorator`, which means it truncates the *whole* table on every run and can only ever hold one day. The highest-risk task is therefore `load_to_bigquery`: it is correct for a single-day table and catastrophic for a historical table, and the fix is to add `"partitionDecorator": "{{ ds_nodash }}"`.

6. **Design the recovery procedure for a corrupted partition.** Suppose you discover that the `20260115` partition of `orders_enriched` has 3,735 rows instead of 1,245, and the DAG has since run for 5 more days. Write the recovery procedure, step by step, including how you avoid making the corruption worse while you fix it, and how you detect the same bug elsewhere. *Expected answer:* (1) Stop the DAG (`airflow dags pause`) to stop new appends; (2) confirm the source row count for that date — 1,245 accepted orders — so you know the target; (3) re-run the load task for logical date `2026-01-15` after fixing the write disposition to `WRITE_TRUNCATE` + `partitionDecorator: "20260115"`, which replaces the partition rather than adding to it; (4) verify the row count equals 1,245; (5) unpause the DAG; (6) search every other partition for the same anomaly — a partition whose row count is a multiple of the source count for its date is a candidate for the same bug; (7) add the row-count verification task so the class of bug cannot recur silently; (8) add an alert on "partition row count is not equal to the source row count", because the failure mode is silent.

---

## 📖 Further Reading

- Airflow: task retries and dependencies — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html
- Airflow: `depends_on_past` and `wait_for_downstream` — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#task-dependencies
- Airflow: backfill — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/backfill.html
- BigQuery: write dispositions — https://cloud.google.com/bigquery/docs/writing-data
- BigQuery: partitioned tables and partition decorators — https://cloud.google.com/bigquery/docs/partitioned-tables
- BigQuery: `MERGE` statements — https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax#merge_statement
- BigQuery: loading data with an error — https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-csv
- Google Cloud Composer: managing DAGs and triggers — https://cloud.google.com/composer/docs/how-to/managing/creating
- Google Cloud: data engineering reliability patterns — https://cloud.google.com/architecture/data-engineering-practices
