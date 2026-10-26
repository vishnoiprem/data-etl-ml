# CloudWatch Widget JSON Cheat Sheet

> Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

Dashboards are described by a single JSON document. The body is a list of
top-level widgets. Each widget is `{ "type": ..., "x": ..., "y": ...,
"width": ..., "height": ..., "properties": {...} }`.

## Coordinate system

- Origin `(0, 0)` is **top-left**.
- Grid is 24 columns wide; each widget has `width` 1–24 and `height` 1–∞.
- Y grows downward; widgets cannot overlap.

## Metric widget (line)

```json
{
  "type": "metric",
  "x": 0, "y": 0, "width": 12, "height": 6,
  "properties": {
    "metrics": [
      ["AWS/EC2", "CPUUtilization", "InstanceId", "i-0abc"]
    ],
    "view": "timeSeries",
    "region": "us-east-1",
    "title": "EC2 CPU",
    "stat": "Average",
    "period": 300
  }
}
```

## Stacked area

```json
{
  "type": "metric",
  "x": 0, "y": 6, "width": 12, "height": 6,
  "properties": {
    "view": "timeSeries",
    "stacked": true,
    "metrics": [
      ["AWS/Lambda", "Invocations", { "stat": "Sum" }],
      ["AWS/Lambda", "Errors",      { "stat": "Sum" }]
    ]
  }
}
```

## Logs Insights widget (table)

```json
{
  "type": "log",
  "x": 0, "y": 0, "width": 24, "height": 8,
  "properties": {
    "query": "SOURCE '/aws/lambda/my-fn' | fields @timestamp, @message | filter @message like /ERROR/ | limit 50",
    "region": "us-east-1",
    "title": "Errors (last 50)"
  }
}
```

## Logs table (no query — single log group)

```json
{
  "type": "log",
  "x": 0, "y": 8, "width": 24, "height": 8,
  "properties": {
    "query": "SOURCE '/aws/lambda/my-fn'",
    "region": "us-east-1"
  }
}
```

## Text / markdown widget

```json
{
  "type": "text",
  "x": 12, "y": 0, "width": 12, "height": 6,
  "properties": {
    "markdown": "# On-call dashboard\n\n- **PagerDuty:** pd.com/our-team\n- **Runbook:** wiki/runbooks/web"
  }
}
```

## Number widget (single-stat)

```json
{
  "type": "metric",
  "x": 0, "y": 0, "width": 6, "height": 4,
  "properties": {
    "metrics": [["AWS/Lambda", "Errors", { "stat": "Sum", "period": 60 }]],
    "view": "singleValue"
  }
}
```

## Reference

- See `../05_dashboards/code/create_dashboard.py` for a working
  end-to-end example.
