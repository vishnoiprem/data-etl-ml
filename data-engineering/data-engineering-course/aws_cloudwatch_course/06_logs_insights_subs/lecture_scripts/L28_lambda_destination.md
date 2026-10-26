---
lecture: L28
title: "Lambda as Subscription Destination (the canonical pattern)"
duration: "12:00"
section: 6
prereqs: ["L27"]
---

# L28 — Lambda as Subscription Destination

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 6 — Logs Insights + Subscriptions
> **Duration:** 12:00

## Prereqs

L27 (Kinesis / Firehose).

## Key terms

- **Lambda destination ARN** — the function ARN to receive log events.
- **Event shape** — CloudWatch Logs delivers a *batch* of log events
  encoded in a `CloudWatchLogsEvent` (data + base64-encoded gzipped
  JSON).
- **Log stream name → invocation** — one batch per stream per
  subscription filter delivery window.
- **Async (event source mapping)** — CloudWatch Logs *invokes* the
  Lambda asynchronously; retries are automatic up to 6h.

## Lecture

Pointing a subscription filter at a Lambda is the canonical
"transform or route" pattern. The Lambda receives a batch of events
gzipped + base64-encoded, decompresses them, and acts on each.

### Event shape

```json
{
  "awslogs": {
    "data": "H4sIAAAAAAAA/6vmUlRSyk..."  // gzipped+base64 payload
  }
}
```

The decoded payload looks like:

```json
{
  "owner": "111122223333",
  "logGroup": "/myapp/api",
  "logStream": "i-0abc",
  "subscriptionFilters": ["errors-to-lambda"],
  "messageType": "DATA_MESSAGE",
  "logEvents": [
    {"id": "...", "timestamp": 1696940000000, "message": "ERROR ..."}
  ]
}
```

A typical handler:

```python
import base64, gzip, json

def handler(event, context):
    data = event["awslogs"]["data"]
    payload = json.loads(gzip.decompress(base64.b64decode(data)))
    for log_event in payload["logEvents"]:
        # 1. Filter further (the sub filter already filtered)
        # 2. Transform
        # 3. Route (SNS, S3, PagerDuty, ...)
        print(log_event["message"])
    return {"ok": True}  # 200 to acknowledge the batch
```

### Permissions

The Lambda's resource policy must allow `logs.amazonaws.com` to
invoke it. CloudWatch Logs adds this automatically when you call
`put_subscription_filter` with the function ARN — no extra step.

### The role for the subscription filter

When the destination is a Lambda, **no role is required**. The
function's own resource policy is enough. (Unlike Kinesis / Firehose,
which need a service role for cross-account access.)

### Common use cases

1. **Route to PagerDuty** — parse the event, build a PagerDuty
   payload, hit the Events API.
2. **Enrich** — look up the affected service in a tag table; add
   metadata to the log before storing.
3. **Anomaly detection** — push to a real-time ML model (e.g. KDA).
4. **Cleanup / redaction** — strip PII before forwarding to S3.

### The fan-out pattern

Because you can only have 2 subscription filters per log group,
Lambda is the standard way to fan out to multiple destinations:

```
CW Logs ──► Lambda ──► SNS  (page on-call)
                  ──► S3    (archive)
                  ──► OpenSearch (search)
                  ──► Kinesis (downstream analytics)
```

### Retries and DLQ

- Lambda automatically retries the invocation up to **6 hours** if
  the function errors.
- After 6h, the events are dropped. To keep them, configure a
  **Dead Letter Queue (DLQ)** on the Lambda (SQS or SNS).

## Hands-on

In your AWS account:

1. Create a Lambda that prints `event["awslogs"]` (decode it).
2. Configure a subscription filter on `/aws/lambda/<any-fn>` with
   `ERROR` as the filter pattern.
3. Trigger the function with an error and watch the Lambda receive
   the event in CloudWatch Logs of its own.

## Quiz prep

- What's the event shape from CloudWatch Logs to a Lambda?
  (`{"awslogs": {"data": "<base64 gzipped json>"}}`)
- How many subscription filters per log group? (2.)
- Does the Lambda destination need a service role? (No.)

## Further reading

- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/SubscriptionFilters.html#LambdaFunctionExample`

## What's next

L29 — Hands-on: build `subscription_filter.py` + 4 moto tests.
