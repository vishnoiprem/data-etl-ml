# 02 — Discussing Tradeoffs

> **Lesson 2 of 9 — Tips & Frameworks** · ~10 min

The "it depends" answer that actually works. The 4-part
structure for any tradeoff question. The senior SA move:
name the alternative, the constraint, and the implication.

---

## 1. The "it depends" problem

The "it depends" answer is the most common answer in
SA interviews. It's also the most commonly *failed*
answer, because most candidates say "it depends"
without specifying what it depends on.

The wrong "it depends":

> "It depends on the workload."

The senior SA "it depends":

> "It depends on 3 specific constraints. First, if
> the workload requires sub-millisecond latency with
> read-heavy traffic, the right answer is DynamoDB.
> Second, if the workload requires complex queries
> with strong consistency, the right answer is
> Aurora. Third, if the workload is time-series
> write-heavy, the right answer is Bigtable. The
> tradeoffs in each case are X, Y, Z."

The senior SA answer specifies *what* it depends on
and *which* answer is right in each case. The 4-part
structure is the move that signals senior SA.

---

## 2. The 4-part tradeoff structure

For any tradeoff question, the 4-part structure:

| # | Part | What to say |
|---|---|---|
| 1 | **The choice** | "The right answer is X." |
| 2 | **The rationale** | "Because [specific constraint that makes X right]." |
| 3 | **The alternative considered** | "We considered Y, but [specific reason it doesn't fit]." |
| 4 | **The tradeoff** | "The cost of X is [specific thing given up]." |

The 4 parts together take 30-45 seconds. A junior SA
gives 1-2 parts; a senior SA gives all 4.

A worked example (the question: "Aurora vs DynamoDB for
a real-time feature store?"):

> **Choice:** "DynamoDB is the right answer for this
> workload."
>
> **Rationale:** "Because the workload is
> read-heavy (100k reads/sec) with single-digit-
> millisecond latency required. DynamoDB gives us
> both. Aurora would require significant caching
> (ElastiCache) to hit the latency requirement,
> which adds operational complexity."
>
> **Alternative considered:** "We considered
> Aurora, but Aurora's read scaling requires
> read replicas, which adds 5-15ms of replication
> lag — that breaks the sub-10ms latency
> requirement."
>
> **Tradeoff:** "DynamoDB's query patterns are
> limited (no joins, no SQL). If the team needs
> complex queries later, we'd need a separate
> analytics database. The tradeoff is operational
> simplicity and latency for query flexibility."

The 4 parts together: 40 seconds. The senior SA
answer.

---

## 3. The 5 things the senior SA move signals

When you use the 4-part tradeoff structure, you signal
5 things:

1. **You have a model.** The choice isn't random; it's
   driven by a *specific* constraint.
2. **You considered alternatives.** You weren't
   intellectually lazy; you thought about other options.
3. **You know the tradeoffs.** You can articulate what
   you're giving up, which means you actually evaluated
   the choice.
4. **You can be wrong.** The "alternative considered"
   part makes it clear that the *right answer* depends
   on the constraint. If the constraint changes, the
   answer changes.
5. **You can defend.** If the customer pushes back,
   you can explain your reasoning and adapt.

The 5 signals compound. A candidate who does all 5 gets
4/4 on tradeoff questions.

---

## 4. The 5 anti-patterns for tradeoff questions

### Anti-pattern 1: "It depends" without specifics

You say "it depends on the workload." The interviewer
reads this as "I don't know."

**Fix:** Name the 2-3 specific constraints that
determine the answer. Use the 4-part structure.

### Anti-pattern 2: "X is the best" without justification

You say "Aurora is the best database." The interviewer
reads this as "I'm making a claim I can't defend."

**Fix:** Name the constraint that makes X the right
answer for *this* workload.

### Anti-pattern 3: "X has tradeoffs" without naming them

You say "every choice has tradeoffs." The interviewer
reads this as "I'm being generic."

**Fix:** Name the *specific* tradeoff for *this* choice.
"X costs Y in terms of Z."

### Anti-pattern 4: No alternative considered

You name X without naming Y. The interviewer reads this
as "I haven't thought about the alternatives."

**Fix:** Name the alternative considered and rejected,
with the reason.

### Anti-pattern 5: Over-confident

You say "X is the right answer, period." The interviewer
reads this as "I can't adapt if the constraint changes."

**Fix:** Frame as "X is the right answer *given* these
constraints. If the constraints change, the answer
might change." Adaptability is the senior SA signal.

---

## 5. The "constraint leads, choice follows" pattern

The senior SA pattern for any tradeoff question:

1. **Identify the constraint.** What's the most
   important constraint on the choice (latency, cost,
   scale, consistency, compliance, operational
   capacity)?
2. **List 2-3 candidate choices.** For each, what
   specifically matches and what specifically doesn't?
3. **Pick the best fit.** The choice that matches the
   most important constraint while fitting the others
   tolerably.
4. **Name the tradeoff.** What's specifically given up
   by picking this choice?

The 4-step pattern takes 30-45 seconds in an
interview. The candidate who does it consistently is
the senior SA.

---

## 6. A worked example: Real-time analytics pipeline

The question: "We're building a real-time analytics
pipeline. 1M events/sec, sub-second latency, 24-hour
retention, on AWS. What database would you use?"

### The constraint-led answer

> **Choice:** "DynamoDB with Streams + Lambda for
> query."
>
> **Rationale:** "Because the workload is
> write-heavy (1M events/sec), read-heavy
> (real-time dashboards), and requires sub-second
> latency. DynamoDB handles 1M writes/sec at
> single-millisecond latency. The Streams + Lambda
> combo gives us real-time aggregations without
> running a separate stream-processing cluster."
>
> **Alternative considered:** "We considered Aurora
> with Kinesis, but Kinesis scaling (shards) becomes
> the bottleneck above 500k events/sec without
> significant operational overhead. We also considered
> Timestream (AWS's time-series DB), but its query
> language is less flexible for our real-time
> dashboards."
>
> **Tradeoff:** "DynamoDB's query patterns are
> limited (no joins, no SQL aggregations beyond
> basic ones). The Lambda-based aggregation layer
> handles the complex queries, but adds Lambda
> cost. The tradeoff is operational simplicity at
> the database layer for higher Lambda cost."

The 4-part answer is 50-60 seconds. The senior SA
move.

---

## Try it

For each of the 5 tradeoff questions below, practice
the 4-part structure:

1. "Aurora vs DynamoDB for an OLTP application with
   10k reads/sec and complex joins?"
2. "Lambda vs EKS for an event-driven processing
   pipeline with 10M events/day?"
3. "Kafka vs SQS for an event stream with ordering
   guarantee and 7-day replay?"
4. "S3 vs EBS for a database storage layer with
   10k IOPS?"
5. "CloudFront vs ALB for a global web application
   with 1B requests/day?"

Practice each one out loud. Time yourself. Aim for
30-60 seconds. The 4 parts should all be present;
the specifics should match the workload.

By the 5th, the 4-part structure will be in muscle
memory. That's the tradeoff round of any architecture
interview.
