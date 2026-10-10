---
l_id: L97
title: Hands-on: LLM Function
duration: "9:00"
prereqs: ["L96 - Hands-on: Text AI"]
---

# L97 — Hands-on: LLM Function

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Section:** 12 — Cortex AI & Machine Learning
> **Duration:** 9:00

## Prereqs

The scored view from L96.

## Lecture

`SENTIMENT`, `CLASSIFY`, and `TRANSLATE` cover 80% of text-AI
needs. The remaining 20% — structured replies, multi-step
reasoning, custom prompts — go through `COMPLETE`. In this
lecture we draft a support reply per review and persist it as a
new column on the scored view.

### Step 1 — Probe `COMPLETE` on one review

```sql
SELECT SNOWFLAKE.CORTEX.COMPLETE(
  'claude-3-5-sonnet',
  [
    {'role': 'system', 'content': 'You write concise, empathetic customer support replies in English.'},
    {'role': 'user',   'content': 'Customer review: ' || review_text}
  ],
  {'max_tokens': 200}
) AS draft_reply
FROM raw.v_customer_reviews
WHERE language = 'en'
LIMIT 3;
```

The response is a JSON object; `choices[0].message.content` is the
reply text.

### Step 2 — Parse the response

```sql
WITH r AS (
  SELECT review_id, review_text,
    SNOWFLAKE.CORTEX.COMPLETE(
      'claude-3-5-sonnet',
      [
        {'role': 'system', 'content': 'You write concise, empathetic customer support replies in English.'},
        {'role': 'user',   'content': 'Customer review: ' || review_text}
      ],
      {'max_tokens': 200}
    ) AS raw
  FROM raw.v_customer_reviews
  WHERE language = 'en'
  LIMIT 5
)
SELECT review_id,
       raw:choices[0].message.content::STRING AS draft_reply
FROM r;
```

The `::STRING` cast is the trick — without it you get the raw
JSON and the Streamlit app will have to parse it again.

### Step 3 — Add it to the scored view

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
  SNOWFLAKE.CORTEX.TRANSLATE(r.review_text, 'auto', 'en') AS english_text,
  CASE
    WHEN r.language = 'en' THEN
      SNOWFLAKE.CORTEX.COMPLETE(
        'claude-3-5-sonnet',
        [
          {'role': 'system', 'content': 'You write concise, empathetic customer support replies in English.'},
          {'role': 'user',   'content': 'Customer review: ' || r.review_text}
        ],
        {'max_tokens': 200}
      ):choices[0].message.content::STRING
    ELSE NULL
  END AS draft_reply
FROM raw.v_customer_reviews r;
```

Only the English reviews get a draft — the rest stay `NULL` until
we wire translation into the prompt.

### Step 4 — Force JSON when the downstream needs it

```sql
SELECT SNOWFLAKE.CORTEX.COMPLETE(
  'claude-3-5-sonnet',
  [
    {'role': 'system', 'content': 'Return JSON with keys: priority (LOW/MED/HIGH), category, draft_reply.'},
    {'role': 'user',   'content': 'Customer review: ' || review_text}
  ],
  {'response_format': {'type': 'json_object'}}
) AS raw
FROM raw.v_customer_reviews
WHERE language = 'en'
LIMIT 3;
```

`response_format: json_object` is the reliable way to get
structured output from any supported model.

### Step 5 — Materialize a scored *table* (optional)

The view recomputes Cortex on every query. If the Streamlit app
hits the view on every page load, you pay for that. A scored
**table** refreshed by a Task is cheaper at scale:

```sql
CREATE OR REPLACE TABLE analytics.scored.customer_reviews_tbl AS
SELECT * FROM analytics.scored.customer_reviews;

-- Later, a Task refreshes it
CREATE OR REPLACE TASK refresh_scored
  WAREHOUSE = ai_demo_wh
  SCHEDULE = '60 MINUTE'
AS
  CREATE OR REPLACE TABLE analytics.scored.customer_reviews_tbl AS
  SELECT * FROM analytics.scored.customer_reviews;
```

For the demo, the view is fine. For production, use the table.

## Key takeaways

- `COMPLETE` is the generic LLM call — use it when the canned
  functions don't fit.
- Parse the response with `raw:choices[0].message.content::STRING`.
- Use `response_format: json_object` for structured output.
- The view is fine for demos; the table is cheaper at scale.

## What's next

In **L98 — Hands-on: Media AI Analytics** we score the attached
images with `CLASSIFY_IMAGE` and `PARSE_DOCUMENT`.
