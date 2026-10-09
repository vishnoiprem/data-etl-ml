# Lesson 31 — Mock Interview: Fitness App Schema

> **Format:** mock interview transcript (~30 minutes).
> Read it aloud. Note how the candidate narrates every
> decision.

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

---

## The prompt

> Design a data model for a fitness app. The app tracks
> workouts, exercises, user profiles, and goals. We want
> to report on engagement (DAU, WAU, monthly active),
> retention (cohorts), and the popularity of exercises
> and workout types.

---

## The transcript

**Interviewer:** Design a data model for a fitness app.

**Candidate:** OK. Before I draw anything, I want to
clarify the use case. The brief mentions engagement,
retention, and exercise popularity. Are these three
separate dashboards, or is the warehouse one set of
tables that serves all three?

**Interviewer:** One warehouse. Three dashboards.

**Candidate:** Good — that means I want conformed
dimensions, not three separate stars. Next, let me
confirm a few things.

**Interviewer:** Go.

**Candidate:** "Active" — is that any user who opened
the app, or any user who logged a workout? And is
engagement measured daily, weekly, monthly, or all
three?

**Interviewer:** Active means logged at least one
workout. Engagement is daily, weekly, monthly.

**Candidate:** OK. "Workout" — is that a session, a
plan, or both? I.e., does a user follow a multi-week
plan that contains many sessions, or is each session
its own thing?

**Interviewer:** Both. Users follow a plan; the plan
has many sessions; each session has many exercises.

**Candidate:** So I have at least four levels: plan,
session, exercise, and the user. And probably a
join table between exercise and session because a
session has many exercises and an exercise appears in
many sessions. Last thing: do we need historical
attribution? If a user changes fitness level from
"beginner" to "intermediate," do we want Q1 sessions
to attribute to "beginner" or "intermediate"?

**Interviewer:** Yes, we want historical. Q1 sessions
should attribute to the user's Q1 fitness level.

**Candidate:** That's SCD 2 on the user dim. Good.

OK, here's my approach. I'll draw a Kimball star with
one fact table — `fact_workout_sets` — at the grain of
*one row per set within a workout session*. That's
the finest grain that's still meaningful: a session
has many sets, and a set has weight, reps, and
duration.

The dimensions:

- `dim_user` — SCD 2, with `effective_date` and
  `expiry_date` and `is_current`. Attributes: name,
  age, gender, country, fitness_level (beginner /
  intermediate / advanced), goal.
- `dim_date` — conformed. I'll role-play it for
  `workout_date` and `signup_date` on the user.
- `dim_exercise` — SCD 2. Exercises change — new
  variations show up, classifications change. Attributes:
  exercise_name, body_part (chest, legs, etc.),
  equipment (barbell, dumbbell, bodyweight), difficulty.
- `dim_workout_type` — a small junk-ish dim. Values:
  strength, cardio, hiit, yoga. Low cardinality, used
  in every group-by.
- `dim_plan` — degenerate-ish. A user can be on a
  plan, and the plan has a name. Could be on the
  fact as `plan_key` (degenerate) or as a real dim.
  I'll make it a real dim because plans have
  attributes (target_audience, weeks_long).

The measures on `fact_workout_sets`:

- `reps` — additive
- `weight_kg` — semi-additive (sum across users OK,
  sum across time not meaningful)
- `duration_seconds` — additive
- `calories_burned` — additive
- `rpe` (rate of perceived exertion, 1–10) — non-additive,
  but the analyst may want avg

Foreign keys on the fact:

```sql
FOREIGN KEY (user_key)       REFERENCES dim_user(user_key),
FOREIGN KEY (exercise_key)   REFERENCES dim_exercise(exercise_key),
FOREIGN KEY (workout_date_key) REFERENCES dim_date(date_key),
FOREIGN KEY (workout_type_key) REFERENCES dim_workout_type(workout_type_key),
FOREIGN KEY (plan_key)       REFERENCES dim_plan(plan_key)
```

**Interviewer:** Why one row per set, not one row per
session?

**Candidate:** Because per-set is the only grain that
lets the analyst answer "what's the average weight
per set for a given exercise in a given week." If I
aggregate to the session, the weight column becomes
an average and we lose the per-set distribution. Per
session also loses the per-exercise breakdown because
a session has many exercises. So one-row-per-set is
the right finest grain.

**Interviewer:** What if a workout has no sets — say,
a yoga session. Does it still get a row?

**Candidate:** Yes. A yoga session has sets of poses,
and each pose has a duration. The grain is still
"one row per set within a session," and a "set" of
poses is just a different set type. The measures on
the yoga row are `duration_seconds` and
`calories_burned`, with `reps` and `weight_kg` null or
zero.

**Interviewer:** Walk me through the engagement
dashboard.

**Candidate:** DAU is a count of distinct users with
at least one row in `fact_workout_sets` on a given
date. That's:

```sql
SELECT workout_date_key, COUNT(DISTINCT user_key) AS dau
FROM fact_workout_sets
GROUP BY workout_date_key;
```

WAU is the same with a 7-day window. MAU is 30-day
window. The fact is the source — we don't need an
aggregate table because the query is cheap. If it
became expensive at 100M+ rows, I'd add a daily
aggregate rollup.

**Interviewer:** How do you do cohort retention?

**Candidate:** Cohort by `signup_month` from
`dim_user.effective_date`. For each cohort month, count
the users who had at least one workout in month 0,
month 1, month 2, etc. The fact has `user_key` and
`workout_date_key`; the dim has `user_key` and
`signup_date_key`. The query:

```sql
WITH cohorts AS (
  SELECT user_key,
         MIN(workout_date_key) AS first_workout
  FROM fact_workout_sets
  GROUP BY user_key
),
cohort_sizes AS (
  SELECT
    (first_workout / 100) % 100 AS cohort_month,
    user_key
  FROM cohorts
)
SELECT c.cohort_month,
       ((f.workout_date_key / 100) % 100 - c.cohort_month) AS month_offset,
       COUNT(DISTINCT c.user_key) AS retained
FROM cohort_sizes c
JOIN fact_workout_sets f ON c.user_key = f.user_key
GROUP BY c.cohort_month, month_offset;
```

That gives you the cohort retention matrix.

**Interviewer:** What about SCD 2 — how do you make
sure the Q1 workouts attribute to the Q1 fitness
level?

**Candidate:** Temporal join. The fact has
`user_key` and `workout_date_key`. The dim has
`user_key`, `effective_date`, `expiry_date`. I join
on `user_key` AND
`workout_date_key BETWEEN effective_date AND expiry_date`.
That gives me the version of the user that was
current on the workout date. If a user was
"beginner" in Q1 and "intermediate" in Q2, all Q1
workouts join to the beginner row, all Q2 workouts
to the intermediate row.

**Interviewer:** What if the user is updated multiple
times in a day?

**Candidate:** That's unusual but possible. I'd add
`effective_timestamp` (datetime, not date) and join
on timestamp range. Or I'd enforce one SCD 2 update
per day in the loader and keep `effective_date` as a
date. Most warehouses do the latter because
day-granular SCD 2 is simpler and the analyst almost
never cares about intra-day versioning.

**Interviewer:** Tradeoffs?

**Candidate:** Three I'd call out:

1. **One row per set vs per session.** Per-set is
   more rows but more flexible. Per-session is
   smaller but loses per-exercise breakdown. I picked
   per-set because the brief says "popularity of
   exercises" — that requires per-exercise, which
   requires per-set.
2. **SCD 2 on user.** More storage, more complexity.
   SCD 1 would be simpler but loses historical
   attribution. I picked SCD 2 because the interviewer
   explicitly said "Q1 to Q1."
3. **Fact vs dim for plan.** I made plan a dim, but
   plan has only 10–20 rows. Could be a flag on the
   fact. I made it a dim because plans have
   attributes (target_audience) and the analyst
   probably wants to filter on them.

**Interviewer:** What indexes?

**Candidate:** B-tree on `fact_workout_sets(user_key)`
for the cohort join, B-tree on
`fact_workout_sets(workout_date_key)` for the
time-range queries, B-tree on
`dim_user(user_key, effective_date)` for the temporal
join. Bitmap-style on `workout_type_key` and
`exercise_key` if the planner needs help.

**Interviewer:** What partitioning?

**Candidate:** Range by `workout_date_key`, monthly.
Most queries are time-bounded and prune to 1–2
partitions. 24 partitions a year, drop the oldest
each month for retention.

**Interviewer:** Last question — how would you model
the "goal" attribute on the user?

**Candidate:** Depends on whether the user has one
goal or many. If one goal, it's a column on
`dim_user`. If many — "lose weight, run a 5K, sleep
better" — it's a separate `dim_goal` and a
bridge table `bridge_user_goal` (one row per
user-goal pair). The bridge table has
`user_key`, `goal_key`, and a `goal_started_date`. I'd
ask the interviewer which it is.

**Interviewer:** One goal per user.

**Candidate:** Then `dim_user.goal_key` is a FK to
`dim_goal`. Easy.

**Interviewer:** Great. That's time.

---

## Rubric scoring (4 buckets)

| Bucket | Score | Notes |
|---|---|---|
| **Clarifies the business** | 5/5 | Asked about "active," grain, SCD. |
| **Picks a grain** | 5/5 | One row per set, defended. |
| **Makes and defends tradeoffs** | 5/5 | Set vs session, SCD 1 vs 2, plan dim. |
| **Talks while drawing** | 5/5 | Narrated every decision. |

---

## Take-aways

- The candidate asked *four* clarifying questions
  before drawing anything. That's the difference
  between senior and junior.
- The grain is "one row per set" — not per session, not
  per workout. The brief said "popularity of exercises,"
  which forced the finest grain.
- SCD 2 on the user is the right call when historical
  attribution is required. The temporal join is
  explained.
- The cohort retention query is given in SQL — not
  pseudocode, but actual SQL.

---

## Try it

Time-box yourself to 30 minutes. Re-state the problem
in your own words. Draw the star schema. Then read the
solution above and compare.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
