# Section 7 Quiz — Patterns + Real-World

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> 12 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

---

**Q1.** Which of the following is **not** one of the 10 most common
EventBridge patterns from L30?

- A. S3 → Lambda
- B. CloudWatch Alarm → SNS
- C. EC2 instance reboot → Auto Scaling
- D. API Gateway → Step Functions

<details><summary>Show answer</summary>

**C — EC2 instance reboot → Auto Scaling.** "EC2 reboot" is not an
EventBridge event source; EC2 lifecycle events (launch, terminate,
stop) are, but a reboot is not. Patterns A, B, and D are all in the
L30 catalog. Auto Scaling group management belongs in a different
class of AWS service.

</details>

---

**Q2.** For an S3 → EventBridge → Lambda ingestion pattern, which
event pattern correctly matches **only** `ObjectCreated:Put` events
on a specific bucket?

- A. `{"source": ["aws.s3"]}`
- B. `{"source": ["aws.s3"], "detail-type": ["Object Created"], "detail": {"bucket": {"name": ["my-bucket"]}}}`
- C. `{"detail-type": ["ObjectCreated:Put"]}`
- D. `{"source": ["s3.amazonaws.com"]}`

<details><summary>Show answer</summary>

**B.** The S3 → EventBridge integration normalizes the `detail-type`
to `Object Created` (with a space), and you must filter on both
`source` (`aws.s3`) and `bucket.name` to avoid the rule firing for
every bucket in the account. Option A would match every S3 event;
option C uses the wrong `detail-type`; option D uses the wrong
`source` value.

</details>

---

**Q3.** In the CloudWatch Alarm → SNS pattern, why is the
`detail.state.value: ["ALARM"]` filter required on the rule?

- A. Without it, the rule would not fire at all
- B. Without it, the rule would fire for every alarm state change (including OK → OK), hammering the SNS topic
- C. SNS cannot accept OK-state events
- D. It is required by IAM, not by EventBridge

<details><summary>Show answer</summary>

**B.** CloudWatch publishes a synthetic state change for every
evaluation period, so without the `state.value` filter, the rule
fires for every OK → OK and INSUFFICIENT_DATA → INSUFFICIENT_DATA
transition. The SNS topic gets hammered and the on-call engineer
gets phantom pages.

</details>

---

**Q4.** In the API Gateway → EventBridge → Step Functions pattern,
what is the **primary** reason to put EventBridge between API
Gateway and Step Functions rather than wiring API Gateway directly
to Step Functions?

- A. EventBridge is cheaper than a direct integration
- B. The indirection gives you archive/replay, fan-out to multiple consumers, and a built-in DLQ with retry
- C. Step Functions cannot be a direct API Gateway integration target
- D. The Step Functions IAM role is not needed with EventBridge

<details><summary>Show answer</summary>

**B.** A direct API Gateway → Step Functions integration works, but
you lose archive/replay (events are lost if the integration
fails), fan-out (one-to-one only), and the native DLQ + retry
behavior. The EventBridge indirection is the production-grade
answer for any customer-facing long-running async API.

</details>

---

**Q5.** Which DLQ pattern is the right choice when you have fewer
than ~20 rules, all owned by the same team?

- A. Per-target DLQ
- B. Cross-target DLQ
- C. No DLQ
- D. Per-event DLQ

<details><summary>Show answer</summary>

**B — Cross-target DLQ.** When you have a small number of rules
owned by a single team, a single shared SQS DLQ with a depth
alarm is the simplest topology. Per-target DLQs add operational
overhead without much benefit at this scale. There is no such
thing as a "no DLQ" or "per-event" DLQ in production.

</details>

---

**Q6.** Which DLQ pattern is the right choice when you have 50+
rules owned by different teams, and a compliance requirement that
each team's failures be isolated?

- A. Cross-target DLQ
- B. Per-target DLQ
- C. Self-healing re-drive only
- D. No DLQ (let the events drop)

<details><summary>Show answer</summary>

**B — Per-target DLQ.** When failure isolation is a compliance
requirement, and you have enough rules that one team's failures
should not page another team, per-target DLQs are the answer.
Each team gets its own SQS queue, its own depth alarm, and its
own page path. The cost is higher but the on-call clarity is
worth it.

</details>

---

**Q7.** For a self-healing re-drive Lambda that moves messages
from a DLQ back to the original target, which property of the
target is **most** important?

- A. The target must be in the same region as the DLQ
- B. The target must be idempotent on re-drive, so a duplicate event does not cause a duplicate side effect
- C. The target must be a Lambda (not SNS or SQS)
- D. The target must log to a specific CloudWatch Log Group

<details><summary>Show answer</summary>

**B — Idempotency.** A re-drive Lambda replays the original event,
which means the target sees the event twice (or more) for any
transient failure. If the target is not idempotent — for example,
if it processes a payment or sends an email — the re-drive creates
duplicates. Always enforce a dedupe key (SQS `MessageDeduplicationId`,
DynamoDB conditional write, etc.) at the target before wiring a
re-drive Lambda.

</details>

---

**Q8.** In the cross-account event bus pattern, which AWS construct
controls who can call `PutEvents` on a custom bus in the consumer
account?

- A. The rule's IAM role
- B. The producer account's IAM user policy
- C. The event bus **resource policy** attached to the custom bus
- D. The producer account's VPC endpoint policy

<details><summary>Show answer</summary>

**C — The event bus resource policy.** Every custom event bus has
a resource-based policy (similar in shape to an S3 bucket policy)
that gates who can call `PutEvents`. The rule's IAM role, the
producer's IAM user policy, and the VPC endpoint policy are all
involved in the cross-account flow, but the **gate** is the bus's
resource policy.

</details>

---

**Q9.** What is the **organization-wide event bus** feature
introduced in 2023?

- A. A single bus per AWS Organization that every member account can `PutEvents` to, with no resource policy edits
- B. A new IAM role for organization-wide service access
- C. A replacement for AWS Control Tower
- D. A new event source for AWS Organizations service events only

<details><summary>Show answer</summary>

**A.** The organization-wide event bus is a single bus in the
management account that every member account in the AWS
Organization can `PutEvents` to. The `aws:PrincipalOrgID` condition
in the bus's policy is set automatically; you do not edit the
policy when a new member account is added. This is the cleanest
pattern for multi-account event fan-out at scale.

</details>

---

**Q10.** When a CW Alarm → EventBridge → SNS rule fires with the
SSM runbook target succeeding, what is the recommended paging
behavior?

- A. Page the on-call engineer regardless
- B. Do not page; post a low-priority Slack message only
- C. Send an SMS to the CEO
- D. Disable the alarm

<details><summary>Show answer</summary>

**B — Do not page; post to Slack only.** The whole point of the
SSM auto-remediation path is that the system fixes itself. The
on-call engineer is only paged when the SSM runbook itself fails.
A low-priority Slack message keeps the rest of the team informed
without spamming the on-call. Paging on success defeats the
self-healing pattern.

</details>

---

**Q11.** Which EventBridge target type is **not** natively
supported as a direct rule target (without a Lambda in the middle)?

- A. Lambda
- B. SNS topic
- C. Step Functions state machine
- D. None of the above — EventBridge supports all three as direct targets

<details><summary>Show answer</summary>

**D — All three are direct targets.** EventBridge supports Lambda,
SNS, SQS, Step Functions, ECS tasks, Kinesis Streams, Kinesis
Data Firehose, API Gateway, CodePipeline, SSM runbooks, and other
event buses as direct rule targets. You can wire any of them in
the console without an intermediate Lambda. The patterns in
L31–L33 use this direct-target capability throughout.

</details>

---

**Q12.** Which of the following is the **least** useful next step
after finishing the EventBridge Crash Course?

- A. Standing up the S3 → Lambda pattern from L31 in your own account with CDK
- B. Adding an organization-wide event bus + archive and replaying an event from your own account
- C. Re-reading the EventBridge FAQs once a year to track new features
- D. Ignoring EventBridge for the next 12 months and only revisiting if a future project needs it

<details><summary>Show answer</summary>

**D — Ignoring EventBridge for 12 months.** The service is moving
fast (org-wide bus in 2023, SQS Re-drive in 2024, schema-registry
updates in 2025). The patterns from L30 are durable, but the
specific features and quotas shift quarterly. The single best
investment of an hour a year is re-reading the EventBridge FAQs;
that keeps the patterns fresh against the new feature surface.
A, B, and C are all good next steps.

</details>
