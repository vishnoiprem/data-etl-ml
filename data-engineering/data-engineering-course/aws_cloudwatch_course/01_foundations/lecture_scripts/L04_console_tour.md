---
lecture: L04
title: "Console Tour — Metrics, Logs, Alarms, Dashboards"
duration: "5:00"
section: 1
prereqs: ["L03"]
---

# L04 — Console Tour — Metrics, Logs, Alarms, Dashboards

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 1 — Foundations
> **Duration:** 5:00

## Prereqs

L03 (CloudWatch overview / pricing).

## Key terms

- **Left-nav** — the rail on the left of the CloudWatch console. Each
  sub-service gets a section; some are collapsed by default.
- **Region selector** — top-right of every console page. CloudWatch is a
  per-region service.
- **"Graphed metrics" tab** — the canvas where you stack metric series
  and choose statistics / periods.
- **Logs Insights query editor** — the SQL-like box at
  *Logs → Insights*.

## Lecture

This lecture is the shortest of the course, but it earns its slot: a
5-minute fly-through of the CloudWatch console so you know where to
find each sub-service before we deep-dive in sections 2–5.

### Top-level navigation

When you open CloudWatch, the left-nav reads (with the ones we'll
actually use in **bold**):

- **Metrics** — list, search, graph
- **Logs** — log groups, log streams, **Logs Insights**
- **Alarms** — list, history
- **Dashboards** — your dashboards
- Events → **EventBridge** rules (technically its own service)
- Synthetics
- Application Monitoring → **ServiceLens**, **RUM**
- **Settings** → *Configure* (cross-account, cross-region)

### Metrics view

*Metrics → All metrics* shows a tree:

```
AWS namespaces
├── EC2
│   └── Per-Instance Metrics
├── Lambda
│   └── Function Name
├── RDS
│   └── DB Instance Identifier
└── [your custom namespaces]
```

Tick a metric → it appears in the **Graphed metrics** tab at the top.
You can change **statistic** (avg, p99, sum, …), **period** (1m, 5m,
1h), and **graph type** (line, stacked area, number, pie, bar) without
leaving the page.

### Logs view

*Logs → Log groups* shows every log group in the region. Click a
group → see its streams → click a stream → see the events.

*Logs → Insights* opens the Logs Insights editor. The default query is
empty; type:

```
fields @timestamp, @message
| limit 20
```

…and click **Run**. The query is free for the first 5 GB scanned / month.

### Alarms view

*Alarms → All alarms* lists every alarm with its current **state** (OK
/ ALARM / INSUFFICIENT_DATA), threshold, period, and target actions.
Click an alarm → see its history of state transitions (the "alarm
timeline").

### Dashboards view

*Dashboards → [name]* shows your dashboards. The **Actions** menu
lets you view source JSON, share, or delete. We build our first
dashboard programmatically in section 5.

### Region / cross-region

CloudWatch is **per-region**. If you create an alarm in `us-east-1`,
it cannot see a metric in `eu-west-1`. To get a global view you either:

1. Use a **cross-region dashboard** (CloudWatch feature since 2021).
2. Use **CloudWatch cross-account observability** (since 2022).

We cover both briefly in L22.

## Hands-on

Open the CloudWatch console in your AWS account:

1. Pick any EC2 instance that has been running for a few minutes.
2. *Metrics → All metrics → EC2 → Per-Instance Metrics* → tick
   `CPUUtilization` for the instance.
3. Switch statistic from **Average** to **p99** in the Graphed metrics
   tab. (p99 requires 1-min or finer resolution; you may need to enable
   detailed monitoring for the instance to see real data — we'll do
   that in section 2.)
4. Navigate to *Logs → Log groups* and find a Lambda function's log
   group (if you have any). Open the most recent log stream.

That's it. From L05 onward we work programmatically with `boto3`.

## Quiz prep

- Where in the console do you change a metric's statistic?
  (Graphed metrics tab → dropdown)
- Where do you find an alarm's state-transition history?
  (Alarm detail page → History tab)
- Where do you find the Logs Insights query editor?
  (*Logs → Insights* in the left-nav)

## Further reading

- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html`
- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html`

## What's next

Section 2 — CloudWatch Metrics, starting with **L05 — Metrics 101**.
