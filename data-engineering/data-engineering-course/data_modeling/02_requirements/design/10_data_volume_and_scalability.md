# Data Volume & Scalability Considerations

## Why this lesson

Volume and scalability are the non-functional requirements that decide whether a "looks right on paper" schema actually performs in production. A fact table at 50k rows/day is a different design problem from one at 10B rows/day: the latter needs hot/cold partitioning, pre-aggregation, and careful dim design to keep joins bounded. A user dim at 100k rows is a different design problem from one at 500M rows: the latter needs surrogate-key strategies, role-playing optimization, and a serious conversation about mini-dims vs single wide dim. This lesson teaches the volume-discovery questions a senior candidate asks, the orders of magnitude that matter, and the schema decisions each tier of volume forces.

---

## The volume tiers

There are three volume tiers every senior modeler should know
cold. Each tier implies a different set of schema and
operational decisions:

| Tier | Rows/day | Rows/year | Historical | Schema implications |
|---|---|---|---|---|
| **Small** | < 1M | < 365M | < 1B | Star schema is fine; full daily partition; no pre-aggregation needed. |
| **Medium** | 1M–100M | 365M–36B | 1B–10B | Hot/cold partition; materialized rollups for the top 10 dashboards; consider dim sharding. |
| **Large** | > 100M | > 36B | > 10B | Pre-aggregation mandatory; columnar + sort-key; consider OLAP cube or serving store. |

The interview signal: the candidate names the *tier* and lists
the implications in one breath.

---

## Volume discovery — the questions a senior candidate asks

> Candidate: "Before I draw, I need to understand the volume
> and growth trajectory, because the schema decisions at 1M
> rows/day are very different from the decisions at 10B
> rows/day."

1. **Daily write volume.**
   > "How many rows per day land in the headline fact table —
   > order of magnitude? 10k, 1M, 100M, 1B?" This decides
   > partitioning and storage strategy.
2. **Historical depth.**
   > "How many years of history do we keep online — 1 year, 3
   > years, 7 years, forever?" This decides retention and
   > archival.
3. **Growth rate.**
   > "What's the year-over-year growth — 2x, 5x, 10x?" This
   > decides whether the design needs to anticipate 10x scale
   > or can be tuned for current scale.
4. **Dim cardinality.**
   > "How many distinct customers / users / products / SKUs in
   > the dim — 100k, 10M, 100M, 1B?" A 1B-row dim is a
   > different design problem from a 100k-row dim.
5. **Hot partitions.**
   > "Are some partitions much hotter than others — e.g., one
   > customer, one product, one region, or one day of the week
   > generating a disproportionate share of the writes?" This
   > decides whether we need a sharding or hashing strategy on
   > the partition key.
6. **Query concurrency.**
   > "How many concurrent queries do we expect — 10, 100, 1000?"
   > This decides whether the warehouse needs read replicas or
   > a serving layer.
7. **Top-N dashboard queries.**
   > "What are the top 5 most-run dashboard queries, and at
   > what latency SLA?" These are the candidates for
   > pre-aggregation.
8. **Dim update frequency.**
   > "How often do dim rows change — daily, hourly, real-time?
   > And how many rows change per refresh?" A 100M-row dim
   > that fully rewrites daily is a different design problem
   > from a 100M-row dim with 1% of rows changing daily.

---

## How volume drives schema choice

| Volume signal | Modeling decision |
|---|---|
| > 100M rows/day on the fact | Hot/cold partition by date; pre-aggregate top dashboards. |
| > 10B historical rows | Archival to cold storage; only the last 90 days live. |
| Dim with > 100M rows | Consider mini-dim split, or sharded dim, or moving high-cardinality attributes to a satellite table. |
| Hot partition (one customer = 30% of writes) | Hash partition within the date partition; or assign a dedicated partition. |
| 10x year-over-year growth | Avoid full-dim rewrites; use SCD 2 inserts only; design for append-mostly. |
| Top-5 dashboard at 5s SLA on a 10B-row fact | Pre-aggregated rollup at daily or hourly grain; serving store. |
| Dim changes 1% per day, dim is 100M rows | Incremental SCD 2 (insert new version, expire old), not full rewrite. |

---

## The cardinality check

Every relationship has a cardinality. Get it wrong and the
schema breaks.

- **1-to-many** — one user has many workouts. The "many" side
  holds the foreign key.
- **many-to-1** — the inverse of the above. Same physical
  representation.
- **many-to-many** — workouts and exercises. Requires a bridge
  table. The bridge holds two foreign keys plus any
  measure-on-the-relationship (e.g., `reps`, `weight`).
- **1-to-1** — rare in a warehouse. Usually a sign that the two
  entities should be one.

The cardinality is a property of the *domain*, not the schema.
A user has many workouts *because that's how the product works*.
The schema encodes it; the schema does not invent it.

---

## Hot partitions — the most common production trap

A *hot partition* is a partition (or a slice of a partition) that
receives a disproportionate share of writes or reads. Examples:

- One mega-customer generating 30% of all orders.
- A "today" partition that everyone queries simultaneously.
- A single product that goes viral and dominates the
  `dim_products` reads.

The senior candidate asks about hot partitions explicitly, and
names three mitigations:

1. **Hash partition within a date partition** to spread the load
   on a single customer.
2. **Isolate the hot entity** — give it its own table or
   dedicated partition key.
3. **Read replicas** for read-heavy hot partitions.

> "Are some partitions much hotter than others — e.g., a single
> mega-customer, a single viral product, or 'today' receiving
> 50% of query traffic? If so, I'd hash-partition within the
> date partition and isolate the hot entity."

---

## The growth-rate check

The senior candidate asks about growth rate and designs for the
*future* volume, not the *current* one. The reasoning:

- A schema that's optimal at 1M rows/day may be unusable at
  100M rows/day (full dim rewrites that took 1 minute now take
  100 minutes).
- Schema migrations are expensive and disruptive. Better to
  over-design for growth than to under-design and have to
  migrate in 18 months.

> "What's the year-over-year growth — 2x, 5x, 10x? I'm going to
> design for the 12-month-out volume, not today's. That means
> SCD 2 inserts (not full dim rewrites), hot/cold partitioning,
> and a pre-aggregation strategy for the top 5 dashboards."

---

## The volume-driven requirements doc (3 minutes)

```markdown
# Requirements — E-Commerce SaaS (with volume section)

## Volume and scalability
- **Daily writes:** 50k orders/day, 200k line items/day
- **Historical:** 100M+ line items over 5 years
- **Growth rate:** 3x year-over-year (currently 200M/year,
  projected 600M/year in 12 months)
- **Dim cardinality:** 5M customers, 100k products, 50 countries
- **Hot partitions:** top-1 customer is 5% of orders (manageable
  with hash partitioning if it grows)
- **Concurrency:** ~50 concurrent analytics queries, ~5
  data-science queries
- **Top dashboards:** revenue-by-day, top-100 products, cohort
  retention (these are candidates for pre-aggregation at
  12-month scale)

## Schema decisions driven by volume
- `fact_order_items` partitioned by `date_key`, hash-partitioned
  by `customer_key` within each date to spread hot customers
- `dim_customers` SCD 2 with incremental insert (no full rewrite)
- Daily pre-aggregated rollup table for the top 3 dashboards,
  refreshed hourly
- 5-year retention online; older partitions archived to
  Parquet on S3
```

---

## Try it

Take any prompt from the canonical modeling questions. Write a
volume and scalability section for the requirements doc, with
order-of-magnitude estimates for: daily writes, historical
depth, dim cardinality, growth rate, concurrency, and the top 3
dashboards that would need pre-aggregation at 12-month scale.

Time yourself: 10 minutes.

---

## In the interview, you would say...

> "I'm going to ask about **volume and growth** before I commit
> to a schema, because the design at 1M rows/day is very
> different from the design at 10B rows/day. Specifically, I
> want to know: daily writes, historical depth, dim cardinality,
> growth rate, hot partitions, concurrency, and the top 3
> dashboard queries that would need pre-aggregation at scale."

---

*Author: Prem Vishnoi <pvishnoi@avilx.com>*
