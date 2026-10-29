# Lesson 6 — Quiz: AI on Cloud Platforms

> **Type:** Quiz · Module 7 · AI on Cloud Platforms
> Self-check on the five cloud platforms. Answers at the bottom.

---

## Section A — Conceptual

**Q1.** Which cloud has the **broadest** foundation-model catalogue through a managed API?
- A) AWS Bedrock
- B) Vertex AI
- C) Azure OpenAI
- D) All roughly equivalent

**Q2.** Which platform lets you call an LLM **directly from SQL** without ETL?
- A) AWS Bedrock
- B) Databricks AI Functions / Cortex COMPLETE
- C) SageMaker Endpoints
- D) None — you must move data

**Q3.** Which platform's vector DB is **Delta-native** (embeddings live in the lake)?
- A) AWS OpenSearch
- B) Vertex AI Vector Search
- C) Databricks Mosaic AI Vector Search
- D) Pinecone

**Q4.** Azure's **Provisioned Throughput Units (PTUs)** are best for:
- A) Spiky, unpredictable traffic
- B) Steady, high-volume traffic
- C) Cost minimisation at any load
- D) Free tier usage

**Q5.** The cheapest LLM inference at scale in 2026 is roughly:
- A) GPT-4o on Azure
- B) Claude Opus on Bedrock
- C) Gemini 1.5 Flash on Vertex
- D) DBRX on Databricks

**Q6.** Document AI (GCP), Textract (AWS), and Document Intelligence (Azure) primarily serve:
- A) Real-time fraud detection
- B) Unstructured document parsing (PDF / OCR / tables)
- C) Feature store serving
- D) Reinforcement learning

**Q7.** The "AI inside the warehouse" pattern (AI in the same compute as your data) is most associated with:
- A) AWS + Glue
- B) BigQuery ML / Snowflake Cortex / Databricks AI Functions
- C) SageMaker
- D) Vertex AI Workbench

**Q8.** Snowflake's Cortex Search service primarily provides:
- A) Web search
- B) Managed RAG retrieval (indexing + querying) over your data
- C) Public LLM training
- D) Search engine optimisation

---

## Section B — Scenario

**Q9.** You're a Snowflake shop with 50M rows of support tickets in `support.tickets`. You want to classify each ticket and embed it for a semantic-search RAG bot. List the Cortex functions you'd use and the architecture.

**Q10.** You're a Databricks shop with Delta Lake + MLflow + Unity Catalog. You're building a real-time recommender. List 4 Databricks-managed components you'd use, and why each.

**Q11.** A regulated bank on Azure needs a GPT-4o RAG with audit trail, VNet isolation, and predictable cost. List 3 Azure-specific design choices.

---

## Section C — Practical

**Q12.** Write a Cortex SQL query that classifies each row of `feedback.text` into one of `bug`, `feature_request`, or `praise`, and writes the result to `feedback.classified`.

**Q13.** Sketch the AWS architecture for a 10M-vector RAG over 5M PDFs in S3, including Textract, Bedrock, and OpenSearch.

**Q14.** Describe how you'd migrate a Bedrock RAG to Vertex AI without changing the application code (porting strategy).

---

## Section D — Open

**Q15.** Pick a cloud AI service you've used. What surprised you about it (good or bad)?

---

## Answer Key

<details>
<summary>A1</summary>

**A** — Bedrock has Anthropic, Meta, Mistral, Amazon, Cohere, Stability — widest managed catalogue. Vertex and Azure are competitive but slightly narrower.
</details>

<details>
<summary>A2</summary>

**B** — Databricks AI Functions (`ai_query`, `ai_classify`) and Snowflake Cortex COMPLETE both let you call an LLM from SQL directly, without ETLing data out.
</details>

<details>
<summary>A3</summary>

**C** — Mosaic AI Vector Search indexes Delta tables directly. Embeddings live in Delta, governed by Unity Catalog. OpenSearch / Vertex Vector Search are separate clusters.
</details>

<details>
<summary>A4</summary>

**B** — PTUs are reserved capacity, ~30–50% cheaper than PAYG for steady load. Spiky load wastes the reserved capacity.
</details>

<details>
<summary>A5</summary>

**C** — Gemini 1.5 Flash on Vertex is roughly $0.075/M input tokens, ~50× cheaper than GPT-4o or Claude Opus. Best for high-volume DE workloads.
</details>

<details>
<summary>A6</summary>

**B** — These are document AI services (OCR, tables, forms, layout). They don't do fraud, feature serving, or RL.
</details>

<details>
<summary>A7</summary>

**B** — BigQuery ML, Snowflake Cortex, and Databricks AI Functions all keep data inside the warehouse / lake. AWS + Glue requires Glue→Bedrock ETL or external API calls.
</details>

<details>
<summary>A8</summary>

**B** — Cortex Search is a managed retrieval service over your Snowflake data. It does indexing + querying and pairs with Cortex COMPLETE for RAG.
</details>

<details>
<summary>A9</summary>

A model answer:

```sql
-- 1. Embed tickets for semantic search
CREATE TABLE support.tickets_embedded AS
SELECT
  ticket_id,
  text,
  SNOWFLAKE.CORTEX.EMBED_TEXT_1024('e5-base-v2', text) AS embedding
FROM support.tickets;

-- 2. Classify tickets
CREATE TABLE support.tickets_classified AS
SELECT
  ticket_id,
  text,
  SNOWFLAKE.CORTEX.CLASSIFY_TEXT(
    text,
    ARRAY_CONSTRUCT('billing', 'bug', 'feature_request', 'praise', 'other')
  ) AS category
FROM support.tickets;

-- 3. Create a Cortex Search service for RAG
CREATE CORTEX SEARCH SERVICE support.tickets_search
ON text
ATTRIBUTES ticket_id, category
WAREHOUSE = cortex_wh
TARGET_LAG = '1 hour'
AS (
  SELECT ticket_id, text, category FROM support.tickets
);
```

For RAG: app calls Cortex Search → top-k chunks → Cortex COMPLETE → answer with citations. All under Snowflake RBAC + row access policy.
</details>

<details>
<summary>A10</summary>

A model answer:

1. **Databricks Vector Search** — embeddings indexed from the Delta table; queries return top-k with metadata filters; Unity Catalog governs.
2. **Feature Store** — offline features in Delta, online tables for sub-50ms serving, point-in-time joins for training.
3. **Mosaic AI Model Serving** — host the recommender on a serverless endpoint; auto-scales with traffic.
4. **DLT (Delta Live Tables)** — streaming ingest + feature engineering with declarative pipelines; quality expectations enforced.

All four are governed by Unity Catalog; lineage tracks raw → features → embeddings → model.
</details>

<details>
<summary>A11</summary>

A model answer:

1. **Azure OpenAI Service with PTUs** — same GPT-4o models, but reserved capacity for predictable cost. Also: VNet integration for private endpoints.
2. **AI Search with private endpoint + customer-managed keys** — vector index lives in your VNet, encryption keys you control.
3. **PTU provisioning matched to expected QPS** — buy capacity for steady-state, fall back to PAYG for spikes.
4. **Content Safety + Azure Policy** — outbound prompts scanned, blocked categories configured, audit log integrated with Sentinel / SIEM.
5. **AI Foundry for prompt + version management** — every prompt in one place, every deployment auditable.
</details>

<details>
<summary>A12</summary>

A model answer:

```sql
CREATE OR REPLACE TABLE feedback.classified AS
SELECT
  id,
  text,
  user_id,
  created_at,
  SNOWFLAKE.CORTEX.CLASSIFY_TEXT(
    text,
    ARRAY_CONSTRUCT('bug', 'feature_request', 'praise')
  ) AS classification,
  CURRENT_TIMESTAMP() AS classified_at
FROM feedback.raw;
```

Or, if you want to keep the original table and add a column:

```sql
ALTER TABLE feedback.raw ADD COLUMN classification VARIANT;

UPDATE feedback.raw
SET classification = SNOWFLAKE.CORTEX.CLASSIFY_TEXT(
    text,
    ARRAY_CONSTRUCT('bug', 'feature_request', 'praise')
);
```

For repeated runs, wrap as a Snowflake Task on a schedule.
</details>

<details>
<summary>A13</summary>

A model answer:

```
   S3 (5M PDFs)
        │
        ▼
   Step Functions / Glue (orchestration)
        │
        ▼
   Textract (OCR + tables + forms)
        │
        ▼
   S3 (parsed text + tables as Parquet)
        │
        ▼
   Lambda / Glue (chunk)
        │
        ▼
   Bedrock Titan Embeddings (1024-dim)
        │
        ▼
   OpenSearch k-NN index (10M vectors)
        │
        ▼
   Bedrock (Claude Haiku) → answer with citations
        │
        ▼
   API Gateway → client
```

Cost drivers: Textract ($1.50/1000 pages = $7500 one-shot for 5M pages), Titan Embeddings (~$1000 for 10M chunks), OpenSearch (~$3000/mo for 10M vectors managed), Bedrock per query.
</details>

<details>
<summary>A14</summary>

A model answer:

The cleanest portable RAG uses **a vendor-agnostic layer**: an internal `LLMClient` and `VectorClient` interface, with cloud-specific implementations behind them.

```python
class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str, **kw) -> str: ...

class BedrockLLM(LLMClient): ...
class VertexLLM(LLMClient): ...

# App code uses LLMClient. Swap implementations via config.
```

To migrate Bedrock → Vertex:
1. Replace `BedrockLLM` with `VertexLLM` (both implement `complete`).
2. Re-embed KB with Vertex Text Embeddings (different dim → re-index).
3. Re-point OpenSearch at Vertex Vector Search (or keep OpenSearch).
4. Re-run eval set, compare faithfulness / cost / latency.
5. Cut over with feature flag per tenant.
6. Decommission Bedrock.

The hardest part is usually re-embedding at scale + re-validating citations.
</details>

<details>
<summary>A15</summary>

This is a personal reflection. A useful prompt to focus on: **what surprised you about the model's behaviour, the cost, the latency, the developer experience, or the integration with your existing data stack?**

Common surprises:
- The model is more verbose than expected (cost goes up)
- Vector search is faster than expected at billion-scale (good surprise)
- "Managed" still requires you to handle quota, throttling, retries
- The eval set you built for one model doesn't transfer cleanly to another

</details>

---

*End of Module 7. Move to [Module 8 — AI DE System Design](../08-ai-system-design/README.md).*