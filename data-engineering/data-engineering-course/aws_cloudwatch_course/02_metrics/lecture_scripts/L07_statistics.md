---
lecture: L07
title: "Statistics: Average, Sum, Min, Max, p99, Percentile"
duration: "10:00"
section: 2
prereqs: ["L06"]
---

# L07 — Statistics: Average, Sum, Min, Max, p99, Percentile

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 2 — CloudWatch Metrics
> **Duration:** 10:00

## Prereqs

L06 (resolution).

## Key terms

- **Statistic** — the aggregation function applied to the datapoints
  inside a period. Default is `Average`.
- **Average** — sum / count.
- **Sum** — total of all datapoints in the period. Use for *rate*
  metrics (requests / minute).
- **p99 / p95 / p50** — the 99th / 95th / 50th percentile. Use for
  *latency* metrics.
- **Extended statistic** — any percentile `p0` through `p99.99`. Billed
  as a separate metric.
- **Metric math** — arithmetic across multiple metrics. Doesn't count
  as a new custom metric.

## Lecture

When you query a metric, you choose a **statistic**. The choice is
just as important as the metric itself: "average CPU" hides spikes
that p99 surfaces; "sum of errors" is the right view for an alarm
"any 5xx in last 5 min".

### The five built-in statistics

| Statistic | Use case | Example |
|---|---|---|
| `Average` | CPU, memory, latency-mean | "is the average latency OK?" |
| `Sum` | counts (requests, errors, bytes) | "how many 5xx in the last 5m?" |
| `Minimum` | floor (idle capacity) | "did the queue ever drain?" |
| `Maximum` | peak (saturation) | "what's the worst CPU in the fleet?" |
| `SampleCount` | how many datapoints in the period | "is the metric even reporting?" |

### Percentiles — the latency lens

`p99` (the 99th percentile) means: *99% of requests were faster than
this value*. It is **the** statistic for user-facing latency SLAs.

Why? Average is misleading: a few very slow requests inflate the
average, but most users still see a fast site. p99 is "the worst-case
most of your users will see."

```python
stats = cw.get_metric_statistics(
    Namespace="MyApp",
    MetricName="LatencyMs",
    Dimensions=[{"Name": "FunctionName", "Value": "checkout"}],
    StartTime=start,
    EndTime=end,
    Period=60,
    Statistics=["Average", "p99", "p95", "p50"],   # extended statistics
    ExtendedStatistics=["p99.9"],                 # the very tail
)
```

> **Note:** Percentile statistics are reported as **extended statistics**.
> CloudWatch stores them separately and bills them as a separate metric.
> Check pricing in the cheat sheet.

### Choosing the right statistic per use case

| Signal | Best statistic |
|---|---|
| "Is the API fast?" | `p99` of latency |
| "Are we dropping traffic?" | `Sum` of `ThrottledRequests` |
| "Is the queue healthy?" | `Maximum` of `ApproximateNumberOfMessagesVisible` |
| "Is the box overloaded?" | `Average` of `CPUUtilization` |
| "Did the alarm fire on too few datapoints?" | `SampleCount` of the alarm metric |

### Metric math — combine for free

Metric math lets you derive new time-series from existing ones
**without** publishing a new metric. Examples:

```python
# Error rate as a percent
math = boto3.client("cloudwatch")
math.get_metric_data(MetricDataQueries=[{
    "Id": "err_rate",
    "Expression": "errors / invocations * 100",
    "Period": 60,
}])
```

You can also reference the result in an alarm:

```python
cw.put_metric_alarm(
    AlarmName="high-error-rate",
    Metrics=[{
        "Id": "err_rate",
        "Expression": "errors / invocations * 100",
        "ReturnData": True,
    }],
    Threshold=1.0,            # 1% error rate
    ComparisonOperator="GreaterThanThreshold",
    EvaluationPeriods=3,
)
```

This is the canonical pattern for a **burn-rate alarm** (see L30).

### Two statistics to avoid

1. **Min over a *count*** — minimum 0 is meaningless.
2. **Average of a *latency*** — gives a wrong impression; always use
   p99 or p95.

## Hands-on

In your AWS account:

1. Open `AWS/Lambda → Duration` for a function.
2. Graph it with **Average** and **p99** overlaid (use the **Add
   math expression** → `AVG` then `p99`).
3. Notice how `p99` is the line you actually care about.

## Quiz prep

- Which statistic is right for a "5xx in last 5 min" alarm? (Sum)
- Which statistic is right for an "API is fast" SLI? (p99)
- Is metric math a separate billable metric? (No)

## Further reading

- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/using-metric-math.html`
- `../../downloads/cloudwatch_cheat_sheet.md`.

## What's next

L08 — `put_metric_data` + `get_metric_data` with boto3.
