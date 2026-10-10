---
l_id: L22
title: Lambda Limits — Timeout
duration: 4:06
prereqs:
  - L20 (Invocation Model — Theory)
  - L21 (Invocation Model — Hands On)
---

# L22 — Lambda Limits — Timeout

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 5 — AWS Lambda Basic Concepts (Part 2)
> **Duration:** 4:06

## Prereqs

- L20 — the four invocation models (especially async, where the
  timeout has the most user-visible effect)
- L21 — deployed `invocation-demo` function and EventBridge rule
- Comfortable setting a function's configuration via the console
  or `aws lambda update-function-configuration`

## Key terms

- **Timeout** — the maximum wall-clock seconds Lambda will let a
  single invocation run before it forcibly terminates the
  execution environment and reports a `Task timed out after X
  seconds` error to CloudWatch Logs.
- **Hard limit** — `900` seconds (15 minutes). Cannot be raised.
- **Soft limit (default)** — `3` seconds for new functions. Can
  be raised up to the hard limit, **per function**, by editing
  the function configuration.
- **Timeout vs. Duration** — Duration is the *measured* time the
  handler actually ran. Timeout is the *ceiling* you set. They
  are different things and they both show up on the CloudWatch
  Metrics graph.

## Lecture

Lambda is a service with **hard service-level limits**. Some
of them (memory, payload size, deployment-package size,
concurrent executions) we cover in Section 11. The limit that
students hit first — and the one that determines whether your
function ever returns a response at all — is **timeout**.

### The current limit

- **Hard upper bound: 900 seconds (15 minutes).** This is a
  service-wide ceiling. You cannot raise it. If you ask for
  `Timeout=901`, the API call will fail.
- **Default for new functions: 3 seconds.** AWS picks a
  conservative default so that runaway code is killed early
  and you do not accidentally burn 15 minutes and a large
  bill.
- **Configurable range: 1 second to 900 seconds**, in 1-second
  increments, set per function.

You change it from the console (`Configuration → General →
Timeout`) or with the CLI:

```bash
aws lambda update-function-configuration \
  --function-name invocation-demo \
  --timeout 60 \
  --region us-east-1
```

### What happens when you hit the limit

When your handler runs longer than the configured timeout,
Lambda does three things, in this order:

1. **Terminates the execution environment.** The handler
   process is killed. Any in-flight work — a long `boto3`
   call, an open TCP connection, a partially written file to
   `/tmp` — is cut off. There is **no graceful shutdown** by
   default; you cannot "trap" the timeout and clean up.
2. **Writes a `Task timed out after X seconds` error** to
   CloudWatch Logs for the invocation. The
   `aws_request_id` is preserved so you can correlate it
   with metrics and X-Ray traces.
3. **Handles the failure per the invocation model**:
   - **Sync** — the caller receives a 200 with a Lambda
     error response, or a connect-timeout / 5xx depending
     on the integration. **No retry.**
   - **Async** — Lambda **retries** the invocation (2 times
     by default, with exponential backoff) before sending
     the event to the configured DLQ or destination.
   - **ESM (poll-based)** — the batch is **not**
     checkpointed, so the same batch is retried
     indefinitely (or until the record expires in the
     stream).

The third point is why timeout matters so much in async and
ESM designs: a 15-minute function that times out gets retried
for another 15 minutes, and another — you can accidentally
multiply your Lambda bill by 3x or more from a single
upstream slowdown.

### The 4 best practices

#### 1. Set the timeout to the **actual** p99 of the handler, plus a buffer

Don't default to 15 minutes "just in case". Use CloudWatch
Metrics (`Duration`, `Max`, p99.9) over a real workload to
find the realistic upper bound, then add 10–20% for headroom.
A 30-second function with a 5-second p99 and a 7-second
timeout is healthier than the same function with a 900-second
timeout — because the second one will *hide* a downstream
slowdown for 15 minutes before it ever fires a CloudWatch
alarm.

#### 2. Make handlers **idempotent**

Because all three non-sync invocation models retry on
failure (and on timeout), every handler must be safe to run
twice with the same `event`. The single most common
production bug in this section's lectures is "I wrote
exactly-once code and now the customer got charged twice."
Use an idempotency key (the `eventID` for S3 events, the
SQS `MessageId`, the Kinesis `sequenceNumber`, or your own
dedupe table in DynamoDB) to short-circuit duplicate
invocations.

#### 3. If a job is genuinely longer than 15 minutes, **offload it**

Lambda is the wrong tool for multi-hour batch jobs. The
right pattern is:

- **Step Functions** — orchestrate the work as a state
  machine. Each state can be a Lambda with its own 15-min
  budget, and the state machine tracks progress. **This is
  the most common production answer.**
- **ECS / Fargate** — long-running containers that can run
  for hours, with the trigger fired by EventBridge or SQS.
- **AWS Batch** — batch-compute jobs that scale
  independently of Lambda.

Section 11's advanced lectures will show a Step Functions
+ Lambda pattern in detail; here we just want you to
internalize that **15 minutes is a ceiling, not a
target**.

#### 4. Watch the right CloudWatch metrics

A function that consistently times out is a function whose
*underlying* problem needs to be fixed (slow database, slow
third-party API, deadlocked code). The metrics to set
CloudWatch alarms on are:

- `Errors` — count of invocations that returned a
  `FunctionError` or timed out.
- `Throttles` — count of invocations rejected because you
  hit your concurrency quota.
- `Duration` (p99) — close to the timeout is a code smell.
- **CloudWatch Logs Insights query** for `Task timed out`
  — count of timeouts in a window.

A reasonable starting alarm: `Errors > 0` for 5 minutes,
paged on. The 5-minute rule avoids flapping from a single
bad event.

### Quick recap

- **Hard limit: 15 minutes (900s).** Cannot be raised.
- **Default: 3 seconds.** Raise per function up to 900.
- **Timeout = Lambda terminates, no graceful cleanup, log
  line written, retry per the invocation model.**
- **Best practices: set timeout to p99 + buffer, make
  handlers idempotent, offload > 15 min to Step Functions
  or ECS, alarm on `Errors` and `Duration` p99.**

## Hands-on

There is no new code in this lecture. Reuse the
`invocation-demo` function from L21:

```bash
# Set a 1-second timeout, then trigger a 30-second handler
# (loop 30 times with sleep(1)) and watch CloudWatch Logs.
aws lambda update-function-configuration \
  --function-name invocation-demo \
  --timeout 1 \
  --region us-east-1

aws lambda invoke \
  --function-name invocation-demo \
  --cli-binary-format raw-in-base64-out \
  --payload '{"sleep": 30}' \
  /tmp/out.json \
  --region us-east-1

# Inspect the log group for the "Task timed out after 1.00 seconds" line.
aws logs tail /aws/lambda/invocation-demo --follow
```

Restore the timeout afterwards:

```bash
aws lambda update-function-configuration \
  --function-name invocation-demo \
  --timeout 30 \
  --region us-east-1
```

## Quiz prep

- Q5, Q6, Q7, Q8 of `quizzes/section_5.md` directly test the
  hard limit, the default, what happens on timeout, and the
  offload-to-Step-Functions pattern.
- Be ready to give the four best practices in one sentence
  each.

## Further reading

- AWS docs: [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)
- AWS docs: [Lambda function configuration — timeout](https://docs.aws.amazon.com/lambda/latest/dg/configuration-memory.html)
- AWS docs: [Step Functions](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html)
- `lecture_scripts/L21_invocation_model_hands_on.md` — the
  handler used in the hands-on timeout demo
- Section 11 lecture `L48_concurrency.md` and
  `L49_reserved_provisioned_concurrency.md` — the
  concurrency-side companion to this lecture
