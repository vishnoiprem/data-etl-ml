---
lecture: L06
title: "Standard vs. High-Resolution Metrics, Storage Resolution"
duration: "12:00"
section: 2
prereqs: ["L05"]
---

# L06 — Standard vs. High-Resolution Metrics, Storage Resolution

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 2 — CloudWatch Metrics
> **Duration:** 12:00

## Prereqs

L05 (metrics 101 — namespaces / dimensions).

## Key terms

- **Storage resolution** — how often CloudWatch samples a metric. Either
  60 seconds (standard) or 1 second (high-resolution).
- **Standard resolution** — 1 datapoint / minute, retained 15 months
  with decreasing granularity (1m → 5m → 1h as you go further back).
- **High resolution** — 1 datapoint / second, retained up to 15 months.
  Costs 3× as much per datapoint.
- **Detailed monitoring** — the EC2-specific term for "1-min
  resolution". Costs $3 / instance-month.
- **Basic monitoring** — the EC2 default: 5-min resolution, free.

## Lecture

CloudWatch gives you two storage resolutions for metrics. The choice
matters for both cost and how fast you can detect problems.

### Standard resolution (1 minute)

- Default for all AWS service metrics except EC2 (which is 5-min basic
  by default).
- Each data point is one minute long.
- Cost: **$0.01 per 1,000 datapoints**.

```python
cw.put_metric_data(
    Namespace="MyApp",
    MetricData=[{
        "MetricName": "LatencyMs",
        "Value": 87.4,
        "Unit": "Milliseconds",
        # No StorageResolution field — defaults to 60
    }],
)
```

### High resolution (1 second)

- Opt-in: set `StorageResolution=1` on each `MetricDatum`.
- Cost: **$0.03 per 1,000 datapoints** (3× standard).
- Use only when you need per-second visibility (e.g. detecting flash
  spikes, or auto-scaling on a custom signal).

```python
cw.put_metric_data(
    Namespace="MyApp",
    MetricData=[{
        "MetricName": "LatencyMs",
        "Value": 87.4,
        "Unit": "Milliseconds",
        "StorageResolution": 1,   # 1-second resolution
    }],
)
```

### Detailed monitoring for EC2

EC2 has a separate toggle that controls whether 1-min or 5-min
metrics are emitted:

- **Basic monitoring** (default, free) — 5-min granularity.
- **Detailed monitoring** ($3 / instance / month) — 1-min granularity.

You toggle it via the console (*EC2 → Instances → Monitoring tab*) or
via `aws ec2 monitor-instances`. Always enable detailed monitoring
*before* building dashboards on top of EC2 metrics; otherwise your
p99 lines look like a stair-step.

### Aggregated datapoints — `StatisticValues`

When you publish a metric, you don't have to publish a single value.
You can publish a *statistic set* (min, max, sum, sample count) for
the period. CloudWatch then aggregates them for you server-side.

```python
cw.put_metric_data(
    Namespace="MyApp",
    MetricData=[{
        "MetricName": "LatencyMs",
        "StatisticValues": {
            "SampleCount": 100,
            "Sum": 8742.0,
            "Minimum": 12.3,
            "Maximum": 245.7,
        },
        "Unit": "Milliseconds",
    }],
)
```

This is the right way to push batch-aggregated data: 1000 requests
on one host become a single API call, not 1000.

### What resolution should I use?

| Use case | Recommended |
|---|---|
| CPU/Network for an EC2 fleet | 1-min (enable detailed monitoring) |
| Lambda duration / errors | 1-min (default) |
| Custom business metric (orders/min) | 1-min |
| API p99 latency, normal traffic | 1-min |
| Trading / high-frequency | 1-sec (high-resolution) |
| One-off dev metric | 1-min |

**Rule of thumb:** default to 1-min. Upgrade to 1-sec only if you
have a specific latency or scale requirement that 1-min cannot satisfy.

### Data retention

CloudWatch stores datapoints at full resolution for **15 days**. After
that it aggregates them to 5-min resolution for 63 days, then 1-hour
for 455 days. You pay *storage* only once; the *resolution* you
publish at determines how many datapoints you get billed for.

## Hands-on

In `02_metrics/code/put_metric_data.py` (built in L09) you'll see how
`StorageResolution=1` is used in the `put_metric_data` API call.

For now, in your AWS account:

```bash
# Enable detailed monitoring for an EC2 instance
aws ec2 monitor-instances --instance-ids i-0abc
```

## Quiz prep

- What is the default storage resolution of `put_metric_data`?
  (60 seconds)
- How much does high-resolution cost vs. standard?
  (3× — $0.03 vs $0.01 per 1,000 datapoints)
- How long are metrics kept at full resolution?
  (15 days)

## Further reading

- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html`
- `../../downloads/cloudwatch_cheat_sheet.md`.

## What's next

L07 — Statistics: Average, Sum, Min, Max, p99, Percentile.
