# Lesson 12 — "PM at a food delivery app: conversion rates declined. How do you investigate?"

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
>
> **Companion:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)
>
> **Pattern:** Product-sense-as-investigation. The bridge between behavioral and SQL/modeling. The most underprepared question in the bank.

---

## Why this lesson

This is the question **every** senior DE candidate gets at Meta,
Google, Uber, Lyft, DoorDash, and they **don't prepare for it** —
because it doesn't fit STAR, doesn't fit system design, and doesn't
fit SQL. It is its own round type: **product-sense investigation**.

The interviewer is not testing whether you can write SQL — they
already have a SQL round. They are testing whether you can:

1. Form a *hypothesis tree* before looking at any data.
2. *Segment* a metric correctly (by user × time × platform × cohort).
3. Distinguish *instrumentation changes* from *user behavior changes*.
4. *Rank* causes by likelihood and *recommend* the next 3
   experiments.

## The framework — 7 steps, 5-7 minutes spoken

| Step | What you say |
|---|---|
| **1. Define the metric precisely** | "Conversion from browse to order. I need: numerator = orders placed, denominator = users who reached the restaurant page. Same definition, same funnel step." |
| **2. Check the funnel for upstream / downstream drift** | "Bounce rate went up? Order-success rate went down? That tells me where in the funnel to look first." |
| **3. Segment by user × time × platform** | "New vs. returning? iOS vs. Android? Region? Day of week? Hour of day?" |
| **4. Check for instrumentation changes** | "Did a deploy ship in the window? Did an SDK update? Did a taxonomy change?" |
| **5. Check for upstream data issues** | "Did the restaurant-inventory feed drop? Did a payment provider add a new failure code we didn't map?" |
| **6. Check for competitor / external launches** | "Did a competitor launch in the affected region? Is there a holiday / event / weather event?" |
| **7. Rank by likelihood + recommend 3 experiments** | "Most likely: (a)…, (b)…, (c)…. I'd run experiment 1 first because X." |

## Worked example — ride-share pickup-time metric drop

> **Step 1.** The metric is *pickup-time p50*: the median time from
> "rider matched with driver" to "rider in car." It dropped from 3.2
> to 3.8 minutes over the past week.
>
> **Step 2.** The funnel: match → driver-en-route → driver-arrived →
> rider-in-car. Where did the slippage come from? I check each leg
> separately.
>
> **Step 3.** Segments: (a) new vs. returning rider, (b) iOS vs.
> Android, (c) top-10 cities vs. tail, (d) weekday vs. weekend,
> (e) hour-of-day.
>
> **Step 4.** Instrumentation: did the pickup-arrival event schema
> change in the past week? Did the matching service deploy? Did the
> map provider swap?
>
> **Step 5.** Upstream: is the driver GPS stream degraded? Is there
> a new tile-loading latency issue?
>
> **Step 6.** External: weather event in the top-3 cities? Major
> sporting event? Driver supply shortage (longer wait, not longer
> ride)?
>
> **Step 7.** Ranking: most likely from priors is (a) a single-city
> weather event, (b) a recent matching-service deploy, (c) GPS
> stream degradation in the top-10 cities.

## What the interviewer is grading

**Meta — Aced 2026:** *"product sense"* is the **opening 10 minutes
of every onsite technical round**. This entire question *is* that
test. Did you start with the metric definition or the data? Did you
narrate the hypothesis tree before looking at numbers?

**Google — Datavidhya 2026:** *"comfort with ambiguity."* The data
isn't available during the interview — so you have to *reason about
the data without seeing it*. That's the test.

**Uber / Lyft / DoorDash:** The exact pattern, just renamed
"operations sense."

## The 4 common failure modes

1. **Jumping to a query** — "I'd run a SQL query to find…" No.
   Form the hypothesis tree first.
2. **No segmentation** — a global "conversion dropped" answer is
   useless. Every metric has segments.
3. **No instrumentation check** — 30% of "metric drops" are data
   bugs, not user behavior. The senior answer always checks.
4. **No ranked recommendation** — the question ends with "what next,"
   and the answer must end with a *numbered list of experiments*.

## Try it — your turn

Pick a real metric you've owned or analyzed. Pretend it dropped by
10% last week. Run through the 7 steps in 5 minutes out loud.

Time yourself. If you go past 7 minutes, you've spent too long on
hypothesis-tree formation and not enough on ranking.

## Pair with

- `06_de_project_deep_dive.md` — the 5-act project structure is the
  way to *narrate* the investigation outcome.
- `sql_interviews/06_window_functions/` and `04_aggregations/` — the
  SQL toolkit you'll need *after* forming the hypothesis.
- `data_modeling/02_requirements/` — the requirements doc is the
  artifact that comes out of this conversation.

---

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
