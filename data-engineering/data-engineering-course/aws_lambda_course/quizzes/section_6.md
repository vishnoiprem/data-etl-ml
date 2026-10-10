# Section 6 Quiz — Enterprise Use Case 1: S3, Lambda, DynamoDB

> **Source lectures:** L23, L24
> **Total questions:** 10
> **Pass bar:** 7 / 10

Answers are at the bottom in a collapsible block. Try the quiz cold first.

---

**Q1.** A bank wants to ingest a daily batch of transactions from a card
processor. The processor uploads a JSON file to an S3 bucket; the bank
wants the rows in DynamoDB within minutes, with no EC2 and no polling.
Which AWS architecture is the best fit?

- A. An EC2 instance running `cron` every 5 minutes, scanning the bucket
  and writing to DynamoDB.
- B. A Lambda function triggered by an S3 `ObjectCreated:Put` event
  notification, writing one `PutItem` per record.
- C. A CloudWatch Events scheduled rule that invokes a Lambda function
  every 5 minutes.
- D. A second S3 bucket with replication to DynamoDB Streams.

<details><summary>Show answer</summary>

**B.** This is the canonical event-driven S3 -> Lambda -> DynamoDB
pattern. (A) requires a server, (C) is polling dressed up as a
schedule, (D) is not a real feature.
</details>

---

**Q2.** Which S3 event type is the right trigger for the pipeline in Q1?

- A. `s3:ObjectCreated:CompleteMultipartUpload`
- B. `s3:ObjectCreated:Post`
- C. `s3:ObjectCreated:Put`
- D. `s3:ReducedRedundancyLostObject`

<details><summary>Show answer</summary>

**C.** The processor uploads via a single `PUT`, so `Put` is the right
event. (A) is for multi-part uploads of large files; (B) is for
HTML form uploads; (D) is unrelated.
</details>

---

**Q3.** The processor occasionally re-uploads the *same* JSON file. You
do not want duplicate rows in DynamoDB. What is the correct guard?

- A. A read-before-write check (`GetItem` then `PutItem`).
- B. `ConditionExpression="attribute_not_exists(transaction_id)"` on
  the `PutItem`.
- C. A Lambda reserved concurrency of 1.
- D. A DynamoDB Global Secondary Index with `transaction_id` as the
  partition key.

<details><summary>Show answer</summary>

**B.** A write-time conditional check is atomic, race-free, and cheaper
than a read-then-write. (A) is racy and two-of-them running in parallel
will both write; (C) serializes invocations but does not help across
separate processes; (D) does not enforce uniqueness.
</details>

---

**Q4.** When a duplicate `PutItem` is rejected by the
`attribute_not_exists` condition, DynamoDB raises:

- A. `ProvisionedThroughputExceededException`
- B. `ConditionalCheckFailedException`
- C. `TransactionConflictException`
- D. `ItemSizeTooLarge`

<details><summary>Show answer</summary>

**B.** That is the canonical "your condition was not met" error from
DynamoDB.
</details>

---

**Q5.** The Lambda function's IAM execution role needs `PutItem` on the
`transactions` table. Which resource ARN is the *least-privilege* form?

- A. `*`
- B. `arn:aws:dynamodb:us-east-1:*:table/*`
- C. `arn:aws:dynamodb:us-east-1:<account>:table/*`
- D. `arn:aws:dynamodb:us-east-1:<account>:table/transactions`

<details><summary>Show answer</summary>

**D.** The role should be scoped to the exact table it writes to, in
the exact region. (C) is too broad (it includes other tables in the
account), (B) is wider still, (A) is the worst.
</details>

---

**Q6.** Why is the `boto3` resource/table object built at *module
import* time, not inside the handler?

- A. So that the Lambda container fails fast at cold start if the IAM
  role is misconfigured.
- B. Because `boto3.resource` objects are not thread-safe.
- C. So that the same connection pool is reused across invocations
  within the same warm container.
- D. Both A and C.

<details><summary>Show answer</summary>

**D.** Import-time construction reuses sockets and TLS sessions across
warm invocations (the standard idiom) *and* surfaces IAM/credential
errors at cold start instead of the first user-facing call. (B) is
false — boto3 resources are thread-safe.
</details>

---

**Q7.** A record arrives with no `transaction_id`. The handler should:

- A. Raise an exception so the whole batch fails and S3 retries.
- B. Log `record.skipped`, increment `skipped`, and continue.
- C. Write a placeholder `transaction_id` of `UNKNOWN`.
- D. Delete the file from S3.

<details><summary>Show answer</summary>

**B.** One bad row must not poison the rest of the batch. The summary
reports `skipped` and the handler returns success; the bad row is
visible in CloudWatch for a human to triage.
</details>

---

**Q8.** The handler emits `logger.log(level, json.dumps(payload, ...))`
instead of `logger.info("wrote %s", tx_id)`. Why?

- A. Because `logger.info` does not exist in Lambda.
- B. Because structured JSON is queryable in CloudWatch Logs Insights;
  free-form strings are not.
- C. Because `json.dumps` is faster than `%` formatting.
- D. Because CloudWatch strips non-JSON log lines.

<details><summary>Show answer</summary>

**B.** Logs Insights parses JSON fields automatically and you can
`filter event = "record.persisted"` directly. (D) is false — CloudWatch
stores any text.
</details>

---

**Q9.** You re-invoke the handler with the same S3 event and see five
`record.duplicate` log lines and a summary of
`{processed: 0, skipped: 0, errors: 0}`. What is going on?

- A. The pipeline is broken; raise an alarm.
- B. The five rows are already in DynamoDB; the `attribute_not_exists`
  condition correctly suppressed the duplicate writes. This is
  idempotency working as designed.
- C. The IAM role is missing `dynamodb:PutItem`.
- D. The function is throttled.

<details><summary>Show answer</summary>

**B.** This is exactly what we want. `errors` is 0, no rows were
duplicated, the pipeline is healthy.
</details>

---

**Q10.** Which statement about the architecture is **false**?

- A. S3 event notifications are at-least-once.
- B. The handler builds `boto3.resource("dynamodb")` once at import
  time.
- C. The IAM policy must include `dynamodb:Scan` for the function to
  write rows.
- D. The function reads the JSON file with `GetObject` from the same
  bucket the event came from.

<details><summary>Show answer</summary>

**C.** The writer never scans; only downstream consumers (with their
own role) do. (A), (B), and (D) are all properties of the design.
</details>
