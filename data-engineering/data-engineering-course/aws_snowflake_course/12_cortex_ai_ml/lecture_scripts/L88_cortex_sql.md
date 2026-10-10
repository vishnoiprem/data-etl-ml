---
l_id: L88
title: AI SQL Functions
duration: "8:30"
prereqs: ["L87 - Snowflake Cortex AI - Overview"]
---

# L88 — AI SQL Functions

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 12 — Cortex AI & Machine Learning
> **Duration:** 8:30

## Prereqs

You have a role with `USAGE` on `SNOWFLAKE.CORTEX` (most modern
Snowflake accounts do; if not, ask your `ACCOUNTADMIN` to grant the
database role `CORTEX_USER` to your user).

## Lecture

The AI SQL functions are the most-used part of Cortex because they
fit into queries you already write. No new pipeline, no new
infrastructure, no data movement.

### The three you will reach for first

#### SENTIMENT

Returns a sentiment score in `[-1, 1]` for a piece of text.

```sql
SELECT review_id,
       review_text,
       SNOWFLAKE.CORTEX.SENTIMENT(review_text) AS score
FROM raw.customer_reviews
LIMIT 10;
```

- `score > 0.3` → broadly positive.
- `-0.3 < score < 0.3` → neutral / mixed.
- `score < -0.3` → broadly negative.

#### SUMMARIZE

Condenses a long text into a 1–3 sentence summary.

```sql
SELECT call_id,
       transcript,
       SNOWFLAKE.CORTEX.SUMMARIZE(transcript) AS summary
FROM raw.support_calls;
```

#### TRANSLATE

Translates between supported language pairs.

```sql
SELECT review_id,
       SNOWFLAKE.CORTEX.TRANSLATE(
         review_text,
         source_language => 'auto',
         target_language => 'en'
       ) AS english_review
FROM raw.customer_reviews
WHERE language <> 'en';
```

`source_language => 'auto'` lets the model detect the input
language — handy when your source data isn't tagged.

### Other useful functions

| Function | What it does |
|---|---|
| `EXTRACT_ANSWER(text, question)` | Pulls a snippet that answers a question from a passage. |
| `CLASSIFY(text, categories)` | Returns one of N labels for a row. |
| `COMPLETE(prompt, model => '...')` | Generic LLM call. Use when the canned functions don't fit. |
| `EMBED_TEXT_768(text)` | Vector embedding (768-dim). |
| `PARSE_DOCUMENT(...)` | Extracts text from PDFs/images stored in a stage. |

### The "LLM function" pattern

`COMPLETE` is the escape hatch:

```sql
SELECT SNOWFLAKE.CORTEX.COMPLETE(
  'claude-3-5-sonnet',
  [
    {'role': 'system', 'content': 'You are a strict JSON classifier.'},
    {'role': 'user',   'content': 'Classify: ' || review_text}
  ],
  {'response_format': {'type': 'json_object'}}
) AS llm_response
FROM raw.customer_reviews
LIMIT 5;
```

Use `COMPLETE` when you need structured output, a custom prompt,
or a specific model the higher-level functions don't expose.

### Cost control patterns

- **Filter first.** Don't send 10M rows if you only need 1,000.
- **Project the column.** Send `LEFT(text, 4000)` rather than the
  full 50,000-character blob.
- **Batch with `COMPLETE`.** If you have a custom prompt, batch
  rows into one call to amortize the prompt overhead.
- **Cache.** If the same text shows up across rows, dedupe first.

### Gotchas

- Model availability varies by region — `SHOW FUNCTIONS IN
  SCHEMA SNOWFLAKE.CORTEX;` to see what's exposed in your account.
- The functions are **synchronous per row** in a `SELECT`; for very
  large tables, switch to a Task that processes in chunks so you
  can checkpoint.
- All function calls are logged and billable. Always preview the
  cost on `LIMIT 100` first.

## Key takeaways

- `SENTIMENT`, `SUMMARIZE`, `TRANSLATE` cover most text-AI needs.
- `COMPLETE(prompt, model)` is the generic LLM call.
- Cost control: filter, project, batch, cache.

## What's next

In **L89 — Cortex Search** we move from one-shot text AI to managed
hybrid search over a column of documents.
