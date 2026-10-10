---
lecture: L02
title: "The Three Pillars of Observability (Metrics / Logs / Traces)"
duration: "12:00"
section: 1
prereqs: ["L01"]
---

# L02 — The Three Pillars of Observability

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 1 — Foundations
> **Duration:** 12:00

## Prereqs

L01 (course intro). No AWS or coding experience required.

## Key terms

- **Metric** — a numeric time-series measurement (e.g. `CPUUtilization=72`
  at 14:00:00). Cheap, aggregate-friendly, the primary signal for
  alerting.
- **Log** — a discrete, structured or unstructured event emitted by a
  service (e.g. `2026-10-10 14:00:00 ERROR user_id=42 login failed`).
  High-fidelity but expensive; best for debugging.
- **Trace** — a single end-to-end request as it fans out across services,
  broken into **spans** with timing and causality. AWS X-Ray handles this.
- **RED method** — Rate / Errors / Duration, three core service metrics.
- **USE method** — Utilization / Saturation / Errors, three core
  *resource* metrics.

## Lecture

The phrase "**three pillars of observability**" was coined by Peter
Bourgeois in 2017 and is now industry standard. The pillars are
**metrics**, **logs**, and **traces**. CloudWatch covers the first two
natively and integrates with **AWS X-Ray** for the third.

### Why three pillars, not one?

Each pillar answers a different question:

| Pillar | Question | Cost | Cardinality |
|---|---|---|---|
| **Metrics** | *How much? How often?* | Cheap | Low / bounded |
| **Logs** | *Why? What happened to this specific request?* | Expensive | High / unbounded |
| **Traces** | *Where in the call graph did it go wrong?* | Medium | Medium |

You cannot answer "is the API fast?" from a single log line, and you
cannot answer "why did this one user's request fail?" from a single
metric. You need both. Traces fill the gap *between* the two: "this
specific request went through auth → user-svc → order-svc and spent 2.3
s in order-svc."

### Metrics in CloudWatch

- Stored as time-series in a **namespace / metric name / dimensions**
  triple.
- Each data point is a `(timestamp, value, unit)` triple, optionally
  tagged with a statistic set (min/max/sum/sample-count) that lets
  CloudWatch aggregate in 1 min or 1 sec resolution.
- **Use for:** dashboards, alarms, auto-scaling, anomaly detection.

```python
# Put a custom metric (we'll see this for real in L08)
cw = boto3.client("cloudwatch")
cw.put_metric_data(
    Namespace="MyApp",
    MetricData=[{
        "MetricName": "LatencyMs",
        "Value": 87.4,
        "Unit": "Milliseconds",
        "Timestamp": datetime.utcnow(),
    }],
)
```

### Logs in CloudWatch

- Organised in **log groups** (typically one per service) and **log
  streams** (typically one per instance, container, or function).
- Each event is a `(timestamp, message)` pair; `message` can be plain
  text or structured JSON.
- **Use for:** debugging, audit trails, compliance, ad-hoc queries via
  Logs Insights.

```python
logs = boto3.client("logs")
logs.put_log_events(
    logGroupName="/myapp/api",
    logStreamName="i-0abc",
    logEvents=[{
        "timestamp": int(time.time() * 1000),
        "message": "ERROR user=42 login failed",
    }],
)
```

### Traces — X-Ray (we will *not* deep-dive)

- **CloudWatch ServiceLens** shows X-Ray traces alongside metrics and
  logs.
- X-Ray is its own service with its own SDK; we mention it here for
  completeness but it is *not* part of the CloudWatch Crash Course.
- If you want a deep-dive on X-Ray, see the *AWS X-Ray Crash Course*
  companion.

### RED vs. USE

Peter Bourgaux (USE) and Tom Wilkie (RED) coined two complementary
methodologies:

- **RED** — for *services*: Rate, Errors, Duration.
- **USE** — for *resources*: Utilization, Saturation, Errors.

CloudWatch's pre-built dashboards for EC2 / RDS / Lambda follow USE;
service-level dashboards you build in section 5 will follow RED.

## Hands-on

No lab in this lecture. In L03 we'll look at the CloudWatch console
itself; in L08 you'll write your first `put_metric_data` call.

## Quiz prep

- What are the three pillars of observability? (Metrics / Logs / Traces)
- Which two are native to CloudWatch? (Metrics / Logs)
- Which AWS service covers traces? (X-Ray)

## Further reading

- AWS whitepaper: *Observability with Amazon CloudWatch*.
- Google SRE book, chapter 6: *Globally Distributed Monitoring*.
- `../../downloads/cloudwatch_cheat_sheet.md`.

## What's next

L03 — CloudWatch Service Overview, Pricing & Free Tier.
