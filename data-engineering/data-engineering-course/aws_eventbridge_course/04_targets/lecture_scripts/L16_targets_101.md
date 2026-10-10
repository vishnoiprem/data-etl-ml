---
lecture: L16
title: "Targets 101 — The 15+ Supported AWS Targets"
duration: "9:15"
section: 4
prereqs: ["L10-L15 (rules + event patterns)"]
downloads:
  - "../../downloads/README.md"
---

# L16 — Targets 101: The 15+ Supported AWS Targets

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 4 — Targets
> **Duration:** 9:15

## Prereqs

- L10–L15 (Rules + event patterns). You should be comfortable with
  the event pattern syntax and the `put_rule` API.

## Key terms

- **Target** — an AWS resource that receives a matched event from
  a rule.
- **Target ARN** — the unique identifier of the target resource;
  every `put_targets` call needs at least one ARN.
- **Target ID** — a per-rule identifier you choose (e.g.
  `lambda-process-order`). Used to update or remove a target.
- **Execution role** — the IAM role EventBridge assumes to invoke
  the target (required for AWS-service targets, optional for some
  HTTP targets).
- **Input transformer** — a small templating DSL that rewrites
  the event before delivering it to the target.

## Lecture

Hi, I'm Prem Vishnoi. Section 3 taught you how to **filter**
events. This section teaches you what happens to events **after**
they're filtered: they go to a **target**. EventBridge has the
broadest target list of any AWS event-routing service — 15+
target types and counting — and the choice of target is where
most of the architectural decisions in an event-driven system
actually get made.

### The full target list

The current (2026) target types EventBridge supports:

| Target | Use case | Notes |
|---|---|---|
| **Lambda function** | Run code in response to an event | Most common target |
| **SQS queue** | Durable buffering, fanout, batch consumers | Queue with policy |
| **SNS topic** | Pub/sub fanout, push to email/HTTP/SMS | Topic with policy |
| **Step Functions state machine** | Long-running workflows | Sync or async |
| **ECS task** | Run a Docker container | Network configuration required |
| **Kinesis stream** | Stream processing | One event = one record |
| **Kinesis Data Firehose** | Stream to S3 / Redshift / OpenSearch | Buffered |
| **API Gateway** | Trigger REST / WebSocket APIs | REST APIs only |
| **API destination** (HTTP) | Call any HTTPS endpoint | OAuth support |
| **EventBridge bus** (in another account/region) | Cross-account / cross-region routing | Bus ARN as target |
| **Batch job** | Submit an AWS Batch job | For HPC workloads |
| **CodePipeline** | Trigger a pipeline execution | Manual pipelines |
| **CodeBuild project** | Trigger a build | For CI/CD glue |
| **SageMaker pipeline** | Trigger an ML pipeline | ML workflows |
| **Redshift Serverless query** | Run a SQL query | Analytics use case |
| **Timestream table** | Write a row to a time-series DB | IoT/observability |

That's the "extended" list. In practice you'll use **four** 95% of
the time: **Lambda, SQS, SNS, Step Functions**. The rest are
specialized.

### Target ARN format

Every target has an ARN. The format depends on the service:

```text
arn:aws:lambda:us-east-1:123456789012:function:processOrder
arn:aws:sqs:us-east-1:123456789012:high-value-orders
arn:aws:sns:us-east-1:123456789012:order-events
arn:aws:states:us-east-1:123456789012:stateMachine:OrderWorkflow
arn:aws:events:us-west-2:123456789012:event-bus/orders-bus-mirror
arn:aws:ecs:us-east-1:123456789012:task-definition/process-order:1
arn:aws:kinesis:us-east-1:123456789012:stream/orders-stream
arn:aws:firehose:us-east-1:123456789012:deliverystream/orders-firehose
arn:aws:execute-api:us-east-1:123456789012:abc123def4/prod
arn:aws:batch:us-east-1:123456789012:job-definition/process-order:1
```

The pattern is `<service>:<resource>`. boto3's
`client.describe_rule` returns the target ARNs under the
`Targets` key.

### The execution role

For most AWS-service targets, EventBridge needs an **execution
role** — an IAM role it assumes to invoke the target. The role is
attached per target, not per rule:

```python
events.put_targets(
    Rule="orders-placed-rule",
    EventBusName="orders-bus",
    Targets=[{
        "Id": "lambda-process-order",
        "Arn": "arn:aws:lambda:us-east-1:123456789012:function:processOrder",
        "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeInvokeLambda"
    }]
)
```

The role's **trust policy** must allow `events.amazonaws.com` to
assume it:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "events.amazonaws.com" },
    "Action": "sts:AssumeRole"
  }]
}
```

The role's **permission policy** depends on the target type. For
Lambda:

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

We cover the role per target type in L17 (Lambda) and L18
(SQS/SNS).

### Adding, removing, and listing targets

`put_targets` is idempotent on the target list **only** if you
manage IDs carefully. The boto3 model is:

- **`put_targets`** — adds the targets in the request. If a target
  with the same `Id` already exists, it's **replaced** (its
  `Arn`, `RoleArn`, input transformer, etc. are overwritten).
- **`remove_targets`** — removes targets by `Id`. Other targets
  are unaffected.
- **`list_targets_by_rule`** — returns the current target list.

```python
# Add
events.put_targets(
    Rule="orders-placed-rule",
    EventBusName="orders-bus",
    Targets=[{"Id": "t1", "Arn": "..."}]
)

# List
resp = events.list_targets_by_rule(
    Rule="orders-placed-rule", EventBusName="orders-bus"
)
ids = [t["Id"] for t in resp["Targets"]]

# Remove
events.remove_targets(
    Rule="orders-placed-rule",
    EventBusName="orders-bus",
    Ids=["t1"],
)
```

### Target IDs: pick stable ones

The `Id` you choose for a target should be **stable** — you'll use
it to update or remove the target later. Best practice is to
embed the target type or function name:

```python
# Good -- human-readable, stable
"Id": "lambda-process-order"
"Id": "sqs-high-value-orders"
"Id": "sns-fanout"

# Bad -- auto-incremented, hard to remove later
"Id": "target1"
```

If your script needs to be **idempotent** (L20), pick IDs that
are derived from the target's role (e.g. the Lambda function
name) so re-running the script replaces the same target in
place.

### Input transformers

By default, the target receives the **full event envelope**:

```json
{
  "version": "0",
  "id": "...",
  "source": "my.app",
  "detail-type": "Order Placed",
  "detail": { "orderId": "O-1001" },
  ...
}
```

If your target wants a **slimmer** payload, use an **input
transformer** to rewrite it:

```python
events.put_targets(
    Rule="orders-placed-rule",
    EventBusName="orders-bus",
    Targets=[{
        "Id": "sqs-high-value",
        "Arn": "arn:aws:sqs:...",
        "InputTransformer": {
            "InputPathsMap": {"orderId": "$.detail.orderId"},
            "InputTemplate": '{"orderId": "<orderId>"}'
        }
    }]
)
```

The `InputPathsMap` is JSONPath (e.g. `$.detail.orderId`). The
`InputTemplate` is a string with `<placeholder>` references.
EventBridge substitutes them at invoke time. This is the cheapest
way to reshape an event without a Lambda in the middle.

### Dead-letter queues (preview of L19)

If a target invocation fails, EventBridge retries. After the
retry policy is exhausted, the event is sent to a **dead-letter
queue** (DLQ) — an SQS queue you've configured. DLQs are how you
avoid losing events on transient failures. We cover the
configuration in L19.

## Hands-on

No separate demo for this lecture. The full target list is
exercised in `put_targets.py` (L20).

## Quiz prep

- How many target types does EventBridge support? (15+, with
  Lambda/SQS/SNS/Step Functions being the most common.)
- What's the difference between `put_targets` and
  `remove_targets`? (Add/replace vs delete by ID.)
- What's an execution role? (IAM role EventBridge assumes to
  invoke the target.)

## Further reading

- AWS docs: [EventBridge targets](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-targets.html)
- AWS docs: [Input transformer](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-transform-target-input.html)
- [`./L17_lambda_targets.md`](./L17_lambda_targets.md) — next lecture

## What's next

L17 — **Lambda Targets + Async Invocation** — the most common
target, the async invocation model, the retry behaviour, and how
EventBridge differs from SQS/Lambda event source mappings.
