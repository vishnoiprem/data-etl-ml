# 02 — How to Answer ETL Design Questions

> **Lesson 2 of 5 — Overview**

The 4-step framework is what you do. The *how* — how you time-box,
how you ask clarifying questions, how you sequence the answer — is
what separates a memorable interview from a forgettable one. This
lesson is the playbook for the 30 minutes you're in the room.

---

## 1. The 30-minute time budget

Most pipeline design interviews are 30 minutes. Sometimes 45. Almost
never 60. The budget is tight. Here's the allocation:

| Phase | Time | What you do |
|---|---|---|
| Clarify | 5 min | Ask 4-6 questions. Sketch back what you heard. |
| Estimate | 5 min | Pick a back-of-envelope number for rows/day, GB/day, peak QPS. |
| Draw | 10 min | High-level architecture: 3-5 boxes, labeled arrows. |
| Deep dive | 10-15 min | Pick the hot path. Walk through the API, the schema, the failure modes. |

If you hit 25 minutes and you haven't done a deep dive, you have
failed. Period. The deep dive is the only signal an interviewer can
use to separate L4 from L5.

---

## 2. The clarifying questions

The 6 questions worth asking, in this order:

1. **Volume** — "How much data per day? Rows? GB? Events?"
2. **Velocity** — "Is this batch or streaming? Or both?"
3. **Format** — "Is the source relational, files, events, API?"
4. **Latency** — "What's the downstream SLA? Hourly? Daily? Real-time?"
5. **Consumers** — "Who reads the output? BI tool? ML model? Product feature?"
6. **Constraints** — "Anything I should know about cost, existing tech, or compliance?"

Don't ask all 6 every time. Ask the 3-4 that change your design. If
the interviewer says "100 events per day" you don't need to ask
about backpressure.

**Pro tip:** repeat back what you heard. "So, 100M events per day,
JSON, hourly SLA, downstream is a recommender. Let me make sure I
have the latency right — 'hourly' means a 1-hour pipeline is OK, but
you'd want sub-minute for new-user recommendations?" This buys you
clarity *and* shows the interviewer you're listening.

---

## 3. The order to draw boxes

Always draw in this order:

1. **The source.** What's at the left edge of the diagram? OLTP
   database? API? File drop? Event stream? Draw it as a cylinder
   for a database, a tube for a stream, a folder for files.
2. **The ingestion layer.** This is the "how does data get from
   source into our system" box. Kafka? S3? Airflow? Debezium?
3. **The transformation layer.** Where the business logic lives.
   Spark? dbt? Python pandas? This is often the biggest box.
4. **The storage layer.** Where does the data live at rest?
   Warehouse? Lakehouse? Wide-column store?
5. **The serving layer.** Who reads it and how? BI? ML? API?

**Always name the source first.** A common mistake: starting with
the warehouse. That's wrong. The source is what the data *is*; the
warehouse is just where it ends up.

---

## 4. The arrow labels

Every arrow needs a label. Not "Kafka" — a label that describes the
*protocol* and the *SLA*:

| Bad label | Good label |
|---|---|
| "Kafka" | "CDC events, at-least-once, 5s lag target" |
| "Spark" | "Batch dedup + SCD2, hourly, idempotent" |
| "Snowflake" | "MERGE INTO on (user_id), every 15 min" |

The labels are what make your diagram a *design* rather than a *tool
list*. A senior design says what each arrow *does* and what *guarantee*
it provides.

---

## 5. The deep dive

After the diagram, the interviewer will say "let's go deeper on X".
Where X is usually one of:

- **The extraction layer** (CDC, schema evolution, backpressure)
- **The transformation** (dedup, joins, data quality, SCD2)
- **The loading** (idempotency, upsert, partitioning)
- **The reliability** (retry, DLQ, monitoring)

Pick the one you know best. If the interviewer suggests one, take
their suggestion. The deep dive is where you talk for 5-10 minutes
uninterrupted. That's the gold.

**The 3 things every deep dive must include:**

1. A **concrete API or SQL** example. "Here's the SQL transformation
   we'd run." A 5-line snippet.
2. A **failure mode**. "If X breaks, here's what happens." One example.
3. A **mitigation**. "We handle that with Y." A specific tool or pattern.

If you give all three, you have a senior answer. If you give one or
two, you have a mid answer. If you give zero, you have a junior answer.

---

## 6. What to do when you don't know

The most realistic scenario: the interviewer asks you about a tool
you've never used. Real examples from real interviews: Flink exactly-once,
Iceberg vs Delta internals, BigQuery streaming inserts.

The senior move: **admit it, then reason from first principles.**

> "I haven't used Flink's exactly-once mode in production. But the
> underlying problem is dedup on a stream where the same event can be
> re-delivered after a worker crash. The standard pattern is an
> idempotency key per event, stored in a KV lookup. The trade-off is
> the extra lookup per event. If Flink can fold that into the state
> store, that's the win."

That answer shows you can reason about systems. The tool is a
detail. The principle is what matters.

---

## Try it

Pick any one of the 8 canonical questions. Set a 30-minute timer.
Do all 4 steps. Record yourself (audio only is fine) and listen back.
You'll be horrified at how much filler you use, and you'll learn
more from 30 minutes of self-recording than from 3 hours of reading.
