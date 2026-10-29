---
l_id: L159
title: When to use materialized views
duration: "4:30"
prereqs: ["L158"]
---

# L159 — When to use materialized views

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 3. Materialized Views
> **Duration:** 4:30

## Prereqs

L158 — Maintenance costs.

## Key terms

- **MV-suitable workload** — a small set of expensive queries
  on a moderately-changing source.
- **MV-unsuitable workload** — high-churn sources, low read
  frequency, or rapidly evolving queries.

## Lecture

Welcome back. Today's lecture is the decision rules. By the end,
you'll know the four questions to ask before creating a
materialized view.

### Question 1: Is the query expensive?

A `SELECT * FROM orders` does *not* need a materialized view;
Snowflake's result cache already serves it cheaply. A
`SELECT region, SUM(amount) FROM orders GROUP BY region` on a
1B-row table — that *might* benefit from a materialized view.

Rule: the query should be heavy enough that pre-computing it
saves a noticeable amount of read compute.

### Question 2: Is the result queried often?

If the dashboard refreshes every 5 seconds, the MV pays for
itself quickly. If a human runs the query once a month, the
maintenance cost will dominate.

Rule: the read frequency should be at least an order of
magnitude higher than the source change frequency.

### Question 3: Is the source relatively stable?

A source that changes 1M times per day is a poor candidate
for an MV — the maintenance cost will dominate. A source that
changes 1,000 times per day is fine.

Rule: prefer MVs on slowly-changing sources (orders/day, not
events/second).

### Question 4: Is the query stable?

If the query changes every week ("add this column", "filter by
that dimension"), an MV is the wrong tool — you'd be
re-creating it constantly. A task-driven pipeline is better
because you can version-control the SQL.

Rule: prefer MVs for stable, well-defined queries.

### The decision matrix

| Expensive? | Often? | Stable? | Stable source? | MV? |
|---|---|---|---|---|
| ✓ | ✓ | ✓ | ✓ | Yes |
| ✓ | ✓ | ✓ | ✗ | Maybe; measure |
| ✓ | ✓ | ✗ | ✓ | Pipeline |
| ✓ | ✗ | ✓ | ✓ | Maybe; small MV |
| ✗ | ✓ | ✓ | ✓ | No (cache suffices) |

### When NOT to use an MV

- **You need real-time data.** MVs lag by a few seconds; pick
  a regular view.
- **The query is rare.** A scheduled task that writes to a
  table is often cheaper.
- **The source is high-churn.** A pipeline is better.
- **The query is unstable.** A pipeline is better.

### When to use an MV

- A dashboard with a stable, expensive aggregate, refreshing
  every few seconds.
- An API that returns aggregated data, with the same query
  pattern across many users.
- A report that runs 10,000 times per day, with the source
  changing 100 times per day.

## Hands-on

For each of the following, decide whether an MV is appropriate:

1. Dashboard showing `SUM(amount) GROUP BY region` refreshing
   every 5 seconds; source changes ~10,000 times per day.
2. Monthly finance close: `SUM(amount) GROUP BY month`; runs
   once per month; source changes 1,000 times per day.
3. A/B test dashboard: `AVG(metric) GROUP BY variant`; source
   changes 1M times per day; query runs 100 times per day.

(Answers: 1 = yes, 2 = no, 3 = no.)

## Key takeaways

- Four questions: expensive? often? stable source? stable query?
- Use MVs for stable, often-queried, expensive aggregations
  on moderately-changing sources.
- For high-churn sources or rare queries, use a pipeline
  instead.
- When in doubt, measure with `METERING_HISTORY`.

## What's next

L160 — Limitations + recap. We close the MV sub-group with the
hard limits and a recap.