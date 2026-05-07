# Architecture — Enterprise RAG Platform

## 1. High-Level View (AWS Mode)

```
                 ┌────────────────────────────────────────────────────┐
                 │                  Source Systems                     │
                 │  SharePoint, Confluence, Drive, Slack, Wikis        │
                 └────────────┬───────────────────────────────────────┘
                              │ scheduled + webhook ingestion
                              ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │                            Ingestion VPC                              │
   │                                                                        │
   │   ┌────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────────┐    │
   │   │  S3    │──►│ EventBr  │──►│  Lambda  │──►│  Step Functions │    │
   │   │ raw    │   │  rules   │   │ extract  │   │   ingestion FSM │    │
   │   └────────┘   └──────────┘   └──────────┘   └────────┬────────┘    │
   │                                                         │             │
   │   ┌────────────┐   ┌──────────┐   ┌──────────────────┐ │             │
   │   │  Textract  │◄──┤ chunker  │◄──┤  Bedrock Embed   │◄┘             │
   │   │ (PDF/IMG)  │   │  Lambda  │   │  Titan v2 (1024) │               │
   │   └────────────┘   └──────────┘   └──────────────────┘               │
   │                                            │                          │
   └────────────────────────────────────────────┼──────────────────────────┘
                                                ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │                  OpenSearch Serverless (private VPC)                  │
   │   k-NN dense vectors  +  BM25 sparse  +  metadata filters             │
   │   index: chunks_v1  (chunk_id, text, vector, doc_id, acl_groups, …)   │
   └──────────────────────────────────────────────────────────────────────┘
                                                ▲
                                                │ retrieve
   ┌──────────────────────────────────────────────────────────────────────┐
   │                            Query VPC                                   │
   │   ┌──────────┐    ┌─────────┐    ┌────────────┐    ┌──────────────┐  │
   │   │ API GW   │──► │ Lambda  │──► │ Hybrid     │──► │ Cohere Rerank │ │
   │   │ (mTLS)   │    │ orches  │    │ retriever  │    │  (Bedrock)    │ │
   │   └──────────┘    └────┬────┘    └────────────┘    └───────┬───────┘ │
   │                         │                                   │         │
   │                         ▼                                   ▼         │
   │                  ┌────────────┐                    ┌────────────────┐ │
   │                  │ Bedrock    │                    │ Bedrock        │ │
   │                  │ Guardrails │◄───── prompt ──────│ Claude Sonnet  │ │
   │                  └────────────┘                    └────────────────┘ │
   │                                                                        │
   │   Cache: ElastiCache (semantic) + DynamoDB (exact)                    │
   └──────────────────────────────────────────────────────────────────────┘
```

## 2. AWS Service Choices and Why

| Layer | Service | Why this, not that |
|-------|---------|--------------------|
| Object store | **S3** | Standard. Versioning + Object Lock for audit. EventBridge integration. |
| OCR | **Textract** | Better than open-source for forms/tables. Async API for scale. |
| Vector store | **OpenSearch Serverless** | Native hybrid (k-NN + BM25) in one query. VPC endpoint. Avoids running a stateful k-NN service. *(Pinecone/Weaviate require data egress; not viable for regulated workloads.)* |
| Embeddings | **Bedrock Titan v2** | In-region, no egress, IAM-controlled. *(OpenAI ada-2 means SaaS dependency.)* |
| LLM | **Bedrock Claude 3.5 Sonnet** | Best instruction-following with citations. Region-pinned. |
| Reranker | **Bedrock Cohere Rerank 3** | First-class managed reranker. Significantly better than dense-only. |
| Orchestration | **Lambda + Step Functions** | Serverless, ingestion bursts well, no idle cost. |
| Cache | **ElastiCache Redis** | Semantic prompt cache (vector lookup) + exact-match TTL cache. |
| Audit | **CloudTrail + QLDB** | Every prompt + retrieved chunks signed for non-repudiation. |
| Observability | **CloudWatch + X-Ray + OpenSearch dashboards** | Tracing across Lambdas, latency/cost dashboards. |

## 3. Data Flow

### 3.1 Ingestion

1. Document lands in `s3://acme-corp-raw-docs/{tenant}/{source}/{doc_id}.{ext}`.
2. EventBridge fires; Lambda extracts text (Textract for PDF, mammoth for DOCX, plain read for TXT/MD).
3. Step Functions orchestrates: extract → chunk → embed → write.
4. Each chunk gets:
   - `chunk_id` (UUID)
   - `doc_id`, `tenant_id`, `source`, `path`
   - `acl_groups` (list of group SIDs that can read this doc)
   - `created_at`, `updated_at`, `last_indexed_at`
   - `text`, `vector` (1024-dim float)
   - `chunk_index`, `total_chunks_in_doc`

### 3.2 Query

1. API Gateway → Lambda orchestrator.
2. **Query rewrite** (optional) — Claude Haiku, low-cost call to expand acronyms and normalize.
3. **Hybrid retrieval** — single OpenSearch `_search` with hybrid scoring (`hybrid` query type), filtered by user's `acl_groups`. Returns top 50.
4. **Rerank** — Cohere Rerank scores all 50 against the query, returns top 5.
5. **Refusal gate** — if `top_rerank_score < 0.3`, return "I don't know based on available documents."
6. **Generate** — Claude Sonnet with the 5 chunks injected as context. System prompt enforces inline citations to chunk IDs.
7. **Validate** — post-hoc check that every claim cites a chunk; drop unsupported claims.
8. **Cache** — store `(query_hash, doc_set_hash) → answer` for 24h.

## 4. Security

- **Network** — All inter-service traffic is VPC-private. PrivateLink for Bedrock. No internet egress from the data plane.
- **IAM** — Per-tenant role assumption. Chunk-level ACL filter at retrieval time enforces document permissions.
- **Encryption** — KMS CMKs per tenant. S3, OpenSearch, EBS, ElastiCache all encrypted with the tenant key.
- **Audit** — Every query is logged with `user_id`, `query`, `retrieved_chunk_ids`, `prompt`, `response`, `model_id`, `tokens`, `cost`. CloudTrail plus QLDB for tamper-evident records.
- **Guardrails** — Bedrock Guardrails configured for: PII redaction (output), prompt-injection detection (input), denied-topics filter.

## 5. Cost Model (illustrative, US East, 2025)

Assume 8,000 users, 10 queries/user/day, 200 working days/year = **16M queries/year**.

| Item | Per-query | Annual |
|------|-----------|--------|
| Embedding (avg query 20 tokens × Titan v2) | $0.000004 | $64 |
| Hybrid retrieval (OpenSearch Serverless OCU) | ~$0.0001 | $1,600 |
| Cohere Rerank (50 docs) | $0.001 | $16,000 |
| Claude Sonnet (5K input + 300 output tokens) | $0.0195 | $312,000 |
| Cache hit ratio assumed 30% → effective LLM cost | | $218,400 |
| Lambda + API GW | $0.00005 | $800 |
| **Total per query (effective)** | **~$0.015** | **~$237K** |

**Optimization levers** (in priority order):
1. Cache aggressively (semantic + exact). Each 10pt cache hit saves ~$22K/year.
2. Route easy queries to Haiku ($0.00025/$0.00125 vs $0.003/$0.015) — typically 40–60% of traffic.
3. Trim context — going from 5 chunks @ 1K tokens to 5 chunks @ 600 tokens cuts input cost 40%.
4. Batch ingestion embeddings via Bedrock Batch (50% discount).

## 6. Failure Modes & Mitigations

| Failure | Detection | Mitigation |
|---------|-----------|------------|
| Hallucination | RAGAS faithfulness eval, daily | Refusal gate, citation validator, lower temperature |
| Stale data | `last_indexed_at` lag metric | Reduce ingestion polling interval; webhook where possible |
| Permission leak | Audit log review, red-team queries | ACL filter at retrieval, not just at index |
| Cost runaway | CloudWatch budget alarm | Per-tenant rate limit, model routing, cache |
| Prompt injection | Bedrock Guardrails detection | Refuse + log; restrict tool use until reviewed |
| OpenSearch overload | Query latency p99 alarm | Scale OCUs, add a hot/warm tier, backpressure |
