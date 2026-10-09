# Lesson 07 — Sample Business Requirements: E-Commerce SaaS

> **What you'll learn:** a worked end-to-end discovery session for
> the canonical "design a warehouse for an e-commerce SaaS" prompt.
> You'll see the candidate ask 7 questions, write a requirements
> doc, and commit to a grain.

---

## The prompt

> Interviewer: "Design a data warehouse for an e-commerce SaaS so
> the analytics team can answer questions about revenue, customer
> cohorts, and product performance."

This is one of the six canonical modeling questions in
[`docs/reference/de_interview_canonical_questions.md`](../../../docs/reference/de_interview_canonical_questions.md#data-modeling-questions).
It shows up at Meta, Shopify, Stripe, Amazon, and most consumer
companies. The expected answer is a star schema with `fact_orders`
at the line-item grain, surrounded by `dim_customers`, `dim_products`,
`dim_date`, and a couple of smaller dims.

---

## The discovery (5 minutes)

> Candidate: "Before I draw, can I ask a few discovery questions?
> I want to make sure I build the right model."

1. **What does 'revenue' mean — gross merchandise value, net of
   refunds, recognized revenue, or collected revenue?** These give
   very different numbers and very different schemas.
2. **What's the grain of the headline metric? Are we tracking
   one row per order, one row per line item, or one row per
   shipment?**
3. **Is the analytics team the only consumer, or do we also need
   to support data science for cohort / LTV modeling, finance for
   recognized revenue, and ops for inventory?**
4. **What's the freshness — daily batch, hourly, or real-time?
   And how are refunds and cancellations handled — as a reversal
   of the original order, or as a separate event?**
5. **How do we identify a customer across devices — by user_id,
   by email, or by a household_id?**
6. **Do we need to track changes to product attributes over time
   (price changes, category re-classifications) — SCD Type 2, or
   is the current value enough?**
7. **Are there multi-currency or multi-region considerations?
   USD cents everywhere, or do we keep currency in the fact
   table?**

---

## The interviewer's answers (compressed)

> Interviewer: Good questions. Revenue is net of refunds, recognized
> at shipment time. Grain is one row per order line item. Consumers
> are analytics, data science, and finance. Freshness is hourly.
> Refunds are separate events (we don't reverse the original order).
> Customer is identified by user_id; we don't have a household
> concept. Product SCD is Type 2. Multi-currency: keep currency
> in the fact table.

---

## The requirements doc (3 minutes)

The candidate writes (or narrates):

```markdown
# Requirements — E-Commerce SaaS

## Consumers
- **Analytics** — revenue dashboards, cohort retention
- **Data Science** — LTV, churn, recommendation features
- **Finance** — recognized revenue, refund tracking

## Use cases
1. Net revenue by month, by category, by country
2. Cohort retention (signup month × order month)
3. LTV by acquisition channel
4. Top-N products by revenue
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
> `quantity` and `net_amount` as the primary measures. The
> customer dimension is SCD Type 2 (we need historical
> attribution). Refunds are a separate fact table
> (`fact_refunds`) joined to `fact_order_items` on
> `order_item_id`. Does that match what you had in mind?"

The interviewer confirms. The candidate has now committed to:

1. **Grain:** order line item.
2. **Customer SCD:** Type 2.
3. **Refunds:** separate fact table, not a reversal of the
   original.
4. **Currency:** kept in the fact table.

Every later decision is consistent with these four. The candidate
is now ready to draw the star schema (Module 03, Lesson 16).

---

## What the candidate did right

- Asked the **metric definition** question first (revenue).
- Asked the **grain** question second — before anything else.
- Asked **SCD** explicitly, not as an afterthought.
- Wrote a requirements doc with all the required sections.
- Repeated the grain back to the interviewer, with named
  measures.
- Made a defensible assumption about refunds (separate fact) and
  said it out loud.

---

## What the candidate did *not* do

- Did not ask about scale beyond what the prompt implied.
- Did not ask about data quality (deduplication, late events).
- Did not ask about PII or regulatory constraints.
- Did not draw the star schema yet — that's Lesson 16.

---

## Try it

Re-do this exercise on a different product. Pick any
consumer-facing app you use (Robinhood, Headspace, Notion,
Calendly). Time yourself: 5 minutes for discovery, 3 minutes for
the doc, 1 minute for the grain commitment. Total: under 10
minutes.

If you can hit 10 minutes for a prompt you've never seen, you're
ready for Module 03.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
