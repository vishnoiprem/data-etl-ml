# Lesson 13 — Entity-Relationship Diagrams (ER)

> **What you'll learn:** Chen's notation for ER diagrams, the four
> cardinalities, and how to draw fast on a whiteboard. By the end of
> this lesson you'll be able to translate a product description into
> an ER diagram in under 5 minutes.

---

## What an ER diagram is for

An ER diagram is the *conceptual* model. It answers two questions:

1. What are the **entities** in the domain? (Users, Orders,
   Products, Workouts.)
2. How are the entities **related**? (A user has many orders; an
   order has many line items; a product is in many line items.)

The ER diagram is *not* the schema. It is the step before the
schema. It exists to make sure you don't miss an entity or get
the cardinalities wrong. Once the ER is right, the schema is a
mechanical translation (Lesson 14).

The mistake candidates make: skip the ER, go straight to the
schema. They end up with the wrong tables because they never
enumerated the entities.

---

## Chen's notation

The academic standard. Peter Chen invented it in 1976. It's still
the cleanest way to draw an ER on a whiteboard.

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
- **Lines** connect them. The cardinality is written at the
  endpoints (`1`, `N`, `M`).

You don't need to draw every attribute on the whiteboard. You
need to draw every entity and every relationship, with the
cardinalities. The attributes go in the DDL.

---

## Crow's foot notation

The industry default. Used by most diagramming tools
(Lucidchart, dbdiagram.io, Mermaid). Looks like a crow's foot at
the "many" end.

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

Crow's foot is faster to draw than Chen's. Use it if you're
comfortable; the diagram is the same, the notation differs.

---

## The four cardinalities

There are exactly four cardinalities. Memorize them.

| Cardinality | Reads as | Example |
|---|---|---|
| 1-to-1 | "each A has exactly one B" | A user has one profile. |
| 1-to-many | "each A has many Bs" | A user has many orders. |
| Many-to-1 | "each B has one A" | (inverse of 1-to-many) |
| Many-to-many | "each A has many Bs and vice versa" | A workout has many exercises; an exercise appears in many workouts. |

The interview rule: **always state the cardinality, never let
the interviewer guess.** A user with "many" workouts and a
workout with "many" users (many-to-many) is a different schema
than a user with "many" workouts and a workout with "one" user
(one-to-many). The candidate who doesn't say the cardinality
out loud has not committed to either.

---

## Worked ER — fitness app

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

Entities: Users, Workouts, Exercises, WorkoutTypes, Devices, Sets
(bridge).
Relationships:
- A user has many workouts (1-to-many).
- A workout has one workout type (many-to-1).
- A workout has many exercises, and an exercise is in many
  workouts (many-to-many, via Sets).
- A workout was done on one device (many-to-1).
- A user has many devices (1-to-many).

This is a complete ER. The candidate has named every entity,
every relationship, and every cardinality. The schema is a
mechanical translation (Lesson 14) — but the ER was where the
thinking happened.

---

## How to draw fast

The candidate who draws slowly loses the round to the one who
draws fast and *narrates* as they go. The mechanics:

1. **Boxes first.** Draw the entities as boxes. Don't write
   attributes yet.
2. **Connect them.** Draw the lines between boxes. Add the
   cardinality markers (`1`, `*`, `||--o{`).
3. **Label the verbs.** Each line gets a verb — "has", "does",
   "contains". The verb tells the interviewer what the
   relationship means.
4. **Talk while you draw.** "I'm putting users on the left
   because they're the most important entity. A user has many
   workouts, a workout has many exercises via this bridge
   table…"

The drawing takes 3–5 minutes. The narration is what makes the
candidate senior.

---

## Common ER mistakes

### Mistake 1 — Wrong cardinality

> "A workout has one user." (Many-to-one from workout to user.)

This is correct, but a candidate who says "a user has one
workout" is wrong. The cardinality must be stated from the
right entity. The convention is to read it both ways and
confirm.

### Mistake 2 — Missing bridge

> "A workout has many exercises."

This is half the many-to-many. The other half is "an exercise
is in many workouts." If the candidate doesn't add the second
clause, they've missed the bridge table. The interviewer will
catch it; better to catch it yourself.

### Mistake 3 — Adding attributes to the ER

> "User has columns id, name, email, country, signup_date…"

The ER is not the schema. Attributes go in the DDL. The
candidate who lists attributes on the ER is wasting the
whiteboard. Boxes and arrows only.

### Mistake 4 — Inventing entities

> "We need a `workout_session` table distinct from `workout`."

Unless the product actually distinguishes sessions from
workouts, this is a phantom entity. If the interviewer doesn't
mention sessions, don't invent them. If they do, ask which is
the canonical concept.

---

## Try it

Pick any of the canonical modeling questions. Draw the ER
diagram in Chen's notation. Time yourself: 5 minutes. The
diagram should have 4–7 entities and 5–10 relationships.

When you can hit 5 minutes for a prompt you've never seen, your
ER muscle is built. Move to Lesson 14.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
