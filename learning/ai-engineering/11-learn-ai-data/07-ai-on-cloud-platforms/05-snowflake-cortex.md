# Lesson 5 — Snowflake Cortex

> **Type:** Article · Module 7 · AI on Cloud Platforms
> Cortex functions, Cortex Search, and the "AI inside the warehouse" pattern.

---

## The Snowflake Cortex stack for DEs

```
   SNOWFLAKE CORTEX SURFACE AREA (DE-RELEVANT)
   ──────────────────────────────────────────
   LLM FUNCTIONS         Cortex COMPLETE, SUMMARIZE, TRANSLATE,
                         EXTRACT_ANSWER, CLASSIFY_TEXT, SENTIMENT,
                         EMBED_TEXT_1024 (and other dims)

   VECTOR SEARCH         Cortex Search (managed RAG-ready service)
                         Native vector type + VECTOR_COSINE_SIMILARITY

   FINE-TUNING           Cortex Fine-tuning (serverless custom models)

   MODEL SERVING         Cortex model serving (LLMs, embeddings,
                         custom fine-tuned models)

   AGENTS                Cortex Agents (tool-use, multi-step)

   GOVERNANCE            Same Snowflake RBAC, row access policies,
                         masking policies — applied to embeddings + LLM calls

   PIPELINES             Snowflake Tasks / Streams / Dynamic Tables
                         + Airflow / dbt / external orchestrators
```

For data engineers, Cortex's unique value: **AI runs on the same compute as your warehouse**. No data movement. No separate vector DB. LLM calls go through your SQL.

---

## Cortex LLM functions — AI from SQL

```sql
-- COMPLETE: general chat completion
SELECT SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large2',
    'Summarise this customer complaint in one sentence: '
    || complaint_text
) AS summary
FROM complaints;

-- SUMMARIZE: short summary of long text
SELECT SNOWFLAKE.CORTEX.SUMMARIZE(article_text) AS summary
FROM articles;

-- CLASSIFY_TEXT: classify into categories
SELECT SNOWFLAKE.CORTEX.CLASSIFY_TEXT(
    feedback_text,
    ['bug', 'feature_request', 'praise', 'complaint']
) AS classification
FROM feedback;

-- EXTRACT_ANSWER: extract an answer from text
SELECT SNOWFLAKE.CORTEX.EXTRACT_ANSWER(
    policy_text,
    'What is the refund period?'
) AS answer
FROM policies;

-- TRANSLATE: language translation
SELECT SNOWFLAKE.CORTEX.TRANSLATE(
    feedback_text,
    'en', 'fr'
) AS french_text
FROM feedback;

-- EMBED_TEXT_1024: vector embeddings
SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_1024('e5-base-v2', product_text) AS embedding
FROM products;
```

The model catalogue includes **Mistral Large 2, Llama 3.x, Reka, Snowflake Arctic** (and via API: Claude, GPT). Serverless, pay per token, no infra.

---

## Cortex Search — managed RAG

Cortex Search is a **managed retrieval service** that pairs nicely with Cortex COMPLETE for RAG.

```sql
-- Create a Cortex Search service
CREATE CORTEX SEARCH SERVICE support_docs_search
ON doc_text
ATTRIBUTES doc_id, source_url, category
WAREHOUSE = compute_wh
TARGET_LAG = '1 hour'
AS (
  SELECT doc_text, doc_id, source_url, category
  FROM raw_support_docs
);
```

```python
# Query the search service + call an LLM
from snowflake.core import Root
from snowflake.snowpark.context import get_active_session

session = get_active_session()
root = Root(session)

svc = (root.databases["support"]
          .schemas["docs"]
          .cortex_search_services["support_docs_search"])

# Search
results = svc.search(
    query="How do I refund a Stripe payment?",
    columns=["doc_text", "doc_id", "source_url"],
    limit=5,
    filter={"@eq": {"category": "billing"}},
)
context = "\n\n".join([r["doc_text"] for r in results])

# LLM
prompt = f"Answer using only the sources below.\n\nSOURCES:\n{context}\n\nQUESTION: How do I refund a Stripe payment?"
answer = session.sql(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', '{prompt}') AS a").collect()[0]["A"]
```

| Strength | Weakness |
|---|---|
| Same Snowflake warehouse (no data movement) | Smaller model catalogue than Bedrock |
| Cortex Search handles ingest + retrieval | Newer, less mature than custom |
| RBAC + row access policies apply | Snowflake-only |

---

## Native vector type

Snowflake has a native **VECTOR** type for embeddings.

```sql
CREATE TABLE docs_with_embeddings (
    doc_id STRING,
    text STRING,
    embedding VECTOR(FLOAT, 1024),  -- native vector column
    metadata VARIANT
);

-- Vector similarity in SQL
SELECT doc_id,
       VECTOR_COSINE_SIMILARITY(
           embedding,
           SNOWFLAKE.CORTEX.EMBED_TEXT_1024('e5-base-v2', :query_text)
       ) AS similarity
FROM docs_with_embeddings
ORDER BY similarity DESC
LIMIT 10;
```

For do-it-yourself vector search, this is the low-friction option — embeddings live in your warehouse table, similarity is a SQL function, ACL applies.

---

## Cortex Fine-tuning

Serverless fine-tuning for custom models:

```sql
-- Create a fine-tuning run
CREATE SNOWFLAKE.ML.FINETUNE
    CUSTOM_MODEL = my_finetuned_llm
    FROM (SELECT prompt, completion FROM training_data)
    BASE_MODEL = 'mistral-large2';
```

For DE-adjacent workloads (custom classification, custom extraction), fine-tuning can be cheaper and more accurate than prompting at scale.

---

## Cortex Agents (tool use)

```python
# Cortex Agents: multi-step tool use within Snowflake
from snowflake.cortex.agent import Agent

agent = Agent(
    name="support_agent",
    llm="mistral-large2",
    tools=[
        {
            "name": "search_docs",
            "type": "cortex_search",
            "service_name": "support_docs_search",
        },
        {
            "name": "get_customer",
            "type": "function",
            "function": "support.public.get_customer(customer_id)",
        },
    ],
)

response = agent.run("What's the refund policy and what's the latest customer issue?")
```

For RAG-with-tools, Cortex Agents is the lowest-glue path inside Snowflake.

---

## The "AI in the warehouse" pattern

```
   ┌────────────────────────────────────────────────────────┐
   │  Snowflake AI (for warehouse shops)                    │
   │                                                        │
   │   raw data → Stages → Snowflake tables                │
   │       │                                                │
   │       ▼                                                │
   │   cleaned tables → Cortex EMBED_TEXT_*                  │
   │       │                                                │
   │       ▼                                                │
   │   VECTOR column → VECTOR_COSINE_SIMILARITY             │
   │       │                                                │
   │       ▼                                                │
   │   Cortex Search service (managed RAG)                  │
   │       │                                                │
   │       ▼                                                │
   │   Cortex COMPLETE / Agents (LLM answers)               │
   │                                                        │
   │   All under one RBAC + row access policy.              │
   │   All audit-logged via Snowflake's query history.      │
   └────────────────────────────────────────────────────────┘
```

The Snowflake pattern: **zero data movement, one ACL model, one governance story**.

---

## Cost modelling

```
   Per million events (typical Snowflake DE workload):
   ──────────────────────────────────────────────────
   Cortex COMPLETE (Mistral Large 2, 1M tokens):     $2
   Cortex EMBED_TEXT (1M tokens):                    $0.10
   Cortex Search service:                            ~$300/mo (warehouse)
   Fine-tuning (one-time, small dataset):            ~$50
   Vector similarity in SQL:                         ~$0 (compute)
   ──────────────────────────────────────────
   Total: ~$300/mo + per-call costs

   Caveat: warehouse cost dominates. A Cortex Search service
   running on a Medium warehouse 24/7 is the main line item.
```

---

## When to pick Cortex

```
   ┌─────────────────────────────────────────────────────┐
   │  Cortex wins when:                                   │
   │                                                     │
   │   - Your data is already in Snowflake                │
   │   - You want AI calls audit-logged in Snowflake     │
   │     query history (compliance)                      │
   │   - You want zero data movement                     │
   │   - You want SQL-first AI (data analysts, not devs)  │
   │                                                     │
   │  Cortex loses when:                                 │
   │                                                     │
   │   - You're not on Snowflake                          │
   │   - You need the absolute lowest inference cost     │
   │     (GCP Gemini Flash wins)                         │
   │   - You want the broadest model catalogue           │
   │     (Bedrock / Vertex)                              │
   │   - You're building high-QPS online vector search   │
   │     (Pinecone / Weaviate more tuned)                │
   └─────────────────────────────────────────────────────┘
```

---

## What Comes Next

> Lesson 6 — **Quiz: AI on Cloud Platforms** — self-check on the five cloud platforms.