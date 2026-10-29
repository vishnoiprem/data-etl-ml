# Module 2 — DAGs, Scheduling & Templates

> **14 questions · Module 2 · DAG anatomy, schedules, logical date vs data interval, catchup, Jinja templating, variables/params/connections**

---

## DAG anatomy

### 1. What are the parameters on a `DAG` object, and which four of them do most production incidents actually involve?

**A DAG's behaviour comes entirely from its constructor.** The parameters that cause most incidents are `start_date`, `schedule`, `catchup`, and `max_active_runs` — in that order of how often they bite.

| Parameter | Meaning | Default | The trap |
|---|---|---|---|
| `dag_id` | unique identifier | required | **Duplicate `dag_id` = no DAG at all** in Airflow 2.x |
| `schedule` | when to create runs | `None` | `schedule_interval` is the deprecated old name |
| `start_date` | earliest logical date considered | required | **Must be timezone-aware** — naive means "server local time" |
| `catchup` | create runs for missed intervals | `False` | `True` can create 730 runs on deploy |
| `max_active_runs` | concurrent runs of this DAG | `16` | `1` for fixed-destination pipelines |
| `default_args` | default kwargs for every task | `{}` | `retries`/`retry_delay` cascade to everything |
| `params` | per-run parameters with defaults | `{}` | recorded in `dag_run.conf` — **not a secret store** |
| `sla` | time allowed after the data interval ends | `None` | measured from **interval end**, not run start |
| `dagrun_timeout` | max seconds a run may take | `None` | kills the whole run, including tasks |
| `tags` | UI labels | `[]` | your only search mechanism in the UI |

The course's `01_hello_world.py` shows the canonical set:

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
```

**The failure story:** a DAG was written with `start_date=datetime(2026, 1, 1)` — naive, no `tzinfo`. The Composer environment's Airflow config had a different local timezone from the developer's laptop. The DAG's first run landed on a logical date shifted by the offset, so its partition decorator (`20260115`) did not match the source file's date directory (`20260114`). The load found 0 rows and "succeeded". The fix was `tzinfo=timezone.utc` everywhere, and the rule became: **every datetime in a DAG file carries an explicit timezone**.

### 2. Explain `start_date` precisely. What does it *not* mean, and what happens if you change it later?

**`start_date` is the earliest logical date Airflow will consider.** It is not "when the DAG was created" and not "when the first run happens".

Three rules:

1. **It should be timezone-aware.** `datetime(2026, 1, 1, tzinfo=timezone.utc)`. A naive datetime is interpreted in the Airflow server's local timezone — which differs between your laptop, a self-hosted server, and Composer.
2. **It is a floor, not a trigger.** Setting it to `2026-01-01` does not create 20 runs for January. It says: *if* runs are to be created for dates on or after `2026-01-01`, this DAG is eligible.
3. **Lowering it retroactively creates history** — but only if `catchup=True`. With `catchup=False`, lowering `start_date` changes nothing except what a manual backfill is allowed to target.

The course's `dag_config.py` is explicit about the intent, and every DAG sets `start_date=datetime(2026, 1, 1, tzinfo=timezone.utc)` — deliberately early, not today's date.

**The failure story:** a team added a new DAG with `start_date=datetime(2024, 1, 1)` and `catchup=True` (copied from an old template). On deploy, the scheduler created **~730 DAG runs** for two years. Each created 4 task instances. The DAG read a partner API that only retains 90 days of history, so 640 of those runs failed instantly — burning 2,920 task-instance rows, saturating the API rate limit for the live run, and tripping the metadata DB. The fix: `catchup=False` by default, plus a structure test asserting it.

### 3. What schedule forms does Airflow 2.x accept, and which one is most commonly misunderstood?

**Five forms: presets, cron, `timedelta`, Datasets, and `None`.** The most misunderstood is cron, because of the timezone.

| Form | Example | Meaning |
|---|---|---|
| Preset | `"@daily"` | exactly `"0 0 * * *"` — midnight UTC |
| | `"@hourly"` | `"0 * * * *"` |
| | `"@weekly"` | `"0 0 * * 0"` — Sunday midnight |
| | `"@monthly"` | 1st of the month, midnight |
| | `"@reboot"` | once, when the scheduler starts |
| Cron | `"0 6 * * *"` | 06:00 **UTC** every day |
| `timedelta` | `timedelta(hours=6)` | every 6 hours from `start_date` |
| Dataset | `[orders_dataset]` | when the dataset is updated (Airflow 2.4+) |
| `None` | `None` | never scheduled; manual trigger only |

Two corrections to the usual wrong answers:

- **Cron is evaluated in UTC** by default in Airflow 2.x. `"0 6 * * *"` fires at 06:00 UTC, not 06:00 local. Composer does not change this. If you want 06:00 New York, you write `"0 10 * * *"` (or accept the DST bug and pin the offset).
- **`@daily` is not magic** — it is exactly `"0 0 * * *"`. Knowing that lets you write the cron you actually want instead of reaching for a preset.

The `timedelta` form is underused and worth knowing, because it changes what `prev_ds` means:

```python
DAG(
    dag_id="hourly_ingest",
    schedule=timedelta(hours=6),
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
)
```

With a `timedelta` schedule the logical date is still the *interval start*, but the interval itself is six hours wide.

**Version note:** **`schedule_interval` → `schedule`** in Airflow 2.4. `schedule_interval` still works but emits a `DeprecationWarning`; it was removed in Airflow 3. Use `schedule`. Conversely, on Airflow 2.0–2.3 `schedule` does not exist at all.

**The failure story:** a DAG was written with `schedule="0 6 * * *"` by a developer in a UTC+5:30 office, who assumed 06:00 local. The DAG actually fired at 00:30 UTC, which was 06:00 local — and the upstream source data for the previous day was not yet complete. The DAG ran on empty data every day for three weeks. The fix was to move to an explicit UTC cron plus a sensor that waits for the source file, not a later schedule.

### 4. `catchup=True` on a DAG with `start_date` two years ago. Walk me through exactly what happens when you deploy it.

**The scheduler creates ~730 DAG runs, each with its own task instances, and all of them become eligible to run immediately.**

The mechanism is the pair of columns the DAG processor writes: `next_dagrun` and `next_dagrun_create_after`. With `catchup=True`, the processor sets `next_dagrun_create_after` to the start of every missed interval back to `start_date`. The scheduler's step 2 then inserts a `dag_run` per interval, and step 3 inserts the task instances.

The reason it is dangerous is not the volume — it is that **historical data often does not exist in the form the pipeline expects**:

- A pipeline written in 2026 may reference a column added in 2026; backfilling to 2024 fails on every run.
- A pipeline reading a partner API may find the partner only retains 90 days of history.
- A pipeline with `WRITE_APPEND` and no partition scope will corrupt the target table 730 times over.

The correct default is `catchup=False` — which is why every DAG in this course sets it explicitly, and why the local runner's `DAG` class defaults to `catchup=False` too.

**When you do want a backfill, do it deliberately** with a backfill job (`airflow dags backfill` in OSS; the **Run → Backfill** button in Composer; `gcloud composer environments run backfill` from the CLI), not by flipping `catchup` and waiting.

**The failure story:** a team deployed a DAG with `catchup=True` and `start_date=datetime(2024, 1, 1)`. Within four minutes, 730 runs existed and the first ~200 started concurrently. The load task used `WRITE_APPEND` without a partition decorator. The revenue table's January 2024 total was **31× the correct value** by the time someone noticed, and the fix required manually deleting and rebuilding 24 months of partitions from a backup.

### 5. What is `max_active_runs`, when must it be `1`, and what breaks if you set it too high?

**`max_active_runs` caps how many runs of the same DAG may be in flight at once.** Set it to `1` when the pipeline writes to a **fixed destination** (one BigQuery table, one GCS prefix), reads a mutable source and must see a consistent snapshot, or is expensive enough that you want to serialise the cost.

Set it higher when runs are **independent** — each writes to its own date partition and reads its own date's data — or when you want to catch up quickly after an outage.

The failure mode of setting it too high is **interleaved writes**. Two runs of the same DAG for different logical dates both append to the same unpartitioned table, and the interleaving is nondeterministic: a downstream query filtered on `order_ts` sees rows from both runs, and a `MERGE` keyed on `order_id` can have run N overwrite run N+1's row for the same order (which happens when a customer reorders the same product id on consecutive days — exactly what the course's `dedup_key(order_id, partition)` is designed to prevent).

The companion knob is `max_active_tasks`, which caps concurrent tasks *across all runs* of the DAG. It is a blunt instrument; for cross-DAG concurrency control use a **pool**.

**The failure story:** a team set `max_active_runs=16` (the default) on a pipeline that appended to a single unpartitioned BigQuery table. During a backfill, 16 runs wrote concurrently. The month-end revenue query, which did a `GROUP BY region` over the whole table, produced a number **2.4× too high** — and the discrepancy was not constant, it varied by day, which made it look like a data-quality bug in the source rather than an orchestration bug. The fix was `max_active_runs=1` plus partition-scoped `WRITE_TRUNCATE`.

### 6. What exactly is a DAG run versus a task instance, and what are the run types you will see in `run_id`?

**A DAG run is one execution of the DAG — one row in `dag_run`, one logical date, one `run_id`.** A **task instance** is one (dag_run, task) pair — one row in `task_instance`. The DAG run's state is derived from its task instances' states.

The `run_id` encodes the run type, and this is what you read when debugging:

| `run_id` prefix | Type | Created by |
|---|---|---|
| `scheduled__2026-01-15T00:00:00+00:00` | scheduled | the scheduler loop |
| `manual__2026-01-15T00:00:00+00:00` | manual | a person, or `TriggerDagRunOperator` |
| `backfill__2026-01-15T00:00:00+00:00` | backfill | a backfill job |
| `dataset_triggered__...` | dataset | a Dataset update (Airflow 2.4+) |

Airflow 2.4+ renamed `execution_date` to `logical_date` everywhere and made the UI render it consistently; the `run_type` column on `dag_run` is the reliable way to distinguish a live miss from a backfill.

**The failure story:** an on-call engineer saw a red DAG, assumed the nightly run had failed, and re-triggered it manually. It failed again — for the same reason. The actual failing run was a **`backfill__`** run from two days earlier, which had been started by a colleague to repair a gap and had been red ever since. The manual re-run was a second, concurrent execution of the same logical date, and because the load was `WRITE_APPEND`, the partition ended up with **2× the rows**. The fix was `max_active_runs=1` and a rule: *never re-trigger manually until you check the `run_type` of the existing run.*

### 7. `logical_date` vs `execution_date` vs `data_interval_start`/`_end` vs wall-clock start. Which one goes in your SQL filter, and why?

**Use `data_interval_start` and `data_interval_end` in filters, and `logical_date` (i.e. `{{ ds }}`) as the partition decorator.** `execution_date` is the deprecated old name for `logical_date` and means exactly the same thing.

| Name | What it is | For the 2026-01-15 daily run |
|---|---|---|
| **Logical date** | the label on the run; the start of the data it processes | `2026-01-15T00:00:00+00:00` |
| **Execution date** | old name for logical date | same value |
| **Data interval** | `[logical_date, next_schedule)` | `[2026-01-15, 2026-01-16)` |
| **Wall-clock start** | when the scheduler actually created the run | `2026-01-16T00:05:00+00:00` |
| **End date** | when the run finished | varies |

The interval is **half-open**: `[start, end)`. A data warehouse filter must match that exactly, or a partition gets processed twice or not at all.

The course's `03_etl_bigquery.py` gets this right, and its docstring names the bug:

```sql
WHERE order_ts >= '{{ data_interval_start }}'
  AND order_ts <  '{{ data_interval_end }}'
```

```text
Airflow's data interval for the 2026-01-15 run is [2026-01-15, 2026-01-16)

so the filter is `order_ts >= '2026-01-15' AND order_ts < '2026-01-16'`.
A filter written as `<= '2026-01-15'` double-counts the midnight row, and
one written with a `BETWEEN` loads the boundary row into two days.
```

This off-by-one is the single most common bug in a daily Airflow pipeline, and it is invisible until the monthly totals are wrong.

The course's pure helper makes it testable without Airflow:

```python
from pipeline_logic import logical_date_window

logical_date_window("2026-01-15")
# ('2026-01-15', '2026-01-16')
```

**The failure story:** a daily load filtered with `order_ts BETWEEN '2026-01-15' AND '2026-01-16'`. The row at exactly `2026-01-16T00:00:00Z` was loaded into both the 15th's run and the 16th's run. The monthly revenue report was **0.8% high** — exactly one extra day out of 31, times the average midnight order. Nobody noticed for two months because 0.8% is within normal reporting variance. It was caught by a row-level audit that found 31 duplicate `(order_id, partition)` pairs.

---

## Jinja templating

### 8. What is `template_fields`, and what happens if you put `{{ ds }}` in an attribute that is not on that list?

**`template_fields` is the class-level declaration of which operator attributes Airflow renders with Jinja.** Each operator type lists its own:

```python
class BashOperator(BaseOperator):
    template_fields = ("bash_command", "env")

class BigQueryExecuteQueryOperator(BaseOperator):
    template_fields = ("sql", "impersonation_chain")

class BigQueryInsertJobOperator(BaseOperator):
    template_fields = ("configuration", "impersonation_chain")
```

If `{{ ds }}` appears in an attribute that is **not** in `template_fields`, it is **never rendered**. The task receives the literal string `"gs://bucket/{{ ds }}/summary.csv"` — braces and all. **Nothing errors.** This is one of the most common silent failures in Airflow, because the only evidence is a path with braces in it, and the error surfaces three layers away in a GCS call.

For a custom operator, declaring the fields is the entire mechanism:

```python
class SummaryOperator(BaseOperator):
    template_fields = ("bucket", "prefix")
```

`PythonOperator` adds `op_args`, `op_kwargs`, and `templates_dict` to the base list — which is why `templates_dict` works for values that are not operator arguments.

**The failure story:** a custom operator had `template_fields = ("path",)` but the team also set `template_fields_dict` incorrectly for one field. The rendered GCS path was `gs://bucket/{{ ds }}/summary.csv` literally. The task succeeded, the operator returned the path, and the *next* task's `gsutil cp` failed with `NoSuchKey: 'gs://bucket/{{ ds }}/summary.csv'` — an error that pointed at the wrong task entirely. The fix was a CI structure test asserting the rendered path has no `{{` in it.

### 9. When exactly does rendering happen, and what are the three consequences of that timing?

**Templates are rendered before the task's `execute` method is called.** The sequence is:

```text
1. Scheduler decides task X should run
2. Worker imports the DAG file
3. Worker builds the context for (dag, task, logical_date)
4. Worker renders every attribute in template_fields   ← HERE
5. Worker calls task.execute(context) with the rendered values
6. Task body runs
```

Three consequences:

**1. A template error fails the task before any work happens.** This is good — a broken template cannot half-write a partition.

**2. You cannot template a value the task itself computed.** If `execute` computes a value and wants to use it in another template, it is too late. Use XCom instead.

**3. `ti.xcom_pull()` inside a template is resolved at render time**, which is *after* the upstream task has finished (because the dependency has been satisfied). This is exactly how `03_etl_bigquery.py` gets the staging table name:

```python
"query": (
    "SELECT ... FROM `{{ ti.xcom_pull(task_ids='validate_and_stage', key='staging_table') }}` "
    "WHERE run_date = '{{ ds }}'"
),
```

Note the subtlety: the `xcom_pull` happens during *rendering*, and it works because the dependency edge (`stage >> load`) guarantees the upstream task has already pushed. A template that pulls from a task that is **not** an upstream dependency will pull `None` and render the literal string `"None"` into your SQL.

**The failure story:** a DAG's SQL read `FROM \`{{ ti.xcom_pull(task_ids='read_orders') }}\`` where `read_orders` was not an upstream dependency of the query task — it was two branches away. The pull returned `None`, the query became `FROM \`None\``, and BigQuery rejected it with:

```text
google.api_core.exceptions.BadRequest: 400 Syntax error: Unexpected keyword "None"
```

The error named BigQuery, not Airflow, so the team spent a day on BigQuery permissions. The fix was to add the missing dependency edge.

### 10. What is in the Jinja context, and which entries are commonly confused with each other?

**Airflow builds a fresh context per task, per DAG run.** The core entries:

| Name | Example | What it is |
|---|---|---|
| `ds` | `2026-01-15` | logical date as `YYYY-MM-DD` |
| `ts` | `2026-01-15T00:00:00+00:00` | logical date as a full timestamp |
| `ds_nodash` | `20260115` | logical date without dashes |
| `prev_ds` | `2026-01-14` | previous interval's start |
| `next_ds` | `2026-01-16` | next interval's start |
| `data_interval_start` | `2026-01-15T00:00:00+00:00` | interval start (inclusive) |
| `data_interval_end` | `2026-01-16T00:00:00+00:00` | interval end (**exclusive**) |
| `logical_date` | `2026-01-15T00:00:00+00:00` | the run's label |
| `run_id` | `scheduled__2026-01-15T00:00:00+00:00` | the run's identifier |
| `dag`, `task`, `ti` | objects | the DAG, the task, the task instance |
| `var`, `conn`, `params` | wrappers | Variables, Connections, DAG-run params |
| `macros` | library | `macros.ds_add()`, `macros.utcnow()` |

The confusion that matters: **`prev_ds` is one *schedule tick* back, not one day back.** For a `@daily` DAG they coincide. For a `timedelta(hours=6)` schedule, `prev_ds` is 6 hours earlier. A DAG that assumes "yesterday" by using `prev_ds` will silently be wrong the moment someone changes the schedule to hourly.

Similarly, **`data_interval_start` equals `ds` for most schedules but not all** — for a schedule with a non-trivial cadence, the interval start and the logical date can differ.

**The failure story:** a `timedelta(hours=6)` DAG used `{{ prev_ds }}` to fetch "yesterday's" file from GCS. `prev_ds` was 6 hours earlier, so the path resolved to a file that did not exist yet at that time, and the DAG silently loaded the *current* partial file via a wildcard. The report's numbers were 40% low for 3 days. The fix was `{{ data_interval_start.date() }}` (or the `macros` equivalent) for a day-granularity path.

### 11. What is the difference between `{{ var.value.x }}` and `{{ var.x }}`, and why does the course's `templating.py` return a `StrictUndefined` sentinel instead of raising?

**Both spellings work in Airflow 2.x** — `var.value.my_var` and `var.my_var` are equivalent — and both appear in real DAGs.

The `StrictUndefined` detail is the interesting part. The course's `templating.py` reimplements Airflow's rendering with plain Jinja2, and its `_VariableView.__getattr__` returns a `StrictUndefined` sentinel for a missing variable *rather than raising immediately*. The comment in the source explains exactly why:

> Jinja's `default` filter only works if the lookup *returns* something undefined — an exception raised here would bypass `default` entirely and fail the render. StrictUndefined still raises when the value is actually used, so a missing variable is still a hard error unless `| default(...)` is applied.

This is the mechanism behind the course's layering pattern:

```python
BUCKET = "{{ params.bucket | default(var.value.gcs_bucket) }}"
```

Read it right to left: a hard-coded default → a Variable override → a param override. The `default` filter only fires because the lookup returned an undefined *sentinel* rather than raising.

The same trick applies to `{{ var.value.x | default('analytics') }}` in a real DAG — and it is why a DAG can still parse and run in a dev environment where a Variable has not been set yet, instead of dying with `AirflowException: Could not find expected variables`.

**The failure story:** a team rewrote a DAG's templates to use `{{ var.value.bucket }}` with no default, and the DAG stopped appearing in the UI — because the template error occurred during the parse phase, not at run time. The parse error was `jinja2.exceptions.UndefinedError: 'dict object' has no attribute 'value'`, shown in the DAG file's detail view. The fix was to add `| default(...)` so the DAG degrades to a safe default and fails loudly only if the default is wrong.

### 12. Your DAG writes to `gs://{{ var.value.target_bucket }}/{{ dag.dag_id }}/{{ ds }}/summary.csv`. What is the size and shape of the rendered path, and what should be in the XCom instead?

**The rendered path is a ~60-byte string.** For the course's target:

```text
gs://demo-target-bucket/etl_to_gcs/2026-01-15/summary.csv
```

That is the *reference*, and it is what belongs in XCom — not the file contents. The rule is: **XCom carries the pointer, not the payload.**

```python
run.xcom.push("write_summary", "gcs_uri", target)
run.xcom.push("write_summary", "local_path", str(local_path))
```

The test the course gives: *could this value be written to a file, and would the file be bigger than a few kilobytes?* If yes, it does not belong in an XCom. A row count (`1245`), a partition name (`20260115`), a table name, a boolean, and a GCS URI are all good. The 1,245 accepted order dicts are not.

**The failure story:** a task pushed its full result — a list of 1,245 order dicts — through XCom. Roughly 100–200 KB pickled. The shared metadata DB slowed down, and the whole environment's DAGs started missing their scheduled start times. The fix was two lines: write to GCS, push the URI.

---

## Variables, params, connections

### 13. Variable vs param vs Connection — what is the decision procedure, and what is the security consequence of getting it wrong?

**Variable = differs per environment. param = differs per run. Connection = holds credentials.** The decision procedure:

```text
Is the value a credential (password, key, token, service-account JSON)?
  │
  └─ YES ─▶ Connection. Always. No exceptions.
  │
  └─ NO ─▶ Does it differ between RUNS of the same DAG?
            │
            ├─ YES ─▶ param (a backfill date, a "force full load" flag)
            │
            └─ NO  ─▶ Does it differ between ENVIRONMENTS (dev/prod)?
                      │
                      ├─ YES ─▶ Variable (bucket names, project IDs, thresholds)
                      │
                      └─ NO  ─▶ Put it in the DAG file as a constant.
```

That last branch matters: **not every value needs to be configurable.** A value that is always the same in every environment and every run is better as a named constant in `dag_config.py` than as a Variable someone can change in the UI at 2am. The course keeps `SAMPLE_DATE = "2026-01-15"` and `SAMPLE_ORDER_COUNT = 5000` as constants for exactly this reason.

**The security consequence of getting it wrong:**

- **Variables are stored in plaintext** in the metadata DB. They are visible in the Composer UI to anyone with Variable-read access, returned by the REST API, and written into task logs if you log them.
- **Params are recorded in the DAG run's `conf`** — visible in the UI's configuration tab and in run history, forever.
- **Connections** encrypt the `password` field with a Fernet key derived from `airflow.cfg`'s `fernet_key` (Google manages it in Composer) and the UI masks it.

Two important precision points: **only `password` is encrypted in Airflow 2.x** — the `extra` blob is **not** encrypted by default, so do not put a private key in `extra`; in Composer 2.x put service-account JSON in `extra` of a Composer-managed connection rather than in a hand-made one, and prefer the environment's attached service account.

The safe logging pattern from `02_templating_and_variables.py` shows the asymmetry: log `conn.host`, never `conn.password`.

**The failure story:** a team stored a service-account JSON key in a Variable named `gcp_key` because it was convenient. The Variable list page in Composer showed the full private key to every engineer with UI access, and the key was written to the metadata DB in the clear — meaning anyone with read access to the Cloud SQL instance, or a metadata-DB dump in a support bundle, had the key. The key was also in the Airflow metadata DB, which is backed up to GCS. Rotating it took a week of coordinated work. The fix was moving it to a Connection and then to the environment's attached service account, so no credential material existed in Airflow at all.

### 14. Give me the three-level layering pattern the course uses, and explain why the order is not arbitrary.

**The order is `params` → `Variable` → hard-coded default, and it is the reverse of the specificity of the thing that changes.**

```python
# dag_config.py
GCP_PROJECT_ID = "{{ var.value.gcp_project_id | default('') }}"
SOURCE_BUCKET  = "{{ var.value.source_bucket | default('') }}"
BQ_DATASET     = "{{ var.value.bq_dataset | default('analytics') }}"
FULL_LOAD_THRESHOLD = "{{ var.value.full_load_threshold | default(1000000) }}"
```

Read right to left: a **hard-coded default** that always works → a **Variable override** for environment-specific values → a **param override** for run-specific values. The Jinja `default` filter is the mechanism, and it only works because the `templating.py` lookup returns an undefined *sentinel* rather than raising (see Q11).

Why the order matters: the most specific wins. A param is the most specific (this one run), a Variable is next (this environment), the constant is the fallback. If you put the default first in the chain — `{{ var.value.x | default(params.x) }}` — a Variable would always beat a param, and a one-off override at trigger time would silently do nothing.

The course's `dag_config.py` states the rule explicitly:

```text
params      -> differs per RUN       (a backfill date, a flag)
Variables   -> differs per ENVIRONMENT (bucket names, project IDs)
Connections -> holds CREDENTIALS     (never put a password in a Variable)
DAG file    -> LOGIC and STRUCTURE
```

**When the alternative wins:** when a value must not be overridable at all, use a constant in `dag_config.py` and do not template it. A pipeline's *validation thresholds* (which reject reason codes exist, the currency rate table) are business rules; `CURRENCY_TO_EUR` in `pipeline_logic.py` is a frozen dict precisely so the expected outputs in the chapters stay correct. Making it a Variable would mean the course's asserted numbers could change under you.

**The failure story:** a team put the BigQuery dataset name in `params` so that a backfill could target a different dataset. A `params` value is recorded in `dag_run.conf` and *persists in the run history forever* — and the "different dataset" name was, in one case, a **customer-facing sandbox dataset** that was supposed to be empty. A scheduled run picked up the stale param through a `params` default in the DAG and wrote 1,245 production rows into the sandbox. The fix was moving the dataset name to a Variable (environment-scoped) and putting the *date* in params, which is what actually varies per run.

---

## Next module

→ [Module 3 — Tasks, XCom & Branching](03-tasks-xcom-and-branching.md)

---

## Related chapters

| Module section | Chapter |
|---|---|
| DAG anatomy (1–6) | [03-dags-and-scheduling](../chapters/03-dags-and-scheduling.md) |
| Jinja templating (7–12) | [05-templates-and-jinja](../chapters/05-templates-and-jinja.md) |
| Variables, params, connections (13–14) | [06-variables-params-and-connections](../chapters/06-variables-params-and-connections.md) |
| The data-interval helper | [01-what-is-orchestration-and-why-airflow](../chapters/01-what-is-orchestration-and-why-airflow.md) |
