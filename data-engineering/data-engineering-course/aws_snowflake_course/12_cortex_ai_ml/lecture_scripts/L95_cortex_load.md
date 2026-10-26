---
l_id: L95
title: Hands-on: Load The Data
duration: "8:00"
prereqs: ["L94 - Hands-on: Overview Of Scenario"]
---

# L95 — Hands-on: Load The Data

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Section:** 12 — Cortex AI & Machine Learning
> **Duration:** 8:00

## Prereqs

A role with `CREATE DATABASE`, `CREATE WAREHOUSE`, `USAGE` on
`SNOWFLAKE.CORTEX`, and access to a public S3 bucket with the
sample review data.

## Lecture

In this lecture we lay the foundation for the next five: the
database, the schemas, the warehouse, and the `customer_reviews`
table populated with the demo dataset.

### Step 1 — Database + schemas

```sql
CREATE DATABASE IF NOT EXISTS ai_demo;
USE DATABASE ai_demo;

CREATE SCHEMA IF NOT EXISTS raw;        -- landing table
CREATE SCHEMA IF NOT EXISTS analytics;  -- scored views
CREATE SCHEMA IF NOT EXISTS ml;         -- notebooks + models
CREATE SCHEMA IF NOT EXISTS app;        -- streamlit apps
```

### Step 2 — Warehouse

```sql
CREATE OR REPLACE WAREHOUSE ai_demo_wh
  WITH WAREHOUSE_SIZE = 'SMALL'
       AUTO_SUSPEND   = 60
       AUTO_RESUME    = TRUE
       INITIALLY_SUSPENDED = TRUE;
USE WAREHOUSE ai_demo_wh;
```

A small warehouse is enough; Cortex is the heavy compute, not us.

### Step 3 — Stage + file format

```sql
USE SCHEMA raw;

CREATE OR REPLACE FILE FORMAT ff_json
  TYPE = JSON
  STRIP_OUTER_ARRAY = TRUE;

CREATE OR REPLACE STAGE reviews_stage
  URL = 's3://snowflake-course-demo/customer-reviews/'
  FILE_FORMAT = ff_json;
```

The bucket is public and read-only. In a real pipeline you'd put
your own data here and use a storage integration.

### Step 4 — Table

```sql
CREATE OR REPLACE TABLE raw.customer_reviews (
  review_id    NUMBER      AUTOINCREMENT,
  customer_id  NUMBER,
  review_date  DATE,
  review_text  TEXT,
  language     TEXT,
  product      TEXT,
  image_url    TEXT
);
```

### Step 5 — Load

```sql
COPY INTO raw.customer_reviews
  (customer_id, review_date, review_text, language, product, image_url)
FROM (
  SELECT $1:customer_id::NUMBER,
         $1:review_date::DATE,
         $1:review_text::TEXT,
         $1:language::TEXT,
         $1:product::TEXT,
         $1:image_url::TEXT
  FROM @raw.reviews_stage/reviews_2024.json
)
FILE_FORMAT = (FORMAT_NAME = 'ff_json')
ON_ERROR = 'CONTINUE';

-- Quick sanity
SELECT COUNT(*), MIN(review_date), MAX(review_date)
FROM raw.customer_reviews;
```

### Step 6 — Convenience view

```sql
CREATE OR REPLACE VIEW raw.v_customer_reviews AS
SELECT review_id, customer_id, review_date, review_text, language, product, image_url
FROM raw.customer_reviews;
```

Views are the contract — every downstream component (Text AI,
LLM function, Media AI, Cortex Search) reads from
`raw.v_customer_reviews`, never from the base table. That way you
can swap the source for a streaming pipe later without rewriting
any of the AI code.

### Step 7 — Sample rows

```sql
SELECT * FROM raw.v_customer_reviews ORDER BY review_date DESC LIMIT 5;
```

You should see reviews in multiple languages, with a few rows
having a populated `image_url`.

## Key takeaways

- Three schemas (`raw`, `analytics`, `ml`, `app`) is enough for
  the whole scenario.
- The view `raw.v_customer_reviews` is the contract every
  downstream tool reads.
- Auto-suspend aggressively; Cortex calls are serverless, so the
  warehouse is mostly idle.

## What's next

In **L96 — Hands-on: Text AI** we add `SENTIMENT`, `CLASSIFY`,
and `TRANSLATE` to the pipeline and materialize a scored view.
