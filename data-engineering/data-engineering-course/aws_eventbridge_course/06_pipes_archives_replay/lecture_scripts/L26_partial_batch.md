---
lecture: L26
title: "Partial Batch Response — Failure Isolation for SQS, Kinesis, and DynamoDB"
duration: "8:00"
section: 6
prereqs:
  - L25
downloads:
  - "../../downloads/eventbridge_cheat_sheet.pdf"
---

# L26 — Partial Batch Response — Failure Isolation for SQS, Kinesis, and DynamoDB

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 6 — Pipes + Archives + Replay
> **Duration:** 8:00

## Prereqs

- Watched **L25 — Pipes 101** so you know the four stages of a
  Pipe and which sources support batching.
- Watched **L19 — Dead-Letter Queues + Retry Policies** so you
  understand what happens when an event target fails on a single
  event.

## Key terms

- **Batch** — a group of records delivered to the target in one
  invocation. SQS supports up to 10 messages per batch; Kinesis
  and DynamoDB Streams can deliver up to 10,000 records per
  shard-poll.
- **All-or-nothing** — the default for an unconfigured target:
  if **any** record in the batch fails, the entire batch is
  retried. Bad poison-message behavior.
- **Partial batch response** — the opt-in behavior where the
  target returns a list of which record IDs failed, and only those
  are retried. Implemented in Lambda via the
  `reportBatchItemFailures` function response field.
- **`ReportBatchItemFailures`** — the JSON-pointer language used
  inside a partial batch failure response. Tells the source
  "retry this specific item" without retrying the whole batch.
- **Poison message** — a single bad record that causes the
  consumer to fail. Without partial batch response, the same
  poison message gets retried forever.

## Lecture

Hi, I'm Prem Vishnoi. In L25 we learned the four stages of a Pipe.
Today we are going to focus on the single most useful feature in
Pipes for production: **partial batch response**. Without it, a
single bad record in a batch of 1,000 will cause the entire batch
to retry until the messages expire and land in the DLQ. With it,
the bad record is the only thing that retries.

### The problem — all-or-nothing batches

When a Pipe reads from a **batched** source (SQS, Kinesis,
DynamoDB Streams), the service groups records into a batch and
delivers the batch to the target in a single call. For a Lambda
target, that means a single Lambda invocation receives N records
at once.

The default failure behavior is brutal:

1. Lambda receives 10 SQS messages.
2. Lambda fails on message 7 (poison message — malformed JSON,
   missing required field, downstream API 4xx).
3. The Pipe sees the Lambda invocation as a failure.
4. The Pipe **redelivers all 10 messages** to Lambda.
5. Lambda fails on message 7 again.
6. After the max-retry count, **all 10 messages** land in the DLQ.
7. You now have 9 good messages in the DLQ mixed in with 1 bad
   one, and you cannot easily tell which is which.

This is "all-or-nothing" retry. It is the worst-case outcome of
any queued workload.

### The fix — partial batch response

If the target returns a list of which records failed, the Pipe
service retries **only those**. The mechanism depends on the
target type, but for Lambda (the most common target) it is the
`reportBatchItemFailures` function response field:

```python
def lambda_handler(event, context):
    failed_ids = []
    for record in event["Records"]:
        try:
            process(record)
        except PoisonMessageError:
            failed_ids.append(record["messageId"])

    return {
        # THIS is the magic. Without it, all-or-nothing.
        # With it, only the listed IDs are retried.
        "batchItemFailures": [
            {"itemIdentifier": id_} for id_ in failed_ids
        ],
    }
```

That is the entire mechanism. Three lines of code change the
failure semantics from "all-or-nothing" to "retry only the bad
ones."

### How to enable it on a Pipe

You have to **opt in** to partial batch response when you create
the Pipe:

```python
pipes.create_pipe(
    Name="orders-to-enriched-s3",
    Source="arn:aws:sqs:us-east-1:111122223333:orders-queue",
    Target="arn:aws:lambda:us-east-1:111122223333:function:process-order",
    TargetParameters={
        "LambdaParameters": {
            "InvocationType": "REPORT_BATCH_ITEM_FAILURES",
        },
    },
    RoleArn="arn:aws:iam::111122223333:role/pipe-role",
)
```

The `LambdaParameters.InvocationType` field is the toggle. The
default is `REQUEST_RESPONSE` (which still works but treats any
Lambda error as a full-batch failure). Setting it to
`REPORT_BATCH_ITEM_FAILURES` is the opt-in.

### How `ReportBatchItemFailures` works per source

The "item identifier" you put in the response depends on the
source:

| Source | `itemIdentifier` is |
|---|---|
| SQS | the `messageId` from the SQS event |
| Kinesis | the `sequenceNumber` of the Kinesis record |
| DynamoDB Streams | the `sequenceNumber` of the DynamoDB record |
| Kafka | the `offset` of the Kafka record |
| Amazon MQ | the `messageId` of the MQ message |

So the Lambda's loop looks slightly different for each source. A
common pattern is to detect the source from the event shape:

```python
def lambda_handler(event, context):
    failed = []
    for record in event["Records"]:
        try:
            process(record)
        except Exception:
            if record["eventSource"] == "aws:sqs":
                failed.append(record["messageId"])
            elif record["eventSource"] == "aws:kinesis":
                failed.append(record["kinesis"]["sequenceNumber"])
            elif record["eventSource"] == "aws:dynamodb":
                failed.append(record["dynamodb"]["SequenceNumber"])
            else:
                raise
    return {"batchItemFailures": [{"itemIdentifier": x} for x in failed]}
```

You can also use the more uniform "any failure → fail the whole
batch" pattern by **not** returning `batchItemFailures` and
letting the Lambda throw. The Pipe service retries the full batch
in that case (legacy all-or-nothing).

### Cost and quota trade-offs

Partial batch response is **free** — there is no extra charge for
enabling it. The trade-off is purely in how Lambda is invoked:

- **With `REQUEST_RESPONSE` + batch failure:** the entire batch is
  re-delivered; cost is "N records × retry count."
- **With `REPORT_BATCH_ITEM_FAILURES`:** only the failed records
  are re-delivered; cost is "1 record × retry count."

For workloads with >1% poison-message rate, partial batch response
saves real money. For workloads with very low failure rates, the
savings are negligible.

### Failure modes you still need to handle

Partial batch response fixes poison messages. It does **not**
fix:

1. **Max-retry-exceeded.** If a record fails 3 times (the default
   max-retry count for a Pipe), it lands in the DLQ — even with
   partial batch response. You still need a DLQ.
2. **Lambda timeouts.** If the entire batch times out (because
   1,000 records × 10ms each = 10 seconds, longer than the
   timeout), the batch fails as a whole. Mitigate with smaller
   batches or longer timeouts.
3. **Lambda out-of-memory.** If a 10,000-record batch OOMs the
   Lambda, the whole batch fails. Mitigate with smaller batches.
4. **Permanent errors.** A `400 Bad Request` from a downstream
   API will retry forever with the same result. Use partial
   batch response *plus* a max-retry count *plus* a DLQ for
   permanent failures.

### Best-practice recipe

For a production Pipe with a Lambda target, the recipe is:

1. **Source:** SQS standard queue, batch size 10.
2. **Filter:** the event pattern.
3. **Enrichment:** (optional) a Lambda that adds metadata.
4. **Target:** Lambda with `InvocationType =
   "REPORT_BATCH_ITEM_FAILURES"`.
5. **Lambda code:** returns `{"batchItemFailures": [...]}` with
   only the failed record IDs.
6. **Max retry count:** 3.
7. **DLQ:** an SQS queue, with a CloudWatch alarm on
   `ApproximateNumberOfMessagesVisible > 0`.

That configuration is what you would ship in a real system.

## Hands-on

There is no code lab for this lecture. The pattern is so simple
that you can implement it inline in any Lambda. If you want to
test it, create a Pipe with an SQS source and a Lambda target.
Send 5 messages to the queue, 1 of which is malformed JSON. With
partial batch response enabled, the 4 good messages should
process successfully and the 1 bad one should retry up to max-retry
times and then land in the DLQ — without the 4 good messages
ending up in the DLQ.

## Quiz prep

These are the section-6 questions to focus on:

- How do you opt in to partial batch response in a Pipe?
- What is the `itemIdentifier` for an SQS message? (the
  `messageId`)
- Without partial batch response, what happens to a batch of 10
  messages when 1 fails? (the whole batch is retried)

## Further reading

- AWS docs: [Partial batch failure handling](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes-batching-concurrency.html)
- AWS docs: [Lambda `reportBatchItemFailures`](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html#services-sqs-batchfailures)
- AWS blog: [Batch failure handling for SQS](https://aws.amazon.com/blogs/compute/handling-failures-aws-lambda-functions-aws-sqs-queues/)
- `../../SYLLABUS.md` — full lecture map.

## What's next

In **L27** we move on to **Archives** — the event-backup feature
that lets you retain every event on a bus for up to 30 days,
*exactly* as it flowed. Archives are the input to the Replay
feature in L28.

**Ready? Let's talk about event durability.**
