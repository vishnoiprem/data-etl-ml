---
l_id: L96
title: Hands-on: Text AI
duration: "9:00"
prereqs: ["L95 - Hands-on: Load The Data"]
---

# L96 — Hands-on: Text AI

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Section:** 12 — Cortex AI & Machine Learning
> **Duration:** 9:00

## Prereqs

`raw.customer_reviews` is loaded (L95). Your role has `USAGE` on
`SNOWFLAKE.CORTEX`.

## Lecture

This lecture puts three Text AI functions in front of the dataset
and materializes the **scored view** everything else will read.

### Step 1 — Probe on a sample

Always start with `LIMIT 5`. You want to see the model output
shape before you commit to a view.

```sql
SELECT review_id,
       review_text,
       SNOWFLAKE.CORTEX.SENTIMENT(review_text)               AS sentiment,
       SNOWFLAKE.CORTEX.TRANSLATE(review_text, 'auto', 'en') AS english_text
FROM raw.v_customer_reviews
LIMIT 5;
```

If `SENTIMENT` errors, you may not have `USAGE` on
`SNOWFLAKE.CORTEX`. If `TRANSLATE` errors, the model isn't in your
region — `SHOW FUNCTIONS IN SCHEMA SNOWFLAKE.CORTEX;` to check.

### Step 2 — Add a coarse-grained label

```sql
SELECT review_id,
       SNOWFLAKE.CORTEX.SENTIMENT(review_text) AS sentiment,
       CASE
         WHEN SNOWFLAKE.CORTEX.SENTIMENT(review_text) >  0.3 THEN 'POSITIVE'
         WHEN SNOWFLAKE.CORTEX.SENTIMENT(review_text) < -0.3 THEN 'NEGATIVE'
         ELSE 'NEUTRAL'
       END AS sentiment_label
FROM raw.v_customer_reviews
LIMIT 5;
```

You could push the `CASE` into a SQL UDF, but the cost is the
same (two sentiment calls per row) and a single expression is
easier to read.

### Step 3 — Classify with a custom label set

```sql
SELECT review_id,
       SNOWFLAKE.CORTEX.CLASSIFY(
         review_text,
         ['COMPLAINT', 'PRAISE', 'QUESTION', 'BUG_REPORT', 'OTHER']
       ) AS label
FROM raw.v_customer_reviews
WHERE language = 'en'
LIMIT 5;
```

`CLASSIFY` returns a JSON object with the predicted label and
confidence. Parse it as needed:

```sql
SELECT review_id,
       SNOWFLAKE.CORTEX.CLASSIFY(
         review_text,
         ['COMPLAINT', 'PRAISE', 'QUESTION', 'BUG_REPORT', 'OTHER']
       ):label::STRING AS label,
       SNOWFLAKE.CORTEX.CLASSIFY(
         review_text,
         ['COMPLAINT', 'PRAISE', 'QUESTION', 'BUG_REPORT', 'OTHER']
       ):confidence::FLOAT AS confidence
FROM raw.v_customer_reviews
WHERE language = 'en'
LIMIT 5;
```

### Step 4 — Materialize the scored view

```sql
USE SCHEMA analytics;

CREATE OR REPLACE VIEW scored.customer_reviews AS
SELECT
  r.review_id,
  r.customer_id,
  r.review_date,
  r.product,
  r.language,
  r.review_text,
  r.image_url,
  SNOWFLAKE.CORTEX.SENTIMENT(r.review_text) AS sentiment,
  CASE
    WHEN SNOWFLAKE.CORTEX.SENTIMENT(r.review_text) >  0.3 THEN 'POSITIVE'
    WHEN SNOWFLAKE.CORTEX.SENTIMENT(r.review_text) < -0.3 THEN 'NEGATIVE'
    ELSE 'NEUTRAL'
  END AS sentiment_label,
  SNOWFLAKE.CORTEX.TRANSLATE(r.review_text, 'auto', 'en') AS english_text
FROM raw.v_customer_reviews r;
```

This view is **recomputed on every query** — Cortex functions are
not materialized automatically. For a stable scored table, use a
Task to refresh on a schedule (next lecture).

### Step 5 — Cost guardrail

```sql
-- Estimate before scaling
SELECT COUNT(*),
       COUNT(*) * 0.0003 AS est_cost_usd  -- illustrative per-row
FROM raw.v_customer_reviews;
```

For tens of thousands of rows, this is cents. For tens of millions,
plan a Task + checkpointing.

## Key takeaways

- Always preview with `LIMIT 5` to confirm the model output shape.
- The scored view is the contract: one place where all Text AI
  results land.
- `SENTIMENT`, `CLASSIFY`, `TRANSLATE` are the three workhorses;
  anything more exotic goes to `COMPLETE` (next lecture).

## What's next

In **L97 — Hands-on: LLM Function** we use `COMPLETE` to draft a
support-reply per review and add it to the scored view.
