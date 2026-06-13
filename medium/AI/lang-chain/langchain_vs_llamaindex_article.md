# LangChain vs LlamaIndex: Which One Should You Use? A Practical Guide for Retail AI

*I built the same Makro supplier contract search with both frameworks. Here is exactly what I learned.*

---

Every data engineer building LLM applications hits the same fork in the road early:

> **"Should I use LangChain or LlamaIndex?"**

Both are free. Both are Python. Both work with OpenAI, Azure OpenAI, and every major LLM. The documentation for both will tell you they can do everything.

After building Axtra360 — CPAxtra's AI platform serving Makro and Lotus's across four countries — I have used both extensively. Here is the honest answer, with working code for each.

---

## The One-Sentence Decision Rule

**Use LlamaIndex when your problem is: "How do I search and retrieve from my documents accurately?"**

**Use LangChain when your problem is: "How do I build an application, agent, or workflow powered by an LLM?"**

That is genuinely the whole decision. Everything below is detail.

---

## The Comparison — Every Dimension

| Feature | LangChain | LlamaIndex |
|---|---|---|
| Primary purpose | Build LLM apps and agents | Search and retrieval from data |
| Best at | Chains, agents, orchestration, memory | Indexing, chunking, retrieval, RAG |
| Learning curve | Easy to moderate | Moderate |
| Flexibility | Very high — customise everything | Good within retrieval scope |
| Ecosystem | Complete (LangServe, LangSmith, LangGraph) | Focused on data pipelines |
| Documentation | Extensive | Good |
| For complex RAG | Good but more manual work | Excellent — built for this |
| For agents | Excellent | Limited |
| For deployment | LangServe built-in | Need to wrap manually |
| Cost | Free | Free |

---

## Why They Feel Confusing

Both frameworks can do RAG. Both can do chatbots. Both can connect to vector stores. So why does it seem like they overlap?

Because they do — in the middle. Think of it as two circles:

```
LlamaIndex territory:
  Document loading → chunking → embedding → indexing → retrieval
  ← specialised, optimised, many built-in strategies

LangChain territory:
  Chains → agents → memory → tools → deployment → monitoring
  ← generalised, flexible, whole application layer

Overlap zone (both work):
  Basic RAG chatbot
  Q&A over documents
  Simple search applications
```

For anything in the overlap zone, use what you already know. For anything outside the overlap — LlamaIndex for pure retrieval pipelines, LangChain for anything involving agents, memory, tools, or deployment.

---

## Part 1 — LlamaIndex: Supplier Contract Search

This is where LlamaIndex shines. Makro has hundreds of supplier contracts in Thai and English. The procurement team needs to query them: "What is the penalty clause in the Nestle contract?" — and get the right answer from the right document.

### Install

```python
%pip install llama-index llama-index-llms-azure-openai llama-index-embeddings-azure-openai
```

### Full RAG pipeline with LlamaIndex

```python
import os
from pathlib import Path

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding

# ── Step 1: Configure LLM and embeddings ────────────────────────────────────
llm = AzureOpenAI(
    model             = "gpt-4o",
    deployment_name   = os.environ["AZURE_OPENAI_DEPLOYMENT"],
    api_key           = os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint    = os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version       = "2024-02-01",
    temperature       = 0.1,   # low temp for factual contract queries
)

embed_model = AzureOpenAIEmbedding(
    model           = "text-embedding-3-large",
    deployment_name = "text-embedding-3-large",
    api_key         = os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint  = os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version     = "2024-02-01",
)

# Apply globally — no need to pass to every component
Settings.llm         = llm
Settings.embed_model = embed_model
Settings.chunk_size  = 512    # tokens per chunk
Settings.chunk_overlap = 50   # overlap between chunks

# ── Step 2: Load supplier contract documents ─────────────────────────────────
# Directory structure:
# ./contracts/
#   ├── nestle_2024.pdf
#   ├── unilever_2024.pdf
#   ├── cp_foods_2024.pdf
#   └── betagro_2024.pdf

CONTRACTS_DIR  = "./contracts"
INDEX_SAVE_DIR = "./index_storage"

# Load documents with metadata
documents = SimpleDirectoryReader(
    CONTRACTS_DIR,
    required_exts    = [".pdf", ".docx", ".txt"],
    recursive        = True,
    filename_as_id   = True,
).load_data()

print(f"Loaded {len(documents)} document chunks")

# Add custom metadata to each document
for doc in documents:
    filename = Path(doc.metadata.get("file_name", "")).stem
    doc.metadata.update({
        "supplier":      filename.split("_")[0].upper(),   # NESTLE, UNILEVER etc
        "contract_year": filename.split("_")[-1] if "_" in filename else "2024",
        "country":       "TH",
        "document_type": "supplier_contract",
    })

# ── Step 3: Build the index ──────────────────────────────────────────────────
# SentenceSplitter preserves sentence boundaries — better than fixed-size chunks
# for legal/contract documents where a sentence split mid-clause loses meaning

splitter = SentenceSplitter(
    chunk_size    = 512,
    chunk_overlap = 50,
)

PERSIST_INDEX = Path(INDEX_SAVE_DIR).exists()

if PERSIST_INDEX:
    # Load existing index from disk (fast — no re-embedding)
    storage_context = StorageContext.from_defaults(persist_dir=INDEX_SAVE_DIR)
    index = load_index_from_storage(storage_context)
    print("Index loaded from disk")
else:
    # Build index — embeds all chunks (slow first time, fast after)
    index = VectorStoreIndex.from_documents(
        documents,
        transformations=[splitter],
        show_progress=True,
    )
    index.storage_context.persist(persist_dir=INDEX_SAVE_DIR)
    print("Index built and saved to disk")

# ── Step 4: Build retriever and query engine ─────────────────────────────────
retriever = VectorIndexRetriever(
    index          = index,
    similarity_top_k = 5,   # retrieve top 5 most relevant chunks
)

# Filter out low-similarity chunks — prevents hallucination from irrelevant context
postprocessor = SimilarityPostprocessor(similarity_cutoff=0.70)

query_engine = RetrieverQueryEngine(
    retriever         = retriever,
    node_postprocessors = [postprocessor],
)

# ── Step 5: Query the contracts ──────────────────────────────────────────────
queries = [
    "What is the penalty clause for late delivery in the Nestle contract?",
    "สัญญา Unilever กำหนดระยะเวลาการชำระเงินไว้กี่วัน?",
    "Which suppliers have halal certification requirements?",
    "What is the minimum order quantity for CP Foods frozen products?",
    "สัญญาไหนมีข้อกำหนดเรื่องบรรจุภัณฑ์ที่เป็นมิตรกับสิ่งแวดล้อม?",
]

for query in queries:
    print(f"\nQ: {query}")
    response = query_engine.query(query)
    print(f"A: {response}")
    # LlamaIndex automatically shows source nodes
    print(f"Sources: {[node.metadata.get('supplier') for node in response.source_nodes]}")
```

### Advanced: metadata filtering for specific supplier

```python
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters

# Query only Nestle contracts — ignore all other supplier documents
nestle_filters = MetadataFilters(filters=[
    MetadataFilter(key="supplier", value="NESTLE"),
    MetadataFilter(key="contract_year", value="2024"),
])

nestle_engine = index.as_query_engine(
    similarity_top_k = 3,
    filters          = nestle_filters,
)

response = nestle_engine.query(
    "What are the quality inspection requirements for chilled products?"
)
print(response)
```

### LlamaIndex sub-question query engine — multi-document reasoning

```python
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import SubQuestionQueryEngine

# Build separate indices per supplier for precise multi-document reasoning
supplier_engines = {}
for supplier in ["NESTLE", "UNILEVER", "CP_FOODS"]:
    supplier_docs = [d for d in documents if d.metadata.get("supplier") == supplier]
    if supplier_docs:
        supplier_engines[supplier] = VectorStoreIndex.from_documents(
            supplier_docs
        ).as_query_engine()

# Wrap each as a tool
tools = [
    QueryEngineTool(
        query_engine = engine,
        metadata     = ToolMetadata(
            name        = f"{supplier.lower()}_contracts",
            description = f"Supplier contract documents for {supplier}"
        )
    )
    for supplier, engine in supplier_engines.items()
]

# SubQuestionQueryEngine breaks complex questions into sub-questions
# then synthesises answers — key strength of LlamaIndex
sub_question_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools = tools,
    verbose            = True,
)

# This single query automatically:
# 1. Sub-question: "What is Nestle's delivery penalty?"
# 2. Sub-question: "What is Unilever's delivery penalty?"
# 3. Sub-question: "What is CP Foods' delivery penalty?"
# 4. Synthesises: comparison across all three
response = sub_question_engine.query(
    "Compare the delivery penalty clauses across Nestle, Unilever, and CP Foods contracts. "
    "Which supplier has the strictest terms?"
)
print(response)
```

---

## Part 2 — LangChain: Supplier Contract Agent with Memory

Now the same problem with LangChain. Notice: LangChain can do the retrieval, but where it adds unique value is the agent layer — memory, tools, multi-step reasoning, conversation history.

### Install

```python
%pip install langchain langchain-openai langchain-community faiss-cpu
```

### RAG chain with LangChain

```python
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import FileChatMessageHistory
from pathlib import Path

# ── LLM and embeddings ───────────────────────────────────────────────────────
llm = AzureChatOpenAI(
    azure_deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"],
    azure_endpoint   = os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key          = os.environ["AZURE_OPENAI_API_KEY"],
    api_version      = "2024-02-01",
    temperature      = 0.1,
    streaming        = True,
)

embeddings = AzureOpenAIEmbeddings(
    azure_deployment = "text-embedding-3-large",
    azure_endpoint   = os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key          = os.environ["AZURE_OPENAI_API_KEY"],
)

# ── Load and chunk documents ─────────────────────────────────────────────────
loader   = PyPDFDirectoryLoader("./contracts/")
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size    = 512,
    chunk_overlap = 50,
    separators    = ["\n\n", "\n", ".", "。", " ", ""]  # handles Thai text
)
chunks = splitter.split_documents(documents)

# Add Makro-specific metadata
for chunk in chunks:
    source = chunk.metadata.get("source", "")
    chunk.metadata.update({
        "supplier":  Path(source).stem.split("_")[0].upper(),
        "doc_type":  "supplier_contract",
        "country":   "TH"
    })

# ── Build vector store ───────────────────────────────────────────────────────
FAISS_PATH = "./faiss_index"
if Path(FAISS_PATH).exists():
    vectorstore = FAISS.load_local(FAISS_PATH, embeddings,
                                   allow_dangerous_deserialization=True)
    print("FAISS index loaded from disk")
else:
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(FAISS_PATH)
    print("FAISS index built and saved")

retriever = vectorstore.as_retriever(
    search_type   = "mmr",    # Max Marginal Relevance — more diverse results
    search_kwargs = {"k": 5, "fetch_k": 20}
)

# ── RAG prompt ───────────────────────────────────────────────────────────────
rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a procurement contract specialist for CPAxtra (Makro/Lotus's).
Answer questions based strictly on the provided contract documents.
If the answer is not in the documents, respond: 'ไม่พบข้อมูลในสัญญาที่มีอยู่'
Always cite the supplier name and contract section you reference.
Respond in the same language as the question (Thai or English)."""),
    MessagesPlaceholder(variable_name="history"),
    ("human", """Contract documents:
{context}

Question: {question}"""),
])

def format_docs(docs):
    return "\n\n---\n\n".join([
        f"[{doc.metadata.get('supplier','?')} | Page {doc.metadata.get('page','?')}]\n{doc.page_content}"
        for doc in docs
    ])

# ── Chain with memory — LangChain's key advantage over LlamaIndex ────────────
base_rag_chain = (
    RunnableParallel({
        "context":  retriever | format_docs,
        "question": RunnablePassthrough(),
        "history":  RunnablePassthrough(),
    })
    | rag_prompt
    | llm
    | StrOutputParser()
)

# Wrap with conversation memory
MEMORY_DIR = Path("./chat_histories")
MEMORY_DIR.mkdir(exist_ok=True)

conversational_rag = RunnableWithMessageHistory(
    base_rag_chain,
    lambda session_id: FileChatMessageHistory(
        str(MEMORY_DIR / f"{session_id}.json")
    ),
    input_messages_key   = "question",
    history_messages_key = "history",
)

# ── Multi-turn conversation — remembers context across turns ─────────────────
config = {"configurable": {"session_id": "procurement_team_001"}}

# Turn 1
r1 = conversational_rag.invoke(
    {"question": "What is the minimum order quantity for Nestle products?"},
    config=config
)
print("Turn 1:", r1)

# Turn 2 — remembers "Nestle" from Turn 1, no need to repeat
r2 = conversational_rag.invoke(
    {"question": "And what about the payment terms for the same supplier?"},
    config=config
)
print("Turn 2:", r2)

# Turn 3 — comparative question across memory + documents
r3 = conversational_rag.invoke(
    {"question": "How does that compare to Unilever's payment terms?"},
    config=config
)
print("Turn 3:", r3)
```

### LangChain agent with tools — the real differentiator

```python
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_community.vectorstores import FAISS

# Define tools the agent can use
@tool
def search_contracts(query: str) -> str:
    """Search Makro supplier contracts for specific clauses, terms, or conditions.
    Use for questions about penalties, payment terms, MOQ, delivery, quality requirements."""
    docs = retriever.get_relevant_documents(query)
    return format_docs(docs)

@tool
def get_supplier_list() -> str:
    """Returns list of all suppliers with active contracts in the system."""
    suppliers = list(set([
        chunk.metadata.get("supplier", "UNKNOWN")
        for chunk in chunks
    ]))
    return f"Active suppliers: {', '.join(sorted(suppliers))}"

@tool
def calculate_penalty(base_amount: float, penalty_rate: float, days_late: int) -> str:
    """Calculate financial penalty for late delivery.
    Args:
        base_amount: Contract value in Thai Baht
        penalty_rate: Penalty as decimal (e.g. 0.02 for 2%)
        days_late: Number of days delivery is late
    """
    daily_penalty = base_amount * penalty_rate
    total_penalty = daily_penalty * days_late
    return (f"Daily penalty: ฿{daily_penalty:,.2f} | "
            f"Total for {days_late} days: ฿{total_penalty:,.2f}")

# Agent prompt
agent_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a senior procurement analyst at CPAxtra (Makro/Lotus's).
You have access to all supplier contracts and can calculate financial impacts.
Always provide specific contract references when answering.
Respond in the same language as the question — Thai or English."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Create agent
tools    = [search_contracts, get_supplier_list, calculate_penalty]
agent    = create_openai_tools_agent(llm, tools, agent_prompt)
executor = AgentExecutor(
    agent   = agent,
    tools   = tools,
    verbose = True,   # shows reasoning steps
    max_iterations = 5,
)

# The agent reasons through multiple steps autonomously:
# Step 1: search_contracts("Nestle late delivery penalty rate")
# Step 2: calculate_penalty(500000, 0.02, 7)
# Step 3: synthesise final answer
response = executor.invoke({
    "input": "Nestle delivered an order worth ฿500,000 seven days late. "
             "What is the total financial penalty according to the contract?",
    "chat_history": []
})
print(response["output"])
```

---

## Part 3 — Side by Side: Same Task, Both Frameworks

This is the most useful comparison. Same task — "Query supplier contracts" — implemented in both:

```python
# ══════════════════════════════════════════════════════════════
# TASK: Find all contracts where delivery penalty > 2%
# ══════════════════════════════════════════════════════════════

# ── LlamaIndex approach ──────────────────────────────────────
# Strengths: built-in metadata filtering, clean retrieval API
from llama_index.core.vector_stores import (
    MetadataFilter, MetadataFilters, FilterOperator
)

penalty_engine = index.as_query_engine(
    similarity_top_k = 10,
    response_mode    = "tree_summarize",   # synthesises across many chunks
)
llamaindex_result = penalty_engine.query(
    "Which supplier contracts have a late delivery penalty rate greater than 2%? "
    "List each supplier and their penalty rate."
)
print("LlamaIndex:", llamaindex_result)

# ── LangChain approach ───────────────────────────────────────
# Strengths: easier to add post-processing, connect to downstream actions
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from typing import List

class PenaltyResult(BaseModel):
    supplier:     str
    penalty_rate: str
    contract_ref: str

penalty_prompt = ChatPromptTemplate.from_messages([
    ("system", """Extract penalty information from contracts.
Return JSON: {{"results": [{{"supplier": "NAME", "penalty_rate": "X%", "contract_ref": "section"}}]}}"""),
    ("human", "Contracts:\n{context}\n\nFind all delivery penalty rates above 2%."),
])

penalty_chain = (
    {"context": retriever | format_docs}
    | penalty_prompt
    | llm
    | JsonOutputParser()
)

langchain_result = penalty_chain.invoke(
    "delivery penalty rate greater than 2 percent"
)
print("LangChain:", langchain_result)

# LlamaIndex gives better raw retrieval accuracy
# LangChain gives structured JSON output easier to use downstream
```

---

## Part 4 — Combining Both in One Pipeline

At CPAxtra we actually use both together for DOC-LM. LlamaIndex handles the retrieval — it is simply better at finding the right chunks. LangChain handles the application layer — memory, agents, LangServe deployment, LangSmith monitoring.

```python
# Hybrid architecture — LlamaIndex retriever + LangChain chain
# Used in Axtra360 DOC-LM service

from llama_index.core import VectorStoreIndex
from langchain_core.runnables import RunnableLambda

# LlamaIndex retriever as a LangChain-compatible component
class LlamaIndexRetriever:
    """Wraps LlamaIndex retriever for use inside a LangChain chain."""

    def __init__(self, index, top_k=5):
        self.retriever = index.as_retriever(similarity_top_k=top_k)

    def retrieve(self, query: str) -> str:
        nodes = self.retriever.retrieve(query)
        return "\n\n---\n\n".join([
            f"[{node.metadata.get('supplier','?')} | score:{node.score:.2f}]\n{node.text}"
            for node in nodes
        ])

llama_retriever = LlamaIndexRetriever(index, top_k=5)

# Use LlamaIndex retrieval inside LangChain LCEL chain
hybrid_chain = (
    {
        "context":  RunnableLambda(lambda x: llama_retriever.retrieve(x["question"])),
        "question": lambda x: x["question"],
        "history":  lambda x: x.get("history", []),
    }
    | rag_prompt
    | llm
    | StrOutputParser()
)

# Add LangChain memory on top
hybrid_with_memory = RunnableWithMessageHistory(
    hybrid_chain,
    lambda session_id: FileChatMessageHistory(
        str(MEMORY_DIR / f"{session_id}.json")
    ),
    input_messages_key   = "question",
    history_messages_key = "history",
)

# Best of both worlds:
# LlamaIndex accuracy in retrieval + LangChain memory, streaming, LangServe
result = hybrid_with_memory.invoke(
    {"question": "What halal certification requirements does CP Foods specify?"},
    config={"configurable": {"session_id": "procurement_002"}}
)
print(result)
```

---

## The Decision Framework — Applied to Makro Use Cases

Here is how I applied the decision across all five Axtra360 services:

| Service | Framework chosen | Why |
|---|---|---|
| DOC-LM (contract search) | LlamaIndex retrieval + LangChain agent | LlamaIndex for retrieval accuracy, LangChain for memory and deployment |
| Chat with Data (Text-to-SQL) | LangChain + LangGraph | Agents, tool use, multi-step reasoning — no retrieval needed |
| SSBI (self-service BI) | LangChain | Chain orchestration, LangServe deployment, LangSmith monitoring |
| Martech (lead generation) | LangGraph (LangChain ecosystem) | Agentic workflow, stateful multi-step process |
| Forecasting explainability | LangChain | Simple chain, LLM explains ML model output |

The pattern: whenever retrieval quality is the critical variable, LlamaIndex retriever as the backbone. Whenever agents, memory, tools, deployment, or monitoring matter, LangChain handles the application layer.

---

## When to Use Each — Summary

**Choose LlamaIndex when:**
- You have many large documents and retrieval accuracy is critical
- You need advanced indexing strategies (hierarchical, knowledge graph)
- You are building a pure document Q&A system
- You need multi-document reasoning (SubQuestionQueryEngine)
- You want a simpler API focused only on search

**Choose LangChain when:**
- You need agents that use multiple tools
- You need conversation memory across turns
- You are deploying to production (LangServe)
- You need monitoring and evaluation (LangSmith)
- Your application does more than just retrieve — it acts, decides, routes
- You are building an end-to-end product, not just a search component

**Use both when:**
- Your RAG application is complex and retrieval quality matters
- You need LlamaIndex's superior chunking and retrieval
- AND you need LangChain's agent, memory, and deployment layer
- Wrap the LlamaIndex retriever as a LangChain `RunnableLambda`

---

## The Answer to the Original Question

> "Should I use LangChain or LlamaIndex?"

If you are building Makro's supplier contract search where users ask one-off questions against a document — start with LlamaIndex. It handles chunking, embedding, and retrieval better out of the box.

If you are building Makro's Chat with Data chatbot where users have multi-turn conversations, the system queries Databricks, and you need to deploy it as a REST API with monitoring — use LangChain.

If your RAG chatbot needs to be excellent at both retrieval and conversation — use LlamaIndex for retrieval inside a LangChain application. That is the production architecture.

---

## This Series

- **Part 1** — BERT Complete Architecture Guide ✅
- **Part 2** — LangServe: Deploy LLM Chains as REST APIs ✅
- **Part 3** — LangSmith: Observability for Production LLM Apps ✅
- **Part 4** — LangChain vs LlamaIndex: Which One for Your Use Case ← this article
- **Part 5** — Coming next: LangGraph Agentic AI for Lead Generation Automation

---

*Prem Vishnoi is Head of Data & AI at CPAxtra (Makro/Lotus's), leading a 25-person data and AI team across Thailand, Cambodia, Myanmar, and Malaysia.*

*Tags: LangChain, LlamaIndex, RAG, LLM, Retrieval Augmented Generation, Azure OpenAI, E-Commerce AI, Python*
