# Lesson 14 — Evolving Models Based on Changing Requirements

> **What you'll learn:** how a production data model changes over
> its lifetime — adding a column, adding a new fact, deprecating
> a dim, doing a non-breaking schema change, and the
> backfill/dual-write/expand-contract pattern that makes those
> changes safe. By the end of this lesson you'll have a
> playbook for "the requirements just changed" — the question
> that comes up in every senior interview.

---

## Why this lesson

Every "design a data model" question in an interview has a
follow-up that the candidates who only studied the first
question miss: *"what happens when the requirements change?"*
The product team ships a new feature. Finance asks for a
new cost breakdown. A new region launches and `dim_region`
needs five more rows. A/B testing is added and every fact
needs an `experiment_key`. A PII regulation lands and a
column has to be hashed. None of these are in the original
schema, all of them are in the real job, and the senior
candidate is the one who has a *playbook* for the changes
— not the one who draws the perfect v1 schema. This lesson
teaches the four moves you'll make most often: add a
column, add a fact, deprecate a dim, and ship a
non-breaking change. Each move has a pattern, and the
patterns compose.

---

## The four kinds of change

There are four kinds of change you'll see in production,
ordered from cheapest to most expensive.

| Change | Example | Cost | Backfill? |
|---|---|---|---|
| **1. Add a column** | `discount_pct` on `fact_order_items` | Cheap (minutes) | Optional |
| **2. Add a new fact** | `fact_refunds` next to `fact_orders` | Medium (hours-days) | Yes |
| **3. Add or evolve a dim** | `dim_customer` grows an SCD 2 history | Medium (hours) | Yes |
| **4. Deprecate a column/dim/table** | `dim_users.legacy_id` → gone | Expensive (days-weeks) | N/A |

The first three are *additive* — they don't break the
existing pipeline. The fourth is *subtractive* — it does.
Most production schema migrations are a mix.

---

## Move 1 — Add a column

The cheapest change. A new attribute appears in the
source (e.g., the order service starts emitting
`discount_pct` on each line item).

**Step 1.** Add the column to the fact table DDL, with
a default value:

```sql
ALTER TABLE fact_order_items
ADD COLUMN discount_pct REAL NOT NULL DEFAULT 0.0;
```

**Step 2.** Update the ELT job to populate the column
from the new source field.

**Step 3.** Verify: query the new column, compare to
source, confirm the rollup matches the old
`discount_amount / gross_amount` (within rounding).

**Step 4.** (Optional) Backfill. If the column has
historical truth in the source (e.g., the OLTP DB has
the value going back a year), backfill. If it doesn't
(e.g., it was a brand-new feature last week), don't
backfill — the historical rows legitimately have the
default.

**Interview rule of thumb:** new columns are safe by
default. Add them with a sensible default, populate
forward, and only backfill when there's historical
truth to backfill *from*.

### The "backwards-compatible column" pattern

The senior move: when you're not sure whether a column
will be used, add it *nullable* and with no default.
This forces the analyst to handle the NULL explicitly,
which prevents silent NULL-vs-zero bugs.

```sql
ALTER TABLE fact_order_items
ADD COLUMN discount_pct REAL;          -- nullable, no default
```

The query then has to say `WHERE discount_pct IS NOT NULL`
to filter to populated rows. That's a feature, not a bug
— it makes the "is this column populated yet?" question
answerable at query time.

---

## Move 2 — Add a new fact

A new event type appears in the source. Examples: refunds,
cancellations, returns, re-shipments, loyalty redemptions.

The decision tree:

1. **Is the new event at the *same grain* as an existing
   fact?** If yes, *add a column* to the existing fact
   (Move 1) with a flag or measure. Example: refunds at
   the order-line-item grain go on `fact_order_items` as
   `refund_amount` and `is_refunded`.
2. **Is the new event at a *different grain*?** Then add
   a *new* fact table. Example: refunds at the refund
   event grain (one row per refund, which can span
   multiple line items) go on `fact_refunds`.
3. **Is the new event *unrelated* to existing facts?** Add
   a new fact and don't worry about dim overlap. Example:
   `fact_login_events` is unrelated to `fact_orders`.

**Step 1.** Decide which case you're in. Write the grain
on the whiteboard before writing DDL.

**Step 2.** Create the new fact table with shared dim
FKs (use the *same* dim tables as the existing fact —
don't create parallel dims).

**Step 3.** Backfill from the source. This is where the
"evolving" part bites you: if the source has the event
going back 6 months, backfill 6 months. If the source
only started emitting last week, backfill 1 week.

**Step 4.** Add a reconciliation check: the new fact
should reconcile to the source. The number of refund
rows in the warehouse should equal the number of refund
events in the OLTP DB, modulo late-arriving events.

**Interview rule of thumb:** when the interviewer says
"now add refunds," your first question is *"at what
grain?"* If you don't ask, you'll be wrong.

### Worked example — adding refunds

> "We have a working e-commerce star. Now add refunds."

You ask: "Is a refund one event per refund, or one event
per refunded line item? Can a refund span multiple line
items?"

If the answer is "one event per refund, can span line
items," then:

- New fact: `fact_refunds`, grain = one row per refund
  event.
- New dim: `dim_refund_reason` (low-cardinality, 5–10
  rows: `customer_request`, `damaged`, `late_shipping`,
  `wrong_item`, `fraud`).
- Shared dims: `dim_customer`, `dim_date`, `dim_orders`
  (new FK).
- Measures: `refund_amount`, `restocking_fee`,
  `net_refund`.

If the answer is "one event per refunded line item,"
then refunds live on `fact_order_items` as
`refund_amount` and `refund_reason` (no new fact).

The candidate who asks the grain question answers
correctly. The candidate who assumes a new fact
("refunds must be a new table!") often creates a
fact at the wrong grain.

---

## Move 3 — Evolve a dim (especially SCD 2 history)

A dim grows. Two common cases:

- **A new attribute appears.** E.g., the customer
  service team wants to track "lifecycle stage" (lead,
  trial, active, churned) on `dim_customer`. The source
  has the value going back a year. You need SCD 2
  history.
- **A new dimension is born.** E.g., a new
  `dim_subscription_plan` is added because the product
  launches a new tier.

### The SCD 2 history play

The pattern:

1. **Identify the new attribute.** Confirm it changes
   over time (i.e., it isn't constant for each customer)
   and that the analytics team needs the *historical*
   value, not the current one.
2. **Create a new dim version table** or evolve the
   existing dim to be SCD 2. The new rows have
   `effective_date = <change_date>`, `is_current = 1`;
   the old rows get `expiry_date = <change_date>` and
   `is_current = 0`.
3. **Backfill from the source.** The source has the
   history (event log, change-data-capture, audit
   table). Replay the history into the SCD 2 dim.
4. **Update the fact load** to look up the dim at the
   *event time*, not load time. This is the temporal
   join (Lesson 21).

**The trap:** if you forget step 4, every historical
fact row will join to the *current* dim row, which is
the SCD 2 row with `is_current = 1` — and your
"historical" analytics are silently using today's
values. The fix is always a temporal join.

### A new dim

Easier. Create the dim, populate from the source,
add the FK to the relevant fact. No SCD 2 history
required unless the dim itself changes over time
(usually it doesn't — a `dim_subscription_plan` is
SCD 1).

---

## Move 4 — Deprecate a column, dim, or table

The most expensive change. Subtractive changes break
consumers. The pattern: **expand-contract**, never
"just delete it."

### Expand-contract

A two-phase migration.

**Phase 1 — Expand.** Add the new structure (new
column, new dim, new table). Dual-write: the pipeline
populates *both* the old and the new. The old is still
the source of truth.

**Phase 2 — Migrate.** Update consumers (BI tools,
notebooks, downstream tables) to read from the new
structure. Roll out gradually: 1% of dashboards, then
10%, then 50%, then 100%.

**Phase 3 — Contract.** Once 100% of consumers are on
the new structure, *remove* the old. This is when the
DDL drops the column or the table.

The crucial property: at every point in the migration,
the system is in a consistent state. There is no
moment where the new structure is partially populated
and partially depended on, and there is no moment
where the old structure is gone but a consumer is
still reading it.

### Why not just "rename the column"?

You can, in a database that supports it. The problem
is that a rename is a single DDL statement that
*simultaneously* drops the old and creates the new.
Every consumer that was reading the old column breaks
at the same instant. In production, with hundreds of
downstream consumers, this is a multi-day outage.

The expand-contract pattern makes the rename
*eventually consistent*: the old is alive for as long
as the migration takes, the new is alive from the
start, and there's no instant where both break.

### Deprecation checklist

Before you delete a column, dim, or table:

1. **Find every consumer.** Grep the codebase, the BI
   tool's metadata, the downstream dbt models,
   every notebook in the analytics repo. The
   `INFORMATION_SCHEMA.COLUMNS` view (in Snowflake,
   BigQuery, Redshift) lists every column and its
   last-modified time — that's a great starting
   point.
2. **Notify consumers.** Email, Slack channel, a
   "deprecated" tag in the dim, a `deprecated_at`
   timestamp.
3. **Set a removal date.** Typically 90 days after
   deprecation. Long enough to migrate; short enough
   that the deprecation doesn't drag on.
4. **Run the expand-contract migration.**
5. **Delete.** Drop the column / dim / table on the
   removal date.

---

## The interview playbook for "the requirements changed"

When the interviewer says "now the requirements
changed," your response is a 30-second pitch in this
order:

1. **Clarify the change.** "What changed? A new
   attribute, a new event, a new dim, or a removal?"
2. **Pick the right move.** Add column (Move 1), add
   fact (Move 2), evolve dim (Move 3), or
   expand-contract (Move 4).
3. **State the cost.** "Minutes" / "Hours, with
   backfill" / "Days, with consumer migration."
4. **Name the trap.** Every move has a trap: "Move 1
   is safe by default" / "Move 2 needs a grain
   decision" / "Move 3 needs a temporal join" / "Move
   4 needs expand-contract."

That's the senior answer. It signals that you have
*migrated schemas in production*, not just designed
them.

---

## What can go wrong

### Wrong — silently breaking a consumer

You drop a column that a downstream dbt model still
reads. The dbt model fails the next morning. The
on-call engineer pages you. The fix is the
expand-contract pattern.

### Wrong — adding a column without a default

```sql
ALTER TABLE fact_order_items ADD COLUMN discount_pct REAL NOT NULL;
```

Existing rows have no value for `discount_pct`. If the
table has a billion rows, the `ALTER` fails or takes
hours. Always add with a default, or add nullable.

### Right but slow — backfilling from a source that doesn't have history

The analyst asks "what was `discount_pct` for orders
placed last month?" but the source only started
emitting `discount_pct` last week. You can't backfill
from nothing. The honest answer is "we have it from
<date> forward, not before."

### Right but expensive — "just add a new fact"

Sometimes a new fact is the right answer. Sometimes a
column on the existing fact is right. The cost of
adding a new fact is non-trivial (new table, new
backfill, new dim FKs, new ELT job). Default to
adding a column on the existing fact *unless* the
grain is genuinely different.

---

## The five-rule checklist for a safe change

Before you ship a schema change, run through:

1. **Backward compatible?** Does the change break
   existing readers? (If yes, you need
   expand-contract.)
2. **Default values?** New NOT NULL columns need a
   default. New FK columns need to point to a valid
   dim row.
3. **Backfill?** Is there historical truth in the
   source? If yes, plan a backfill job. If no, plan
   "we have it from <date> forward."
4. **Consumers identified?** Have you grepped the
   codebase, the BI tool, the dbt models?
5. **Rollback plan?** If the migration goes wrong
   (the backfill corrupts data, the new column
   breaks a query), can you roll back? In a
   well-designed expand-contract, yes — the old
   structure is still there.

---

## Try it

Pick any of the canonical modeling questions. Design
v1 of the star. Then evolve it through these three
changes:

1. Add a column: a new measure on the fact
   (e.g., `cost` on `fact_order_items`).
2. Add a new fact: a related event at a different
   grain (e.g., refunds, cancellations).
3. Deprecate a dim attribute: remove a column from
   `dim_customer` (e.g., `legacy_id`).

For each, write the DDL, list the consumers you'd
need to find, and time-box the migration (e.g., "Move
1: 30 minutes, no backfill").

The full DDL for the five practice schemas is in
[`code/star_schemas.py`](../code/star_schemas.py). The
ER-to-table translator in
[`code/er_to_tables.py`](../code/er_to_tables.py)
implements the five mechanical translation rules from
the original Lesson 14, which are still the foundation
for *creating* a schema. This lesson is about
*evolving* one.

---

## In the interview, you would say...

> "When the requirements change, I pick from four moves:
> add a column (cheap, safe by default with a
> default value), add a new fact (medium cost, requires
> a grain decision — same grain as an existing fact
> means a new column, different grain means a new
> table), evolve a dim (medium cost, requires a
> temporal join so historical facts see historical dim
> values), or deprecate (expensive, requires
> expand-contract — never just rename, because every
> consumer breaks at the same instant). The senior
> answer names the move, the cost, and the trap in 30
> seconds."

*Author: Prem Vishnoi <pvishnoi@avilx.com>*
