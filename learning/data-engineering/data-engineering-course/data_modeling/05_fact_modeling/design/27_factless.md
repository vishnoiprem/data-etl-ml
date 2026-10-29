# Lesson 27 — Factless Fact Tables

> **What you'll learn:** the right fact-table type for
> "this happened" tracking — when there are no measures,
> just the existence of an event. By the end of this
> lesson you'll know when to use a factless fact and
> when to use a regular transactional fact.

---

## What a factless fact is

A factless fact table has one row per *event*, but the
event has *no numeric measures*. The fact exists to
record the occurrence of something.

The defining properties:

- **No measures.** The only columns are FKs to
  dimensions and possibly flags.
- **Existence is the measure.** The fact that a row
  exists *is* the data.
- **COUNT(*)** is the typical query.

The classic example is *attendance*: "user X attended
event Y on date Z." The fact has three FKs (user,
event, date) and no measures. The count of rows is the
attendance count.

---

## Three use cases

There are three patterns where a factless fact is the
right tool:

### Use case 1 — Attendance / participation

"User X attended event Y on date Z." The fact records
*who* showed up *where* *when*.

Examples:
- A student attended a class.
- An employee attended a meeting.
- A user attended a webinar.
- A customer attended a pop-up event.

### Use case 2 — Coverage / eligibility

"Store S had product P in stock on date D." The fact
records *what was available* *where* *when*.

Examples:
- A store had a product in inventory on a date.
- A customer was eligible for a promotion on a date.
- A user had a feature available on a date.
- A patient was covered by insurance on a date.

### Use case 3 — Many-to-many bridge

A factless fact can serve as a *bridge* between two
dimensions. The fact has only the two FKs and the date
when the relationship existed.

Examples:
- A student took a class (student ↔ class).
- A user is in a group (user ↔ group).
- A product is in a category (product ↔ category).

This is essentially the same as the bridge table from
the ER translation (Lesson 14), but with a date
dimension to make it time-aware.

---

## The grain

The grain of a factless fact is *one row per
occurrence of the event*. For an attendance fact, it's
one row per (user, event, date). For a coverage fact,
it's one row per (entity, item, date).

Like all facts, the grain is *stated out loud*. The
statement is often simpler than for transactional
facts because there are no measures to anchor the
grain.

---

## The columns

A factless fact has only:

- A **primary key** (synthetic).
- **Foreign keys** to the dimensions.
- Optionally, **flags** that describe the event (e.g.,
  `was_registered` for an attendance fact, where the
  flag distinguishes "registered but didn't attend"
  from "actually attended").

There are *no numeric measures*. This is the
defining property.

### Example: attendance

```sql
CREATE TABLE fact_attendance_factless (
    attendance_key INTEGER PRIMARY KEY,
    user_key       INTEGER NOT NULL,
    event_key      INTEGER NOT NULL,
    date_key       INTEGER NOT NULL,
    FOREIGN KEY (user_key)  REFERENCES dim_user(user_key),
    FOREIGN KEY (event_key) REFERENCES dim_event(event_key),
    FOREIGN KEY (date_key)  REFERENCES dim_date(date_key)
);
```

Four columns: PK + 3 FKs. No measures.

### Example: coverage

```sql
CREATE TABLE fact_coverage_factless (
    coverage_key   INTEGER PRIMARY KEY,
    store_key      INTEGER NOT NULL,
    product_key    INTEGER NOT NULL,
    date_key       INTEGER NOT NULL,
    in_stock       INTEGER NOT NULL DEFAULT 1,  -- a flag
    FOREIGN KEY (store_key)   REFERENCES dim_store(store_key),
    FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
    FOREIGN KEY (date_key)    REFERENCES dim_date(date_key)
);
```

The `in_stock` flag is a 0/1, not a measure. The
"measure" is the existence of the row.

---

## The "no measures" decision

The hardest call: when is a factless fact the right
shape, and when should you add a measure?

The rule:

- If the question is *purely existence* ("did X
  happen?") → factless.
- If the question has a *magnitude* ("how many
  times?", "how long?", "how much?") → add the
  measure, even if it's a count or duration.

Examples:

- "Did the user attend the webinar?" → factless.
- "How long did the user stay in the webinar?" → add
  `duration_minutes`.
- "Was the product in stock?" → factless.
- "How many units were in stock?" → add `units_on_hand`.

The factless pattern is the right choice when the
question is a yes/no. As soon as there's a magnitude,
add a measure.

---

## When to use

A factless fact is the right choice when:

- The event has *no inherent magnitude*.
- The question is *existence* ("did X happen?").
- The count of rows *is* the answer.

Attendance, eligibility, coverage, registration, many-
to-many bridges with a date — all factless.

## When *not* to use

- The event has a *magnitude* (use a regular
  transactional fact).
- The question is *state at end of period* (use a
  periodic snapshot).
- The event has a *lifecycle with milestones* (use an
  accumulating snapshot).

The trap: making a factless fact when a measure would
be useful. "User attended webinar" is factless; "user
attended webinar for 45 minutes" is not. If the
interviewer says "we want to know how long they
stayed," add a measure.

---

## The example: `fact_attendance_factless`

The schema in `code/fact_tables.py`:

```sql
CREATE TABLE fact_attendance_factless (
    attendance_key INTEGER PRIMARY KEY,
    user_key       INTEGER NOT NULL,
    event_key      INTEGER NOT NULL,
    date_key       INTEGER NOT NULL
);
```

Sample data (5 attendance records):

| attendance_key | user | event | date |
|---|---|---|---|
| 1 | Alice | Yoga | 2024-01-15 |
| 2 | Alice | Spin | 2024-01-16 |
| 3 | Bob | Yoga | 2024-01-15 |
| 4 | Bob | Pilates | 2024-01-17 |
| 5 | Carol | Spin | 2024-01-16 |

The "measure" is the existence of the row. The total
attendance is 5.

---

## Sample queries

### Attendance by event

```sql
SELECT
    e.event_name,
    COUNT(*) AS n_attendees
FROM fact_attendance_factless f
JOIN dim_event e ON f.event_key = e.event_key
GROUP BY e.event_name
ORDER BY n_attendees DESC;
```

### Daily attendance trend

```sql
SELECT
    d.date,
    COUNT(*) AS n_attendees
FROM fact_attendance_factless f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.date
ORDER BY d.date;
```

### Most-engaged users

```sql
SELECT
    u.name,
    COUNT(*) AS n_events
FROM fact_attendance_factless f
JOIN dim_user u ON f.user_key = u.user_key
GROUP BY u.name
ORDER BY n_events DESC
LIMIT 10;
```

---

## Tradeoffs to call out

1. **Why factless, not transactional?** "There's no
   magnitude to measure. The question is
   'did X attend?' not 'how long did X attend?'"
2. **Why is `in_stock` a flag and not a measure?**
   "The question is *availability* — was the
   product in stock or not? A 0/1 is the right
   shape. If we needed *how many units*, we'd add
   a measure."
3. **Why no `count` measure on the fact?** "We could
   add `count = 1` and use `SUM(count)`, but
   `COUNT(*)` is the same query without the column.
   The row's existence is the count."

---

## Try it

Open
[`code/fact_tables.py`](../code/fact_tables.py) and read
`build_factless_fact`. Then:

1. State the grain: "one row per (user, event,
   date) attendance."
2. Identify that there are no numeric measures
   (other than the PK and FKs).
3. Run the test:

```bash
python3 -m unittest data_modeling/05_fact_modeling/tests/test_facts.py
```

The test asserts that the factless fact has no
numeric measures (other than the PK and FKs) and
the sample data has 5 attendance records.

---

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
