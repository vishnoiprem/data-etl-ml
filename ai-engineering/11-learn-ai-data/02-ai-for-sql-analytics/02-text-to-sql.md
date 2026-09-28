# Lesson 2 — Text-to-SQL

> **Type:** Article · Module 2 · AI for SQL & Analytics
> The real accuracy of AI on a 200-table warehouse, the failure modes that drive the gap, and when text-to-SQL is the right tool.

---

## The 30-second take

Text-to-SQL is **spectacular on benchmarks and rough on real warehouses**. On Spider, modern LLMs hit 85–90%. On BIRD (messier, more realistic), ~52%. On your actual 200-table warehouse with inconsistent naming and business logic in views, single to low double digits.

The fix is not a better model. The fix is a **semantic layer** that defines "active customer," "revenue," and "last quarter" once, in one place, and lets the AI generate SQL against *that*, not against the raw warehouse.

---

## The accuracy gap

```
   Spider benchmark          BIRD benchmark           Real warehouse
   (5-20 clean tables)       (messier, real-ish)      (200+ tables,
                                                         inconsistent
                                                         naming,
                                                         views)

   ████████████████ 85-90%   ██████ ~52%             ▌ ~5-18%

   Human expert on BIRD:                                  ██████████ ~93%
```

**Why the gap compounds:**
- Benchmarks use 5–20 well-documented tables. Your warehouse has 200+.
- Three of your `status` columns mean different things.
- "Active customer" is defined in a Looker view nobody documented.
- Joins go through bridge tables.
- The "real" revenue is a backout in a view.

Every factor degrades accuracy. They **compound**.

---

## The semantic layer is the precondition

```
   ┌──────────────────────────────────────────────────────────┐
   │  WITHOUT semantic layer                                 │
   │                                                          │
   │   "revenue last quarter"                                 │
   │        │                                                 │
   │        ▼                                                 │
   │   AI picks a plausible definition                        │
   │        │                                                 │
   │        ▼                                                 │
   │   wrong number, plausible-looking                        │
   │                                                          │
   │  WITH semantic layer                                     │
   │                                                          │
   │   "revenue last quarter"                                 │
   │        │                                                 │
   │        ▼                                                 │
   │   metric_registry.metric('revenue_q')                    │
   │        │                                                 │
   │        ▼                                                 │
   │   dbt model: fct_revenue_quarterly                       │
   │   (single source of truth, versioned, tested)            │
   │        │                                                 │
   │        ▼                                                 │
   │   right number, every time                               │
   └──────────────────────────────────────────────────────────┘
```

A semantic layer is a **small, curated set of well-defined metrics and entities** with:
- Names (`active_customer`, `gross_revenue_q`)
- Definitions (the SQL expression)
- Owners
- Tests

Tools: **Cube, dbt Semantic Layer, LookML, MetricFlow, Lightdash.**

---

## When text-to-SQL is the right tool

✅ **Right tool:**
- Ad-hoc analyst questions over a curated semantic layer
- Power users with a small, well-documented schema
- BI on a single product area
- Internal tools over a 10–20 table curated schema

❌ **Wrong tool:**
- "Give everyone in the company a chatbot over the warehouse"
- A 200+ table warehouse with undocumented logic
- Anything where wrong = silently wrong = CEO decision

---

## The text-to-SQL failure modes (real examples)

### Wrong table
*"Top customers by revenue"* → AI picks `customers_v2_backup` because it has a `revenue` column.

### Wrong join
AI joins `orders` to `customers` on `customer_name` instead of `customer_id`. Returns 3× the rows.

### Wrong filter
*"Cancelled orders last week"* → AI uses `WHERE status = 'CANCELLED'` but `status` has a different meaning in this table.

### Wrong aggregation
*"Net revenue"* → AI uses `SUM(gross_amount)` ignoring `refunds`. Plausible-looking, 12% high.

### Wrong grain
*"Orders per customer"* → AI returns orders per order line item. Looks plausible, 4× high.

---

## The text-to-SQL maturity ladder

```
   Level 1: NO semantic layer
            AI over raw warehouse
            accuracy: 5-18% on real
                       │
                       ▼
   Level 2: SEMANTIC LAYER (curated)
            AI over 10-50 well-defined metrics/entities
            accuracy: 60-80%
                       │
                       ▼
   Level 3: FEW-SHOT + SEMANTIC LAYER
            AI with curated examples per metric
            accuracy: 80-90%
                       │
                       ▼
   Level 4: RETRIEVAL-AUGMENTED TEXT-TO-SQL
            AI retrieves relevant schema + examples via RAG
            accuracy: 85-95%
                       │
                       ▼
   Level 5: AGENTIC TEXT-TO-SQL
            AI iterates, runs EXPLAIN, fixes its own mistakes
            accuracy: 90%+ but slower and more expensive
```

Most production systems live at **Level 2 or 3**. Level 4–5 are active research.

---

## The "talk to your data" mistake pattern

The story from Lesson 1 of Module 1:

> A retail team rolled out text-to-SQL over their real warehouse. Benchmark accuracy 85–90%. Real-warehouse accuracy collapsed to low double digits. Killed in 3 weeks.

The pattern repeats. The fix is **not a better prompt**. The fix is **a curated surface for the AI to talk to**.

---

## The build-vs-buy matrix

| Build | Buy |
|---|---|
| Cube / dbt Semantic Layer | Snowflake Cortex Analyst |
| Custom RAG over your schema | Databricks Genie |
| Internal agent over semantic layer | BigQuery Conversation Analytics |
| | ThoughtSpot, Sigma, Mode |

The buy side has gotten very good in the last 18 months. If your use case is "business users ask questions over a curated semantic layer," **buy first**. Build only when the off-the-shelf product hits a wall.

---

## What Comes Next

> Lesson 3 — **AI Query Optimization** — using AI as a reading assistant for EXPLAIN plans, query profiles, and cluster configs. Where AI helps, where it overpromises.
