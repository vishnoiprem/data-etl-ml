# Section 6 Quiz — Logs Insights + Subscriptions

> 9 questions, multi-choice, single answer.

---

**Q1.** Which are valid subscription-filter destinations?

- A. Kinesis Data Streams
- B. Kinesis Data Firehose
- C. Lambda
- D. All of the above

<details><summary>Show answer</summary>

**D — All of the above.** Three destination types: KDS, Firehose, Lambda. Use KDS for low-latency / replayable, Firehose for S3 / OpenSearch, Lambda for routing / transformation.

</details>

---

**Q2.** How many subscription filters can a log group have?

- A. 1
- B. 2
- C. 5
- D. Unlimited

<details><summary>Show answer</summary>

**B — 2.** A hard limit. To fan out to more, use a Lambda as the first destination and have it route onward.

</details>

---

**Q3.** What's the equality operator in a JSON filter pattern?

- A. `==`
- B. `=`
- C. `eq`
- D. `equals`

<details><summary>Show answer</summary>

**B — `=`.** Not `==` — this trips up half the developers who use it for the first time.

</details>

---

**Q4.** Which destination is **replayable** (you can re-read past events)?

- A. Kinesis Data Streams
- B. Kinesis Data Firehose
- C. Lambda
- D. SNS

<details><summary>Show answer</summary>

**A — Kinesis Data Streams.** Records are durably stored (replicated across 3 AZs) for 1–365 days. Firehose writes to S3, so technically replayable from there, but the Firehose service itself doesn't have a "replay" feature.

</details>

---

**Q5.** What's the default Firehose buffering?

- A. 1 MB / 60 s
- B. 5 MB / 300 s
- C. 10 MB / 600 s
- D. 100 MB / 3600 s

<details><summary>Show answer</summary>

**B — 5 MB / 300 s.** For debug workloads, tighten the interval to 1 MB / 60 s so events appear in S3 quickly.

</details>

---

**Q6.** What does `?ERROR ?WARN` match?

- A. Events with `ERROR` OR `WARN`
- B. Events with both `ERROR` AND `WARN`
- C. JSON events with `level = "ERROR" || "WARN"`
- D. Regex matching `ERROR|WARN`

<details><summary>Show answer</summary>

**B — Both.** Each token after a `?` adds an AND constraint. Use `-DEBUG` to exclude.

</details>

---

**Q7.** What's the event shape from CloudWatch Logs to a Lambda destination?

- A. `{"awslogs": {"data": "<base64 gzipped json>"}}`
- B. `{"logEvents": [...]}`
- C. `{"Records": [...]}`
- D. `{"log": "..."}`

<details><summary>Show answer</summary>

**A.** The Lambda receives a single `awslogs.data` field; the contents are gzipped + base64-encoded JSON. Decode with `gzip.decompress(base64.b64decode(data))`.

</details>

---

**Q8.** Does a Lambda subscription destination need a service role?

- A. Yes, like Kinesis / Firehose
- B. No — the function's resource policy is enough
- C. Only if the Lambda is in a different account
- D. Only for cross-region

<details><summary>Show answer</summary>

**B — No.** CloudWatch Logs adds the necessary permission to the Lambda's resource policy automatically when you call `put_subscription_filter` with the function ARN. Kinesis and Firehose *do* need a service role.

</details>

---

**Q9.** What does a Lambda destination do after a 6-hour retry exhaustion on errors?

- A. Events are silently dropped
- B. Events are routed to a configured DLQ
- C. Events are re-delivered forever
- D. The Lambda is disabled

<details><summary>Show answer</summary>

**A — Silently dropped, by default.** To keep them, configure a **Dead Letter Queue (DLQ)** on the Lambda (SQS or SNS). Section 6 covers this in L28.

</details>
