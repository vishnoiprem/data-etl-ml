# Lesson 1 — RAG in LangChain, End-to-End

> **Type:** Article + Worked Example · Course 4
> The canonical RAG build in LangChain, from raw documents to a streaming, ACL-filtered, eval-gated chain.

---

## What this lesson covers

A complete RAG system built with LangChain primitives, demonstrating:
1. Document loading (Notion + S3 PDFs)
2. Chunking (recursive structure-aware)
3. Embedding (Cohere embed-v3)
4. Vector store (Qdrant)
5. BM25 store (in-memory for the worked example, OpenSearch for prod)
6. Hybrid retrieval + Cohere rerank
7. Citations in the answer
8. ACL at the retriever (not in the LLM prompt)
9. Streaming
10. Eval harness (recall@k, faithfulness, citation accuracy)

This is the chain you'd put in front of real users.

---

## The architecture in one diagram

```
   ┌─────────────────────────────────────────────────────────────┐
   │                  RAG CHAIN (LCEL)                            │
   │                                                              │
   │   USER QUERY                                                 │
   │      │                                                       │
   │      ▼                                                       │
   │   ┌─────────────┐                                            │
   │   │  Rewrite    │  multi-query expansion (×3)                │
   │   └─────┬───────┘                                            │
   │         │                                                    │
   │         ▼                                                    │
   │   ┌─────────────────────────────┐                            │
   │   │   Hybrid Search              │                            │
   │   │   ┌─────────┐ ┌─────────┐  │                            │
   │   │   │ Vector  │ │  BM25   │  │  parallel retrieval        │
   │   │   │ (Qdrant)│ │(in-mem) │  │                            │
   │   │   └────┬────┘ └────┬────┘  │                            │
   │   │        └─────┬─────┘       │                            │
   │   │              ▼             │                            │
   │   │       RRF fusion → top-50 │                            │
   │   └─────────────┬─────────────┘                            │
   │                 │                                           │
   │                 ▼                                           │
   │   ┌──────────────────────────┐                              │
   │   │  ACL filter              │  tenant_id, role-based       │
   │   └──────────┬───────────────┘                              │
   │              │                                              │
   │              ▼                                              │
   │   ┌──────────────────────────┐                              │
   │   │  Cohere Rerank           │  top-50 → top-10             │
   │   └──────────┬───────────────┘                              │
   │              │                                              │
   │              ▼                                              │
   │   ┌──────────────────────────┐                              │
   │   │  Prompt Assembly         │  query + context + history   │
   │   └──────────┬───────────────┘                              │
   │              │                                              │
   │              ▼                                              │
   │   ┌──────────────────────────┐                              │
   │   │  Claude Sonnet           │  generate answer + cites     │
   │   └──────────┬───────────────┘                              │
   │              │                                              │
   │              ▼                                              │
   │   ANSWER (with [Source N] citations)                        │
   └─────────────────────────────────────────────────────────────┘
```

Every box is a `Runnable`. The chain is **one expression**:

```python
chain = (
    RunnablePassthrough.assign(
        expanded_queries=rewrite_query,
        sources=hybrid_retrieve | acl_filter | rerank,
    )
    | assemble_prompt
    | model
    | StrOutputParser()
)
```

That's the entire pipeline.

---

## The four design decisions that decide quality

Before writing any code, answer these. They determine 80% of the system's quality:

| Decision | Default | Better | Best |
|---|---|---|---|
| **Splitter** | Fixed-size (chunk_size=1024) | Recursive (chunk_size=400, overlap=80) | Structure-aware (respects headings) |
| **Retrieval** | Vector-only top-5 | Hybrid (BM25 + vector), top-50 | Hybrid + rerank, top-10 |
| **Embeddings** | OpenAI small (1536-d) | Cohere embed-v3 (1024-d) | Domain-specific (fine-tuned on your docs) |
| **Eval** | "looks good" | Recall@k on 50 hand-labeled queries | Recall@k + faithful + citation_accuracy |

The worked example below makes the "Better" column the default — it's the right starting point for most production systems.

---

## Worked Example — RAG over 5K internal docs, production-grade

> **Goal:** Build a RAG system over 5K internal docs (Notion pages + S3-stored PDFs). Internal employees only. ACL by workspace and team. Streaming. Citations. Eval-gated. ~$0.012 per query.

### Step 1 — Document loading

```python
# loaders/load_all.py
from langchain_community.document_loaders import (
    NotionDBLoader,
    S3DirectoryLoader,
    PyPDFLoader,
)
from langchain_community.document_loaders.s3_file import S3FileLoader
import os

def load_notion():
    loader = NotionDBLoader(
        integration_token=os.environ["NOTION_TOKEN"],
        database_id=os.environ["NOTION_DB_ID"],
        request_timeout_sec=30,
    )
    docs = loader.load()
    for d in docs:
        d.metadata["source"] = "notion"
        d.metadata["workspace_id"] = d.metadata.get("workspace", True)  # Notion ACL
    return docs

def load_s3_pdfs():
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    docs = []
    for page in paginator.paginate(Bucket="company-docs"):
        for obj in page["Contents"]:
            if obj["Key"].endswith(".pdf"):
                loader = S3FileLoader("company-docs", obj["Key"])
                for d in PyPDFLoader(loader._get_file_path()).load():
                    d.metadata["source"] = "s3_pdf"
                    d.metadata["workspace_id"] = obj["Key"].split("/")[0]
                    docs.append(d)
    return docs

ALL_DOCS = load_notion() + load_s3_pdfs()
print(f"Loaded {len(ALL_DOCS)} documents")
```

Two loaders, one merged corpus. The metadata is critical — it carries the ACL context.

### Step 2 — Chunking (the most-debated decision)

```python
# splitters/chunk.py
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,            # tokens (≈ 4 chars/token)
    chunk_overlap=80,          # 20% overlap
    separators=[
        "\n\n",                # paragraphs first
        "\n",                  # then lines
        "。", ". ",            # then sentences (CJK + Latin)
        " ",
        "",
    ],
    length_function=len,       # token-accurate via tiktoken wrapper if needed
)

def chunk_with_metadata(docs: list[Document]) -> list[Document]:
    chunks = splitter.split_documents(docs)
    # Add chunk-index-in-doc metadata
    by_doc = {}
    for c in chunks:
        doc_id = c.metadata["source"] + ":" + c.metadata.get("path", str(c.metadata.get("page_number", 0)))
        by_doc.setdefault(doc_id, 0)
        c.metadata["chunk_index"] = by_doc[doc_id]
        by_doc[doc_id] += 1
    return chunks

CHUNKS = chunk_with_metadata(ALL_DOCS)
print(f"{len(CHUNKS)} chunks from {len(ALL_DOCS)} docs")
# e.g., 32,450 chunks from 5,000 docs
```

**Why recursive?** It respects structure (paragraphs > sentences > words). Why 400/80? That's the sweet spot for embedding granularity — small enough to be specific, large enough to retain meaning (see Module 4 of `11-learn-ai-data/`).

### Step 3 — Embedding + BM25 stores

```python
# stores/setup.py
from langchain_cohere import CohereEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_community.retrievers import BM25Retriever
from qdrant_client import QdrantClient
from qdrant_client.http import models
import cohere

# Embeddings (Cohere embed-v3)
co = cohere.Client(os.environ["COHERE_API_KEY"])
embeddings = CohereEmbeddings(model="embed-english-v3.0", client=co)

# Vector store (Qdrant)
qdrant = QdrantClient(url=os.environ["QDRANT_URL"])
QDRANT_COLLECTION = "company-docs"

qdrant.recreate_collection(
    collection_name=QDRANT_COLLECTION,
    vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
)

vector_store = QdrantVectorStore(
    client=qdrant,
    collection_name=QDRANT_COLLECTION,
    embedding=embeddings,
)

# Batch embed + upsert (Qdrant handles batching internally; 32K chunks ~5min)
vector_store.add_documents(CHUNKS, batch_size=64)

# BM25 store (in-memory for the worked example; OpenSearch in prod)
BM25_INDEX = BM25Retriever.from_documents(CHUNKS, k=50)
```

**Two stores, one corpus.** Vector for semantic; BM25 for exact-term. The hybrid retrieval below combines them.

### Step 4 — Hybrid retrieval + rerank

```python
# retrieval/hybrid.py
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain_cohere import CohereRerank
from langchain_core.runnables import RunnableLambda

vector_retriever = vector_store.as_retriever(search_kwargs={"k": 50})
bm25_retriever = BM25_INDEX

# Hybrid: weighted combination of vector + BM25 via RRF
hybrid_retriever = EnsembleRetriever(
    retrievers=[vector_retriever, bm25_retriever],
    weights=[0.6, 0.4],  # 60% vector, 40% BM25 (tune on your eval)
)

# Rerank top-50 → top-10
reranker = CohereRerank(model="rerank-english-v3", top_n=10)

compressed_retriever = ContextualCompressionRetriever(
    base_compressor=reranker,
    base_retriever=hybrid_retriever,
)

def retrieve(query: str, user_acl: dict) -> list:
    """ACL-filtered, hybrid-retrieved, reranked top-10."""
    docs = compressed_retriever.invoke(query)
    return [d for d in docs if acl_allows(d.metadata, user_acl)]
```

ACL filtering happens **after rerank** — we rerank the top candidates, then drop the ones the user can't see. This is cheaper than ACL-filtering first (smaller set to filter) and safer than ACL-filtering last (we'd return nothing).

### Step 5 — The full chain (LCEL, with citations and streaming)

```python
# chain/rag_chain.py
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

from retrieval.hybrid import retrieve

model = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Answer the question using ONLY the sources below.

RULES:
1. If the sources don't contain the answer, say "I don't know" — never guess.
2. Cite each claim with [Source N] matching the source number.
3. If sources disagree, say so explicitly.
4. ≤ 200 words unless the question demands more."""),
    ("human", """SOURCES:
{context}

QUESTION: {question}

ANSWER:"""),
])

def format_context(docs):
    """Format the retrieved docs as numbered sources for the prompt."""
    return "\n\n".join(
        f"[Source {i+1}: {d.metadata.get('title', d.metadata.get('source', 'unknown'))}]\n{d.page_content}"
        for i, d in enumerate(docs)
    )

chain = (
    RunnablePassthrough.assign(
        sources=RunnableLambda(retrieve),
    )
    | RunnablePassthrough.assign(
        context=lambda x: format_context(x["sources"]),
    )
    | RAG_PROMPT
    | model
    | StrOutputParser()
).with_config({"run_name": "rag.v1"})
```

`RunnablePassthrough.assign` adds fields to the input dict without dropping the original. By the time the prompt runs, `context` and `sources` are populated.

### Step 6 — Streaming variant

```python
# chain/stream.py
from langchain_core.output_parsers import StrOutputParser

async def stream_rag(query: str, user_acl: dict):
    # Pre-fetch sources synchronously (cheap, parallel)
    sources = retrieve(query, user_acl)
    context = format_context(sources)

    # Stream the LLM response
    prompt_value = RAG_PROMPT.invoke({"context": context, "question": query})

    async for chunk in model.astream(prompt_value):
        yield {"chunk": chunk.content, "sources": [s.metadata for s in sources]}
```

For UI streaming, you fetch sources in parallel then stream the LLM. The user sees the citations appear immediately, the answer tokens stream in.

### Step 7 — ACL — the safety-critical part

```python
# acl.py
def acl_allows(doc_metadata: dict, user_acl: dict) -> bool:
    """Filter documents by user's workspace + role permissions."""
    # Workspace check
    if doc_metadata.get("workspace_id") != user_acl["workspace_id"]:
        return False

    # Visibility check
    visibility = doc_metadata.get("visibility", "workspace")
    if visibility == "public":
        return True
    if visibility == "workspace":
        return True
    if visibility == "team":
        return user_acl["team_id"] in doc_metadata.get("allowed_teams", [])
    if visibility == "restricted":
        return user_acl["user_id"] in doc_metadata.get("allowed_users", [])

    # Fail-closed: missing metadata = no access
    return False
```

**ACL at the retriever, not in the prompt.** The LLM is not trusted to enforce access control. If we returned a confidential doc to the retriever and just told the LLM "ignore it," a prompt injection would expose it.

### Step 8 — Eval harness

```python
# eval/run_eval.py
from langsmith import evaluate
from langchain_core.runnables import RunnableLambda
from chain.rag_chain import chain
from eval.dataset import load_rag_eval_set

# 200 hand-labeled (question, expected_doc_ids, expected_answer) triples
DATASET = "rag-internal-docs.v1"

# Evaluator 1: Recall@k — was the right doc in the retrieved top-10?
def recall_at_k(run, example):
    expected_ids = set(example.outputs["expected_doc_ids"])
    retrieved_ids = {s.metadata["doc_id"] for s in run.outputs["sources"]}
    return {"key": "recall_at_10", "score": len(expected_ids & retrieved_ids) / len(expected_ids)}

# Evaluator 2: Faithfulness — LLM-as-judge on whether every claim is in the sources
from langsmith.evaluation import LangChainStringEvaluator
faithfulness_judge = LangChainStringEvaluator(
    "labeled_score_string",
    config={"criteria": {"faithful": "Is every claim in the answer supported by the sources?"}, "normalize_by": 5},
)

# Evaluator 3: Citation accuracy — are the [Source N] markers correct?
citation_judge = LangChainStringEvaluator(
    "labeled_score_string",
    config={"criteria": {"citations": "Does each [Source N] citation refer to the correct source?"}, "normalize_by": 5},
)

# Wrap chain to expose sources in outputs
def chain_with_sources(inputs):
    out = {"answer": chain.invoke(inputs)}
    # Re-retrieve to expose sources (cheaper: store from chain, but works)
    out["sources"] = retrieve(inputs["question"], inputs["user_acl"])
    return out

results = evaluate(
    RunnableLambda(chain_with_sources),
    data=DATASET,
    evaluators=[recall_at_k, faithfulness_judge, citation_judge],
    experiment_prefix="rag-v1",
)

# CI gate
assert results["recall_at_10"]["mean"] >= 0.85, "recall regressed"
assert results["faithfulness"]["mean"] >= 4.0, "faithfulness regressed"
```

Three evaluators. Each catches a different failure mode. **Recall@k** catches retrieval misses; **faithfulness** catches hallucinations; **citation accuracy** catches mis-attribution.

### Step 9 — Cost roll-up

```
   At 5K queries/day, 150K queries/month:
   ──────────────────────────────────────
   Cohere embed (query):  150K × 200 tok × $0.10/M   = $3/mo
   Qdrant search:         managed, 32K vectors       = $30/mo
   BM25:                  in-memory, $0              = $0/mo
   Cohere rerank:         150K × $0.001             = $150/mo
   Claude Sonnet:         150K × (1.5K in + 200 out) = $300 + $450 = $750/mo
   LangSmith traces:                               = $50/mo
   ─────────────────────────────────────────
   Total: ~$983/mo for 150K queries = $0.007/query
```

The dominant cost is the LLM (rerank + Sonnet). Vector DB and embeddings are negligible. **Cost is driven by quality choices, not infrastructure.**

### Step 10 — Failure modes the eval set catches

| Failure | Symptom | Eval catches |
|---|---|---|
| Splitter change → mid-paragraph chunks | Worse retrieval | recall@k drops |
| Embedding model swap | Different similarity space | recall@k drops, faithfulness drops |
| Removed BM25 | Misses exact terms (e.g., "policy-D-12") | recall@k drops on identifier queries |
| Removed rerank | Top-10 includes irrelevant docs | faithfulness drops |
| ACL bug → returns restricted doc | Security incident | Recall@k fine; need separate security test |
| LLM vendor update | Different phrasing | citation_accuracy drops |
| New doc type without loader | Docs silently missing | recall@k drops on those queries |

The eval set is the **regression detector** for every change. Without it, you're shipping blind.

### What this example demonstrates

1. **LangChain primitives compose.** Loaders → splitter → store → retriever → rerank → prompt → model → parser.
2. **Hybrid + rerank is the default.** Vector-only misses exact terms; rerank recovers 5–10% recall.
3. **ACL is at the retriever, not in the prompt.** Defense in depth.
4. **Citations are a first-class output.** Without them, users can't trust the answer.
5. **Eval catches what you didn't anticipate.** The set is the moat.

Read this example once and you understand the LangChain RAG implementation. Read it twice and you understand production RAG systems.

---

## What Comes Next

> Lesson 2 — **Document loaders** — the messy reality of PDFs, Notion, Confluence, and S3. OCR, tables, and the 80% rule (only 3% of enterprise data is plain text).