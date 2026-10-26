# Lesson 03 — Rubric for Data Modeling Questions

> **What you'll learn:** the 4-bucket rubric interviewers actually
> use, with concrete examples of what "strong" and "weak" looks like
> for each bucket. By the end of this lesson you'll know exactly
> what a 4/4 answer looks like.

---

## Why the rubric matters

The interviewer's scoring is not vibes. Most companies have a
written rubric that the interviewer fills in during or right after
the round. You will not see the rubric, but you can reverse-engineer
it from the patterns of strong and weak answers.

There are four buckets, in this order of importance:

1. **Discovery & requirements** — did you ask the right questions?
2. **Conceptual model** — is the ER diagram correct and complete?
3. **Logical / dimensional model** — is the star schema sound?
4. **Tradeoffs & communication** — did you defend your choices and
   narrate clearly?

Each bucket is scored 1 (weak) to 4 (strong). The buckets are not
weighted equally — bucket 1 carries roughly 1.5× the weight of the
others, because a candidate who can't clarify a fuzzy prompt can
also build a wrong model, and a wrong model wastes the rest of the
round.

---

## Bucket 1 — Discovery & requirements (1.4 / weak to 4 / strong)

### What strong looks like

The candidate asks 5–8 questions before drawing. The questions are
*specific* to the prompt, not generic ("can you scale?").

> "Before I draw, can I ask: do we need to track changes to the
> user's fitness level over time, or do we only care about the
> current value? Because that drives the SCD choice for
> `dim_users`."

The candidate also writes a requirements doc (or narrates one).
The doc has consumers, use cases, grain, source systems, and
freshness.

### What weak looks like

The candidate starts drawing immediately. Or, worse, asks one
generic question ("any scale requirements?") and then draws.

A weak discovery bucket usually tanks the rest of the round,
because the candidate builds the wrong model. The interviewer then
spends 20 minutes watching the candidate debug their own design.

### What to do

Use the 5W+H framework from Lesson 02. Always ask "what's the
grain?" If the interviewer is silent or vague, make a reasonable
assumption and *say it out loud* ("I'll assume the grain is one
row per workout session, since that's the most common reading of
the prompt — please correct me if I'm wrong").

---

## Bucket 2 — Conceptual model / ER diagram

### What strong looks like

The ER diagram is *complete*: every entity the prompt names is
present, every important relationship is drawn, and the cardinalities
are correct (1-to-many vs many-to-many).

A strong ER for a fitness app includes Users, Workouts, Exercises,
WorkoutTypes, Devices, and Sessions. The candidate distinguishes
"Workout" (the event) from "WorkoutType" (the template), which
many mid-level candidates conflate.

### What weak looks like

Missing entities (no Devices, no Sessions), wrong cardinalities
(a user has *one* workout?), or no ER diagram at all — the
candidate jumps straight to the star schema.

### What to do

Before drawing the star schema, draw the ER. The ER is the *map*.
The star schema is the *territory*. If you don't have the map, you
will miss entities, and you will lose the round.

Use any notation. Chen's notation is the academic default; Mermaid
`erDiagram` is fine if the whiteboard is virtual. Boxes-and-arrows
is fine. Pick one and be consistent.

---

## Bucket 3 — Logical / dimensional model (star schema)

### What strong looks like

The star schema is at the *right grain*. Every fact table has its
grain stated out loud, in writing, in the same line as the CREATE
TABLE statement. The measures are at the right granularity. The
dimensions are normalized only as far as needed (star, not
snowflake, by default).

A strong fitness-app star has `fact_workouts` at the grain of
"one row per workout session," with measures
`duration_minutes`, `calories_burned`, `sets_completed`. The
dimensions are `dim_users` (SCD 2), `dim_workout_types`, and
`dim_exercises`. `dim_date` is a conformed dimension.

### What weak looks like

Multiple grains in one table. A fact table with both session-level
and user-level measures. Dimensions that double as facts (e.g., a
`user_gender` column on `dim_users` that should be a junk
dimension). Snowflaking where a star would do.

The most common weak pattern is "all the columns are in one big
table." This is the OLTP-in-the-warehouse anti-pattern.

### What to do

State the grain. Then state it again. Write it on the whiteboard
("GRAIN: one row per workout session"). Build the fact table
around that grain, and every measure must be a sensible
aggregation *at* that grain. `total_workouts` is a measure;
`lifetime_total` is not (it's a derived metric, not a fact).

---

## Bucket 4 — Tradeoffs & communication

### What strong looks like

The candidate narrates as they draw. They call out tradeoffs
without being asked. "I'm picking SCD Type 2 for `dim_users`
because the fitness level changes over time and we need historical
attribution, even though it doubles the row count of the dim."

A strong candidate also handles the depth-dive cleanly. When the
interviewer says "ok, let's go deep on `dim_users`," the
candidate has a clear mental model and can talk for 10 minutes
without re-discovering their own design.

### What weak looks like

Silent drawing. Or, the candidate draws the right schema and then
cannot answer the simplest follow-up ("why SCD 2?").

The silent-drawer pattern is the most common cause of senior
candidates getting a 3/4 instead of a 4/4. The schema is
correct; the rubric penalizes the silence.

### What to do

Narrate. Every table, every column, every choice. "I'm adding
`workout_date_key` to the fact table so we can join to
`dim_date` for month-end rollups — this avoids the `EXTRACT`
function at query time." If you don't have anything to say, say
*what you're about to draw* before you draw it.

---

## Putting it together

| Bucket | 4/4 (strong) | 1/4 (weak) |
|---|---|---|
| Discovery | 5–8 specific questions, requirements doc | Starts drawing immediately |
| ER diagram | Complete, correct cardinalities, every entity | Missing entities, wrong cardinalities |
| Star schema | Right grain, stated, defensible measures | Multiple grains, OLTP-shaped, unstated grain |
| Tradeoffs & comms | Narrates, defends, handles depth dive | Silent, can't answer follow-ups |

The strong candidate in bucket 1 almost always pulls the rest of
the round up. The weak candidate in bucket 1 almost always
drags the rest of the round down, even if their schema would
have been correct. **The single most leveraged thing you can do
in this round is ask the right questions up front.**

---

## Try it

Find a recent data modeling interview on YouTube (search "data
modeling interview fitness app" or "ride sharing data modeling
interview"). Watch the candidate. Score them on the 4 buckets.
You'll see the same patterns this rubric describes.

---

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
