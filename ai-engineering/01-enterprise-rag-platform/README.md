# 01 — Enterprise RAG Platform

> **Customer problem:** Knowledge workers spend ~4 hours/week searching internal documentation. Build a unified, grounded Q&A platform across 40M+ enterprise documents with citations, freshness guarantees, and a hallucination rate <3%.

This is the **flagship project** of the portfolio — built end-to-end with theory, working code, sample data, and both LOCAL and AWS execution modes.

---

## 1. The Press Release (Working Backwards)

> **AcmeCorp launches AskAcme, an enterprise knowledge assistant.**
> Today AcmeCorp made AskAcme generally available to all 8,000 employees. AskAcme answers questions grounded in AcmeCorp's internal documentation — policies, runbooks, design docs, contracts — with inline citations to the source paragraphs. Pilot users reported a 47% reduction in time-to-answer and a 4.6/5 trust score on factual accuracy. AskAcme is built on Amazon Bedrock and Amazon OpenSearch, deployed in a private VPC with no data egress.

**Customer FAQ**
- *Will it make things up?* — Every answer cites the exact paragraph it was drawn from. Answers without high-confidence sources return "I don't know" rather than guess.
- *Can it see my private documents?* — Document-level access control mirrors source-system permissions (SharePoint, Confluence, Drive). You only see what you'd see there.
- *How fresh is the data?* — Documents are reindexed within 15 minutes of being updated.

---

## 2. Theory — Why RAG?

A foundation model alone cannot answer questions about *your* private, current data. There are three options:

| Option | When it wins | Limits |
|--------|--------------|--------|
| **Long context** (paste docs into prompt) | Tiny corpora, one-off | Cost scales with input; 200K-token cap; needle-in-haystack drift |
| **Fine-tuning** | Style/format adaptation, narrow domain | Doesn't add facts reliably; expensive to refresh; no citations |
| **RAG** | Most enterprise Q&A | Quality bounded by retrieval quality |

RAG decouples *what the model knows* (frozen weights) from *what it has access to* (your indexed corpus), and is the right default for enterprise knowledge applications.

### The RAG quality equation

```
Answer quality = f(retrieval recall, retrieval precision, context use, generation fidelity)
```

Most teams over-invest in the generation step (the LLM) and under-invest in retrieval. **Retrieval is where projects fail.** This codebase reflects that — most of the surface area is retrieval-side.

### Why hybrid retrieval

Pure dense retrieval (embeddings + cosine similarity) struggles with:
- **Rare terms / proper nouns** (e.g., "EBS gp3 throughput limit")
- **Exact code or error strings**
- **Out-of-distribution domain vocabulary**

Pure sparse retrieval (BM25) struggles with:
- **Paraphrases** ("how do I cancel" vs. "termination procedure")
- **Multi-language** content
- **Conceptual questions**

The fix: run both, fuse with **Reciprocal Rank Fusion (RRF)**, then **rerank** the top 50 candidates with a cross-encoder. This is the architecture used in this project.

### Why reranking matters

Bi-encoders (the embedding model) encode query and document independently — fast, but lossy. Cross-encoders see query and document together — slow, but ~5–15 points more accurate. Reranking only the top-50 from cheap retrieval gives you the best of both.

---

## 3. Architecture

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                       INGESTION                          │
                    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
                    │  │   S3     │→ │  Glue    │→ │ Textract │→ │ Chunker  │ │
                    │  │ raw docs │  │ trigger  │  │ for PDFs │  │ semantic │ │
                    │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
                    └────────────────────────────┬────────────────────────────┘
                                                 ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │                       INDEXING                           │
                    │  ┌──────────────┐         ┌────────────────────────┐    │
                    │  │  Bedrock     │ ──────► │  OpenSearch Serverless │    │
                    │  │ Titan Embed  │         │   (k-NN + BM25 hybrid) │    │
                    │  └──────────────┘         └────────────────────────┘    │
                    └─────────────────────────────────────────────────────────┘

   USER QUERY
      │
      ▼
   ┌────────┐    ┌─────────────────┐    ┌─────────────┐    ┌──────────────┐
   │ Query  │ →  │ Hybrid Retrieve │ →  │  Rerank     │ →  │  Generation  │
   │ rewrite│    │ (BM25 + dense)  │    │ (cross-enc) │    │  (Claude)    │
   │        │    │   top 50        │    │   top 5     │    │  + citations │
   └────────┘    └─────────────────┘    └─────────────┘    └──────────────┘
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full AWS deployment view.

---

## 4. Project Layout

```
01-enterprise-rag-platform/
├── README.md               (this file)
├── ARCHITECTURE.md         (deployment / AWS view)
├── Makefile                (demo, ingest, query, eval, test)
├── requirements.txt
├── .env.example
├── src/
│   ├── config.py           Pydantic settings
│   ├── ingestion/
│   │   ├── loader.py       Document loaders (txt/md/pdf)
│   │   └── chunker.py      Recursive + semantic chunking
│   ├── embedding/
│   │   └── embedder.py     Local (sentence-transformers) + Bedrock Titan
│   ├── retrieval/
│   │   ├── vector_store.py FAISS (local) + OpenSearch (AWS) adapters
│   │   ├── bm25.py         Pure-Python BM25 sparse retrieval
│   │   ├── hybrid.py       RRF fusion of dense + sparse
│   │   └── reranker.py     Cross-encoder reranking
│   ├── generation/
│   │   ├── llm.py          LLM adapter (local stub + Bedrock Claude)
│   │   └── rag_pipeline.py End-to-end RAG orchestrator
│   ├── eval/
│   │   └── ragas_eval.py   Faithfulness, context precision, answer relevance
│   └── api/
│       └── main.py         FastAPI service
├── sample_data/docs/       (10 synthetic enterprise documents)
├── scripts/
│   ├── ingest.py           CLI: ingest sample_data/ into the index
│   ├── query.py            CLI: ask a question
│   └── evaluate.py         CLI: run the eval harness
├── tests/                  Pytest suite
└── infrastructure/
    └── cdk_app.py          AWS CDK stack (illustrative)
```

---

## 5. Quick Start

```bash
# Install
pip install -r requirements.txt

# Run end-to-end demo (ingest → query → eval)
make demo
```

Expected output: ingestion summary, an example Q&A with citations, and a small eval table.

```bash
# Run the API
make api
# In another shell:
curl -X POST localhost:8000/ask -H 'Content-Type: application/json' \
  -d '{"question": "What is our PTO policy for new hires?"}'
```

---

## 6. AWS Mode

```bash
export AI_ENGINEERING_MODE=AWS
export AWS_REGION=us-east-1
export OPENSEARCH_ENDPOINT=...
export BEDROCK_EMBEDDING_MODEL=amazon.titan-embed-text-v2:0
export BEDROCK_GENERATION_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0

python scripts/ingest.py
python scripts/query.py "What is our PTO policy?"
```

---

## 7. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Chunk size | 512 tokens, 64 overlap | Balances retrieval precision with enough context. Empirically optimal across most corpora. |
| Chunking strategy | Recursive (default) + semantic option | Recursive respects document structure (headings, paragraphs); semantic groups by meaning when structure is poor. |
| Embedding dim | 1024 (Titan v2) / 384 (local) | Larger = better recall, more storage. Titan v2 is well-tuned for English enterprise text. |
| Top-k retrieve | 50 | Wide enough to give rerank room to work without blowing context budget. |
| Top-k after rerank | 5 | Sweet spot for context usage at 200K-token limit. |
| Reranker | bge-reranker-base (local), Cohere Rerank (AWS) | Cross-encoder, ~5-point lift over dense alone. |
| Generation guardrails | Refuse if max-rerank-score < 0.3 | Prevents hallucination on out-of-corpus questions. |
| Citations | Mandatory in prompt + post-hoc validation | Generator must cite chunk IDs; pipeline drops uncited claims. |

---

## 8. Eval Methodology

We use a 3-tier eval:

1. **Retrieval-only metrics** — Recall@10, MRR. Run weekly against a labeled golden set.
2. **End-to-end LLM-as-judge** — RAGAS-style: faithfulness, answer relevance, context precision.
3. **Human spot-check** — 20 samples reviewed weekly by a domain SME.

The `src/eval/ragas_eval.py` module implements (1) and (2). See `scripts/evaluate.py` for the CLI.

---

## 9. Production Considerations (not all in code)

- **Permissions** — re-check ACLs at query time, not just at index time. We index a `acl_groups` field per chunk and filter at retrieval.
- **Freshness** — S3 EventBridge triggers re-ingestion. Track `last_indexed_at` and alert on staleness.
- **Cost** — embedding is cheap, LLM generation is the cost dominator. Cache by `(query_hash, top_k_chunk_hashes)`.
- **PII** — Bedrock Guardrails for outbound PII redaction; Macie for index-side scanning.
- **Observability** — every step emits a span (chunk_ids, scores, latency, tokens). Visualized in CloudWatch / OpenTelemetry.

---

## 10. What "Done" Looks Like

| Metric | Target | How measured |
|--------|--------|--------------|
| Recall@10 (golden set) | ≥ 0.85 | Retrieval-only eval, weekly |
| Faithfulness | ≥ 0.90 | RAGAS LLM-as-judge |
| Hallucination rate | < 3% | Human spot-check, 20/week |
| p95 latency | < 2.5 s | CloudWatch |
| Cost per answer | < $0.02 | Cost attribution dashboard |
| Index freshness | < 15 min lag | EventBridge → indexing latency |
