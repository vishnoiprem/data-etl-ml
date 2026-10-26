# 03 — Rubric for ETL Questions

> **Lesson 3 of 5 — Overview**

Every interviewer has a rubric. You should know it as well as they
do — because the rubric is the answer key to the test you're taking.
This lesson is the most re-readable lesson in this track; come back
to it before every interview.

---

## 1. The 5-bucket rubric

Most senior+ interviewers grade on five buckets. They're not
weighted equally. The weights below are the typical split at FAANG,
Stripe, Airbnb, and the big banks; the exact numbers vary by company
but the order does not.

| Bucket | Weight | What they're looking for |
|---|---|---|
| **Problem framing** | 15% | Did you clarify? Did you name the right non-functionals? |
| **Estimation** | 10% | Back-of-envelope numbers. Are they in the right ballpark? |
| **High-level architecture** | 20% | Are the components named correctly? Is the data flow sensible? |
| **Hot-path deep dive** | 35% | Did you go deep on the 1 thing that matters? Did you cover failure modes? |
| **Tradeoff articulation** | 20% | Did you name tradeoffs? Did you defend your choices? |

**The deep dive is 35%.** That's the most points on the table. Spend
your time there.

---

## 2. Bucket 1: Problem framing (15%)

| Score | What it looks like |
|---|---|
| 5/5 | Asks 4-6 clarifying questions, repeats back, names the latency and the consumer. |
| 3/5 | Asks 2-3 questions, but skips volume or downstream consumer. |
| 1/5 | Asks 0 questions and starts drawing. |

A 5/5 framing turns into a 5/5 deep dive. A 1/5 framing is very hard
to recover from. The first 5 minutes are disproportionately important.

---

## 3. Bucket 2: Estimation (10%)

The interviewer doesn't want a precise number. They want a
*ballpark* with the arithmetic shown. The single most common
mistake: not showing the math.

> ❌ "It's about 1 terabyte per day."
> ✅ "10K events/sec × 1 KB/event × 86400 sec/day ≈ 864 GB/day. So
>    about 1 TB/day."

Show the math. Even if the math is rough, the *showing* is what gets
you the points. The number itself almost doesn't matter.

| Score | What it looks like |
|---|---|
| 5/5 | Shows the math. Round numbers in the right order of magnitude. |
| 3/5 | Numbers are right but no math shown. |
| 1/5 | No numbers at all. |

---

## 4. Bucket 3: High-level architecture (20%)

The rubric is simpler than you think: 3-5 boxes, labeled arrows, a
clear left-to-right or top-to-bottom flow. That's the architecture.

| Score | What it looks like |
|---|---|
| 5/5 | 3-5 boxes, every arrow labeled with protocol + SLA, a sensible flow. |
| 3/5 | 5-7 boxes, most arrows labeled, the flow is correct but a few details missing. |
| 1/5 | 10+ boxes, arrows unlabeled, the flow is unclear. |

**The failure mode is too many boxes.** If your diagram has 10
boxes, you have a tool list, not an architecture. Strip it back to
the essentials.

---

## 5. Bucket 4: Hot-path deep dive (35%)

This is the make-or-break bucket. The interviewer picks the hot
path — usually extraction, transformation, or reliability — and
expects 5-10 minutes of uninterrupted explanation.

| Score | What it looks like |
|---|---|
| 5/5 | A concrete API or SQL example. One failure mode. One mitigation. Mentions idempotency. |
| 3/5 | A vague description. Mentions failure modes but not how they're handled. |
| 1/5 | No deep dive. The candidate ends after the high-level diagram. |

The 5/5 answer has 3 ingredients. Memorize them:

1. **Concrete artifact** — show a SQL transform, a JSON message
   schema, a config snippet. Anything that says "I've done this
   before."
2. **Failure mode** — "If X breaks, here's what happens." Pick one.
3. **Mitigation** — "We handle that with Y." Be specific.

---

## 6. Bucket 5: Tradeoff articulation (20%)

Every senior design names 2-3 tradeoffs unprompted. Tradeoffs are
*not* a "would you rather" question — they're a *you chose X over Y
for reason Z* statement.

| Tradeoff | Common senior framing |
|---|---|
| Batch vs streaming | "I'd start with hourly batch because the SLA allows it. Sub-minute would push us to Kafka + Flink and 3× the cost." |
| ETL vs ELT | "ELT is the default in 2026 because the warehouse is fast and storage is cheap. ETL only when there's a regulatory reason to scrub before landing." |
| Lakehouse vs warehouse | "Lakehouse for the source of truth (raw + bronze), warehouse for the curated gold. The medallion pattern is the bridge." |
| CDC vs polling | "CDC for low-latency and completeness. Polling only when the source has no binlog (older Oracle, SaaS APIs)." |
| At-least-once vs exactly-once | "At-least-once with idempotency keys is the practical answer. True exactly-once is expensive and rarely worth it." |

If you say these things in the first 10 minutes, you have a senior
answer. If you say them only when prompted, you have a mid answer.

---

## 7. The meta-pattern: "unprompted senior moves"

The senior candidates consistently do things the mid candidates don't:

- **Mention monitoring unprompted.** "I'd add a reconciliation check
  that compares source and destination row counts after every
  pipeline run."
- **Mention cost.** "Storage is cheap but Kafka + Flink would 3× our
  monthly bill. Batch is the right call."
- **Mention failure.** "If the source is unreachable for > 1 hour we
  page on-call. The pipeline doesn't auto-retry forever because
  backfill is cheaper than thrashing."
- **Mention evolution.** "Schema evolution is the silent killer.
  Every source needs a schema registry and a contract test."

These four moves alone will move you from a 3/5 to a 4.5/5 in the
interviewer's head.

---

## Try it

Take the most recent system design interview you gave (or any mock
interview transcript). Score yourself against the 5 buckets. Where
did you score lowest? Spend 30 minutes practicing just that bucket.
The rubric is the most leverage you have in the next 4 weeks.
