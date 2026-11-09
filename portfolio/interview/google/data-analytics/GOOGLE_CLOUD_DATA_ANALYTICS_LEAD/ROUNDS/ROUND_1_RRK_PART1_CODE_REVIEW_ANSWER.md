# RRK1 Part 1: Code Review Answer (Pub/Sub to BigQuery, PII, Singapore)

**Scenario:** Singapore customer, Pub/Sub to BigQuery, 100M events/day, PII, data must stay in Singapore. Task: top 3 risks in the code and how a Lead fixes them. 10 minutes. Reason about the code; do not rewrite it.

> **Read this first.** Sections 1 to 6 are a prepared answer script. It was written for a snippet that included a **backfill** (`SELECT *` back into the same table) and a **Cloud Function**. The mock-interview snippet in this session was different (a Cloud Run Pub/Sub subscriber with `message.ack()` first, logging of full events, an external enrichment call with a hardcoded key, and a dataset with no explicit location). **Always review the code actually on screen.** Section 7 maps the script to that snippet and lists what it misses. Section 8 is the merged answer to practise.

---

## 1. Opening (30 seconds)

"Before I fix code, let me state my assumptions. This is 100M events per day, PII, Singapore residency, MAS regulated. Pub/Sub delivers at least once, not exactly once. So my bar is: no duplicates, no PII leak, no partial publish, and we can roll back. If those assumptions are wrong, my recommendation changes."

Why it works: structure before solution.

## 2. Top 3 risks

### Risk 1: Correctness. Duplicates will happen, and a backfill will double the data
- `insert_rows_json` is not idempotent. Pub/Sub will redeliver; a retry inserts the same event twice.
- A backfill that does `SELECT *` and inserts the rows back into the same table doubles the data per run. No dedupe key, no `MERGE`, no check.
- **Fix:** use `event_id` as the dedupe key. Write to a staging table, then `MERGE` into prod on `event_id`. Make the backfill idempotent: same input, same output, however many times it runs.

### Risk 2: Security. PII and residency are not protected
- Raw email is written to prod. No masking or tokenisation. No check on IAM, VPC Service Controls or region. The dataset location is unknown.
- **Fix:** mask or tokenise email before write; BigQuery column masking with Dataplex policy tags; dataset in `asia-southeast1`; VPC Service Controls around Pub/Sub, compute and BigQuery; a least-privilege service account that can only write to this table.

### Risk 3: Reliability. No DLQ, no atomic publish, no observability
- If `json.loads` fails on one message, the whole batch can fail. No dead-letter path, no retry with backoff, no quarantine. A partial BigQuery failure leaves partial data, and acknowledgment is inconsistent.
- **Fix:** validate the schema first; quarantine bad records to a DLQ topic; retry with exponential backoff; write to staging, validate row counts and checksums, then publish atomically. Never publish partial. Dashboards for freshness, error rate, DLQ depth and cost per TB.

## 3. Scale and cost (1 minute)

- At 100M events/day, row-by-row `insert_rows_json` from a function or single service will not scale and is expensive. Function timeouts and concurrency limits apply.
- A backfill with `SELECT *` over 30 days and no partition filter is a full scan.
- **Fix:** move to Dataflow for streaming (watermarks, late data, exactly-once processing with an idempotent sink). For backfill, filter on `event_date`, process by day, checkpoint, and resume from the last successful day.

## 4. Maintainability (30 seconds)

No tests, no data contract, no versioning; one schema change breaks prod. **Fix:** schema registry, contract tests in CI, additive nullable columns only, unit tests for the dedupe logic, integration tests for the `MERGE`.

## 5. Recommendation (close with this)

"Do not patch this function. Replace it with a production pattern: Pub/Sub to Dataflow to BigQuery staging to `MERGE` to prod, with a DLQ, masking and reconciliation."

- **Week 1:** stop the bleed; add the DLQ and masking.
- **Week 2:** build staging, `MERGE` and the reconciliation job.
- **Week 3:** cut over with a 3-day dual run, compare counts, then decommission the old function.
- **Measures:** zero duplicate `event_id`, zero PII in prod, freshness p95 under 5 minutes, DLQ depth near zero, backfill restartable.

**Enterprise scope line (critical):** "As a Lead I would not fix this for one customer. I would turn it into a practice asset: a reusable ingestion template, a runbook and a checklist, so every consultant does it the same way."

## 6. Likely follow-ups

| Question | Answer |
|---|---|
| What if Pub/Sub redelivers? | Expected. Dedupe on `event_id` in `MERGE` is mandatory. |
| What if the schema changes? | Backward compatible only. New nullable fields; a contract test fails the build on a breaking change; old-format messages go to quarantine, not prod. |
| What if the backfill runs twice? | It must be safe to run twice. Staging plus `MERGE` makes it idempotent. |
| Why Dataflow over a function? | A function is fine at low volume. At 100M/day you need watermarks, state, backpressure and an idempotent sink. |

Tip: state the recommendation clearly, then stop. Do not keep adding bugs.

---

## 7. Corrections and gaps against the snippet used in the mock

The mock snippet (Cloud Run subscriber, `message.ack()` first):

| Real defect in the mock snippet | Covered by the script above? |
|---|---|
| `message.ack()` is the first line, before the write; the broad `except` swallows failures, so failed events are lost and never retried | **No.** Highest priority. The script says "acknowledgment is inconsistent" but never names ack-before-write. |
| `log.info("received %s", event)` and `log.error("bad message %s", message.data)` write full PII to logs (log buckets default to the `global` location unless configured) | **No.** |
| `enrich(event["email"], KEY)` sends raw email to an external API: residency and privacy breach | **No.** |
| `KEY = "..."` live credential in source | **No.** (Use Secret Manager.) |
| Dataset created without a location, which defaults to the US multi-region: breaks "stays in Singapore" | **Partly.** The script asks for `asia-southeast1` but doesn't flag that the default is a likely violation to verify first. |
| One `insert_rows_json` call per message; 100M/day is about 1,160 events/s average and about 3,500/s at a 3x peak | **Yes** (Scale section). Say the numbers. |
| No dedupe or `insertId`, no dead-letter topic, unversioned schema | **Yes.** |

**Script statements to tighten**
- "Dataflow handles exactly-once via an idempotent sink": say precisely that Dataflow is exactly-once for pipeline state, and end-to-end exactly-once depends on the sink being idempotent (Storage Write API offsets or `MERGE`).
- "Staging then `MERGE` for every event at 100M/day" can be costly. For streaming, prefer the Storage Write API with a deduplication key or a BigQuery subscription, and `MERGE` only partition-scoped batches. Mention the cost.
- "MAS regulated" is an assumption. Say it as one ("assuming a financial customer").
- Do not claim a defect exists in code you have not seen (the backfill, the Cloud Function) when the screen shows something else.

---

## 8. Merged answer to practise (about 5 minutes, own words)

1. **Assumptions (20 s):** 100M/day, PII, Singapore residency, Pub/Sub at-least-once, so the bar is no loss, no duplicates, no PII leak, and verified location.
2. **Risk 1, reliability and correctness:** ack-before-write plus a swallowing `except` loses events; no DLQ; no idempotency. Fix: ack after a confirmed write, nack on failure, a dead-letter topic with a max-attempts policy, an `event_id` dedupe key.
3. **Risk 2, PII and residency:** PII in logs and sent raw to an external API, a hardcoded key, and an unverified dataset location (default US). Fix: log IDs only, tokenise before any external call, Secret Manager, verify dataset, topic storage policy and log-bucket locations are Singapore, VPC Service Controls, least privilege.
4. **Risk 3, scale and cost:** one insert per message at about 1,160 events/s average, about 3,500/s at peak. Fix: Storage Write API or a BigQuery subscription or Dataflow, with flow control, batching and a monitored backlog.
5. **One line each:** schema versioning, tests, structured logs, config in environment.
6. **Close:** "I'd block this PR until acknowledgment follows a confirmed write, no PII reaches logs or an external service, the data and logs are verified in Singapore, and writes are idempotent and batched. Then I'd package the pattern as a reusable template and checklist for the practice."
