# Section 4 Quiz — Targets, DLQ, Retry Policy

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the
> question.

---

**Q1.** How many target types does EventBridge support (as of 2026)?

- A. 3 (Lambda, SQS, SNS)
- B. 6 (Lambda, SQS, SNS, Step Functions, EventBridge bus, Kinesis)
- C. 15+ (Lambda, SQS, SNS, Step Functions, ECS, Kinesis, Firehose, API Gateway, API destination, EventBridge bus, Batch, CodePipeline, CodeBuild, SageMaker, Timestream, Redshift, and more)
- D. Exactly 25

<details><summary>Show answer</summary>

**C — 15+.** EventBridge supports Lambda, SQS, SNS, Step Functions, ECS tasks, Kinesis Streams, Kinesis Data Firehose, API Gateway, API destinations (HTTP), EventBridge bus (cross-account/cross-region), Batch jobs, CodePipeline, CodeBuild, SageMaker pipeline, Timestream, Redshift Serverless, and more.

</details>

---

**Q2.** When a rule targets a Lambda function, what IAM role does EventBridge use to invoke it?

- A. The Lambda function's execution role
- B. The IAM role attached to the **target** (per-target `RoleArn`)
- C. The role of the user who created the rule
- D. No role is needed; Lambda trusts the events service implicitly

<details><summary>Show answer</summary>

**B — The target's `RoleArn`.** EventBridge assumes this role to call `lambda:InvokeFunction`. The role's trust policy must allow `events.amazonaws.com`. The Lambda function's own execution role is what the **function** uses to call other services (S3, DynamoDB, etc.) — that's a separate role.

</details>

---

**Q3.** When a rule targets an SQS queue, does EventBridge need an execution role?

- A. Yes — every target requires an execution role
- B. No — SQS uses a resource policy on the queue; no `RoleArn` is needed on the target
- C. Only if the queue is in a different account
- D. Only if the queue is encrypted

<details><summary>Show answer</summary>

**B — No.** SQS uses resource-based policies, not role assumption. The queue needs a policy that allows `events.amazonaws.com` to call `sqs:SendMessage` (with an optional `Condition: ArnEquals` on `aws:SourceArn` for tighter scoping). The target itself has no `RoleArn`.

</details>

---

**Q4.** Is the default invocation mode for a Lambda target sync or async?

- A. Sync — EventBridge waits for the Lambda response
- B. Async — EventBridge invokes and returns immediately; the response is not captured
- C. Both — you can choose per target

<details><summary>Show answer</summary>

**B — Async.** EventBridge invokes Lambda asynchronously. Lambda returns `202 Accepted` and processes in the background. To fail the rule if Lambda fails, you'd need to invoke synchronously (rare). The default is async, with the retry policy + DLQ handling failures.

</details>

---

**Q5.** What is a **target ID** used for?

- A. Identifying the underlying AWS resource (Lambda function, SQS queue)
- B. Identifying a target **within a rule** so you can update or remove it
- C. Tagging the target with a cost center
- D. Naming the IAM role for the target

<details><summary>Show answer</summary>

**B — Identifying a target within a rule.** A rule can have multiple targets; each needs a unique `Id` (per rule) so `put_targets` can replace it and `remove_targets` can delete it. The target's underlying AWS resource is identified by its ARN, not the target ID.

</details>

---

**Q6.** What happens to a failed event if the target has no DLQ configured?

- A. The event is retried indefinitely
- B. The event is silently dropped after the retry policy exhausts
- C. The event is held in a default AWS-managed DLQ
- D. The rule is auto-disabled

<details><summary>Show answer</summary>

**B — Silently dropped.** Without a DLQ, EventBridge retries per the retry policy, then drops the event. A CloudWatch metric is incremented, but no event payload is preserved. For any critical target, **always configure a DLQ**.

</details>

---

**Q7.** In a `RetryPolicy`, what does `MaximumEventAgeInSeconds` control?

- A. The maximum number of retry attempts
- B. The oldest age of an event that will still be retried; older events go to the DLQ
- C. The SQS visibility timeout
- D. The Lambda function timeout

<details><summary>Show answer</summary>

**B — Total wall-clock age before giving up.** If an event is older than `MaximumEventAgeInSeconds` when a retry would fire, it goes to the DLQ (or is dropped) immediately. Useful for "this data is only useful for 5 minutes" use cases.

</details>

---

**Q8.** What kind of AWS resource is a **dead-letter queue (DLQ)** for an EventBridge target?

- A. An SNS topic
- B. A DynamoDB table
- C. An SQS queue
- D. An S3 bucket

<details><summary>Show answer</summary>

**C — An SQS queue.** The DLQ ARN passed in `DeadLetterConfig.Arn` is always an SQS ARN. The queue needs its own resource policy allowing `events.amazonaws.com` to call `sqs:SendMessage`. You can redrive messages from the DLQ back to the source flow once the underlying issue is fixed.

</details>

---

**Q9.** A Lambda function is the target of an EventBridge rule. The function returns a non-2xx status (e.g. a 500). What happens?

- A. EventBridge considers the invocation successful because the function was called
- B. EventBridge retries per the target's `RetryPolicy`; after exhaustion, sends the event to the DLQ
- C. EventBridge disables the rule automatically
- D. The rule is rolled back to a previous version

<details><summary>Show answer</summary>

**B — Retries per the policy, then DLQ.** A non-2xx response is a failure for EventBridge. The retry policy (`MaximumRetryAttempts`, `MaximumEventAgeInSeconds`) controls how many times and for how long it retries. After exhaustion, the event goes to the DLQ (if configured) or is dropped.

</details>

---

**Q10.** Which CloudWatch metric should you alarm on to detect a stuck DLQ?

- A. `AWS/Events` `SuccessfulInvocations`
- B. `AWS/SQS` `ApproximateNumberOfMessagesVisible` on the DLQ
- C. `AWS/Lambda` `Errors`
- D. `AWS/Events` `MatchedEvents`

<details><summary>Show answer</summary>

**B — `ApproximateNumberOfMessagesVisible` on the DLQ.** When the DLQ has any messages, that's a production incident — events are failing to reach their targets. A CloudWatch alarm with `threshold = 1` and `comparison-operator = GreaterThanOrEqualToThreshold` catches the moment messages start landing in the DLQ.

</details>
