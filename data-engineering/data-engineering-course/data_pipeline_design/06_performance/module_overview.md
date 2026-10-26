# Module 06 — Performance, Scalability & Fault Tolerance

> **4 lessons · ~2 hours**

The "operations" module. Every senior interview ends with
"how does this fail?" — this module is the answer. DAG
orchestration, retry with backoff, and monitoring with SLA
tracking. By the end you'll be able to talk about reliability
for an hour.

Author: **Prem Vishnoi &lt;pvishnoi@avilx.com&gt;**

---

## Lessons

| # | Lesson | What you'll learn |
|---|---|---|
| 25 | [Orchestration and DAGs](design/25_orchestration_and_dags.md) | Airflow, Dagster, Prefect; the DAG as code. |
| 26 | [Retry, Backoff, and Dead Letter Queues](design/26_retry_backoff_and_dlq.md) | Exponential backoff with jitter; DLQs for poison messages. |
| 27 | [Monitoring: SLA, Quality, Alerting](design/27_monitoring_sla_quality_alerting.md) | SLA tracking, p95 latency, data quality metrics. |
| 28 | [Data Quality: The Five Checks Every Pipeline Must Have](design/28_data_quality.md) | Row count, null rate, distribution drift, freshness, schema — with a Python `QualityCheck` class. |

---

## Code

- [`code/orchestrator.py`](code/orchestrator.py) — a tiny DAG
  runner with topological sort and per-task state.
- [`code/retry.py`](code/retry.py) — exponential backoff
  decorator with optional jitter.
- [`code/monitoring.py`](code/monitoring.py) — SLA tracker with
  sliding-window success rate and p95 duration.
- [`tests/test_perf.py`](tests/test_perf.py) — 15+ unit tests.

---

## What this module is

The "operations" module. Most candidates can draw the
pipeline; few can describe how it *fails*. This module is
the difference between a mid answer and a senior answer in
the reliability deep dive.
