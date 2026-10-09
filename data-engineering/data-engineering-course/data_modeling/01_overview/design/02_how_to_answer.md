# Lesson 02 — How to Answer Data Modeling Questions

> **What you'll learn:** the 5-step playbook that every strong data
> modeling answer follows, with a worked example from the canonical
> "design a fitness app schema" question.

---

## The 5-step playbook

Every data modeling answer — from a 30-minute pair-programming round
to a 60-minute open whiteboard — follows the same five steps. If you
can internalize this structure, you will not freeze when the
interviewer hands you the prompt.

```
┌──────────────────────────────────────────────────────┐
│ Step 1: Discovery questions (5 min)                   │
│   - Functional: features, actors, use cases            │
│   - Non-functional: scale, freshness, retention        │
│   - "What's the grain?"  (always ask)                  │
│                                                       │
│ Step 2: Requirements doc (3 min)                       │
│   - 5–10 lines, written or narrated                    │
│   - Names the consumers, the metrics, the grain        │
│                                                       │
│ Step 3: ER diagram (5 min)                             │
│   - High-level entities + relationships                │
│   - Chen's notation, boxes-and-arrows, or Mermaid      │
│                                                       │
│ Step 4: Star schema (10 min)                           │
│   - Translate ER → fact(s) + dimension(s)              │
│   - Pick a grain for each fact table; say it out loud   │
│                                                       │
│ Step 5: Tradeoffs + depth dive (10–20 min)             │
│   - SCD type, fact type, partitioning                   │
│   - Interviewer drives the depth dive — be ready        │
└──────────────────────────────────────────────────────┘
```

The first three steps are *always* the same. Steps 4 and 5 adapt to
the question.

---

## Step 1 — Discovery questions (5 minutes)

You ask questions. The interviewer answers. The questions you ask
are themselves scored — the candidate who asks "what does engagement
mean — daily, weekly, monthly?" demonstrates that they understand
metrics have a definition, not a vibe.

The 5 categories of questions (5W+H adapted for data modeling):

| Question | Why it matters |
|---|---|
| **Who** are the consumers? (analysts, DS, ops, ML, finance) | Drives which metrics and which dimensions matter. |
| **What** are the 3–5 questions the warehouse must answer? | Drives the choice of fact table. |
| **When** is freshness required? (real-time, hourly, daily) | Drives streaming vs batch, snapshot vs accumulating. |
| **Where** are the source systems? (OLTP DB, events, third-party) | Drives the staging layer. |
| **Why** does this question matter? (revenue, retention, growth) | Drives priority and depth. |
| **How** is the metric defined? (DAU = unique logged-in users? unique users with any event?) | Drives the exact column and grain. |

> **Always ask "what's the grain?"** The grain is the single most
> important decision in dimensional modeling. If you don't pin it
> down, the rest of the answer is built on sand.

---

## Step 2 — Requirements doc (3 minutes)

Write a 5–10 line requirements doc before drawing. This is the
*artifact* the interviewer sees you produce. The doc has:

1. **Consumers** — who queries this warehouse.
2. **Use cases** — 3–5 questions the warehouse must answer.
3. **Source systems** — where the data comes from.
4. **Volume** — orders of magnitude (rows/day, GB/day).
5. **Freshness** — hourly, daily, real-time.
6. **Retention** — how long we keep the data.

You can write it on the whiteboard, in the chat, or narrate it.
What you cannot do is skip it. The senior candidates all write one;
the mid-level candidates all skip it.

---

## Step 3 — ER diagram (5 minutes)

Draw the high-level entities and the relationships between them.
This is the *conceptual* model. It does not need every column — it
needs every entity and every relationship.

For a fitness app, the ER looks like:

```
┌────────┐ 1   * ┌──────────┐ *   1 ┌──────────┐
│ Users  ├───────┤ Workouts ├───────┤ Exercises│
└────────┘       └──────────┘       └──────────┘
     │ 1                               │
     │ *                               │
┌──────────┐ 1   * ┌──────────┐ *   1 │
│ Sessions │       │Devices   │       │
└──────────┘       └──────────┘       │
                                        │
┌──────────┐ 1   * ┌──────────┐ *   1 │
│ Workout  ├───────┤  Sets    ├───────┘
│ Types    │       │          │
└──────────┘       └──────────┘
```

The notation is yours. Chen's notation is the academic default;
boxes-and-arrows is fine; Mermaid is fine. Pick one and be
consistent.

---

## Step 4 — Star schema (10 minutes)

Translate the ER diagram into one or more fact tables surrounded by
their dimensions. This is the *physical* model — the one the
analysts will actually query.

For a fitness app:

```
            ┌──────────────┐
            │  dim_users   │
            └──────┬───────┘
                   │ user_id
                   ▼
┌──────────┐  ┌──────────────┐  ┌──────────────┐
│dim_dates │◄─┤ fact_workouts├─►│dim_workout_  │
│          │  │              │  │   types      │
└──────────┘  │ measures:    │  └──────────────┘
              │  duration    │
              │  calories    │  ┌──────────────┐
              │  sets        │◄─┤ dim_exercises│
              └──────────────┘  └──────────────┘
```

The grain is **one row per workout session**. You must say that
out loud. Every measure, every dimension key, every join — all
of it is consistent with that grain.

---

## Step 5 — Tradeoffs + depth dive (10–20 minutes)

Pick the three or four decisions that have alternatives and call
them out:

- **SCD type for `dim_users`** — Type 1 (overwrite) for things
  that don't matter historically (display name), Type 2 for things
  that do (fitness level, age).
- **Fact type for the workout table** — transactional
  (one row per workout session), not snapshot.
- **Partitioning** — by `workout_date` for time-based queries.
- **Indexes** — bitmap on `dim_users.country`, B-tree on
  `fact_workouts.user_id`.

The interviewer will then drive you into a depth dive. Common
depth-dive topics:

- "How would you handle a user who deletes their account?"
- "How do you track historical fitness level for accurate
  cohort analysis?"
- "How would you add a new workout type mid-quarter?"

You don't need to know the answer in advance. You need to have
*built* a model that supports the answer — that's the whole
point of steps 1–4.

---

## Worked example — "Design a fitness app schema"

> Interviewer: "Design the data warehouse for a fitness app so
> the analytics team can report on monthly engagement."

> Candidate: "Before I draw, can I ask a few discovery questions?"

1. **What does 'engagement' mean here?** Daily active users,
   weekly active users, sessions per user, workouts per user?
2. **What entities does a workout have?** A user, a date, a
   workout type, a duration, an optional set of exercises?
3. **Do we need to track historical fitness level changes?** E.g.
   a user moves from Beginner → Intermediate.
4. **What's the freshness?** Daily batch, hourly, real-time?
5. **What's the retention?** Forever, or 2 years?

> Interviewer: Engagement = monthly active users + average
> workouts per user. Entities: user, workout, exercise. SCD 2
> for fitness level. Hourly batch. 2-year retention.

> Candidate: "OK, the requirements are:
> - **Consumers:** analytics team
> - **Use cases:** MAU, workouts/user/month, retention by cohort
> - **Grain of the fact table:** one row per workout session
> - **Sources:** users table (OLTP), workouts table, exercises
>   table
> - **Freshness:** hourly
> - **Retention:** 2 years
>
> The star schema is `fact_workouts` (one row per session),
> surrounded by `dim_users`, `dim_workout_types`,
> `dim_exercises`, and `dim_date`."

> *(draws the diagram, narrates each table, then calls out the
> SCD 2 choice for `dim_users` and the transactional fact for
> `fact_workouts`)*

That's the shape of a strong answer in under five minutes of
narration.

---

## Try it

Pick any of the canonical questions in
[`docs/reference/de_interview_canonical_questions.md`](../../../docs/reference/de_interview_canonical_questions.md#data-modeling-questions)
and run the 5-step playbook end-to-end. Time yourself. The first
time you do this, budget 30 minutes. By the time you've done three,
you should be under 15.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
