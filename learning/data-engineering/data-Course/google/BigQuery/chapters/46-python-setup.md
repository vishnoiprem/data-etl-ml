# 7.1 — Python Client: Setup & Authentication

> **Section 7 · Python Client Library · Lecture 7.1 · 3:08**

## 🎯 What you will learn

- Install and configure `google-cloud-bigquery`
- The authentication methods and when to use each
- The `bigquery.Client` object and its core configuration
- A reusable, production-grade client setup

---

## 🧠 Concept

The Python client is the most common way to interact with BigQuery programmatically, and it is
how you will build real pipelines.

### Install

```bash
# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install google-cloud-bigquery pandas pyarrow db-dtypes

# Or from a requirements file
pip install -r resources/requirements.txt

# Verify
python -c "import google.cloud.bigquery as bq; print(bq.__version__)"
```

### Authentication options

| Method | When to use | Security |
|--------|-------------|----------|
| `gcloud auth application-default login` | Local development | ✅ Short-lived tokens |
| Service account key file | Legacy automation, non-GCP CI | ⚠️ Long-lived secret |
| **Impersonation** | **Local dev + CI** | ✅ **Short-lived, no key files** |
| Workload Identity | GKE, Cloud Run, GCE | ✅ Best — no keys at all |

```bash
# Recommended: impersonation (no key files)
gcloud auth application-default login \
    --impersonate-service-account=bq-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

```python
# The client finds credentials automatically
from google.cloud import bigquery

client = bigquery.Client()                    # uses ADC
client = bigquery.Client(project="YOUR_PROJECT_ID")
client = bigquery.Client(project="YOUR_PROJECT_ID", location="US")
```

### The client object

```python
from google.cloud import bigquery

client = bigquery.Client(
    project="YOUR_PROJECT_ID",
    location="US",
    default_query_job_config=bigquery.QueryJobConfig(
        maximum_bytes_billed=1_000_000_000,   # 1 GB safety cap on EVERY query
        labels={"env": "dev", "team": "data-eng"},
    ),
)
```

💡 **Set `default_query_job_config` on the client.** It applies a byte cap and labels to every
query the client runs, so a careless `client.query(...)` can never run away.

---

## 🛠️ Hands-On

### 1. Verify the connection

```python
from google.cloud import bigquery

client = bigquery.Client()

print(f"Project: {client.project}")
print(f"Location: {client.location}")

# Test query
query = """
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT country_code) AS countries
    FROM `bigquery-public-data.world_bank.country_population`
"""
result = client.query(query).result()
for row in result:
    print(f"Rows: {row.total_rows}, Countries: {row.countries}")
```

### 2. A production-grade client module

```python
"""
bq_client.py — a reusable, production-grade BigQuery client.

Usage:
    from bq_client import get_client
    client = get_client()
"""
from __future__ import annotations

import logging
import os
from typing import Any

from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

log = logging.getLogger(__name__)

DEFAULT_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "YOUR_PROJECT_ID")
DEFAULT_LOCATION = os.environ.get("BQ_LOCATION", "US")
DEFAULT_MAX_BYTES = int(os.environ.get("BQ_MAX_BYTES_BILLED", 10 * 1024**4))

# Reuse one client per process — it manages a connection pool internally
_client: bigquery.Client | None = None


def get_client(
    project: str = DEFAULT_PROJECT,
    location: str = DEFAULT_LOCATION,
    max_bytes_billed: int = DEFAULT_MAX_BYTES,
) -> bigquery.Client:
    """Return a configured BigQuery client (singleton)."""
    global _client
    if _client is not None:
        return _client

    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=max_bytes_billed,
        labels={"env": os.environ.get("ENV", "dev")},
        use_legacy_sql=False,
    )

    _client = bigquery.Client(
        project=project,
        location=location,
        default_query_job_config=job_config,
    )
    log.info("BigQuery client ready: project=%s location=%s", project, location)
    return _client


def run_query(
    sql: str,
    client: bigquery.Client | None = None,
    params: dict[str, Any] | None = None,
    job_config: bigquery.QueryJobConfig | None = None,
):
    """Execute a query and return the result, with a friendly error message."""
    client = client or get_client()
    try:
        if params:
            job_config = job_config or bigquery.QueryJobConfig()
            job_config.query_parameters = [
                bigquery.ScalarQueryParameter(k, v.__class__.__name__, v)
                for k, v in params.items()
            ]
        job = client.query(sql, job_config=job_config)
        return job.result()
    except GoogleCloudError as exc:
        log.error("Query failed: %s", exc)
        raise
```

### 3. Query with parameters

```python
client = get_client()

sql = """
    SELECT
        order_date,
        COUNT(*) AS order_count,
        SUM(total_amount) AS revenue
    FROM `YOUR_PROJECT_ID.curated.orders`
    WHERE order_date BETWEEN @start_date AND @end_date
    GROUP BY order_date
    ORDER BY order_date
"""

job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter("start_date", "DATE", "2026-01-01"),
        bigquery.ScalarQueryParameter("end_date", "DATE", "2026-01-31"),
    ]
)

for row in client.query(sql, job_config=job_config).result():
    print(row.order_date, row.order_count, row.revenue)
```

💡 **Always use `ScalarQueryParameter` with an explicit type.** Inferring the type from the Python
value can produce surprises (a `datetime.date` becomes `DATE`, but a string stays `STRING`).

### 4. A dry-run helper

```python
def estimate_cost(sql: str, client: bigquery.Client | None = None) -> dict[str, float]:
    """Estimate the cost of a query without running it."""
    client = client or get_client()
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)

    job = client.query(sql, job_config=job_config)

    bytes_processed = job.total_bytes_processed or 0
    tib = bytes_processed / (1024**4)
    return {
        "bytes_processed": bytes_processed,
        "tib": round(tib, 4),
        "estimated_cost_usd": round(tib * 6.25, 4),
    }


estimate = estimate_cost("SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders`")
print(f"Estimated cost: ${estimate['estimated_cost_usd']}")
```

💡 **Call `estimate_cost` before every non-trivial query in your pipeline.** It is free, instant,
and prevents surprises.

---

## 🛠️ Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `DefaultCredentialsError` | No ADC found | `gcloud auth application-default login` |
| `Forbidden: Permission denied` | IAM role missing | `roles/bigquery.jobUser` + `dataViewer` |
| `Not found: Dataset` | Wrong project or region | Check `client.project` and `client.location` |
| `Query exceeds resource limits` | Byte cap or quota | Add a partition filter |
| `AttributeError: module 'google.cloud' has no attribute 'bigquery'` | Missing package | `pip install google-cloud-bigquery` |
| `google.auth.exceptions.RefreshError` | Expired key | Use impersonation or re-login |

---

## 💡 Production Notes

- **Reuse one client per process.** It manages an HTTP connection pool internally; creating a
  client per query is slow and wasteful.
- **Set `maximum_bytes_billed` in the default job config** — the single best safety habit.
- **Use `location` explicitly** for non-US datasets, or queries will fail with "Not found".
- **Prefer impersonation over key files.** It eliminates the largest secret-management problem.
- **Set `use_legacy_sql=False`** in the default config.
- **Wrap queries in a helper with error handling** rather than scattering `client.query` calls.

---

## 🔑 Key Takeaways

- `pip install google-cloud-bigquery`; credentials come from ADC automatically.
- **Set `default_query_job_config` with `maximum_bytes_billed`** — it protects every query.
- **Reuse one client per process** — it pools connections.
- Use **impersonation instead of key files** for local development and CI.
- Always pass an **explicit `location`** for non-US datasets.
- Build a `estimate_cost` helper and use it before every non-trivial query.

---

## 📚 Practice Exercises

1. **Client module.** Write a production `bq_client.py` with: client singleton, a `run_query`
   helper with retry, a `dry_run_cost` helper, a `dataset_exists` check, and structured logging.

2. **Authentication matrix.** Set up all four authentication methods in separate environments.
   Document which you would use for: local dev, a GitHub Action, a GKE pod, and a laptop on a
   corporate VPN.

3. **Cost guardrail.** Write a decorator that wraps any function taking SQL, dry-runs it first,
   and raises if the estimated cost exceeds a threshold. Apply it to your query functions.

4. **Error handling.** Write a wrapper that catches `GoogleCloudError`, inspects the reason code,
   and retries only on transient errors (`backendError`, `rateLimitExceeded`) with exponential
   backoff.

5. **Notebook integration.** Set up a Jupyter kernel that uses your `bq_client` module and
   pre-loads a helper for `%%bigquery`-style magics.

---

## 📖 Further Reading

- Python client reference — https://cloud.google.com/python/docs/reference/bigquery/latest/index
- Authentication — https://cloud.google.com/docs/authentication/provide-credentials-adc
- BigQuery client samples — https://cloud.google.com/bigquery/docs/samples-python
