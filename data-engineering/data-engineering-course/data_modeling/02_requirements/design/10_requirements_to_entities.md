# Lesson 10 — Translating Requirements to Entities

> **What you'll learn:** the mechanical step of going from a
> requirements doc to an entity list. By the end of this lesson
> you'll be able to take any use case and back out the entities
> and the relationships.

---

## The translation rules

Once you have a requirements doc, translating to entities is a
mechanical exercise. There are five rules:

1. **Each noun is an entity.** A use case like "MAU by month" has
   nouns: *user*, *month*. Each is a candidate entity.
2. **Each verb is a relationship or a fact.** "User does workout"
   is a fact (the workout event). "User has country" is a
   relationship (user → country).
3. **Each metric is a measure on a fact.** "Average workout
   duration" is a measure on `fact_workouts`. "Workouts per
   user" is a derived metric, computed at query time.
4. **Each filter or grouping is a dimension.** "By country" is a
   dimension. "By month" is a date dimension. "By workout type"
   is a workout type dimension.
5. **Each slowly-changing thing is a dimension with SCD.** A
   user's fitness level changes over time → `dim_users` SCD 2.

The output of the translation is a list of *candidate* entities.
You'll then prune (some "entities" are really attributes of other
entities) and connect (draw the relationships).

---

## Worked translation — fitness app

Requirements doc (compressed):

```markdown
Use cases:
1. MAU = unique users with >=1 workout in a month
2. Avg workouts per user per week
3. Retention by cohort (signup month × order month)
4. Avg workout duration by workout type

Sources: users table (Postgres), workouts table (Postgres),
exercises table (Postgres).
```

### Apply the rules

| Use case | Nouns → Entities | Verbs → Facts / Relationships | Filters → Dimensions |
|---|---|---|---|
| 1. MAU by month | user, month | user has workout → `fact_workouts` | month → `dim_date` |
| 2. Workouts per user per week | user, week | user has workout → `fact_workouts` | week → `dim_date` |
| 3. Retention by cohort | user, cohort | user signs up → `fact_signups` or SCD on `dim_users` | signup month → `dim_date` |
| 4. Avg duration by workout type | user, workout | workout has type → `fact_workouts` | workout type → `dim_workout_types` |

### The entity list

After applying all four use cases:

- **User** — dim
- **Workout** — fact (one row per workout session)
- **WorkoutType** — dim
- **Exercise** — dim (associated with a workout)
- **Date** — conformed dim

### The relationship list

- A user has many workouts (1-to-many, `dim_users.user_id` →
  `fact_workouts.user_id`).
- A workout has one workout type (many-to-1, `fact_workouts.workout_type_id` →
  `dim_workout_types.workout_type_id`).
- A workout has many exercises (many-to-many via a bridge
  table, or stored as a JSON array on the workout row).
- A workout happens on a date (many-to-1, `fact_workouts.date_id` →
  `dim_date.date_id`).

That's the ER diagram in words. The candidate now draws it on
the whiteboard (Lesson 13 covers ER notation).

---

## The cardinality check

Every relationship has a cardinality. Get it wrong and the
schema breaks.

- **1-to-many** — one user has many workouts. The "many" side
  holds the foreign key.
- **many-to-1** — the inverse of the above. Same physical
  representation.
- **many-to-many** — workouts and exercises. Requires a bridge
  table. The bridge holds two foreign keys plus any
  measure-on-the-relationship (e.g., `reps`, `weight`).
- **1-to-1** — rare in a warehouse. Usually a sign that the two
  entities should be one.

The cardinality is a property of the *domain*, not the schema.
A user has many workouts *because that's how the product works*.
The schema encodes it; the schema does not invent it.

---

## The prune step

Not every entity survives the prune. Three common prune cases:

### Case 1 — Entity is really an attribute

> "We need a `workout_status` table: planned, started, paused,
> completed, abandoned."

This is an attribute of the workout, not an entity. Either:

- Make it a column on `fact_workouts` (5 distinct values, low
  cardinality — perfect for a dimension column), OR
- Make it a tiny `dim_workout_status` table (if you have many
  status-specific attributes you want to track, e.g.,
  `is_terminal`, `minutes_in_status`).

The 5-value version almost never needs a separate table.

### Case 2 — Entity is really a metric

> "We need an `engagement_score` table that holds the daily
> engagement score for each user."

Engagement score is a *computed metric*, not an entity. It
belongs in a metric table or a view, not a base fact table.
If the modeler wants to expose it as a fact, they should
document the formula and the freshness, not invent a new
table.

### Case 3 — Entity is a fact, not a dimension

> "We need a `purchase` table: every purchase a user has made."

A purchase is an event — a fact. It belongs in `fact_orders` or
`fact_order_items`, not in a `dim_purchases` table. A common
confusion for new modelers.

---

## The connect step

After pruning, draw the relationships. There are three patterns:

### Pattern A — Fact with multiple dims

```
dim_a, dim_b, dim_c  ───  fact_x  ───  measures
```

The most common star-schema pattern. The fact holds foreign keys
to all the dims and the measures.

### Pattern B — Fact with a bridge

```
dim_a  ───  fact_x  ───  dim_b
              │
              └──  bridge_dim_c_dim_d  ───  dim_c, dim_d
```

Used for many-to-many relationships between a fact and a
dimension (e.g., workouts and exercises).

### Pattern C — Factless fact

```
dim_a  ───  fact_x  ───  dim_b
              (no measures)
```

Used to record *that an event happened* without measuring it.
E.g., "user X attended class Y on date Z" — no numeric measure,
just the join keys. Covered in Lesson 27.

---

## Try it

Take the requirements doc you wrote for the e-commerce prompt
(Lesson 07). Apply the 5 translation rules. List the entities,
the relationships, and the cardinalities. Time yourself: 10
minutes.

The output should be 4–7 entities, 5–10 relationships, and a
clear "this is the fact, these are the dims" split.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
