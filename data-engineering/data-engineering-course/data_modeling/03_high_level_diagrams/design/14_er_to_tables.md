# Lesson 14 — From ER to Tables (the translation rules)

> **What you'll learn:** the five mechanical rules that turn an ER
> diagram into a relational schema. By the end of this lesson
> you'll be able to translate any ER to a set of tables in your
> head.

---

## The five rules

Once the ER is right, the translation is mechanical. There are
exactly five rules:

1. **Each entity becomes a table.** Add a primary key.
2. **Each 1-to-many relationship becomes a foreign key on the
   "many" side.**
3. **Each many-to-many relationship becomes a bridge (junction)
   table with two foreign keys.**
4. **Each multi-valued attribute becomes its own table.**
5. **Derived attributes are not stored; they are computed at
   query time.**

That's it. Five rules. Memorize them, and you can translate any
ER to a schema in your head.

The Python in [`code/er_to_tables.py`](../code/er_to_tables.py)
implements these rules as functions. The `translate_er` function
takes a list of entities and relationships and returns a set of
table specs. It is the same algorithm a database textbook
teaches, just with the syntax stripped out.

---

## Rule 1 — Entity to table

```
User ───────────────► users(id PRIMARY KEY, name, email, …)
```

Pick a primary key. If the entity has a natural unique
identifier (SSN, email, ISBN), use that. Otherwise, add a
synthetic `id` column. Synthetic ids are the default in
warehouses.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL
);
```

---

## Rule 2 — 1-to-many to foreign key

```
User 1───────* Order
                    │
                    ▼
            orders(id, user_id, …)
            FOREIGN KEY (user_id) REFERENCES users(id)
```

The "many" side holds the foreign key. Always.

```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

The cardinality is preserved in the data: a user can have many
rows in `orders`; each order has exactly one user (because
`user_id` is a single column, not a list).

---

## Rule 3 — Many-to-many to bridge table

```
Workout *───────────* Exercise
                 │
                 ▼
        workout_exercises(
            workout_id,
            exercise_id,
            reps,            ← measures on the relationship
            weight_kg,
            PRIMARY KEY (workout_id, exercise_id)
        )
```

The bridge table has:

- A composite primary key (the two FKs).
- Optionally, *measures on the relationship* — `reps`, `weight`,
  `sets`. These are the measures you couldn't store on either
  side alone.

```sql
CREATE TABLE workout_exercises (
    workout_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    reps INTEGER,
    weight_kg REAL,
    PRIMARY KEY (workout_id, exercise_id),
    FOREIGN KEY (workout_id) REFERENCES workouts(id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);
```

---

## Rule 4 — Multi-valued attribute to its own table

```
User (id, name, ..., phone_numbers)
                    │
                    ▼
        user_phones(user_id, phone_number)
        PRIMARY KEY (user_id, phone_number)
```

A "multi-valued attribute" is one that has multiple values per
row. E.g., a user has many phone numbers, a product has many
images, an event has many tags.

The rule: pull the multi-valued attribute out of the entity
into its own table, with the entity's PK as a foreign key.

```sql
CREATE TABLE user_phones (
    user_id INTEGER NOT NULL,
    phone_number TEXT NOT NULL,
    PRIMARY KEY (user_id, phone_number),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

This is the same shape as a many-to-many bridge — and in fact
it is one. The "entity" on the right side is the phone number
(or image, or tag), and the cardinality is many-to-many.

In modern warehouses you often *don't* do this. You use a
JSON array or a `LIST` column instead. But the rule still
applies if you want a normalized schema.

---

## Rule 5 — Derived attributes are not stored

A **derived attribute** is one whose value can be computed
from other attributes. E.g.:

- `lifetime_revenue` = SUM of all `revenue` in the fact table.
- `user_age` = NOW() − `birth_date` (well, this is also a
  derived attribute, but you can store the snapshot).
- `num_orders` = COUNT from `fact_orders`.

The rule: don't store these. Compute them at query time.
Storing them creates a synchronization problem — they go stale
whenever the underlying events change.

The exception: if the derivation is expensive and the query is
hot, you can store a *materialized* version and refresh it on a
schedule. This is a materialized view, not a column on the
entity.

---

## Worked translation — fitness app

ER (from Lesson 13):

- Entities: User, Workout, Exercise, WorkoutType, Device, Sets
  (bridge).
- Relationships:
  - User 1—* Workout
  - Workout *—1 WorkoutType
  - Workout *—* Exercise (via Sets)
  - Workout *—1 Device
  - User 1—* Device

Apply the five rules:

```sql
-- Rule 1: entities to tables
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    fitness_level TEXT,
    signup_date TEXT
);

CREATE TABLE workouts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    workout_type_id INTEGER NOT NULL,
    device_id INTEGER,
    started_at TEXT,
    duration_minutes INTEGER,
    calories_burned INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (workout_type_id) REFERENCES workout_types(id),
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

CREATE TABLE workout_types (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE exercises (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    muscle_group TEXT
);

CREATE TABLE devices (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    device_type TEXT,
    os_version TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Rule 3: many-to-many to bridge
CREATE TABLE workout_exercises (
    workout_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    reps INTEGER,
    weight_kg REAL,
    sets INTEGER,
    PRIMARY KEY (workout_id, exercise_id),
    FOREIGN KEY (workout_id) REFERENCES workouts(id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);
```

The five rules produced the schema. No design decisions in
the translation — only mechanical steps.

---

## What can go wrong

### Wrong — N:M encoded as 1:N

If you encode a many-to-many as a single foreign key, you can
only have one "many" per "one" — which loses data. The bridge
table is non-negotiable for M:N.

### Wrong — derived attribute stored

`num_orders` on the `users` table. The day a user makes an
order, the column is wrong. Always compute.

### Right but verbose — bridge with measures

A bridge table can have measures (`reps`, `weight_kg`). This
is correct and common. Don't be afraid to add measures — they
go in the bridge because the bridge is the fact, in dimensional
modeling terms.

### Right but slow — too many joins

A 1-to-many relationship with a *deep* chain (A → B → C → D →
E) requires 4 joins to query. If you find yourself doing this,
consider denormalizing. But that's a *physical* optimization,
not an ER issue — fix it in the schema, not the ER.

---

## The ER-to-table checklist

Before you draw the schema from an ER, run through:

1. Every entity has a primary key (synthetic `id` if no
   natural one).
2. Every 1-to-many has the FK on the "many" side.
3. Every M:N has a bridge table.
4. Every multi-valued attribute is either pulled out, or
   justified (JSON column, array, etc.).
5. No derived attributes are stored.

This is the 30-second mental check. If you can run through it
in 30 seconds, you're ready for Lesson 15 (star vs snowflake).

---

## Try it

Take the ER you drew for the e-commerce prompt (Lesson 07's
worked example). Apply the five rules. Write the DDL. Time
yourself: 5 minutes.

Compare your output to the worked `build_ecommerce_schema`
in `code/star_schemas.py` (Lesson 16). The schemas should
match in shape if not in detail.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
