# Section 1 Quiz — Foundations

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** How many working boto3 + moto code demos anchor this course?

- A. 1
- B. 3
- C. 5
- D. 7

<details><summary>Show answer</summary>

**C — 5.** They are: `create_event_bus.py` (section 2), `put_rule.py`
(section 3), `put_targets.py` (section 4), `schedule_cron.py`
(section 5), and `archive_replay.py` (section 6).

</details>

---

**Q2.** Which of the following is the **best** definition of an
**event** in event-driven architecture?

- A. A future-tense request that names a specific consumer
- B. A past-tense JSON fact about something that happened; producers
  do not address specific consumers
- C. A durable record stored in a queue until a worker takes it
- D. A binary blob exchanged between two microservices

<details><summary>Show answer</summary>

**B — A past-tense JSON fact that producers do not address at
specific consumers.** "Order Placed" is past tense; the producer
doesn't know who, if anyone, will react.

</details>

---

**Q3.** Which AWS service is the direct predecessor of EventBridge?

- A. AWS Step Functions
- B. Amazon MQ
- D. Amazon SNS Classic
- D. CloudWatch Events

<details><summary>Show answer</summary>

**D — CloudWatch Events.** Launched in 2016; superseded in July 2019
when EventBridge added SaaS partner sources, schema registry,
archives/replay, and cross-account buses.

</details>

---

**Q4.** Which statement best distinguishes **pub/sub** from a
**message queue**?

- A. Pub/sub delivers each message to *one* consumer; a queue
  delivers to all subscribers
- B. Pub/sub delivers each message to *every* subscriber; a queue
  delivers to *one* consumer per message
- C. Pub/sub requires durable storage; a queue does not
- D. There is no real difference; the terms are synonyms

<details><summary>Show answer</summary>

**B — Pub/sub = fanout to every subscriber; queue = one consumer
per message.** Pub/sub is for broadcasts and notifications; a queue is
for work distribution with back-pressure.

</details>

---

**Q5.** Which of the following is **not** a category of event source
in EventBridge?

- A. AWS services
- B. SaaS partners
- C. Custom applications via `PutEvents`
- D. SMS messages from end users

<details><summary>Show answer</summary>

**D — SMS messages from end users.** The three categories are AWS
services, SaaS partners, and custom apps via `PutEvents`. SMS is
not an EventBridge source.

</details>

---

**Q6.** Which of these is the **strongest** reason to use a
synchronous call instead of an event-driven design?

- A. You want decoupling between producer and consumer
- B. You need an immediate answer (e.g. a login session token)
- C. You want multiple consumers to react to the same fact
- D. You want to add a new consumer without changing the producer

<details><summary>Show answer</summary>

**B — You need an immediate answer.** A login API can't fire an
event and then "see what comes back" — the user is waiting on the
session token. The other three are reasons to use an
event-driven design.

</details>

---

**Q7.** Which AWS region is recommended as the default for this
course?

- A. `eu-west-1`
- B. `ap-southeast-1`
- C. `us-west-2`
- D. `us-east-1`

<details><summary>Show answer</summary>

**D — `us-east-1`.** Same default as the Lambda course — most
services and most partner event sources are most reliably available
there, and the demo scripts assume it.

</details>

---

**Q8.** Which statement about pub/sub, queues, and streams is
correct?

- A. All three have per-consumer offsets so you can replay
- B. Pub/sub and queues both fan out to every consumer
- C. Only streams retain all events for replay by multiple consumers
- D. Kinesis is a pub/sub system with one consumer per message

<details><summary>Show answer</summary>

**C — Only streams (Kinesis, Kafka, DynamoDB Streams) retain all
events and let multiple consumers track their own offset.** Pub/sub
(EventBridge, SNS) does not retain by default, and queues delete
on process.

</details>

---

**Q9.** Which of the four capabilities did EventBridge add on top of
CloudWatch Events?

- A. Lambda invocations, CloudWatch metrics, IAM, KMS encryption
- B. SaaS partner sources, schema registry, archives/replay,
  cross-account buses
- C. S3 triggers, DynamoDB streams, API Gateway, Step Functions
- D. EC2, S3, IAM, VPC

<details><summary>Show answer</summary>

**B — SaaS partner sources, schema registry, archives/replay, and
cross-account buses.** Those are the four features that
distinguish EventBridge (2019) from CloudWatch Events (2016).

</details>

---

**Q10.** Section 1 is best described as:

- A. An optional appendix covering advanced EventBridge APIs
- B. The conceptual foundation — vocabulary you'll use in every
  later section
- C. A CloudFormation / CDK-only module
- D. A hands-on Bedrock GenAI deep dive

<details><summary>Show answer</summary>

**B — The conceptual foundation.** Sections 2–7 all build on the
event-driven, pub/sub, and "why EventBridge" vocabulary we set up
here.

</details>