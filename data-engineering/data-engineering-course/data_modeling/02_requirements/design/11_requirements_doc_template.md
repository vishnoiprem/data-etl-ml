# Lesson 11 — The Requirements Document Template

> **What you'll learn:** the structure of the `RequirementsDoc` we
> built in [`code/requirements_doc.py`](../code/requirements_doc.py),
> line by line. By the end of this lesson you'll be able to fill
> one in under 3 minutes for any prompt.

---

## The template

The `RequirementsDoc` helper produces a Markdown doc with seven
sections:

1. **Header** — product name.
2. **Consumers** — who queries the warehouse, and why.
3. **Use cases** — 3–5 questions the warehouse must answer.
4. **Source systems** — where the data comes from.
5. **Fact tables (with grain)** — the fact tables and their
   grain.
6. **Non-functional** — volume, freshness, retention.
7. **Assumptions / open questions** — anything you assumed or
   didn't pin down.

The order matters. The first three sections are what the
interviewer cares about; the rest is supporting detail.

---

## Section by section

### Header

```markdown
# Requirements — <Product Name>
```

Names the artifact. Trivial but essential — without the header,
the doc is anonymous and the interviewer has to guess what
you're talking about.

### Consumers

```markdown
## Consumers
- **<Team name>** — <what they use the warehouse for>
- **<Team name>** — <what they use the warehouse for>
```

A bullet per team. The "what they use it for" matters — it
tells the interviewer which use cases are highest priority and
which dimensions matter.

> Example: "**Data Science** — churn prediction, expansion
> propensity modeling."

The phrasing matters. "Churn prediction" implies a target
column is needed on the customer dim. "Expansion propensity"
implies a feature pipeline off the subscription events. The
phrasing *implies the schema*.

### Use cases

```markdown
## Use cases
1. <Question 1>
2. <Question 2>
3. <Question 3>
```

Numbered, not bulleted. The numbering signals priority — #1 is
the most important. Each use case is a *question*, not a
metric name. "What's the churn rate by cohort?" is a use case.
"Churn rate" alone is a metric; it doesn't tell the modeler
the grain.

### Source systems

```markdown
## Source systems
| name | system | volume | freshness |
| --- | --- | --- | --- |
| <name> | <system> | <volume> | <freshness> |
```

A table, not bullets. The columns are standardized so the
interviewer can scan the table. "Volume" is orders of
magnitude ("10M/day"), not precise counts. "Freshness" is the
publication cadence ("hourly", "real-time"), not the latency
budget.

### Fact tables (with grain)

```markdown
## Fact tables
- **<name>** — grain: *<one-sentence grain>*
  - measures: <measure 1>, <measure 2>, ...
  - dimensions: <dim 1>, <dim 2>, ...
```

The grain is *italicized and named*. This is the single most
important sentence in the entire document. The interviewer
will read it twice. If it's wrong, the rest of the round is
wrong.

The "measures" and "dimensions" lines are quick-reference. They
are *not* the schema; they are the *promises* the schema will
keep. The actual DDL is in Module 03.

### Non-functional

```markdown
## Non-functional
- **Volume:** <orders of magnitude>
- **Freshness:** <cadence>
- **Retention:** <how long>
```

Three lines. These drive the partitioning, the storage budget,
and the SLA. Without them, the modeler is guessing.

### Assumptions / open questions

```markdown
## Assumptions / open questions
- <assumption 1>
- <assumption 2>
```

The most under-rated section. The modeler writes down every
assumption they made and every question they couldn't get
answered. This is the *audit trail* — when the interviewer
corrects the modeler mid-round ("actually, refunds are
reversals, not separate events"), the modeler refers back to
this list and either edits it (good) or ignores it (bad).

The senior candidate writes a long assumptions list. The
mid-level candidate writes nothing. The list is the *signal*.

---

## Worked example — full template

```markdown
# Requirements — Subscription SaaS

## Consumers
- **Analytics** — MRR, churn, expansion dashboards
- **Data Science** — churn prediction, expansion propensity
- **Customer Success** — accounts-at-risk alerts

## Use cases
1. MRR by month, by plan, by acquisition channel
2. Net new MRR (new + expansion − churn − contraction)
3. Logo churn by cohort
4. Revenue churn (lost MRR) by cohort
5. Expansion rate by cohort

## Source systems
| name | system | volume | freshness |
| --- | --- | --- | --- |
| customers | PostgreSQL | 10k/day | real-time |
| subscriptions | PostgreSQL | 5k/day | real-time |
| invoices | PostgreSQL | 50k/day | real-time |
| plans | PostgreSQL | 100 rows | daily |

## Fact tables
- **fact_subscriptions_monthly** — grain: *one row per customer-month*
  - measures: mrr, arr, is_active, is_new, is_churned,
    is_expansion, is_contraction
  - dimensions: dim_customers, dim_plans, dim_date
- **fact_subscription_events** — grain: *one row per subscription event*
  - measures: mrr_delta
  - dimensions: dim_customers, dim_plans, dim_date, dim_event_type

## Non-functional
- **Volume:** 100k active subs, 1M+ historical customer-months
- **Freshness:** daily
- **Retention:** 7 years (finance / audit)

## Assumptions / open questions
- MRR is recognized at end of month (per interviewer)
- Plan changes are a single event (per interviewer)
- Free trials are a $0 plan with a flag
- ASC 606 recognized revenue is out of scope for v1
- Multi-currency: assuming single currency for v1
```

That's a 30-line doc. It took 3 minutes to write and it sets
up every later decision.

---

## The "what to leave out" rule

The template is minimal on purpose. Do not add:

- **Schema DDL.** That's Module 03. Mixing DDL into the
  requirements doc makes the doc a schema, not a spec.
- **Architecture diagrams.** That's a system-design round, not
  a data-modeling round.
- **Pipeline flow.** Out of scope.
- **Tooling decisions.** "We'll use Snowflake" is a v1 question
  that depends on the org's existing stack. Don't anchor on a
  tool in the requirements doc.

The discipline of *not* adding these is what makes the
requirements doc *just* a requirements doc. The interviewer
can refer back to it as the single source of truth for *what*
needs to be true, not *how* it will be true.

---

## Try it

Open the `RequirementsDoc` helper and instantiate one for any
product you know. Use the template above. Time yourself: 3
minutes. Print the rendered Markdown.

If you can hit 3 minutes for a prompt you've never seen, your
hands have learned the structure. The interview will feel
mechanical, in a good way.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
