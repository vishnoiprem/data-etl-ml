---
lecture: L30
title: "SLO / SLI fundamentals & error-budget burn-rate alerts"
duration: "12:00"
section: 7
prereqs: ["L29"]
---

# L30 — SLO / SLI Fundamentals & Error-Budget Burn-Rate Alerts

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 7 — Real-World Patterns
> **Duration:** 12:00

## Prereqs

L29 (subscription filters).

## Key terms

- **SLI (Service Level Indicator)** — a measured signal of service
  quality (e.g. `availability = 1 - errors/requests`).
- **SLO (Service Level Objective)** — a target for the SLI over a
  window (e.g. "99.9% over 30 days").
- **Error budget** — `(1 - SLO) × window`. The amount of failure you
  can tolerate.
- **Burn rate** — how fast you're spending the budget. A burn rate
  of 1 = you'll exhaust the budget exactly at the end of the window.
- **Fast burn** — high burn rate over a short window (e.g. 1h).
  Catches a sudden outage.
- **Slow burn** — moderate burn rate over a long window (e.g. 6h).
  Catches a slow degradation.

## Lecture

Static thresholds are the wrong abstraction for "is my service
healthy?". The right one is **SLO + burn rate**.

### Step 1 — pick the SLI

For a web API, the canonical SLIs are:

- **Availability** = `1 - error_count / request_count`
- **Latency** = `requests_faster_than_threshold / total_requests`
- **Throughput** = `successful_requests_per_second`

For CloudWatch:

```python
# Availability SLI
expr = "(invocations - errors) / invocations * 100"
```

### Step 2 — pick the SLO

Start with a **realistic** number. Most teams start at 99% (the
"three-nines myth") and quickly discover they can't meet it. Begin
at 99.5% (a 4-hour monthly budget) and tighten over time.

### Step 3 — compute the error budget

```
SLO          = 99.9% over 30 days
error budget = (1 - 0.999) × 30 × 24 × 60 = 43.2 minutes
```

### Step 4 — burn-rate alerts

From the Google SRE workbook (chapter 5), the canonical pair is:

| Alert | Window | Threshold | Latency |
|---|---|---|---|
| **Fast burn** | 1h | 14.4× the SLO budget | pages on-call |
| **Slow burn** | 6h | 6× the SLO budget | pages on-call |

A 14.4× burn rate over 1h will exhaust a 30-day budget in 2 days. A
6× burn rate over 6h will exhaust it in 5 days. Both warrant a page.

### Step 5 — build it in CloudWatch

Using metric math:

```python
cw.put_metric_alarm(
    AlarmName="checkout-availability-fast-burn",
    Metrics=[
        {"Id": "err_rate",
         "Expression": "(invocations - errors) / invocations * 100",
         "ReturnData": True},
        {"Id": "invocations",
         "MetricStat": {"Metric": {"Namespace": "AWS/Lambda",
                                   "MetricName": "Invocations",
                                   "Dimensions": [{"Name": "FunctionName",
                                                   "Value": "checkout"}]},
                        "Period": 60, "Stat": "Sum"},
         "ReturnData": False},
        {"Id": "errors",
         "MetricStat": {"Metric": {"Namespace": "AWS/Lambda",
                                   "MetricName": "Errors",
                                   "Dimensions": [{"Name": "FunctionName",
                                                   "Value": "checkout"}]},
                        "Period": 60, "Stat": "Sum"},
         "ReturnData": False},
    ],
    Threshold=0.1,            # 99.9% => 0.1% error rate
    ComparisonOperator="GreaterThanThreshold",
    EvaluationPeriods=60,     # 60 × 1 min = 1h window
    DatapointsToAlarm=60,     # 60 of 60
    TreatMissingData="notBreaching",
    AlarmActions=[oncall_topic],
)
```

The slow-burn alarm uses `EvaluationPeriods=360, DatapointsToAlarm=360,
Period=60` for a 6h window at 1-min granularity.

### Step 6 — visualise

A dashboard with:
- Single-value widget for current availability %.
- Two line widgets: 1h and 6h burn rate.
- Text widget: "Error budget remaining: 38.4 min (89%)".

This is exactly what `assignments/assignment_1_slo_dashboard.md` asks
you to build.

## Hands-on

In your AWS account, build a fast-burn alarm for one of your Lambda
functions. Subscribe an email to a new SNS topic and wait for the
alarm to fire (you can trigger it by raising the function's error
rate temporarily).

## Quiz prep

- What's the error budget for a 99.9% SLO over 30 days?
  (43.2 minutes.)
- What does a 14.4× burn rate mean? (Exhausts a 30-day budget in 2
  days.)
- Why use metric math instead of a custom metric? (Doesn't count as
  a custom metric; no extra cost.)

## Further reading

- Google SRE workbook, chapter 5: *Alerting on SLOs*.
- `assignments/assignment_1_slo_dashboard.md` — build it end to end.

## What's next

L31 — Cost Optimization.
