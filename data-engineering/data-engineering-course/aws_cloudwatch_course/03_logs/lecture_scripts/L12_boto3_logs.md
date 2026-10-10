---
lecture: L12
title: "`create_log_group` + `put_log_events` + `filter_log_events`"
duration: "18:00"
section: 3
prereqs: ["L11"]
---

# L12 — `create_log_group` + `put_log_events` + `filter_log_events`

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 3 — CloudWatch Logs
> **Duration:** 18:00

## Prereqs

L11 (log events / cost model). Comfortable with `boto3`.

## Key terms

- **`create_log_group`** — creates a log group. Idempotent
  (`ResourceAlreadyExistsException` is *not* raised; it's a success).
- **`create_log_stream`** — creates a log stream inside a group.
  Idempotent.
- **`put_log_events`** — appends up to 1 MB / 10,000 events per call.
  Requires a `sequenceToken` after the first call.
- **`filter_log_events`** — searches events by time, log-stream-name,
  and (optionally) a filter pattern. Paginated.
- **`get_log_events`** — reads events sequentially from a stream.
  Different from `filter_log_events`; mostly used for tailing.

## Lecture

The three API calls you'll use 95% of the time:

### `create_log_group` / `create_log_stream`

```python
import boto3
logs = boto3.client("logs")

# 1. Create a log group
logs.create_log_group(logGroupName="/myapp/api")

# 2. Set a retention policy
logs.put_retention_policy(logGroupName="/myapp/api", retentionInDays=30)

# 3. Create a stream
logs.create_log_stream(logGroupName="/myapp/api", logStreamName="i-0abc")
```

> `create_log_group` is **idempotent** — re-running the call does not
> raise. CloudWatch silently no-ops. You don't need a try/except for
> `ResourceAlreadyExistsException`.

### `put_log_events`

```python
import time, json
resp = logs.put_log_events(
    logGroupName="/myapp/api",
    logStreamName="i-0abc",
    logEvents=[{
        "timestamp": int(time.time() * 1000),
        "message": json.dumps({"level": "INFO", "user": 42, "msg": "hi"}),
    }],
)
# resp["nextSequenceToken"] is required for the next call
```

A few rules:

- **10,000 events / 1 MB max per call.** Batch accordingly.
- Events are stored in the order they were sent. CloudWatch *rejects*
  events older than 14 days *or* more than 2 hours in the future.
- After the first call, subsequent calls must include
  `sequenceToken = resp["nextSequenceToken"]`. If two writers race
  with the same token, you get `InvalidSequenceTokenException` — re-read
  with `describe_log_streams` to recover.

### `filter_log_events`

```python
resp = logs.filter_log_events(
    logGroupName="/myapp/api",
    startTime=int((time.time() - 3600) * 1000),  # 1h ago
    endTime=int(time.time() * 1000),
    filterPattern="ERROR",
    interleaved=True,           # sort by timestamp across streams
)
for e in resp["events"]:
    print(e["timestamp"], e["message"])
```

The `filterPattern` syntax is a *subset* of Logs Insights:

- Plain text: `"ERROR"` matches any event with `ERROR` in the message.
- JSON path: `{ $.level = "ERROR" }` — note the `=`, not `==`.
- Logical: `?ERROR ?WARN` (AND), `?ERROR ?WARN ?DEBUG` (3-way AND).
- Negation: `-ERROR` excludes.

### `get_log_events` vs. `filter_log_events`

| API | Use for |
|---|---|
| `get_log_events` | tailing a single stream, in order |
| `filter_log_events` | searching across many streams, paginated |

For ad-hoc queries with regex / stats / time-bucket aggregations, use
**Logs Insights** (L13) instead.

## Hands-on

We'll wire all of this up in L14's `create_log_group.py`. For now, in
your AWS account, run the snippets from the lecture against a real log
group.

```python
import boto3, time, json
logs = boto3.client("logs")
logs.create_log_group(logGroupName="/myapp/demo")
logs.create_log_stream(logGroupName="/myapp/demo", logStreamName="demo")
logs.put_log_events(
    logGroupName="/myapp/demo",
    logStreamName="demo",
    logEvents=[{
        "timestamp": int(time.time() * 1000),
        "message": "hello from L12",
    }],
)
```

## Quiz prep

- What's the max events per `put_log_events` call? (10,000)
- How do you re-find the `sequenceToken` after a race? (`describe_log_streams`)
- What's the difference between `get_log_events` and
  `filter_log_events`?

## Further reading

- `https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs.html`
- L13 — Logs Insights query language primer.

## What's next

L13 — CloudWatch Logs Insights — query language primer.
