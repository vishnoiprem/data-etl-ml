---
lecture: L11
title: "Log Events, Timestamps, Ingestion, Storage Costs"
duration: "12:00"
section: 3
prereqs: ["L10"]
---

# L11 — Log Events, Timestamps, Ingestion, Storage Costs

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 3 — CloudWatch Logs
> **Duration:** 12:00

## Prereqs

L10 (log groups / streams).

## Key terms

- **Log event** — a single `(timestamp, message)` pair, ≤ 256 KB. Plain
  text or JSON.
- **Ingestion** — bytes *received* via `put_log_events`, agent, or
  Lambda. Billed per GB.
- **Storage** — bytes *kept* (after retention). Billed per GB-month.
- **`@timestamp` / `@message`** — implicit fields available in Logs
  Insights.
- **Structured (JSON) log** — a log event whose `message` is a JSON
  document. Logs Insights can extract any field without regex.

## Lecture

A log event has exactly two parts:

| Field | Type | Notes |
|---|---|---|
| `timestamp` | unix milliseconds | required; the *event* time, not ingestion time |
| `message` | string (≤ 256 KB) | required; usually JSON, sometimes plain text |

CloudWatch also adds two implicit fields you can query in Insights:

- `@timestamp` — same as `timestamp`.
- `@message` — same as `message`.
- `@logStream` — the stream the event came from.
- `@log` — the log group the event came from.

### Plain text vs. structured (JSON)

**Plain text** is fine for human consumption but terrible for querying:

```
2026-10-10 14:23:01 INFO user=42 path=/checkout status=200 latency_ms=87
```

**Structured JSON** is the right choice for production:

```json
{"ts": "2026-10-10T14:23:01Z", "level": "INFO", "user": 42,
 "path": "/checkout", "status": 200, "latency_ms": 87}
```

In Logs Insights you can then write:

```
fields @timestamp, user, status, latency_ms
| filter status >= 500
| stats avg(latency_ms) by user
```

…without any regex.

### Cost model

CloudWatch Logs bills in two ways:

| Item | Cost |
|---|---|
| Ingestion (per GB) | $0.50 |
| Storage (per GB-month) | $0.03 |
| Insights queries (per GB scanned) | $0.005 |

> **Gotcha:** Ingestion is *uncompressed* bytes. A 200-byte JSON event
> counts as 200 bytes, not the ~50 bytes it would compress to. If you
> care about cost, store bulky fields in S3, not Logs.

### Log levels

There is no first-class concept of "log level" in CloudWatch Logs.
Conventions:

- Use a JSON `level` field (`"DEBUG"`, `"INFO"`, `"WARN"`, `"ERROR"`).
- Filter via a metric filter (L13) to count errors.
- Use a subscription filter (section 6) to ship ERRORs to a separate
  stream.

### Lambda's automatic log event

Lambda automatically emits a `REPORT` line at the end of every
invocation:

```
REPORT RequestId: 8ee9... Duration: 87.42 ms Billed Duration: 88 ms
Memory Size: 128 MB Max Memory Used: 75 MB  Init Duration: 41.12 ms
```

The `REPORT` line is the source of `Duration` and `Errors` metrics in
the `AWS/Lambda` namespace. We exploit this in L13 to compute cold
starts.

## Hands-on

In your AWS account:

1. Open *CloudWatch → Logs → Log groups* → pick any Lambda log group.
2. Find a `REPORT` line and observe the `Billed Duration` and `Memory
   Used` fields.
3. Now write a structured event yourself:

```python
import boto3, json, time
logs = boto3.client("logs")
logs.put_log_events(
    logGroupName="/myapp/demo",
    logStreamName="demo-stream",
    logEvents=[{
        "timestamp": int(time.time() * 1000),
        "message": json.dumps({
            "level": "INFO",
            "msg": "demo event",
            "user": 42,
        }),
    }],
)
```

## Quiz prep

- What's the max size of a log event? (256 KB)
- What's the difference between ingestion cost and storage cost?
  (Ingestion = bytes received once; storage = bytes kept per month.)
- How do you query a JSON field without a regex in Logs Insights?
  (Use the field name directly: `fields user, status`)

## Further reading

- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html`

## What's next

L12 — `create_log_group` + `put_log_events` + `filter_log_events` with boto3.
