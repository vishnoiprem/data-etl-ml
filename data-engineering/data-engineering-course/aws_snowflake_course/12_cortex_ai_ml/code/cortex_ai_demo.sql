-- ============================================================================
-- 12_cortex_ai_ml / cortex_ai_demo.sql
-- ----------------------------------------------------------------------------
-- Snowflake Cortex LLM functions (SENTIMENT, SUMMARIZE, TRANSLATE, EXTRACT)
-- applied to a small reviews table.  No model deployment, no GPU billing —
-- Cortex is serverless.
--
-- Lecture reference: "Cortex AI: SENTIMENT, SUMMARIZE, TRANSLATE" (Section 12, L02)
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

USE DATABASE SNOWFLAKE_DEMO;
USE SCHEMA GETTING_STARTED;

-- ── 1. A small reviews dataset to score ────────────────────────────────
CREATE OR REPLACE TABLE CORTEX_REVIEWS (
    review_id  NUMBER,
    product    VARCHAR(50),
    review     VARCHAR
);

INSERT INTO CORTEX_REVIEWS VALUES
  (1, 'snowboard',  'Absolutely love this board.  Carves like a dream and the bindings are bomber.'),
  (2, 'snowboard',  'The edges delaminated after two runs.  Customer service was slow to respond.'),
  (3, 'helmet',     'Fits well, warm, lightweight.  No complaints.'),
  (4, 'helmet',     'Too small, even after adjusting the dial.  Returning it.'),
  (5, 'goggles',    'Fogged up the entire day.  Anti-fog coating did nothing.');

-- ── 2. SENTIMENT — returns a category: POSITIVE / NEGATIVE / NEUTRAL ────
SELECT review_id, product, review,
       SNOWFLAKE.CORTEX.SENTIMENT(review)                      AS sentiment_score
FROM   CORTEX_REVIEWS
ORDER  BY review_id;

-- ── 3. SUMMARIZE — one-sentence TL;DR ────────────────────────────────
SELECT review_id,
       SNOWFLAKE.CORTEX.SUMMARIZE(review)                      AS summary
FROM   CORTEX_REVIEWS
ORDER  BY review_id;

-- ── 4. TRANSLATE — translate to Spanish ───────────────────────────────
SELECT review_id,
       SNOWFLAKE.CORTEX.TRANSLATE(review, 'es')                AS review_es
FROM   CORTEX_REVIEWS
ORDER  BY review_id;

-- ── 5. EXTRACT_ANSWER — question over an unstructured blob ────────────
SELECT SNOWFLAKE.CORTEX.EXTRACT_ANSWER(
           review,
           'What product problem is the customer describing?'
       )                                                       AS problem
FROM   CORTEX_REVIEWS
ORDER  BY review_id;

-- ── 6. CLASSIFY_TEXT — custom labels (e.g. complaint categories) ───────
SELECT review_id,
       SNOWFLAKE.CORTEX.CLASSIFY_TEXT(
           review,
           ['durability', 'fit', 'fog', 'service']
       )                                                       AS topic
FROM   CORTEX_REVIEWS
ORDER  BY review_id;

-- ── 7. Roll up sentiment by product ───────────────────────────────────
SELECT product,
       AVG(SNOWFLAKE.CORTEX.SENTIMENT(review))                  AS avg_sentiment,
       COUNT(*)                                                 AS n_reviews
FROM   CORTEX_REVIEWS
GROUP  BY product
ORDER  BY avg_sentiment DESC;
