---
lecture: L31
title: "Cost Optimization — log retention, metric filters, anomaly bands"
duration: "10:00"
section: 7
prereqs: ["L30"]
---

# L31 — Cost Optimization — log retention, metric filters, anomaly bands

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 7 — Real-World Patterns
> **Duration:** 10:00

## Prereqs

L30 (SLOs).

## Key terms

- **Log retention** — the dominant Logs cost. Set it deliberately.
- **High-resolution vs. standard** — high-res costs 3× per datapoint.
- **Metric math** — does *not* count as a custom metric.
- **Metric streams → Firehose → S3** — bulk-export pattern for
  analytics without per-API cost.
- **Anomaly detection** — paid feature; use only when needed.

## Lecture

The seven biggest cost levers, in order of impact:

### 1. Log retention (biggest single lever)

Default is **Never expire** — set it deliberately. For most workloads
**30 days** is plenty.

```python
for lg in logs.describe_log_groups()["logGroups"]:
    if "retentionInDays" not in lg:
        logs.put_retention_policy(logGroupName=lg["logGroupName"],
                                  retentionInDays=30)
```

Run this as a monthly Lambda or a one-off script.

### 2. Don't enable detailed monitoring unless you need 1-min EC2

`aws ec2 monitor-instances` costs $3 / instance / month. Default
5-min basic monitoring is free. Only enable for instances you graph
on 1-min dashboards.

### 3. Use metric math instead of new custom metrics

```
err_rate = errors / invocations * 100
```

…as a metric-math expression doesn't add a new billable metric.

### 4. Use percentile statistics only where needed

`p99` is a separate billable "extended statistic". If you only ever
look at `p99`, that's fine; if you also pull `p95`, `p90`, and `p50`,
that's 4 metrics instead of 1.

### 5. Tighten alarm evaluation periods

`EvaluationPeriods=60, Period=60` polls every minute. If you don't
need that granularity, use `Period=300` — 5× fewer datapoints.

### 6. Subscription-filter only what you need

A subscription filter fires for *every* matching event, with
downstream cost. Use specific filter patterns (`{ $.level = "ERROR" }`)
instead of broad ones (`"ERROR"`).

### 7. Use metric streams to S3 for bulk analysis

If you're doing analytics on metrics ("show me CPU across 10,000
instances over 90 days"), Metric Streams → Firehose → S3 is **10-100×**
cheaper than Insights queries.

```python
cw.put_metric_stream(
    Name="all-metrics-to-firehose",
    FirehoseArn="arn:aws:firehose:...:deliverystream/metrics-archive",
    RoleArn="arn:aws:iam::...:role/CWMetricStreamToFirehose",
    OutputFormat="opentelemetry0.7",
    IncludeFilters=[{"Namespace": "AWS/EC2"}],
)
```

### Quick cost audit script

```python
cw = boto3.client("cloudwatch")
logs = boto3.client("logs")

# 1. List alarms > 10 (each over free tier costs $0.10)
alarms = cw.describe_alarms()["MetricAlarms"]
print(f"alarms: {len(alarms)} (free: 10)")

# 2. List log groups with no retention
no_retention = [g["logGroupName"] for g in logs.describe_log_groups()["logGroups"]
                if "retentionInDays" not in g]
print(f"log groups with no retention: {len(no_retention)}")

# 3. List detailed-monitored EC2 instances
ec2 = boto3.client("ec2")
detailed = [i for r in ec2.describe_instances()["Reservations"]
            for i in r["Instances"]
            if i.get("Monitoring", {}).get("State") == "enabled"]
print(f"EC2 instances with detailed monitoring: {len(detailed)}")
```

## Hands-on

In your AWS account, run the audit script above. Set retention on
any log group missing it.

## Quiz prep

- What's the default log retention? (Never expire.)
- Does metric math count as a billable custom metric? (No.)
- How much does detailed EC2 monitoring cost per instance-month? ($3.)

## Further reading

- AWS pricing: <https://aws.amazon.com/cloudwatch/pricing/>
- `07_real_world/lecture_scripts/L32_alarms_at_scale.md` (next).

## What's next

L32 — Alarms at Scale.
