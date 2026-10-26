# Section 5 Quiz — AWS Lambda Basic Concepts (Part 2): Invocation Model & Limits

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

---

**Q1.** Which AWS Lambda invocation model **returns the function's return value to the caller**?

- A. Asynchronous
- B. Synchronous
- C. Event-source mapping
- D. All four invocation models return the value

<details><summary>Show answer</summary>

**B — Synchronous.** In a sync invocation, the caller blocks until the function returns and receives the return value (or the error). Async invocations return HTTP 202 with no payload; the handler's return value is discarded. Event-source mappings return per-record success/failure information to the poller, not to a "caller" in the same sense.

</details>

---

**Q2.** You have wired an EventBridge scheduled rule to a Lambda function. Which invocation model is the rule using, and who is responsible for retries on failure?

- A. Synchronous; the caller (EventBridge) is responsible for retries
- B. Asynchronous; Lambda is responsible for retries and the DLQ
- C. Event-source mapping; Lambda polls the schedule
- D. Direct service; Step Functions owns the retry policy

<details><summary>Show answer</summary>

**B — Asynchronous; Lambda is responsible for retries and the DLQ.** EventBridge schedule invocations are async: the rule hands the event to Lambda and continues. Lambda retries twice by default (configurable up to 6) and then routes the failed event to the configured DLQ or destination.

</details>

---

**Q3.** Which `boto3 client.invoke` call is the **synchronous** form?

- A. `invoke(FunctionName='x', InvocationType='Event')`
- B. `invoke(FunctionName='x', InvocationType='RequestResponse')`
- C. `invoke_async(FunctionName='x', InvokeArgs='{}')`
- D. Both A and C are synchronous

<details><summary>Show answer</summary>

**B — `invoke(FunctionName='x', InvocationType='RequestResponse')`.** That is the sync API call: the SDK blocks until the function returns and the response payload is read into `resp['Payload']`. `InvocationType='Event'` is async (returns immediately with status 202). `invoke_async` is the legacy async API limited to 128 KB payloads.

</details>

---

**Q4.** Kinesis Data Streams → Lambda is best classified as which invocation model?

- A. Synchronous
- B. Asynchronous
- C. Event-source mapping (poll-based)
- D. Direct service-to-service

<details><summary>Show answer</summary>

**C — Event-source mapping (poll-based).** Lambda runs a poller in your function's account, reads records from the Kinesis shard, batches them, invokes your handler with the batch, and checkpoints on success. Batching, checkpoints, and the DLQ are all managed by Lambda. There is no real-time push from Kinesis to Lambda.

</details>

---

**Q5.** What is the **hard upper bound** for the AWS Lambda function timeout?

- A. 60 seconds
- B. 300 seconds
- C. 900 seconds (15 minutes)
- D. 3600 seconds (1 hour)

<details><summary>Show answer</summary>

**C — 900 seconds (15 minutes).** This is a service-wide hard limit. You can set any value from 1 to 900 seconds per function, but you cannot raise the ceiling beyond 900. New functions default to 3 seconds, which is a soft default you can raise up to 900 per function.

</details>

---

**Q6.** When a Lambda function exceeds its configured timeout, which of the following happens **first**?

- A. Lambda sends the event to the DLQ
- B. The execution environment is terminated and the handler process is killed
- C. The caller receives a graceful shutdown signal
- D. CloudWatch stops collecting metrics for the function

<details><summary>Show answer</summary>

**B — The execution environment is terminated and the handler process is killed.** There is no graceful shutdown. The handler cannot "trap" the timeout and clean up. Lambda then writes a `Task timed out after X seconds` line to CloudWatch Logs and handles the failure per the invocation model (no retry for sync, retry for async, no checkpoint for ESM).

</details>

---

**Q7.** Your handler has a real p99 of 14 minutes and 30 seconds. The cleanest, most Lambda-native way to handle this workload is to:

- A. Set the timeout to 900 seconds and call it done
- B. Set the timeout to 900 seconds and turn on provisioned concurrency
- C. Use Step Functions to orchestrate the work as a state machine, with each Lambda state under 15 minutes
- D. Split the function into 30 Lambdas and run them in parallel

<details><summary>Show answer</summary>

**C — Use Step Functions to orchestrate the work as a state machine, with each Lambda state under 15 minutes.** The 900-second ceiling cannot be raised, and a 14:30 p99 leaves essentially no headroom. Step Functions is the AWS-native way to coordinate multi-step, long-running workloads while keeping each Lambda invocation well under the timeout. Provisioned concurrency (B) is about scaling, not duration. Splitting into 30 parallel Lambdas (D) is rarely the right answer and adds coordination complexity that Step Functions already solves.

</details>

---

**Q8.** Why is it important to make Lambda handlers **idempotent** when they are invoked asynchronously?

- A. Because Lambda deduplicates events by `eventID` and you must handle the duplicates
- B. Because async invocations are retried on failure, and the same event may be delivered more than once
- C. Because async handlers cannot write to DynamoDB more than once per invocation
- D. Because idempotency is required for any function that writes to S3

<details><summary>Show answer</summary>

**B — Because async invocations are retried on failure, and the same event may be delivered more than once.** Lambda retries async failures 2 times by default (configurable up to 6), and each retry re-runs the handler with the same `event`. Without idempotency, a transient downstream failure can cause duplicate writes, duplicate charges, or duplicate messages. Use a stable event ID (S3 `eventID`, SQS `MessageId`, Kinesis `sequenceNumber`, or your own dedupe key) to short-circuit duplicates.

</details>

---

**Q9.** Which AWS service → Lambda combination is **NOT** typically classified as asynchronous?

- A. EventBridge scheduled rule → Lambda
- B. S3 `ObjectCreated:Put` event notification → Lambda
- C. API Gateway REST API → Lambda
- D. SNS topic → Lambda subscriber

<details><summary>Show answer</summary>

**C — API Gateway REST API → Lambda.** API Gateway invocations are synchronous: the API Gateway caller (your HTTP client) blocks until the Lambda returns, and the Lambda's response is serialized back as the HTTP response body. EventBridge schedules (A), S3 event notifications (B), and SNS subscriptions (D) are all async: the calling service hands the event to Lambda and moves on; Lambda handles retries and the DLQ.

</details>

---

**Q10.** You observe a CloudWatch alarm on the `Errors` metric firing every night at 03:00 UTC, and the log lines say `Task timed out after 15.00 seconds`. The handler is a 12-second function with a 15-second timeout. The **first** thing you should do is:

- A. Raise the timeout to 900 seconds
- B. Add provisioned concurrency
- C. Investigate why the handler occasionally runs past 15 seconds and fix the underlying cause (a slow downstream call, deadlock, or unhandled retry storm)
- D. Disable the alarm

<details><summary>Show answer</summary>

**C — Investigate why the handler occasionally runs past 15 seconds and fix the underlying cause.** Raising the timeout (A) hides the bug behind a 15-minute ceiling — you turn a 15-second p100 into a 15-minute p100, which multiplies your bill and your blast radius on a bad day. Provisioned concurrency (B) addresses cold starts and throttling, not duration. Disabling the alarm (D) loses visibility. Best practice: set the timeout to the real p99 plus a small buffer, alarm on `Errors` and `Duration` p99, and fix the downstream cause (slow API, slow DB query, missing index, retry storm, etc.) instead of papering over it.

</details>
