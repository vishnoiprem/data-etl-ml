# Section 3 Quiz — Logs

> 10 questions, multi-choice, single answer.

---

**Q1.** What's the unit of log retention in CloudWatch Logs?

- A. Log stream
- B. Log group
- C. Log event
- D. Log subscription

<details><summary>Show answer</summary>

**B — Log group.** Retention is set once per group, applied to all streams in it. The same is true for IAM permissions and subscription filters.

</details>

---

**Q2.** What's the max size of a single log event?

- A. 64 KB
- B. 256 KB
- C. 1 MB
- D. 10 MB

<details><summary>Show answer</summary>

**B — 256 KB.** Events larger than this are rejected. For larger payloads, use S3 with a reference URL in the log.

</details>

---

**Q3.** How many log events can a single `put_log_events` call write?

- A. 100
- B. 1,000
- C. 10,000
- D. 1,000,000

<details><summary>Show answer</summary>

**C — 10,000 events / 1 MB max per call.** Batch accordingly. After the first call you must include `sequenceToken`; on race you'll get `InvalidSequenceTokenException` and re-read via `describe_log_streams`.

</details>

---

**Q4.** What's the difference between `get_log_events` and `filter_log_events`?

- A. They're aliases
- B. `get_log_events` tails a stream; `filter_log_events` searches with pattern + time
- C. `filter_log_events` is for Kinesis only
- D. `get_log_events` is for Insights only

<details><summary>Show answer</summary>

**B.** `get_log_events` reads events sequentially from a single stream; `filter_log_events` searches across streams with a pattern and a time window, paginated. For regex / stats use Logs Insights.

</details>

---

**Q5.** Which Costs more: Logs Ingestion or Logs Storage?

- A. Ingestion ($0.50/GB) — usually the bigger line item
- B. Storage ($0.03/GB-month) — usually the bigger line item
- C. They're the same price
- D. Neither is charged

<details><summary>Show answer</summary>

**A — Ingestion ($0.50/GB).** Storage is much cheaper per GB-month, but accumulates. The most common cost surprise is forgetting to set retention on chatty log groups — the storage bill grows unboundedly.

</details>

---

**Q6.** What does `SOURCE '/aws/lambda/my-fn'` do in a Logs Insights query?

- A. Reads a file from S3
- B. Selects the log group `/aws/lambda/my-fn` as the source
- C. Creates a new log group
- D. Subscribes to a stream

<details><summary>Show answer</summary>

**B — Selects the log group as the source.** `SOURCE` is the only Logs Insights command that takes a log group name; everything else (`fields`, `filter`, `stats`, `sort`, `limit`) is separated by `|`.

</details>

---

**Q7.** What does `bin(5m)` do in a Logs Insights query?

- A. Time-bucket rows into 5-minute windows
- B. Truncate timestamps to the day
- C. Filter to the last 5 minutes
- D. Convert timestamps to ISO 8601

<details><summary>Show answer</summary>

**A — Time-bucket rows into 5-minute windows.** Used with `stats count() ... by bin(5m)` to compute a time-series of counts per 5-min bucket. Other values: `bin(1h)`, `bin(1d)`.

</details>

---

**Q8.** What's the difference between Insights and `filter_log_events`?

- A. They're the same
- B. Insights is server-side SQL-like; `filter_log_events` is per-call client-filtered
- C. Insights is for metrics; `filter_log_events` is for logs
- D. `filter_log_events` doesn't exist

<details><summary>Show answer</summary>

**B.** Insights runs the query server-side and returns tabular results; `filter_log_events` returns events and the filter pattern is a small DSL. Use Insights for stats / percentiles / time-bucketed counts.

</details>

---

**Q9.** How long can a single Logs Insights query run?

- A. 1 minute
- B. 15 minutes
- C. 60 minutes
- D. 24 hours

<details><summary>Show answer</summary>

**C — 60 minutes.** And it can scan up to 30 days of data. For long-running historical scans, export to S3 with a subscription filter (section 6).

</details>

---

**Q10.** What is `@initDuration` in a Lambda `REPORT` line?

- A. The function's total runtime
- B. The cold-start initialization time
- C. The memory init phase cost
- D. The DLQ retry count

<details><summary>Show answer</summary>

**B — The cold-start initialization time.** Present only on cold-start invocations. Use a metric filter `ispresent(@initDuration)` to count cold starts (L13).

</details>
