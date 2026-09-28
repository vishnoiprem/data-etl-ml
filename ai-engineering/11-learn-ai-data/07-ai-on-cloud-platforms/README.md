# Module 7 — AI on Cloud Platforms

> 6 lessons · AWS · GCP · Azure · Databricks · Snowflake Cortex
> Managed AI services and how they fit a data engineer's workflow.

---

## Lesson Index

| # | Lesson | Type | Notes |
|---|--------|------|-------|
| 1 | [AWS AI for DEs](./01-aws-ai-for-des.md) | Article | [Open](./01-aws-ai-for-des.md) |
| 2 | [GCP AI for DEs](./02-gcp-ai-for-des.md) | Article | [Open](./02-gcp-ai-for-des.md) |
| 3 | [Azure AI for DEs](./03-azure-ai-for-des.md) | Article | [Open](./03-azure-ai-for-des.md) |
| 4 | [Databricks AI](./04-databricks-ai.md) | Article | [Open](./04-databricks-ai.md) |
| 5 | [Snowflake Cortex](./05-snowflake-cortex.md) | Article | [Open](./05-snowflake-cortex.md) |
| 6 | [Quiz: AI on Cloud Platforms](./06-quiz-cloud.md) | Quiz | [Open](./06-quiz-cloud.md) |

---

## Module Outcomes

By the end of Module 7 you can:

1. **Navigate** the managed AI surface area on each major cloud.
2. **Pick** the right managed service for embeddings, vector search, model serving, and RAG.
3. **Reason** about cost, lock-in, and operational complexity for each platform.
4. **Wire** AI services into existing data pipelines (Bedrock, Vertex, Azure AI Foundry, Databricks AI Functions, Snowflake Cortex).
5. **Evaluate** build-vs-buy for vector DB and feature store on your cloud.

---

## The managed-AI map

```
   ┌──────────────────────────────────────────────────────────────────┐
   │                   CLOUD AI SURFACE AREA                           │
   ├─────────────┬──────────────┬───────────────┬────────────────────┤
   │             │  Embeddings  │  Vector DB    │  Model Serving     │
   ├─────────────┼──────────────┼───────────────┼────────────────────┤
   │  AWS        │ Bedrock      │ OpenSearch    │ Bedrock / SageMaker│
   │             │ Titan Embed  │ + k-NN        │ JumpStart / Custom │
   ├─────────────┼──────────────┼───────────────┼────────────────────┤
   │  GCP        │ Vertex AI    │ Vertex Matching│ Vertex AI         │
   │             │ Text Embed   │ Engine        │ Endpoints          │
   ├─────────────┼──────────────┼───────────────┼────────────────────┤
   │  Azure      │ Azure OpenAI │ Azure AI      │ Azure AI Foundry   │
   │             │              │ Search        │ / AKS              │
   ├─────────────┼──────────────┼───────────────┼────────────────────┤
   │  Databricks │ Mosaic AI    │ Vector Search │ Mosaic AI Model    │
   │             │ Embeddings   │ (Delta + LSH) │ Serving            │
   ├─────────────┼──────────────┼───────────────┼────────────────────┤
   │  Snowflake  │ Cortex       │ Cortex Search │ Cortex Fine-tuning│
   │             │ Embed        │ (in-warehouse)│ (serverless)       │
   └─────────────┴──────────────┴───────────────┴────────────────────┘
```
