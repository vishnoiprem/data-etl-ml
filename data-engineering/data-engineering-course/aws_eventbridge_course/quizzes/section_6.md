# Section 6 Quiz — Pipes + Archives + Replay

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

---

**Q1.** Which best describes the shape of an EventBridge Pipe?

- A. Event bus → rule → target (pub/sub)
- B. Source → optional filter → optional enrichment → target
  (point-to-point)
- C. Target → enrichment → filter → source
- D. Many targets per source, many sources per target

<details><summary>Show answer</summary>

**B — Source → optional filter → optional enrichment → target
(point-to-point).** A Pipe is a four-stage pipeline. The source
and target are required (one of each); the filter and enrichment
are optional. Unlike a rule, a Pipe can have **only one target**.

</details>

---

**Q2.** Which is **not** a valid source for an EventBridge Pipe?

- A. SQS queue
- B. Kinesis stream
- C. DynamoDB stream
- D. SNS topic

<details><summary>Show answer</summary>

**D — SNS topic.** SNS is a *target* (rules can fan out to it),
not a source for Pipes. Pipe sources are pull-based (SQS,
Kinesis, DynamoDB Streams, Kafka, MQ) plus another event bus. SNS
is push-based and is consumed by subscribers, not by Pipes.

</details>

---

**Q3.** Without partial batch response, what happens to a batch
of 10 SQS messages when 1 of them is a poison message?

- A. Only the 1 poison message is retried; the 9 good ones are
  marked complete
- B. The 9 good messages are retried along with the poison
  message; all 10 may end up in the DLQ
- C. The 9 good messages are silently dropped
- D. The Lambda invocation is canceled

<details><summary>Show answer</summary>

**B — All 10 are retried together, and all 10 may end up in the
DLQ.** Without partial batch response, the failure of any single
record in the batch is treated as a failure of the entire batch.
The fix is to enable
`TargetParameters.LambdaParameters.InvocationType = "REPORT_BATCH_ITEM_FAILURES"`
and have the Lambda return
`{"batchItemFailures": [{"itemIdentifier": "<id>"}, ...]}`.

</details>

---

**Q4.** What is the `itemIdentifier` in a partial batch response
for an **SQS** source?

- A. The SQS `messageId`
- B. The SQS `sequenceNumber`
- C. The SQS `receiptHandle`
- D. The SQS `md5OfBody`

<details><summary>Show answer</summary>

**A — The SQS `messageId`.** Each source has its own identifier:
SQS uses `messageId`, Kinesis uses `sequenceNumber`, DynamoDB
Streams uses `SequenceNumber`, Kafka uses `offset`. The
`receiptHandle` and `md5OfBody` are not the right identifiers for
the partial batch response.

</details>

---

**Q5.** How long does an EventBridge Archive retain events?

- A. 7 days
- B. 30 days (hard limit)
- C. 90 days
- D. Configurable from 1 to 365 days

<details><summary>Show answer</summary>

**B — 30 days, hard limit.** You cannot choose a different
retention. If you need longer, the standard pattern is to also
send archived events to S3 for permanent storage.

</details>

---

**Q6.** An Archive is attached to which resource?

- A. A rule
- B. A target
- C. An event bus
- D. A Pipe

<details><summary>Show answer</summary>

**C — An event bus.** An Archive's source is always a single
event bus (typically a custom bus, not the default bus). It
captures every event that flows through the bus, optionally
filtered by an event pattern.

</details>

---

**Q7.** Is `start_replay` idempotent?

- A. Yes — running it twice with the same time range is a no-op
- B. No — running it twice with the same time range re-delivers
  the events to the destination a second time
- C. Yes — but only if you use the same `ReplayName`
- D. No — but the second call is automatically rejected

<details><summary>Show answer</summary>

**B — No, replays are not idempotent.** Running `start_replay`
twice with the same `EventStartTime` and `EventEndTime` will
re-deliver the same events to the destination. Targets must be
idempotent (use `event.id` as a dedup key) to handle this safely.

</details>

---

**Q8.** What is the main use case for an Archive + Replay?

- A. Faster event delivery
- B. Lower cost than a rule
- C. Backfill / reconciliation / forensic replay of past events
- D. Encrypting events at rest

<details><summary>Show answer</summary>

**C — Backfill / reconciliation / forensic replay of past
events.** The other options are not what archives are for.
Encryption at rest is a side benefit (KMS is mandatory) but not
the primary use case. The primary use case is being able to
*re-deliver* events from the past 30 days to a target — for
debugging, for backfilling a new system, or for rebuilding state
after a bug.

</details>

---

**Q9.** A Pipe has how many targets?

- A. Up to 5, like a rule
- B. Exactly 1
- C. Up to 10
- D. As many as the source supports

<details><summary>Show answer</summary>

**B — Exactly 1.** Pipes are *point-to-point*: one source, one
target. If you need fan-out to many consumers, use a rule on an
event bus. The complementarity is the whole point: rules for
1-to-many, pipes for point-to-point.

</details>

---

**Q10.** When a Pipe's enrichment Lambda runs, what does its
return value do?

- A. It is logged but otherwise ignored
- B. It **replaces** the event payload that is delivered to the
  target
- C. It is appended to the event's `detail` field
- D. It is sent to the DLQ if the target fails

<details><summary>Show answer</summary>

**B — The return value replaces the event payload.** The
enrichment Lambda is a transformation step: whatever it returns
becomes the new event. This is the killer feature of a Pipe —
you can reshape, enrich, and rewrite the event in a single
Lambda call, with no consumer code to write.

</details>
