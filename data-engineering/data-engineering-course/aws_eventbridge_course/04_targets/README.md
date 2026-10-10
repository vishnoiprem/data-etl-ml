# Section 4 — Targets (L16–L20)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Working artifact:** `code/put_targets.py` + `code/test_put_targets.py` (6 moto tests)
> **Quiz:** [`../quizzes/section_4.md`](../quizzes/section_4.md)

Section 3 taught you how to **filter** events with rules. This section
teaches you what happens **after** an event matches a rule: it goes to
one or more **targets** — the actual AWS resources that do work in
response to the event.

EventBridge supports **15+ target types**: Lambda, SQS, SNS, Step
Functions, ECS tasks, Kinesis Streams, Kinesis Data Firehose, API
Gateway, API destination (HTTP), EventBridge event bus (in another
account/region), Batch jobs, CodePipeline, CodeBuild, SageMaker, and
more. We focus on the four you'll use 95% of the time: **Lambda,
SQS, SNS, and Step Functions**.

## Lecture map

| L# | Title | What you'll learn |
|---|---|---|
| **L16** | Targets 101 | The 15+ supported targets, ARN format, role assumption |
| **L17** | Lambda Targets | Async invocation, EventBridge as event source mapping, retries |
| **L18** | SQS + SNS Targets | Queue with policy, pub/sub fanout, DLQ for failures |
| **L19** | DLQ + Retry Policies | `RetryPolicy` (max retries, max age), redrive, dead-letter queues |
| **L20** | Section Recap + `put_targets.py` | Walk through the demo, run the tests, take the quiz |

## What the demo does

`code/put_targets.py` is an **idempotent** boto3 script — safe to
re-run any number of times — that:

1. Creates a custom event bus named `orders-bus`.
2. Creates a rule `orders-placed-rule` with an event pattern matching
   `source: "my.app"` + `detail-type: "Order Placed"`.
3. Adds a **Lambda target** to the rule.
4. Adds an **SQS target** to the rule (with the EventBridge
   service-principal policy on the queue).
5. Lists target IDs and removes one.
6. Re-adds the target — proving the script is idempotent.

```bash
# Dry-run (no AWS calls, just prints intent)
python3 04_targets/code/put_targets.py --dry-run

# Real AWS — requires an existing Lambda function and SQS queue ARN
LAMBDA_ARN=arn:aws:lambda:us-east-1:123456789012:function:processOrder \
SQS_ARN=arn:aws:sqs:us-east-1:123456789012:high-value-orders \
  python3 04_targets/code/put_targets.py

# Tests
python3 -m pytest 04_targets/code/test_put_targets.py -v
```

## Section quiz

After the lectures, take [`../quizzes/section_4.md`](../quizzes/section_4.md)
(10 questions covering target types, DLQ, and retry policy).

## What's next

Section 5 — **EventBridge Scheduler (L21–L24)** — uses a different
trigger: not an event, but **time**. Cron + rate expressions, flexible
windows, time zones, one-off invocations.
