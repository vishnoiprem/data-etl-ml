---
title: L55 — Lambda Monitoring — CloudWatch Logs
author: Prem Vishnoi <prem.vishnoi@example.com>
section: 11
duration: 2:17
---

# L55 — Lambda Monitoring — CloudWatch Logs

> Metrics tell you *that* something happened. Logs tell you
> *what* happened. Every Lambda function is attached to a CloudWatch
> Log Group at function creation, and every `print()` becomes a log
> event.

## Prereqs

- L53 (metrics theory) — same ecosystem, different modality.

## Key terms

- **Log group** — named bucket of log streams. Lambda creates
  `/aws/lambda/<function-name>` automatically.
- **Log stream** — one per execution environment (instance), named
  after the instance ID.
- **Retention** — by default, log groups **never expire**. You must
  set a retention policy or pay for storage.
- **Structured logging** — emit JSON lines, easier to query in
  Insights.

## 1. The default behavior

- A new Lambda creates `/aws/lambda/<function-name>` *at create
  time*. It is empty until first invocation.
- Each function execution produces *at least two* log lines:
  `INIT_START` (boot) and `END` (with duration) plus `REPORT`.
- `print()`, `logging.info()`, `sys.stdout.write()` all go here.
- `STDERR` (and unhandled exceptions) go here too.

## 2. The two-minute rotation rule

By default, log events are flushed at function end. They go to
CloudWatch with no further delay. **Retention is forever** unless
you set it:

```bash
aws logs put-retention-policy \
    --log-group-name /aws/lambda/my-api \
    --retention-in-days 30
```

A typical pattern: 30 days in dev, 90 days in prod, 365 days for
audit-graded workloads.

## 3. Structured logging (recommended)

`print()` of plain text is cheap and bad. `print(json.dumps({...}))`
is the same number of bytes and infinitely queryable:

```python
import json, logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info(json.dumps({
        "msg": "request received",
        "request_id": context.aws_request_id,
        "function": context.function_name,
        "n": len(event.get("records", [])),
    }))
    # ...
    logger.info(json.dumps({
        "msg": "request done",
        "request_id": context.aws_request_id,
        "duration_ms": int(context.get_remaining_time_in_millis() - 0.001) - 0,
    }))
```

## 4. Lambda log event anatomy

A `START`/`END`/`REPORT` triple for one invocation looks like:

```
START RequestId: ab12-... Version: $LATEST
... your lines ...
END RequestId: ab12-...
REPORT RequestId: ab12-...  Duration: 132.45 ms  Billed Duration: 133 ms
                       Memory Size: 512 MB  Max Memory Used: 78 MB
                       Init Duration: 180.20 ms
```

`Init Duration` only appears on cold starts.

## Lecture summary

- Logs are on by default, and `print` is enough.
- Set a retention policy — "never expire" is rarely what you want.
- Print JSON. Always.

## Quiz prep

- What log group does Lambda create for a function named
  `my-api`?
- What's the default log retention?
- Why is `print(json.dumps({...}))` better than `print("...")`?

## Further reading

- AWS — [Lambda CloudWatch Logs](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-logs.html)
- AWS — [CloudWatch Logs retention](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html#SettingLogRetention)
