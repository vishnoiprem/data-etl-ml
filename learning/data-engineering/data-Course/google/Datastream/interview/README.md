# Interview Question Bank — Google Cloud Datastream & Change Data Capture

> **The question bank for this course.** Module files build the understanding;
> [top-50.md](top-50.md) is the final-night revision.

---

## What this bank is

This is a working interview bank for Google Cloud Datastream and change data
capture — not a flashcard list, and not a set of definitions. Every question
was selected because the answer **changes what you build**, and every answer
is written the way a senior engineer who has actually run this in production
would say it out loud.

Each answer follows the same six-part structure:

1. **The direct answer**, in the first one or two sentences. No throat-clearing.
2. **The mechanism** — the internal concept that explains it: the log, the
   before/after image, the merge clause, the merge key, the read consistency
   window, the partition, the offset, the constraint.
3. **When the alternative wins** — the trade-off and its boundary condition.
   "It depends" is never acceptable without saying what it depends on.
4. **A production failure story** — the actual symptom, and the fix.
5. **Code**, where it clarifies and nowhere else.
6. **Numbers** — row counts, gigabytes, latencies, dollars, percentages.

The failure story is the part interviewers probe. Anyone can recite that
`binlog_format` must be `ROW`; a senior interviewer wants to know whether
you have *seen* it fail, and what the destination table looked like when it
did.

### How the bank is structured

| File | Questions | What it covers |
|---|---:|---|
| [01-foundations-and-cdc.md](01-foundations-and-cdc.md) | 14 | What CDC is and why polling cannot detect deletes; the log → transport → sink model; log vs table; when *not* to use CDC; event amplification; the read consistency window; `ROW` vs `STATEMENT`; `binlog_row_image`; the replication user's privileges; the VPC path; idempotency; streaming vs synchronised merge |
| [02-the-merge-and-bigquery.md](02-the-merge-and-bigquery.md) | 14 | What Datastream does on the BigQuery side; merge key requirements; non-unique and mutable merge keys; idempotency; UPDATE/DELETE of an absent row; schema evolution; changed types; the event envelope; clustering; partitioning; monitoring metrics; the cost model |
| [03-operations-and-recovery.md](03-operations-and-recovery.md) | 14 | Backfill modes; why the destination must be empty; recovering a corrupted destination; truncated binary logs; schema-change handling; lagging vs broken; the `READY`-but-stale triage; the `RUNNING` state; latency vs lag; reconciliation; ordering; `__op__`; the DML quota |
| [04-kafka-and-streaming.md](04-kafka-and-streaming.md) | 14 | At-least-once and the duplicate write; Datastream vs Kafka semantics; consumer groups; partition key = merge key; the Confluent GCF sink connector; `min-instances`; Cloud Run vs Cloud Functions; the function's three stages; parameterised inserts; duplicate handling; poison messages and the DLQ; Confluent billing; Secret Manager; when to use Kafka |
| [top-50.md](top-50.md) | **50** | The highest-yield subset — read this the night before |

**Total: 106 questions.** The module files are arranged in the order the
course teaches the material; `top-50.md` is arranged by *interview theme*,
because that is how a conversation actually goes.

### How the bank maps to the chapters

| Module file | Primary chapters |
|---|---|
| `01-foundations-and-cdc.md` | [01-what-is-change-data-capture](../chapters/01-what-is-change-data-capture.md), [03-sources-and-the-binary-log](../chapters/03-sources-and-the-binary-log.md) |
| `02-the-merge-and-bigquery.md` | [02-the-merge-and-merge-keys](../chapters/02-the-merge-and-merge-keys.md), [04-schema-evolution-and-backfills](../chapters/04-schema-evolution-and-backfills.md) |
| `03-operations-and-recovery.md` | [04-schema-evolution-and-backfills](../chapters/04-schema-evolution-and-backfills.md), [06-operations-and-troubleshooting](../chapters/06-operations-and-troubleshooting.md) |
| `04-kafka-and-streaming.md` | [05-kafka-and-confluent](../chapters/05-kafka-and-confluent.md), [07-capstone-project](../chapters/07-capstone-project.md) |
| `top-50.md` | All of the above — selected for cross-layer coverage |

---

## The study plan

**A four-week plan for someone who knows SQL and has seen a database.** If
you have four weeks, do this. If you have two, compress weeks 1 and 2 and
skip week 3's reading in favour of the module questions.

### Week 1 — The model

Read [01-what-is-change-data-capture](../chapters/01-what-is-change-data-capture.md)
and [03-sources-and-the-binary-log](../chapters/03-sources-and-the-binary-log.md).
They are the foundation: what the log is, why the merge converges, and why
polling structurally cannot do what CDC does.

Then run the pipeline on your own machine:

```bash
python project/cdc_pipeline.py \
    --input sample_data/changes.ndjson \
    --output out/customers \
    --merge-keys customer_id
```

Break it on purpose: add a second merge key, feed it a duplicate, delete a
row out of the input, drop a required field. Watch the skip reasons in the
summary change. Then run `pytest project/tests -q` and read what each test is
actually asserting.

Then answer [01-foundations-and-cdc.md](01-foundations-and-cdc.md) **out
loud**. Not in your head — out loud, standing up. If you cannot say the
answer in two sentences, you do not have the first half of it.

### Week 2 — The merge

Read [02-the-merge-and-merge-keys](../chapters/02-the-merge-and-merge-keys.md)
and [04-schema-evolution-and-backfills](../chapters/04-schema-evolution-and-backfills.md).

The merge is the whole game. Read `project/cdc.py` — `CdcState.apply()` is
about forty lines and it is the semantic contract every other tool
reimplements. Then deliberately break the merge key and watch what the
reconciliation query reports.

Read [02-the-merge-and-bigquery.md](02-the-merge-and-bigquery.md) and answer
every question aloud.

### Week 3 — Operations, cost, and correctness

Read [06-operations-and-troubleshooting](../chapters/06-operations-and-troubleshooting.md).
You do not need a GCP account for the questions; you need to *understand*
them.

The practice that teaches the most: take `sql/reconciliation.sql`, point the
source snapshot at the *destination* table instead of the source, and run it.
It returns zero discrepancies. That is the point — reconciling against the
wrong side proves nothing.

Then read [03-operations-and-recovery.md](03-operations-and-recovery.md) and
answer it aloud. This is the week most people skip, and it is the week that
separates a candidate who knows CDC from a candidate who has shipped on it.

### Week 4 — Kafka, `top-50.md`, and a mock interview

Read [05-kafka-and-confluent](../chapters/05-kafka-and-confluent.md) and
[07-capstone-project](../chapters/07-capstone-project.md), then answer
[04-kafka-and-streaming.md](04-kafka-and-streaming.md) aloud.

Then read [top-50.md](top-50.md) **once, end to end**, in one sitting. Do not
write anything down yet. Notice which answers you could not produce.

Then go back and answer the ones you missed, out loud, writing down the
mechanism and the number if you can. Re-read only the answers you got wrong
or got vaguely right.

Finally, do a mock: pick 20 questions at random, set a timer for 90 seconds
per question, and answer each one **out loud** with the structure —
direct answer, mechanism, trade-off, failure story, number. The point of the
mock is not whether you know the answer; it is whether you can *get to* it
under pressure.

> **The honest advice:** `top-50.md` is for the final night. Reading it on
> day one is the single most common way people waste this bank. The module
> files are for building the understanding — they are slower, they repeat
> themselves, and they contain questions that will never be asked. That
> repetition is the point: it is what turns "I have read about the merge key"
> into "I know what happens when it is not unique."

---

## How to use the bank

**Do not memorise.** Memorised answers sound memorised, and a senior
interviewer can tell within two questions. What you are building is not
recall; it is the ability to *reason from a mechanism to a decision*.

**Write your own answer first.** Before you read the bank's answer, write
your own — three or four sentences, from memory. Then compare. You will find
one of three things:

- You knew it, and the bank adds a detail or a number. Good — you were
  nearly there, and the detail is worth keeping.
- You knew the shape but not the mechanism. This is the interesting case.
  Go back to the chapter and find the mechanism.
- You had the wrong model entirely. This is the most valuable outcome. Stop
  and re-read the chapter.

**Answer out loud.** Speaking is a different task from reading, and it is
the task the interview actually is. If you can only answer when you can see
the words, you have not prepared. The aim is: question → first two sentences
immediately, mechanism second, numbers third.

**Probe the failure story.** When you tell a failure story, ask yourself
"what was the symptom?" — a table with two rows for one customer, a bill
fifteen times the estimate, a 0.4% drift that read like a rounding error. An
interviewer who hears "it was wrong" will not follow up. An interviewer who
hears "the row count grew, so the count check passed, and it took a customer
appearing twice in a loyalty calculation to surface it" will ask three good
questions.

**Use the numbers.** The bank attaches numbers to most answers because
numbers are what distinguish an answer from a recital: ~2.0× amplification,
a 5-second read consistency window, `binlog_expire_logs_seconds`, 377
events over 200 rows, 8,000 events per second against BigQuery's DML quota.
You do not need to memorise them exactly — you need to *have* them, so that
"CDC is better here" becomes "CDC reads 100,000 events from a sequential
log instead of probing 10 million rows, and at ~2× amplification the poll
was already reading half the table".

**Revise by theme, not by file.** If you are weak in one area, read the
relevant `##` section of `top-50.md` and then go back to the corresponding
module file. Reading the bank front to back twice is less effective than
reading the weak section three times.

---

## What the interviewer is actually testing

Each theme in `top-50.md` probes a different mental model. Know which one
you are in, and you will know which details to lead with.

### "The model" — do you think in logs, or in tables?

They are testing whether you reason about an **immutable history being
projected into a mutable state**, or about a table that happens to be
updated. The table-thinker asks "which row do I update"; the log-thinker asks
"what is the source of truth, and how do I rebuild from it". The tell is
what you do when the destination is corrupted, and when a delete arrives
before its insert.

### "The merge" — do you know what the merge key has to satisfy?

They are testing whether you know that a merge key must be **unique, immutable
and minimal**, and what each property prevents. The trap is naming the
primary key and stopping. A candidate who says "the primary key, because it
must be unique and immutable" is answering; a candidate who says "the
primary key" and then cannot say what happens when it is not unique is not.

### "Configuration" — do you know the source's settings, or just the console?

They are testing **operational fluency with the source**: `ROW` vs
`STATEMENT`, `FULL` vs `MINIMAL`, `wal_level=logical`, the replication
privileges, the firewall to the allocated IP. These are the settings people
change once and then forget, and they are exactly the settings that fail
silently — a stream stays `READY` while nothing arrives.

### "Operations and recovery" — can you run and debug the thing?

They are testing whether you can tell a **lagging** pipeline from a **broken**
one, whether you know that reconciliation compares values and not counts, and
whether you can rebuild a destination from the log. The arithmetic test —
backlog growth = source write rate − processing rate — is the single
highest-signal answer in this section.

### "Kafka and streaming" — do you know what the transport does *not* guarantee?

They are testing honesty about **delivery semantics**. The trap is
"exactly-once". The strong answer distinguishes a converging, keyed
destination from an appending, stateless one, explains why Kafka needs a
`PRIMARY KEY` where Datastream needs nothing, and says that the partition
key and the merge key must be the same value. Senior interviewers push here
because this is where the production outages live.

### "Design and trade-offs" — can you defend a decision?

They are testing whether you can **make and justify a choice** under
competing constraints. "We used Datastream" is not an answer; "we used
Datastream because there was one destination and it was BigQuery, so paying
for Kafka's at-least-once semantics and re-implementing merge semantics was
pure cost" is. Watch for the follow-up: they will ask what you would do
differently at 10× the data.

---

## A note on versions

This bank was written against **Google Cloud Datastream as of late 2026**,
with the Confluent Cloud GCF sink connector and Cloud Run Functions
(2nd gen) as the Kafka-side targets.

The merge semantics, the log behaviour and the operational patterns in these
answers are stable, and the reasoning is what is being tested. The **API
details are not**: flag names, connector property names and default values
do change between releases.

So: **check every API detail against the tools you have installed.** From
the course root:

```bash
python -c "from google.cloud import secretmanager; print('secretmanager ok')"
python -c "from google.cloud import bigquery; print('bigquery ok')"
```

The course's own linter does this for you across every chapter and project
file:

```bash
python resources/audit_course.py
```

If a snippet in these answers does not match your installed SDK, the answer's
*reasoning* is still correct — but the code is not, and on an interview that
is the part that gets typed.

---

## Related material

- The course README — [../README.md](../README.md)
- One-page merge/config/flag reference — [CHEATSHEET.md](../resources/CHEATSHEET.md)
- The questions students actually ask — [FAQ.md](../resources/FAQ.md)
- The runnable pipelines — [project/](../project/)
