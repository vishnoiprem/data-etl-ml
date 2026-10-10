---
l_id: L134
title: Methods of data sampling
duration: "5:00"
prereqs: ["L133"]
---

# L134 — Methods of data sampling

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 19 — Data Sampling
> **Duration:** 5:00

## Prereqs

L133 — Why data sampling? You should already know *why* a sample
is useful; today is the *how*.

## Key terms

- **`SAMPLE (p)`** — Snowflake's primary sampling operator. Returns
  roughly `p%` of the input rows.
- **`SAMPLE (N ROWS)`** — returns roughly `N` rows.
- **`SAMPLE BERNOULLI (p)`** — per-row Bernoulli sampling. Strictly
  random at the row level. Slower on very large tables.
- **`SAMPLE SYSTEM (p)`** — block-level sampling. Each *micro-
  partition* (block) is included with probability `p`. Faster, but
  less uniform.
- **`TABLESAMPLE`** — the ANSI SQL equivalent of `SAMPLE SYSTEM`.

## Lecture

Welcome back. Today we cover the three sampling primitives in
Snowflake. They are all keywords, all attach to a table expression,
and all return a subset. The differences are statistical: how
*uniform* is the random selection, and how *fast* does it run.

### 1. `SAMPLE (p)` — the default

```sql
SELECT * FROM orders SAMPLE (10);     -- 10% of rows
SELECT * FROM orders SAMPLE (0.5);    -- 0.5% of rows
```

This is a Snowflake-specific shorthand. By default it behaves
like `SAMPLE SYSTEM`: it samples whole micro-partitions. For most
use cases (test/dev, ad-hoc), this is exactly what you want.

You can also specify a row count:

```sql
SELECT * FROM orders SAMPLE (10000 ROWS);
```

Snowflake estimates the percentage from the row count and the
table's total, and applies that percentage via `SAMPLE SYSTEM`.

### 2. `SAMPLE BERNOULLI (p)` — per-row, strictly random

```sql
SELECT * FROM orders SAMPLE BERNOULLI (10);
```

`BERNOULLI` means each individual row is included with probability
`p` (here, 10%). This gives you the most uniform distribution
because there's no correlation between adjacent rows.

The trade-off is performance. Snowflake has to evaluate every row
in the source table, which means it has to scan more partitions
than `SAMPLE SYSTEM` would. For a 1B-row table, `SAMPLE BERNOULLI
(1)` can be 5–10× slower than `SAMPLE SYSTEM (1)`.

Use `BERNOULLI` when:

- you need a *strictly* uniform random sample (rare in practice)
- the table is small (≤ a few million rows)
- you're training an ML model where uniformity matters

### 3. `SAMPLE SYSTEM (p)` — block-level, fastest

```sql
SELECT * FROM orders SAMPLE SYSTEM (10);
```

`SYSTEM` samples whole micro-partitions. Snowflake picks each
partition with probability `p` and includes *all* rows in that
partition. The result is "blocky" — adjacent rows tend to be
included or excluded together — but it is much faster.

Use `SYSTEM` (or the bare `SAMPLE`) when:

- you want speed and "good enough" randomness
- you're doing test/dev or ad-hoc exploration
- you don't care about variance within a micro-partition

### 4. `TABLESAMPLE` — the ANSI SQL form

```sql
SELECT * FROM orders TABLESAMPLE SYSTEM (10);
SELECT * FROM orders TABLESAMPLE BERNOULLI (10);
```

Same semantics as `SAMPLE` and `SAMPLE BERNOULLI`, but with the
ANSI SQL name. Use this when you're writing portable SQL.

### How to choose

| Use case | Pick |
|---|---|
| Quick dev/test subset | `SAMPLE (10)` or `SAMPLE SYSTEM (10)` |
| ML training, uniform | `SAMPLE BERNOULLI (10)` |
| Portable SQL | `TABLESAMPLE SYSTEM (10)` |
| Approximate count of a huge table | `SAMPLE BERNOULLI (1)` |

### Common pitfalls

- **Sampling on a view.** The view's filter still applies, but the
  randomness is computed *after* the filter. That's usually what
  you want.
- **`SAMPLE` does not guarantee an exact percentage.** It guarantees
  a *probability*; the actual fraction can vary by a few percent.
- **Order of operations.** `SAMPLE` runs *after* `WHERE`. Filter
  first, then sample.

## Hands-on

```sql
USE SCHEMA SNOWFLAKE_SAMPLE_DATA.TPCH_SF1;  -- ~6M rows in ORDERS

SELECT COUNT(*) FROM ORDERS;                              -- ~6,000,000
SELECT COUNT(*) FROM ORDERS SAMPLE (10);                  -- ~600,000
SELECT COUNT(*) FROM ORDERS SAMPLE BERNOULLI (10);        -- ~600,000
SELECT COUNT(*) FROM ORDERS SAMPLE SYSTEM (10);           -- ~600,000
```

## Key takeaways

- `SAMPLE` (no keyword) defaults to `SAMPLE SYSTEM` — block-level.
- `SAMPLE BERNOULLI` is per-row, strictly random, slower.
- `TABLESAMPLE` is the ANSI equivalent; pick it for portable SQL.
- Sampling runs after `WHERE`; filter first, then sample.

## What's next

L135 is the **hands-on** — we use TPC-H data to validate that
sampled aggregations approximate the full-table aggregations.