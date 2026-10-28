# 1.5 — Templates and Jinja

> **Section 1 · Composer Fundamentals & Model · Lecture 1.5 · 8:30**

## 🎯 What you will learn

- How Airflow's Jinja templating works and exactly *when* rendering happens
- The template context: `ds`, `ts`, `prev_ds`, `data_interval_start/end`, `dag`, `task`, `ti`, and more
- `template_fields` — the mechanism that decides which attributes get rendered
- Why undefined variables fail loudly (and why that is a feature)
- Macros: `macros.ds_add()`, `macros.ds_format()`, `macros.utcnow()`
- The rendering timing trap: templates are rendered *before* the task body runs
- How to debug a template locally with the course's `templating.py`

---

## 🧠 Concept

### What templating is for

A DAG file is Python code that runs at parse time. But many values in a
DAG are only known at *run* time: the logical date, the bucket name, the
partition, the value another task computed.

Templating is how Airflow bridges that gap. You write a **string
containing Jinja syntax** in a place Airflow knows to render, and Airflow
substitutes the run-time values into it before the task executes.

```python
bash_command="gsutil cp gs://{{ var.value.source_bucket }}/{{ ds }}/orders.csv gs://{{ var.value.target_bucket }}/"
```

At parse time this is just a string. At run time it becomes:

```bash
gsutil cp gs://demo-source-bucket/2026-01-15/orders.csv gs://demo-target-bucket/
```

This is what lets **one DAG file serve every environment and every
date**.

### The context

The context is a dictionary of names available inside every template.
Airflow builds a fresh one per task, per DAG run.

| Name | Example value | What it is |
|---|---|---|
| `ds` | `2026-01-15` | logical date as `YYYY-MM-DD` |
| `ts` | `2026-01-15T00:00:00+00:00` | logical date as a full timestamp |
| `ds_nodash` | `20260115` | logical date without dashes |
| `prev_ds` | `2026-01-14` | previous interval's start |
| `next_ds` | `2026-01-16` | next interval's start |
| `prev_ds_nodash` | `20260114` | previous start, no dashes |
| `next_ds_nodash` | `20260116` | next start, no dashes |
| `data_interval_start` | `2026-01-15T00:00:00+00:00` | interval start (inclusive) |
| `data_interval_end` | `2026-01-16T00:00:00+00:00` | interval end (**exclusive**) |
| `logical_date` | `2026-01-15T00:00:00+00:00` | the run's label |
| `run_id` | `scheduled__2026-01-15T00:00:00+00:00` | the run's identifier |
| `dag` | `<DAG: etl_to_gcs>` | the DAG object |
| `task` | `<Task: aggregate>` | the task object |
| `ti` | `<TaskInstance: ...>` | the task instance |
| `task_instance` | same as `ti` | older alias |
| `var` | — | Airflow Variables |
| `conn` | — | Airflow Connections |
| `params` | — | DAG-run parameters |
| `macros` | — | the macro library |
| `var_json` / `conn_json` | — | the whole dict as JSON |

Note the `prev_ds` / `next_ds` / `data_interval_start` family. They are
not all the same:

- `prev_ds` is **one schedule tick back**, not one day back. For a
  `@daily` DAG they coincide. For a `timedelta(hours=6)` schedule,
  `prev_ds` is 6 hours earlier.
- `data_interval_start` is the *interval* start; for most schedules it
  equals `ds`, but for a schedule with a non-trivial cadence it may not.

The course's `build_context()` implements this exactly:

```python
from templating import build_context

context = build_context(dag_id="etl_to_gcs", logical_date="2026-01-15")
context["ds"]                 # '2026-01-15'
context["data_interval_end"]  # '2026-01-16T00:00:00+00:00'
```

### `template_fields` — the mechanism

Airflow does not render every string in your DAG. It renders only the
attributes a task declares as templatable.

```python
class BashOperator(BaseOperator):
    template_fields = ("bash_command", "env")
```

```python
class BigQueryExecuteQueryOperator(BaseOperator):
    template_fields = ("sql", "impersonation_chain")
```

```python
class BigQueryInsertJobOperator(BaseOperator):
    template_fields = ("configuration", "impersonation_chain")
```

This is a **class-level declaration**. Each operator type lists its own
templatable attributes. When Airflow runs a task, it walks
`template_fields`, renders each value, and replaces it with the rendered
string.

For a custom operator, this is the whole mechanism:

```python
class SummaryOperator(BaseOperator):
    template_fields = ("bucket", "prefix")
```

If `bucket` is not in `template_fields`, `{{ ds }}` inside it is
**never rendered** — the task receives the literal string
`"gs://bucket/{{ ds }}/summary.csv"`. This is one of the most common
silent failures in Airflow, because nothing errors; you just get a
path with braces in it.

`PythonOperator` adds `op_args`, `op_kwargs`, and `templates_dict` to
the base list.

### Rendering timing — the critical rule

**Templates are rendered before the task's `execute` method is called.**

```text
1. Scheduler decides task X should run
2. Worker imports the DAG file
3. Worker builds the context for (dag, task, logical_date)
4. Worker renders every attribute in template_fields   ← HERE
5. Worker calls task.execute(context) with the rendered values
6. Task body runs
```

This has three consequences that bite people.

**Consequence 1: a template error fails the task before any work
happens.** That is good — a broken template cannot half-write a
partition.

**Consequence 2: you cannot template a value computed by the task
itself.** If your `execute` method computes a value and then wants to
use it in another template, it is too late. Use XCom instead.

**Consequence 3: `ti.xcom_pull()` inside a template is resolved at
render time**, which is *after* the upstream task has finished (because
the dependency has been satisfied). This is exactly how
`03_etl_bigquery.py` gets the staging table name:

```python
"query": (
    "SELECT order_id, customer_id, order_ts, region, channel, "
    "currency, status, amount, product_id, "
    "CURRENT_TIMESTAMP() AS load_ts, "
    "'{{ ds }}' AS run_date "
    "FROM `{{ ti.xcom_pull(task_ids='validate_and_stage', key='staging_table') }}` "
    "WHERE run_date = '{{ ds }}'"
)
```

The template is rendered at step 4, the upstream task already succeeded
at that point, so the XCom is there to pull.

A subtlety: in Airflow 2.x, `ti.xcom_pull` inside a template **during
parsing** (i.e. at DAG-file import time) would fail — there is no run
yet. Templates are rendered at *execution* time, so this is safe. But
it does mean you must not call `xcom_pull` at DAG-file module scope.

### Undefined variables fail loudly

Airflow renders Jinja with `StrictUndefined`. An undefined name is a
**hard error**, not an empty string.

```text
jinja2.exceptions.UndefinedError: 'my_var' is undefined
```

Airflow wraps it:

```text
Task failed with exception
airflow.exceptions.AirflowException: jinja2.exceptions.UndefinedError: 'my_var' is undefined
```

This is deliberate. The alternative — rendering undefined as `""` —
would produce a task that runs against a path like
`gs:///2026-01-15/orders.csv` and fails much later, in a much more
confusing place. Failing at render time, before any side effect, is
strictly better.

The course's `templating.py` uses `StrictUndefined` for exactly this
reason, and its `render_template` wraps failures in
`TemplateRenderError`:

```python
from templating import render_template, TemplateRenderError

try:
    render_template("gs://{{ var.value.nope }}/x.csv", context)
except TemplateRenderError as exc:
    print(exc)          # failed to render template: 'gs://{{ var.value.nope }}/x.csv'
    print(type(exc.cause).__name__)  # UndefinedError
```

### The `default` filter — the escape hatch

Strictness is good until you need a fallback. Jinja's `default` filter
supplies one:

```python
"gs://{{ var.value.source_bucket | default('') }}/{{ ds }}/orders.csv"
```

If `source_bucket` is missing, you get an empty string instead of an
error. This is why `dag_config.py` uses `default()` on every Variable:

```python
GCP_PROJECT_ID = "{{ var.value.gcp_project_id | default('') }}"
SOURCE_BUCKET = "{{ var.value.source_bucket | default('') }}"
TARGET_BUCKET = "{{ var.value.target_bucket | default('') }}"
```

The pattern `hard-coded default → Variable override → param override`
appears there as:

```python
BUCKET = "{{ params.bucket | default(var.value.gcs_bucket) }}"
```

Note the nesting: a `params` value wins; otherwise the Variable; and
(though not written here) you could nest another `default()` for a
literal fallback.

**A warning about `default()`**: it converts a *configuration error* into
a *silent wrong value*. `default('')` on a bucket name produces
`gs:///2026-01-15/orders.csv` — a task that fails later with a
confusing GCS error, instead of failing immediately with "variable not
found". Use `default()` when a missing value is genuinely acceptable;
do not use it to silence a real misconfiguration.

### Macros

Airflow exposes a library of helper functions under `macros`.

| Macro | Returns |
|---|---|
| `macros.ds_add(ds, -1)` | the date N days before `ds` |
| `macros.ds_format(ds, '%Y-%m')` | `ds` reformatted |
| `macros.utcnow()` | the current UTC time |
| `macros.timestamp()` | the current UTC timestamp |
| `macros.datetime_format(dt, fmt)` | a datetime reformatted |
| `macros.airflow_version` | the Airflow version string |
| `macros.to_utc(dt)` | converts to UTC |
| `macros.weekday(ds)` | the day of the week |
| `macros.month(ds)` | the month number |

The course's `02_templating_and_variables.py` uses one:

```python
"echo 'yesterday+1 : {{ macros.ds_add(ds, 1) }}'; "
```

`macros.ds_add(ds, 1)` for `ds = 2026-01-15` gives `2026-01-16`.

Note that `macros` is **not** implemented in the course's teaching
`templating.py` — it models the date macros only through the context
values (`prev_ds`, `next_ds`). That is a deliberate simplification,
and the chapter flags it.

### Jinja features you will use

Beyond substitution, Jinja gives you:

```jinja
{# a comment #}

{% if var.value.environment == 'prod' %}
gs://prod-bucket/...
{% else %}
gs://dev-bucket/...
{% endif %}

{% for region in ['AMER', 'EMEA'] %}
--region={{ region }}
{% endfor %}
```

Airflow supports all of these inside templated fields. But remember:
**the rendered result is a string.** You cannot render a Python object.
`{% if %}` in a template produces a string branch, not a Python branch.

If you need real control flow over real data, that is Python, inside the
task's `execute` — not Jinja.

### Airflow's template search path

Airflow can load templates from files on the DAGs folder:

```python
PythonOperator(
    task_id="render_file",
    python_callable=render_file,
    template_ext=[".sql", ".txt"],
    templates_dict={"query": "sql/aggregate.sql"},
)
```

Airflow searches `templates/` relative to the DAG file, then the
configured `template_searchpath`. The rendered content is available in
the context as `templates_dict["query"]`.

This is useful for long SQL that would otherwise clutter the DAG file.
It also means an external SQL file becomes a deployable artefact — and
that a syntax error in it fails at render time.

---

## 🛠️ Hands-On

### Step 1: Build a context and render every core variable

The course's `templating.py` reimplements Airflow's rendering without
Airflow installed. Use it:

```bash
cd project/core
python3 -c "
from templating import build_context, render_template

ctx = build_context(dag_id='etl_to_gcs', task_id='render_paths', logical_date='2026-01-15')
names = ['ds','ts','ds_nodash','prev_ds','next_ds','data_interval_start','data_interval_end','logical_date','run_id']
for name in names:
    print(f'{name:<20} {render_template(\"{{ \" + name + \" }}\", ctx)}')
print()
print('dag.dag_id          ', render_template('{{ dag.dag_id }}', ctx))
print('task.task_id        ', render_template('{{ task.task_id }}', ctx))
print('ti.dag_id           ', render_template('{{ ti.dag_id }}', ctx))
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
logical_date         2026-01-15T00:00:00+00:00
run_id               manual__2026-01-15T00:00:00+00:00

dag.dag_id           etl_to_gcs
task.task_id         render_paths
ti.dag_id            etl_to_gcs
```

Everything derives from the logical date. Nothing reflects wall-clock
time.

### Step 2: Run the templating DAG

The `templating_paths` DAG renders every path the pipeline needs:

```bash
python project/local_runner.py --dag templating_paths --verbose
```

Expected output:

```text
INFO   ✓ read_orders            success
INFO       source     -> gs://demo-source-bucket/2026-01-15/orders.csv
INFO       target     -> gs://demo-target-bucket/templating_paths/2026-01-15/summary.csv
INFO       bigquery   -> analytics.orders_enriched
INFO       partition  -> 20260115
INFO       previous   -> gs://demo-source-bucket/2026-01-14/orders.csv
INFO   ✓ render_paths           success
INFO       accepted=1245 rejected=0
INFO   ✓ transform_orders       success
INFO   ✓ aggregate              success
```

Look at the template strings in `local_runner.py`'s `build_template_dag`
and match each rendered line to its template:

```python
paths = {
    "source": "gs://{{ var.value.source_bucket }}/{{ ds }}/orders.csv",
    "target": "gs://{{ var.value.target_bucket }}/{{ dag.dag_id }}/{{ ds }}/summary.csv",
    "bigquery": "{{ var.value.bq_dataset }}.{{ var.value.bq_table }}",
    "partition": "{{ ds_nodash }}",
    "previous": "gs://{{ var.value.source_bucket }}/{{ prev_ds }}/orders.csv",
}
```

### Step 3: Render with a different logical date

The templates are a *function of the logical date*. Change the date,
change the output:

```bash
python project/local_runner.py --dag templating_paths --date 2026-03-10 --verbose 2>&1 | grep -E 'source|target|partition|previous'
```

Expected output:

```text
INFO       source     -> gs://demo-source-bucket/2026-03-10/orders.csv
INFO       target     -> gs://demo-target-bucket/templating_paths/2026-03-10/summary.csv
INFO       partition  -> 20260310
INFO       previous   -> gs://demo-source-bucket/2026-03-09/orders.csv
```

No DAG code changed. This is the whole point of templating: **one DAG
file, every date.**

### Step 4: Override a Variable and watch the template change

```bash
python project/local_runner.py --dag templating_paths --vars '{"source_bucket":"my-real-bucket","target_bucket":"prod-bucket"}' --verbose 2>&1 | grep -E 'source|target|bigquery'
```

Expected output:

```text
INFO       source     -> gs://my-real-bucket/2026-01-15/orders.csv
INFO       target     -> gs://prod-bucket/templating_paths/2026-01-15/summary.csv
INFO       bigquery   -> analytics.orders_enriched
```

The `bq_dataset` / `bq_table` variables were not overridden, so they
kept their defaults from `DEFAULT_VARIABLES`.

### Step 5: Prove that undefined variables fail loudly

```bash
cd project/core
python3 -c "
from templating import build_context, render_template, TemplateRenderError

ctx = build_context(dag_id='etl_to_gcs', logical_date='2026-01-15')
try:
    render_template('gs://{{ var.value.source_bucket }}/{{ ds }}/orders.csv', ctx)
except TemplateRenderError as exc:
    print('FAILED:', exc)
    print('cause :', type(exc.cause).__name__, '-', exc.cause)
"
```

Expected output:

```text
FAILED: failed to render template: 'gs://{{ var.value.source_bucket }}/{{ ds }}/orders.csv'
cause : UndefinedError - "variable 'source_bucket' not found (available: none)" is undefined
```

The "available: none" list is the set of Variables this context was
built with — and here we passed no `variables=` mapping at all, so the
list is empty. The important part is the **exception type**:
`UndefinedError`, not an empty string.

Now with a variable present, and with `default`:

```bash
cd project/core
python3 -c "
from templating import build_context, render_template

ctx = build_context(dag_id='etl_to_gcs', logical_date='2026-01-15',
                    variables={'source_bucket': 'demo-source-bucket'})
print('present :', render_template('{{ var.value.source_bucket }}', ctx))
print('default :', render_template(\"{{ var.value.missing | default('fallback') }}\", ctx))
"
```

Expected output:

```text
present : demo-source-bucket
default : fallback
```

### Step 6: Build a context with a wider data interval

```bash
cd project/core
python3 -c "
from templating import build_context, render_template

ctx = build_context(dag_id='etl_to_gcs', logical_date='2026-01-15', data_interval_days=7)
print('ds                 ', render_template('{{ ds }}', ctx))
print('data_interval_start', render_template('{{ data_interval_start }}', ctx))
print('data_interval_end  ', render_template('{{ data_interval_end }}', ctx))
print()
print('filter:', render_template(\"order_ts >= '{{ data_interval_start }}' AND order_ts < '{{ data_interval_end }}'\", ctx))
"
```

Expected output:

```text
ds                  2026-01-15
data_interval_start 2026-01-15T00:00:00+00:00
data_interval_end   2026-01-22T00:00:00+00:00

filter: order_ts >= '2026-01-15T00:00:00+00:00' AND order_ts < '2026-01-22T00:00:00+00:00'
```

That filter is the half-open convention, straight out of the context.

### Step 7: Render several templates at once

`templating.py` has `render_all()` for rendering a set:

```bash
cd project/core
python3 -c "
from templating import build_context, render_all

ctx = build_context(dag_id='etl_to_gcs', logical_date='2026-01-15',
                    variables={'source_bucket': 'demo-source-bucket',
                               'target_bucket': 'demo-target-bucket',
                               'bq_dataset': 'analytics', 'bq_table': 'orders_enriched'})
paths = {
    'source': 'gs://{{ var.value.source_bucket }}/{{ ds }}/orders.csv',
    'target': 'gs://{{ var.value.target_bucket }}/{{ dag.dag_id }}/{{ ds }}/summary.csv',
    'bigquery': '{{ var.value.bq_dataset }}.{{ var.value.bq_table }}',
    'partition': '{{ ds_nodash }}',
}
for name, value in render_all(paths, ctx).items():
    print(f'{name:<10} {value}')
"
```

Expected output:

```text
source     gs://demo-source-bucket/2026-01-15/orders.csv
target     gs://demo-target-bucket/etl_to_gcs/2026-01-15/summary.csv
bigquery   analytics.orders_enriched
partition  20260115
```

### Step 8: Compare the two Variable spellings

Both spellings work, and you will see both in real DAGs:

```bash
cd project/core
python3 -c "
from templating import build_context, render_template

ctx = build_context(dag_id='x', logical_date='2026-01-15',
                    variables={'target_bucket': 'demo-target-bucket'})
print('var.value.target_bucket ->', render_template('{{ var.value.target_bucket }}', ctx))
print('var.target_bucket       ->', render_template('{{ var.target_bucket }}', ctx))
"
```

Expected output:

```text
var.value.target_bucket -> demo-target-bucket
var.target_bucket       -> demo-target-bucket
```

`var.value.x` is the canonical spelling (and the one that matches the
Python API, `Variable.get("x")`). `var.x` is the shorthand. Chapter 1.6
covers this in full.

---

## 🛠️ Common Errors and Fixes

### `jinja2.exceptions.UndefinedError: 'x' is undefined`

A name in the template is not in the context. Common causes:

1. A **missing Variable** — `{{ var.value.my_var }}` when `my_var` is not
   set.
2. A **typo** in the name.
3. A **missing macro** — `{{ macros.something }}` where the macro does not
   exist.
4. Using a context variable in a place that is **not** templated.

Airflow surfaces it as:

```text
Task failed with exception
airflow.exceptions.AirflowException: jinja2.exceptions.UndefinedError: 'x' is undefined
```

The fix depends on intent:

```python
# The variable is required — create it, or fail loudly. Correct.
"{{ var.value.required_bucket }}"

# The variable is optional — supply a fallback.
"{{ var.value.optional_bucket | default('') }}"
```

### The template was not rendered at all — the output contains `{{ }}`

The attribute is not in the operator's `template_fields`. This fails
**silently**, which is why it is dangerous.

```python
class SummaryOperator(BaseOperator):
    template_fields = ("bucket", "prefix")   # ← add the attribute here
```

Check the operator's class definition, not the instance.

### The template rendered, but with the wrong date

Almost always a **logical date vs wall clock** confusion:

- `{{ ds }}` — the logical date (the day of data).
- `{{ run_id }}` — includes the logical date.
- `{{ ts }}` — the logical date as a timestamp.

If you want "now", that is `{{ macros.utcnow() }}` — and using it in a
path means the path changes on every retry, which breaks idempotency.

### `TypeError: expected string or bytes-like object` on a rendered field

You templated a field that Airflow expects to be a dict or a list, and
rendering turned it into a string. Airflow's `render_template` returns a
string for every templated field; for dict fields it walks the nested
structure. If you are rendering a whole dict yourself, use
`{{ var_json.my_dict }}` or render the individual keys.

### The task failed but the error mentions `ti` or `task_instance` is undefined

You used `ti` in a field that is not templated, or in a Python callable
where you should use `context["ti"]`.

```python
# WRONG in a Python callable
def my_task(**context):
    x = ti.xcom_pull(...)          # NameError

# RIGHT
def my_task(**context):
    x = context["ti"].xcom_pull(...)
```

### The rendered value contains `{{ }}` inside a Jinja comment or a JSON body

If your SQL contains literal braces (JSON, a Jinja-looking string), you
must escape them or Jinja will try to evaluate them:

```jinja
{{ '{"key": "{{ ds }}"}' }}
```

or use a `{% raw %}` block.

### `TemplateRenderError: failed to render template` (the local module)

That is the course's wrapper, not Airflow's. The real cause is on
`.cause`:

```python
except TemplateRenderError as exc:
    print(type(exc.cause).__name__, exc.cause)
```

### `ValueError: No config file found` / `Cannot read the airflow.cfg`

Not a templating issue — an Airflow configuration issue. On Composer
this does not happen; the environment is pre-configured. Locally, set
`AIRFLOW_HOME` and run `airflow db init`.

---

## 💡 Production Notes

- **Always use `{{ ds }}` for data paths, never `{{ macros.utcnow() }}`.**
  A path built from "now" changes on every retry, so a retry writes to a
  different place and the original half-written output stays behind.
- **Use `default()` only for genuinely optional values.** It trades a
  loud configuration error for a silent wrong value.
- **Prefer `{{ var.value.x }}` over `{{ var.x }}`** for consistency with
  the Python API, even though both work.
- **Keep SQL in `template_fields` and put the interval filter in it** —
  never build the filter with Python string concatenation in `execute`.
  The templated version is visible in the UI's rendered view.
- **Use `{{ ti.xcom_pull(...) }}` in templates rather than pulling in
  Python** when the value is needed to *build* the task's input. The
  templated pull happens before execution and shows up in the UI's
  rendered view, which is exactly what you want when debugging.
- **Do not template on `{{ run_id }}` for destination paths.** Manual and
  scheduled runs of the same logical date have different run_ids and
  would write to different places.
- **In Composer, use the UI's "Rendered Templates" view** (Task
  Instance → Details) to see exactly what was rendered. This is the
  fastest way to debug a template.
- **Keep templates in `templates_dict` when there are many.** It keeps
  the DAG file readable and makes each rendered value individually
  inspectable.

---

## 🔑 Key Takeaways

- Templating substitutes **run-time values into strings** before the
  task executes, letting one DAG file serve every environment and date.
- The context provides `ds`, `ts`, `ds_nodash`, `prev_ds`, `next_ds`,
  `data_interval_start/end`, `logical_date`, `run_id`, `dag`, `task`,
  `ti`, plus `var`, `conn`, `params` and `macros`.
- **`template_fields` is the mechanism.** An attribute not listed is
  never rendered — and it fails *silently*.
- **Rendering happens before `execute`.** Template errors fail the task
  before any side effect; values computed by the task itself cannot be
  templated.
- **Undefined variables are a hard error** (`UndefinedError`), by
  design. Use `| default(...)` only for genuinely optional values.
- **Macros** (`macros.ds_add`, `macros.ds_format`, `macros.utcnow`) are
  helpers; `ds_add` is the one you will actually use.
- The rendered result is always a **string** — real control flow belongs
  in Python, inside `execute`.

---

## 📚 Practice Exercises

1. **Template inventory.** List every template variable used across the
   four DAG files in `project/dags/`. For each, say whether it comes
   from the run context, a Variable, a param, a Connection, or an XCom.

2. **Undefined hunt.** Write a script that walks every DAG file in
   `project/dags/`, extracts all `{{ ... }}` expressions, and lists the
   distinct names used. Then classify each as context / var / conn /
   params / macros. What would you need to do to make this check
   automatic in CI?

3. **Rendered paths.** For the logical date `2026-07-04`, render every
   path in the `templating_paths` DAG and verify each one contains the
   expected date and the expected bucket.

4. **The `default` trade-off.** Write two versions of a template — one
   with `| default('')` and one without — and explain precisely what
   each does when the Variable is missing. Which would you ship for a
   required bucket, and why?

5. **Interval filters.** Use `build_context` with `data_interval_days=7`
   and render the exact BigQuery `WHERE` clause the DAG should use. Now
   write the wrong version (using `<=`) and explain which row it
   double-counts.

6. **A custom templated operator.** Write a `SummaryOperator` with
   `template_fields = ("bucket", "prefix")` and an `execute` that calls
   `summarise_by_region()` and `render_summary_csv()`. Demonstrate that
   an attribute *not* in `template_fields` is left unrendered.

7. **Reflection.** Explain why Airflow renders templates *before* the
   task body runs rather than during it. What class of bug does that
   ordering prevent, and what does it cost you?

---

## 📖 Further Reading

- Airflow templates reference — https://airflow.apache.org/docs/apache-airflow/stable/templates-ref.html
- Airflow Jinja templating — https://airflow.apache.org/docs/apache-airflow/stable/templates.html
- Airflow macros — https://airflow.apache.org/docs/apache-airflow/stable/templates-ref.html#macros
- Airflow TaskFlow — https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html
- Jinja 2 documentation — https://jinja.palletsprojects.com/en/3.1.x/templates/
- Google Cloud Composer: managing DAGs — https://cloud.google.com/composer/docs/how-to/managing/creating
