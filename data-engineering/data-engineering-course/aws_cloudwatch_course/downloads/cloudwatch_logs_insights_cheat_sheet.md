# CloudWatch Logs Insights Cheat Sheet

> Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

## Query language basics

Logs Insights uses a SQL-like language. The two core commands are `fields`
and `filter`; you almost always finish with `stats` or `sort`/`limit`.

```
fields @timestamp, @message, @logStream
| filter @message like /ERROR/
| stats count() as err_count by bin(5m)
| sort err_count desc
| limit 20
```

## Useful functions

| Function | Purpose |
|---|---|
| `bin(period)` | Time-bucket rows (e.g. `bin(5m)`, `bin(1h)`) |
| `parse @message "..."` | Extract fields via regex (grok-style) |
| `strcontains(field, "x")` | Substring search |
| `ispresent(field)` | Truthy test |
| `count()`, `sum()`, `avg()`, `max()`, `min()` | Aggregates |
| `percentile(field, p)` | p99, p95, etc. |
| `diff(seconds)` | Time-since-last-event (for stale alarms) |
| `coalesce(a, b)` | First non-null |

## 30+ ready-made queries

### 1. Top 10 error messages (last 1h)

```
fields @timestamp, @message
| filter @message like /ERROR|Exception/
| stats count() as n by @message
| sort n desc
| limit 10
```

### 2. p99 latency per Lambda function

```
fields @timestamp, @duration
| filter @type = "REPORT"
| stats percentile(@duration, 99) as p99 by bin(5m)
```

### 3. Cold-start count per Lambda

```
fields @timestamp, @initDuration
| filter ispresent(@initDuration)
| stats count() as cold_starts by bin(5m)
```

### 4. API Gateway 5xx rate

```
fields @timestamp, @status
| filter @status >= 500
| stats count() as n5xx by bin(1m)
```

### 5. Number of unique requesters

```
fields @timestamp, @remoteAddr
| stats count_distinct(@remoteAddr) as uniq
```

## Reference

- See `../03_logs/lecture_scripts/L13_insights.md` for the full language walk-through.
- See `../05_dashboards/code/create_dashboard.py` for using a query inside a widget.
