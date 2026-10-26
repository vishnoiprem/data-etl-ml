---
l_id: L98
title: Hands-on: Media AI Analytics
duration: "8:00"
prereqs: ["L97 - Hands-on: LLM Function"]
---

# L98 — Hands-on: Media AI Analytics

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Section:** 12 — Cortex AI & Machine Learning
> **Duration:** 8:00

## Prereqs

The scored view from L97, with `image_url` populated for a few
rows.

## Lecture

Some of our reviews include an attached image — a photo of a
damaged product, a screenshot of a buggy screen, a receipt. We
want labels and captions for those images, generated inside
Snowflake so we don't ship the bytes anywhere.

### Two functions for two jobs

| Function | Input | Output |
|---|---|---|
| `CLASSIFY_IMAGE` | Image URL, candidate labels | Best label + confidence |
| `PARSE_DOCUMENT` | Document URL, prompt | Structured JSON |
| `EXTRACT_ANSWER` | Document URL, question | Snippet answer |

### Step 1 — Classify a few images

```sql
SELECT review_id,
       image_url,
       SNOWFLAKE.CORTEX.CLASSIFY_IMAGE(
         image_url,
         ['DAMAGED_PACKAGE', 'BUG_SCREENSHOT', 'RECEIPT', 'PRODUCT_PHOTO', 'OTHER']
       ) AS classification
FROM raw.v_customer_reviews
WHERE image_url IS NOT NULL
LIMIT 5;
```

Returns a JSON object:

```json
{
  "label":       "DAMAGED_PACKAGE",
  "confidence":  0.92
}
```

### Step 2 — Parse a document (e.g. a receipt)

```sql
SELECT SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
  '@raw.receipts_stage/receipt_1234.pdf',
  {'mode': 'LAYOUT'}
) AS parsed;
```

`PARSE_DOCUMENT` returns the text content of the document. Combine
it with `EXTRACT_ANSWER` to get structured fields:

```sql
SELECT SNOWFLAKE.CORTEX.EXTRACT_ANSWER(
  parsed_text,
  'What is the total amount and the merchant name?'
) AS answer
FROM (
  SELECT SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
    '@raw.receipts_stage/receipt_1234.pdf',
    {'mode': 'LAYOUT'}
  ) AS parsed_text
);
```

### Step 3 — Add image classification to the scored view

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
    WHEN r.image_url IS NOT NULL THEN
      SNOWFLAKE.CORTEX.CLASSIFY_IMAGE(
        r.image_url,
        ['DAMAGED_PACKAGE', 'BUG_SCREENSHOT', 'RECEIPT', 'PRODUCT_PHOTO', 'OTHER']
      ):label::STRING
    ELSE NULL
  END AS image_label
FROM raw.v_customer_reviews r;
```

Only rows with an `image_url` are sent to `CLASSIFY_IMAGE` — you
pay nothing for the other 95% of the table.

### Step 4 — Surface in the scored view

```sql
SELECT review_id, product, sentiment_label, image_label
FROM analytics.scored.customer_reviews
WHERE image_label IS NOT NULL
ORDER BY review_date DESC
LIMIT 20;
```

You should see a healthy mix of `DAMAGED_PACKAGE`,
`BUG_SCREENSHOT`, `RECEIPT`, `PRODUCT_PHOTO`.

### Cost and limits

- Images must be reachable from Snowflake's egress allow-list
  (most public S3 / GCS URLs work; private buckets need a
  storage integration).
- Files over ~20 MB can be slow or rejected; downsize before
  you classify.
- Pricing is per image. For a 100K-image backlog, plan a Task.

## Key takeaways

- `CLASSIFY_IMAGE` returns the best label + confidence.
- `PARSE_DOCUMENT` + `EXTRACT_ANSWER` is the pattern for any
  text-on-image question (receipts, screenshots, contracts).
- The scored view carries `image_label` so the Streamlit app
  can render a single "image type" badge per row.

## What's next

In **L99 — Hands-on: Cortex Service** we expose all of this
through a Cortex Search service and a Streamlit app for human
triage.
