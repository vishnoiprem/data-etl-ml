# Lesson 19 — Practice: Cloud Services Platform

> **What you'll learn:** the multi-fact star for an AWS/Azure/GCP-
> style cloud services platform — usage events for compute, storage,
> and networking joined to a `dim_customer` and `dim_service`, with
> **cost** as the headline measure. By the end of this lesson
> you'll be able to draw a cloud-billing warehouse that mirrors
> the way AWS Cost Explorer, Azure Cost Management, and GCP Billing
> actually model usage under the hood.

---

## Why this lesson

Cloud billing is one of the most common real-world data-modeling
prompts you will see at a hyperscaler (AWS, Azure, GCP) or at a
SaaS company that has migrated its infrastructure to the cloud. The
prompt — "model our cloud usage so we can answer questions about
cost by service, by team, by region, and over time" — sounds
straightforward, but it has three traps: (1) usage is multi-grained
(an EC2 hour is a *different* event from an S3 GET request, and
trying to fit both into one fact breaks the grain rule); (2)
**cost is not in the source** — it is a derived measure that
depends on the rate card, the region, the reservation status, and
the discount tier; and (3) IAM and billing live in a different
schema from usage, but finance and engineering want to see them
together. This lesson walks you through the model that production
cloud-billing warehouses actually use.

## The prompt

> "Design a data warehouse for a cloud services platform
> (think AWS / Azure / GCP) so the FinOps team can analyze
> spend by service, by customer, by region, and over time —
> and so engineering can correlate cost with usage."

The expected schema is a **two-fact** star: `fact_usage` for the
underlying usage events (compute hours, storage GB-hours, API
requests, network GB) and `dim_customer` plus `dim_service` plus
`dim_region` plus `dim_date` as the shared dimensions. A second
small fact `fact_billing` records the actual invoice line items
once the rate card has been applied.

---

## The star schema

```
                  ┌──────────────┐
                  │ dim_customer │
                  │ (SCD 2)      │
                  └──────┬───────┘
                         │ customer_key
                         ▼
┌──────────┐      ┌──────────────┐      ┌──────────┐
│ dim_date │◄─────┤  fact_usage  ├─────►│dim_service│
│          │      │              │      │          │
└──────────┘      │ measures:    │      └──────────┘
                  │  usage_qty   │      ┌──────────┐
┌──────────┐      │  unit_price  │◄─────┤dim_region │
│dim_usage_│      │  cost_usd    │      │          │
│  type    │      └──────┬───────┘      └──────────┘
└──────────┘             │
                        │            ┌──────────────┐
                        └───────────►│ fact_billing │
                                     │              │
                                     │ measures:    │
                                     │  billed_amt  │
                                     │  discount_amt│
                                     │  net_amount  │
                                     └──────┬───────┘
                                            │
                                       ┌────┴────────┐
                                       │ dim_invoice │
                                       └─────────────┘
```

Eight tables. Two facts, six dimensions.

---

## Why two fact tables

The two facts answer different questions:

- **`fact_usage`** answers engineering questions: "How many
  compute-hours did team X consume last week?" "What is the
  p95 API latency by region?" "Which services are growing
  fastest?" Every row is a **usage event** — one EC2 hour, one
  S3 GET, one GB egressed.
- **`fact_billing`** answers finance questions: "What did
  customer Y pay this month?" "How much of our revenue is
  Reserved Instance discounts?" "What's the variance between
  invoiced amount and recognized revenue?" Every row is a
  **line item on an invoice**.

Trying to combine them into one fact is tempting — and wrong. The
grains are different (an hour of usage is a continuous event; a
billing line is a monthly aggregation). The measures are different
(usage has `usage_qty` and `unit_price`; billing has
`billed_amount`, `discount_amount`, and `net_amount` with
reservation and credits applied). The dimensions overlap
(`dim_customer`, `dim_service`, `dim_date`) but the rows don't
align one-to-one — many usage events roll up into one billing
line.

The right move: two facts, shared dimensions, and a separate
"reconciliation" view that joins them on `customer_key +
service_key + month` to compute the usage-vs-billed variance
(typically 1–3% in steady state; spikes are how you catch
billing bugs).

---

## The measures on `fact_usage`

| Measure | Type | Notes |
|---|---|---|
| `usage_qty` | REAL | The quantity consumed. Hours for compute, GB for storage, count for API calls. |
| `unit_price` | REAL | The list price at the time of usage, from the rate card. |
| `cost_usd` | REAL | `usage_qty * unit_price * (1 - discount_pct)`. |

`cost_usd` is the headline measure on the usage fact. It is the
*list-cost* — what the usage would have cost at the public
rate card. Reserved Instance discounts, Savings Plans, and
Enterprise Discount Program (EDP) credits are applied later on
the billing fact, not the usage fact. This separation is what
lets you compute "what would this have cost without the
discount?" — a question FinOps asks every week.

`unit_price` is non-additive in the same way unit prices
everywhere are non-additive (you cannot sum unit prices to get a
meaningful number). `usage_qty` and `cost_usd` are additive.

---

## The measures on `fact_billing`

| Measure | Type | Notes |
|---|---|---|
| `billed_amount` | REAL | The amount on the invoice line. |
| `discount_amount` | REAL | Reserved Instance / Savings Plan / EDP discount. |
| `net_amount` | REAL | `billed_amount - discount_amount`. |

The billing fact has no `usage_qty` — that lives on `fact_usage`.
The billing fact is a **financial fact**: it answers "how much
did we invoice" and "how much did we discount" but not "how
much did they use." The join back to `fact_usage` is the
reconciliation view.

If your business needs recognized revenue (e.g., for SaaS
accounting with deferred revenue), add a third small fact
`fact_revenue` with `recognized_amount` and `deferred_amount`.
For this lesson, we stop at usage + billing.

---

## The dimensions

### `dim_customer` (SCD Type 2)

Cloud customers change plans (Free → Developer → Business →
Enterprise) and consolidate accounts. SCD 2 is mandatory —
"what plan was this customer on when they incurred this usage?"
is a daily question, and the answer must be the *historical*
plan, not the current one. The SCD 2 columns are the same as
in every other lesson: `effective_date`, `expiry_date`,
`is_current`.

A common wrinkle: enterprise customers have *account
hierarchies* — a parent org with many child accounts. The
parent org's `customer_key` is the dim; the child account is
an attribute (`child_account_id`) on the dim. Snowflaking the
hierarchy into a separate `dim_org_node` is the rare case
where snowflaking wins (the hierarchy changes on org
restructuring, not on plan changes).

### `dim_service`

A cloud platform has 200+ services (EC2, S3, RDS, Lambda,
CloudFront, …). The dim has the service name, category
(compute, storage, networking, database, ML, security), and
the *billing unit* (per-hour, per-GB, per-request). The
billing unit is what makes `unit_price` meaningful — without
it, the analyst doesn't know whether the price is per hour
or per request.

SCD 1 for most attributes. The exception: `unit_price` on
the dim is a snapshot of the rate card, not a per-row
column. The rate card is a separate, slowly-changing
structure (a new rate card every 1–5 years per service per
region). The rate card lives in its own table and is
applied to `fact_usage` at load time, not via the dim.

### `dim_region`

A small dim (50–100 rows for a global cloud) with
`region_name`, `geography` (US, EU, APAC), and `is_regional`
vs `global` (services like IAM and Route 53 are global, not
regional). SCD 1.

### `dim_date`

The standard conformed date dim. The cloud-billing question
"what was our cost on Black Friday 2024?" needs day-grain
date joins, and "what's the MoM growth" needs month-grain.

### `dim_usage_type`

A small dim with 10–20 rows: `compute_hours`, `storage_gb_hours`,
`api_requests`, `network_egress_gb`, `database_iops`, etc. This
is the "what kind of usage is this row?" column. Without it,
the analyst has to guess from the `service_key` and
`usage_qty` what unit the qty is in. With it, the query
"compute cost last month" is `WHERE usage_type = 'compute_hours'`
— explicit and joinable.

### `dim_invoice`

The invoice header — `invoice_id`, `billing_period_start`,
`billing_period_end`, `invoice_status` (draft, issued, paid,
written-off). Joins to `fact_billing` so the analyst can
filter "unpaid invoices" or compute "days sales outstanding"
(DSO).

---

## Why cost is computed at load time, not query time

A candidate trap: leave `cost_usd` out of `fact_usage` and
compute it as `usage_qty * unit_price` in every query. The
problem:

- **Rate cards change.** AWS lowers S3 prices every 2–3
  years. If you compute cost at query time, the analyst has
  to know which rate card to use for which time period.
- **Discounts differ by customer.** A reserved-instance
  customer has a 30% discount; an on-demand customer has
  0%. Computing this per-query means re-implementing the
  pricing engine in SQL.
- **Query speed.** A `SUM(usage_qty * unit_price)` over a
  billion-row fact is slow. A `SUM(cost_usd)` over the same
  table is fast (one INT or REAL, no expression).

The right move: compute `cost_usd` in the ELT job that
loads `fact_usage`. Store it. Trust it. Refresh it when the
rate card changes (which is rare). The `unit_price` column
is still on the fact for the rare case where the analyst
wants to re-derive cost at a different rate.

---

## The IAM wrinkle

IAM (Identity and Access Management) is a separate concern
from billing. The events are: user created, role assumed,
policy attached, key rotated, login succeeded, login failed.
These are *security audit* events, not cost events.

The correct model is a **third fact table** —
`fact_iam_events` — with its own grain (one event per IAM
action) and its own dimensions (`dim_iam_user`, `dim_role`,
`dim_policy`). Finance doesn't query it; Security does. The
two schemas share `dim_customer` (a customer has IAM users)
but otherwise don't join.

This is the "bus architecture" or "data vault" pattern:
multiple fact tables, shared conformed dimensions, no
attempt to model everything in one star. The interview
answer is: "I would have a separate security schema that
shares `dim_customer` with the billing schema. They are
different grains and different consumers; trying to put
both in one fact would break the grain rule."

---

## Worked query — cost by service by region, last 30 days

```sql
SELECT
    s.service_name,
    s.category,
    r.geography,
    SUM(f.cost_usd) AS total_cost_usd
FROM fact_usage f
JOIN dim_service s   ON f.service_key  = s.service_key
JOIN dim_region  r   ON f.region_key   = r.region_key
JOIN dim_date    d   ON f.date_key     = d.date_key
WHERE d.date >= DATE('now', '-30 days')
GROUP BY s.service_name, s.category, r.geography
ORDER BY total_cost_usd DESC
LIMIT 20;
```

This is the canonical FinOps dashboard query. The senior
candidate writes it without thinking. The trick: the
measures (`cost_usd`) are pre-computed on the fact, so
`SUM(cost_usd)` is fast even on a billion-row fact.

---

## Worked query — usage vs billed variance

```sql
WITH usage_rollup AS (
    SELECT
        c.customer_id,
        s.service_name,
        strftime('%Y-%m', d.date) AS month,
        SUM(f.cost_usd) AS usage_cost
    FROM fact_usage f
    JOIN dim_customer c ON f.customer_key = c.customer_key
    JOIN dim_service  s ON f.service_key  = s.service_key
    JOIN dim_date     d ON f.date_key     = d.date_key
    GROUP BY 1, 2, 3
),
billing_rollup AS (
    SELECT
        c.customer_id,
        s.service_name,
        strftime('%Y-%m', i.billing_period_start) AS month,
        SUM(b.net_amount) AS billed
    FROM fact_billing b
    JOIN dim_invoice  i ON b.invoice_key  = i.invoice_key
    JOIN dim_customer c ON b.customer_key = c.customer_key
    JOIN dim_service  s ON b.service_key  = s.service_key
    GROUP BY 1, 2, 3
)
SELECT
    u.customer_id,
    u.service_name,
    u.month,
    u.usage_cost,
    COALESCE(b.billed, 0) AS billed,
    u.usage_cost - COALESCE(b.billed, 0) AS variance_usd
FROM usage_rollup u
LEFT JOIN billing_rollup b
  ON u.customer_id  = b.customer_id
 AND u.service_name = b.service_name
 AND u.month        = b.month
ORDER BY ABS(variance_usd) DESC
LIMIT 20;
```

A 1–3% variance is healthy. A 10% variance is a billing bug
worth investigating. This query is how FinOps finds those
bugs.

---

## Tradeoffs to call out

1. **Why two fact tables, not one?** "Usage and billing are
   different grains. Usage is per-event; billing is
   per-invoice-line. Combining them requires nullable
   measures and breaks the grain rule."
2. **Why pre-compute `cost_usd` at load time?** "Rate cards
   and discounts differ per customer and over time.
   Computing at load encapsulates the pricing logic in one
   place; the analyst just sums."
3. **Why `dim_usage_type` and not a TEXT column?** "It
   lets the analyst attach attributes (e.g.,
   `is_billable`, `is_metered`) and reuse the dim across
   services. A TEXT column loses this."
4. **Why is IAM a separate schema?** "IAM events are
   security audit events, not cost events. Different
   grains, different consumers, different retention. The
   schemas share `dim_customer` and that's the only join
   they have."
5. **Why SCD 2 on `dim_customer`?** "Customers change
   plans. We need to attribute historical usage to the
   right plan, not the current one. The SCD 2 columns are
   non-negotiable."

---

## Try it

Without looking at the working code, draw the cloud
services star from memory. Then:

1. State the grain of each fact table out loud.
2. List the measures on each fact.
3. Explain why `cost_usd` is pre-computed, not derived.
4. Identify which dimensions are shared between the two
   facts (the conformed dims) and which are unique to one.

Time yourself: 10 minutes. The full DDL is in
[`code/star_schemas.py`](../code/star_schemas.py) as
`build_cloud_services_schema(q)`. The implementation is
minimal — enough to pass a test, not enough to be
production — but the structure is the same shape you'd
ship to a FinOps team.

```bash
python3 -m unittest data_modeling/03_high_level_diagrams/tests/test_schemas.py
```

---

## In the interview, you would say...

> "Cloud billing has two facts, not one — `fact_usage` for
> engineering questions (cost = usage × rate card, computed
> at load) and `fact_billing` for finance questions (the
> invoice line, with discounts applied). They share
> conformed dims on customer, service, region, and date,
> but the grains don't align. Cost is pre-computed on the
> usage fact so the analyst doesn't re-implement the
> pricing engine in every query. IAM is a separate schema
> that shares `dim_customer` — different grain, different
> consumer."

*Author: Prem Vishnoi <prem.vishnoi@example.com>*
