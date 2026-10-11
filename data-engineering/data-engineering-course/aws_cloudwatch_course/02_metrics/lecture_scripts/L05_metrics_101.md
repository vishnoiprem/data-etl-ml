---
lecture: L05
title: "Metrics 101 — Namespaces, Metric Names, Dimensions"
duration: "10:00"
section: 2
prereqs: ["L04"]
---

# L05 — Metrics 101 — Namespaces, Metric Names, Dimensions

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 2 — CloudWatch Metrics
> **Duration:** 10:00

## Prereqs

L04 (console tour). Basic Python and `boto3` helpful for the hands-on
section.

## Key terms

- **Namespace** — a container for related metrics. AWS namespaces start
  with `AWS/` (e.g. `AWS/EC2`). Your custom namespaces must **not** start
  with `AWS/`.
- **Metric name** — the name of the measurement within a namespace
  (e.g. `CPUUtilization`).
- **Dimension** — a key=value pair that disambiguates a metric. Examples:
  `InstanceId=i-0abc`, `FunctionName=my-lambda`.
- **Time-series** — the unique combination of `{namespace, metric name,
  dimensions}`. A single time-series is a single line on a graph.
- **Cardinality** — the number of unique time-series for a metric. High
  cardinality is the most common way teams burn their CloudWatch bill.

## Lecture

A CloudWatch metric is a **time-series** identified by a unique
combination of:

1. **Namespace** (string, e.g. `AWS/EC2`)
2. **Metric name** (string, e.g. `CPUUtilization`)
3. **Dimensions** (set of key=value pairs, e.g. `{InstanceId: i-0abc}`)

The same metric name in different namespaces is a different metric.
The same metric name in the same namespace with different dimensions
is a different metric. Dimensions are how you slice.

### Anatomy of a metric

```
namespace      metric-name           dimensions
AWS/EC2        CPUUtilization        {InstanceId: i-0abc}
                                          │
                                          └──── one time-series
```

A single EC2 instance of `t3.medium` produces dozens of time-series
(CPUUtilization, NetworkIn, NetworkOut, StatusCheckFailed_*, …) each
with `{InstanceId: i-0abc}` as its only dimension.

### Standard namespaces (subset)

| Namespace | Source | Common dimensions |
|---|---|---|
| `AWS/EC2` | EC2 hypervisor | `InstanceId` |
| `AWS/Lambda` | Lambda service | `FunctionName`, `Resource` |
| `AWS/ApiGateway` | API Gateway | `ApiName`, `Stage`, `Resource`, `Method` |
| `AWS/RDS` | RDS | `DBInstanceIdentifier` |
| `AWS/DynamoDB` | DynamoDB | `TableName`, `GlobalSecondaryIndexName`, `Operation` |
| `AWS/ELB` | ELB / ALB | `LoadBalancer`, `AvailabilityZone` |
| `AWS/ECS` | ECS | `ClusterName`, `ServiceName` |
| `AWS/States` | Step Functions | `StateMachineArn`, `ActivityArn` |

A full list is in `../../downloads/cloudwatch_cheat_sheet.md`.

### Custom namespaces

You can publish your own metrics to **any namespace that doesn't start
with `AWS/`**. Best practice:

- One namespace per application or service, e.g. `MyApp`, `CheckoutAPI`,
  `Ingestion`.
- Use a single namespace per service so dashboards auto-discover all
  metrics.

```python
cw.put_metric_data(
    Namespace="MyApp",
    MetricData=[{
        "MetricName": "LatencyMs",
        "Value": 87.4,
        "Unit": "Milliseconds",
    }],
)
```

### Dimensions — the cardinality trap

Each unique combination of dimensions is a *separate* time-series. If
you do:

```python
put_metric_data(Namespace="MyApp",
                MetricData=[{"MetricName": "LatencyMs",
                             "Dimensions": [{"Name": "RequestId",
                                             "Value": uuid4()}],
                             "Value": 87.4}])
```

…you create a **new** time-series for every request. With 1,000 RPS you
emit 86 million series / day, each of which is billable as a
*custom metric*. This will bankrupt your AWS account in days.

**Rules of thumb:**

- Dimensions should be **bounded enums** (function name, region, status
  code), not free-form user input.
- **Never** put request-id, user-id, session-id, IP, or anything
  high-cardinality in a dimension.
- If you want per-request debug data, **use logs**, not metric
  dimensions.

### Recommended pattern

| Use case | Right pillar |
|---|---|
| "How many users got 500 in the last 5 min?" | Metric with `{status=500}` dimension |
| "Why did *this user* get 500?" | Log with `user_id` field |
| "Show me the failing request" | Trace span |

## Hands-on

In your AWS account:

1. Open the console: *Metrics → All metrics* → search for a metric
   you've already published (e.g. `AWS/Lambda → Errors`).
2. Note the **namespace**, **metric name**, and **dimensions**.
3. Switch to a different metric, e.g. `AWS/EC2 → CPUUtilization`,
   and see the `InstanceId` dimension.

## Quiz prep

- What are the 3 things that uniquely identify a CloudWatch metric?
- Why is putting `RequestId` in a dimension dangerous?
- What's the difference between `AWS/EC2` and a custom `EC2` namespace?

## Further reading

- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html`
- `../../downloads/cloudwatch_cheat_sheet.md` (namespaces table).

## What's next

L06 — Standard vs. High-Resolution Metrics, Storage Resolution.
