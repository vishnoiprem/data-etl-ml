# Lesson 6 — LLM Frameworks

> **Type:** Article · Module 5 · RAG & LLM Data Infrastructure
> When to use LangChain, LlamaIndex, Haystack, or roll your own.

---

## The 2026 state of LLM frameworks

```
   MOST ABSTRACTION                     LEAST ABSTRACTION
   ──────────────────────────────────────────────────────────────
   LangChain / LangGraph                Custom Python + LLM SDK
   LlamaIndex                           OpenAI / Anthropic / Cohere SDK
   Haystack                             Direct HTTP to model API
   Semantic Kernel

   (frameworks)                         (you own everything)
```

Each level trades **time-to-first-demo** for **time-to-production-quality**.

---

## The decision matrix

| Need | Pick |
|---|---|
| Prototype in a day | LangChain or LlamaIndex |
| Production RAG | Custom Python or LlamaIndex |
| Agent with tool use | LangGraph |
| Document-heavy load | LlamaIndex |
| Search-focused (RAG only) | Custom + a vector DB |
| Multi-modal pipelines | Custom + vendor SDKs |
| Multi-agent orchestration | LangGraph or custom state machines |

---

## LangChain / LangChain Expression Language (LCEL) / LangGraph

**Strengths:**
- Massive ecosystem of integrations (vector DBs, embedders, loaders, splitters)
- LCEL for declarative chains: `prompt | llm | parser`
- LangGraph for stateful multi-step agents
- Strong community, frequent updates

**Weaknesses:**
- High abstraction churn — APIs change between versions
- Hard to debug at scale — too many layers
- Performance overhead vs. raw SDK
- "Magic" — many internals are opaque

**When to use:**
- Quick prototypes
- Agent / multi-step flows (LangGraph is genuinely good here)
- You want batteries-included loaders (Notion, Slack, Confluence, S3, etc.)

```python
# LCEL — declarative chain
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_template(
    "Answer using only the context: {context}\n\nQuestion: {question}"
)
chain = prompt | ChatOpenAI(model="gpt-4o") | StrOutputParser()
answer = chain.invoke({"context": ctx, "question": q})
```

---

## LlamaIndex

**Strengths:**
- Document-first design (great for RAG)
- Built-in ingest pipelines (loaders, splitters, embedders)
- Strong query engine abstractions
- Better than LangChain for "search over my docs"
- Simpler API surface

**Weaknesses:**
- Smaller ecosystem than LangChain
- Less flexible for non-RAG workflows
- Some abstractions leak through

**When to use:**
- Production RAG is your primary use case
- You want document-ingest utilities built in
- Less need for tool-using agents

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

documents = SimpleDirectoryReader("docs/").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
answer = query_engine.query("What's the refund policy?")
```

---

## Haystack

**Strengths:**
- Built by deepset, production-focused
- Pipeline abstractions are clean
- Strong on enterprise RAG (PDFs, tables, multi-modal)
- Good agent and tool story

**Weaknesses:**
- Smaller community than LangChain
- Some learning curve

**When to use:**
- Enterprise search / RAG with complex document types
- You want declarative pipelines with clear data flow
- You're deploying on Kubernetes

```python
from haystack import Pipeline
from haystack.components.retrievers import InMemoryBM25Retriever

pipe = Pipeline()
pipe.add_component("retriever", InMemoryBM25Retriever(document_store=ds))
results = pipe.run({"retriever": {"query": "refund policy"}})
```

---

## When to roll your own

You probably should, for production:

```python
# Custom RAG loop, ~80 lines of Python
def rag(query, vector_db, embedder, llm, top_k=10):
    # 1. embed query
    q_vec = embedder.embed(query)
    # 2. retrieve
    candidates = vector_db.search(q_vec, k=top_k, filter=acl_filter(user))
    # 3. (optional) rerank
    candidates = reranker.rerank(query, candidates)[:5]
    # 4. build prompt
    context = format_with_citations(candidates)
    prompt = assemble_prompt(query, context, history)
    # 5. call LLM
    answer = llm.complete(prompt, temperature=0)
    # 6. log + return with citations
    log_interaction(query, answer, candidates)
    return answer, candidates
```

**Why custom wins in production:**
- **Predictable cost.** No magic callbacks, no hidden prompts.
- **Predictable latency.** You see every LLM call.
- **Easy to debug.** One file, one flow.
- **No framework upgrade tax.**
- **Eval-friendly.** Pure Python is easy to test.

The framework "saves you 2 days" but costs you "2 weeks" at scale. This is why most senior teams migrate from LangChain to custom within 6 months of production.

---

## The hybrid pattern

You can use a framework for **parts** of the system and custom for the rest:

```
   framework handles        custom handles
   ─────────────────        ────────────────
   • loader ecosystem       • ACL filtering
   • splitters              • observability + eval
   • basic chain            • citation logic
   • tool/agent abstractions• cost monitoring
                            • production hardening
```

This gives you the time-to-demo of the framework plus the production quality of custom.

---

## The "LangGraph for agents" sweet spot

Agents are different. **LangGraph genuinely helps** with stateful, multi-step, branching agent logic. Most of the "agent" infra (state, cycles, human-in-the-loop, persistence) is non-trivial to build from scratch.

```python
from langgraph.graph import StateGraph

# Build a ReAct agent that can call tools and recover from errors
# LangGraph handles state, branching, retries, observability
```

For non-agentic RAG, custom is fine. For agents, **LangGraph is currently the best-of-breed abstraction**.

---

## The "vector store wrappers" question

Every framework has its own vector store abstraction. **Don't use them in production.** Talk to the vector DB directly:

```python
# Don't do this in production
from langchain.vectorstores import Pinecone
vs = Pinecone.from_documents(docs, embeddings, index_name="my-index")

# Do this
from pinecone import Pinecone
client = Pinecone(api_key=...)
index = client.Index("my-index")
index.upsert(vectors=..., metadata=...)
```

The wrapper hides capability (metadata filters, namespaces, hybrid search). Direct calls give you everything.

---

## The "common mistakes" with frameworks

1. **Pin versions.** LangChain changes monthly. Pin a working version; upgrade deliberately.
2. **Don't import everything.** `from langchain import *` is a recipe for bloat.
3. **Read the source.** When the abstraction breaks, you need to debug.
4. **Measure, don't assume.** A framework doesn't always add overhead, but it does sometimes — measure.

---

## What Comes Next

> Lesson 7 — **Quiz: RAG & LLM Data Infrastructure** — self-check on the seven lessons of Module 5.
