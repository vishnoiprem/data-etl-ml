---
title: L54 — Lambda Monitoring — CloudWatch Metrics — Hands On
author: Prem Vishnoi <prem.vishnoi@example.com>
section: 11
duration: 6:17
---

# L54 — Lambda Monitoring — CloudWatch Metrics — Hands On

> The previous lecture listed the metrics and explained them. This
> one builds the dashboard that will live on your team's wall — a
> single pane showing invocations, errors, duration, throttles, and
> concurrency for one function.

## Prereqs

- L53 (theory).
- An AWS account + a deployed function with at least a few
  invocations.

## Key terms

- **`put_dashboard`** — boto3 API to (re)create a CloudWatch
  dashboard.
- **Widget type** — `metric`, `number`, `text`, `log`, `stacked`, etc.
- **Period** — granularity of each data point in seconds.

## 1. The dashboard we will build

A single dashboard `my-api-overview` with five widgets:

1. **Invocations/min** (line).
2. **Errors/min** (line) + **Error rate %** (number).
3. **Duration p50/p95/p99** (line, multi-stat).
4. **Throttles/min** (line).
5. **Concurrent executions vs. account limit** (stacked).

## 2. boto3 — build it from scratch

```python
import json, boto3

cw = boto3.client("cloudwatch", region_name="us-east-1")
ACCOUNT_LIMIT = 1000

widgets = []

widgets.append({
    "type": "metric",
    "x": 0, "y": 0, "width": 12, "height": 6,
    "properties": {
        "title": "Invocations / min",
        "metrics": [
            ["AWS/Lambda", "Invocations", "FunctionName", "my-api",
             {"stat": "Sum", "period": 60}],
        ],
        "view": "timeSeries",
    },
})

widgets.append({
    "type": "metric",
    "x": 12, "y": 0, "width": 12, "height": 6,
    "properties": {
        "title": "Errors / min",
        "metrics": [
            ["AWS/Lambda", "Errors", "FunctionName", "my-api",
             {"stat": "Sum", "period": 60}],
        ],
        "view": "timeSeries",
    },
})

widgets.append({
    "type": "metric",
    "x": 0, "y": 6, "width": 12, "height": 6,
    "properties": {
        "title": "Duration p50/p95/p99",
        "metrics": [
            ["AWS/Lambda", "Duration", "FunctionName", "my-api",
             {"stat": "p50", "period": 60}],
            ["...", {"stat": "p95", "period": 60}],
            ["...", {"stat": "p99", "period": 60}],
        ],
        "view": "timeSeries",
        "yAxis": {"left": {"label": "ms"}},
    },
})

widgets.append({
    "type": "metric",
    "x": 12, "y": 6, "width": 12, "height": 6,
    "properties": {
        "title": "Throttles / min",
        "metrics": [
            ["AWS/Lambda", "Throttles", "FunctionName", "my-api",
             {"stat": "Sum", "period": 60}],
        ],
        "view": "timeSeries",
    },
})

widgets.append({
    "type": "metric",
    "x": 0, "y": 12, "width": 24, "height": 6,
    "properties": {
        "title": "Concurrent executions",
        "metrics": [
            ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", "my-api",
             {"stat": "Maximum", "period": 60}],
        ],
        "view": "timeSeries",
    },
})

cw.put_dashboard(
    DashboardName="my-api-overview",
    DashboardBody=json.dumps({"widgets": widgets}),
)
```

Now go to CloudWatch → Dashboards → `my-api-overview`. You'll see
five widgets in a 24-grid layout.

## 3. Pulling fresh data on demand

Before the dashboard is populated, generate some traffic:

```bash
for i in $(seq 1 30); do
    aws lambda invoke --function-name my-api --payload '{}' \
        /tmp/out$i.json > /dev/null
done
```

Refresh the dashboard. Each widget should now have data.

## 4. Adding an alarm with boto3

```python
sns_topic = "arn:aws:sns:us-east-1:111122223333:oncall"
cw.put_metric_alarm(
    AlarmName="my-api-throttles",
    Namespace="AWS/Lambda",
    MetricName="Throttles",
    Statistic="Sum",
    Period=60,
    EvaluationPeriods=2,
    DatapointsToAlarm=1,
    Threshold=1,
    ComparisonOperator="GreaterThanThreshold",
    Dimensions=[{"Name": "FunctionName", "Value": "my-api"}],
    AlarmActions=[sns_topic],
)
```

A single throttle in 1 of the last 2 minutes → page.

## 5. EMF metrics for the dashboard

Drop this in your handler:

```python
import json, time, os
def handler(event, context):
    t0 = time.perf_counter()
    n = len(event.get("records", []))
    # ... do work ...
    print(json.dumps({
        "_aws": {
            "Timestamp": int(time.time() * 1000),
            "CloudWatchMetrics": [{
                "Namespace": "MyApp",
                "Dimensions": [["FunctionName", "Stage"]],
                "Metrics": [
                    {"Name": "ItemsProcessed", "Unit": "Count"},
                    {"Name": "LatencyMs",      "Unit": "Milliseconds"},
                ],
            }],
        },
        "FunctionName": context.function_name,
        "Stage": os.environ.get("STAGE", "prod"),
        "ItemsProcessed": n,
        "LatencyMs": (time.perf_counter() - t0) * 1000,
    }))
    return {"ok": True}
```

Now add `MyApp` widgets to the same dashboard by switching the
namespace:

```python
# Reuse the widgets above but set Namespace = "MyApp"
# and MetricName = "LatencyMs" or "ItemsProcessed"
```

## Lecture summary

- `put_dashboard` is the entire API — a JSON document, no clicks.
- One widget per standard metric, plus EMF widgets for custom
  metrics.
- Alarms on `Throttles` and `Errors` cover the most urgent signals.

## Hands-on (≈ 5 minutes)

```bash
# 1. Create the dashboard for an existing function
python 11_lambda_advanced_concepts/code/cw_dashboard_build.py \
    --function my-api

# 2. Burst some traffic
python 11_lambda_advanced_concepts/code/concurrency_burst.py

# 3. Watch the dashboard fill
open https://console.aws.amazon.com/cloudwatch/home#dashboards:name=my-api-overview
```

## Quiz prep

- Which API creates/updates a CloudWatch dashboard?
- How do you show three percentiles (p50/p95/p99) on one widget?
- What's the simplest way to wire an alarm that pages on any
  throttle?

## Further reading

- AWS — [`put_dashboard` reference](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_PutDashboard.html)
- AWS — [Lambda monitoring dashboard CFN template](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html#monitoring-metrics-examples)
