---
lecture: L35
title: "Course Wrap-up & Where to Go Next"
duration: "5:00"
section: 7
prereqs: ["L34"]
---

# L35 — Course Wrap-up & Where to Go Next

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 7 — Real-World Patterns
> **Duration:** 5:00

## Prereqs

L34 (containers).

## Recap of what you learned

In 35 lectures, you've built a complete mental model of CloudWatch:

| Section | Skill |
|---|---|
| 1 | Three pillars, pricing, console tour |
| 2 | Custom metrics, resolution, statistics, p99 |
| 3 | Log groups, retention, Insights, time-windowed reads |
| 4 | Metric / composite / anomaly alarms, SNS actions |
| 5 | Dashboards with metric / log / text widgets |
| 6 | Subscription filters, Kinesis / Firehose / Lambda destinations |
| 7 | SLOs, cost, alarms at scale, serverless + containers |

You have **5 working `boto3 + moto` demos** (≥ 23 moto tests passing
total) and **1 graded assignment** (SLO dashboard with burn-rate
alerts).

## Where to go next

### Within the AWS data-engineering family

- **AWS Lambda Crash Course** — Lambda is the most common producer
  of CloudWatch metrics and logs. The two courses pair naturally.
- **AWS Glue Crash Course** — Glue jobs emit metrics into
  `AWS/Glue`; the same dashboards + alarms pattern applies.
- **AWS EventBridge Crash Course** — EventBridge is the event
  bus that often *triggers* the Lambda functions you'll watch.
- **AWS Step Functions Crash Course** — Step Functions emit
  `AWS/States` metrics; you can alarm on `ExecutionsFailed`.

### Within the CloudWatch family

- **X-Ray Crash Course** — for traces (the third pillar). ServiceLens
  ties it to CloudWatch metrics + logs.
- **CloudWatch Synthetics** — for canary checks of public URLs.
- **CloudWatch RUM** — for web-vitals from real users.
- **CloudWatch ServiceLens** — the unified view tying X-Ray to
  CloudWatch.

### Beyond CloudWatch

- **Datadog / New Relic / Grafana Cloud** — richer per-pod / per-Lambda
  telemetry, often with APM, RUM, and synthetics in one product.
  CloudWatch is the cheapest and most integrated; the third-party
  tools are richer and have higher per-host cost.
- **Prometheus + Grafana** — for Kubernetes-heavy workloads.
  CloudWatch Container Insights overlaps with Prometheus but Grafana's
  dashboards are more flexible.
- **Honeycomb / Lightstep** — for high-cardinality event-based
  observability. Different paradigm from CloudWatch metrics.

### What to read

- *Google SRE Workbook*, chapters 5–6 (alerting on SLOs, monitoring
  distributed systems).
- *CloudWatch docs*, especially the deep-dives on metric math and
  cross-account observability.
- *The Morning Paper* (Adrian Colyer) — random selection of
  observability papers for breadth.

### What to do

1. Run the 5 demos locally; **moto** lets you do this without an
   AWS account.
2. Wire the metrics + alarms + dashboard into one of your own
   services.
3. Try the **assignment_1_slo_dashboard.md** in your own account.
4. Subscribe a personal email to a test SNS topic and watch the
   end-to-end flow fire.

## Thank you

Thanks for taking the **AWS CloudWatch Crash Course**. If you
have questions or feedback, open an issue on the repo or email me at
**pvishnoi@avilx.com**.

Happy monitoring.
