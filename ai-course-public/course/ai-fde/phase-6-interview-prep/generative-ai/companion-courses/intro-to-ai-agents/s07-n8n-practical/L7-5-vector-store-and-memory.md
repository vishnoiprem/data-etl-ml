# L7.5: Vector store and memory — RAG in n8n, from Postgres pgvector to Pinecone

> **FDE framing in one line:** n8n ships first-class vector store nodes for Qdrant, Pinecone, Postgres pgvector, Supabase, and Redis. The FDE's job is to pick the right vector store for the customer's data volume + data sensitivity, and to wire the load + query + retrieve nodes correctly. The "vector store as memory" pattern turns an n8n workflow into a RAG agent.

## In 60 seconds

> "5 vector stores: Qdrant for on-prem, Pinecone for managed, pgvector for existing Postgres, Supabase for new apps, Redis for small datasets. The RAG pattern is 3 nodes for indexing (load → embed → insert) + 2 nodes for query (retrieve → reason). 3 memory patterns: simple (single-shot), window buffer (multi-turn), summary (long conversations). The chunking strategy is part of the design; fixed-size is the baseline, semantic is for structured docs. The wrong choice is to use Pinecone for 10K vectors (overkill). The right choice is the right vector store + the right chunking + the right memory for the conversation."

**The wrong choice is to read past this block.** The right choice is to recite the 60-second script before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. The 5 vector store options in n8n: Qdrant (open-source, self-hosted), Pinecone (managed, fast), Postgres pgvector (use existing Postgres), Supabase (managed Postgres with pgvector), Redis (in-memory, fast for small datasets). The right choice is determined by the customer's data volume, sensitivity, and existing infrastructure.
2. The 3-node RAG pattern: Document Loader (load files) → Embeddings (vectorize) → Vector Store (store). For query: Vector Store (retrieve) → AI Agent (reason over retrieved docs). The RAG pattern is the same as Section 2.3, but visual.
3. The 3 memory patterns: simple memory (no context), window buffer memory (last N messages), summary memory (summarize old messages). The FDE picks the right memory for the right conversation length; the choice affects cost and quality.

## Concept

n8n ships first-class nodes for the most common vector stores. The FDE does not write the embedding code; the FDE does not write the vector search code; the FDE configures the vector store node with the credential, the index name, and the embedding model. The node handles the rest. **The vector store node is the FDE's RAG-in-a-box; the pattern is the same whether the FDE is using n8n, Python, or any other platform.**

The 5 vector store options:

1. **Qdrant.** Open-source vector database; self-hosted or managed. The right choice when the customer has a Kubernetes cluster; the right choice for large datasets (10M+ vectors); the right choice for production RAG. Qdrant's Rust core is fast; the HNSW index is tunable. The FDE runs Qdrant on a dedicated VM or in K8s.
2. **Pinecone.** Managed vector database; the right choice when the customer does not want to operate infrastructure; the right choice for fast time-to-production. Pinecone's serverless tier is free up to 100K vectors; the paid tier is $0.096/hour for 1M vectors. The FDE picks Pinecone when the customer wants "vector DB as a service."
3. **Postgres pgvector.** Vector search in Postgres. The right choice when the customer already has Postgres (most apps do); the right choice for small-to-medium datasets (up to 1M vectors); the right choice for the FDE who wants one database for everything. pgvector's HNSW index is fast; the FDE adds `CREATE EXTENSION vector;` and creates a `vector(1536)` column.
4. **Supabase.** Managed Postgres with pgvector built-in. The right choice when the customer is building a new app on Supabase; the right choice for SMB RAG; the right choice for "Postgres as a service." Supabase's free tier includes 500MB of vector storage.
5. **Redis.** In-memory vector search. The right choice for small datasets (up to 100K vectors); the right choice for low-latency retrieval; the right choice when the customer already has Redis. Redis's HNSW index is fast; the FDE uses `FT.SEARCH` with the `KNN` clause.

The 3-node RAG pattern:

1. **Document Loader.** Loads files from a source. Examples: Read PDFs (load from S3 or Google Drive), Read Webpages (scrape URLs), Read Notion Pages, Read Google Docs. The loader returns text chunks.
2. **Embeddings (Embed node).** Converts text to vectors. The FDE picks the embedding model (OpenAI text-embedding-3-small, Cohere embed-english-v3.0, local sentence-transformers). The embeddings node is configured with the credential and the model name.
3. **Vector Store (Insert node).** Stores the vectors. The FDE picks the vector store (Qdrant, Pinecone, pgvector, Supabase, Redis), configures the index name, and the node inserts the vectors with metadata.

For query: **Vector Store (Retrieve node)** retrieves the top-K most similar vectors. The AI Agent node receives the retrieved docs as context and reasons over them. **The RAG pattern is: load → embed → insert; query → retrieve → reason.**

The 3 memory patterns:

1. **Simple memory.** No context; the agent receives only the current prompt. The right choice for single-shot workflows (classification, extraction, simple Q&A). The FDE picks simple memory when the conversation is one-shot.
2. **Window buffer memory.** Last N messages; in-memory or persisted. The right choice for multi-turn conversations within a single execution. The FDE picks window buffer memory when the conversation is bounded (e.g., 10 messages).
3. **Summary memory.** Old messages are summarized; the agent receives the summary + the recent messages. The right choice for long conversations (100+ messages); the right choice for cost-sensitive workflows. The FDE picks summary memory when the conversation is long and the recent context matters.

## The pattern

The RAG pattern in n8n (the 3-node load + the 2-node query):

```
LOAD (one-time setup):
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Read    │────▶│  Embed   │────▶│  Qdrant  │
│  PDFs    │     │ (OpenAI) │     │  Insert  │
└──────────┘     └──────────┘     └──────────┘

QUERY (every execution):
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Qdrant  │────▶│ AI Agent │────▶│  Slack   │
│ Retrieve │     │ (reason) │     │ (output) │
└──────────┘     └──────────┘     └──────────┘
```

The Document Loader configuration (Read PDFs from S3):

```json
{
  "name": "Read PDFs from S3",
  "type": "n8n-nodes-base.s3",
  "parameters": {
    "operation": "download",
    "bucketName": "northwind-docs",
    "fileName": "={{$json.key}}",
    "options": {}
  },
  "position": [250, 300]
}
```

The Embeddings node configuration (OpenAI text-embedding-3-small):

```json
{
  "name": "Embed Chunks",
  "type": "@n8n/n8n-nodes-langchain.embeddingsOpenAi",
  "parameters": {
    "model": "text-embedding-3-small",
    "options": {}
  },
  "credentials": {
    "openAiApi": {"id": "cred-openai", "name": "OpenAI Production"}
  },
  "position": [450, 300]
}
```

The Vector Store Insert configuration (Qdrant):

```json
{
  "name": "Qdrant Insert",
  "type": "@n8n/n8n-nodes-langchain.vectorStoreQdrant",
  "parameters": {
    "operation": "insert",
    "qdrantCollection": "northwind-docs",
    "options": {
      "metadata": "={{$json.metadata}}",
      "content": "={{$json.text}}",
      "embedding": "={{$json.embedding}}"
    }
  },
  "credentials": {
    "qdrantApi": {"id": "cred-qdrant", "name": "Qdrant Production"}
  },
  "position": [650, 300]
}
```

The Vector Store Retrieve configuration (Qdrant):

```json
{
  "name": "Qdrant Retrieve",
  "type": "@n8n/n8n-nodes-langchain.vectorStoreQdrant",
  "parameters": {
    "operation": "retrieve",
    "qdrantCollection": "northwind-docs",
    "topK": 5,
    "options": {
      "query": "={{$json.question}}"
    }
  },
  "credentials": {
    "qdrantApi": {"id": "cred-qdrant", "name": "Qdrant Production"}
  },
  "position": [450, 500]
}
```

The 5 vector store options compared (the FDE's reference):

```python
VECTOR_STORE_OPTIONS = {
    "qdrant": {
        "type": "open-source / managed",
        "best_for": "10M+ vectors, production RAG, on-prem",
        "cost": "Self-hosted: $20/month VM; managed: $0.096/hour",
        "n8n_node": "vectorStoreQdrant",
        "setup": "Run Qdrant Docker image; create collection; configure credential",
    },
    "pinecone": {
        "type": "managed",
        "best_for": "Fast time-to-production, no infra to operate",
        "cost": "Free up to 100K vectors; $0.096/hour for 1M+ vectors",
        "n8n_node": "vectorStorePinecone",
        "setup": "Create Pinecone account; create index; configure API key",
    },
    "postgres_pgvector": {
        "type": "Postgres extension",
        "best_for": "Existing Postgres, <1M vectors, single-database stack",
        "cost": "Free (open-source); included in existing Postgres",
        "n8n_node": "vectorStorePostgres",
        "setup": "CREATE EXTENSION vector; CREATE TABLE docs (id serial, content text, embedding vector(1536));",
    },
    "supabase": {
        "type": "managed Postgres + pgvector",
        "best_for": "New Supabase apps, SMB RAG",
        "cost": "Free tier: 500MB; Pro: $25/month",
        "n8n_node": "vectorStoreSupabase",
        "setup": "Create Supabase project; enable pgvector; configure service role key",
    },
    "redis": {
        "type": "in-memory",
        "best_for": "<100K vectors, low-latency retrieval, existing Redis",
        "cost": "Free (open-source); included in existing Redis",
        "n8n_node": "vectorStoreRedis",
        "setup": "Enable RediSearch; FT.CREATE idx ON HASH PREFIX 1 doc: SCHEMA content TEXT embedding VECTOR HNSW 6 DIM 1536",
    },
}
```

The 3 memory patterns compared (the FDE's reference):

```python
MEMORY_PATTERNS = {
    "simple": {
        "description": "No context; the agent receives only the current prompt",
        "context_size": 1,
        "cost": "Lowest (no memory cost)",
        "best_for": "Single-shot workflows (classification, extraction, simple Q&A)",
        "n8n_config": "memory: { type: 'none' }",
    },
    "window_buffer": {
        "description": "Last N messages; in-memory or persisted",
        "context_size": "N (default 10)",
        "cost": "Moderate (each message adds tokens)",
        "best_for": "Multi-turn conversations within a single execution",
        "n8n_config": "memory: { type: 'windowBuffer', contextWindowLength: 10 }",
    },
    "summary": {
        "description": "Old messages are summarized; the agent receives summary + recent messages",
        "context_size": "summary + last N",
        "cost": "Higher (extra LLM call to summarize)",
        "best_for": "Long conversations (100+ messages); cost-sensitive workflows",
        "n8n_config": "memory: { type: 'summary', summaryModel: 'gpt-5-mini', contextWindowLength: 20 }",
    },
}
```

The pattern that wins interviews is the "5 vector stores + 3-node RAG + 3 memory patterns" pattern. The candidate who says "I pick Qdrant for on-prem, Pinecone for managed, pgvector for existing Postgres, Supabase for new apps, Redis for small datasets. The RAG pattern is 3 nodes (load → embed → insert) for indexing + 2 nodes (retrieve → reason) for query. The 3 memory patterns are simple (single-shot), window buffer (multi-turn), summary (long conversations). The wrong choice is to use Pinecone for a 10K-vector dataset (overkill). The right choice is the right vector store for the data + the right memory for the conversation" is the candidate who demonstrates the RAG-mindset.

## Code or example

The 4-axis rubric for picking the vector store:

```python
def pick_vector_store(requirements: dict) -> str:
    """Pick the right vector store for the customer's requirements."""
    volume = requirements.get("vector_count", 100_000)
    on_prem = requirements.get("on_prem_required", False)
    existing_postgres = requirements.get("existing_postgres", False)
    managed = requirements.get("managed_preferred", False)
    budget_usd_per_month = requirements.get("budget_usd_per_month", 100)

    if on_prem:
        return "qdrant"  # Self-hosted on K8s
    if existing_postgres and volume < 1_000_000:
        return "postgres_pgvector"  # Use existing Postgres
    if managed and volume < 1_000_000:
        return "pinecone"  # Managed; fast setup
    if requirements.get("new_app", False) and volume < 100_000:
        return "supabase"  # New Supabase app
    if volume < 100_000 and requirements.get("existing_redis", False):
        return "redis"  # Existing Redis
    return "qdrant"  # Default: self-hosted Qdrant
```

The chunking strategy (the FDE's reference):

```python
CHUNKING_STRATEGIES = {
    "fixed_size": {
        "description": "Split text into N-token chunks; overlap M tokens",
        "config": "chunkSize: 512, chunkOverlap: 50",
        "best_for": "Generic documents; baseline",
        "n8n_node": "Code node with custom JS",
    },
    "semantic": {
        "description": "Split at natural boundaries (paragraphs, sections)",
        "config": "Use the Document Loader's built-in splitter",
        "best_for": "Structured documents (contracts, manuals, FAQs)",
        "n8n_node": "Code node with paragraph splitting",
    },
    "recursive": {
        "description": "Try paragraph → sentence → word boundaries until chunk size is met",
        "config": "Use the Recursive Character Splitter",
        "best_for": "Mixed-structure documents",
        "n8n_node": "Code node with LangChain splitter",
    },
    "document_specific": {
        "description": "Use the document's own structure (e.g., Markdown headers)",
        "config": "Use the Markdown Splitter or HTML Splitter",
        "best_for": "Markdown, HTML, code files",
        "n8n_node": "Code node with markdown-it or beautifulsoup",
    },
}
```

The 5 most common RAG errors and fixes:

```python
RAG_ERRORS = {
    "no_results": {
        "symptom": "Vector Store returns 0 results for a query that should match",
        "cause": "Embeddings model mismatch (query embedded with model A, docs with model B)",
        "fix": "Use the same embedding model for indexing and querying; verify in the node config",
    },
    "low_relevance": {
        "symptom": "Vector Store returns top-K results but they're not relevant",
        "cause": "Chunking strategy is wrong (chunks too small or too large)",
        "fix": "Adjust chunk size (try 256, 512, 1024); add chunk overlap; use semantic chunking",
    },
    "high_cost": {
        "symptom": "Embedding + LLM cost is higher than expected",
        "cause": "Top-K is too high; chunks are too large",
        "fix": "Reduce top-K from 10 to 5; reduce chunk size; use a smaller embedding model (text-embedding-3-small)",
    },
    "stale_data": {
        "symptom": "Vector Store returns old data after a doc is updated",
        "cause": "Doc was updated in source but not re-indexed",
        "fix": "Add a scheduled workflow that re-indexes the docs daily; or use the Vector Store's update node",
    },
    "rate_limit": {
        "symptom": "Embedding API returns 429 Too Many Requests",
        "cause": "Indexing too many docs at once",
        "fix": "Add a Wait node between batches; reduce batch size; use the rate limiter",
    },
}
```

The Northwind RAG setup (the case study):

```python
# Northwind Logistics: 500 freight contracts, 200 SOPs, 1000 customer emails
NORTHWIND_RAG = {
    "documents": {
        "contracts": {"count": 500, "source": "S3 (s3://northwind-docs/contracts/)", "chunk_strategy": "semantic"},
        "sops": {"count": 200, "source": "Notion (Northwind SOPs database)", "chunk_strategy": "recursive"},
        "emails": {"count": 1000, "source": "Postgres (emails table)", "chunk_strategy": "fixed_size: 256"},
    },
    "vector_store": {
        "type": "postgres_pgvector",  # Northwind already has Postgres
        "table": "docs (id serial, content text, embedding vector(1536), metadata jsonb)",
        "index": "HNSW on embedding (m=16, ef_construction=64)",
    },
    "embedding_model": "text-embedding-3-small",  # $0.02 per 1M tokens
    "retrieval": {
        "top_k": 5,
        "reranking": "none (use the LLM to re-rank)",
    },
    "cost_per_query": "$0.001 (embed query) + $0.005 (LLM with 5 retrieved docs)",
    "queries_per_day": 200,
    "daily_cost": "$1.20 / $30/month budget = 4%",
}
```

## Production addendum

The vector store question is the answer to "how do you add RAG to an n8n workflow." The 60-second script:

> "5 vector stores: Qdrant for on-prem, Pinecone for managed, pgvector for existing Postgres, Supabase for new apps, Redis for small datasets. The RAG pattern is 3 nodes for indexing (load → embed → insert) + 2 nodes for query (retrieve → reason). 3 memory patterns: simple (single-shot), window buffer (multi-turn), summary (long conversations). The chunking strategy is part of the design; fixed-size is the baseline, semantic is for structured docs. The wrong choice is to use Pinecone for 10K vectors (overkill). The right choice is the right vector store + the right chunking + the right memory for the conversation."

This is the difference between a candidate who says "I added RAG" and a candidate who says "5 vector stores, 3-node RAG pattern, 3 memory patterns, 4-axis rubric, 5 most common errors, the chunking strategy is part of the design." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-core-build/n8n/04-rag-pipeline.json` — the RAG workflow example.
- **Reference implementation**: `course/hardcode/level-4-rag-pipelines/07-hybrid-search-rag.py` — the canonical RAG setup.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — n8n as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/01-mcp-drafter/` — the MCP server could use a vector store for tool discovery.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — vector store as a system design choice.

## The 3 questions this lecture preps you for

1. **"How do you add RAG to an n8n workflow?"** Answer: 3 nodes for indexing (Document Loader → Embeddings → Vector Store Insert) + 2 nodes for query (Vector Store Retrieve → AI Agent). The 5 vector stores are Qdrant (on-prem), Pinecone (managed), pgvector (existing Postgres), Supabase (new apps), Redis (small datasets). The chunking strategy is part of the design.
2. **"What are the 3 memory patterns?"** Answer: simple (no context, single-shot), window buffer (last N messages, multi-turn), summary (old messages summarized, long conversations). The FDE picks simple for single-shot, window buffer for multi-turn, summary for long conversations. The choice affects cost (summary is highest) and quality (window buffer is highest for short conversations).
3. **"How do you pick the right vector store?"** Answer: 4-axis rubric. On-prem → Qdrant. Existing Postgres → pgvector. Managed → Pinecone. New Supabase app → Supabase. Small dataset + existing Redis → Redis. Default → Qdrant (self-hosted). The wrong choice is Pinecone for 10K vectors (overkill, expensive). The right choice is the rubric.

## Read next

`L7-6-error-handling-in-n8n.md` — the error workflow, retry, continue-on-fail, IF/Switch nodes, the production-readiness patterns. How to make an n8n workflow that survives the 3am page.
