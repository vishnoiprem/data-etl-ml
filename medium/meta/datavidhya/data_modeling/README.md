# Data Modeling — Medium Interview Track

A focused, opinionated module for data engineers preparing for medium-difficulty schema design interviews. Think **Meta, LinkedIn, Airbnb, Google Ads, Stripe**. Not beginner. Not staff+. Solid senior-IC territory.

This module covers two complementary halves:

1. **OLTP relational design** — normalised schemas for transactional systems (notification platforms, social graphs, product catalogues).
2. **OLAP dimensional design** — star schemas for analytics warehouses (funnels, ad platforms, engagement metrics).

You will not become a Kimball Group apologist here. You will learn to **pick the right tool**, defend the choice in an interview, and ship SQL that runs on PostgreSQL 14+.

---

## Mental model: OLTP vs OLAP vs Star vs Snowflake

| Property                  | OLTP (3NF)                       | OLAP Star Schema                | Snowflake                       |
| ------------------------- | -------------------------------- | ------------------------------- | ------------------------------- |
| Optimised for             | Writes, single-row reads         | Aggregations, scans             | Storage savings, drill-down     |
| Normalisation             | 3NF / BCNF                       | Denormalised dimensions         | Partially normalised dimensions |
| Cardinality per table     | Many narrow tables               | Few wide tables                 | Mixed                           |
| Query style               | Point lookups, FK joins          | Star joins (1 fact + N dims)    | Multi-hop joins                 |
| Storage cost              | Low redundancy                   | Higher redundancy (precomputed) | Medium                          |
| ETL pattern               | Application writes               | Batch / streaming load          | Batch load                      |
| Example systems           | Notification service, social DB  | Funnel warehouse, ad analytics  | Large dims (geo, product hier.) |

**One-line rule of thumb:**
- If users are **writing rows** one at a time → 3NF (OLTP).
- If analysts are **scanning billions of rows** to answer business questions → star schema (OLAP).
- Snowflake only when a dimension is huge and rarely queried at leaf level (e.g. a 50M-row product hierarchy).

---

## Quick decision flow

```
Start
  │
  ├─ "Is this a transactional app with concurrent writes?"
  │     YES → OLTP, normalise to 3NF, surrogate keys, FK indexes
  │     NO  ↓
  │
  ├─ "Are we aggregating historical events for analytics?"
  │     YES → Star schema
  │     NO  ↓
  │
  └─ "Mixed workload (transactional + reporting)?"
        YES → Dual-write or CDC pipeline: 3NF source → star schema mart
```

**Never put a star schema behind a transactional application.** The denormalisation destroys write throughput and creates update anomalies.

---

## 2-week study plan

| Day   | Focus                                                         | Deliverable                              |
| ----- | ------------------------------------------------------------- | ---------------------------------------- |
| 1     | OLTP fundamentals (NF1–5, keys, constraints)                  | Read `01_oltp_fundamentals.md`           |
| 2     | Notification schema (event + scheduled)                      | Run `02_oltp_notification_system.sql`    |
| 3     | Social media schema (graph edges, engagement)                 | Run `03_oltp_social_media.sql`           |
| 4     | Dimensional fundamentals (facts, dims, SCD)                   | Read `04_dimensional_fundamentals.md`    |
| 5     | Product funnel star schema                                    | Run `05_star_product_funnel.sql`         |
| 6     | Ad platform schema (3 fact tables, late data)                 | Run `06_star_ad_platform.sql`            |
| 7     | Notification analytics (conformed dims)                       | Run `07_star_notification_analytics.sql` |
| 8     | Schema diagrams (visual review)                               | Read `08_schema_diagrams.md`             |
| 9–10  | Interview walkthroughs (verbal practice)                      | Read `09_interview_walkthroughs.md`      |
| 11–13 | Practice queries (30 problems, 6 per schema)                  | Solve `10_practice_queries.sql`          |
| 14    | Mock interview (timer, whiteboard, talk aloud)                | Record yourself, review                  |

Daily time commitment: **90 minutes**. Half reading, half running SQL.

---

## Cheat sheet

### OLTP quick reference

- **Primary key**: prefer `BIGINT GENERATED ALWAYS AS IDENTITY` unless you have a strong natural key (e.g. ISO country code).
- **Foreign keys**: always create an index on the FK column. Always decide `ON DELETE` behaviour explicitly (`CASCADE`, `RESTRICT`, `SET NULL`).
- **Soft delete**: `deleted_at TIMESTAMPTZ NULL`. Never hard-delete user-visible rows.
- **Audit columns**: `created_at`, `updated_at`, `created_by`. Default `now()`.
- **JSONB**: fine for sparse attributes (settings, metadata). Not an excuse to skip modelling.
- **Many-to-many**: always a join table with composite PK `(left_id, right_id)`.

### Star schema quick reference

- **Fact grain**: one row = one measurable event. Document it in a comment above the `CREATE TABLE`.
- **Fact types**: transactional (events), periodic snapshot (daily aggregates), accumulating snapshot (lifecycle).
- **Dimension types**: conformed (shared across marts), role-playing (date plays multiple roles), junk (low-cardinality flags), degenerate (transaction ID), SCD (slowly changing).
- **SCD Type 2**: add `valid_from`, `valid_to`, `is_current` columns. Use a surrogate `dim_key`. Never overwrite.
- **Indexes**: fact tables need bitmap or zone-map indexes on low-cardinality dim keys. Postgres typically uses B-tree on the surrogate PK.
- **Late-arriving facts**: insert with `effective_date` from the event, not the load date. Dimension lookups may use the "as-of" date.
- **Avoid**: snowflaking for the sake of it, million-column facts, sub-second grain on large dims.

### Migration hygiene

- Use `BEGIN; ... COMMIT;` in production migrations.
- Never drop a column in the same migration as adding a new one. Two releases minimum.
- Always backfill before adding a `NOT NULL` constraint.

---

## Files in this module

| File                                  | Purpose                                                    |
| ------------------------------------- | ---------------------------------------------------------- |
| `README.md`                           | This file. Overview, study plan, cheat sheet.              |
| `01_oltp_fundamentals.md`             | Normalisation, keys, indexes, constraints.                 |
| `02_oltp_notification_system.sql`     | OLTP schema: multi-channel notification system.            |
| `03_oltp_social_media.sql`            | OLTP schema: social graph + engagement.                    |
| `04_dimensional_fundamentals.md`      | Facts, dimensions, SCD types, schema flavours.             |
| `05_star_product_funnel.sql`          | Star schema: e-commerce funnel analytics.                  |
| `06_star_ad_platform.sql`             | Star schema: ads clicks, impressions, conversions.         |
| `07_star_notification_analytics.sql`  | Star schema: notification engagement by channel/segment.   |
| `08_schema_diagrams.md`               | ASCII diagrams for all 5 problems.                         |
| `09_interview_walkthroughs.md`        | Elevator pitches, probing Qs, right/wrong answers.         |
| `10_practice_queries.sql`             | 30 practice problems (6 per schema) with hints + answers.  |
| `run_all.sql`                         | Master script — runs every `*.sql` in order.               |

---

## How to use this module

1. Read the README and the two fundamentals files end-to-end first.
2. For each SQL file: read the header comment, run it in `psql`, inspect the output, then run the example queries at the bottom.
3. Attempt the practice queries in `10_practice_queries.sql` **before** peeking at the solutions.
4. Use `09_interview_walkthroughs.md` to rehearse out loud. Saying it is the only way to find the gaps.
5. Whiteboard the diagrams from memory once a day for the first week.

---

## Design decisions worth flagging

These are the choices I made that you should question and form your own opinion on:

- **`notifications` vs `notification_deliveries` are split** in `02` so a single notification can fan out to email + push + SMS, each with independent state.
- **Three fact tables (impressions / clicks / conversions) instead of one** in `06` because impressions outnumber clicks 1000:1 — a single table would be 99.9% sparse.
- **SCD Type 2 on `dim_users`** in `05` because cohort analysis needs historical user segments.
- **Conformed `dim_date`** across all star schemas so cross-mart joins "just work".
- **Soft delete (`deleted_at`)** instead of `is_active` — keeps the row, makes audit trails trivial.
- **Composite PKs on join tables** (`post_hashtags`, `likes`) instead of surrogate keys — saves storage and enforces uniqueness.
- **No `users.email` UNIQUE** in some sample data inserts (to allow test data) — production schemas should have it.

If you disagree with any of these, that's good. The interview answer is always **why**, not what.
