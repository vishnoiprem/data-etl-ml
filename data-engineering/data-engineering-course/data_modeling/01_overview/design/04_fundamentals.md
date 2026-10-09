# Lesson 04 — Data Modeling Fundamentals

> **What you'll learn:** the four vocabulary distinctions that show
> up in every data modeling conversation — fact vs dimension, grain,
> ER vs dimensional, and OLTP vs OLAP. By the end of this lesson
> you'll be able to explain each one in a sentence and pick the
> right one in a schema.

---

## The four distinctions

This lesson is a reference. The four distinctions below appear in
every data modeling interview; if you don't have them sharp, the
rest of the track will read like noise.

1. **Fact vs dimension**
2. **Grain**
3. **ER (entity-relationship) vs dimensional (star/snowflake)**
4. **OLTP vs OLAP**

We'll cover each one and end with a worked example that uses all
four.

---

## 1. Fact vs dimension

A **fact** is a measurement. It is a numeric value (or a count, or
a flag) tied to a specific event at a specific time. Examples:
`revenue`, `quantity_sold`, `workout_duration_minutes`,
`clicks`.

A **dimension** is the *context* for the fact. It tells you *who*,
*what*, *where*, *when*, *how*. Examples: `user`, `product`,
`date`, `device`, `country`.

The fact-dim split is the foundation of Kimball-style dimensional
modeling. The rule of thumb: if it's a number you aggregate
(`SUM`, `COUNT`, `AVG`), it's a fact measure. If it's a label you
filter or group by, it's a dimension attribute.

A common interview trap: a candidate calls `user_age` a "fact" and
gets marked down. Age is a dimension attribute (it doesn't change
on every event). The fact is the *event* — the user did X at
time Y in country Z.

### Why the split exists

- **Storage** — fact tables are tall and narrow (millions of rows,
  ~10–30 columns). Dimension tables are short and wide (thousands
  of rows, hundreds of columns).
- **Indexing** — fact tables are indexed on the dimension keys, not
  on the measures (we never query for "all workouts with
  duration > 60" without also filtering by user or date).
- **Updating** — fact tables are append-only. Dimension tables
  change (slowly). The SCD machinery (Lesson 21) exists to handle
  the asymmetry.

---

## 2. Grain

The **grain** of a fact table is *what one row represents*. It is
the single most important decision in dimensional modeling. Get it
right and the rest follows; get it wrong and nothing else works.

Examples of grain statements:

- "One row per order line item."
- "One row per workout session."
- "One row per user-day."
- "One row per page view."

The grain must be:

- **Specific** — "transaction data" is not a grain. "One row per
  completed checkout" is.
- **Stated** — write it on the whiteboard, in the comment of the
  CREATE TABLE, in the README. Always.
- **Consistent** — every measure in the fact table must be a
  sensible aggregation *at* that grain. `total` at the order-line
  grain; `lifetime_value` is not — it's a derived metric.

### Common grain traps

- **Mixing grains** — putting both `session_duration` and
  `lifetime_session_count` in the same table. Pick one grain;
  compute the other on top.
- **Grain drift** — the fact table quietly becomes "one row per
  (user, day)" instead of "one row per workout session" because
  someone added a `user-day` aggregate column. Once that happens,
  the table is no longer a fact table — it's a snapshot.
- **Unstated grain** — the most common failure mode in interviews.
  The candidate draws `fact_events` with `user_id`, `event_type`,
  `ts`, `properties` and never says what one row is. The
  interviewer has to guess.

### How to choose the grain

Ask: "What is the *smallest* unit at which we still care?" If
you're building an e-commerce warehouse and the analytics team
wants to know "what's the most popular product on Monday?", the
smallest unit is one order line item, not one order (because an
order can have multiple line items) and not one product-day (too
coarse).

When in doubt, **go finer**. A row at the finer grain can always
be aggregated up. A row at the coarser grain cannot be split
down.

---

## 3. ER (entity-relationship) vs dimensional (star / snowflake)

These are two different ways of representing a domain. They are
*not* in opposition — they live at different stages of the
modeling process.

| | ER | Dimensional |
|---|---|---|
| Stage | Conceptual / logical | Physical |
| Purpose | Map the entities and relationships | Drive query performance |
| Notation | Chen's, Crow's foot, Mermaid `erDiagram` | Star schema (fact + dim) |
| Audience | Engineers, PMs, designers | Analysts, data scientists |
| Output | Diagram | DDL |

The modeling process is:

1. **Conceptual (ER)** — what are the entities, and how do they
   relate? (Users, Orders, Products, OrderItems.)
2. **Logical (relational)** — what are the tables, and what are the
   keys? (Normalization rules from 3NF / BCNF.)
3. **Physical (dimensional)** — how do we lay out the tables for
   the warehouse? (Star schema: one wide fact table, several
   short dim tables.)

The mistake candidates make: they skip the conceptual stage and
go straight to the physical. They draw the star schema, but
they've missed entities (no Devices, no Sessions) because they
never enumerated the entities in the first place.

### Star vs snowflake

- **Star** — the dimension tables are flat (denormalized). A
  `dim_product` table has columns for category, subcategory, and
  brand, even though brand could be a separate table. This is
  the default for warehouses.
- **Snowflake** — the dimension tables are normalized. A
  `dim_product` table has a `brand_id` column that joins to a
  `dim_brand` table.

Star is faster (fewer joins), simpler (one place to look), and
easier for analysts. Snowflake saves space (smaller dim tables,
fewer redundant values) but adds joins. For warehouses, **star
wins 95% of the time**. The only place snowflake is right is when
a dimension has millions of distinct values and changes
constantly (e.g., a geographic hierarchy that updates monthly).

---

## 4. OLTP vs OLAP

**OLTP** (online transaction processing) is the system of record.
It is the database behind your app: every time a user creates an
order, posts a status, or refreshes a feed, an OLTP write happens.
Examples: PostgreSQL, MySQL, the user's primary database.

**OLAP** (online analytical processing) is the system of analysis.
It is the warehouse: every time a data scientist runs a cohort
query or an analyst refreshes a dashboard, an OLAP read happens.
Examples: Snowflake, BigQuery, Redshift, ClickHouse.

The differences drive the modeling choices:

| | OLTP | OLAP |
|---|---|---|
| Workload | Many small reads/writes | Few large reads, bulk loads |
| Schema | 3NF normalized | Star schema denormalized |
| Indexes | Many (per-query) | Few (per-fact-table) |
| Rows | Millions | Billions |
| Latency target | Sub-100ms per query | Seconds to minutes for big scans |
| Source of truth? | Yes (typically) | No — derived from OLTP |

The data modeling interview is, almost always, an OLAP modeling
question. The interviewer wants to know: can you design a star
schema for the warehouse? Even when the prompt is for an OLTP
system ("design a schema for a hospital patient records
system"), the same modeling primitives apply, with a stronger
emphasis on normalization and referential integrity.

### The pipeline (for context)

OLTP and OLAP coexist. The pipeline between them looks like:

```
OLTP DB  →  CDC / batch extract  →  staging (raw)
        →  transform / clean  →  warehouse (star schema)
        →  serve (BI tool, notebook, ML feature store)
```

This is what the `data_pipeline_design/` track is about. For data
modeling, the only thing that matters is: the OLAP schema is the
*consumer-facing* one. That's the one you're designing in the
interview.

---

## Worked example — fitness app

Let's put all four together.

> "Design a data warehouse for a fitness app so the analytics team
> can report on monthly engagement."

**Fact vs dimension:**
- Fact: `fact_workouts` — measures are `duration_minutes`,
  `calories_burned`, `sets_completed`.
- Dimensions: `dim_users` (SCD 2), `dim_workout_types`,
  `dim_exercises`, `dim_date`.

**Grain:** one row per workout session. Stated out loud, written
on the whiteboard, comment in the CREATE TABLE.

**ER vs dimensional:**
- ER (conceptual): Users, Workouts, Exercises, WorkoutTypes,
  Devices. Users have many Workouts; Workouts have many
  Exercises (many-to-many via Sets).
- Dimensional (physical): the star above. Snowflake only if
  WorkoutTypes has millions of distinct values; not in this
  case.

**OLTP vs OLAP:**
- The fitness app itself (the mobile/web product) is OLTP —
  the user logs in, starts a workout, etc. PostgreSQL or
  similar.
- The warehouse we just designed is OLAP — the analytics team
  queries it. Star schema, slow-changing dimensions, fact
  tables partitioned by date.

That's the four distinctions in one example. Every data modeling
question is a permutation of these four decisions.

---

## Try it

For each canonical question in
[`docs/reference/de_interview_canonical_questions.md`](../../../docs/reference/de_interview_canonical_questions.md#data-modeling-questions):

1. Name the grain of the main fact table.
2. List 2–3 measures and 2–3 dimensions.
3. State whether you'd model it as OLTP, OLAP, or both.
4. State whether the main fact is a transactional, snapshot, or
   accumulating fact (we'll cover these in Module 05, but take
   a guess first).

This exercise takes 5 minutes per question. The whole list
should take 30 minutes.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
