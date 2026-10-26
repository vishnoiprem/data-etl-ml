---
l_id: L133
title: Why data sampling?
duration: "5:00"
prereqs: ["L132"]
---

# L133 — Why data sampling?

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 19 — Data Sampling
> **Duration:** 5:00

## Prereqs

L132 — Share data from multiple databases. By now you can move data
around (clones, shares) — sampling is about getting a subset of it
*inside* a single query.

## Key terms

- **Sampling** — drawing a representative subset of a larger dataset.
- **Statistical validity** — the property that the subset's
  properties (mean, distribution, etc.) approximate the whole's.
- **`LIMIT N`** — *not* sampling. It returns the first N rows in the
  table's natural order — usually not representative.
- **Test/dev environment** — the most common consumer of sampled
  data.

## Lecture

Welcome to section 19. This is the shortest section in the
published course, and the most underrated. By the end of it you'll
have a third way to get a subset of a table — the right way —
without writing a `WHERE ROWNUM <= 1000` query and pretending
that's representative.

### Why sample at all

Most real Snowflake tables have billions of rows. Three workloads
regularly need a representative subset:

1. **Test and dev.** A developer wants to run a transformation
   pipeline against realistic data. They don't need 4 billion rows
   to validate a `JOIN`.
2. **ML training.** Most models are not better after 100k rows.
   Pull a sample, train locally, ship the model.
3. **Ad-hoc exploration.** A data scientist wants to look at the
   shape of the data without scanning the whole table.

In each case, a *statistically valid* sample is what you want. The
wrong way is `LIMIT 1000` — that returns the first 1000 rows in
the table's natural order, which is almost always correlated with
insertion time, not random with respect to your features.

### What "representative" means

A sample is representative if, for the features you care about, the
sample's distribution is close to the full table's. Concretely:

- If the full table is 50% `region='EU'` / 50% `region='NA'`, a
  1% sample should also be roughly 50/50.
- If the full table's `amount` is uniform on `[0, 1000]`, the
  sample's `amount` distribution should look the same.

Snowflake's `SAMPLE` operators give you that statistical property
for free. The next lecture covers the three flavors.

### Sample size intuition

A common rule of thumb:

- **1,000 rows** — enough to validate a `SELECT` or a `JOIN`
  with reasonable confidence.
- **100,000 rows** — enough for most ML training; covers most
  categorical combinations.
- **1% of N** — a typical *proportional* sample. For a 1B-row
  table, that's 10M rows.

Pick the smallest sample that gives you the confidence you need.
Sampling is about saving compute and your own time, not maximizing
"more data".

### When sampling is the wrong tool

- **Exact counts.** A `SELECT COUNT(*)` against a sample will
  *estimate* the total — usually within a few percent, but never
  exact. Use sampling for shape, not for ground truth.
- **Aggregations across the full table.** `SUM(amount)` over a
  sample is an estimate, not a real number. If you need a real
  number, scan the full table.
- **Row-level joins with many-to-many.** A sample can dramatically
  underestimate fan-out; be careful with graph-shaped data.

## Hands-on

```sql
-- The wrong way: LIMIT returns the first 1000 rows in natural order
SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS LIMIT 1000;

-- The right way: SAMPLE returns a random 1000 rows
SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS SAMPLE (1000 ROWS);
```

`SAMPLE` is the keyword we'll use in the next lecture.

## Key takeaways

- Sample for test/dev, ML training, and ad-hoc exploration.
- `LIMIT N` is not sampling — it's the first N rows.
- A 1,000-row sample is enough for most validation tasks.
- Use sampling for shape, not for exact aggregations.

## What's next

L134 covers the three sampling primitives: `SAMPLE`,
`SAMPLE BERNOULLI`, and `SAMPLE SYSTEM`.