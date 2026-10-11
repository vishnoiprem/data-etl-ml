# Lesson 30 — Materialized Views and Pre-Aggregation

> **What you'll learn:** the pre-aggregation pattern —
> compute the expensive aggregate once, store it, and serve
> queries from the stored result. By the end you'll know
> when to roll up, when to leave it raw, and how to keep
> the rollup fresh.

---

## The problem with running aggregates on raw facts

The canonical fact table has millions or billions of rows.
A query like "revenue by country by month" has to scan
the whole fact, join the customer dim, group by two
columns. On 50M rows, that's a slow query — and the
dashboard hits it every 30 seconds.

If the underlying fact is append-only (transactional fact,
Lesson 24), the aggregate is *also* append-only: every
new row adds a little to the existing month-country cell.
The same query, run a thousand times, computes the same
thing a thousand times.

That's the use case for a pre-aggregated rollup.

---

## The pattern: rollup table

A rollup is a smaller table that holds the *result* of an
expensive aggregate. The dashboard query reads the
rollup, not the fact.

```
fact_orders        (50M rows)
   ↓
   group by country, month
   ↓
agg_country_month   (120 rows, one per country × month)
```

The query `SELECT country, month, SUM(amount) FROM fact_orders GROUP BY country, month` on 50M rows becomes
`SELECT country, month, total FROM agg_country_month` on
120 rows. Five orders of magnitude faster.

### The tradeoff

The rollup costs storage (small) and freshness (you have
to refresh it). You accept a delay — minutes or hours
behind the fact — for a query that's 1000x faster.

In the interview, the question is *not* "should I have
a rollup" — it's "which aggregates are worth rolling up."
Rule of thumb: roll up the aggregates that are queried
often and are slow on the raw fact. Don't roll up
everything.

---

## Pre-joined wide tables

The other pre-aggregation pattern: a *wide* table that
pre-joins the fact to the dimensions the analyst needs.
The wide table has the joined columns on it, so the
analyst doesn't have to join at query time.

```
fact_orders        (50M rows, customer_key, product_key, ...)
dim_customer       (1000 rows)
   ↓
   JOIN customer ON fact.customer_key = dim.customer_key
   ↓
wide_orders        (50M rows, customer_key, country, date_key, amount)
```

The query "revenue by country by month" goes from a
3-way join to a single-table scan on the wide table. The
analyst never has to remember which dim to join.

### When to use

- A small set of dimensions (3–5) covers 80% of queries.
- The fact-to-dim join is expensive (large dim, many
  rows).
- Storage is cheap and the wider rows are still
  reasonable.

### When *not* to use

- The fact table is used by many teams with different
  dimension needs — one team's wide table is another's
  noise.
- Dim attributes change often (SCD 2) — the wide table
  has to be rebuilt to reflect historical truth.
- The fact is sparse (most rows don't join to the dim
  for a given query).

---

## Materialized views — the native form

In a real warehouse, you don't write a separate "build
the rollup" script. You use a *materialized view*:

```sql
-- Snowflake
CREATE MATERIALIZED VIEW agg_country_month AS
SELECT
  c.country,
  (f.date_key / 100) % 100 AS month,
  COUNT(*) AS n,
  SUM(f.amount) AS total
FROM fact_orders f
JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY c.country, month;
```

The warehouse:

- Stores the result of the query.
- Refreshes it on a schedule (or on demand).
- Rewrites queries that reference the underlying query
  to read from the materialized view instead.

Snowflake, BigQuery, Redshift, Postgres (with
`pg_matviews` extension), and Oracle all have native
materialized views. SQLite does not, so this module
simulates the pattern with a regular table.

### The benchmark

`benchmark_rollup_query` in
[`code/materialized_views.py`](../code/materialized_views.py)
simulates the rollup pattern: build the rollup, then
query the rollup instead of the raw fact. Compare to
`benchmark_raw_aggregate`, which runs the same query
against the raw fact with the join.

---

## Refresh strategies

The hard part of materialized views is *keeping them
fresh*. There are three common strategies.

### 1. Full refresh

Truncate the rollup and re-compute it from scratch. Simple
and correct. Slow on large facts (you scan the whole
fact every refresh).

```sql
DELETE FROM agg_country_month;
INSERT INTO agg_country_month
SELECT c.country, ..., SUM(f.amount)
FROM fact_orders f JOIN dim_customer c ON ...
GROUP BY c.country, month;
```

In the demo, `refresh_rollup` does exactly this.

### 2. Incremental refresh

Only add the *new* fact rows to the rollup. Fast, but
requires a way to know "what's new since last refresh"
and *only* works if the aggregate is monotonic
(transactional facts — yes, balance snapshots — no).

```sql
INSERT INTO agg_country_month
SELECT c.country, ..., SUM(f.amount)
FROM fact_orders f JOIN dim_customer c ON ...
WHERE f.order_key > (SELECT MAX(last_key) FROM refresh_log)
GROUP BY c.country, month;
```

The interview: "I'd use incremental refresh because
the fact is append-only and the aggregate is
additive — I just need to track the high-water mark."

### 3. Streaming / continuous

BigQuery, Materialize, and others maintain the rollup
in near-real-time as rows arrive. The cost is operational
complexity and infrastructure.

---

## The freshness-vs-latency tradeoff

The decision is: how stale is the rollup allowed to be?

- **5 minutes stale** — incremental refresh every 5
  minutes, or streaming. Good for operational dashboards.
- **1 hour stale** — incremental refresh every hour. Good
  for executive dashboards.
- **24 hours stale** — full refresh nightly. Good for
  reporting and finance.
- **Never stale** — don't pre-aggregate. Run the
  aggregate on demand. Good for one-off analyses.

In the interview: "I'd refresh the country × month
rollup hourly because the dashboard refreshes hourly
and the user tolerance for staleness is low. For
quarter-by-region, I'd refresh nightly because the
report is daily and an hourly refresh would waste
compute."

---

## When *not* to pre-aggregate

Pre-aggregation is a strong tool, not a default. Skip
it when:

- **The query is rare** — one analyst runs it once a
  quarter. Compute on demand.
- **The cardinality of the group-by is high** — a
  rollup by `(customer_id, date_key)` has as many rows
  as the fact itself. No win.
- **The query has many filters** — a rollup by
  `country × month` doesn't help a query that filters
  by `product_id`. You'd need a rollup per filter
  combination — combinatorial explosion.
- **The fact changes retroactively** — a periodic
  snapshot fact (Lesson 25) doesn't have an additive
  rollup; you'd recompute every refresh.

---

## Pre-aggregation checklist

Before adding a rollup, ask:

1. **Is the aggregate queried often?** (Yes → roll up.
   No → compute on demand.)
2. **Is the aggregate additive?** (Yes → incremental
   refresh possible. No → full refresh only.)
3. **What's the cardinality of the group-by?** (Low →
   small rollup. High → rollup may not be smaller than
   the fact.)
4. **How stale can the rollup be?** (5 min → incremental
   every 5 min. 1 day → nightly full refresh.)
5. **Does the rollup replace a slow fact scan?** (Yes
   → measure. No → don't bother.)

If you answer "yes, additive, low cardinality, hourly
staleness, replaces a 30s scan," you have a rollup
candidate.

---

## Common interview answers

- "I'd pre-aggregate the country × month rollup because
  the dashboard query runs every 30s and the underlying
  fact is 50M rows. Hourly incremental refresh."
- "I wouldn't roll up by customer × date because the
  cardinality is too high — the rollup would be almost
  as big as the fact. Instead I'd let those queries run
  on demand and cache at the BI layer."
- "For finance reporting, I'd add a full refresh
  nightly — finance is OK with one-day staleness and
  prefers the simplicity of 'rebuild from scratch' over
  incremental complexity."

---

## Try it

Open
[`code/materialized_views.py`](../code/materialized_views.py)
and run:

```bash
cd data_modeling/06_performance/code
python3 materialized_views.py
```

Then run the tests:

```bash
python3 -m unittest data_modeling/06_performance/tests/test_performance.py
```

The test `test_rollup_matches_raw` asserts that the
rollup and the raw aggregate return the same number of
(country, month) groups — that's the *correctness*
property. The test `test_refresh_rollup_returns_rows`
exercises the full-refresh workflow.

---

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
