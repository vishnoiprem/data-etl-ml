---
lecture: L22
title: "Cross-Region / Cross-Account Dashboards"
duration: "10:00"
section: 5
prereqs: ["L21"]
---

# L22 — Cross-Region / Cross-Account Dashboards

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 5 — CloudWatch Dashboards
> **Duration:** 10:00

## Prereqs

L21 (widget types).

## Key terms

- **Cross-region widget** — a single widget can query a metric from a
  different region by specifying `"region"` in its properties.
- **Cross-account observability** — since 2022, you can configure one
  account (the *monitoring account*) to view metrics and logs from N
  *source accounts*.
- **CloudWatch cross-account console** — the *Source accounts* page in
  the monitoring account lists the source accounts it's watching.
- **Centralised dashboards** — common pattern: one
  "monitoring/observability" account owns the dashboards; every
  workload account is a *source*.

## Lecture

Most teams standardise on a single *observability* account where all
the dashboards live. The trick is wiring it up.

### Cross-region (same account)

Set `"region": "eu-west-1"` (or any region) inside any metric/log
widget. The dashboard renders metrics from that region even though
the dashboard itself lives in `us-east-1`.

```json
{
  "type": "metric",
  "properties": {
    "metrics": [["AWS/Lambda", "Errors"]],
    "view": "timeSeries",
    "region": "eu-west-1"     # ← cross-region
  }
}
```

Gotcha: the **dashboard itself** is still regional. You cannot view a
`us-east-1` dashboard from `eu-west-1`; only its widgets can pull
cross-region.

### Cross-account (multi-account)

For multi-account setups (orgs with central ops + many workload
accounts), the model is:

```
Workload account (source)  ─────►  Observability account (monitoring)
   - emits metrics                          - owns dashboards
   - emits logs                             - pulls via cross-account
   - allows the monitoring account
```

Concrete steps:

1. **In the workload account**, run:
   ```bash
   aws iam create-service-linked-role \
       --aws-service-name observability.cloudwatch.amazonaws.com
   ```
2. **In the observability account**, call
   `PutAccountConfiguration` with the workload account ID.
3. The observability account can now see metrics / logs from the
   workload account.

For dashboards, the same `region` field inside a widget is how you
specify "watch metric from account X in region Y". The console has a
*Linked accounts* panel for this.

### Gotchas

1. **Logs from another account are *not* free.** They cross S3-style
   pricing buckets — usually < $0.01/GB but check.
2. **Cross-account Insights** has different limits (1 GB scanned per
   query, 30 days max).
3. **Cross-account alarms** must use SNS topics in the same account
   as the alarm. If you want to page from the observability account,
   the topic lives there.

## Hands-on

In your AWS account, add a cross-region widget to your existing
dashboard:

```json
{"type": "metric", "x": 0, "y": 0, "width": 12, "height": 6,
 "properties": {
   "metrics": [["AWS/Lambda", "Invocations"]],
   "view": "timeSeries",
   "region": "eu-west-1"
 }}
```

## Quiz prep

- Can a dashboard itself be cross-region? (No; only its widgets can.)
- What AWS service manages the cross-account observability
  relationship? (CloudWatch's own cross-account feature.)
- Where must an SNS topic live relative to its alarm? (Same account.)

## Further reading

- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Unified-Cross-Account.html`

## What's next

L23 — `put_dashboard` + `get_dashboard` with boto3.
