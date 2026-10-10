---
lecture: L16
title: "Threshold types, Period, Evaluation Periods, Datapoints-to-Alarm"
duration: "12:00"
section: 4
prereqs: ["L15"]
---

# L16 — Threshold types, Period, Evaluation Periods, Datapoints-to-Alarm

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 4 — CloudWatch Alarms
> **Duration:** 12:00

## Prereqs

L15 (alarm 101).

## Key terms

- **`Period`** — granularity of each datapoint in seconds (10, 30, 60
  …).
- **`EvaluationPeriods`** — how many periods the alarm looks back (N).
- **`DatapointsToAlarm`** — how many of those N must breach (M).
- **M-of-N alarm** — an alarm with `DatapointsToAlarm = M` and
  `EvaluationPeriods = N`.
- **Static threshold** — a fixed number (e.g. `CPU > 70%`).
- **Anomaly-detection threshold** — a band around an ML model of the
  metric (covered in L18).
- **Threshold type** — `Static` or `AnomalyDetection`.

## Lecture

The most confusing part of CloudWatch alarms is the difference between
`Period`, `EvaluationPeriods`, and `DatapointsToAlarm`. Get this wrong
and you'll either have an alarm that never fires, or one that fires
constantly.

### The M-of-N rule

```
Period = 60            # each datapoint is a 1-min aggregate
EvaluationPeriods = 5  # look at the last 5 datapoints
DatapointsToAlarm = 3  # fire if 3 of those 5 are above threshold
```

This is the canonical "5 min window, 3 of 5 datapoints" pattern. It
tolerates one or two transient spikes without firing, but catches a
sustained problem.

### Choosing the right values

| Use case | Period | Eval | ToAlarm | Why |
|---|---|---|---|---|
| Critical 5xx page | 60 | 5 | 3 | Tolerate transient blip |
| Slow-burn cost alarm | 3600 | 24 | 12 | Hourly granularity over a day |
| Cold-start spammy | 60 | 1 | 1 | Fire on first occurrence |
| Disk filling up | 60 | 60 | 30 | 30-of-60 — alert when half the hour is bad |

### Comparison operators

| Operator | When it fires |
|---|---|
| `GreaterThanThreshold` | metric > threshold |
| `GreaterThanOrEqualToThreshold` | metric >= threshold |
| `LessThanThreshold` | metric < threshold |
| `LessThanOrEqualToThreshold` | metric <= threshold |
| `LessThanLowerOrGreaterThanUpperThreshold` | anomaly: outside the band |
| `LessThanLowerThreshold` | anomaly: below the lower band |
| `GreaterThanUpperThreshold` | anomaly: above the upper band |

### Static vs. anomaly-detection

- **Static** — a fixed number. Easy to reason about; brittle to
  changing baselines.
- **Anomaly-detection** — a band around an ML model of the metric.
  Adapts to traffic. Higher cost (anomaly detection is a paid feature).
  Covered in L18.

### A worked example

A team wants an alarm for "API p99 latency > 500ms for at least 3
minutes in a 5-minute window."

```python
cw.put_metric_alarm(
    AlarmName="checkout-p99-latency",
    Namespace="AWS/ApiGateway",
    MetricName="Latency",
    Statistic="p99",
    Dimensions=[{"Name": "ApiName", "Value": "checkout"}],
    Period=60,            # 1-min datapoints
    EvaluationPeriods=5,  # 5-minute lookback
    DatapointsToAlarm=3,  # 3 of 5 must breach
    Threshold=500,
    ComparisonOperator="GreaterThanThreshold",
    TreatMissingData="notBreaching",
)
```

A single 1-minute spike of 800ms doesn't fire (only 1-of-5 breach).
Three consecutive minutes of 600ms does (3-of-5 breach). Two minutes
of 800ms then a drop to 100ms also doesn't fire (2-of-5).

## Hands-on

In your AWS account:

1. Create a test alarm: `AWS/Lambda → Errors > 0` for 1 minute, with
   `DatapointsToAlarm = 1`.
2. Trigger the function with an error payload and watch it fire.
3. Add a second alarm with the same threshold but
   `DatapointsToAlarm = 5` — this one won't fire because only 1
   datapoint breaches.

## Quiz prep

- In a "3 of 5" alarm with a 60s period, how long is the lookback?
  (5 minutes)
- What does `Period` control? (Size of each datapoint in seconds.)
- Which operator do you use for an anomaly-detection alarm?
  (`LessThanLowerOrGreaterThanUpperThreshold` for both sides, or
  `LessThanLowerThreshold` / `GreaterThanUpperThreshold` for one side.)

## Further reading

- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmEvaluation.html`

## What's next

L17 — SNS as Alarm Action — wiring the on-call pager.
