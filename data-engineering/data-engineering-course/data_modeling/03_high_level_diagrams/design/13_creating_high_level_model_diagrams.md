# Lesson 13 — Creating High-Level Model Diagrams

> **What you'll learn:** the family of high-level diagrams you can
> draw to communicate a data model — ER, conceptual, logical,
> physical, and dimensional — and when each one is the right
> tool. By the end of this lesson you'll know which diagram to
> reach for in the first 5 minutes of an interview, and you'll
> be able to draw each one fast on a whiteboard.

---

## Why this lesson

A data modeling interview is two conversations in one: a
*design* conversation ("here's the model I would build") and a
*communication* conversation ("here's how I'm drawing it for
you"). The first conversation is meaningless without the second
— a perfect star schema that the interviewer can't read is a
failed interview. This lesson teaches you the four (or five)
diagrams every senior candidate has in their toolbox, and the
order in which to deploy them: an ER diagram to enumerate
entities, a conceptual diagram to commit to vocabulary, a
logical schema to commit to structure, a physical diagram to
commit to types and indexes, and a dimensional diagram to
answer the analyst's questions. Most candidates draw one
diagram poorly; senior candidates draw the right diagram at
the right moment.

---

## The five levels of data model

There are five levels of data model, ordered from most
abstract to most concrete. Every diagram you draw in an
interview sits at one of these levels. Knowing which level
you're at — and announcing it — is half the work.

| Level | What it answers | Notation | Example |
|---|---|---|---|
| **1. ER / Conceptual** | What are the entities and how are they related? | Chen's or crow's foot | User 1—* Order |
| **2. Logical** | What are the tables, columns, and keys? (no types) | Plain-text schema | `users(id, name)` |
| **3. Physical** | What are the DDL, types, indexes, partitions? | SQL DDL | `CREATE TABLE users (...)` |
| **4. Dimensional** | What are the facts and dims for analytics? | Star-schema sketch | `fact_orders` ★ surrounded by dims |
| **5. Operational / OLTP** | How are reads and writes served at low latency? | 3NF, B-tree, queue | (rare in interviews) |

The first four are what you'll draw. The fifth is the "are
you a backend engineer too?" differentiator; it's rarely
required for a data-modeling round, but knowing it exists is
a senior signal.

---

## Level 1 — ER / Conceptual diagram

The most common whiteboard diagram in a data-modeling
interview. It answers two questions:

1. What are the **entities** in the domain? (Users, Orders,
   Products, Workouts.)
2. How are the entities **related**? (A user has many
   orders; an order has many line items; a product is in
   many line items.)

The ER diagram is *not* the schema. It is the step before
the schema. It exists to make sure you don't miss an entity
or get the cardinalities wrong. Once the ER is right, the
schema is a mechanical translation (Lesson 14).

### Chen's notation

The academic standard. Peter Chen invented it in 1976.
It's still the cleanest way to draw an ER on a whiteboard.

```
  ┌─────┐                              ┌──────┐
  │     │                              │      │
  │     │────< has many >──────────────│      │
  │User │                              │Order │
  │     │                              │      │
  └─────┘                              └──────┘
   entity                               entity
```

- **Rectangle** = entity (a noun: User, Order, Product).
- **Diamond** = relationship (a verb: has, contains, owns).
- **Oval** = attribute (a property of an entity).
- **Lines** connect them. The cardinality is written at
  the endpoints (`1`, `N`, `M`).

You don't need to draw every attribute on the whiteboard.
You need to draw every entity and every relationship, with
the cardinalities. The attributes go in the DDL.

### Crow's foot notation

The industry default. Used by most diagramming tools
(Lucidchart, dbdiagram.io, Mermaid). Looks like a crow's
foot at the "many" end.

```
  ┌──────┐                              ┌──────┐
  │      │                              │      │
  │ User ├─────<  has many  >───────────┤ Order│
  │      │                              │      │
  └──────┘                              └──────┘
     |                                      ||
   "one"                              "one or many"
```

- `|` = one
- `||` = exactly one
- `o{` = zero or many
- `|{` = one or many

Crow's foot is faster to draw than Chen's. Use it if
you're comfortable; the diagram is the same, the notation
differs.

### The four cardinalities

There are exactly four cardinalities. Memorize them.

| Cardinality | Reads as | Example |
|---|---|---|
| 1-to-1 | "each A has exactly one B" | A user has one profile. |
| 1-to-many | "each A has many Bs" | A user has many orders. |
| Many-to-1 | "each B has one A" | (inverse of 1-to-many) |
| Many-to-many | "each A has many Bs and vice versa" | A workout has many exercises; an exercise appears in many workouts. |

The interview rule: **always state the cardinality, never
let the interviewer guess.** A user with "many" workouts
and a workout with "many" users (many-to-many) is a
different schema than a user with "many" workouts and a
workout with "one" user (one-to-many). The candidate who
doesn't say the cardinality out loud has not committed to
either.

### Worked ER — fitness app

> "Design a fitness app schema."

```
                 ┌──────────┐
                 │ Exercises│
                 └────┬─────┘
                      │ *
            *         │         1
   ┌────────────┐  ┌──┴────────┐
   │WorkoutTypes├──┤  Workouts │
   └────┬───────┘  └────┬──────┘
        │ 1             │ *
        │               │
        │               │ 1
   ┌────┴────┐          │
   │  Sets   │          │
   │(bridge) │          │
   └────┬────┘          │
        │ *             │
        └──────┬────────┘
               │ 1
          ┌────┴────┐
          │  Users  │
          └────┬────┘
               │ 1
               │ *
          ┌────┴────┐
          │ Devices │
          └─────────┘
```

Entities: Users, Workouts, Exercises, WorkoutTypes,
Devices, Sets (bridge).
Relationships:
- A user has many workouts (1-to-many).
- A workout has one workout type (many-to-1).
- A workout has many exercises, and an exercise is in
  many workouts (many-to-many, via Sets).
- A workout was done on one device (many-to-1).
- A user has many devices (1-to-many).

This is a complete ER. The candidate has named every
entity, every relationship, and every cardinality. The
schema is a mechanical translation (Lesson 14) — but the
ER was where the thinking happened.

---

## Level 2 — Logical schema

After the ER is right, you translate to a **logical
schema**: a list of tables and their columns, with
primary keys (PK) and foreign keys (FK) marked, but
*without* types. The logical schema is the contract
between you and the interviewer about the *shape* of
the model — what tables exist, what columns are in
each, and how they join.

```
users
  PK  id
      name
      email
      country
      signup_date

workouts
  PK  id
  FK  user_id          → users(id)
  FK  workout_type_id  → workout_types(id)
  FK  device_id        → devices(id)
      started_at
      duration_minutes
      calories_burned

workout_exercises           (bridge)
  PK,FK  workout_id        → workouts(id)
  PK,FK  exercise_id       → exercises(id)
        reps
        weight_kg
        sets
```

A logical schema is faster to draw than a full DDL, and
it forces the interviewer to engage on structure
(should this be a bridge table? should this column
denormalize?) rather than syntax.

---

## Level 3 — Physical schema (DDL)

The DDL. This is the level most candidates jump to, and
the level that loses them the most rounds. The DDL
commits to types (`TEXT` vs `VARCHAR(255)`), indexes
(`BTREE` vs `HASH`), partitions (`PARTITION BY date`),
and storage (`ROW` vs `COLUMNAR`). These are *physical*
optimizations, not design decisions.

```sql
CREATE TABLE workouts (
    id               INTEGER PRIMARY KEY,
    user_id          INTEGER NOT NULL,
    workout_type_id  INTEGER NOT NULL,
    device_id        INTEGER,
    started_at       TIMESTAMP NOT NULL,
    duration_minutes INTEGER,
    calories_burned  INTEGER,
    FOREIGN KEY (user_id)         REFERENCES users(id),
    FOREIGN KEY (workout_type_id) REFERENCES workout_types(id),
    FOREIGN KEY (device_id)       REFERENCES devices(id)
);

CREATE INDEX ix_workouts_user_id ON workouts(user_id);
CREATE INDEX ix_workouts_started_at ON workouts(started_at);
```

The interview rule: if the prompt says "design a data
warehouse," default to a *dimensional* (star) schema at
Level 4, not a normalized 3NF at Level 3. If the prompt
says "design a transactional database for an app," Level
3 is fine, and you should still mention the indexing
strategy.

---

## Level 4 — Dimensional schema (star)

The star schema is the diagram for analytics. It
re-packages the logical schema into a fact table
surrounded by flat dimension tables.

```
                ┌──────────────┐
                │ dim_users    │
                │ (SCD 2)      │
                └──────┬───────┘
                       │ user_key
                       ▼
┌──────────┐    ┌──────────────┐    ┌──────────┐
│ dim_date │◄───┤fact_workouts ├───►│dim_devices│
│          │    │              │    └──────────┘
└──────────┘    │ measures:    │
                │  duration    │    ┌──────────────┐
                │  calories    │◄───┤dim_workout_  │
                │  avg_hr      │    │  type        │
                └──────────────┘    └──────────────┘
```

The star schema is the right diagram for a *data
modeling* interview, because it forces you to commit to:

1. The **grain** of the fact (one row per what?).
2. The **measures** (numeric, additive).
3. The **dimensions** (descriptive, slowly changing).
4. The **SCD strategy** for each dim (1, 2, or 3).

We cover all of this in Lessons 16–20. The point of this
lesson is: the dimensional diagram is one of five
diagrams, and you choose it when the prompt is about
analytics.

---

## When to use which diagram

The five diagrams are not interchangeable. The
interviewer is checking which one you reach for.

| Interviewer says… | You reach for… |
|---|---|
| "Design the data model" | **ER diagram** (Chen or crow's foot). |
| "Show me the schema" | **Logical schema** (tables + columns, no types). |
| "Write the DDL" | **Physical schema** (SQL). |
| "Design a data warehouse" | **Dimensional schema** (star). |
| "How would you index this?" | **Physical schema** with indexes. |
| "Walk me through a query" | **Dimensional schema** with a SQL join. |

The candidate who can flip between these in 30 seconds
is the senior one. The candidate who picks the wrong
diagram and sticks with it for 20 minutes is not.

---

## How to draw fast

The candidate who draws slowly loses the round to the
one who draws fast and *narrates* as they go. The
mechanics:

1. **Boxes first.** Draw the entities as boxes. Don't
   write attributes yet.
2. **Connect them.** Draw the lines between boxes. Add
   the cardinality markers (`1`, `*`, `||--o{`).
3. **Label the verbs.** Each line gets a verb — "has",
   "does", "contains". The verb tells the interviewer
   what the relationship means.
4. **Talk while you draw.** "I'm putting users on the
   left because they're the most important entity. A
   user has many workouts, a workout has many exercises
   via this bridge table…"

The drawing takes 3–5 minutes. The narration is what
makes the candidate senior.

---

## Common ER mistakes

### Mistake 1 — Wrong cardinality

> "A workout has one user." (Many-to-one from workout
> to user.)

This is correct, but a candidate who says "a user has
one workout" is wrong. The cardinality must be stated
from the right entity. The convention is to read it
both ways and confirm.

### Mistake 2 — Missing bridge

> "A workout has many exercises."

This is half the many-to-many. The other half is "an
exercise is in many workouts." If the candidate doesn't
add the second clause, they've missed the bridge table.
The interviewer will catch it; better to catch it
yourself.

### Mistake 3 — Adding attributes to the ER

> "User has columns id, name, email, country,
> signup_date…"

The ER is not the schema. Attributes go in the DDL. The
candidate who lists attributes on the ER is wasting the
whiteboard. Boxes and arrows only.

### Mistake 4 — Inventing entities

> "We need a `workout_session` table distinct from
> `workout`."

Unless the product actually distinguishes sessions
from workouts, this is a phantom entity. If the
interviewer doesn't mention sessions, don't invent
them. If they do, ask which is the canonical concept.

### Mistake 5 — Drawing the wrong diagram for the prompt

> (For an analytics prompt) "Let me draw the normalized
> 3NF schema with foreign keys…"

The candidate has misread the prompt. Analytics prompts
want a star. OLTP prompts want 3NF. Drawing the wrong
one costs the round.

---

## Try it

Pick any of the canonical modeling questions. Draw the
**ER diagram** in Chen's notation, then translate it to
a **logical schema**, then to a **physical DDL**, then
to a **star schema**. Time yourself: 5 minutes per
diagram. By the end you should have four views of the
same model, and you should be able to flip between
them in seconds.

When you can hit 5 minutes for a prompt you've never
seen, your diagram muscle is built. Move to Lesson 14.

---

## In the interview, you would say...

> "I always start with the ER — boxes and arrows, no
> attributes — to commit to entities and cardinalities.
> Then I translate to a logical schema (tables and
> columns, no types) to commit to structure. For a data
> warehouse prompt, I skip the 3NF physical and go
> straight to a star — fact table at the right grain,
> flat dimensions around it. The five levels aren't
> different diagrams of the same model; they're five
> different conversations with the interviewer, and I
> pick the one that matches the prompt."

*Author: Prem Vishnoi <pvishnoi@avilx.com>*
