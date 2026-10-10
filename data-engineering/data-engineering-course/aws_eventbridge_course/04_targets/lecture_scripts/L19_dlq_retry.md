---
lecture: L19
title: "Dead-Letter Queues + Retry Policies"
duration: "11:10"
section: 4
prereqs: ["L18 (SQS + SNS targets)"]
downloads:
  - "../../downloads/README.md"
---

# L19 — Dead-Letter Queues + Retry Policies

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 4 — Targets
> **Duration:** 11:10

## Prereqs

- L18 — SQS/SNS targets, resource policies.
- L17 — async invocation, retry policy preview.

## Key terms

- **RetryPolicy** — per-target configuration that controls how
  many times and for how long EventBridge retries a failed
  invocation.
- **MaximumRetryAttempts** — how many times to retry a failed
  invocation. `0` means no retries (one shot then DLQ).
- **MaximumEventAgeInSeconds** — the oldest age of an event that
  will still be retried. Events older than this go to the DLQ.
- **DeadLetterConfig** — the configuration block that names the
  DLQ ARN.
- **Redrive** — moving messages from a DLQ back to the source
  queue after fixing the consumer. The SQS feature, not
  EventBridge.

## Lecture

Hi, I'm Prem Vishnoi. Every target fails sometimes. Lambda
times out, SQS has a permission error, the API endpoint is down
for 30 seconds. The question isn't "will it fail?" — it will —
but "what happens to the event when it does?". The answer is the
**retry policy** and the **dead-letter queue**. Get these
right and your system is resilient; get them wrong and you lose
events on the first hiccup.

### The failure model

EventBridge considers an invocation **failed** when:

- The target returns a non-`2xx` HTTP status.
- The target throws a timeout (Lambda function timeout, SQS
  throttle, API endpoint 5xx).
- The IAM role is missing a permission.
- The target resource is in a different account/region and the
  trust isn't set up.

When an invocation fails, EventBridge:

1. **Retries** the invocation per the `RetryPolicy`.
2. If retries exhaust, **sends the event to the DLQ** (if
   configured).
3. Otherwise, **drops the event** with a CloudWatch metric
   increment.

This is the only correct way to think about it: **without a DLQ,
failed events disappear**.

### The RetryPolicy

The `RetryPolicy` is a per-target block:

```python
events.put_targets(
    Rule="orders-placed-rule",
    EventBusName="orders-bus",
    Targets=[{
        "Id": "lambda-process-order",
        "Arn": "arn:aws:lambda:...",
        "RetryPolicy": {
            "MaximumRetryAttempts": 3,
            "MaximumEventAgeInSeconds": 300,  # 5 minutes
        },
    }]
)
```

Two fields:

- **`MaximumRetryAttempts`** — how many times to retry. `0`
  means no retries (one shot, then DLQ or drop). The default is
  the AWS-account-wide default (around 24 hours / 185 attempts;
  the exact value has changed historically).
- **`MaximumEventAgeInSeconds`** — the oldest age of an event
  that will still be retried. If an event is older than this
  when its retry fires, it goes to the DLQ (or is dropped)
  immediately. Useful for "this data is only useful for 5
  minutes" use cases.

**Practical defaults:**

| Use case | Retries | Max age |
|---|---|---|
| Critical workflow (e.g. payment) | 5 | 600 (10 min) |
| Standard async work | 3 | 300 (5 min) |
| Fire-and-forget metrics | 1 | 60 (1 min) |
| Real-time alert | 0 | 30 (30 sec) |

The trade-off: more retries = more resilience to transient
failures, but also more latency on permanent failures (the event
sits in the retry queue longer before reaching the DLQ).

### Exponential backoff

EventBridge retries with **exponential backoff** and **jitter**.
The first retry is around 1 second after the failure; subsequent
retries grow exponentially up to a 5-minute cap. With
`MaximumRetryAttempts: 3` and `MaximumEventAgeInSeconds: 300`,
your timeline is roughly:

- t=0:    initial invocation fails
- t=1s:   retry 1
- t=3s:   retry 2
- t=10s:  retry 3
- t=10s+: DLQ

That's the rough shape; the actual times are jittered so two
parallel failures don't synchronize.

### DLQ configuration

The DLQ is just an SQS queue. The configuration is on the target:

```python
events.put_targets(
    Rule="orders-placed-rule",
    EventBusName="orders-bus",
    Targets=[{
        "Id": "lambda-process-order",
        "Arn": "arn:aws:lambda:...",
        "DeadLetterConfig": {
            "Arn": "arn:aws:sqs:us-east-1:123456789012:orders-dlq"
        }
    }]
)
```

The DLQ must exist **before** you attach the target. The DLQ
needs a resource policy that allows EventBridge to write:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowEventBridgeDLQ",
    "Effect": "Allow",
    "Principal": {"Service": "events.amazonaws.com"},
    "Action": "sqs:SendMessage",
    "Resource": "arn:aws:sqs:us-east-1:123456789012:orders-dlq",
    "Condition": {
      "ArnEquals": {
        "aws:SourceArn": "arn:aws:events:us-east-1:123456789012:rule/orders-bus/orders-placed-rule"
      }
    }
  }]
}
```

Same shape as the regular SQS target policy. The
`Condition: ArnEquals` is recommended; without it, any rule in
your account can write to your DLQ.

### DLQ message format

The DLQ message is the same as the original event envelope, plus
metadata about the failure:

```json
{
  "version": "0",
  "id": "evt-abc-123",
  "source": "my.app",
  "detail-type": "Order Placed",
  "time": "2026-10-10T12:00:00Z",
  "detail": { "orderId": "O-1001" },
  "resources": ["arn:aws:lambda:..."],
  "dlq-body": {
    "ErrorCode": "Lambda.ServiceException",
    "ErrorMessage": "Rate exceeded for function",
    "RequestId": "...",
    "Resource": "arn:aws:lambda:us-east-1:123456789012:function:processOrder"
  }
}
```

(`dlq-body` is the field name as of 2026; historically it was
`deadLetterQueueData`.) The original event envelope is preserved
as-is, so your DLQ consumer can re-emit the event to the bus
once the underlying issue is fixed.

### Redrive (recovery from DLQ)

Once you've fixed the consumer, you want to **redrive** the DLQ —
replay the messages back through the original flow. There are two
ways:

1. **Manual: re-emit each message with `PutEvents`.** Read the
   DLQ, re-emit each event with the same `id` (or a new `id` if
   you want to dedupe), and let the rule fire again.

```python
import boto3, json

sqs = boto3.client("sqs")
events = boto3.client("events")

# Receive messages from DLQ
resp = sqs.receive_message(
    QueueUrl="https://sqs.us-east-1.amazonaws.com/123456789012/orders-dlq",
    MaxNumberOfMessages=10,
    WaitTimeSeconds=5,
)
for msg in resp.get("Messages", []):
    body = json.loads(msg["Body"])
    events.put_events(Entries=[{
        "EventBusName": "orders-bus",
        "Source": body["source"],
        "DetailType": body["detail-type"],
        "Detail": json.dumps(body["detail"]),
    }])
    sqs.delete_message(
        QueueUrl="...",
        ReceiptHandle=msg["ReceiptHandle"],
    )
```

2. **SQS DLQ redrive** (2024+ feature): the SQS console/API now
   has a "Start DLQ redrive" action that moves messages back to
   the source queue. This is the cleanest path when your
   EventBridge rule writes to SQS and SQS-to-Lambda is the
   downstream.

### Alerting on DLQ depth

A DLQ that has messages in it is a **production incident**. The
eventual-consistency model is: your consumer failed, the event
sat in the DLQ, and nothing in your alerting caught it. The
fix is a CloudWatch alarm on `ApproximateNumberOfMessagesVisible`
on the DLQ:

```bash
aws cloudwatch put-metric-alarm \
    --alarm-name orders-dlq-not-empty \
    --metric-name ApproximateNumberOfMessagesVisible \
    --namespace AWS/SQS \
    --dimensions Name=QueueName,Value=orders-dlq \
    --statistic Average \
    --period 60 \
    --threshold 1 \
    --comparison-operator GreaterThanOrEqualToThreshold \
    --evaluation-periods 1 \
    --alarm-actions arn:aws:sns:...:alerts
```

I treat any non-zero DLQ depth as a **page**. The DLQ is a
**silent failure indicator**; if no one is watching it, you'll
lose events for hours before anyone notices.

### Operational checklist

For every production EventBridge rule with a critical target:

- [ ] DLQ configured and exists
- [ ] DLQ resource policy allows the specific rule ARN
- [ ] Retry policy set (don't rely on defaults)
- [ ] CloudWatch alarm on DLQ depth
- [ ] Runbook: what to do when the alarm fires
- [ ] Tested: simulate a failure (e.g. break the Lambda IAM
  role) and confirm the event lands in the DLQ

## Hands-on

No separate demo for this lecture. DLQ behaviour is exercised in
`put_targets.py` (L20) via the `DeadLetterConfig` block.

## Quiz prep

- What happens to a failed event with no DLQ? (Dropped.)
- What's the difference between `MaximumRetryAttempts` and
  `MaximumEventAgeInSeconds`? (Retry count vs total wall-clock
  time before giving up.)
- Is the DLQ an SQS queue? (Yes — and it needs its own
  resource policy.)
- How do you alert on a stuck DLQ? (CloudWatch alarm on
  `ApproximateNumberOfMessagesVisible`.)

## Further reading

- AWS docs: [EventBridge DLQ](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html)
- AWS docs: [EventBridge retry policy](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-target-retry.html)
- AWS docs: [SQS DLQ redrive](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-configure-dead-letter-queue-redrive.html)
- [`./L20_section_recap.md`](./L20_section_recap.md) — next lecture

## What's next

L20 — **Section 4 Recap + `put_targets.py` walk-through** — we
tie Sections 1–4 together, walk through the demo code, and run
the test suite.
