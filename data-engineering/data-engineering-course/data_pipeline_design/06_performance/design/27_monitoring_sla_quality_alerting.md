# 27 — Monitoring: SLA, Data Quality Metrics, Alerting

> **Lesson 27 of 30 — Performance & Fault Tolerance**

The difference between a pipeline that runs and a pipeline
that's *known to run*. This lesson is the monitoring stack:
SLA tracking, quality metrics, and the alerts that wake
on-call.

---

## 1. The three things to monitor

Every production pipeline monitors three categories:

| Category | What it answers |
|---|---|
| **SLA** | "Is the pipeline on time?" |
| **Quality** | "Is the data correct?" |
| **Operations** | "Is the system healthy?" |

The senior move: name all three unprompted. "I monitor SLA,
data quality, and operational health. SLA is the freshness
and duration. Quality is the row counts and null rates.
Operational is the CPU, memory, and lag."

---

## 2. The SLA definition

An SLA is a *promise* about the pipeline's behavior:

- "The daily pipeline completes by 6 AM."
- "The streaming pipeline has a 30-second lag at p99."
- "The CDC pipeline has zero data loss."

Each SLA has a metric, a target, and an alert threshold.

```
Metric:        pipeline.duration_minutes
Target:        <= 60 minutes
Alert:         > 90 minutes
```

The senior move: "I'd define the SLA as a metric and a
target. The alert is when the metric exceeds the target
plus a buffer."

---

## 3. The freshness SLA

The simplest SLA: the source must have been updated within
the expected window.

```sql
-- The freshness check
SELECT NOW() - MAX(updated_at) AS lag FROM orders;
```

If `lag > SLA`, page on-call. The senior move: "Every source
has a freshness SLA. The pipeline enforces it via a check
that runs every 5 minutes."

---

## 4. The duration SLA

The pipeline must complete within a time budget. The metric
is the wall-clock duration; the SLA is the target.

```python
duration = end_time - start_time
if duration > SLA:
    page_oncall("Pipeline exceeded SLA")
```

The senior move: "I'd track the duration on every DAG run.
The alert is when the p95 over the last 7 days exceeds the
SLA. A single slow run is OK; a sustained pattern is not."

---

## 5. The data quality metrics

The quality metrics are the row count, null rate, and
schema conformance:

| Metric | What it answers |
|---|---|
| `row_count` | Did the pipeline produce the expected number of rows? |
| `null_rate` | Are the columns mostly populated? |
| `unique_rate` | Are the unique keys actually unique? |
| `schema_match` | Does the destination match the contract? |

The senior move: "I'd track row count, null rate on
critical columns, and uniqueness on primary keys. The
alert is a 3-sigma deviation from the 30-day mean."

---

## 6. The operational metrics

The operational metrics are the system health:

| Metric | What it answers |
|---|---|
| `consumer.lag` | How far behind is the consumer? |
| `db.connections` | Is the pool exhausted? |
| `disk.usage` | Will the disk fill up? |
| `error.rate` | Are we failing more than usual? |

The senior move: "I'd track consumer lag (alert if > 5
minutes), DB connection pool wait (alert if > 5 seconds),
disk usage (alert if > 80%), and error rate (alert if
> 1% over 5 minutes)."

---

## 7. The alert tiers

Not all alerts are equal. The senior pattern is three
tiers:

| Tier | Channel | When |
|---|---|---|
| **Info** | Slack / dashboard | Worth knowing, no action needed. |
| **Warning** | Slack + ticket | Action during business hours. |
| **Page** | PagerDuty / phone | Action now, 24/7. |

The senior move: "I'd tier the alerts. Freshness miss
during business hours is a ticket; freshness miss at 3 AM
is a page. SLA miss is always a page."

---

## 8. The dashboards

Every team has a dashboard. The minimum:

- **Pipeline health**: green/yellow/red for each DAG, plus
  duration over time.
- **Data quality**: row count, null rate, unique rate over
  time, with SLA lines.
- **Operational**: consumer lag, error rate, disk usage.

The senior move: "I'd build a Grafana dashboard with three
rows: pipeline health, data quality, operational. The
dashboard is the on-call's first stop."

---

## 9. The code: `code/monitoring.py`

The course provides a tiny SLA tracker:

```python
from data_pipeline_design.06_performance.code.monitoring import SLATracker

tracker = SLATracker()
tracker.record_job("daily_orders", duration_ms=45_000, success=True)
print(tracker.success_rate("daily_orders", window_minutes=60))
print(tracker.p95_duration("daily_orders", window_minutes=60))
```

The test in `tests/test_perf.py` feeds 100 fake job runs
and asserts the success rate and p95.

---

## 10. The interview answer

> "I monitor three things: SLA, data quality, and
> operational health. SLA is freshness and duration, with
> alerts when the p95 over 7 days exceeds the target. Data
> quality is row count, null rate, and uniqueness, with
> alerts on 3-sigma deviations. Operational is consumer lag,
> error rate, and disk usage. I'd tier the alerts: info
> goes to Slack, warning goes to a ticket, page goes to
> PagerDuty. The deep dive would be the freshness check
> pattern and the alert thresholds."

That single paragraph covers: three categories, three
metrics per category, three alert tiers, deep-dive choice.
Senior answer in 30 seconds.

---

## Try it

Look at the most recent pipeline you've worked on. Is there
an SLA? Is there a freshness check? Is there a quality
check on row count? Is there an alert? Is the alert
tiered? If any is "no," the pipeline is *running* but not
*known to be running*.
