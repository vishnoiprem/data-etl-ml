---
lecture: L18
title: "Composite Alarms & Anomaly Detection Alarms"
duration: "13:00"
section: 4
prereqs: ["L17"]
---

# L18 — Composite Alarms & Anomaly Detection Alarms

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 4 — CloudWatch Alarms
> **Duration:** 13:00

## Prereqs

L17 (SNS as alarm action).

## Key terms

- **Composite alarm** — an alarm whose state is computed from other
  alarms using boolean logic (AND / OR / NOT).
- **`AlarmRule`** — a string expression like
  `ALARM(checkout-5xx) OR ALARM(checkout-p99)`.
- **Anomaly detection** — a CloudWatch feature that builds an ML model
  of a metric and returns an "expected band".
- **`ANOMALY_DETECTION_BAND(metric, N)`** — metric-math function that
  produces a band `N` standard deviations wide around the model's
  expected value.
- **Band width** — typically 2σ (95% of normal data) or 3σ (99.7%).

## Lecture

Two advanced alarm types. Use them when static thresholds get noisy.

### Composite alarms

A composite alarm combines other alarms with boolean logic:

```python
cw.put_composite_alarm(
    AlarmName="checkout-page-oncall",
    AlarmRule=(
        "ALARM(checkout-5xx) OR "
        "ALARM(checkout-p99-latency) OR "
        "ALARM(checkout-error-budget-fast-burn)"
    ),
    ActionsEnabled=True,
    AlarmActions=[oncall_topic_arn],
)
```

This single composite alarm is the **only** alarm that pages on-call.
The leaf alarms (`checkout-5xx`, `checkout-p99-latency`,
`checkout-error-budget-fast-burn`) still exist and transition
independently — useful for debug — but the pager only fires when the
composite is in ALARM.

The expression language supports `ALARM(name)`, `OK(name)`,
`INSUFFICIENT_DATA(name)`, `AND`, `OR`, `NOT`, parentheses.

### Why use composite alarms?

1. **Single paging target.** Operators get one notification stream,
   not three.
2. **De-duplication.** If two leaves fire at once, you don't get
   paged twice.
3. **Encapsulation.** Maintenance can disable individual leaves
   without changing the on-call surface.

### Anomaly detection alarms

For metrics that have a strong weekly or daily seasonality (e.g. web
traffic at noon), static thresholds either:
- Fire constantly during peak hours, or
- Miss real problems during off-peak.

Anomaly detection builds a model of "expected for this time of day
and day of week" and lets you alarm on *deviations*.

```python
# 1. Create the model
cw.put_anomaly_detector(
    Namespace="AWS/ApiGateway",
    MetricName="Count",
    Stat="Sum",
    Dimensions=[{"Name": "ApiName", "Value": "checkout"}],
)

# 2. Alarm on the 3-sigma band
cw.put_metric_alarm(
    AlarmName="checkout-traffic-anomaly",
    Metrics=[{
        "Id": "anomaly",
        "Expression": "ANOMALY_DETECTION_BAND(m1, 3)",
        "Label": "3-sigma band",
    }, {
        "Id": "m1",
        "MetricStat": {
            "Metric": {
                "Namespace": "AWS/ApiGateway",
                "MetricName": "Count",
                "Dimensions": [{"Name": "ApiName", "Value": "checkout"}],
            },
            "Period": 300,
            "Stat": "Sum",
        },
        "ReturnData": False,
    }],
    Threshold=0,                              # always
    ComparisonOperator="LessThanLowerOrGreaterThanUpperThreshold",
    EvaluationPeriods=3,
    DatapointsToAlarm=2,
)
```

> **Note:** Anomaly detection takes **up to 2 weeks** to train. You
> won't see sensible bands for the first 14 days. Plan for this in
> any new service rollout.

### When to use what

| Pattern | Use |
|---|---|
| Static threshold | Stable, well-understood metrics (CPU, disk) |
| Anomaly detection | Seasonal traffic (web RPS, queue depth) |
| Composite | Consolidating multiple leaves into one paging target |
| Metric math + composite | Burn-rate alarms (L30) |

## Hands-on

In your AWS account:

1. Build a composite alarm that is the OR of two existing alarms
   you already have.
2. Subscribe a different email to the composite alarm's topic and
   verify it fires when one of the leaves fires.

(Anomaly detection is best left for production, since the model
needs 2 weeks of training data.)

## Quiz prep

- What's the syntax for an OR over two alarms?
  (`ALARM(a) OR ALARM(b)`)
- How long does anomaly detection take to train? (Up to 2 weeks.)
- What does `ANOMALY_DETECTION_BAND(m, 3)` produce? (A 3σ band
  around the expected value.)

## Further reading

- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Create_Composite_Alarm.html`
- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Anomaly_Detection.html`

## What's next

L19 — Hands-on: build `put_metric_alarm.py` + 5 moto tests.
