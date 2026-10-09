# Lesson 01 — Introduction to Data Modeling Questions

> **What you'll learn:** what the data modeling interview round actually
> is, when you'll see it, and what it tests. By the end of this
> lesson you'll know the difference between a modeling round, a SQL
> round, and a system-design round.

---

## What the round is

The data modeling interview is a 30–60 minute whiteboard conversation.
The interviewer hands you a vague product prompt ("design a schema for
a fitness app" or "how would you model Uber's data warehouse") and
watches how you think.

It is **not** a SQL test. You will not be asked to write window
functions or debug a query. The interviewer wants to see how you
reduce a fuzzy product description to a set of tables, dimensions,
and facts that an analyst could query on day one.

It is **also not** a system-design round. There is no "draw the
boxes-and-arrows topology" here. The boxes are tables, and the
arrows are foreign keys. The hard parts are the *decisions*, not the
plumbing.

---

## What it actually tests

There are four things the interviewer scores you on, in roughly this
order of importance:

1. **Discovery** — can you ask the right questions before you draw
   anything? "What's the grain?" "How do we measure engagement?" "Do
   we need historical attribution, or is the current value enough?"
2. **Grain** — can you commit to *one* grain per fact table, name it
   out loud, and make every later decision consistent with it?
3. **Tradeoffs** — can you defend your choices? "I'm picking SCD Type
   2 here because the fitness level changes over time and we need
   historical accuracy, even though it doubles the row count of
   `dim_users`."
4. **Communication** — can you narrate the schema as you draw it? The
   whiteboard is *visible* — a quiet candidate gets partial credit.
   A candidate who talks through their thinking out loud gets the
   same schema scored a full bucket higher.

The rubric is covered in detail in Lesson 03. For now, the point is:
the round is a structured conversation, not a quiz.

---

## When you'll see this round

You'll see a dedicated data-modeling round at companies that treat
data engineering as a distinct discipline: **Meta, Uber, Lyft,
Airbnb, Pinterest, Spotify, Netflix, Stripe, Doordash, Instacart,
Snowflake, Databricks**. Big banks and consultancies often bundle
modeling into a SQL round instead.

Senior+ candidates (L5/L6, Staff) will see it in two flavors:

- **Pair modeling**: 30–45 minutes, one or two specific subdomains
  (e.g., "design the data model for a subscription product's
  retention dashboard"). Expects depth, not breadth.
- **Open whiteboard**: 60 minutes, broader prompt ("design the
  warehouse for a ride-sharing company"). Expects breadth-first
  exploration, then a depth dive on the area the interviewer cares
  about.

Both flavors use the same 5-step playbook — see Lesson 02.

---

## The anatomy of a data modeling question

Almost every question has the same shape:

> "Design the [warehouse | schema | data model] for [Product X] so
> that the [analytics | data science | operations] team can answer
> [question Y]."

For example:

- "Design a data warehouse for **Uber** so the ops team can
  measure **driver utilization by city by hour**."
- "Design the schema for a **fitness app** so we can report
  **monthly active users and workout engagement**."
- "Design a **Spotify** warehouse so we can answer
  **how song skip rate varies by genre and release decade**."

Notice the pattern: each question names a **product**, a **team**
(the consumer of the data), and a **question** (the use case). Your
job is to back out from the question to a set of tables that can
answer it.

---

## What "good" looks like

A senior candidate's answer has these properties:

- A **requirements doc** — written (or narrated) up front, before
  any tables. Five to ten lines. Names the consumers, the metrics,
  the grain.
- An **ER diagram** — the high-level relationships between entities.
  Could be Chen's notation, could be boxes-and-arrows, could be
  Mermaid. The notation matters less than the consistency.
- A **star schema** — one or more fact tables, each surrounded by
  the dimensions that describe it. Star, not snowflake, by default.
- **Tradeoffs called out** — SCD type, snapshot vs transactional
  fact, partitioning strategy. Each one named and defended in one
  sentence.
- **A depth dive** — the interviewer drives you into one area. The
  senior candidate is ready: they know which fact table is hot, and
  they can talk about it for ten minutes.

A mid-level candidate draws the tables, gets the right tables, and
loses the round because they never said *why* they picked the grain
or the SCD type.

---

## Try it

Pick one product you know well (Slack, Notion, Robinhood, your own
employer's product). In 5 minutes, write down:

1. The consumers of the data (who queries the warehouse?).
2. Three questions the warehouse must answer.
3. The grain of one fact table for each question.
4. One SCD choice you'd make and why.

If you can do this without looking anything up, you're ready for
Module 02. If not, Module 02 is exactly the place to fix it.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
