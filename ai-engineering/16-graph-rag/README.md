# 16 — Graph RAG (Hybrid Retrieval with a Knowledge Graph)

> **Customer problem:** Vector-only RAG works for single-hop questions but
> breaks on the **two-hop questions** that enterprise users actually ask
> ("I'm a new hire traveling internationally — what's the approval path?").
> Build a retrieval system that combines **vector search, BM25, and a
> knowledge graph** behind a single API, and prove it works on an eval set
> that includes adversarial / out-of-scope queries.

**Full stack: React + FastAPI + ClickHouse — runs in one `docker compose up`.**
See [`docker-compose.yml`](./docker-compose.yml) and the **Run the full stack**
section below.

This project is the **bridge** between the vector-RAG flagship
(`01-enterprise-rag-platform`) and the regulated / multi-agent / LLMOps
projects above it. It runs **fully local** — no AWS account, no Docker
required — and ships with a real LLM (Anthropic Claude) plus a
deterministic mock fallback so the demo is reproducible.

---

## 1. The Press Release (Working Backwards)

> **AcmeCorp launches AskAcme v2 — now with graph-grounded answers.**
> AskAcme v2 combines vector search, lexical search, and a knowledge graph
> over AcmeCorp's documentation. Customers report a **2.3× increase in
> correctly-cited two-hop answers** and a **40% drop in hallucinated
> citations** on multi-document questions. Internal evaluation against a
> 28-question golden + two-hop + adversarial set: **94% citation precision
> on single-hop, 81% on two-hop, 100% refusal on out-of-scope queries.**

**Customer FAQ**
- *Why does this exist when we already have vector search?* — Vector search
  finds similar text. Graph search finds the **relations between entities**,
  which is what "what's the path from A to B?" actually needs.
- *Does it need a different DB?* — Locally, NetworkX + SQLite. In production,
  Amazon Neptune (or Neo4j). The class boundary is the swap point.
- *What about cost?* — Same as vector RAG plus the LLM cost of triple
  extraction at ingest. At query time, graph walks are cheap.

---

## 2. Theory — Why Graph RAG?

Vector RAG is great for *"find me a doc that talks about X"*. It is bad at:

| Question type | Vector RAG | Graph RAG |
|---|---|---|
| Single-hop fact | ✅ | ✅ |
| **Two-hop** (A → B → C) | ⚠️ sometimes | ✅ |
| **Relation** (how does X relate to Y) | ❌ | ✅ |
| **Refusal** for OOS questions | ⚠️ often hallucinates | ✅ traceable |
| **Freshness** at the entity level | ⚠️ re-embed cost | ✅ graph mutation |

Three retrieval strategies in this project, all answering the same question:

- **Vector** — semantic similarity over `sentence-transformers/all-MiniLM-L6-v2` + FAISS inner-product
- **BM25** — lexical match via `rank-bm25`
- **Graph** — entity-link the query → seed subgraph → flatten to supporting chunks
- **Hybrid** — Reciprocal Rank Fusion (Cormack et al., 2009) of all three

The **money shot** is the two-hop question:

> *"I'm a new hire about to travel internationally for a client visit. What is the approval path?"*

The answer requires facts from `onboarding.md`, `it-runbooks.md`, and
`expense-policy.md`. No single document has the full answer. Pure vector
RAG returns the closest single doc; **graph RAG returns the chain**.

---

## 3. Architecture

```
                        ┌──────────────────────────────────────┐
   user question ───▶   │  Entity linker (cheap substring match) │
                        └────────────────┬─────────────────────┘
                                         │ seed entities
                                         ▼
┌─────────────────────┐    ┌─────────────────────────────────────┐
│ Vector (FAISS)      │    │  Knowledge graph (NetworkX)        │
│ all-MiniLM-L6-v2    │    │  built from LLM-extracted triples   │
└──────────┬──────────┘    └─────────────────┬───────────────────┘
           │                                │
           │    ┌───────────────────────────┘
           │    │  subgraph expand (depth=2)
           │    ▼
           │   edges → supporting chunks
           │            │
           ▼            ▼
   ┌────────────────────────────────────────────────┐
   │  Reciprocal Rank Fusion  (RRF, k=60)           │
   │  score(d) = Σ  1 / (k + rank_strategy(d))       │
   └────────────────────┬───────────────────────────┘
                        │ top-K chunks + graph trace
                        ▼
            ┌────────────────────────────┐
            │  Anthropic Claude (or Mock) │
            │  grounded answer + cites    │
            └────────────────────────────┘
```

The `GraphStore` class in `src/graph_store.py` is the seam where **Neptune**
or **Neo4j** plugs in for production. See
[`ARCHITECTURE.md`](./ARCHITECTURE.md) for ADRs.

---

## 4. Project Layout

```
16-graph-rag/
├── README.md                ← you are here
├── ARCHITECTURE.md          ← ADRs (NetworkX vs Neptune, RRF, JSON-schema)
├── Makefile                 ← install / ingest / query / eval / test / clean
├── docker-compose.yml       ← clickhouse + api + web (one-command stack)
├── requirements.txt         ← -r ../shared/requirements.txt + networkx, faiss-cpu, rank-bm25, ...
├── .env.example             ← LLM_MODE, ANTHROPIC_API_KEY, EMBED_MODEL
│
├── src/                     ← core library (Python)
│   ├── config.py, llm.py, embeddings.py, ingestion.py
│   ├── vector_index.py, bm25_index.py, graph_store.py, graph_builder.py
│   ├── retrievers.py, generation.py, pipeline.py
│
├── api/                     ← FastAPI service
│   ├── app/main.py          ← /health /graph /query /eval/summary /ingest/*
│   └── Dockerfile
│
├── web/                     ← React + Vite + Tailwind + Plotly + Cytoscape
│   ├── src/App.tsx
│   ├── src/components/      ← QueryPanel, KnowledgeGraphView, EvalDashboard, ui/*
│   ├── src/lib/api.ts       ← typed API client
│   ├── package.json
│   └── Dockerfile
│
├── db/
│   └── init.sql             ← ClickHouse schema (eval_results, query_log, graph_snapshot)
│
├── scripts/
│   ├── ingest.py            ← build local indices
│   ├── query.py             ← CLI query
│   ├── evaluate.py          ← run eval, print Markdown table
│   ├── extract_demo.py      ← show LLM extracting a sample triple
│   └── seed_clickhouse.py   ← write eval + graph into ClickHouse
│
├── sample_data/             ← AcmeCorp corpus + 3 eval JSONL files
├── data/                    ← built indices (gitignored)
├── tests/                   ← pytest, mock mode, no API key needed
└── dashboard.py             ← original Streamlit dashboard (still works, no DB)
```

---

## 5. Quick Start

```bash
cd ai-engineering/16-graph-rag

# 1. Install (only adds networkx; everything else is already in 01-...)
make install

# 2. Build indices + graph from sample_data/corpus
make ingest

# 3. Ask a question (default strategy: hybrid)
make query Q="What is the PTO policy for new hires?"

# 4. Compare strategies on the two-hop money shot
make query Q="I'm a new hire about to travel internationally for a client visit. What is the approval path?" STRATEGY=vector
make query Q="I'm a new hire about to travel internationally for a client visit. What is the approval path?" STRATEGY=hybrid

# 5. Run the full eval (all 28 questions × 4 strategies)
make eval

# 6. Run the test suite (no API key needed — uses MockLLM)
make test
```

**Works with no API key.** If `ANTHROPIC_API_KEY` is unset, `LLM_MODE=auto`
falls back to `MockLLM` — a deterministic implementation that returns
canned answers + canned triples for the AcmeCorp corpus. The same `make
eval` and `make test` commands run end-to-end.

To use a real LLM, copy `.env.example` to `.env`, paste your
`ANTHROPIC_API_KEY`, and re-run `make ingest` to rebuild the graph with
real triple extraction.

---

## 6. Design Decisions

| Decision | Choice | Why |
|---|---|---|
| Graph store | NetworkX + SQLite (local); Neptune (prod) | Zero-infra demo. ABC seam for prod swap. |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | 22 MB, fast on CPU, 384-dim. Same as 01. |
| Vector index | FAISS IndexFlatIP (inner product) | L2-normalised vectors → inner product = cosine. |
| Hybrid fusion | Reciprocal Rank Fusion (k=60) | Rank-based, no score normalisation needed. |
| Entity linker | Substring match over node labels | Cheap, effective for demo. Prod = NER. |
| LLM | Anthropic Claude 3.5 Haiku (default); mock fallback | Cheap, fast, follows JSON-tool-use reliably. |
| Triple extraction | Tool-use JSON mode (Anthropic) | Schema-constrained, validated. |
| Graph expand depth | 2 hops | Covers the two-hop eval set; tunable. |
| Chunk size | 1200 chars / 200 overlap | Mirrors `01-enterprise-rag-platform`. |

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for full ADRs.

---

## 7. Eval Methodology

Three JSONL sets in `sample_data/`:

| Set | Size | Purpose | Expected |
|---|---|---|---|
| `eval_golden.jsonl` | 15 | Single-hop facts | All strategies ≥ 80% keyword hit |
| `eval_twohop.jsonl` | 8 | Multi-doc / relational | Graph + hybrid ≥ 75% citation precision; vector ~30% |
| `eval_adversarial.jsonl` | 5 | Out-of-scope / PII | All strategies refuse 100% |

Per row we measure:

- **Citation precision** — fraction of cited docs that are in `expected_doc_ids`
- **Keyword hit rate** — fraction of `expected_keywords` appearing in the answer
- **Refused** — answer contains "I don't have that information" / "I don't know"

`make eval` writes a `data/eval_report.jsonl` with per-row details, plus a
Markdown summary table.

---

## 8. Production Considerations

| Concern | Local (this demo) | Production |
|---|---|---|
| Graph store | NetworkX + SQLite | Amazon Neptune (Gremlin/SPARQL) or Neo4j (Cypher) |
| Vector index | FAISS on disk | OpenSearch k-NN / Pinecone / pgvector |
| Embeddings | sentence-transformers on CPU | Bedrock Titan Embed v2 / Cohere Embed |
| LLM | Anthropic Claude 3.5 Haiku (or mock) | Bedrock Claude (Haiku for cheap, Sonnet for hard) |
| Triple extraction | Tool-use JSON per chunk | Same, with a small eval gate on the graph before serving |
| Freshness | Full re-ingest | Event-driven delta; entity-level invalidation |
| Eval | Local pytest + JSONL | Continuous eval against sampled prod traffic (mirrors `04-fm-evaluation/`) |
| Authn / tenancy | None | Same as `06-regulated-industry/` |
| Cost telemetry | None | Cost per query, per tenant, per strategy — see `05-distributed-inference/` |

The **most important** production concern is **graph staleness**. A graph
that drifts behind the corpus will quietly produce wrong answers. The fix
is to treat the graph like a derived view: it is rebuilt on the same
schedule as the embeddings, and a sample-of-N entity-existence check
gates every release.

---

## 9. The Two-Hop Money Shot — what `make demo` shows

Run `make demo` and you'll see this in sequence:

```
═══ Single-hop question (all strategies should answer) ═══
→ make query Q="What is our PTO policy for new hires?"
   Both `vector` and `hybrid` correctly cite pto-policy.md.

═══ Two-hop money shot (graph + hybrid should win) ═══
→ make query Q="I'm a new hire about to travel internationally..."
   strategy=vector  → cites 1 doc (incomplete answer)
   strategy=hybrid  → cites 3 docs (onboarding + it-runbooks + expense-policy)
                       + graph trace: New Hire → Onboarding Program → IT Runbooks
                         → Expense Policy → VP Approval
═══ Running evaluation ═══
   strategy comparison table (see Section 7)
```

The graph trace is the difference. It's the visible evidence that the
system is *reasoning over relations*, not just *finding similar text*.

---

## 10. Done metrics

| Metric | Target | How measured |
|---|---|---|
| Single-hop citation precision (all strategies) | ≥ 80% | `make eval` → `eval_golden.jsonl` |
| Two-hop citation precision (graph + hybrid) | ≥ 75% | `make eval` → `eval_twohop.jsonl` |
| Two-hop citation precision (vector) | intentionally lower (~30%) | same — the proof |
| Adversarial refusal rate (all strategies) | 100% | `make eval` → `eval_adversarial.jsonl` |
| Tests pass with no API key | yes | `make test` (mock mode) |
| Time to first answer, local | < 5 s end-to-end | `make query` after `make ingest` |

The README does not hard-code numbers — run `make eval` to get the actual
table for your machine, and paste it under this section.

---

## Related projects

- `01-enterprise-rag-platform/` — the vector-RAG flagship
- `04-fm-evaluation/` — the eval framework this project's harness could graduate into
- `05-distributed-inference/` — model routing + caching for the generation step
- `06-regulated-industry/` — guardrails, redaction, audit (drop-in for this project's answer)
- `08-llmops-platform/` — composes the other projects; the eventual home for this one
