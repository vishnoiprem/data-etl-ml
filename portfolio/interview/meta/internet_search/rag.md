# RAG (Retrieval-Augmented Generation)

> **Note on sourcing**: The Meta DE interview-prep notes in this directory do not contain RAG content. This file is grounded in widely-cited public knowledge (Lewis et al. 2020 original RAG paper; standard practice in vector search; industry tooling from LangChain, LlamaIndex, Pinecone, OpenAI, RAGAS). No private-company specifics are invented.

## 1. The Problem RAG Solves

An LLM:
- **Has a training cutoff** → doesn't know anything new.
- **Hallucinates** → makes up facts that sound plausible.
- **Doesn't know your private data** → can't answer questions about your company's docs, code, or customers.

**RAG fixes all three** by retrieving relevant context at query time and giving it to the LLM.

```
Without RAG:
  User ─► "What's our Q3 churn policy?"
       ─► LLM: "I don't have access to your company's policies..." (Q3)

With RAG:
  User ─► "What's our Q3 churn policy?"
       ─► Retrieve relevant chunks from your knowledge base
       ─► LLM: "Based on your churn doc (updated Aug 2024), the policy is..." (Q3)
```

## 2. The Pipeline (How It Works)

```
┌─────────────────────────────────────────────────────────────┐
│                       INGESTION (offline)                   │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
        ┌────────────────────────────────────────┐
        │   1. Documents (PDFs, docs, code, ...)  │
        └────────────────┬───────────────────────┘
                                ▼
        ┌────────────────────────────────────────┐
        │   2. Chunking                           │
        │      - Split docs into chunks            │
        │      - 200–800 tokens typical            │
        │      - Keep metadata (source, page, ...) │
        └────────────────┬───────────────────────┘
                                ▼
        ┌────────────────────────────────────────┐
        │   3. Embedding                           │
        │      - Each chunk → vector               │
        │      - via embedding model (e.g.,        │
        │        text-embedding-3, BGE, E5, Cohere)│
        └────────────────┬───────────────────────┘
                                ▼
        ┌────────────────────────────────────────┐
        │   4. Vector Store                        │
        │      - pgvector, Pinecone, Weaviate,    │
        │        FAISS, Qdrant, Chroma, LanceDB   │
        └────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       QUERY (online)                        │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
        ┌────────────────────────────────────────┐
        │   5. Query Embedding                     │
        │      - Same model as ingest              │
        └────────────────┬───────────────────────┘
                                ▼
        ┌────────────────────────────────────────┐
        │   6. Retrieve top-K chunks              │
        │      - Cosine / dot / euclidean          │
        │      - K = 3–10 typical                  │
        │      - Optional reranking (cross-encoder)│
        └────────────────┬───────────────────────┘
                                ▼
        ┌────────────────────────────────────────┐
        │   7. Prompt construction                │
        │      - System: "Answer only from context"│
        │      - Context: [retrieved chunks]      │
        │      - User: original question          │
        └────────────────┬───────────────────────┘
                                ▼
        ┌────────────────────────────────────────┐
        │   8. LLM generates answer               │
        └────────────────┬───────────────────────┘
                                ▼
        ┌────────────────────────────────────────┐
        │   9. Cite sources (return chunk IDs)    │
        └────────────────────────────────────────┘
```

**Why this works**: the LLM no longer relies on memorized facts. It sees **fresh, retrieved context** at every query. Less hallucination. Domain-specific answers are possible.

## 3. When to Use RAG

**Use RAG when**:
- You need answers grounded in your own docs / data (private + public mix).
- Knowledge changes frequently (policies, prices, releases).
- You need citations/audit trails (compliance, support).
- The domain is narrow but deep (legal, medical, internal SOPs).
- Cost matters: smaller models + retrieved context > giant model alone.

**Don't use RAG when**:
- You can fit everything in the context window (small knowledge base, <100 pages).
- You need strict logic / math (LLMs still hallucinate with retrieved math).
- You need real-time streaming data (use tool-calling + APIs instead).
- The task is pure creative generation (no grounding needed).

**Alternatives to RAG**:
- **Long context** (Gemini 1.5 Pro 2M, Claude 200k): just paste everything in. Costs more, slower, but no chunking.
- **Fine-tuning**: bake knowledge into the model. Doesn't help with freshness; high cost; no citations.
- **Tool-calling / agents**: model queries APIs (search, DBs, calculators). RAG is just a special case of retrieval-as-tool.

## 4. Example — Customer Support Bot

**Scenario**: SaaS company with 5,000 help articles. Customer asks a question.

```
Q: "How do I reset my billing payment method?"

Step 1 (embed query)  → vector(q)
Step 2 (retrieve top-5) → [
  chunk_1: "How to change payment method...",
  chunk_2: "Billing FAQ: cards, ACH, wallets",
  chunk_3: "Step-by-step: update billing",
  chunk_4: "Troubleshoot failed payments",
  chunk_5: "Contact support: billing@..."
]
Step 3 (rerank optional) → top-2 most relevant
Step 4 (prompt)         → system: "Answer only from these articles. Cite sources."
                           context: [chunk_1, chunk_3]
                           user: "How do I reset my billing payment method?"
Step 5 (LLM)            → "To change your payment method, go to Billing → Settings →
                            Payment. [Source: article 4823]"
```

**What's good**:
- The answer references your actual help docs.
- Citation lets the user verify.
- If you update the docs, answers update automatically.

## 5. Working Prototype (LangChain + OpenAI + FAISS, ~50 lines)

```python
"""
Minimal RAG prototype using LangChain, OpenAI, and FAISS.
Requires:
    pip install langchain langchain-openai faiss-cpu tiktoken
"""

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# -------- 1. INGEST --------

documents = [
    "Q3 churn policy: customers inactive >90 days enter reactivation. " +
    "Offer 1-month free + 15% retention discount. Owner: CX team.",
    "Pricing: Pro $49/mo, Business $149/mo, Enterprise custom. " +
    "Annual discount 20% if paid upfront.",
    "Refund window: 30 days, no questions. Beyond 30 days, escalate " +
    "to manager. Refunds > $500 require Finance approval.",
]

# Chunk (small docs can skip this; large ones must)
splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
chunks = splitter.create_documents(documents)

# Embed and store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectordb = FAISS.from_documents(chunks, embeddings)
retriever = vectordb.as_retriever(search_kwargs={"k": 3})

# -------- 2. RETRIEVE + GENERATE --------

prompt = ChatPromptTemplate.from_template("""
Answer the question using ONLY the context below.
If the answer isn't in the context, say "I don't know."
Cite the source like [chunk <n>].

Context:
{context}

Question: {question}
""")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def format_docs(docs):
    return "\n\n".join(f"[chunk {i}] " + d.page_content
                       for i, d in enumerate(docs, 1))

chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt | llm | StrOutputParser()
)

# -------- 3. ASK --------

answer = chain.invoke("What's our refund policy for $700?")
print(answer)
```

**Expected output**:
> Refunds over $500 require Finance approval. Beyond the 30-day window, escalate to a manager. [chunk 3]

## 6. The Hard Parts (Common Pitfalls)

### a) Chunking
- **Too small** → loses context.
- **Too large** → retrieval returns irrelevant content.
- **No overlap** → loses context at boundaries.
- **Fix**: chunk 200–800 tokens, 10–20% overlap, keep section/page metadata.

### b) Retrieval quality
- Semantic search alone misses exact-match needs ("error 503").
- **Fix**: hybrid search (BM25 + vector), or pre-filter by metadata.

### c) Context stuffing
- Stuffing 50 chunks into the prompt hurts performance.
- **Fix**: rerank (cross-encoder), compress (summarize), or limit to top-5.

### d) Hallucination still happens
- LLM may ignore context and invent.
- **Fix**: prompt engineering ("use ONLY context"), low temperature, citation requirements.

### e) Stale indexes
- Docs update but vector store doesn't.
- **Fix**: incremental indexing, refresh-on-write, or nightly rebuilds.

### f) Embedding mismatches
- Query embedding model ≠ doc embedding model = nonsense results.
- **Fix**: lock the model and version it.

### g) Eval is hard
- Noisy ground truth; subjective "is the answer good?".
- **Fix**: use frameworks like **RAGAS**, **TruLens**, or **LangSmith** for retrieval-precision and answer-relevance metrics.

## 7. Advanced Patterns

| Pattern | What it adds |
|---|---|
| **Hybrid search** | BM25 + dense vectors → better recall |
| **Reranking** | Cross-encoder rerank top-50 → keep top-5 → cleaner context |
| **Multi-query** | Generate K variants of the query, retrieve for each, deduplicate |
| **HyDE** | Generate a hypothetical answer, embed that, retrieve for it |
| **Parent-document retriever** | Retrieve small chunks but return their parent context |
| **Agentic RAG** | LLM decides when/what to retrieve (multi-hop, follow-up queries) |
| **Graph RAG** | Build a knowledge graph; retrieve subgraphs, not just chunks |
| **Self-RAG** | Model critiques its own retrieval + answer, re-retrieves if needed |
| **CRAG** | Corrective RAG: validate retrieved chunks, fall back to web search if low-confidence |

## 8. Common Interview Q&A

**Q. "What is RAG and why use it?"**
> Retrieval-Augmented Generation: retrieve relevant context from a vector store and pass it to the LLM as part of the prompt. Solves LLM knowledge cutoffs, hallucinations, and private-data blind spots without the latency of fine-tuning.

**Q. "RAG vs fine-tuning?"**
> RAG = inject knowledge at query time. Fresh, no training cost, has citations. Fine-tuning = bake knowledge into weights. Doesn't help freshness, expensive, no built-in citation. Often combine: fine-tune for style/format, RAG for facts.

**Q. "How do you chunk?"**
> 200–800 tokens, 10–20% overlap, preserve structure (markdown headers, code blocks). Add metadata (source, section, date). For structured docs, parent-document retriever works well.

**Q. "How do you evaluate RAG?"**
> Two axes: **retrieval quality** (precision/recall of retrieved chunks) and **answer quality** (faithfulness to context, correctness). Use RAGAS, TruLens, LangSmith, or hand-curated eval sets.

**Q. "What if retrieval is bad?"**
> Improve in order: better chunking → better embeddings → hybrid search → reranking → query rewriting. Don't add fancy agents before fixing the foundation.

**Q. "When NOT to use RAG?"**
> When the knowledge base is small enough to fit in context, or when you need precise reasoning over tables/numbers (use tool-calling instead).

**Q. "How do you keep the index fresh?"**
> Incremental indexing on doc updates. Nightly full rebuild for reconciliation. Or stream events from the doc system to the indexer.

## 9. References (Public Sources)

- Lewis, P., et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* NeurIPS 2020. [arxiv.org/abs/2005.11401](https://arxiv.org/abs/2005.11401) — original RAG paper.
- Gao, Y., et al. (2023). *Retrieval-Augmented Generation for Large Language Models: A Survey.* [arxiv.org/abs/2312.10997](https://arxiv.org/abs/2312.10997) — comprehensive survey of RAG techniques and patterns.
- Documentation: LangChain, LlamaIndex, Pinecone, Weaviate, Qdrant, Chroma, pgvector, OpenAI Cookbook, Anthropic prompt docs.
- Evaluation frameworks: RAGAS ([ragas.io](https://ragas.io)), TruLens ([trulens.org](https://www.trulens.org/)), LangSmith.