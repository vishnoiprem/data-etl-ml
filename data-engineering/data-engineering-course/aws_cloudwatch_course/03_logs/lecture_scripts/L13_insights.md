---
lecture: L13
title: "CloudWatch Logs Insights — query language primer"
duration: "10:00"
section: 3
prereqs: ["L12"]
---

# L13 — CloudWatch Logs Insights — query language primer

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 3 — CloudWatch Logs
> **Duration:** 10:00

## Prereqs

L12 (`put_log_events` / `filter_log_events`).

## Key terms

- **Logs Insights** — a SQL-like query language for CloudWatch Logs.
- **`SOURCE`** — keyword to pick a log group: `SOURCE '/aws/lambda/my-fn'`.
- **Pipe syntax** — every command after the source is separated by `|`.
- **`stats`** — aggregate functions (`count`, `sum`, `avg`, `p99`).
- **`bin(period)`** — time-bucket rows.
- **Implicit fields** — `@timestamp`, `@message`, `@logStream`, `@log`.

## Lecture

Logs Insights is a query engine that runs *server-side* over your log
groups. You don't download the data; you send a query, and CloudWatch
returns tabular results. It's the right tool for **ad-hoc
investigation** and **dashboard panels**.

### Query anatomy

```
SOURCE logGroupName(...)
| fields @timestamp, @message, level, status
| filter status >= 500
| stats count() as err_count by bin(5m)
| sort err_count desc
| limit 10
```

Every query has the form `<source> | <command> | <command> ...`. The
five commands you'll use 95% of the time:

| Command | Purpose | Example |
|---|---|---|
| `fields` | pick columns | `fields @timestamp, @message, level` |
| `filter` | keep only rows that match | `filter level = "ERROR"` |
| `stats` | aggregate | `stats count() as n by level` |
| `sort` | order results | `sort n desc` |
| `limit` | top-N | `limit 50` |

### The two source formats

```
SOURCE '/aws/lambda/my-fn'                            -- one group
SOURCE logGroups([ '/aws/lambda/api', '/aws/lambda/web' ])   -- many
```

### Five essential queries

**1. Top error messages**

```
SOURCE '/aws/lambda/api'
| fields @timestamp, @message
| filter @message like /ERROR|Exception/
| stats count() as n by @message
| sort n desc
| limit 10
```

**2. p99 Lambda duration (last 1h, 1-min buckets)**

```
SOURCE '/aws/lambda/api'
| fields @timestamp, @duration
| filter @type = "REPORT"
| stats percentile(@duration, 99) as p99 by bin(1m)
| sort @timestamp asc
```

**3. Cold-start count per minute**

```
SOURCE '/aws/lambda/api'
| filter @type = "REPORT" and ispresent(@initDuration)
| stats count() as cold_starts by bin(5m)
```

**4. 5xx rate per minute (API Gateway)**

```
SOURCE '/aws/lambda/api'
| fields @timestamp, @status
| filter @status >= 500
| stats count() as n5xx by bin(1m)
```

**5. Recent 50 ERRORs (table-style)**

```
SOURCE '/aws/lambda/api'
| filter @message like /ERROR/
| fields @timestamp, @message
| sort @timestamp desc
| limit 50
```

### When to use Insights vs. `filter_log_events`

| Use case | Right tool |
|---|---|
| "Search for the string 'ERROR' in the last hour" | `filter_log_events` |
| "Group errors by minute for the last 24h" | Logs Insights |
| "Tail the latest 20 events" | `get_log_events` |
| "Show me p99 latency per minute in a dashboard" | Logs Insights inside a `log` widget |
| "Scan every log for a credit-card number" (compliance) | `filter_log_events` with PII filter |

### Limitations

- A single Insights query can run for **up to 60 minutes** and scan
  **up to 30 days** of data.
- You cannot join across log groups and time periods inside one query
  (you can do it across groups, but the time window is global).
- The query language is **not SQL** — there's no `JOIN`, no subquery.

## Hands-on

In the CloudWatch console:

1. *Logs → Insights* → pick a Lambda function's log group.
2. Paste query 1 (top error messages) and click **Run**.
3. Add a number widget with the same query (we'll do this in L23).

## Quiz prep

- What does `bin(5m)` do? (Time-bucket rows into 5-minute windows.)
- What's the difference between Insights and `filter_log_events`?
  (Insights is server-side SQL-like; `filter_log_events` is in-process.)
- How long can a single Insights query run? (60 minutes.)

## Further reading

- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html`
- `../../downloads/cloudwatch_logs_insights_cheat_sheet.md` — 30+
  ready-made queries.

## What's next

L14 — Hands-on: build `create_log_group.py` + 5 moto tests.
