# Section 19 — Data Sampling

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Lectures:** L133–L135
> **Duration:** ~16 min

By section 18 you've learned how to keep data safe (Time Travel,
Fail Safe, table types), how to copy it for free (zero-copy
cloning), and how to share it without copying it (data sharing).
The last operational technique in the published curriculum is
**data sampling** — the ability to pull a representative subset of
a huge table without scanning all of it.

Section 19 is short but useful. We start with **Why data sampling?**
(L133) — the use cases (test/dev, ML training, prototyping, smoke
tests) and why naive `LIMIT 1000` queries aren't statistically
valid. **Methods of data sampling** (L134) introduces Snowflake's
three sampling primitives: `SAMPLE`, `SAMPLE BERNOULLI`, and
`SAMPLE SYSTEM` (`TABLESAMPLE`). **Sampling data: Hands-on** (L135)
puts it all together on a TPC-H dataset.

| L# | Title | Min |
|---|---|---|
| L133 | Why data sampling? | 5:00 |
| L134 | Methods of data sampling | 5:00 |
| L135 | Sampling data: Hands-on | 6:00 |

## Key concepts you'll need later

- **`SAMPLE`** — Snowflake's row-level sampling function. Takes a
  percentage or row count.
- **`SAMPLE BERNOULLI`** — per-row Bernoulli sampling. Each row is
  included with probability `p`. Strictly randomized.
- **`SAMPLE SYSTEM`** — block-level sampling. Each *block* of rows
  is included with probability `p`. Faster, less uniform.
- **`TABLESAMPLE`** — the ANSI SQL equivalent. Same semantics as
  `SAMPLE SYSTEM`; useful for portability.
- **Stratified sampling** — Snowflake doesn't have a single
  keyword; you compose `SAMPLE` inside a `QUALIFY` / partition
  expression to keep per-group counts balanced.

## What comes next

Section 20 is the **extra topics** catch-all: Tasks, Streams,
Materialized Views, Data Masking, Roles deep-dive, BI Tools, Best
Practices, and Bonus lectures. It's the largest section in the
course.