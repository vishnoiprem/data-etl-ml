---
lecture: L23
title: "`put_dashboard` + `get_dashboard` with boto3"
duration: "12:00"
section: 5
prereqs: ["L22"]
---

# L23 — `put_dashboard` + `get_dashboard` with boto3

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 5 — CloudWatch Dashboards
> **Duration:** 12:00

## Prereqs

L22 (cross-region / cross-account).

## Key terms

- **`put_dashboard`** — accepts a `DashboardName`, `DashboardBody`
  (JSON string), and optionally a list of `DashboardNames` to update.
- **`DashboardBody`** — must be a JSON string. You build it with
  `json.dumps(body)` after assembling it as a Python dict.
- **`get_dashboard`** — returns the body as a JSON string in
  `DashboardBody`. Re-parse with `json.loads`.
- **`delete_dashboards`** — accepts one or more names.
- **`list_dashboards`** — paginated list of dashboard names + ARNs.

## Lecture

The two API calls you'll use 95% of the time for dashboards:

### `put_dashboard`

```python
import json
import boto3

cw = boto3.client("cloudwatch")

body = {
    "widgets": [
        {"type": "metric",
         "x": 0, "y": 0, "width": 24, "height": 6,
         "properties": {
             "metrics": [["AWS/EC2", "CPUUtilization", "InstanceId", "i-0abc"]],
             "view": "timeSeries",
             "region": "us-east-1",
             "title": "EC2 CPU",
             "stat": "Average",
             "period": 300,
         }},
    ]
}
resp = cw.put_dashboard(
    DashboardName="ec2-overview",
    DashboardBody=json.dumps(body),
)
print(resp["DashboardValidationMessages"])
# [] means the body is valid; non-empty means there were warnings.
```

`put_dashboard` returns a list of *validation messages*. These are
warnings (e.g. "metric doesn't exist yet") rather than errors. The
dashboard is still saved.

### `get_dashboard`

```python
resp = cw.get_dashboard(DashboardName="ec2-overview")
body = json.loads(resp["DashboardBody"])
print(resp["DashboardArn"], body["widgets"][0]["type"])
```

The body comes back as the raw JSON string you originally sent.
Re-parse it to inspect / mutate.

### `delete_dashboards`

```python
cw.delete_dashboards(DashboardNames=["ec2-overview"])
```

Accepts a list of names; deletes them all in one call.

### `list_dashboards`

```python
paginator = cw.get_paginator("list_dashboards")
for page in paginator.paginate():
    for entry in page["DashboardEntries"]:
        print(entry["DashboardName"], entry["DashboardArn"])
```

### Validation

CloudWatch never rejects a `put_dashboard` because of a typo in the
body. It happily saves a body that references a metric that doesn't
exist; the widget just renders "No data". Always inspect
`DashboardValidationMessages` and make sure it's empty.

### Putting it together (idempotent pattern)

```python
def upsert_dashboard(name, widgets):
    body = {"widgets": widgets}
    cw.put_dashboard(
        DashboardName=name,
        DashboardBody=json.dumps(body),
    )
```

Re-running `upsert_dashboard` with the same widgets produces the
same dashboard.

## Hands-on

We'll wire this all up in `create_dashboard.py` (L24). For now, run
the snippets above against your AWS account.

## Quiz prep

- What's the type of `DashboardBody`? (JSON string, not a Python dict.)
- How do you receive validation warnings? (In the response from
  `put_dashboard`.)
- What does `delete_dashboards` accept? (A list of names.)

## Further reading

- `https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html`
- `../../downloads/cloudwatch_widget_json_cheat_sheet.md` — full
  widget reference.

## What's next

L24 — Hands-on: build `create_dashboard.py` + 4 moto tests.
