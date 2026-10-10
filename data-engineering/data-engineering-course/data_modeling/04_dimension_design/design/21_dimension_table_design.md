# Dimension Table Design

## Why this lesson

A dimension table is the *context* for a fact. The fact tells you what happened; the dim tells you who, what, where, when, how. If the dim is wrong, every join to it is wrong, every filter on it is wrong, and every aggregation through it is wrong. This lesson is the foundational anatomy of a dimension table: its purpose, its primary key, its natural key, its slowly-changing behavior flag, its wide-and-denormalized rule, and the 7 components of a good dim. By the end, you should be able to design a `dim_customer` from scratch and explain every column in under 2 minutes — the entry ticket for the rest of Module 04.

---

## What a dimension table is

A *dimension table* (or simply *dim*) is the table that holds
the descriptive context for a fact event. If a fact row says
"Alice bought a laptop on March 15," the dim is what tells
you who Alice is, what a laptop is, and what March 15 means.

Three properties distinguish a dim from a fact:

1. **Dimensional** — it describes *who, what, where, when,
   how*. Its columns are attributes (strings, dates, flags,
   categorical enums), not measures.
2. **Slowly changing** — its rows are stable; they change
   rarely compared to fact events. A user changes country
   every 3 years; a product gets re-categorized every
   quarter. The fact stream is 10M events/day; the dim
   changes 100 rows/day.
3. **Wide and denormalized** — a dim typically has 20–200
   columns, all flattened into one row per entity. We do
   *not* normalize dims into many sub-tables. (Snowflake
   schemas do, but Kimball star schemas — the interview
   default — do not.)

The interview definition: "a dim is the descriptive context
for a fact. It's wide, denormalized, and slowly changing,
joined to the fact on a surrogate key."

---

## Dimension vs fact — the contrast

| Property | Dimension | Fact |
|---|---|---|
| **Role** | Describes the context. | Records the event. |
| **Columns** | Attributes (strings, dates, flags). | Measures (numeric, additive). |
| **Grain** | One row per entity (customer, product). | One row per event (order, click). |
| **Cardinality** | 100k–100M rows. | 10M–100B rows. |
| **Change rate** | Slow (rare updates). | Append-only, fast. |
| **Joins** | Joined *to* (from the fact). | Joined *from*. |
| **Cardinality of FK** | The "1" side of 1-to-many. | The "many" side. |

The senior candidate narrates this contrast in 30 seconds:
"A dim is the 'who' and the 'where.' A fact is the 'what
happened' and 'how much.' The fact has the measures; the
dim has the attributes."

---

## The 7 components of a good dimension table

Every well-designed dim has these 7 components. Omit any
one and the dim will hurt you in production.

### 1. Surrogate primary key (PK)

A *surrogate key* is a synthetic integer (or UUID) that
uniquely identifies a row in the dim. It is *not* the
natural key from the source system.

```sql
customer_key BIGINT  PRIMARY KEY  -- surrogate
customer_id  VARCHAR NOT NULL     -- natural key from source
```

**Why a separate surrogate key?** Two reasons:

- **Source keys change.** A customer ID might be reissued,
  reformatted, or merged. The dim needs an immutable
  identity that doesn't change when the source changes.
- **SCD 2 requires it.** When a customer changes
  attributes, you expire the old row and insert a new
  one. The natural key (`customer_id`) has many rows; the
  surrogate key (`customer_key`) has one row each. The
  fact joins on the surrogate, so the fact is bound to a
  *specific version* of the customer, not the customer
  in general.

The interview rule: "the fact joins to the dim on the
surrogate key, never the natural key."

### 2. Natural key (NK)

The *natural key* is the business identifier from the source
system. It is *not* the PK; it is a column with a unique
index (or unique constraint in the source system).

```sql
customer_id VARCHAR NOT NULL  UNIQUE
```

The natural key is what the application uses; the surrogate
key is what the warehouse uses. The dim is the translation
table between the two.

### 3. Attributes (the descriptive columns)

The attributes are the reason the dim exists. For
`dim_customer`:

- `first_name`, `last_name`
- `email`
- `phone`
- `country`, `state`, `city`
- `signup_date`
- `acquisition_channel`
- `lifetime_value_tier` (computed)
- `is_active` (flag)
- … (20–200 columns is normal)

The wide-and-denormalized rule: keep all these in one
row, not normalized across many sub-tables. The interview
default is a Kimball star schema with wide flat dims.

### 4. Slowly-changing behavior flag

The dim declares *how* it changes over time. The choices
are SCD 1, SCD 2, SCD 3, SCD 4, SCD 6. The default in
interview answers is **SCD 2** unless the candidate has a
reason to override.

The SCD flag is sometimes a column (`scd_type = 2`), more
often a *meta fact about the table* documented in the data
dictionary. Either way, the dim knows how it changes.

```sql
-- SCD 2 columns
effective_date  DATE  NOT NULL
expiry_date     DATE  NOT NULL  DEFAULT '9999-12-31'
is_current      BOOLEAN NOT NULL DEFAULT TRUE
```

### 5. Audit columns

Every dim should have audit metadata:

- `created_at` — when this row was first inserted.
- `created_by` — which process / user / pipeline.
- `updated_at` — when this row was last modified.
- `updated_by` — same.
- `source_system` — which upstream system.
- `load_batch_id` — which ETL run.

These are *not* part of the user-facing schema. They're
operational metadata that lets the data team debug "when
did this row appear, and where did it come from?"

### 6. Surrogate-key generator

Every dim has a way to generate new surrogate keys. Most
warehouses use:

- **Identity / auto-increment** column (Snowflake
  `AUTOINCREMENT`, BigQuery `GENERATED BY DEFAULT AS
  IDENTITY`, Postgres `SERIAL`).
- **Sequence** with explicit `nextval()`.
- **Hash of the natural key** for some pipelines
  (deterministic, allows idempotent loads).

The interview cares less about which generator and more
that the candidate names one.

### 7. The "version pointer" (for SCD 2)

For SCD 2 dims, you need a way to identify the *current*
version of a row quickly. Two patterns:

- **`is_current` flag** — `is_current = 1` for the live
  version, 0 for expired.
- **`expiry_date = '9999-12-31'`** — a sentinel value
  for the current version.

Most production dims use both. The `is_current` flag is
an index-friendly filter; the `9999-12-31` sentinel makes
the temporal join cleaner.

---

## The wide-and-denormalized rule

A dim is *wide*: 20–200 columns is normal. A dim is
*denormalized*: all the attributes are flattened into
one row, even if some are hierarchical (country → state →
city).

Why denormalize? Three reasons:

1. **Query simplicity.** A single join from the fact
   gives the analyst every attribute. No 5-level
   snowflake join.
2. **Index friendliness.** A wide dim is a single
   contiguous read; a snowflake is 5+ random reads.
3. **Warehouse optimization.** Columnar warehouses
   (Snowflake, BigQuery, Redshift) compress wide denormalized
   dims extremely well because of the low cardinality of
   each column.

When to *split* into mini-dims (the exception to the
rule):

- **High-cardinality rapidly-changing subset.** If 5% of
  the dim's columns change every day for 80% of rows
  (e.g., session-level flags), split those out into a
  `dim_customer_session_flags` mini-dim. The main
  `dim_customer` is then narrower and more cache-friendly.
- **Hot subset isolation.** If a subset of dim columns
  is queried 100x more than the rest, isolate it into a
  "hot" mini-dim.
- **Role-playing dim.** If a dim plays two different roles
  on the same fact (e.g., `ship_from_address` vs
  `ship_to_address`), each role gets its own
  role-playing dim view or its own denormalized copy of
  the relevant subset.

The interview signal: name the rule, name the exceptions.
The senior candidate says "wide and denormalized by
default; split into mini-dims only when the high-cardinality
rapidly-changing subset is a real query bottleneck."

---

## Role-playing dims — preview

A *role-playing dim* is one dim used in multiple roles
on the same fact. The classic example: `dim_date` as
`order_date`, `ship_date`, `delivery_date` on
`fact_orders`. The same physical dim is referenced three
times via three FKs on the fact, each with a different
role name.

The detailed treatment of role-playing dims is in
Lesson 23, but the foundational concept belongs here:
**a single logical dim can play multiple roles, and the
role is named on the fact's FK column**.

---

## Slowly-changing flag — preview

A dim's slowly-changing flag declares *how* the dim
changes. The default is SCD 2 (expire and insert, full
history). The detailed treatment — including Type 1
(overwrite, no history) and Type 3 (add a previous
column, one level of history) — is in Lesson 22.

The foundational concept: a dim must declare its
slowly-changing behavior, because the choice affects
the schema (extra columns), the joins (temporal joins
for Type 2), and the analyst's ability to reconstruct
history.

---

## Audit columns — preview

Audit columns (`created_at`, `updated_at`, `source_system`,
`load_batch_id`) are operational metadata, not part of
the user-facing model. They let the data team debug
"when did this row appear, where did it come from, and
which pipeline run wrote it." Every dim should have
them; the warehouse team will thank you.

---

## Worked example — `dim_customer`

Below is a complete `dim_customer` design, end-to-end. This
is the kind of design a senior candidate narrates in 2–3
minutes during an interview.

### The DDL

```sql
CREATE TABLE dim_customer (
    -- 1. Surrogate primary key
    customer_key      BIGINT  PRIMARY KEY,

    -- 2. Natural key (from source system)
    customer_id       VARCHAR NOT NULL UNIQUE,

    -- 3. Attributes (the descriptive context)
    first_name        VARCHAR,
    last_name         VARCHAR,
    email             VARCHAR,
    phone             VARCHAR,
    country           VARCHAR,
    state             VARCHAR,
    city              VARCHAR,
    signup_date       DATE,
    acquisition_channel VARCHAR,  -- 'organic', 'paid_search', etc.
    lifetime_value_tier VARCHAR,  -- 'platinum', 'gold', 'silver'
    is_active         BOOLEAN,

    -- 4. Slowly-changing behavior (SCD 2 columns)
    effective_date    DATE  NOT NULL,
    expiry_date       DATE  NOT NULL DEFAULT '9999-12-31',
    is_current        BOOLEAN NOT NULL DEFAULT TRUE,

    -- 5. Audit columns
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_system     VARCHAR,   -- 'salesforce', 'segment', etc.
    load_batch_id     BIGINT
);

-- Indexes for the common query patterns
CREATE INDEX idx_dim_customer_natural  ON dim_customer(customer_id);
CREATE INDEX idx_dim_customer_current  ON dim_customer(is_current)
    WHERE is_current = TRUE;  -- partial index for the hot path
CREATE INDEX idx_dim_customer_country ON dim_customer(country)
    WHERE is_current = TRUE;
```

### The anatomy, walked through

- **`customer_key`** — surrogate PK. Generated by
  `nextval(dim_customer_seq)`. The fact joins here.
- **`customer_id`** — natural key from Salesforce. Unique
  but not the PK. The dim is the translation table
  between source and warehouse.
- **Attributes** — name, email, country, signup date, etc.
  Wide and denormalized. Country is here even though it
  could be a `dim_geography` (we chose denormalization
  for query simplicity).
- **SCD 2 columns** — `effective_date`, `expiry_date`,
  `is_current`. When a customer's country changes, the
  old row expires and a new row is inserted. The
  `is_current` partial index makes the "current view"
  query (`WHERE is_current = TRUE`) a fast index scan.
- **Audit columns** — `created_at`, `updated_at`,
  `source_system`, `load_batch_id`. Operational metadata.
- **Indexes** — partial index on `is_current = TRUE` for
  the hot path; index on `country` for the common filter.

### The whiteboard pattern

```
        dim_customer
   ┌─────────────────────┐
   │ customer_key (PK)   │  ◀── surrogate, sequential
   │ customer_id (NK)    │  ◀── from source
   │ first_name          │
   │ last_name           │
   │ email               │  ◀── wide, denormalized
   │ country             │
   │ state               │
   │ signup_date         │
   │ acq_channel         │
   │ ltv_tier            │
   │ is_active           │
   │ effective_date      │  ◀── SCD 2
   │ expiry_date         │
   │ is_current          │
   │ created_at          │  ◀── audit
   │ source_system       │
   └──────────┬──────────┘
              │ customer_key
              │ (FK, not customer_id)
              ▼
        fact_orders
```

Note: the fact joins on `customer_key` (the surrogate),
*not* on `customer_id` (the natural key). This is what
makes the temporal join work — the fact is bound to a
specific version of the customer.

---

## The "good dim" checklist

When you finish designing a dim, run this checklist:

- [ ] Has a surrogate PK distinct from the natural key.
- [ ] Has the natural key with a unique index.
- [ ] Has 20+ attributes that are wide and denormalized.
- [ ] Declares its SCD behavior (Type 2 by default).
- [ ] Has `effective_date`, `expiry_date`, `is_current` if SCD 2.
- [ ] Has audit columns (`created_at`, `updated_at`,
      `source_system`, `load_batch_id`).
- [ ] Has a partial index on `is_current = TRUE` for the hot
      path.
- [ ] Has indexes on the columns most commonly filtered
      (country, signup_date, etc.).
- [ ] The fact joins on the surrogate key, not the natural key.
- [ ] The dim is documented in the data dictionary with its
      SCD behavior, refresh cadence, and source system.

If you can tick all 10 boxes for `dim_customer`, you
understand dimension table design. Move to Lesson 22.

---

## Try it

For the `dim_customer` example, do the following:

1. Draw the DDL on a whiteboard.
2. Walk through the 7 components in order, naming each
   column.
3. Explain why the surrogate key is separate from the
   natural key.
4. Explain when this dim would be split into mini-dims
   (the exception to the wide-and-denormalized rule).
5. Time yourself: 5 minutes. The senior candidate hits
   this in under 5 minutes.

Then re-do the exercise for `dim_product` and
`dim_geography`. If you can hit 5 minutes per dim, the
foundational anatomy is at interview fluency.

---

## In the interview, you would say...

> "A dimension table is the descriptive context for a fact:
> wide, denormalized, slowly changing. It has 7 components:
> surrogate PK, natural key, attributes, SCD behavior flag,
> audit columns, surrogate-key generator, and (for SCD 2)
> a version pointer. The fact joins on the surrogate, never
> the natural key. The default is Kimball-style: one wide
> row per entity, all attributes flattened, with SCD 2
> columns for historical attribution."

---

*Author: Prem Vishnoi <prem.vishnoi@example.com>*
