# 01 — Introduction to ETL Design Questions

> **Lesson 1 of 5 — Overview**

The data pipeline design interview is the most underprepared-for round
in the data engineering loop. SQL is rehearsed. Coding is rehearsed.
Behavioral is rehearsed. "Design Netflix's clickstream pipeline" lands
on the candidate like a piano.

This lesson is the antidote. You'll learn what the round actually
tests, the 4-step framework every interviewer expects, and the
one-sentence answer that anchors every good design.

---

## 1. What "data pipeline design" actually tests

Interviewers want to know four things, in order of importance:

1. **Can you clarify a vague problem?** Real pipelines start ambiguous.
   Good candidates ask questions before drawing boxes. What data? How
   much? What latency? What downstream consumers?
2. **Can you reason about scale?** How many rows per day? How many
   gigabytes? How does that change the design?
3. **Can you make and defend tradeoffs?** Batch vs streaming. CDC vs
   polling. Warehouse vs lakehouse. Every choice has a cost. Articulate it.
4. **Can you go deep on the critical area?** Don't go wide. Go deep
   on the hot path. The hot path is usually extraction (CDC, schema
   evolution) or reliability (idempotency, retry).

There are no right answers. There are well-reasoned answers.

---

## 2. The 4-step framework

```
┌──────────────────────────────────────────────────────┐
│ Step 1: Clarify requirements (5 min)                 │
│   - Volume, velocity, format, schema, latency         │
│   - Downstream consumers + their SLA                  │
│                                                      │
│ Step 2: Back-of-envelope estimation (5 min)          │
│   - Rows/day, GB/day, peak QPS                       │
│   - Pick numbers; back-of-envelope is enough          │
│                                                      │
│ Step 3: High-level design (10 min)                   │
│   - Boxes and arrows: source, ingest, transform,     │
│     load, serve, monitor                             │
│   - Identify the "hot path"                          │
│                                                      │
│ Step 4: Deep dive on hot path (10-15 min)            │
│   - API, schema, idempotency, retry, failure modes   │
│   - This is where senior candidates shine            │
└──────────────────────────────────────────────────────┘
```

A common failure: spending 25 min on the high-level diagram and 5 min
on the deep dive. **Invert it.** The deep dive is what separates
senior from junior.

---

## 3. The one-sentence answer

The most underrated move in a pipeline design interview is to open
with a one-sentence summary of the architecture *before* you start
drawing:

> "At a high level I'd build a CDC pipeline from Postgres into Kafka,
> then stream into a Delta Lake where dbt models produce the gold
> tables. The hot path is the CDC connector; the rest is mostly
> glue."

This single sentence does three things: (1) it tells the interviewer
you have a mental model, (2) it names the *hot path* so they know
where to push, and (3) it buys you 30 seconds of uninterrupted
drawing time while the interviewer digests the framing.

---

## 4. The 5 tradeoffs you'll mention unprompted

Every strong pipeline design names these tradeoffs early, even before
the interviewer asks:

| Tradeoff | The two ends |
|---|---|
| **Batch vs streaming** | Hourly Airflow jobs vs Kafka + Flink. Cost vs latency. |
| **ETL vs ELT** | Transform before load (ETL) vs load then transform (ELT). |
| **Lakehouse vs warehouse** | Raw Parquet on S3 + Delta vs Snowflake/BigQuery. |
| **Push vs pull** | Webhook push from source vs scheduled pull. |
| **At-least-once vs exactly-once** | Cheap-and-cheerful retries vs expensive dedup. |

Don't try to "win" each tradeoff. Just name them and say "given the
requirements I'd pick X for reason Y". That's the senior answer.

---

## 5. The mistake junior candidates make

They start drawing immediately. They draw 8 boxes. They label the
arrows with tool names ("Kafka", "Spark", "Snowflake") and call it
done. The interviewer asks "what happens if Kafka is down?" and the
candidate freezes, because the design has no failure modes.

**The senior answer is different.** It has 3-5 boxes, not 8. Each box
has a one-sentence purpose. The arrows have *protocols* and *SLAs*,
not tool names. And the deep dive covers three failure modes in
detail: source unreachable, transform fails, sink rejects.

If you can draw a pipeline that *fails well*, you'll pass the round.

---

## 6. The canonical question set

The 8 questions in
`docs/reference/de_interview_canonical_questions.md` cover ~80% of
the pipeline design questions asked at FAANG, Stripe, Airbnb, and the
big banks:

1. Design a document processing pipeline
2. Data lakehouse vs data warehouse
3. Medallion Architecture (bronze/silver/gold)
4. Delta Lake — what it adds on top of Parquet
5. Hadoop vs PySpark — when each is right
6. Scheduling dependencies between two nightly jobs
7. Task that fails 10% of runs — how to handle
8. Design Netflix's Clickstream Data Pipeline

Every module in this track builds toward being able to answer all 8
with confidence. The mock interviews in Module 07 work three of them
end-to-end (Netflix clickstream, document processing, banking CDC).

---

## Try it

Pick any one of the 8 canonical questions. Without writing anything
down, give a 60-second oral answer that includes:

- A one-sentence summary
- A back-of-envelope estimate
- The hot path
- One failure mode

If you can do that in 60 seconds, you have the framework. If you
can't, re-read sections 2 and 3.
