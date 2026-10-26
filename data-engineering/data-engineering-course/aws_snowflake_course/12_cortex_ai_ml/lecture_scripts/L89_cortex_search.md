---
l_id: L89
title: Cortex Search
duration: "8:00"
prereqs: ["L88 - AI SQL Functions"]
---

# L89 — Cortex Search

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 12 — Cortex AI & Machine Learning
> **Duration:** 8:00

## Prereqs

A table that has a text column you want to make searchable. You
should be comfortable with `CREATE TABLE` and basic role grants.

## Lecture

Cortex Search is **managed, serverless hybrid search**. You point
it at a table column, it builds a keyword index (BM25) + a vector
index, and exposes a single endpoint that returns the most
relevant rows. You query from SQL or from a REST API.

### When Cortex Search is the right answer

- "Find me the docs that talk about refund policy."
- "What tickets in the last 30 days mention this product?"
- "Search our knowledge base from inside a Streamlit app."

It's not a replacement for ElasticSearch at petabyte scale, but for
the "search inside Snowflake" use case it removes 90% of the
plumbing.

### Step 1 — create a search service

```sql
CREATE OR REPLACE CORTEX SEARCH SERVICE support_kb_search
  ON chunk_text
  ATTRIBUTES title, url
  WAREHOUSE = compute_wh
  TARGET_LAG = '1 hour'
  AS (
    SELECT chunk_text,
           title,
           url
    FROM raw.support_kb_chunks
  );
```

- `ON chunk_text` — the column to index.
- `ATTRIBUTES` — extra columns to return without re-querying.
- `TARGET_LAG` — how stale the index is allowed to be. `'1 hour'`
  is the sweet spot for most pipelines.
- The `AS (...)` is the **materialization query** — Cortex runs it
  on the schedule you set, so the index sees new rows automatically.

### Step 2 — query from SQL

```sql
SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
  'support_kb_search',
  'how do I get a refund?',
  LIMIT => 5
) AS results;
```

Returns a JSON value with the top 5 hits and their `chunk_text`,
`title`, `url`.

### Step 3 — query from a REST API

```sql
-- Get a service URL and a search token
DESC CORTEX SEARCH SERVICE support_kb_search;
```

The REST endpoint is:

```
POST https://<account>.snowflakecomputing.com/api/v2/databases/<db>/schemas/<schema>/cortex-search-services/<svc>:query
Authorization: Bearer <PAT or OAuth token>
Content-Type: application/json

{
  "query": "refund policy",
  "columns": ["chunk_text", "title", "url"],
  "limit": 5
}
```

This is what your app server (a Streamlit app, a Node service, a
Lambda) calls.

### How the hybrid search works

- The query is run through both a **BM25 keyword index** and a
  **vector index** (768-dim embedding under the hood).
- The two rankings are fused (Reciprocal Rank Fusion by default).
- You get the best of both worlds: precise keyword matches for
  product names, semantic matches for natural-language questions.

### Operational notes

- `TARGET_LAG` controls freshness vs cost. `1 minute` is fine for
  small indexes; `1 hour` is cheaper for millions of rows.
- Drop and recreate the service if you change the schema of the
  underlying table. There is no `ALTER ... INDEX REBUILD`.
- Monitor with `SHOW CORTEX SEARCH SERVICES;` and the
  `CORTEX_SEARCH_DAILY_USAGE_HISTORY` view.

## Key takeaways

- `CREATE CORTEX SEARCH SERVICE` builds a managed hybrid index.
- Query from SQL (`SEARCH_PREVIEW`) or REST.
- `TARGET_LAG` controls freshness; `ATTRIBUTES` controls what
  comes back without re-querying.

## What's next

In **L90 — Cortex Analyst** we go from "search my docs" to "ask a
question in English, get SQL back".
