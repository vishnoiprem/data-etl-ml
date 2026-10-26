---
lecture: L24
title: "Hands-on: build `create_dashboard.py` + 4 moto tests"
duration: "10:00"
section: 5
prereqs: ["L23"]
---

# L24 — Hands-on: build `create_dashboard.py` + 4 moto tests

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 5 — CloudWatch Dashboards
> **Duration:** 10:00

## Prereqs

L23 (`put_dashboard`).

## Key terms

(All covered in L20–L23.)

## Lecture

This lecture walks you through `05_dashboards/code/create_dashboard.py`
and its 4 moto tests.

### What the script does

Builds a 3-widget dashboard `checkout-overview`:

1. **Metric widget** — `AWS/ApiGateway Latency p99` for `checkout`.
2. **Logs Insights widget** — top 20 ERRORs in
   `/aws/lambda/checkout` over the last hour.
3. **Text widget** — runbook markdown (runbook URL, on-call link).

The script calls `put_dashboard` (idempotent), `get_dashboard`, and
prints a summary of each widget.

### How to run

```bash
cd aws_cloudwatch_course
python3 05_dashboards/code/create_dashboard.py
# or:
python3 05_dashboards/code/create_dashboard.py --dry-run
```

Required IAM permissions (real AWS):

```
cloudwatch:PutDashboard
cloudwatch:GetDashboard
cloudwatch:DeleteDashboards
cloudwatch:ListDashboards
```

### How the tests work

`test_create_dashboard.py` uses `moto.mock_aws`. Four tests cover:

1. `test_create_dashboard_creates_three_widgets` — body has 3
   widgets.
2. `test_get_dashboard_returns_expected_body` — round-trip preserves
   the JSON.
3. `test_widget_types_are_correct` — widgets are of types
   `metric`, `log`, `text`.
4. `test_dry_run_does_not_call_put_dashboard` — `--dry-run`
   suppresses the call.

### Run the tests

```bash
cd aws_cloudwatch_course
python3 -m pytest 05_dashboards/code/ -v
```

4 tests pass in < 1 second.

## Hands-on

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-engineering-course/aws_cloudwatch_course
python3 05_dashboards/code/create_dashboard.py
python3 -m pytest 05_dashboards/code/ -v
```

## Quiz prep

- How many widgets does the demo build? (3.)
- Are the widget types `metric / log / text`? (Yes.)
- Is `put_dashboard` idempotent? (Yes.)

## Further reading

- `05_dashboards/code/create_dashboard.py` — the script.
- `05_dashboards/code/test_create_dashboard.py` — the tests.

## What's next

Section 6 — Logs Insights + Subscriptions + Kinesis / Firehose.
