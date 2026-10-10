---
lecture: L17
title: "Lambda Targets + Async Invocation"
duration: "10:20"
section: 4
prereqs: ["L16 (targets 101)"]
downloads:
  - "../../downloads/README.md"
---

# L17 — Lambda Targets: Async Invocation, Retries, EventBridge as Event Source Mapping

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 4 — Targets
> **Duration:** 10:20

## Prereqs

- L16 — target ARN format, execution role, target IDs.
- A passing familiarity with Lambda (covered in the AWS Lambda
  Crash Course, sections 2 and 5).

## Key terms

- **Async invocation** — EventBridge invokes the Lambda
  asynchronously. Lambda returns `202` immediately; processing
  happens in the background.
- **Retry policy** — EventBridge's automatic retries for failed
  invocations. Configured per target, separate from Lambda's
  internal retries.
- **DLQ (dead-letter queue)** — an SQS queue that receives events
  whose retry attempts are exhausted.
- **Event source mapping (ESM)** — the Lambda feature for
  polling Kinesis/DynamoDB Streams/SQS. Different from
  EventBridge-driven invocation.

## Lecture

Hi, I'm Prem Vishnoi. The single most common EventBridge target is
a **Lambda function**. About 60% of the rules I write in
production invoke Lambda. This lecture is dedicated to that
target: how EventBridge invokes Lambda, what the retry semantics
are, and the difference between EventBridge-driven and
ESM-driven invocation.

### How EventBridge invokes Lambda

When a rule matches, EventBridge calls `lambda:InvokeFunction`
**asynchronously**. The event is enqueued for Lambda; Lambda
returns `202 Accepted` and processes the event in the background.

```python
# EventBridge puts this event into Lambda's async queue
event = {
    "version": "0",
    "id": "evt-abc-123",
    "source": "my.app",
    "detail-type": "Order Placed",
    "time": "2026-10-10T12:00:00Z",
    "detail": { "orderId": "O-1001", "total": 129.99 }
}
```

Your Lambda handler receives the event as its first argument:

```python
def handler(event, context):
    order = event["detail"]
    print(f"processing {order['orderId']} for ${order['total']}")
    # ... business logic ...
    return {"statusCode": 200}
```

Two things to notice:

1. **The handler does not return the event envelope** — it
   receives it. The handler's *return value* is ignored by
   EventBridge; if you want to react to it, you need a second
   step (e.g. write to a DynamoDB table from the handler).
2. **The async model** means EventBridge can fire-and-forget
   millions of invocations. The rate is bounded by your
   account's Lambda concurrency.

### The execution role for Lambda

The role attached to the Lambda target (the one EventBridge
assumes) needs `lambda:InvokeFunction` permission for the
specific function:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "lambda:InvokeFunction",
    "Resource": "arn:aws:lambda:us-east-1:123456789012:function:processOrder"
  }]
}
```

There's also a **resource-based policy** on the Lambda function
itself, but the default Lambda permission model allows
`events.amazonaws.com` to invoke it without a statement. You only
need to add a statement if you've locked the function down.

### Retry behaviour

EventBridge retries failed invocations using its **RetryPolicy**
(separate from Lambda's own retries). The default policy is:

- **Maximum retry attempts:** 24 hours (the older default) or
  185 attempts (the newer default; the value is configurable).
- **Maximum event age:** 24 hours.

A failed invocation is one where:

- Lambda returns a non-`200` HTTP status (function error,
  timeout, throttling).
- EventBridge can't reach Lambda (network blip, IAM error).

The retry policy is **per target**, not per rule. So if a rule
has two Lambda targets, each can have its own retry policy. The
default is conservative; for a critical workflow, tighten it
down to "retry 3 times in 5 minutes, then DLQ".

```python
events.put_targets(
    Rule="orders-placed-rule",
    EventBusName="orders-bus",
    Targets=[{
        "Id": "lambda-process-order",
        "Arn": "arn:aws:lambda:...",
        "RetryPolicy": {
            "MaximumRetryAttempts": 3,
            "MaximumEventAgeInSeconds": 300,
        },
        "DeadLetterConfig": {
            "Arn": "arn:aws:sqs:us-east-1:123456789012:orders-dlq"
        }
    }]
)
```

We cover DLQ configuration in detail in L19.

### EventBridge vs SQS/Lambda event source mapping

A common point of confusion: how is EventBridge → Lambda
different from SQS → Lambda (event source mapping)?

| | EventBridge → Lambda | SQS → Lambda (ESM) |
|---|---|---|
| **Trigger** | EventBridge rule match | New message on SQS |
| **Invocation** | Async (`Invoke` API) | Polling (Lambda pulls) |
| **Retry** | EventBridge retry policy | Lambda ESM retry (visibility timeout) |
| **Backpressure** | Lambda concurrency limits | SQS depth grows |
| **Filtering** | EventBridge event pattern | Lambda-side filter |
| **Throughput** | High (millions of events/sec) | Bounded by SQS quotas |
| **Cost** | $1/M events (custom bus) | $0.40/M SQS requests + Lambda |

Use **EventBridge → Lambda** when:

- You have a **diverse set of event sources** (S3, custom app,
  SaaS, schedule) and you want one routing layer.
- You want **filtering at the bus** so Lambda only sees events
  that match the pattern.
- You need **cross-account event routing** (the bus is the
  integration point).

Use **SQS → Lambda** when:

- You have a **single, high-volume producer** (e.g. an
  application writing to SQS directly).
- You want **at-least-once delivery without an event router** —
  the queue is the buffer.
- You need **batching** (Lambda ESM can batch up to 10,000
  records per invocation).

In practice, you'll often see **EventBridge → SQS → Lambda** as
the canonical pattern: EventBridge does the filtering, SQS is
the durable buffer, Lambda processes at its own pace. We cover
SQS targets in L18.

### Lambda as a synchronous target

EventBridge can also invoke Lambda **synchronously** by setting
`InvocationType: RequestResponse` — but this is rare. The
default async model is what you'll use 99% of the time.

When would you use sync? When you need to **fail the rule** if
Lambda fails. With async, EventBridge retries and forgets; with
sync, you can propagate the failure to a downstream rule. (This
is a niche pattern; for most uses, async + DLQ is the right
choice.)

### Limits

- **Target throughput** — up to **5,000 invocations per second
  per target** for Lambda (Lambda's own concurrency limits
  apply on top).
- **Event payload** — 256 KB per event. Larger events are
  dropped; if you need to send more, store the payload in S3 and
  put a reference in the event.
- **Number of targets per rule** — 5 in the original design, but
  the current limit is **higher** (and you can fan out to a
  service like SNS to reach more).

## Hands-on

No separate demo for this lecture. The full Lambda-target flow is
exercised in `put_targets.py` (L20).

## Quiz prep

- Is EventBridge → Lambda async or sync? (Async by default.)
- Where is the retry policy configured for a Lambda target? (On
  the target itself, not the rule.)
- What's the difference between EventBridge and SQS event source
  mapping for Lambda? (EventBridge pushes; ESM polls. EventBridge
  is filtered at the bus; ESM is filtered in Lambda.)

## Further reading

- AWS docs: [Lambda as a target](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-lambda.html)
- AWS docs: [Async invocation](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html)
- AWS docs: [Retry policy](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-target-retry.html)
- [`./L18_sqs_sns.md`](./L18_sqs_sns.md) — next lecture

## What's next

L18 — **SQS + SNS Targets** — durable buffering with SQS and
pub/sub fanout with SNS. Both have resource policies you need to
attach so EventBridge can write to them.
