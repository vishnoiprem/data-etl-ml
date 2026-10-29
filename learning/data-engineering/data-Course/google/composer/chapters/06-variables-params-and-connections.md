# 1.6 — Variables, Params, and Connections

> **Section 1 · Composer Fundamentals & Model · Lecture 1.6 · 8:30**

## 🎯 What you will learn

- The three configuration mechanisms Airflow offers — Variable, param, Connection — and how they differ
- A decision procedure for which one to use
- The security model: why credentials belong in Connections and never in Variables
- The layering pattern: hard-coded default → Variable → param
- How to read and write each one from Python and from the Composer UI
- The two Variable template spellings: `{{ var.value.x }}` and `{{ var.x }}`
- How Airflow encrypts Connection secrets, and what is *not* protected

---

## 🧠 Concept

### Three mechanisms, three jobs

Airflow gives you three ways to keep configuration out of your DAG
files. They are not interchangeable, and confusing them causes real
problems.

| | **Variable** | **param** | **Connection** |
|---|---|---|---|
| **Scope** | environment-wide | per DAG (or per task) | environment-wide |
| **Set by** | admin, in the UI or code | the person triggering the run | admin, in the UI or code |
| **Lifecycle** | long-lived | per-run | long-lived |
| **Varies by** | environment | run | environment |
| **Can hold secrets** | **no** (plaintext in the DB) | no (recorded in the run's conf) | **yes** (encrypted) |
| **Typical content** | bucket names, project IDs, thresholds | a date, a flag, an override | passwords, API keys, service-account JSON |
| **Read in code** | `Variable.get("x")` | `context["params"]["x"]` | `BaseHook.get_connection("x")` |
| **Read in a template** | `{{ var.value.x }}` | `{{ params.x }}` | `{{ conn.x.host }}` |

The one-line version:

- **Variable** = *this value is different in prod than in dev.*
- **param** = *this value is different in this run than in other runs.*
- **Connection** = *this value is a secret.*

### When to use which

Use this decision procedure:

```text
Is the value a credential (password, key, token, service-account JSON)?
  │
  └─ YES ─▶ Connection. Always. No exceptions.
  │
  └─ NO ─▶ Does it differ between RUNS of the same DAG?
            │
            ├─ YES ─▶ param
            │         (a backfill date, a "force full load" flag,
            │          an ad-hoc region filter)
            │
            └─ NO  ─▶ Does it differ between ENVIRONMENTS (dev/prod)?
                      │
                      ├─ YES ─▶ Variable
                      │         (bucket names, project IDs, dataset
                      │          names, thresholds, owner email)
                      │
                      └─ NO  ─▶ Put it in the DAG file as a constant.
                                It is part of the logic.
```

The final branch matters. **Not every value needs to be
configurable.** A value that is always the same in every environment and
every run is better as a named constant in `dag_config.py` than as a
Variable that someone can change in the UI at 2am.

```python
# dag_config.py — a constant, not a Variable
SAMPLE_DATE = "2026-01-15"
SAMPLE_ORDER_COUNT = 5000
```

### The security model

This is the part that gets people into security incidents.

**Variables are stored in plaintext in the metadata database.** They are
visible in the Composer UI to any user with the Variable-read role, they
appear in the **Variables** list page, and they are returned by the REST
API to anyone who can read them. They are also written into task logs
if you log them.

**Connections are stored with their secret fields encrypted** using a
Fernet key derived from the `fernet_key` in `airflow.cfg` (in Composer,
Google manages this). The `password` field and the sensitive parts of
`extra` are encrypted at rest. The UI masks them.

The rule, stated once:

> **Never put a password, API key, service-account JSON, or any other
> credential in a Variable or a param.**

The reasons:

1. **Variables are readable in plaintext** by anyone with UI access, and
   they are written to the metadata DB in the clear.
2. **Params are recorded in the DAG run's `conf`** and are visible in
   the UI's configuration tab, and in the run history, forever.
3. **Connections are the only mechanism Airflow gives you for
   secrets**, and they integrate with the provider operators — the
   BigQuery operator reads the service-account JSON from a Connection's
   `extra`, not from a Variable.

A Variable is not "encrypted but visible in the UI". It is plaintext.
Treat it as configuration, not as a secret store.

The course's `02_templating_and_variables.py` demonstrates the safe
pattern:

```python
def report_environment(**context) -> dict:
    ti = context["ti"]
    log.info("dag_id        : %s", context["dag"].dag_id)
    log.info("logical_date : %s", context["logical_date"])
    log.info("params       : %s", context["params"])

    # A Variable is environment-level configuration. Use `default()` so the
    # DAG still parses in an environment where it has not been set.
    owner = context["var"].get("pipeline_owner", "unassigned")
    log.info("owner (var)  : %s", owner)

    # A Connection holds credentials. Reading the host is safe; reading a
    # password into a log is not.
    try:
        conn = context["conn"].get("http_orders_api")
        if conn is not None:
            log.info("api host     : %s", conn.host)
    except Exception as exc:
        log.warning("no http_orders_api connection: %s", exc)

    return {"dag_id": context["dag"].dag_id, "owner": owner}
```

Note the asymmetry in that last block: it logs `conn.host` (not secret)
and never logs `conn.password`.

### The layering pattern

The course's `dag_config.py` states the rule explicitly:

```text
params      -> differs per RUN       (a backfill date, a flag)
Variables   -> differs per ENVIRONMENT (bucket names, project IDs)
Connections -> holds CREDENTIALS     (never put a password in a Variable)
DAG file    -> LOGIC and STRUCTURE
```

And it implements a three-level layering:

```python
# hard-coded default  →  Variable override  →  param override
BUCKET = "{{ params.bucket | default(var.value.gcs_bucket) }}"
```

Read it right to left:

1. If `params.bucket` is set, use it.
2. Otherwise, fall back to `var.value.gcs_bucket`.
3. (In the full form, a final `| default('literal')` would give a
   hard-coded fallback.)

`dag_config.py` uses the simpler two-level form on most values:

```python
GCP_PROJECT_ID = "{{ var.value.gcp_project_id | default('') }}"
SOURCE_BUCKET = "{{ var.value.source_bucket | default('') }}"
TARGET_BUCKET = "{{ var.value.target_bucket | default('') }}"
BQ_DATASET = "{{ var.value.bq_dataset | default('analytics') }}"
BQ_TABLE = "{{ var.value.bq_table | default('orders_enriched') }}"
FULL_LOAD_THRESHOLD = "{{ var.value.full_load_threshold | default(1000000) }}"
```

The `default()` here means **the DAG parses and runs in an environment
where the Variable has not been set yet** — which is exactly what you
want when a new environment is being bootstrapped. The failure surfaces
as "bucket is empty", not as "the DAG does not exist".

The ordering matters, and it is a deliberate design choice:

```text
param  ──(most specific, per run)──▶  wins
  │
Variable ──(per environment)────────▶  fallback
  │
DAG constant ──(least specific)─────▶  final fallback
```

A param always beats a Variable, because a param is the more specific
decision — it was made for *this run*.

### The two Variable spellings

Both of these work:

```jinja
{{ var.value.target_bucket }}
{{ var.target_bucket }}
```

The canonical form is `var.value.x`. It matches the Python API
(`Variable.get("x")`) and it is what the Airflow documentation uses. The
short form `var.x` is a convenience that Airflow also supports.

**Use `var.value.x` in new code.** It is unambiguous, it is the
documented spelling, and when you see `var.x` in an old DAG you know
immediately that the file predates current conventions.

### Connection anatomy

A Connection has a fixed set of fields plus a JSON `extra` blob.

| Field | Holds |
|---|---|
| `conn_id` | the unique name you reference it by |
| `type` | `bigquery`, `gcpbigquery`, `http`, `postgres`, … |
| `description` | free text |
| `host` | hostname |
| `login` | username |
| `password` | password (**encrypted**) |
| `schema` | database / schema name |
| `port` | port |
| `extra` | JSON blob, e.g. `{"project_id": "…", "location": "US"}` |

The `extra` field is where everything non-standard goes. For GCP
connections, `extra` typically holds:

```json
{"project_id": "my-project", "location": "US", "key_path": "/opt/airflow/dags/key.json"}
```

Read it back with `extra_dejson`:

```python
import json
conn = BaseHook.get_connection("gcp_default")
extra = json.loads(conn.extra or "{}")
project = extra.get("project_id")
```

Airflow 2.x exposes this as `conn.extra_dejson` in templates:

```jinja
{{ conn.gcp_default.extra_dejson['project_id'] }}
```

### Reading and writing from Python

**Variables:**

```python
from airflow.models import Variable

bucket = Variable.get("target_bucket")                        # raises if missing
bucket = Variable.get("target_bucket", default_var="")         # safe
bucket = Variable.get("target_bucket", default_var=None)       # None if missing
```

Airflow 2.x also has `Variable.get_var` / `Variable.set` (the older
API) and the newer `Variable.get` / `Variable.set` (the 2.0+ API).
Both exist; the newer names are the ones to use.

**Writing a Variable:**

```python
Variable.set("target_bucket", "my-bucket")
```

This writes to the metadata database. In Composer, prefer the UI for
production changes — a Variable set from a DAG file at parse time is a
hidden side effect and a race.

**Params:**

```python
def my_task(**context):
    params = context["params"]
    force = bool(params.get("force_full_load", False))
```

Note `params.get(...)` with a default. Params declared in the DAG's
`params={...}` block have defaults; params supplied at trigger time
override them.

**Connections:**

```python
from airflow.hooks.base import BaseHook

conn = BaseHook.get_connection("gcp_default")   # raises AirflowNotFoundException
host = conn.host
password = conn.password                          # decrypted on read
extra = json.loads(conn.extra or "{}")
```

For a *soft* lookup — "use it if it exists" — the context's `conn` object
supports `.get()`:

```python
conn = context["conn"].get("http_orders_api")
if conn is not None:
    log.info("api host: %s", conn.host)
```

### Setting them in the Composer UI

**Variables:** **Admin → Variables → +**. Enter a Key and a Value.
Optionally mark it as **Secret** — this masks the value in the UI, but
it does **not** encrypt it in the database and does **not** make it
appropriate for credentials. It only stops shoulder-surfing.

**Connections:** **Admin → Connections → +**. Fill in the Conn Id, the
Connection Type, and the host/login/password/schema/port fields, plus
the JSON `extra` if needed. The password field is encrypted
automatically.

**Params:** params are declared in the DAG file:

```python
params={
    "audience": "data-engineers",
    "bucket": "default-bucket",
}
```

and overridden at trigger time. In Composer, use **Trigger DAG → DAG
Run Config** and enter a JSON object:

```json
{"audience": "platform-team", "bucket": "my-bucket"}
```

In OSS Airflow 2.x, `airflow dags trigger <dag_id> --conf '{"bucket": "my-bucket"}'`.

### What is *not* protected

Being precise here matters:

| Stored in | Encrypted at rest? | Visible in UI? | In task logs? |
|---|---|---|---|
| Variable | **No** | Yes, plainly | If you log it |
| Param | No (stored in `dag_run.conf`) | Yes, in the run config tab | If you log it |
| Connection `password` | **Yes** (Fernet) | Masked | Only if you log it |
| Connection `extra` | Partially — `extra` is **not** encrypted in Airflow 2.x by default | Yes, plainly | If you log it |

That last row is the subtle one. **The `extra` field of a Connection is
not encrypted** in Airflow 2.x — only `password` is. So do not put a
private key in `extra`. In Composer 2.x, put service-account JSON in
`extra` only when the environment is using a service account whose key
is not embedded; prefer Workload Identity / attached service accounts,
where no key material is stored at all.

---

## 🛠️ Hands-On

### Step 1: See the defaults the local runner uses

The runner ships with a realistic set of Variables and Connections:

```bash
cd project
python3 -c "
from local_runner import DEFAULT_VARIABLES, DEFAULT_CONNECTIONS
print('DEFAULT_VARIABLES:')
for k, v in sorted(DEFAULT_VARIABLES.items()):
    print(f'  {k:<24} {v}')
print()
print('DEFAULT_CONNECTIONS:')
for name, spec in sorted(DEFAULT_CONNECTIONS.items()):
    print(f'  {name}:')
    for k, v in sorted(spec.items()):
        print(f'    {k:<12} {v}')
"
```

Expected output:

```text
DEFAULT_VARIABLES:
  alert_email             data-oncall@example.com
  bq_dataset              analytics
  bq_table                orders_enriched
  full_load_threshold     1000000
  gcp_project_id          demo-project
  pipeline_owner          data-platform
  reject_bq_table         analytics.orders_rejected
  source_bq_table         raw.orders
  source_bucket           demo-source-bucket
  target_bucket           demo-target-bucket

DEFAULT_CONNECTIONS:
  gcp_default:
    conn_id             gcp_default
    extra               {"project_id": "demo-project", "location": "US"}
    host                bigquery.googleapis.com
    schema              analytics
  http_orders_api:
    conn_id             http_orders_api
    extra               {"timeout": 30, "retries": 3}
    host                api.example.com
    login               svc_account
    password            not-a-real-secret
```

Look at `http_orders_api`: it has a `password` field. In real Airflow
that value would be encrypted in the database and masked in the UI. The
course uses a placeholder that is obviously not a secret.

### Step 2: Override a Variable and watch the DAG use it

```bash
python project/local_runner.py --dag etl_to_gcs --vars '{"target_bucket":"prod-orders-bucket"}' --verbose 2>&1 | grep -E 'would write|gcs_object_path'
```

Expected output:

```text
INFO       would write gs://prod-orders-bucket/etl_to_gcs/2026-01-15/summary.csv
INFO       gcs_object_path -> gs://prod-orders-bucket/orders/summary.csv
```

One Variable changed; the DAG file was not touched. **That is the entire
point of Variables.**

### Step 3: Read a Variable from Python

```bash
cd project/core
python3 -c "
from templating import build_context

ctx = build_context(dag_id='etl_to_gcs', logical_date='2026-01-15',
                    variables={'pipeline_owner': 'data-platform',
                               'target_bucket': 'demo-target-bucket'})
print('owner  :', ctx['var'].get('pipeline_owner', 'unassigned'))
print('bucket :', ctx['var'].get('target_bucket'))
print('missing:', ctx['var'].get('does_not_exist', 'fallback'))
"
```

Expected output:

```text
owner  : data-platform
bucket : demo-target-bucket
missing: fallback
```

`var.get(name, default)` is the safe read. `var.get(name)` with no
default raises.

### Step 4: The two spellings, side by side

```bash
cd project/core
python3 -c "
from templating import build_context, render_template

ctx = build_context(dag_id='etl_to_gcs', logical_date='2026-01-15',
                    variables={'target_bucket': 'demo-target-bucket',
                               'bq_dataset': 'analytics',
                               'bq_table': 'orders_enriched'})
for tpl in [
    '{{ var.value.target_bucket }}',
    '{{ var.target_bucket }}',
    '{{ var.value.bq_dataset }}.{{ var.value.bq_table }}',
    '{{ var_json }}',
]:
    print(f'{tpl:<45} -> {render_template(tpl, ctx)}')
"
```

Expected output:

```text
{{ var.value.target_bucket }}                -> demo-target-bucket
{{ var.target_bucket }}                      -> demo-target-bucket
{{ var.value.bq_dataset }}.{{ var.value.bq_table }} -> analytics.orders_enriched
```

Both spellings give the same result. Use `var.value.x` in new code.

> **Note:** Airflow's real context also exposes `{{ var_json }}` and
> `{{ conn_json }}` — the entire Variables and Connections maps as JSON
> strings. The course's `templating.py` is a teaching model and does not
> implement those two, so `{{ var_json }}` raises
> `UndefinedError` locally even though it works in Composer.

### Step 5: Read a Connection, safely and unsafely

```bash
cd project/core
python3 -c "
from templating import build_context, render_template

conns = {'gcp_default': {
    'conn_id': 'gcp_default',
    'host': 'bigquery.googleapis.com',
    'schema': 'analytics',
    'extra': '{\"project_id\": \"demo-project\", \"location\": \"US\"}',
}}
ctx = build_context(dag_id='etl_to_gcs', logical_date='2026-01-15', connections=conns)

print('host         ->', render_template('{{ conn.gcp_default.host }}', ctx))
print('schema       ->', render_template('{{ conn.gcp_default.schema }}', ctx))
print('extra.project->', render_template(\"{{ conn.gcp_default.extra_dejson['project_id'] }}\", ctx))
print('extra.loc    ->', render_template(\"{{ conn.gcp_default.extra_dejson['location'] }}\", ctx))
"
```

Expected output:

```text
host         -> bigquery.googleapis.com
schema       -> analytics
extra.project-> demo-project
extra.loc    -> US
```

`extra_dejson` parses the JSON blob and exposes it as a dict.

### Step 6: Prove that a missing Variable is a hard error

```bash
cd project/core
python3 -c "
from templating import build_context, render_template, TemplateRenderError

ctx = build_context(dag_id='x', logical_date='2026-01-15')
try:
    render_template('{{ var.value.secret_thing }}', ctx)
except TemplateRenderError as exc:
    print('without default ->', type(exc.cause).__name__)
    print('   ', exc.cause)
print()
print('with default    ->', render_template(\"{{ var.value.secret_thing | default('none') }}\", ctx))
"
```

Expected output:

```text
without default -> UndefinedError
    "variable 'secret_thing' not found (available: none)" is undefined

with default    -> none
```

### Step 7: Params — the per-run override

```bash
python project/local_runner.py --dag etl_to_gcs --params '{"bucket":"ad-hoc-bucket"}' --verbose 2>&1 | grep -E 'would write'
```

Expected output:

```text
INFO       would write gs://demo-target-bucket/etl_to_gcs/2026-01-15/summary.csv
```

Note that the param did *not* change the output path — because the
`etl_to_gcs` DAG's path template reads `var.value.target_bucket`, not
`params.bucket`. That is a good illustration of an important point:
**a param only affects the DAG if the DAG reads it.**

Read the params through the context:

```bash
cd project/core
python3 -c "
from templating import build_context, render_template

ctx = build_context(dag_id='templating_and_variables', logical_date='2026-01-15',
                    params={'audience': 'platform-team', 'bucket': 'my-bucket'})
print('params        ->', ctx['params'])
print('audience      ->', render_template('{{ params.audience }}', ctx))
print('bucket        ->', render_template('{{ params.bucket }}', ctx))
print('defaulted     ->', render_template(\"{{ params.missing | default('none') }}\", ctx))
"
```

Expected output:

```text
params        -> {'audience': 'platform-team', 'bucket': 'my-bucket'}
audience      -> platform-team
bucket        -> my-bucket
defaulted     -> none
```

### Step 8: The layering pattern, end to end

```bash
cd project/core
python3 -c "
from templating import build_context, render_template

TPL = '{{ params.bucket | default(var.value.gcs_bucket) | default(\"hard-coded\") }}'

cases = [
    ('param wins',      {'gcs_bucket': 'from-variable'}, {'bucket': 'from-param'}),
    ('variable wins',   {'gcs_bucket': 'from-variable'}, {}),
    ('hard-coded wins', {},                           {}),
]
for label, variables, params in cases:
    ctx = build_context(dag_id='x', logical_date='2026-01-15',
                        variables=variables, params=params)
    print(f'{label:<18} -> {render_template(TPL, ctx)}')
"
```

Expected output:

```text
param wins         -> from-param
variable wins      -> from-variable
hard-coded wins    -> hard-coded
```

Three levels, resolved most-specific-first.

### Step 9: What the DAG file actually does

```bash
sed -n '83,115p' project/dags/02_templating_and_variables.py
```

That is the real, deployable Airflow DAG: params declared with
defaults, a Variable read safely with `get(..., default)`, a Connection
read with a soft `.get()`, and a BashOperator whose command is entirely
template-driven.

---

## 🛠️ Common Errors and Fixes

### `airflow.exceptions.AirflowException: Could not find expected variables`

`Variable.get("x")` was called and `x` does not exist, with no default
supplied. This is the classic "it worked in dev" error: the Variable
was created in dev but not in prod.

```python
# FAILS in any environment where the variable is not set
Variable.get("source_bucket")

# Safe
Variable.get("source_bucket", default_var="")
```

Or, in a template:

```jinja
{{ var.value.source_bucket | default('') }}
```

### `airflow.exceptions.AirflowNotFoundException: Could not find expected connection`

`BaseHook.get_connection("x")` and the Connection does not exist.

```python
from airflow.hooks.base import BaseHook

conn = BaseHook.get_connection("gcp_default")
```

In Composer, create it under **Admin → Connections**. In OSS, use
`airflow connections add`.

### `KeyError: 'source_bucket'` in a template

A `params` key that does not exist, accessed with `[]` rather than
`.get()`. Use `{{ params.source_bucket | default('') }}`.

### The Variable is set but the DAG still uses the old value

Airflow caches Variables in the **web server** and in **workers**. A
Variable changed in the UI may not be visible to a task for up to a
minute (the cache TTL). In Airflow 2.x you can bypass the cache with
`Variable.get("x", cache_timeout=0)` — but that hits the database on
every call.

### The param is not being picked up

Check three things:

1. **Did you pass it?** In Composer: **Trigger DAG → DAG Run Config**,
   as a JSON object. In OSS: `--conf '{"key": "value"}'`.
2. **Does the DAG read it?** `params` are only values *if the DAG
   references them*. A param nobody reads does nothing.
3. **Is the key name right?** `params` keys are case-sensitive.

### `TypeError: 'NoneType' object is not subscriptable` on `context["params"]`

In Airflow 2.x, `context["params"]` is always a dict (empty if no params
were declared). But if you access `context["params"]["x"]` and `x` is
missing, you get a `KeyError`. Use `.get("x", default)`.

### The Connection's `extra` is not being parsed

`conn.extra` is a **string**. Parse it:

```python
import json
extra = json.loads(conn.extra or "{}")
```

Or, in a template, use `extra_dejson`, which Airflow provides for
exactly this.

### The Connection password is not being used by the provider operator

Provider operators look for a specific Connection type and specific
fields. Check that:

- The Connection's **type** matches what the operator expects
  (`gcpbigquery`, `google_cloud_platform`, `http`, …).
- The service-account JSON is in `extra` under the key the operator
  expects (`key_path`, `keyfile_dict`, `project_id`).
- In Composer, the environment's service account may already have the
  needed roles — in which case no key material is needed at all, and the
  best practice is to attach the service account rather than store a key.

### A secret appeared in a task log

Someone logged a Variable, a param, or `conn.password`. Redact before
logging:

```python
log.info("using password %s", "***")   # never log the value
```

Cloud Logging retains task logs, so a leaked secret in a log is a leaked
secret. Rotate it.

---

## 💡 Production Notes

- **Never put a credential in a Variable or a param.** Variables are
  plaintext in the metadata DB; params are stored in `dag_run.conf` and
  shown in the UI. Use a Connection.
- **Do not put private-key material in a Connection's `extra` either.**
  Only `password` is encrypted in Airflow 2.x. Prefer attached service
  accounts in Composer.
- **Declare params with defaults in the DAG.** A param with a default
  makes the DAG runnable without a trigger config.
- **Use `params` for run-scoped decisions** — backfill dates, force
  flags, ad-hoc filters. Use Variables for environment-scoped config.
- **Set Variables through the UI, not from a DAG file.** A DAG file that
  writes a Variable at parse time creates a hidden side effect and a
  race with the scheduler.
- **Version your Variable changes.** They are not in git. Keep a record
  of what each Variable means and which environments have it set.
- **Remember the Variable cache.** A UI change may take up to a minute
  to reach a running task.
- **Layer: param → Variable → constant.** This lets a run override
  everything without editing the DAG.
- **Use `| default()` on *required* Variables too**, if you want the DAG
  to parse in a fresh environment. The failure then surfaces as "empty
  bucket" — which is a clearer message than "DAG not found".

---

## 🔑 Key Takeaways

- Three mechanisms, three jobs: **Variable** = per environment,
  **param** = per run, **Connection** = secrets.
- The decision procedure: *credential?* → Connection. *Differs per run?*
  → param. *Differs per environment?* → Variable. *Neither?* → a
  constant in the DAG file.
- **Variables are plaintext** in the metadata database and visible in the
  UI. Only Connection `password` is encrypted. `extra` is **not**.
- The layering pattern: **`params.bucket | default(var.value.gcs_bucket)
  | default('hard-coded')`** — most specific wins.
- Both `{{ var.value.x }}` and `{{ var.x }}` work; **prefer
  `var.value.x`**.
- Read Variables with `Variable.get("x", default_var="")`, params with
  `context["params"].get("x", default)`, Connections with
  `BaseHook.get_connection("x")` — or the soft `context["conn"].get("x")`.
- A param that no task reads **does nothing**.

---

## 📚 Practice Exercises

1. **Classify everything.** Go through `project/dags/dag_config.py` and
   classify each constant as Variable, param, Connection, or hard-coded
   constant. Justify each answer.

2. **Implement a Variable.** Add `region_filter` to
   `DEFAULT_VARIABLES` in `local_runner.py` with a default of
   `"all"`, then override it on the command line with
   `--vars '{"region_filter": "EMEA"}'` and confirm the run still
   succeeds.

3. **Params that work.** Modify the `templating_paths` DAG's `target`
   template to read `params.target_bucket | default(var.value.target_bucket)`,
   then run it with `--params '{"target_bucket": "from-params"}'` and
   confirm the rendered path uses it. Explain why this is the correct
   layering.

4. **The security audit.** Find every place in `project/dags/` where a
   value is logged. For each, classify it as safe or unsafe and say
   why. Rewrite any unsafe one.

5. **Connection anatomy.** Using the default `gcp_default` connection,
   print the host, the schema, and both keys from `extra_dejson`. Then
   write the JSON you would put in `extra` for a Composer environment
   that uses an attached service account with no key material.

6. **Layering drill.** Produce a table of the resolved value of
   `{{ params.bucket | default(var.value.gcs_bucket) | default('hard-coded') }}`
   for all eight combinations of "param present/absent" × "variable
   present/absent". Verify each row with `render_template`.

7. **Reflection.** A teammate wants to store an API key in a Variable
   because "it's easier than setting up a Connection". Write a
   two-paragraph argument against it, using the encryption table from
   this chapter.

---

## 📖 Further Reading

- Airflow Variables — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/variables.html
- Airflow Connections — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/connections.html
- Airflow params — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html#dag-run-params
- Airflow templates reference — https://airflow.apache.org/docs/apache-airflow/stable/templates-ref.html
- Airflow security model — https://airflow.apache.org/docs/apache-airflow/stable/security.html
- Google Cloud Composer: managing connections — https://cloud.google.com/composer/docs/how-to/managing/connections
- Google Cloud Composer: managing environments (IAM, service accounts) — https://cloud.google.com/composer/docs/how-to/managing/environments
