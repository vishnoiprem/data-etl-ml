# Lesson 4 — AI for Airflow

> **Type:** Article · Module 3 · AI for Pipeline Development
> Generating DAGs that extend your team's template, with retries, callbacks, tests, and a runbook.

---

## The DAG template is the moat

Every team has a canonical DAG template. **The single highest-leverage Airflow setup is a `templates/dag_template.py` that the AI extends instead of inventing.**

```python
# templates/dag_template.py — referenced in CLAUDE.md
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from acme.callbacks import slack_on_failure

default_args = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": slack_on_failure,
    "email_on_failure": False,
}

def make_dag(dag_id: str, schedule: str, tags: list[str]) -> DAG:
    return DAG(
        dag_id=dag_id,
        start_date=datetime(2026, 1, 1),
        schedule=schedule,
        catchup=False,
        default_args=default_args,
        tags=tags,
        max_active_runs=1,
    )
```

The AI extends this. The team doesn't have 15 different DAG patterns.

---

## The DAG-generation prompt

```text
ROLE: senior Airflow 2.9 engineer.

CONTEXT:
- DAGs in dags/, one per source domain
- Extend the template at templates/dag_template.py
- Use Astronomer Cosmos or TaskFlow API only
- Slack on_failure callback via acme.callbacks.slack_on_failure
- Retries 2, retry_delay 5 min, exponential backoff

TASK: generate a DAG dags/stripe_payments.py that:
- ingests payments from Stripe API
- runs daily at 06:00 UTC
- extracts → validates → loads (raw.stripe.payments_v2)
- ends with a freshness check + DQ assertions
- alerts Slack on failure

TASKS (use TaskFlow API):
1. extract_payments (PythonOperator) — extracts from API
2. validate_payments (PythonOperator) — Pydantic validation
3. load_to_snowflake (PythonOperator) — MERGE upsert
4. dq_check (PostgresOperator / SnowflakeOperator) — dbt source freshness + row count

CONSTRAINTS:
- extend templates/dag_template.py; do not re-define default_args
- XCom only for small metadata (counts, ids); not for DataFrames
- each task has its own try/except so failures propagate correctly
- include a runbook link in the docstring

FORMAT:
1. dags/stripe_payments.py in ```python
2. tests/dags/test_stripe_payments.py — 3 unit tests using airflow.models DagBag

VERIFICATION:
- airflow dags list shows the new DAG
- airflow tasks test stripe_payments extract_payments <date>  succeeds
- on_failure_callback fires on a deliberately failing task
```

---

## The on-failure callback pattern

The callback is **the difference between a 3 a.m. page and a quiet pager**:

```python
def slack_on_failure(context):
    """Post a structured alert to Slack with runbook link."""
    ti = context["ti"]
    dag_id = context["dag"].dag_id
    task_id = ti.task_id
    execution_date = context["execution_date"]
    log_url = ti.log_url
    runbook = RUNBOOKS.get(dag_id, "https://internal/runbooks/general")

    msg = (
        f":red_circle: *DAG failure*\n"
        f"*DAG*: `{dag_id}`\n"
        f"*Task*: `{task_id}`\n"
        f"*Run*: {execution_date}\n"
        f"*Logs*: {log_url}\n"
        f"*Runbook*: {runbook}"
    )
    slack.post("#data-alerts", msg)
```

The AI generates this once. It's reused across every DAG.

---

## The TaskFlow pattern

```python
from airflow.decorators import dag, task
from pendulum import datetime

@dag(
    dag_id="stripe_payments",
    start_date=datetime(2026, 1, 1),
    schedule="0 6 * * *",
    catchup=False,
    default_args=default_args,
    tags=["domain:stripe", "tier:raw"],
)
def stripe_payments():

    @task
    def extract() -> list[dict]:
        return run_extract("2026-01-01")

    @task
    def validate(records: list[dict]) -> list[dict]:
        return [Payment.parse(r) for r in records if Payment.is_valid(r)]

    @task
    def load(records: list[dict]) -> None:
        merge_into_snowflake(records, "raw.stripe.payments_v2")

    @task
    def dq_check() -> None:
        assert_freshness("raw.stripe.payments_v2", sla_minutes=60)

    extract() >> validate() >> load() >> dq_check()

stripe_payments()
```

AI writes this correctly when told to use the TaskFlow API.

---

## The DAG test pattern

```python
# tests/dags/test_stripe_payments.py
from airflow.models import DagBag

def test_dag_loaded():
    """DAG file parses without import errors."""
    dagbag = DagBag(dag_folder="dags/", include_examples=False)
    assert len(dagbag.import_errors) == 0, dagbag.import_errors

def test_dag_has_expected_tasks():
    dag = DagBag().get_dag("stripe_payments")
    expected = {"extract", "validate", "load", "dq_check", "end"}
    assert set(dag.task_ids) == expected

def test_dag_schedule_and_retries():
    dag = DagBag().get_dag("stripe_payments")
    assert dag.schedule == "0 6 * * *"
    assert dag.default_args["retries"] == 2
    assert dag.tags == ["domain:stripe", "tier:raw"]
```

---

## The retry / backoff policy

```python
default_args = {
    "retries": 3,
    "retry_delay": timedelta(minutes=1),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
    "retry_backoff_factor": 2,
}
```

Tells Airflow: retry at 1m, 2m, 4m (exponential, capped at 30m).

AI defaults to `retry_delay = 5 minutes, retries = 3` (constant). For transient errors, exponential is better. **Specify this in CLAUDE.md.**

---

## The on-failure alert routing

```
   severity 1 (downstream prod impact)    →  PagerDuty page
   severity 2 (delayed load, no impact)   →  Slack #data-alerts
   severity 3 (slow, not failing)         →  Slack #data-perf
   severity 4 (test DAG failure)          →  Slack #data-ci

   Set per-task: `on_failure_callback = route_alert(severity=...)`
```

---

## The runbook generation prompt

```text
Given dags/stripe_payments.py, generate the runbook:

# Runbook — stripe_payments DAG

## When this DAG fails

### Most common causes
1. Stripe API rate-limit (429) → wait 5 min, re-run last task
2. Snowflake MERGE conflict → check for concurrent loads
3. Schema drift → see `docs/stripe_schema_history.md`

### Quick checks
- `airflow tasks list stripe_payments`
- `airflow dags show stripe_payments`
- Snowflake: `SELECT MAX(loaded_at) FROM raw.stripe.payments_v2`

### Recovery steps
1. Identify the failing task from the alert
2. Check the runbook link in the alert
3. If transient: clear the task and let it retry
4. If schema: notify the schema owner, update the source
5. If persistent: page the on-call

### Escalation
- L1: @data-platform-oncall
- L2: @data-platform-lead
- L3: VP Data
```

---

## The AI for Airflow — what it gets wrong

- **SLA / SLI definitions.** AI doesn't know your business SLAs.
- **Backfill logic.** AI writes the daily DAG; the backfill is separate.
- **Cross-DAG dependencies.** `trigger_dag_id=` and `sensor` patterns need explicit spec.
- **Resource pools.** AI doesn't know your concurrency constraints.
- **Testing in CI.** The DAG file is tested; the actual run is harder.

---

## What Comes Next

> Lesson 5 — **AI Testing & Validation** — generating dbt tests, pytest suites, and end-to-end data contracts using AI as a test-generation partner.
