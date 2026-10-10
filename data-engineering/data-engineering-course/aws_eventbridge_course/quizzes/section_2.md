# Section 2 Quiz — EventBus Basics

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** What is the literal name of the event bus that AWS
auto-creates in every account, in every region?

- A. `aws-default`
- B. `default`
- C. `event-bus`
- D. `acme-orders`

<details><summary>Show answer</summary>

**B — `default`.** It is undeletable and has a managed resource
policy that allows AWS service principals to publish to it.

</details>

---

**Q2.** Which of these is a true statement about an EventBridge bus?

- A. It is global (one per AWS account)
- B. It is regional and account-scoped
- C. It is regional but shared across all accounts automatically
- D. It is account-scoped but global across regions

<details><summary>Show answer</summary>

**B — Regional and account-scoped.** A bus lives in one
(account, region). Same name in two regions is two different buses.

</details>

---

**Q3.** Which boto3 API call creates a custom event bus?

- A. `events.create_event_bus(Name=...)`
- B. `events.put_event_bus(Name=...)`
- C. `events.register_bus(Name=...)`
- D. `events.new_bus(Name=...)`

<details><summary>Show answer</summary>

**A — `events.create_event_bus(Name=...)`.** If the bus already
exists, boto3 raises
`ResourceAlreadyExistsException` — which our script catches and
treats as a successful no-op.

</details>

---

**Q4.** Which boto3 API attaches a **resource policy** to a bus?

- A. `events.put_event_bus_policy(...)`
- B. `events.put_permission(EventBusName=..., Policy=...)`
- C. `events.attach_policy(...)`
- D. `events.set_bus_policy(...)`

<details><summary>Show answer</summary>

**B — `events.put_permission(EventBusName=..., Policy=...)`.** The
`Policy` parameter must be a JSON *string*, not a Python dict.

</details>

---

**Q5.** What is the required name prefix for a **partner** event
bus?

- A. `aws.events.partner/`
- B. `partner/`
- C. `aws.partner/`
- D. `saas/`

<details><summary>Show answer</summary>

**C — `aws.partner/`.** For example, the Zendesk partner bus is
`aws.partner/zendesk.com`. This prefix is how AWS recognizes a bus
as a partner bus.

</details>

---

**Q6.** What does the **idempotent** pattern in
`ensure_event_bus` rely on?

- A. Re-running the script always creates a new bus with a
  timestamped name
- B. Catching `ResourceAlreadyExistsException` on
  `CreateEventBus` and re-fetching the ARN via `DescribeEventBus`
- C. Using `wait_for_bus_to_exist` before creating
- D. Locking the bus with a DynamoDB conditional write

<details><summary>Show answer</summary>

**B — Catch `ResourceAlreadyExistsException` on `CreateEventBus`
and re-fetch the ARN via `DescribeEventBus`.** That's the
production-grade idempotency pattern: first call creates, second
call hits the exception, third call also hits the exception — and
in all cases you get back the same ARN.

</details>

---

**Q7.** What does the `--dry-run` flag in
`create_event_bus.py` do?

- A. Calls `DeleteEventBus` so the script has no net effect
- B. Builds the boto3 client but does not actually call any AWS API
- C. Short-circuits before any boto3 client is built; prints what
  *would* happen; returns exit code 0
- D. Runs the script against a sandbox account

<details><summary>Show answer</summary>

**C — Short-circuits before any boto3 client is built; prints what
*would* happen; returns exit code 0.** The test suite proves this
by patching `boto3.client` with a `MagicMock` and asserting it
was never called.

</details>

---

**Q8.** Which of the following is a good reason to create a custom
bus instead of using the default bus?

- A. To receive events from AWS services in your account
- B. To isolate unrelated event flows and to opt-in to events instead
  of getting everything AWS publishes by default
- C. Custom buses are cheaper than the default bus
- D. The default bus is in `us-east-1` only

<details><summary>Show answer</summary>

**B — To isolate unrelated event flows and to opt-in to events
instead of getting everything AWS publishes by default.** Custom
buses are *also* free, but the main reason is isolation and
explicit control over which events appear.

</details>

---

**Q9.** In the ARN
`arn:aws:events:us-east-1:111122223333:event-bus/aws.partner/zendesk.com`,
what does `aws.partner` represent?

- A. The AWS region
- B. The AWS account ID
- C. The prefix that marks this as a partner event bus
- D. The IAM role assumed by the partner

<details><summary>Show answer</summary>

**C — The prefix that marks this as a partner event bus.** Every
partner bus has a name that begins with `aws.partner/`.

</details>

---

**Q10.** Section 2's working demo, `create_event_bus.py`, is best
described as:

- A. A CloudFormation template that deploys an event bus
- B. An idempotent boto3 script that creates a custom bus,
  attaches a resource policy, lists all buses, and supports
  `--dry-run`
- C. A Lambda function that consumes events from a bus
- D. A CDK app that defines an event bus in TypeScript

<details><summary>Show answer</summary>

**B — An idempotent boto3 script that creates a custom bus,
attaches a resource policy, lists all buses, and supports
`--dry-run`.** It is fully tested with `moto` — 9 tests, no AWS
account required.

</details>