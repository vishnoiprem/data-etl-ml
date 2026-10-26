---
lecture: L21
title: "Widget Types — Metric, Logs Table, Insights, Text, Stacked"
duration: "13:00"
section: 5
prereqs: ["L20"]
---

# L21 — Widget Types — Metric, Logs Table, Insights, Text, Stacked

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 5 — CloudWatch Dashboards
> **Duration:** 13:00

## Prereqs

L20 (dashboard 101).

## Key terms

- **Metric widget** — line / stacked / number / gauge / pie chart.
- **`view`** — `timeSeries` (line), `singleValue` (big number),
  `gauge`, `bar`, `pie`.
- **`stacked`** — boolean; renders metric lines as stacked areas.
- **Logs widget** — `type: "log"`. Either ad-hoc Logs Insights query
  or a bare `SOURCE` against a log group.
- **Text widget** — `type: "text"` with markdown or HTML.

## Lecture

There are essentially **three widget types**: `metric`, `log`, and
`text`. Each accepts a different `properties` shape.

### 1. Metric widget

```json
{
  "type": "metric",
  "x": 0, "y": 0, "width": 12, "height": 6,
  "properties": {
    "metrics": [
      ["AWS/Lambda", "Invocations", { "stat": "Sum"   }],
      ["AWS/Lambda", "Errors",      { "stat": "Sum"   }],
      ["AWS/Lambda", "Throttles",   { "stat": "Sum"   }]
    ],
    "view": "timeSeries",
    "stacked": false,
    "region": "us-east-1",
    "stat": "Average",
    "period": 300,
    "title": "Lambda health"
  }
}
```

Inside `metrics`, the **tuple format** is
`[Namespace, MetricName, {stat: ..., dimensions: ...}]`. The
`dimensions` key is optional; per-tuple overrides default metric-level
options.

The `view` controls rendering:

| `view` | Renders as |
|---|---|
| `timeSeries` | line / stacked area |
| `singleValue` | one big number |
| `gauge` | dial / progress |
| `bar` | bars |
| `pie` | pie chart |

### 2. Logs Insights widget

```json
{
  "type": "log",
  "x": 0, "y": 6, "width": 24, "height": 8,
  "properties": {
    "query": "SOURCE '/aws/lambda/my-fn' | fields @timestamp, @message | filter @message like /ERROR/ | limit 50",
    "region": "us-east-1",
    "stacked": false,
    "title": "Recent 50 ERRORs"
  }
}
```

Same query language as the Insights editor (L13).

### 3. Bare logs widget (no query)

```json
{
  "type": "log",
  "properties": {
    "query": "SOURCE '/aws/lambda/my-fn'",
    "region": "us-east-1"
  }
}
```

Just shows the latest events from a log group. Use for raw tailing.

### 4. Text widget

```json
{
  "type": "text",
  "properties": {
    "markdown": "# On-call\n\n- PagerDuty: pd.com/team\n- Runbook: wiki/runbooks/web",
    "background": "solid"
  }
}
```

Set `background: "transparent"` to remove the panel box.

### 5. Number widget (single stat)

```json
{
  "type": "metric",
  "properties": {
    "metrics": [["AWS/Lambda", "Errors", { "stat": "Sum", "period": 60 }]],
    "view": "singleValue",
    "title": "Errors (1 min)"
  }
}
```

### Layout tips

| Goal | Layout |
|---|---|
| Hero metric at the top | Row of singleValue widgets |
| Time-series overview | One wide (24×6) line widget |
| Recent logs | Wide (24×8) `log` widget |
| Runbooks / links | Text widget in the corner |

## Hands-on

In your AWS account, open the dashboard you created in L20 and add
three more widgets by editing the JSON via the console (Actions →
View/edit source).

## Quiz prep

- Which `view` renders a number widget? (`singleValue`)
- How do you stack two metric lines into an area chart?
  (`"stacked": true`)
- What's the difference between a `log` widget with a query and one
  without? (With query: tabular results; without: raw tail.)

## Further reading

- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/dashboard/build-dashboard-body-json.html`
- `../../downloads/cloudwatch_widget_json_cheat_sheet.md`.

## What's next

L22 — Cross-Region / Cross-Account Dashboards.
