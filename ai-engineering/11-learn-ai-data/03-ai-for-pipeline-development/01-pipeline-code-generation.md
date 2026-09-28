# Lesson 1 — Pipeline Code Generation

> **Type:** Article · Module 3 · AI for Pipeline Development
> Generating ingestion pipelines that handle edge cases, not just happy paths.

---

## The 80/20 of pipelines

Pipelines are **80% boilerplate** (extractor skeleton, retries, logging, DAG, tests) and **20% the part you actually have to think about** (business validation, idempotency, edge cases). AI handles the 80% almost perfectly. The 20% is yours.

```
   Pipeline tasks                              AI handles?
   ─────────────                               ──────────
   Source connector boilerplate                ✅ 100%
   Pagination logic                            ✅ 90% (verify edge cases)
   Retry + backoff                             ✅ 100%
   Schema validation (Pydantic)                ✅ 90%
   Loader (warehouse upsert)                  ✅ 80% (verify MERGE logic)
   DAG scaffold                                ✅ 100%
   Logging                                     ✅ 100%
   Tests (happy path)                          ✅ 100%
   Tests (edge cases)                          ⚠️ must specify
   Business validation rules                   ❌ on you
   Idempotency strategy                        ❌ on you
   Backfill plan                               ❌ on you
   On-call runbook                             ❌ on you
```

---

## The happy-path trap

AI loves the happy path. It generates beautiful extraction code that handles the case where the API returns clean data on the first try. If you don't ask for edge cases, **it won't write that code**.

The failure mode in production is exactly the failure mode you did not specify.

```
   Happy path only (default)                    With explicit edge cases
   ────────────────────                         ────────────────────────
   ✅ API returns 200                           ✅ API returns 200
   ✅ all pages return                          ✅ handles 429 (backoff)
   ✅ schema unchanged                          ✅ handles 5xx (retry)
   ✅ no duplicates                             ✅ handles partial pages
   ✅ correct data                              ✅ handles new field tomorrow
   → SILENT FAILURES IN PROD                    ✅ handles duplicate row
                                                 → production-ready
```

---

## The pipeline-generation prompt

```text
ROLE: senior data platform engineer. Pipeline stack: Airflow 2.9 + Python 3.11 + Snowflake.

CONTEXT:
- Source: Stripe payments endpoint, paginated, Bearer-token auth.
- Destination: raw.stripe.payments_v2 Snowflake table, partitioned by ingest_date.
- Idempotency: re-running for the same ingest_date must upsert on payment_id.
- Schedule: @daily, 06:00 UTC.
- Retries: 3 with exponential backoff (60s, 300s, 900s).
- Alerting: Slack channel #data-alerts on failure.

TASK: Generate these files:
1. dags/stripe_payments.py — Airflow DAG from templates/dag_template.py
2. stripe_payments/extract.py — paginated extractor
3. stripe_payments/validate.py — Pydantic v2 schema
4. stripe_payments/load.py — Snowflake MERGE upsert
5. stripe_payments/test_extract.py — pytest stubs

CONSTRAINTS — DO NOT GENERATE HAPPY-PATH ONLY CODE. You MUST explicitly handle:
- 429 rate-limited response → exponential backoff + jitter
- 5xx server error → retry up to 3 times
- partial page (e.g. last page has 5 items) → still write what you got
- new field appears in API response → log warning, accept, surface
- duplicate payment_id in same page → de-dupe before load
- malformed JSON in a record → skip + log row, do NOT fail whole extract
- secret rotation failure (401) → fail loudly, alert, do NOT silently use stale token

Additional:
- use uv-managed env, structlog JSON output, type hints everywhere
- idempotent end-to-end: re-running for same ingest_date == no new rows
- tests: include edge cases listed above

FORMAT: one file per ```python block, file path comment at top.

VERIFICATION: list 5 unit tests + 1 integration test I should run before deploy.
```

**This single instruction in the constraints block is the difference between demo code and production code.**

---

## The "split into components" workflow

Never generate a whole pipeline in one shot. Break it apart:

```
   ┌────────────────────────────────────────────────┐
   │  STEP 1 — Source connector                     │
   │  "Generate the paginated Stripe API client    │
   │   with explicit backoff for 429 and 5xx."     │
   └─────────────┬──────────────────────────────────┘
                 ▼
   ┌────────────────────────────────────────────────┐
   │  STEP 2 — Extractor                            │
   │  "Generate the extractor that pages through   │
   │   all results, dedupes by payment_id, logs    │
   │   partial pages and unknown fields."          │
   └─────────────┬──────────────────────────────────┘
                 ▼
   ┌────────────────────────────────────────────────┐
   │  STEP 3 — Validator                            │
   │  "Generate the Pydantic v2 schema with        │
   │   strict types. Mark unknown fields.          │
   │   Reject malformed records."                  │
   └─────────────┬──────────────────────────────────┘
                 ▼
   ┌────────────────────────────────────────────────┐
   │  STEP 4 — Loader                               │
   │  "Generate the Snowflake MERGE upsert.       │
   │   Idempotent on (payment_id, ingest_date)."   │
   └─────────────┬──────────────────────────────────┘
                 ▼
   ┌────────────────────────────────────────────────┐
   │  STEP 5 — Orchestrator                         │
   │  "Generate the Airflow DAG using             │
   │   templates/dag_template.py. Schedule         │
   │   @daily, 06:00 UTC, retries 3."             │
   └─────────────┬──────────────────────────────────┘
                 ▼
   ┌────────────────────────────────────────────────┐
   │  STEP 6 — Tests                                │
   │  "Generate pytest tests covering every edge   │
   │   case in the constraints list."              │
   └────────────────────────────────────────────────┘
```

Each step runs at ~80% quality on first try. The whole pipeline assembled from these steps is **production-grade on day one**, not after a week of debugging.

---

## The "what AI gets wrong about pipelines" honesty

### 1. State management in streaming
AI defaults to batch pipeline patterns. Stateful streaming (exactly-once, watermarking, late-arrival handling) needs explicit spec.

### 2. Backfill behaviour
What happens when the source has 6 months of historical data and you want to load it? AI won't write the backfill DAG unless you ask.

### 3. Resource sizing
AI doesn't know your cluster size, executor memory, or shuffle partitions. Tell it.

### 4. Compliance / ACLs
AI doesn't know which rows are PII. Tell it which columns to mask.

### 5. Operational concerns
On-call runbook, alert routing, escalation — these are yours.

---

## The pipeline deliverable (what to ship)

After the workflow above, you have:

```
   dags/stripe_payments.py          (DAG)
   stripe_payments/                 (package)
       __init__.py
       extract.py                  (API client + extractor)
       validate.py                 (Pydantic schema)
       load.py                     (Snowflake MERGE)
       models.py                   (dataclasses)
   tests/
       test_extract.py             (edge cases)
       test_validate.py
       test_load.py
       fixtures/
           stripe_page1.json
           stripe_429.json
           stripe_partial.json
   README.md                       (runbook)
```

Each file went through the review (Lesson 5 of Module 1). Each test covers an edge case from the constraints block. The DAG extends your team's canonical template. README documents the runbook: "if you get an alert at 3 a.m., here's what to check."

---

## The 3-a.m. test

> Before shipping, ask: *"If this pipeline fails at 3 a.m., can someone who has never seen this code debug it in 30 minutes?"*

If the answer is no:
- The README is too thin.
- The tests don't cover the failure mode.
- The error messages are too generic.
- The alerting doesn't point to the next action.

Fix those before shipping. AI can draft all four. You review and own them.

---

## Worked Example — Stripe Payments daily ingestion pipeline, end-to-end

> **Task:** Build a pipeline that ingests Stripe Payments daily into a Snowflake warehouse. Source: Stripe REST API, paginated, rate-limited. Sink: `raw.stripe.payments_v2`. Must handle 429s, partial pages, schema changes, idempotent loads.

### Step 1 — The prompt (with the explicit anti-happy-path constraint)

```text
ROLE: senior data platform engineer.

CONTEXT — STACK:
- Python 3.11, dbt-snowflake 1.8, Airflow 2.9 on KubernetesExecutor
- Stripe SDK v8 (Python)
- Snowflake target table: raw.stripe.payments_v2 (schema: 23 columns)

TASK:
Build a daily incremental ingestion pipeline for Stripe Payments (v2).
Output directory: pipelines/stripe/payments/

Files (each a separate code block):
1. extract.py   — pulls payments since {{ ds }} from Stripe API, paginates, writes raw parquet to s3://lake/stripe/payments/{{ ds }}/
2. validate.py  — Pydantic model for the 23 fields + a row-level validator
3. load.py      — reads parquet from S3, MERGE-upserts into raw.stripe.payments_v2
4. dags/stripe_payments.py — Airflow DAG, extends templates/dag_template.py, schedules 06:00 UTC daily
5. tests/test_extract.py   — covers happy path, 429, partial page, empty response, schema-drift (new field)
6. tests/test_validate.py — covers happy path, malformed metadata, NULL handling
7. tests/test_load.py    — covers first-load, idempotent re-run, partial failure
8. fixtures/ — sample response payloads: stripe_page1.json, stripe_429.json, stripe_partial.json
9. README.md  — runbook: "if you get the alert at 3 a.m., here's the playbook"

CONSTRAINTS — DO NOT VIOLATE:
- DO NOT generate happy-path-only code. Every code path must handle failure explicitly.
- Use exponential backoff on 429 (initial=2s, max=120s, jitter).
- Pagination via cursor (Stripe returning has_more + next cursor).
- Schema validation MUST raise a typed error and quarantine the offending rows (write to s3://lake/stripe/payments/{{ ds }}/quarantine/).
- New fields in Stripe response → add to a `metadata_added_fields` log table (do not silently drop).
- Idempotency: every load must be safe to re-run. Use the payment_id as dedup key, MERGE with the staging row winning on _loaded_at.
- Type hints on every function.
- No bare except. Re-raise with context.
- on_failure_callback fires the team's slack_on_failure (already wired in template).
- SLAs: extract 4 min, validate 1 min, load 5 min.
- DO NOT use Airflow XCom for the raw payload. Only IDs and counts.
- Every error message must include: which task, what failed, what to do next.

FORMAT:
For each file, output the full contents in a ```python block (or ```yaml, ```bash as appropriate).
End with a "HANDOFF NOTES" section listing 5 things you couldn't decide and that the human should pick up.

VERIFICATION — you, the reviewer:
- pytest tests/ → all green
- mypy --strict extract.py validate.py load.py → no errors
- ruff check → no errors
- airflow tasks test stripe_payments extract_payments 2026-01-15 succeeds on a fixture
- a deliberate 429 (use stripe_429.json) retries and eventually succeeds
- a re-run of the DAG results in zero new rows in raw.stripe.payments_v2
```

### Step 2 — What AI gives you (extract.py)

```python
"""Stripe Payments extractor. Reads payments since {{ ds }}, paginated."""
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import backoff
import pandas as pd
import stripe

from pipelines.stripe.config import STRIPE_API_KEY, RAW_BUCKET

log = logging.getLogger(__name__)

MAX_RETRIES = 5
INITIAL_BACKOFF = 2.0
MAX_BACKOFF = 120.0


class StripeExtractError(Exception):
    """Raised when we cannot extract payments for the day after all retries."""


@backoff.on_exception(
    backoff.expo,
    (stripe.error.RateLimitError, stripe.error.APIConnectionError),
    max_tries=MAX_RETRIES,
    max_value=MAX_BACKOFF,
    jitter=backoff.full_jitter,
    logger=log,
)
def _fetch_page(since_ts: int, cursor: str | None) -> dict:
    """Fetch one page from Stripe. Retries on 429 and connection errors."""
    return stripe.PaymentIntent.list(
        created={"gte": since_ts},
        limit=100,
        starting_after=cursor,
        expand=["customer"],
    )


def extract_payments(execution_date: str, output_dir: Path) -> int:
    """Extract all payments modified on or after execution_date.

    Returns the number of rows extracted. Writes raw parquet to output_dir.
    """
    since_ts = int(
        datetime.strptime(execution_date, "%Y-%m-%d")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = output_dir / "payments.parquet"
    quarantine_path = output_dir / "quarantine"
    quarantine_path.mkdir(exist_ok=True)

    all_rows, quarantined = [], []
    cursor, page = None, 0
    while True:
        page += 1
        try:
            resp = _fetch_page(since_ts, cursor)
        except stripe.error.AuthenticationError as e:
            # 401 — config issue, fail loud
            raise StripeExtractError(
                f"Stripe auth failed on page {page}. Check STRIPE_API_KEY. "
                f"Action: verify the secret in vault."
            ) from e
        except stripe.error.InvalidRequestError as e:
            # 400 — likely our cursor is corrupted or scope is wrong
            raise StripeExtractError(
                f"Stripe rejected request on page {page}, cursor={cursor!r}. "
                f"Action: check API version and cursor handling."
            ) from e
        except stripe.error.APIError as e:
            # 5xx after retries — fail loud
            raise StripeExtractError(
                f"Stripe 5xx after {MAX_RETRIES} retries on page {page}. "
                f"Action: check https://status.stripe.com and re-run."
            ) from e

        for obj in resp.data:
            try:
                all_rows.append(_normalize(obj))
            except (KeyError, ValueError, TypeError) as e:
                # Row-level: log + quarantine, do not fail the whole run
                quarantined.append({"raw": dict(obj), "reason": str(e)})
                log.warning(
                    "Quarantined payment_id=%s reason=%s",
                    getattr(obj, "id", None),
                    e,
                )

        if not resp.has_more:
            break
        cursor = resp.data[-1].id

    if all_rows:
        pd.DataFrame(all_rows).to_parquet(parquet_path)
    if quarantined:
        pd.DataFrame(quarantined).to_parquet(
            quarantine_path / f"q_{execution_date}.parquet"
        )
    log.info(
        "extract_payments date=%s pages=%d rows=%d quarantined=%d",
        execution_date, page, len(all_rows), len(quarantined),
    )
    return len(all_rows)


def _normalize(obj: stripe.PaymentIntent) -> dict:
    """Convert a stripe.PaymentIntent into a flat dict matching raw.stripe.payments_v2."""
    return {
        "id": obj.id,
        "customer": obj.customer.id if obj.customer else None,
        "amount": obj.amount,
        "currency": obj.currency,
        "status": obj.status,
        "created": obj.created,
        "captured": obj.captured,
        "payment_method": obj.payment_method,
        "metadata": dict(obj.metadata or {}),
        "last4": (obj.payment_method_details.card.last4
                  if getattr(obj.payment_method_details, "card", None) else None),
        # ... 13 more fields
        "_extracted_at": int(time.time()),
    }
```

### Step 3 — What AI gave you (excerpts of the other files)

```python
# dags/stripe_payments.py
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.models import Variable
from acme.callbacks import slack_on_failure

from pipelines.stripe.payments.extract import extract_payments
from pipelines.stripe.payments.validate import validate_payments
from pipelines.stripe.payments.load import load_payments


default_args = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": slack_on_failure,
    "email_on_failure": False,
}


@dag(
    dag_id="stripe_payments",
    start_date=datetime(2026, 1, 1),
    schedule="0 6 * * *",
    catchup=False,
    default_args=default_args,
    tags=["domain:stripe", "tier:tier1"],
    max_active_runs=1,
)
def stripe_payments_dag():
    @task
    def extract(ds: str) -> str:
        out = Path(f"s3://lake/stripe/payments/{ds}/")
        n = extract_payments(ds, out)
        return str(out)

    @task
    def validate(in_path: str, ds: str) -> str:
        out = Path(in_path)
        rejected = validate_payments(out, ds)
        if rejected:
            # Surface quarantine count, do not fail
            return f"{out}/quarantine/q_{ds}.parquet"
        return str(out)

    @task
    def load(in_path: str, ds: str) -> dict:
        n = load_payments(in_path, ds)
        return {"loaded_rows": n}

    load(validate(extract()))


stripe_payments_dag()
```

```python
# tests/test_extract.py
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pipelines.stripe.payments.extract import extract_payments


FIXTURES = Path(__file__).parent / "fixtures"


def test_happy_path(extract_dir):
    with open(FIXTURES / "stripe_page1.json") as f:
        page1 = json.load(f)
    with open(FIXTURES / "stripe_page2_last.json") as f:
        page_last = json.load(f)

    with patch("stripe.PaymentIntent.list") as mock_list:
        mock_list.side_effect = [
            MagicMock(data=page1["data"], has_more=True),
            MagicMock(data=page_last["data"], has_more=False),
        ]
        n = extract_payments("2026-01-15", extract_dir)

    assert n == len(page1["data"]) + len(page_last["data"])
    assert (extract_dir / "payments.parquet").exists()


def test_handles_429_then_succeeds(extract_dir):
    """First call raises 429, second succeeds. backoff.expo retries silently."""
    import stripe

    with open(FIXTURES / "stripe_page1.json") as f:
        page1 = json.load(f)

    with patch("stripe.PaymentIntent.list") as mock_list:
        mock_list.side_effect = [
            stripe.error.RateLimitError("rate limited"),
            MagicMock(data=page1["data"], has_more=False),
        ]
        # Use tiny backoff for the test
        with patch("pipelines.stripe.payments.extract.INITIAL_BACKOFF", 0.01):
            n = extract_payments("2026-01-15", extract_dir)

    assert n == len(page1["data"])


def test_quarantines_malformed_row(extract_dir):
    """If a row fails _normalize, write to quarantine/, do not fail the run."""
    bad = [{"id": "pi_x", "amount": "NOT-AN-INT", "currency": "usd"}]
    good = [{"id": "pi_y", "amount": 1000, "currency": "usd"}]

    with patch("stripe.PaymentIntent.list") as mock_list:
        # _normalize will keyerror on bad; good passes
        # We construct the objects with the necessary attributes
        from pipelines.stripe.payments.extract import _normalize
        ...

    n = extract_payments("2026-01-15", extract_dir)
    assert (extract_dir / "quarantine" / "q_2026-01-15.parquet").exists()


def test_empty_response(extract_dir):
    with patch("stripe.PaymentIntent.list") as mock_list:
        mock_list.return_value = MagicMock(data=[], has_more=False)
        n = extract_payments("2026-01-15", extract_dir)
    assert n == 0
    # No parquet written when empty
    assert not (extract_dir / "payments.parquet").exists()
```

### Step 4 — What you (the human) add in review

You don't write the code. You **change** the code:

1. **Add a constant** `MAX_PARALLEL_PAGES = 4` and use `concurrent.futures` for parallel pagination. AI didn't. AI used sequential pagination — for 50 pages at 0.4s each = 20s. With parallel = 5s. Worth it.
2. **Tighten the auth-error message.** AI's says "Check STRIPE_API_KEY." You change it to:
   ```
   Stripe auth failed. Verify the secret at vault.example.com → secrets/data-platform/stripe.
   If recently rotated, run `airflow connections unset stripe_api; airflow connections add ...`.
   ```
3. **Add a `metadata_added_fields` log table** to `load.py`. AI didn't because the constraint was abstract; you make it concrete.
4. **Push the fixtures** to a real test directory in the repo (Stripe doesn't ship them). You write 2 of the 3 fixtures by hand (using Stripe's published sample responses) and ask AI to write the third from your schema.
5. **Add a runbook entry** to README.md:
   ```
   ## Alert: "Stripe 5xx after 5 retries"
   1. Check https://status.stripe.com — incident?
   2. If yes, wait it out, replay DAG with `airflow dags trigger stripe_payments -e 2026-01-15`.
   3. If no, check our outbound IP isn't on Stripe's block list.
   4. Re-trigger with backfill flag if you suspect data gap.
   ```

### Step 5 — Final CI run

```bash
ruff check pipelines/stripe/payments/
mypy --strict pipelines/stripe/payments/
pytest tests/ -v
# ... all green
```

### What this example demonstrates

| AI gave you | You added |
|---|---|
| 9 file scaffolding | Schema-aware error messages with next-action |
| Backoff, retry, pagination | Parallel pagination |
| Quarantine path | `metadata_added_fields` log table |
| DAG, test stubs | Real fixtures you wrote yourself |
| Generic README | Runbook with concrete links + commands |
| The "happy path" trap avoidance baked in via the constraints block | The 5 judgment calls AI couldn't make |

**Time:** ~25 min for the AI to draft, ~50 min for you to review, edit, and add the missing pieces. **Manual baseline:** a senior engineer writes this from scratch in 4–6 hours. **Speedup: ~5× with higher correctness** (because the failure modes were explicit in the prompt).

The single biggest leverage: the **CONSTRAINTS — DO NOT VIOLATE** block. Without it, AI gives you the happy path. With it, AI gives you production-ready skeleton.

---

## What Comes Next

> Lesson 2 — **AI for Spark** — generating PySpark code that's correct on your cluster config, your data shape, and your AQE settings.
