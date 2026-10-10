# Assignment 2 — Cortex Search + Streamlit-in-Snowflake Review App

> **Duration:** 3 hours.  Combines sections 6, 12, 20.

## Goal

Stand up an internal RAG-style app that lets a non-technical user
ask *"Which snowboard reviews mention edge delamination?"* and get
grounded answers from a real `reviews` table — all inside Snowflake,
no data ever leaves the account.

## Steps

1. Land a `CORTEX_REVIEWS` table (VARIANT) with at least 1 000 reviews
   spanning ≥ 3 product categories.
2. Build a `RAW_REVIEWS_TYPED` view with `:` navigation to expose
   `product`, `rating`, `body` columns.
3. Create a `CORTEX SEARCH SERVICE` over `body` with a semantic model
   hinting the `product` column as a filter.
4. Build a Streamlit-in-Snowflake app that:
   - shows a chat input,
   - calls `CORTEX.SEARCH()` with the user's question,
   - passes the top-K hits to `CORTEX.COMPLETE()` as context,
   - renders the answer + the source snippets.
5. Add a Cortex `SENTIMENT` call that colour-codes each snippet green/red.
6. Save the app via the Snowflake CLI (`snow streamlit deploy`).

## Deliverable

A PR that adds:
- `12_cortex_ai_ml/code/cortex_ai_demo.sql` (extended with a Search service)
- `20_extra_topics/code/create_streamlit_app.py` (the Streamlit app)
- `tests/test_streamlit_app.py` (≥ 5 tests, mocking `snowflake.connector`)
- A 60-second screen recording of the chat working in the Snowflake UI.

## Bonus

- Add a **tag-based masking policy** so non-PII roles cannot see the
  customer's email in the snippets.
- Add a **task** that re-ranks the index every 15 minutes based on
  feedback (👍 / 👎) the user clicks in the UI.
- Add a **secure view** over the reviews that the app reads from,
  so the Search service can be exposed as a Share to a partner account.

## Author

Prem Vishnoi <pvishnoi@avilx.com>
