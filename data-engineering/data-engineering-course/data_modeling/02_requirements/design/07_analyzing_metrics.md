# Analyzing Metrics

## Why this lesson

Metrics are the *reason* a data warehouse exists. Before you draw a single dim or fact, the senior candidate has a clear answer to "what metrics does the business care about, and how are they defined?" A fitness app cares about DAU, MAU, retention, and workouts-per-user. A marketplace cares about GMV, take rate, and matching latency. A SaaS cares about MRR, churn, and NRR. Each metric implies a different fact table, a different grain, and a different dim. This lesson uses an e-commerce worked example to show you how to identify, define, and prioritize metrics — and how metric choice cascades into schema choice.

---

## The prompt

> Interviewer: "Design a data warehouse for an e-commerce SaaS so
> the analytics team can answer questions about revenue, customer
> cohorts, and product performance."

The candidate's first job is to identify the *metrics* the business
cares about. Below is how a senior candidate surfaces them.

---

## Metric discovery — the e-commerce worked example

> Candidate: "Before I draw, can I ask a few discovery questions?
> I want to make sure I build the right model — and that starts
> with agreeing on what metrics we're measuring."

### 1. Surface the headline metric

The first metric question is the most important: *what is the one
number the CEO looks at?* For e-commerce it is usually one of:

- **Gross Merchandise Value (GMV)** — total dollar value of goods
  sold through the platform, before refunds, fees, or costs.
- **Net Revenue** — GMV minus refunds, chargebacks, and discounts.
- **Recognized Revenue** — net revenue booked under ASC 606 / IFRS
  rules, often at shipment time.

These three give very different numbers. The candidate asks:

> "What's the headline metric — GMV, net revenue, or recognized
> revenue? And is the dollar value gross, net of refunds, or
> net of discounts and shipping?"

### 2. Surface the engagement / growth metrics

Beyond revenue, the business tracks a handful of growth metrics:

- **Daily Active Users (DAU)** — unique users with ≥1 session in a day.
- **Monthly Active Users (MAU)** — unique users with ≥1 session in
  a month.
- **Conversion rate** — % of sessions that result in an order.
- **Retention** — % of users from cohort C who are still active in
  month C+1, C+2, …
- **Customer Lifetime Value (LTV)** — projected revenue per
  customer over their lifetime.

The candidate asks:

> "Are we tracking engagement metrics like DAU, MAU, and
> conversion? Are we computing LTV by acquisition channel? Are we
> doing cohort retention analysis (signup month × order month)?"

### 3. Surface the operational metrics

Operations and merchandising teams care about additional metrics:

- **Refund rate** — refunds ÷ orders, by category.
- **Top-N products by revenue** — merchandising rankings.
- **Cart abandonment rate** — sessions that add to cart but never
  check out.
- **Average order value (AOV)** — net revenue ÷ orders.

> "Do we also need operational metrics — refund rate by category,
> top-N products, AOV, cart abandonment?"

---

## What metrics matter — the metric taxonomy

Here is a compact taxonomy of the metrics a senior candidate is
expected to know cold. For any prompt, the candidate can pattern-match
the prompt to the relevant subset:

| Category | Metric | Definition | Fact table |
|---|---|---|---|
| **Engagement** | DAU | unique users with ≥1 session/day | `fact_sessions` |
| **Engagement** | MAU | unique users with ≥1 session/month | `fact_sessions` |
| **Engagement** | Stickiness | DAU / MAU | derived |
| **Growth** | New users | signups in period | `fact_signups` |
| **Growth** | Conversion rate | orders / sessions | derived |
| **Growth** | Retention | active users in month N from cohort M | `fact_sessions` + cohort flag |
| **Revenue** | GMV | sum of gross order amount | `fact_orders` |
| **Revenue** | Net revenue | GMV − refunds − discounts | `fact_orders` + `fact_refunds` |
| **Revenue** | AOV | net revenue / orders | derived |
| **Revenue** | LTV | cumulative net revenue per customer | `fact_orders` |
| **Operational** | Refund rate | refunds / orders | `fact_refunds` + `fact_orders` |
| **Operational** | Top-N products | ranking of products by net revenue | `fact_orders` |
| **Operational** | Cart abandonment | sessions that add to cart but don't checkout | `fact_sessions` (with funnel) |

The interview signal: the candidate names metrics from the right
*category* for the prompt (engagement for a fitness app, revenue
for e-commerce, MRR for subscription) and explicitly defines each
in business terms.

---

## The interviewer's answers (compressed)

> Interviewer: Headline metric is **net revenue**, recognized at
> shipment time. We also care about **refund rate**, **cohort
> retention**, and **LTV by acquisition channel**. The grain is
> **one row per order line item**. Refunds are **separate
> events** (we don't reverse the original order).

---

## The metric-driven requirements doc (3 minutes)

The candidate writes (or narrates):

```markdown
# Requirements — E-Commerce SaaS

## Headline metrics
- **Net revenue** by month, by category, by country
- **Refund rate** by category
- **Cohort retention** (signup month × order month)
- **LTV** by acquisition channel
- **Top-N products** by net revenue

## Use cases
1. Net revenue by month, by category, by country
2. Cohort retention (signup month × order month)
3. LTV by acquisition channel
4. Top-N products by net revenue
5. Refund rate by category

## Source systems
| name | system | volume | freshness |
| --- | --- | --- | --- |
| users | PostgreSQL | 10k/day | real-time |
| orders | PostgreSQL | 50k/day | real-time |
| refunds | PostgreSQL | 500/day | real-time |
| product_catalog | PostgreSQL | 200/day | hourly |

## Fact tables
- **fact_order_items** — grain: one row per order line item
  - measures: quantity, gross_amount, discount_amount, net_amount,
    tax_amount, shipping_amount
  - dimensions: dim_customers, dim_products, dim_date, dim_orders

## Non-functional
- **Volume:** 50k orders/day, 200k line items/day, 100M+ historical
- **Freshness:** hourly
- **Retention:** 5 years
```

---

## The grain commitment (1 minute)

> Candidate: "OK — to make sure I have this right: the grain of
> the fact table is **one row per order line item**, with
> `quantity` and `net_amount` as the primary measures (the
> metrics net revenue, AOV, and refund rate all reduce to sums
> over this fact). The customer dimension is SCD Type 2 (we need
> historical attribution for cohort LTV). Refunds are a separate
> fact table (`fact_refunds`) joined to `fact_order_items` on
> `order_item_id`. Does that match what you had in mind?"

The interviewer confirms. The candidate has committed to:

1. **Grain:** order line item.
2. **Customer SCD:** Type 2.
3. **Refunds:** separate fact table, not a reversal of the
   original.
4. **Currency:** kept in the fact table.
5. **Headline metric:** net revenue (refund-aware).

Every later decision is consistent with these five. The candidate
is now ready to draw the star schema.

---

## What the candidate did right

- Identified the **headline metric** (net revenue) and asked how it
  was defined.
- Surfaced **multiple metric categories** — revenue, engagement,
  operational — not just one.
- Wrote a requirements doc organized around metrics, not entities.
- Repeated the grain back to the interviewer with named measures
  and named metrics.
- Made a defensible assumption about refunds (separate fact) and
  said it out loud.

---

## What the candidate did *not* do

- Did not ask about scale beyond what the prompt implied.
- Did not ask about data quality (deduplication, late events).
- Did not ask about PII or regulatory constraints.
- Did not draw the star schema yet — that's Module 03.

---

## Try it

Re-do this exercise on a different product. Pick any
consumer-facing app you use (Robinhood, Headspace, Notion,
Calendly). Time yourself: 5 minutes for metric discovery, 3
minutes for the doc, 1 minute for the grain commitment. Total:
under 10 minutes.

If you can hit 10 minutes for a prompt you've never seen, you're
ready for Module 03.

---

## In the interview, you would say...

> "I'm going to start by identifying the **headline metric** the
> business cares about and asking how it's defined — because
> 'revenue' can mean GMV, net revenue, or recognized revenue, and
> each implies a different schema. Then I'll surface 3–5 metrics
> across the relevant categories (engagement, growth, revenue,
> operational) and make sure each has a clear definition before I
> commit to a grain."

---

*Author: Prem Vishnoi <prem.vishnoi@example.com>*
