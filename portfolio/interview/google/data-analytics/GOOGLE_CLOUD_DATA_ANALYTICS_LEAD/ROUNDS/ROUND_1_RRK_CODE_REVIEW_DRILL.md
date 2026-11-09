# Q15 Code-Review Drill — Working Answer

**Round:** 1 of 2 — RRK | **Interviewer:** Navakanth Talluri | **Question:** Q15, "Reviewing code: [DATA PROCESSING SNIPPET]"
**Why this exists:** The recruiter's brief states one RRK round includes "reviewing a short piece of data-processing code." This is the single most *predictable* technical question in the round — the format is known, only the snippet is unknown. A rehearsed review order is worth more than more study.

**Source material:** `INTERVIEW_PREP/ROUND_2_TECHNICAL/code/dataflow_batch_pipeline.py` (316 lines, Dataflow batch: GCS → BigQuery with validation + dead letter). Plus `GCP_DATA_ENGINEERING_COURSE/project/core/pipeline_logic.py`.

> **Note on the file location.** `ROUND_1_RRK.md` §Q15 TODO says the file is "in the course project." It is not — it lives in `INTERVIEW_PREP/ROUND_2_TECHNICAL/code/`. `pipeline_logic.py` *is* in the course project. Corrected here so you do not hunt for it.

---

## 1. The Order You Say Out Loud

Do not start at line 1. Say the order first — it is the thing being graded.

> "I'm going to work through this in six passes: **correctness**, then **idempotency and restart**, then **scale**, then **data semantics**, then **security of the write path**, then **maintainability**. I'll tell you what I find at each pass, and I'll separate what breaks the pipeline from what breaks at scale, because those are different conversations."

| # | Pass | The question in your head | Signal |
|---|---|---|---|
| 1 | Correctness | What does this compute, and is that what it's supposed to compute? | Off-by-one, timezone, null handling, boundary conditions |
| 2 | Idempotency & restart | If I run this twice, same result? Can I restart after a partial failure? | **The one most candidates skip** |
| 3 | Scale | What happens at 100× the input? | Per-row work, memory growth, broadcast, N+1 |
| 4 | Data semantics | Late events, duplicates, ordering keys, schema evolution | Event-time vs processing-time |
| 5 | Security of write path | Is anything unvalidated reaching the sink? PII in logs? | Injection, PII, least privilege |
| 6 | Maintainability | Can the next engineer change this safely? | Named contracts, testable seams |

**Open with F3 if you want the strongest possible opening.** F3 (`datetime > date` raises `TypeError` on every record) shows the deepest reading:

> "There's a correctness bug that the pipeline is hiding from you. On line 116 you compare an `order_date` datetime against `.date()`. Those are different types — that raises `TypeError` every time. **And because the `except Exception` catches it, every valid record is being routed to the dead-letter path.** The pipeline looks green because it always produces output. So my first question isn't 'which line is wrong' — it's 'how many records are in that dead-letter path right now, and did anyone look?'"

**Why this order:** an interviewer hears "correctness first" and relaxes — you are not going to nitpick style. But if you jump to line 1 and start reading, you are reading, not reviewing, and you will spend the first five minutes on cosmetics.

---

## 2. The Findings — Verified Against the Actual File

Every finding below was checked by running the code. Nothing here is speculative.

### Pass 1 — Correctness

**F1 · Silent boolean coercion (line 85).** `str(value).lower() in ('true','1','yes','y','t')` — anything not in that list becomes `False`. `'maybe'`, `'TRUE '` (trailing space), `'on'`, `'Y'` all silently become `False`. A `"pending"` status field or a corrupted boolean becomes a confident wrong answer rather than a dead letter. **A coercion function that cannot fail is a coercion function that will lie.**

> Fix: an explicit tri-state — `True` / `False` / raise — so unknown values are rejected rather than defaulted.

**F2 · Integer truncation (line 81).** `int(float(value))` turns `'1.9'` into `1` and `'1e3'` into `1000` with no error. Silent numeric corruption on a money column. **On an order amount, this is a reconciliation incident waiting to happen.**

**F3 · `datetime` compared against `date` — this throws on *every* record (line 116).** `_business_rules` does:

```python
order_date = record.get('order_date')      # a datetime, from _coerce_type
if order_date and order_date > datetime.utcnow().date():   # .date() is a date
```

**`datetime > date` raises `TypeError` regardless of timezone awareness** — verified by execution. `datetime.datetime(2024,1,1) > datetime.date(2024,1,1)` → `TypeError: '>' not supported between instances of 'datetime.datetime' and 'datetime.date'`.

So this line does not "sometimes" misbehave: **it raises for every record that reaches it**, and the broad `except Exception` at line 53 swallows the `TypeError` and routes the record to the dead-letter path. **Every valid order is being dead-lettered.** The pipeline still "works" in the sense that it never crashes and always produces output — which is exactly why this defect can survive a long time unnoticed.

> **This is the single best finding in the file to present in an interview**, because it demonstrates three things at once: you read past the happy path, you understand the difference between a `datetime` and a `date`, and you know that a broad `except` converts a crash into silent data loss.

**F4 · `datetime.utcnow()` throughout.** Lines 48, 57, 116, 154, 155, 175. Deprecated from Python 3.12 (`DeprecationWarning: datetime.datetime.utcnow() is deprecated ... Use timezone-aware objects`), and it returns a **naive** UTC timestamp — so every `_processed_ts` and `_failed_ts` written to the table is a naive local-interpreted value with no timezone marker. Fix: `datetime.now(timezone.utc)`, and one declared source timezone for the whole pipeline.

### Pass 2 — Idempotency & Restart  ← *the differentiator*

**F5 · `WRITE_APPEND` with no dedupe key (line 268).** The pipeline appends to BigQuery. There is no `order_id` dedupe, no `MERGE`, no write disposition switch, no partition filter. **Re-run the job for the same date and every row is duplicated.** With at-least-once source delivery — the default for GCS and most upstream extractors — duplicates are not an edge case, they are the normal case.

> This is the answer to lead with. It is the defect that separates a leader who has run data platforms in production from one who has only designed them, and the recruiter's brief names **"idempotency and deduplication"** explicitly.

**F6 · 90-day partition expiry on an order table (line 217).** `expiration_ms: 7776000000` = 90 days. On a fulfilment/order fact table this **deletes order history older than 90 days**. Expiration is not a retention policy; on a table carrying financial and fulfilment history it is data destruction that looks like a config line.

**F7 · The dead-letter path is not persisted (lines 145–164).** `WriteDeadLetterToGCS.process()` does a `logging.info` and yields a `'logged'` tag — and **that `'logged'` output is never consumed**. So records that fail validation are printed to Cloud Logging and then go nowhere. **A dead-letter tag that never lands anywhere is not a dead-letter path; it is a silent data-loss path wearing a dead-letter costume.** A reviewer who spots this has found the most consequential bug in the file.

### Pass 3 — Scale

**F8 · Side input broadcast (line 253).** `beam.pvalue.AsDict(customer_lookup)` ships the **entire customer dimension to every worker**. Fine at 4,800 rows; at 10M customers it OOMs the workers. The code even admits it in the comment on lines 226–227 — a reviewer noting that the code already knows its own limit is credible. Fix: `CoGroupByKey` or a BigQuery join, as the comment says.

**F9 · The validation loop is O(fields) per record** — fine, but combined with `SCHEMA_AUTODETECT` on the write, the schema is inferred from data rather than declared. **Auto-detected schema drifts silently** when a source changes shape, and the drift lands as a load error at 3am rather than as a contract violation at the boundary. Fix: declare the schema explicitly, and treat a new field as a contract break.

### Pass 4 — Data Semantics

**F10 · Unlisted fields are silently dropped (lines 65–75).** `_validate_and_coerce` builds a new dict containing **only** the schema fields. `extra_field` and `_source_file` vanish from the valid path. The dead-letter path survives because it re-reads the original `element` (line 55). So: **valid records lose provenance and unmodelled fields; rejected records keep them.** Inconsistent, and it means a schema evolution that adds a field is invisible until someone notices the column is missing downstream.

**F11 · No event-time semantics.** Processing-time only (`_processed_ts`). No event-time watermark, no lateness policy, no allowed-lateness. **A late-arriving order is silently processed in the wrong window** — which, on a monthly close, means the number changes after the number was reported.

**F12 · Clustering on a field that is never produced (line 220).** `clustering: ['customer_id', 'region', 'status', 'channel']` — but the schema has no `region` column. Enrichment produces `customer_region`, not `region`. **BigQuery will reject the clustering spec, or silently ignore it**, and the table ends up with a clustering configuration that matches nothing.

### Pass 5 — Security of the Write Path

**F13 · PII in logs (line 161).** `logging.info(f"DEAD LETTER [{gcs_path}]: {json.dumps(element, default=str)}")` — dumps the **entire record** to Cloud Logging. Dead-letter records are precisely the ones most likely to contain malformed PII: a bad email, a bad user_id, a partial customer record. **A PII-shaped record is exactly what lands in the dead-letter path.** Log sink permissions are usually broader than dataset permissions.

> Also note `default=str` — it will serialise anything, including objects that were never meant to be logged.

**F14 · No data-classification enforcement.** Nothing checks whether `customer_id`, `amount` or `region` is regulated before it is written to a dataset that has no policy tags, no `VPC-SC` perimeter, and no column-level security. The clustering field `region` doubles as a residency signal, and there is no residency control on the output at all.

### Pass 6 — Maintainability

**F15 · The broad `except Exception` (line 53) flattens distinct failure modes.** A schema violation, a type error, a `KeyError` from a missing key, and a genuine infrastructure failure all become the same dead letter with a string message. Triage then depends on reading free text. **Losing the error taxonomy is losing the ability to prioritise the backlog.**

**F16 · The schema is hard-coded in the pipeline function (line 195)**, with a comment saying "in production: load from Schema Registry / Data Catalog." A data contract is a first-class artefact — it should be versioned, referenced, and testable, not a literal inside a function.

---

## 3. The Seniority Sentence

The brief says interviewers listen for the *design* issue, not the line. Use one of these:

> "The code is probably correct on the happy path. **The risk is that it's correct only if the upstream guarantees exactly-once delivery, and nothing in this code enforces that assumption** — so the write is not idempotent and a re-run duplicates every row. That's the one I'd change first."

> "The dead-letter path is the interesting part, and it's not doing what it looks like it's doing. It's tagged and logged but never persisted, so rejected records are dropped after Cloud Logging's retention window. **I'd fix that before I'd tune anything else**, because right now the pipeline's failure mode is silent loss."

---

## 4. The Question You Will Be Asked Immediately

**"What would you do to fix it?"**

The order matters more than the list:

1. **Fix the `datetime` vs `date` comparison (F3)** — one line, and until it is fixed the pipeline is dead-lettering valid records. Compare `order_date.date()` against a date, or compare against `datetime.now(timezone.utc)`. **Do this first because it is currently breaking every record.**
2. **Make the write idempotent** — `MERGE` on `order_id` with a deterministic upsert key, or a staging table plus a scheduled merge. This is the correctness fix.
3. **Persist the dead letters** — an actual `WriteToText` to GCS with a date-partitioned prefix, plus a replay path and a count that reconciles to source.
4. **Make coercion fail loudly** — tri-state boolean, no silent truncation, one timezone discipline (`datetime.now(timezone.utc)` throughout, and a declared source timezone).
5. **Preserve the schema and the provenance** — keep unmodelled fields (or reject them explicitly under a contract), carry `_source_file` on the valid path too.
6. **Fix the scale limit** — replace the broadcast side input with a join or `CoGroupByKey`.
7. **Declare the schema** — drop `SCHEMA_AUTODETECT`, pin the schema, make a new field a contract break.
8. **Then the governance layer** — policy tags, `VPC-SC`, masked columns, and a PII-scrubbed log payload.

Say the ordering out loud with a reason: *"The type bug first, because until that's fixed the pipeline is rejecting valid records and nothing else I do matters. Then idempotency, because everything after that is worth doing on top of a write path that is correct."*

---

## 5. Rehearsal Protocol — Do This Three Times

| Run | Material | Timebox | Goal |
|---|---|---|---|
| 1 | `dataflow_batch_pipeline.py` | 12 min | Learn the six-pass order |
| 2 | `dataflow_batch_pipeline.py` | 8 min | Get under time, find F5/F7 (idempotency + dead letter) |
| 3 | **An unfamiliar snippet** | 12 min | Stop relying on knowing the code |

**Run 3 is the one that matters.** Reading code you wrote yourself is a different skill from reading code you have never seen. Use one of:

- `GCP_DATA_ENGINEERING_COURSE/project/core/pipeline_logic.py` (909 lines — `deduplicate`, `watermark_lag`, `partition_for_event` are rich)
- `INTERVIEW_PREP/ROUND_2_TECHNICAL/code/composer_dag.py`
- `INTERVIEW_PREP/ROUND_2_TECHNICAL/code/bigquery_optimization.sql`
- `INTERVIEW_PREP/assets/code/custom_dataflow_transform.py`

**Get one genuinely unfamiliar snippet.** Where the interviewer gets it is unknown; the *format* is not. Build the habit, not the memorisation.

**Do not** answer "this looks good, just add type hints." A review with no findings is a failed review — you must find something, and it must be a semantic finding, not a style nit.

---

## 6. What "Good" Sounds Like — Scoring Rubric

| Level | Signal |
|---|---|
| **Strong pass** | Names the six-pass order; finds F5 (non-idempotent write) and F7 (dead letter not persisted) unprompted; frames findings by *blast radius*, not severity of style; states a fix order with a reason; distinguishes "breaks now" from "breaks at 10×" |
| **Pass** | Correctness + scale findings; offers fixes; but idempotency or restartability not raised |
| **Near-miss** | Style and line-level comments; no idempotency or semantics finding; no fix order |
| **Fail** | Says the code is fine; reads the file line by line aloud; cannot articulate what the code computes |

---

## 7. Bonus: The Related Questions This Opens

The interviewer often follows the code review with one of these. Have the answers ready.

**"How would you test this?"** → Layered: unit (coercion, boundary), contract (schema compatibility on both boundaries — added optional column, widened type, new enum value), data-quality gates (row counts against a source of truth, null rates, value ranges, freshness), and the three most valuable ones most teams skip: **reconciliation** (against an independently computed control total), **restartability** (kill mid-run, confirm identical output), **idempotency** (run twice, assert output unchanged).

**"How would you make the dead-letter path replayable?"** → Partition by date and reason; keep the original payload plus the error taxonomy; make replay a versioned, re-runnable step that goes through the *same* validation, not a bespoke script; reconcile replayed count against rejected count.

**"What would this look like on Pub/Sub and Dataflow Streaming instead of batch?"** → Ordering keys on `customer_id` where order matters, `exactly_once` on the Dataflow runner, event-time windows with allowed lateness, and a dead-letter Pub/Sub topic that *is* consumed by a triage consumer — not a log line.

---

*Findings verified by execution against `INTERVIEW_PREP/ROUND_2_TECHNICAL/code/dataflow_batch_pipeline.py`. Course project tests: 102 passed, 0 failed (was 2 failed / 25 skipped before the fixes recorded in `ROUND_1_RRK_GAP_CLOSURE.md`).*
