# Lesson 09 — Sample Business Requirements: Subscription Product

> **What you'll learn:** a worked end-to-end discovery session for
> a subscription SaaS prompt (the kind you get at Slack, Notion,
> Linear, Calendly). You'll see how the grain decision interacts
> with the SCD choice for `dim_customers` and the choice of
> accumulating vs transactional fact tables.

---

## The prompt

> Interviewer: "Design a data warehouse for a subscription
> product (think Notion or Linear) so the analytics team can
> measure monthly recurring revenue, churn, and expansion."

Subscription products have a *time-series* flavor that single-purchase
products don't. The same customer can have a $0 plan in January, a
$10 plan in February, a $50 plan in March, and a $0 plan in April
(churn). The schema has to support all of that without losing
the customer.

---

## The discovery (5 minutes)

> Candidate: "Subscription products have a few non-obvious
> modeling decisions. Before I draw, can I ask a few discovery
> questions?"

1. **How is 'MRR' defined — recognized at the start of the
   period, at the end, or as a daily average across the period?
   And do we treat upgrades and downgrades as the same logical
   event (a plan change), or as separate events (cancel + new
   sub)?**
2. **What counts as 'churn' — voluntary cancel, non-payment,
   account deletion, or all of the above? And is churn measured
   at the subscription level or at the customer level (a
   customer with three seats churning = 1 churn or 3)?**
3. **What's the grain of the headline metric — one row per
   subscription, one row per customer, or one row per
   customer-month?**
4. **Is the analytics team the only consumer, or do we also need
   to support finance (ASC 606 recognized revenue), ops (live
   cancellation flows), and customer success (accounts at risk)?**
5. **How do we model free trials — as a $0 plan, as a separate
   entity, or as a flag on the subscription?**
6. **Do we need to track changes to plan attributes (price,
   features) over time — SCD Type 2, or is the current value
   enough?**
7. **What's the freshness — daily, hourly, or real-time? And how
   do we handle refunds / partial refunds — as a reversal of
   the original invoice, or as a separate event?**

---

## The interviewer's answers (compressed)

> Interviewer: MRR is end-of-month, recognized. Plan changes are
> a single event. Churn is voluntary cancel only, at the
> subscription level. Grain is one row per customer-month. ASC
> 606 is out of scope for now. Free trials are a $0 plan with a
> flag. Plan SCD is Type 2. Freshness is daily. Refunds are
> separate events.

---

## The requirements doc (3 minutes)

The candidate writes (or narrates):

```markdown
# Requirements — Subscription SaaS

## Consumers
- **Analytics** — MRR, churn, expansion dashboards
- **Data Science** — churn prediction, expansion propensity
- **Customer Success** — accounts-at-risk alerts
- (Finance / ASC 606 deferred to a later phase)

## Use cases
1. MRR by month, by plan, by acquisition channel
2. Net new MRR (new + expansion − churn − contraction)
3. Logo churn by cohort
4. Revenue churn (lost MRR) by cohort
5. Expansion rate (upgrades as % of starting MRR) by cohort

## Source systems
| name | system | volume | freshness |
| --- | --- | --- | --- |
| customers | PostgreSQL | 10k/day | real-time |
| subscriptions | PostgreSQL | 5k/day | real-time |
| invoices | PostgreSQL | 50k/day | real-time |
| plans | PostgreSQL | 100 rows | daily |

## Fact tables
- **fact_subscriptions_monthly** — grain: one row per
  customer-month
  - measures: mrr, arr, is_active, is_new, is_churned,
    is_expansion, is_contraction
  - dimensions: dim_customers, dim_plans, dim_date
- **fact_subscription_events** — grain: one row per subscription
  event (created, upgraded, downgraded, churned, reactivated)
  - measures: mrr_delta
  - dimensions: dim_customers, dim_plans, dim_date, dim_event_type

## Non-functional
- **Volume:** 100k active subs, 1M+ historical customer-months
- **Freshness:** daily
- **Retention:** 7 years (finance / audit)
```

---

## The grain commitment (1 minute)

> Candidate: "OK — to make sure I have this right: the primary
> fact table is `fact_subscriptions_monthly` at the grain of
> **one row per customer-month**, with `mrr`, `is_active`, and
> `is_churned` as the headline measures. The
> `fact_subscription_events` table at the event grain handles
> the change events (new, upgrade, downgrade, churn). `dim_plans`
> is SCD Type 2 (we need historical plan prices for accurate
> revenue). Free trials are modeled as a $0 plan with an
> `is_trial` flag. Does that match what you had in mind?"

The interviewer confirms. The candidate has committed to:

1. **Grain:** customer-month (a periodic snapshot fact — see
   Module 05).
2. **Plan SCD:** Type 2.
3. **Event model:** separate event-level fact table for
   transitions.
4. **Trial model:** $0 plan with a flag (not a separate
   entity).
5. **Churn definition:** voluntary cancel only.

These five decisions drive the star schema in Module 05, where we
look at the *periodic snapshot* pattern in detail.

---

## What the candidate did right

- Asked the **MRR definition** question first — MRR is a
  famously slippery metric.
- Asked the **churn definition** question second — another
  famously slippery metric.
- Committed to the **customer-month grain** — the right call
  for subscription analytics.
- Made the **plan SCD** explicit.
- Deferred ASC 606 to a "later phase" — a real engineering
  answer to a real scoping question.

---

## What the candidate did *not* do

- Did not ask about **multi-currency**.
- Did not ask about **enterprise contracts** (annual commits,
  ramp deals).
- Did not ask about **usage-based pricing** (if the product
  meters by usage, the model is very different — see Lesson 09
  for a separate treatment).

---

## Try it

Re-do this exercise on a different subscription product. Try
Headspace (consumer subscription with annual plans), AWS (usage-
based with commits), or Slack (per-seat workspace subscription).
Time yourself: 5 minutes for discovery, 3 minutes for the doc, 1
minute for the grain commitment. Total: under 10 minutes.

Notice how the **grain** changes for usage-based products
(it's no longer customer-month — it's customer-meter-month or
even customer-API-call).

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
