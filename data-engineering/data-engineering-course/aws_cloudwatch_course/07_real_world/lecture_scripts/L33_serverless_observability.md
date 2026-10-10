---
lecture: L33
title: "Observability for Serverless (Lambda + API Gateway + DynamoDB)"
duration: "8:00"
section: 7
prereqs: ["L32"]
---

# L33 — Observability for Serverless (Lambda + API Gateway + DynamoDB)

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 7 — Real-World Patterns
> **Duration:** 8:00

## Prereqs

L32 (alarms at scale).

## Key terms

- **Lambda's automatic metrics** — `Invocations`, `Errors`, `Throttles`,
  `Duration`, `ConcurrentExecutions`, `IteratorAge`.
- **Cold starts** — visible via the `Init Duration` field in `REPORT`
  log lines.
- **API Gateway dimensions** — `ApiName`, `Stage`, `Resource`, `Method`.
- **DynamoDB metrics** — `ConsumedReadCapacityUnits`, `ThrottledRequests`,
  `UserErrors`, `SystemErrors`.

## Lecture

CloudWatch has first-class metrics for every serverless service. The
key is knowing *which* metric maps to *which* symptom.

### Lambda

| Symptom | Metric | Statistic |
|---|---|---|
| Slow function | `Duration` | p99 |
| Function failing | `Errors` | Sum |
| Function throttled | `Throttles` | Sum |
| Concurrency at limit | `ConcurrentExecutions` | Maximum |
| Stream consumer lagging | `IteratorAge` (only for stream triggers) | Maximum |
| Cold starts | derived from `@initDuration` in `REPORT` | count |

**Cold-start alert** (Logs Insights inside a metric filter):

```
filter @type = "REPORT" and ispresent(@initDuration)
| stats count() as cold_starts by bin(5m)
```

### API Gateway

The `AWS/ApiGateway` namespace is gold:

| Symptom | Metric | Dimensions |
|---|---|---|
| 5xx errors | `5XXError` | `ApiName`, `Stage` |
| 4xx errors | `4XXError` | `ApiName`, `Stage` |
| Latency | `Latency` | p99 |
| Cache hit ratio | `CacheHitCount` / `Count` | (compute in metric math) |

> Enable detailed CloudWatch metrics on the API Gateway stage, or you
> get *only* `Count` and `4XXError`/`5XXError`.

### DynamoDB

| Symptom | Metric | Use |
|---|---|---|
| Throttled (capacity) | `ThrottledRequests` | page on-call |
| Throttled (code) | `UserErrors` | investigate code |
| Hot partition | `ConsumedReadCapacityUnits` (per item) | re-design partition key |
| Replication lag | `ReplicationLatency` (global tables) | depends on SLA |

### A minimal serverless dashboard

| Widget | Source |
|---|---|
| Lambda invocations (line, by fn) | `AWS/Lambda Invocations` Sum |
| Lambda errors (number, big) | `AWS/Lambda Errors` Sum |
| p99 latency (line) | `AWS/ApiGateway Latency` p99 |
| 5xx rate (line) | metric math on `5XXError / Count` |
| DynamoDB throttles (number, big) | `AWS/DynamoDB ThrottledRequests` Sum |
| Cold starts (line) | Logs Insights inside a `log` widget |

This is what a real team's "checkout overview" looks like. We built
the bones of it in L24.

## Hands-on

In your AWS account, build a "Lambda" dashboard with 4 widgets:

1. `Invocations` Sum (line)
2. `Errors` Sum (number)
3. `Duration` p99 (line)
4. `Throttles` Sum (number)

## Quiz prep

- What Lambda metric indicates concurrency saturation?
  (`ConcurrentExecutions`.)
- What dimension lets you slice API Gateway errors by route?
  (`Resource` + `Method`.)
- Which DynamoDB metric indicates capacity throttling?
  (`ThrottledRequests`.)

## Further reading

- `https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html`
- `https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-metrics-and-dimensions.html`

## What's next

L34 — Observability for Containers.
