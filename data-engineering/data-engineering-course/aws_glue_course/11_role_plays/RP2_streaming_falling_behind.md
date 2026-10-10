# Role Play 2 — Glue Streaming Job is Falling Behind

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Pacing:** 10-12 minutes total
> **Personas:**
> - **Ravi** (learner) — senior data engineer, owns the streaming pipeline
> - **Maya** (instructor / manager) — the user's engineering manager, asking pointed questions

## Scenario

Maya: *"Hey Ravi, the marketing team's real-time campaign attribution dashboard has been showing 2-hour-old data for the last 3 days. The product manager is asking me daily when it'll catch up. I checked the Glue Job run history and the streaming job is technically still running, but the batch latency p99 is 4 minutes now (it was 30 seconds 2 weeks ago). And the CloudWatch `glue.streaming.numRecordsProcessedPerBatch` metric is dropping. What's going on? Walk me through the diagnosis and what you'd do."*

You have 10 minutes. Be ready to:
1. Diagnose the likely root cause(s).
2. Propose a short-term fix and a long-term fix.
3. Communicate the trade-offs.
4. Get sign-off on a plan.

## Learning objectives

1. Recognize the **4 common streaming-job-degradation patterns**: batch size, worker count, downstream sink back-pressure, and Kinesis/Kafka throttling.
2. Read the **3 CloudWatch metrics** that matter for streaming Glue jobs: `glue.streaming.numRecordsProcessedPerBatch`, `glue.driver.streaming.batchProcessingTimeInMs`, `glue.driver.streaming.schemaDiscovered`.
3. Distinguish **mitigation** (a quick fix that buys you a week) from **remediation** (the right fix that lasts).
4. Practice **managing up** — give the manager a clear answer, a clear plan, and a clear ask.

## Opening (90 seconds)

> **Ravi:** "OK, before I jump in — let me make sure I understand the constraint. The marketing PM wants same-day data. Right now they're getting 2-hour-old data. The streaming job itself is up, just slow. And this started in the last 2 weeks, not the day it launched. Is that right?"
> **Maya:** "Yes."
> **Ravi:** "OK. Two more questions. Did we change anything 2 weeks ago — a new Glue version, a new schema, a bump in upstream traffic? And can I have 30 minutes to look at the CloudWatch metrics before I give you a plan?"

The senior move: **don't diagnose in the meeting**. Acknowledge the urgency, ask for a follow-up.

## Diagnosis (3-4 minutes, off-line, then summarized)

The 4 common causes, in order of likelihood for a 2-week-old regression:

1. **Upstream traffic increase.** 80% of the time, this is it. The batch size is correct, the workers are correct, but the producer (a Kinesis stream, an MSK topic, a Kafka stream) is now sending 3x the volume. The job can't keep up because the input rate exceeds the throughput.
2. **Schema drift.** The upstream producer added a new field. Glue is failing half the batches, retrying, and falling behind. Check `glue.driver.streaming.schemaDiscovered` and the Job run logs for `SchemaValidationException`.
3. **Downstream sink throttling.** The target (DynamoDB, S3, an HTTP API) is now rate-limiting. The job is processing fine but blocking on writes. Check `glue.driver.streaming.batchProcessingTimeInMs` — if it's high *and* the batch size is small, you're back-pressured.
4. **Resource under-provisioning.** Worker count was sized for the old volume. The fix is `NumberOfWorkers` from 5 to 10 (or change `WorkerType` from `G.025X` to `G.2X`).

The right diagnostic step: pull up the **3 CloudWatch metrics** and look at the trend. Upstream traffic increase → `numRecordsProcessedPerBatch` is high but `batchProcessingTimeInMs` is also high. Schema drift → `numRecordsProcessedPerBatch` is *variable*, with many 0-record batches. Downstream throttling → batch processing time is high but `numRecordsProcessedPerBatch` is small. Resource under-provisioning → all 3 are high.

## The plan (3 minutes)

> **Ravi:** "OK, I've looked at the metrics. Two things, in order."
>
> "**First**, the `numRecordsProcessedPerBatch` is up 4x, and the upstream Kinesis `IncomingBytes` is up 3.2x. So we're processing more records per batch but the *rate* at which we drain the stream is still the same — we have a capacity problem, not a correctness problem. That's the immediate cause of the 4-minute p99."
>
> "**Second**, the schema for the `attribution` field drifted on the 14th. The new schema has a `null` for `campaign_id` that the old schema didn't. The job is failing ~12% of batches and retrying. That's why the throughput dropped *and* the marketing dashboard is 2 hours stale — the retries are blocking new batches."
>
> "**Short-term fix** (today): bump `NumberOfWorkers` from 5 to 10, and pin the schema with `--schema-pinned` and `--schema-version-id` so we don't keep discovering the new one. This will get us back to sub-30s latency by tomorrow."
>
> "**Long-term fix** (this sprint): work with the producer team to either revert the schema drift or formally version it. I want a 2-hour SLA on schema-change notifications, not 0."
>
> "**What I need from you**: sign-off on the worker-count bump, and 30 min with the producer team's EM to talk about the schema contract."

## What the role play tests

- **Diagnostic skill** — use the right metrics, in the right order.
- **Engineering judgment** — separate symptom (slow) from cause (schema + capacity).
- **Communication** — give the manager a 3-paragraph answer, not a 30-paragraph one.
- **Prioritization** — fix the immediate pain today, fix the systemic issue this sprint.

## Common mistakes learners make in this role play

- **Jumping straight to "add more workers."** That's the easy answer, and it ignores the schema-drift problem. If you only fix the capacity, the 2-hour staleness stays because the retries are still blocking.
- **Blaming the producer team.** "They broke the schema" is true but useless. The right answer is "we need a 2-hour SLA on schema notifications" — a process change, not a finger-point.
- **Over-promising on the fix time.** "I'll have it fixed by EOD" is unrealistic if the upstream is Kinesis with 24-hour retention. The right answer is "sub-30s by tomorrow morning."
- **Not asking for the follow-up.** A senior DE always ends with "what I need from you." If you don't, the manager is left wondering what to do with the info.
