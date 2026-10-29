# Course Syllabus

**Title:** AI-Native Data Engineering and Production AI Systems: From First Principles to Staff-Level Architecture

**Audience:** Senior data engineering leaders (15+ years) targeting Meta AI-Native DE, Senior Technical Design, and Google AI/ML infrastructure roles.

**Outcome target:** Production-grade capability in retrieval, RAG, AI evaluations, security, and AI system design. **Not a promise of top-1% status or interview success.** The bar is *exceptional professional capability*, demonstrated through runnable code, defensible tradeoffs, and clear written communication.

---

## Module map

| # | Module | Core deliverable | Time |
|---|---|---|---|
| M1 | AI-Native DE Foundations | Taxonomy + a one-page architecture diagram of a RAG system | 90 min |
| M2 | Vector Mathematics and Similarity Search | From-scratch KNN in NumPy + tests | 90 min |
| M3 | Embeddings and Model Selection | Embedding eval harness + dual-index rollout plan | 90 min |
| M4 | ANN and Vector DB Internals | HNSW vs IVF-PQ benchmark on the same dataset | 120 min |
| M5 | Document Ingestion and Parsing | Idempotent ingestion service with DLQ | 120 min |
| M6 | Chunking and Context Preservation | Structure-aware chunker + chunk-size ablation | 90 min |
| M7 | Retrieval and Ranking | BM25 + dense + RRF + MMR pipeline | 120 min |
| M8 | LLM Fundamentals | Prefill/decode analysis + token-budget calculator | 90 min |
| M9 | RAG End-to-End | Working enterprise doc assistant with citations | 180 min |
| M10 | Evaluation and Experimentation | Golden dataset + RAGAS-style metrics | 120 min |
| M11 | Observability, Reliability, Cost | Tracing + P95 dashboard + cost model | 90 min |
| M12 | Security, Privacy, Governance | ACL filter + prompt-injection test suite | 120 min |
| M13 | Agents, Tools, MCP | Read-only SQL+search agent with approval gates | 120 min |
| M14 | AI-Native Data Platforms | Spark + Kafka + feature-store design exercise | 120 min |
| M15 | Staff-Level AI System Design | 100M-doc capacity model + 3-year evolution | 120 min |
| M16 | AI-Native Full Stack | FastAPI service with ingest/retrieve/chat + tests | 180 min |
| M17 | Product Metrics, SQL, Python Coding | 5 timed mock problems with solutions | 180 min |
| M18 | Leadership, Ownership, Influence | 5 STAR-based answers with rubric | 90 min |
| **Capstone** | Secure Enterprise AI Knowledge Assistant | Runnable, tested, documented | 8-12 hr |

**Total:** ~32 hours of guided study + 8-12 hours capstone + daily interview drills.

---

## 21-day intensive schedule

| Day | Focus | Modules |
|---|---|---|
| 1 | AI-native DE + end-to-end RAG architecture | M1 |
| 2 | Vector math + exact KNN in Python | M2 |
| 3 | Embeddings + similarity evaluation | M3 |
| 4 | HNSW, IVF-PQ, FAISS, vector DBs | M4 |
| 5 | Document ingestion + chunking | M5, M6 |
| 6 | Hybrid retrieval (BM25, RRF, MMR) | M7 |
| 7 | First working RAG application | M8, M9 |
| 8 | Golden datasets + retrieval evaluation | M10 |
| 9 | Generation quality + hallucination debugging | M10 |
| 10 | ACLs, security, privacy | M12 |
| 11 | Observability, P95, cost | M11 |
| 12 | Embedding migration, zero downtime | M3, M15 |
| 13 | Agents, tools, MCP, text-to-SQL | M13 |
| 14 | AI-native streaming, Spark, Kafka | M14 |
| 15 | Senior technical design mock | M15 |
| 16 | Python coding mock | M17 |
| 17 | Spark SQL + data modeling mock | M14, M17 |
| 18 | AI-native full stack mock | M16 |
| 19 | Product metrics + ambiguity mock | M17 |
| 20 | Senior ownership + leadership mock | M18 |
| 21 | Full simulated onsite, scoring, targeted revision | All |

---

## Daily session (60-120 min)

| Block | Time | What |
|---|---:|---|
| 1 | 10 min | Plain-English concept (the 12-year-old version) |
| 2 | 20 min | Deep technical + formulas + diagram |
| 3 | 30 min | Runnable code + debugging |
| 4 | 20 min | System design + tradeoffs |
| 5 | 20 min | Mock interview (5 Meta Qs + 3 Google Qs) |
| 6 | 10 min | Scorecard + corrections + flashcards |

For 60-min sessions, cut Block 3 to 15 min and skip Block 5.

---

## Prerequisites

| Skill | Required level | How to verify |
|---|---|---|
| Python 3.11+ | Comfortable — decorators, dataclasses, async | Can read `asyncio` code without panicking |
| SQL | Window functions, CTEs, EXPLAIN | Can write a 3-table join with a window function |
| Spark / PySpark | Has used DataFrames + Spark SQL | Can explain `transform` vs `action` |
| Basic ML | Knows train/test, overfitting, embeddings | Can describe what an embedding is |
| Cloud | Comfortable with one of AWS/GCP | Has deployed something to a VM |
| Git | Commits, branches, PRs | Can resolve a merge conflict |
| Linear algebra (basics) | Vectors, dot product, norms | Can write `np.dot(a, b)` |

**Not required:** PhD math, prior LLM production experience, paid API access.

---

## Technology choices (all free, all Apple Silicon compatible)

| Layer | Tool | Why |
|---|---|---|
| Language | Python 3.11+ | Standard |
| Vector math | NumPy | Standard, no GPU needed |
| Sparse retrieval | rank_bm25 (or `bm25s`) | Pure Python, MIT |
| Dense embeddings | sentence-transformers (BGE-small / E5-small) | Free, local, M1/M2/M3 optimized |
| Vector index | FAISS (faiss-cpu) or hnswlib | FAISS is the reference; hnswlib is pure C++/Python |
| Vector DB (optional) | Chroma or pgvector | Chroma is the easiest local start |
| LLM (local) | Ollama (llama3.1:8b-instruct-q5_K_M) | Free, runs on M-series, MIT |
| LLM (API) | OpenAI-compatible (optional) | For grading the grading |
| HTTP | FastAPI + Uvicorn | Standard |
| DB (metadata) | SQLite (default) or DuckDB | Zero-config |
| Tracing | OpenTelemetry (console exporter) | Standard |
| Tests | pytest | Standard |
| Notebooks | Jupyter | Standard |

**No paid API is required for the baseline.** If you want to use OpenAI/Anthropic for the LLM, that's an optional swap.

---

## Project architecture (capstone)

```
secure-enterprise-ai-assistant/
├── README.md                # 90-second walkthrough
├── pyproject.toml           # pinned deps
├── docker-compose.yml       # optional: postgres + chroma + ollama
├── src/
│   ├── ingest/              # PDF/HTML/text -> chunks -> embeddings
│   ├── retrieval/           # BM25 + dense + RRF + ACL
│   ├── generation/          # prompt assembly + citation
│   ├── agent/               # tool-use agent with approval gate
│   ├── eval/                # golden set + metrics
│   ├── observability/       # OTel + token accounting
│   └── api/                 # FastAPI routes
├── tests/                   # pytest
├── data/
│   ├── raw/                 # 10-100 synthetic docs
│   └── golden/              # 50 labeled Q/A pairs
└── notebooks/               # exploratory work
```

---

## Evaluation rubric (for capstone, 0-100)

| Dimension | Weight | What we look for |
|---|---:|---|
| Correctness (code runs, tests pass) | 25 | All pytest pass; smoke test of the API works |
| RAG quality (retrieval + answer) | 20 | Recall@10 ≥ 0.7 on golden; answer faithfulness ≥ 0.8 |
| System design (architecture) | 15 | Mermaid diagram; clear separation of ingest / retrieve / generate |
| Security (ACLs, PII, prompt-injection) | 15 | ACL filter at query time; injection test suite passes |
| Observability (traces, metrics, cost) | 10 | OpenTelemetry traces show retrieval+gen steps; cost per query |
| Code quality (readability, tests, types) | 10 | Type hints, docstrings, tests for the hot paths |
| Documentation (README, walkthrough) | 5 | 90-second walkthrough is concrete and accurate |

**Passing bar:** ≥ 70. **Stretch bar:** ≥ 85. **Anything < 70 means a specific weak dimension, not a global rewrite.**

---

## Interview grading rubric (per mock, 0-10)

| Dimension | 0-2 | 3-5 | 6-8 | 9-10 |
|---|---|---|---|---|
| Problem clarification | Asks nothing | Asks 1 surface question | Asks about constraints, scale, SLAs | Surfaces hidden constraints (cost, security, tenant isolation) |
| Technical correctness | Major errors | Mostly right, gaps in details | Right, with one minor gap | Defends the answer with reasoning and tradeoffs |
| Coding | Doesn't compile | Compiles, some logic bugs | Passes tests | Idiomatic, tested, profiled |
| System design | Single box | Multiple components, no SLAs | Sized, costed, with SLOs | Includes failure modes, migration, evolution |
| Scalability | "Just add boxes" | Horizontal scaling mentioned | Concrete capacity numbers | Back-of-envelope + measured numbers |
| Privacy/security | Ignored | Mentioned | ACL filter + encryption | Tenant isolation, prompt-injection tests, audit |
| Reliability | No retry | Retry mentioned | Backoff, circuit breaker | Idempotency, error budgets, on-call runbook |
| Tradeoff analysis | One option, no tradeoffs | Two options, vague | Quantified tradeoffs | Recommends with a defended call |
| Communication | Hard to follow | Mostly clear | Structured, with diagrams | Adapts to audience, summarizes well |
| Ownership | Waits for the question | Asks for next step | Proactively scopes adjacent work | Frames the problem, sets the agenda |

**No automatic perfect scores.** The rubric above is how the assistant scores you. If you score 9-10, you probably have a gap you didn't see.

---

## Setup (Apple Silicon macOS)

### 1. Python 3.11+

```bash
# If you don't have it
brew install python@3.11
python3.11 -m venv .venv
source .venv/bin/activate
python --version  # Python 3.11.x
```

### 2. Course deps (pinned)

```bash
pip install --upgrade pip
pip install \
  "numpy==1.26.4" \
  "scipy==1.11.4" \
  "pandas==2.1.4" \
  "scikit-learn==1.3.2" \
  "rank_bm25==0.2.2" \
  "sentence-transformers==2.2.2" \
  "faiss-cpu==1.7.4" \
  "hnswlib==0.7.0" \
  "chromadb==0.4.18" \
  "fastapi==0.109.0" \
  "uvicorn[standard]==0.25.0" \
  "pydantic==2.5.3" \
  "httpx==0.25.2" \
  "pytest==7.4.4" \
  "jupyter==1.0.0" \
  "matplotlib==3.8.2" \
  "tiktoken==0.5.1" \
  "opentelemetry-api==1.22.0" \
  "opentelemetry-sdk==1.22.0"
```

### 3. Local LLM (optional but recommended)

```bash
# Install Ollama
brew install ollama
# Start the daemon
ollama serve &
# Pull a small instruction-tuned model
ollama pull llama3.1:8b-instruct-q5_K_M
# Smoke test
curl -s http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b-instruct-q5_K_M",
  "prompt": "Reply with the single word: ok",
  "stream": false
}' | python3 -m json.tool
```

### 4. Verify

```bash
python3 -c "
import numpy, sentence_transformers, faiss, hnswlib, fastapi, tiktoken
print('numpy       :', numpy.__version__)
print('sbert       :', sentence_transformers.__version__)
print('faiss       :', faiss.__version__)
print('hnswlib     :', hnswlib.__version__)
print('fastapi     :', fastapi.__version__)
print('tiktoken    :', tiktoken.__version__)
"
```

### 5. Project layout

```bash
git init secure-enterprise-ai-assistant
cd secure-enterprise-ai-assistant
mkdir -p src/{ingest,retrieval,generation,agent,eval,observability,api} tests data/{raw,golden} notebooks
```

### 6. First notebook (smoke test)

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/ai-course-public/course/ai-native-de
jupyter nbconvert --to notebook --execute lessons/m01-foundations/L1-ai-native-de-101.ipynb --output L1-ai-native-de-101.ipynb
```

---

## What this course is NOT

- **NOT** a guarantee of interview success or "world top 1%" status. The bar is professional capability, not a hiring outcome.
- **NOT** a vendor pitch. Tools are interchangeable; the principles are not.
- **NOT** a survey of every LLM. We use 1-2 reference models and teach the patterns.
- **NOT** a PhD course. We use math where it helps and avoid it where it doesn't.
- **IS** a hands-on, runnable, defensible path from first principles to a staff-level system design.

---

*Last updated: 2026-10-15*
*License: MIT*
