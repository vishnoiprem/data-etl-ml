---
lecture: L32
title: "Alarms at Scale — naming, tags, multi-account"
duration: "10:00"
section: 7
prereqs: ["L31"]
---

# L32 — Alarms at Scale — naming, tags, multi-account

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 7 — Real-World Patterns
> **Duration:** 10:00

## Prereqs

L31 (cost optimization).

## Key terms

- **Naming convention** — `<severity>-<service>-<signal>-<condition>`,
  e.g. `p2-checkout-5xx-rate-high`.
- **Tag strategy** — `Severity`, `Team`, `Service`, `Oncall`. CloudWatch
  alarms support tags.
- **Composite alarm** — one pager-facing alarm per service; leaves
  are private.
- **PagerDuty / Opsgenie integration** — SNS → Lambda → vendor API.

## Lecture

When you have 5 alarms you can wing it. When you have 500 you need a
strategy.

### Naming convention

```
<severity>-<service>-<signal>-<condition>

p1-checkout-5xx-rate-high        (pager-worthy, 5xx > 1% in 5 min)
p2-checkout-p99-latency-high     (pager-worthy, p99 > 500ms in 5 min)
p3-checkout-error-budget-slow    (slow-burn alert)
```

Severity prefixes let you filter in the console / in scripts:

```bash
aws cloudwatch describe-alarms \
  --alarm-name-prefix p1- \
  --query 'MetricAlarms[].AlarmName'
```

### Tag strategy

CloudWatch alarms support tags. Apply these:

| Tag | Example |
|---|---|
| `Severity` | `p1`, `p2`, `p3` |
| `Team` | `payments` |
| `Service` | `checkout-api` |
| `Oncall` | `payments-oncall` |
| `SLO` | `availability-99.9` |
| `AutoResolve` | `true` / `false` |

```python
cw.tag_resource(
    ResourceARN=alarm_arn,
    Tags=[{"Key": "Severity", "Value": "p1"},
          {"Key": "Team",     "Value": "payments"}],
)
```

### Composite pattern

One *pager-facing* composite alarm per service. All the leaves are
internal and not paged directly.

```python
cw.put_composite_alarm(
    AlarmName="p1-checkout-page",
    AlarmRule=(
        "ALARM(checkout-5xx-high) OR "
        "ALARM(checkout-p99-latency-high) OR "
        "ALARM(checkout-error-budget-fast-burn)"
    ),
    AlarmActions=[oncall_topic],
)
```

The leaves still exist (useful for debug dashboards) but they don't
page on-call.

### Multi-account

For orgs with many workload accounts:

- The **monitoring account** owns the dashboards and the on-call
  topic.
- Workload accounts emit metrics + logs; cross-account observability
  routes them.
- The on-call topic lives in the monitoring account.

This keeps paging out of any single workload account's blast radius.

### Health dashboard pattern

Build a top-level "org health" dashboard that lists, for every
service, the current state of its composite alarm. A single
`number` widget per service with `singleValue` rendering gives a
green / red / yellow grid for the whole company.

## Hands-on

In your AWS account:

1. Add a `Severity` tag to two existing alarms.
2. Filter the alarms list by tag (CLI: `--query`).
3. If you have multiple alarms for the same service, group them
   under a composite.

## Quiz prep

- What's the canonical alarm-name format?
  (`<severity>-<service>-<signal>-<condition>`)
- What does a composite alarm do? (Combines other alarms with
  boolean logic.)
- Where should the on-call topic live in a multi-account setup?
  (In the monitoring account.)

## Further reading

- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/alarm-changes.html`

## What's next

L33 — Observability for Serverless.
