# 06 — The DE Project Deep-Dive: How to Walk an Interviewer Through a Past System

> **Lesson 6 of 5 — Practice** · ~20 min

The single most important round for senior+ data engineering
candidates. It is not a 2-minute STAR story. It is not a
system-design whiteboard. It is a **30-60 minute structured
technical narrative** that proves you can build, debug, and
own a real data system end-to-end.

This lesson teaches the structure, gives you a worked example,
and shows you the failure modes that get strong engineers
filtered out at the offer stage.

---

## 1. Why this round exists (and why it filters so many people)

Most senior+ DE interview loops have a round called something
like **"Project Deep-Dive,"** **"System Walk-Through,"** or
**"Past Project."** It looks like a conversation. It feels
informal. The interviewer opens with a soft prompt — "Tell me
about a data system you designed or owned end-to-end" — and
then spends the next 30-60 minutes asking follow-up questions.

It is the **highest-signal round** in the loop because it tests
things no other round can:

- Can you describe a system in **5 layers** (context,
  requirements, design, implementation, outcome)?
- Can you handle follow-up **"why"** questions without getting
  defensive?
- Can you self-critique ("what would you do differently?")?
- Can you talk about numbers (volume, latency, cost, headcount,
  on-call load)?
- Do you actually understand the system you claim to have built,
  or are you reciting what your team did?

> **In the interview, you would say:** "I'd love to walk you
> through a project where I had end-to-end ownership. I'll
> frame it as five acts — context, requirements, design,
> implementation, and outcome — and I'll flag the tradeoffs
> and the things I'd do differently. Total time about 30
> minutes. Sound good?"

That single sentence does three things: it **structures** the
interviewer's expectations, it **signals** that you understand
the format, and it **invites** them to interrupt with
follow-ups (which is the entire point of the round).

The opposite — "uh, yeah, I worked on a streaming pipeline
at my last job" — loses the room in 30 seconds.

---

## 2. The 5-act structure

Every deep-dive should have the same skeleton. Time allocations
assume a 30-minute round; scale them up for 45 or 60.

| Act | Duration | What you cover |
|---|---|---|
| **1. Context** | 1-2 min | Team, stack, business problem, your role |
| **2. Requirements & Constraints** | 3-5 min | Volume, velocity, latency, cost, compliance, downstream consumers |
| **3. Design Decisions** | 10-15 min | The 3-5 architecture decisions, with the rejected alternatives |
| **4. Implementation & Tradeoffs** | 10-15 min | What you actually shipped, what broke, what you compromised on |
| **5. Outcome & Lessons** | 3-5 min | Numbers (latency, cost, uptime), what you'd do differently |

**Act 1 — Context.** Three sentences. Who you are, what team,
what the system did. Don't waste time on company history.

**Act 2 — Requirements & Constraints.** This is where most
candidates skip ahead to architecture. Don't. Name the
**numbers** that shaped the design. *"We needed sub-minute
freshness for a real-time fraud model. We had 200M events/day
across 4 sources. Compliance required 7-year retention with
right-to-delete within 30 days. The team was 5 engineers, no
on-call rotation."* If you can't name 3-4 concrete constraints,
you didn't really own the system.

**Act 3 — Design Decisions.** The meat. Pick **3-5 decisions**,
not 10. For each: the choice, the alternative(s) you
considered, and the *reason* you chose. "We picked Kafka
because we needed ordered partition-level delivery and
exactly-once semantics for downstream aggregations. We
considered Kinesis — easier ops, but no cross-shard ordering
and 5x cost at our volume. We considered Pulsar — interesting
multi-tenancy story, but our team had no operational
experience."

**Act 4 — Implementation & Tradeoffs.** What actually shipped.
The compromises. The 2-3 things that went wrong. The on-call
incident at 2am. Be specific. *"We underestimated partition
rebalance pain, so we shipped with a hot-partition on
`user_id` that caused 4x skew. We re-partitioned 3 weeks in."*

**Act 5 — Outcome & Lessons.** Numbers. Then self-critique.
*"Freshness went from 6 hours to 40 seconds p95. Cost
increased $30k/month but downstream models improved AUC by
0.07, which the team estimated was worth ~$2M/year in
fraud-catch. The thing I'd do differently: I'd add
backpressure handling and a dead-letter queue in the first
sprint, not the fourth."*

> **The single biggest differentiator:** Act 5. Candidates
> who can name a real mistake and what they'd change get
> hired. Candidates who end on "and the project was a
> success" get passed on.

---

## 3. Worked example: migrating a batch ETL pipeline to streaming CDC

A full, walk-through-able deep-dive. ~1500 words of what you
would actually say out loud. Use this as a template.

### Act 1 — Context (90 sec)

> "In 2024 I led the migration of our order-fulfillment
> pipeline from nightly batch ETL to streaming change-data-capture.
> I was the tech lead — 2 other engineers on the project, plus
> a data modeling partner. The business context: the batch
> pipeline powered the supply-chain dashboard that 200 store
> managers used to make next-day replenishment decisions. The
> 24-hour lag meant stores were stocking against yesterday's
> reality, which cost us roughly $4M/year in stockouts and
> overstock per the ops finance team."

### Act 2 — Requirements & Constraints (4 min)

> "The hard requirements, in order of how much they shaped
> the design:
>
> First, sub-minute freshness for new orders and order-status
> changes. Anything slower was a non-starter for the use case.
>
> Second, exactly-once delivery into the warehouse, because
> downstream aggregations would double-count without it. The
> batch pipeline had exactly-once by construction — it ran
> once a night. Streaming made that a real engineering problem.
>
> Third, schema evolution. The order-events schema was owned
> by 3 different product teams, and they shipped breaking
> changes roughly every 6 weeks. We couldn't lock the schema
> down.
>
> Fourth, cost. The batch pipeline cost $8k/month in
> warehouse compute. The CFO was willing to go up to $20k
> if we delivered the freshness, but anything beyond that
> needed a re-approval — which would not have happened.
>
> Fifth, compliance. Order data is PII. We needed
> column-level encryption at rest, field-level masking in
> the serving layer, and a 7-year retention with a
> right-to-delete pipeline."

### Act 3 — Design Decisions (12 min)

> "Three design decisions drove the system.
>
> **Decision 1: CDC source from Postgres, not application-level
> events.** We considered asking the product teams to publish
> order events from their services. That would have given us
> cleaner data and lower latency. But it required a
> cross-team migration with 4 product teams and no committed
> engineering time. We chose to read the Postgres WAL via
> Debezium. Trade-off: we got all the writes including
> backfills and admin updates, which we then had to filter.
> We solved that with a filter topic in Kafka that dropped
> non-business writes using a regex on the table name and
> column.
>
> **Decision 2: Kafka over Kinesis and Pulsar.** We needed
> ordered delivery per partition key (order_id), and we
> needed exactly-once into Snowflake via the Kafka connector.
> Kinesis didn't support cross-shard ordering, and the
> Snowflake connector had weaker exactly-once guarantees at
> the time. Pulsar was technically interesting — its
> tiered-storage model would have been 30% cheaper — but
> nobody on the team had run it in production, and we had
> a 4-month deadline. We picked Kafka. We sized for 12
> brokers with 3x replication, 200MB/s peak throughput.
>
> **Decision 3: Schema Registry with backward-compatible
> evolution.** This was the single highest-friction
> decision. The product teams wanted to drop columns, rename
> fields, and change types freely. We forced all changes
> through Schema Registry with a CI check that rejected
> breaking changes. We allowed backward-compatible changes
> (add a column with default, deprecate a field) and gave
> teams a 90-day deprecation window. The first 3 weeks
> were painful — 4 PRs rejected in a row, one shouting
> match with a senior PM — but after the second month,
> teams started proposing compatible changes proactively.
> This was the call I am most proud of in the project."

### Act 4 — Implementation & Tradeoffs (12 min)

> "Implementation took 4 months, with 2 incidents worth
> naming.
>
> **What worked:** the dual-write period. We ran the batch
> and streaming pipelines in parallel for 6 weeks, comparing
> outputs row-by-row on a 1% sample daily. That caught 3
> semantic bugs in the CDC pipeline before we cut over —
> specifically, a timestamp-timezone mismatch that would
> have shifted every order by 8 hours in the APAC
> dashboard.
>
> **What broke:**
>
> First, the hot-partition problem. We partitioned by
> `store_id`, expecting 200 stores to be roughly uniform.
> One mega-store in the Bay Area generated 12% of all
> orders, so a single partition ran hot and capped our
> throughput at 4k events/second. We re-partitioned by
> hash of `order_id` and added the `store_id` as a
> secondary key in the event payload. Took 3 weeks,
> required a coordinated cutover.
>
> Second, the backfill. When we first turned on CDC, we
> had to backfill ~6 months of historical orders to seed
> the new warehouse tables. We underestimated the
> backfill time by 4x — it took 2 weeks at 30% of
> cluster capacity, blocking other workloads. The lesson:
> backfills are a project unto themselves, not a
> sub-task.
>
> Third, late-arriving data. CDC events can arrive out of
> order if the WAL is being replayed or a network blip
> happens. We initially dropped anything more than 5
> minutes late, which dropped 0.3% of orders. We changed
> the policy: late events go to a reconciliation topic,
> and a separate job merges them into the warehouse with
> a 24-hour grace period. The downstream aggregations
> needed to be idempotent — that was a non-obvious
> requirement that took us 2 weeks of refactoring."

### Act 5 — Outcome & Lessons (3 min)

> "Numbers:
>
> - Freshness: 24 hours → 40 seconds p95, 3 seconds median.
> - Cost: $8k/month batch → $24k/month streaming at
>   steady state. The CFO approved the increase because
>   the supply-chain team's stockout rate dropped from
>   6.1% to 2.4% in the first quarter, which the ops
>   team estimated saved $3.2M/year.
> - On-call load: we absorbed the new pipeline into the
>   existing 6-person rotation. Average pages per week
>   went from 2 to 4, which was acceptable.
> - Schema: 11 backward-compatible changes shipped in
>   the first 6 months post-launch, 0 breaking changes.
>
> **What I'd do differently:**
>
> First, I'd build backpressure and dead-letter handling
> in week 1, not week 12. We learned that lesson through
> 2 minor incidents that we got lucky on.
>
> Second, I'd push harder on partitioning strategy up
> front. We had data on store-size distribution; I should
> have modeled the partition skew before the architecture
> review, not after the incident.
>
> Third, I'd write a runbook for the backfill in week 1.
> We spent more time on the backfill than on the
> real-time path, and we had not budgeted for it.
>
> The pattern I took from this project — the dual-write
> validation period and the schema-evolution CI gate —
> is now the default for every new pipeline on the team.
> We shipped 4 more CDC pipelines in the next 6 months
> using the same template, and none of them had a
> meaningful production incident."

---

## 4. Common failure modes

Things that filter senior candidates at this round.

**Rambling past 35 minutes.** The interviewer has 3-4
follow-up questions queued. If you burn the whole 30 minutes
on Acts 1-3, they never get to Acts 4-5. Practice with a
timer. If you're over 25 minutes at Act 3, **skip ahead to
outcome** and offer to come back.

**Skipping the numbers.** "It was faster" loses to
"freshness went from 24 hours to 40 seconds p95." Every
quantifiable claim needs a number. If you don't have the
number, say so honestly: "I don't have the exact figure,
but it was roughly 4x." Honesty is better than
fabrication.

**No self-critique.** "The project was a success" is a
yellow flag. Every system has flaws. If you can't name one,
the interviewer assumes you weren't paying attention. Pick
something specific — the backfill, the hot partition, the
late-arriving data — and own it.

**"What would you do differently?" — defensive answer.**
Interviewers ask this to test intellectual honesty. A
defensive answer ("nothing major, it went well") loses.
A specific answer ("I'd build backpressure in week 1,
not week 12") wins.

**Over-indexing on tools.** "We used Kafka, Debezium,
Snowflake, Schema Registry, dbt, Airflow, Great
Expectations, Datadog" is a *list*, not a *narrative*.
Tools are mentioned in service of decisions. Lead with
the decision, name the tool as the means.

**Skipping the rejected alternatives.** "We picked
Kafka" is weaker than "We picked Kafka over Kinesis and
Pulsar because..." The interview signal is in the
*rejection*, not the *selection*. Show you considered
options.

**Forgetting who the audience is.** A Staff+ interviewer
wants to hear about cross-team influence and judgment
under ambiguity. A Senior interviewer wants to hear
about technical depth and execution. Calibrate the
emphasis.

---

## 5. Signals the interviewer is sending you

The deep-dive is a two-way signal. Watch for these:

- **"Can you elaborate on X?"** — they're interested in
  that thread. Spend more time there.
- **"What were the alternatives you considered?"** —
  they want to see the rejected paths. Name 2.
- **"What would you do differently?"** — they want
  self-critique. Don't punt.
- **"How did you measure success?"** — they want
  outcome numbers. Have them.
- **"What was the team dynamic?"** — they want
  leadership and influence. Don't make this a solo
  hero story.
- **"Walk me through the code"** — they want depth.
  Be ready to drop into a specific function or query.
- **Long silence after you finish a section** — they
  are about to ask the follow-up they've been holding.
  Don't fill the silence. Wait.

---

## 6. The 3 prep questions for any deep-dive

Before you walk into the room, you should be able to
answer these 3 about your chosen project in under 30
seconds each:

1. **"What was the single hardest decision you made on
   this project, and why?"** If you can't answer this
   crisply, you don't really own the narrative.
2. **"What would you do differently if you started
   today?"** If your answer is "nothing," you haven't
   reflected.
3. **"What was the most interesting failure, and what
   did you learn?"** "We had no failures" is not a
   credible answer for any real system.

If you can answer those 3, you can survive the round.

---

## Try it

Pick one project from your past — ideally one where you
had end-to-end ownership and can name at least 3 design
decisions and 1 thing that went wrong.

**Step 1 — Outline (15 min).** Write the 5 acts in bullet
form. For each, list 3-5 specific facts (numbers, names,
dates). Don't write the prose.

**Step 2 — First pass (30 min).** Time yourself. Tell the
story out loud, with the outline in front of you. Record
it. Don't stop, don't self-edit.

**Step 3 — Listen back (10 min).** Write down 3 things:
(a) where you rambled, (b) where you skipped a number, (c)
where you got a question you weren't ready for.

**Step 4 — Tighten (20 min).** Rewrite the weakest 2
sections. Cut 20% of the words. Practice once more.

**Step 5 — Mock (45 min).** Have a friend play the
interviewer. Tell them to interrupt with "why?" every
3-4 minutes. Practice holding the thread when interrupted.

Total time: ~2 hours. Do this for **2 different projects**,
and you have 2 deep-dives ready for the loop. Most senior+
loops ask 1-2 deep-dives per candidate.

---

*Author: Prem Vishnoi <pvishnoi@avilx.com>*
