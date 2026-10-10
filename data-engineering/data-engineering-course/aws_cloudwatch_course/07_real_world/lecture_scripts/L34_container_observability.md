---
lecture: L34
title: "Observability for Containers (ECS / EKS)"
duration: "5:00"
section: 7
prereqs: ["L33"]
---

# L34 — Observability for Containers (ECS / EKS)

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 7 — Real-World Patterns
> **Duration:** 5:00

## Prereqs

L33 (serverless observability).

## Key terms

- **Container Insights** — CloudWatch's per-container / per-pod metrics
  feature. Costs extra.
- **ECS metrics** — `CPUUtilization`, `MemoryUtilization` (cluster and
  service level).
- **EKS metrics** — `cluster_failed_node_count`, `node_cpu_utilization`.
- **CloudWatch agent** — the standard sidecar for host-level metrics.
- **AWS Distro for OpenTelemetry (ADOT)** — the standard way to ship
  traces + metrics to CloudWatch.

## Lecture

Containers are mostly "more of the same" — but with a per-pod /
per-container dimension that explodes cardinality.

### ECS

| Metric | Dimensions |
|---|---|
| `CPUUtilization` | `ClusterName`, `ServiceName` |
| `MemoryUtilization` | `ClusterName`, `ServiceName` |
| `RunningTaskCount` | `ClusterName`, `ServiceName` |
| `EphemeralStorageUtilized` | `ClusterName` |

For per-pod / per-container metrics, enable **Container Insights**.
This adds a *paid* layer of detail at the task level.

### EKS

The EKS control plane emits metrics via the
`Container Insights` namespace. The data plane (worker nodes) is
visible via the CloudWatch agent (on EC2) or the **ADOT** collector
(on Fargate / on-prem).

### The cardinality problem

If you naively put `ContainerId` as a dimension, you get *millions*
of time-series. Container Insights' default settings are
sane — they aggregate to task level by default.

### Logs from containers

The simplest pattern is the **awslogs** log driver:

```json
{
  "logConfiguration": {
    "logDriver": "awslogs",
    "options": {
      "awslogs-group": "/ecs/myapp",
      "awslogs-region": "us-east-1",
      "awslogs-stream-prefix": "myapp"
    }
  }
}
```

This creates one log group `/ecs/myapp` and one stream per container
instance. Add a metric filter for `ERROR` to surface 5xx.

### Traces from containers

For traces, the canonical pattern is:

```
Container → ADOT collector → CloudWatch ServiceLens → X-Ray
```

ServiceLens correlates the trace with metrics + logs in the console.

### When to leave CloudWatch for a third-party tool

CloudWatch is **great for AWS-native metrics + logs**. For deep
container telemetry (per-pod flame graphs, eBPF-level visibility)
you'll quickly hit the limits. Datadog, New Relic, Grafana Cloud are
common complements.

## Hands-on

In your AWS account, if you have an ECS cluster:

1. Open *CloudWatch → Container Insights* and explore the
   `CPUUtilization` and `MemoryUtilization` widgets.
2. Check the log group for a service: `/ecs/<service-name>`.
3. Note the high cardinality of streams.

## Quiz prep

- What is Container Insights? (CloudWatch's per-pod / per-container
  metrics feature.)
- What's the standard log driver for ECS? (`awslogs`.)
- What's the standard collector for traces in containers? (ADOT.)

## Further reading

- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights.html`

## What's next

L35 — Course Wrap-up.
