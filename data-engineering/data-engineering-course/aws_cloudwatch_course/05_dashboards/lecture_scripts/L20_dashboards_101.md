---
lecture: L20
title: "Dashboards 101 — Body JSON, Widget Coordinate System"
duration: "10:00"
section: 5
prereqs: ["L19"]
---

# L20 — Dashboards 101 — Body JSON, Widget Coordinate System

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 5 — CloudWatch Dashboards
> **Duration:** 10:00

## Prereqs

L19 (alarms hands-on).

## Key terms

- **Dashboard body** — the JSON document that describes every widget
  on the dashboard.
- **Widget coordinate** — `x, y, width, height` per widget; origin is
  top-left.
- **`put_dashboard`** — idempotent API call that *replaces* the
  whole dashboard body.
- **`get_dashboard`** — returns the current body + the dashboard's
  ARN.
- **Free-tier dashboards** — the first 3 dashboards (≤ 50 metrics each)
  per region per account are free for 12 months.

## Lecture

A CloudWatch dashboard is a **single JSON document** stored in a
region. The console turns that JSON into a grid of widgets.

### Body shape

```json
{
  "widgets": [
    {"type": "metric", "x": 0,  "y": 0, "width": 12, "height": 6,
     "properties": {...}},
    {"type": "text",   "x": 12, "y": 0, "width": 12, "height": 6,
     "properties": {...}}
  ]
}
```

- The whole document is wrapped in `{"widgets": [...]}`.
- Each widget has `type`, `x`, `y`, `width`, `height`, and `properties`.
- Origin is **top-left**; `y` grows downward.

### Coordinate system rules

1. The grid is **24 columns wide**. Most widgets should use
   multiples of 4 or 6.
2. A widget's `(x, y)` is its **top-left** corner.
3. Widgets **cannot overlap** — if they do, the dashboard won't render.
4. There is **no way to nest** widgets; this isn't HTML.

### Putting a dashboard

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
             "title": "EC2 CPU",
             "stat": "Average",
             "period": 300,
             "view": "timeSeries",
             "region": "us-east-1",
         }},
    ],
}
cw.put_dashboard(
    DashboardName="ec2-overview",
    DashboardBody=json.dumps(body),
)
```

`put_dashboard` is **idempotent** — calling it twice with the same
body produces the same result.

### Common mistakes

1. **`region` inside the widget** — every metric widget must specify
   the region, *unless* the dashboard is in that region. Cross-region
   works but you have to be explicit.
2. **Missing `period`** — defaults to auto, which sometimes looks
   weird (mixed periods between widgets). Always set it.
3. **`type="log"` but no `query`** — the widget will render empty.
4. **Body too big** — maximum body size is 256 KB; for very large
   dashboards, split into multiple.

## Hands-on

In your AWS account:

```python
import json, boto3
cw = boto3.client("cloudwatch")
cw.put_dashboard(
    DashboardName="hello",
    DashboardBody=json.dumps({"widgets": [
        {"type": "text", "x": 0, "y": 0, "width": 24, "height": 4,
         "properties": {"markdown": "# Hello dashboard!"}}
    ]}),
)
cw.get_dashboard(DashboardName="hello")
```

## Quiz prep

- How wide is the dashboard grid in columns? (24)
- Where does `(0, 0)` sit? (Top-left)
- Is `put_dashboard` idempotent? (Yes.)

## Further reading

- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/dashboard/dashboard-api.html`

## What's next

L21 — Widget Types: Metric, Logs Table, Insights, Text, Stacked.
