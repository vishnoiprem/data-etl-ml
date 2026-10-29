# Weaviate for Banking AI: Why, When, How — A Principal Engineer's Guide

*A practical deep-dive for engineering leaders building RAG systems in financial services*

**April 2026 | Reading time: ~18 min**

---

## The Motivation: Why Vector Databases Matter in Banking

Imagine you're a relationship manager at HSBC, managing 200 affluent clients across Singapore, Hong Kong, and the UAE. A client calls asking: *"What are my options for diversifying my SGD-heavy portfolio into global fixed income given the current rate environment?"*

To answer well, you need to pull from: product fact sheets, compliance guidelines for cross-border wealth, recent market commentary, the client's risk profile, and suitability rules for Singapore under MAS regulations. That's five different knowledge sources, all unstructured text, updated at different frequencies.

A SQL query can't do this. A keyword search misses the semantic intent. You need **vector search** — the ability to find documents by *meaning*, not just matching words.

This is where Weaviate comes in.

---

## What is Weaviate? The 60-Second Version

Weaviate is an open-source, cloud-native vector database written in Go. It stores both the original data objects (JSON documents) and their vector embeddings side by side, enabling you to combine semantic similarity search with structured filtering in a single query.

**Why it matters for banking AI:**

- **Hybrid search:** Combines BM25 keyword search with vector similarity. In finance, you need both — semantic understanding for broad queries AND exact-match for product codes, ISIN numbers, and regulation references.
- **Multi-tenancy:** Built-in tenant isolation means one Weaviate cluster can serve multiple business units (wealth, insurance, lending) with data separation — critical for compliance.
- **Built-in RAG:** Weaviate has native generative search — you can retrieve documents AND generate LLM responses in a single API call.
- **RBAC & security:** Role-based access control, OIDC authentication, and HIPAA-compliance options for regulated environments.

**Current state (April 2026):** Weaviate is at v1.35, with the Python client at v4.20.4. Key recent features include Object TTL (time-to-live for automatic data expiry), ACORN filtered search for faster queries, server-side batching, and multimodal embeddings support. Gartner recognized Weaviate as an Emerging Leader in their 2025 Innovation Guide for Generative AI Engineering.

---

## Why Weaviate? The Decision Framework

As a principal engineer evaluating vector databases for a banking platform, here's how I'd frame the decision:

### The Shortlist

| Database     | Strengths                                                           | Weakness for Banking                             |
|--------------|---------------------------------------------------------------------|--------------------------------------------------|
| **Weaviate** | Hybrid search, built-in RAG, multi-tenancy, open-source, K8s-native | Younger ecosystem than Elasticsearch             |
| **Pinecone** | Fully managed, simple API                                           | No self-hosting, data leaves your infrastructure |
| **pgvector** | Runs in existing PostgreSQL                                         | No hybrid search, limited at scale               |
| **Qdrant**   | High performance, Rust-based                                        | Smaller ecosystem, fewer integrations            |
| **ChromaDB** | Developer-friendly, easy start                                      | Not production-grade for large scale             |
| **Milvus**   | Massive scale, battle-tested                                        | Complex to operate, heavier footprint            |

### Why Weaviate Wins for Banking

**1. Self-hosting capability (regulatory requirement)**

Banks cannot send proprietary client data, product information, or compliance documents to a third-party SaaS vector database. Weaviate can be self-hosted on Kubernetes within HSBC's own cloud VPC. Pinecone cannot. This alone eliminates several alternatives.

**2. Hybrid search is not optional in finance**

Consider this query: *"What is the minimum investment amount for HSBC Premier Plus structured deposit in SGD?"*

Pure vector search might return semantically similar documents about investment minimums generally. But you also need exact-match on "HSBC Premier Plus" and "SGD." Weaviate's hybrid search (vector + BM25) handles both in a single query, weighted by an `alpha` parameter you can tune per use case.

**3. Multi-tenancy for regulatory data separation**

HSBC's IWPB division serves clients across 57 countries. Regulatory requirements differ by jurisdiction — Singapore MAS rules differ from UK FCA rules. Weaviate's multi-tenancy allows tenant-per-jurisdiction isolation within a single cluster, avoiding the operational overhead of separate databases per market.

**4. Built-in module ecosystem**

Weaviate has integrated vectorizer modules for Cohere, OpenAI, HuggingFace, and now Mistral (relevant since HSBC's Mistral partnership). You can swap embedding models without changing application code — just update the collection configuration.

---

## When to Use Weaviate: The Decision Tree

Not every problem needs a vector database. Here's when to reach for Weaviate versus alternatives:

**USE Weaviate when:**
- You're building a RAG system over unstructured documents (product sheets, compliance manuals, research reports)
- You need semantic search — finding documents by meaning, not just keywords
- You need hybrid search — combining semantic understanding with exact-match
- Your data changes frequently and you need real-time indexing (Weaviate indexes in real-time, no batch-only constraints)
- You need multi-tenancy for data isolation across business units or jurisdictions

**DON'T use Weaviate when:**
- Your data is purely structured/tabular — use PostgreSQL or a data warehouse
- You're doing simple keyword search — Elasticsearch is mature and battle-tested
- You only need embeddings for offline analytics — store vectors in your data lake
- Your dataset is tiny (< 10K documents) — pgvector in your existing Postgres is simpler

**COMBINE Weaviate with other stores when:**
- You need both vector search AND relational queries — use Weaviate for retrieval + PostgreSQL for transactional data
- You need graph relationships between entities — use Weaviate for vector search + Neo4j for relationship traversal (Graph RAG pattern)

---

## Architecture: How Weaviate Fits in a Banking RAG System

### The Reference Architecture

Here's how I'd architect a RAG system for HSBC's Wealth & Premier Solutions using Weaviate:

```
                    ┌─────────────────────────────────┐
                    │     RM Copilot (LangGraph)      │
                    │   Supervisor → Agents → Tools   │
                    └──────────┬──────────────────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │     RAG Orchestration Layer     │
                    │  (LangChain / LlamaIndex)       │
                    │                                 │
                    │  ┌──────────┐  ┌──────────────┐ │
                    │  │ Query    │  │ Reranker     │ │
                    │  │ Rewriter │  │ (Cross-Enc.) │ │
                    │  └────┬─────┘  └──────▲───────┘ │
                    │       │               │         │
                    └───────┼───────────────┼─────────┘
                            │               │
                    ┌───────▼───────────────┼───────────┐
                    │         WEAVIATE                  │
                    │                                   │
                    │  ┌────────────┐  ┌──────────────┐ │
                    │  │ Hybrid     │  │ Multi-tenant │ │
                    │  │ Search     │  │ Collections  │ │
                    │  │ (BM25 +    │  │              │ │
                    │  │  Vector)   │  │ SG | HK | UK │ │
                    │  └────────────┘  └──────────────┘ │
                    │                                   │
                    │  ┌────────────┐  ┌──────────────┐ │
                    │  │ HNSW Index │  │ Vectorizer   │ │
                    │  │ + Filters  │  │ Module       │ │
                    │  └────────────┘  └──────────────┘ │
                    └───────────────────────────────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │     Document Pipeline           │
                    │  Kafka CDC → Chunker → Embedder │
                    └─────────────────────────────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │     Source Systems              │
                    │  Product DB | Compliance Docs | │
                    │  Market Research | CRM          │
                    └─────────────────────────────────┘
```

### Architecture Decisions Explained

**1. Document Pipeline (Kafka → Chunker → Weaviate)**

Source documents flow through a Kafka-based pipeline. When a product fact sheet is updated in the CMS, a CDC event triggers re-ingestion. The chunker splits documents using semantic chunking (not fixed-size) to preserve meaning boundaries. Each chunk is embedded and stored in Weaviate with rich metadata (source_id, version, jurisdiction, classification, last_updated).

Why Kafka? Because in a bank, we need audit trails for every document that enters the knowledge base. Kafka provides immutable, replayable event streams — we can prove exactly which version of which document was indexed at any point in time.

**2. Multi-Tenant Collections**

I'd create jurisdiction-specific tenants within Weaviate:

```python
# Each jurisdiction gets its own tenant for data isolation
client.collections.create(
    name="WealthProducts",
    multi_tenancy_config=wvc.config.Configure.multi_tenancy(enabled=True),
    # ... vectorizer config
)

# Add tenants per jurisdiction
collection = client.collections.get("WealthProducts")
collection.tenants.create([
    wvc.tenants.Tenant(name="SG"),   # Singapore
    wvc.tenants.Tenant(name="HK"),   # Hong Kong
    wvc.tenants.Tenant(name="UK"),   # United Kingdom
    wvc.tenants.Tenant(name="UAE"),  # UAE
])
```

When a Singapore RM queries the system, the application routes to the `SG` tenant automatically, ensuring they only receive Singapore-applicable product and compliance information.

**3. Hybrid Search with Tunable Alpha**

Different query types benefit from different search strategies:

```python
# For product-specific queries (need exact match + semantic)
# alpha=0.5 gives equal weight to BM25 and vector
response = collection.query.hybrid(
    query="HSBC Premier Plus structured deposit SGD",
    alpha=0.5,
    limit=10,
    return_metadata=wvc.query.MetadataQuery(score=True, distance=True)
)

# For conceptual queries (semantic-heavy)
# alpha=0.8 weights toward vector search
response = collection.query.hybrid(
    query="portfolio diversification strategies for rate-sensitive assets",
    alpha=0.8,
    limit=10
)
```

**4. Built-in RAG (Generative Search)**

Weaviate can call an LLM directly from a search query, eliminating a network hop:

```python
# Single API call: retrieve relevant docs + generate response
response = collection.generate.hybrid(
    query="What are the eligibility criteria for HSBC Premier in Singapore?",
    alpha=0.5,
    limit=5,
    grouped_task="Based on the retrieved product documents, summarize the eligibility criteria. Cite specific documents."
)

# response.generated contains the LLM's answer
# response.objects contains the source documents
```

---

## Prototype: Working Code for a Wealth Knowledge Base

Here's a complete, runnable prototype that demonstrates a Weaviate-powered RAG system for wealth management. This code uses the Weaviate v4 Python client (v4.20.x).

### Step 1: Setup and Connection

```python
import weaviate
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType, Configure
import os, json

# Option A: Connect to Weaviate Cloud (sandbox - free)
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=os.environ["WEAVIATE_URL"],
    auth_credentials=weaviate.auth.AuthApiKey(os.environ["WEAVIATE_API_KEY"]),
    headers={"X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"]}
)

# Option B: Connect to local Docker instance
# client = weaviate.connect_to_local(
#     headers={"X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"]}
# )

print(f"Connected: {client.is_ready()}")
```

### Step 2: Create the Collection (Schema)

```python
# Delete if exists (for development)
if client.collections.exists("WealthKnowledge"):
    client.collections.delete("WealthKnowledge")

# Create collection with vectorizer and generative module
wealth_kb = client.collections.create(
    name="WealthKnowledge",
    
    # Vectorizer: automatically creates embeddings on import
    vectorizer_config=Configure.Vectorizer.text2vec_openai(
        model="text-embedding-3-small"
    ),
    
    # Generative module: enables RAG queries
    generative_config=Configure.Generative.openai(
        model="gpt-4o-mini"
    ),
    
    # Properties define the schema
    properties=[
        Property(name="title", data_type=DataType.TEXT),
        Property(name="content", data_type=DataType.TEXT),
        Property(name="document_type", data_type=DataType.TEXT),  
        # e.g., "product_sheet", "compliance", "market_research"
        Property(name="jurisdiction", data_type=DataType.TEXT),   
        # e.g., "SG", "HK", "UK"
        Property(name="product_category", data_type=DataType.TEXT),
        # e.g., "structured_deposit", "unit_trust", "insurance"
        Property(name="last_updated", data_type=DataType.DATE),
        Property(name="source_url", data_type=DataType.TEXT,
                 skip_vectorization=True),  # Don't vectorize URLs
        Property(name="classification", data_type=DataType.TEXT,
                 skip_vectorization=True),  # "public", "internal", "confidential"
    ],
    
    # HNSW index with cosine distance (best for text embeddings)
    vector_index_config=Configure.VectorIndex.hnsw(
        distance_metric=wvc.config.VectorDistances.COSINE,
        ef_construction=128,    # Build-time accuracy (higher = better, slower)
        max_connections=32,     # Graph connectivity
        ef=64,                  # Query-time accuracy
    ),
)

print(f"Collection created: {wealth_kb.name}")
```

### Step 3: Ingest Documents (Simulated Wealth Data)

```python
from datetime import datetime, timezone

# Simulated wealth management documents
documents = [
    {
        "title": "HSBC Premier Eligibility Criteria — Singapore",
        "content": (
            "To qualify for HSBC Premier in Singapore, customers must maintain "
            "a Total Relationship Balance (TRB) of SGD 200,000 or above, or "
            "have a mortgage facility of SGD 500,000 or above with HSBC Singapore. "
            "Premier customers receive complimentary worldwide travel insurance, "
            "preferential rates on foreign exchange, and access to the Global "
            "Investment Centre with over 350 investment solutions."
        ),
        "document_type": "product_sheet",
        "jurisdiction": "SG",
        "product_category": "premier_banking",
        "last_updated": datetime(2026, 1, 15, tzinfo=timezone.utc),
        "source_url": "https://internal.hsbc.com/sg/premier-eligibility",
        "classification": "internal",
    },
    {
        "title": "Structured Deposit Risk Disclosure — Singapore",
        "content": (
            "Structured deposits are NOT conventional fixed deposits. The principal "
            "amount is guaranteed only at maturity. Early withdrawal may result in "
            "a loss of principal. The potential return is linked to the performance "
            "of the underlying reference asset. Structured deposits are covered by "
            "the Singapore Deposit Insurance Corporation (SDIC) up to SGD 100,000 "
            "per depositor per scheme member. Suitability assessment is mandatory "
            "under MAS Notice SFA 04-N12."
        ),
        "document_type": "compliance",
        "jurisdiction": "SG",
        "product_category": "structured_deposit",
        "last_updated": datetime(2026, 2, 1, tzinfo=timezone.utc),
        "source_url": "https://internal.hsbc.com/sg/compliance/structured-deposits",
        "classification": "internal",
    },
    {
        "title": "Global Fixed Income Outlook Q1 2026",
        "content": (
            "With the Federal Reserve holding rates steady and the ECB signaling "
            "further easing, global fixed income presents selective opportunities. "
            "Investment-grade corporate bonds in the 3-5 year duration bucket "
            "offer attractive risk-adjusted returns. Emerging market sovereign debt "
            "remains attractive but requires careful country selection. For SGD-based "
            "investors, hedging costs have decreased, making unhedged USD exposure "
            "more viable. We recommend a barbell strategy: short-duration high-quality "
            "corporates paired with selective EM sovereign positions."
        ),
        "document_type": "market_research",
        "jurisdiction": "GLOBAL",
        "product_category": "fixed_income",
        "last_updated": datetime(2026, 3, 15, tzinfo=timezone.utc),
        "source_url": "https://internal.hsbc.com/research/fi-outlook-q1-2026",
        "classification": "internal",
    },
    {
        "title": "MAS Suitability Assessment Requirements",
        "content": (
            "Under MAS Notice SFA 04-N12, financial advisers must conduct a "
            "Customer Knowledge Assessment (CKA) before recommending specified "
            "investment products including structured deposits, unit trusts with "
            "derivatives exposure, and leveraged foreign exchange trading. The "
            "assessment must evaluate the customer's educational background, "
            "investment experience, and understanding of the product's risks. "
            "Records of the assessment must be retained for at least 5 years "
            "from the date of transaction."
        ),
        "document_type": "compliance",
        "jurisdiction": "SG",
        "product_category": "regulatory",
        "last_updated": datetime(2025, 11, 20, tzinfo=timezone.utc),
        "source_url": "https://internal.hsbc.com/sg/compliance/mas-sfa04",
        "classification": "internal",
    },
    {
        "title": "Global Money Account Features and Benefits",
        "content": (
            "The HSBC Global Money Account allows customers to hold and convert "
            "up to 20 currencies within the HSBC mobile app. Key features include "
            "instant international transfers in 65+ currencies, a Global Money "
            "Debit Card with no foreign transaction fees, and real-time exchange "
            "rates with competitive spreads. Available in 10 markets including "
            "Singapore, Hong Kong, UK, UAE, and Australia. Over 2 million customers "
            "use Global Money as of 2026. No minimum balance required for Premier "
            "customers."
        ),
        "document_type": "product_sheet",
        "jurisdiction": "GLOBAL",
        "product_category": "global_money",
        "last_updated": datetime(2026, 3, 1, tzinfo=timezone.utc),
        "source_url": "https://internal.hsbc.com/global/global-money-features",
        "classification": "internal",
    },
    {
        "title": "Portfolio Diversification Best Practices for HNW Clients",
        "content": (
            "High-net-worth clients with concentrated single-currency portfolios "
            "face significant currency and geographic risk. Best practice guidelines "
            "recommend no more than 40% allocation to any single currency or "
            "geography. For SGD-concentrated portfolios, recommended diversification "
            "targets include: 30-40% USD-denominated assets (US Treasuries, "
            "investment-grade corporates), 15-20% EUR-denominated assets, 10-15% "
            "alternative investments (private credit, real estate), and maintaining "
            "SGD allocation at 25-35% for liquidity and local commitments."
        ),
        "document_type": "market_research",
        "jurisdiction": "GLOBAL",
        "product_category": "portfolio_strategy",
        "last_updated": datetime(2026, 2, 20, tzinfo=timezone.utc),
        "source_url": "https://internal.hsbc.com/research/hnw-diversification",
        "classification": "internal",
    },
]

# Batch import
collection = client.collections.get("WealthKnowledge")

with collection.batch.dynamic() as batch:
    for doc in documents:
        batch.add_object(properties=doc)

print(f"Imported {len(documents)} documents")
```

### Step 4: Search — Vector, Keyword, and Hybrid

```python
# --- 1. Pure Vector Search (semantic similarity) ---
print("=" * 60)
print("VECTOR SEARCH: 'diversifying SGD portfolio into global bonds'")
print("=" * 60)

results = collection.query.near_text(
    query="diversifying SGD portfolio into global bonds",
    limit=3,
    return_metadata=wvc.query.MetadataQuery(distance=True)
)

for obj in results.objects:
    print(f"  [{obj.properties['document_type']}] {obj.properties['title']}")
    print(f"  Distance: {obj.metadata.distance:.4f}")
    print()


# --- 2. BM25 Keyword Search (exact matching) ---
print("=" * 60)
print("KEYWORD SEARCH: 'MAS SFA 04-N12 suitability'")
print("=" * 60)

results = collection.query.bm25(
    query="MAS SFA 04-N12 suitability",
    limit=3,
    return_metadata=wvc.query.MetadataQuery(score=True)
)

for obj in results.objects:
    print(f"  [{obj.properties['document_type']}] {obj.properties['title']}")
    print(f"  BM25 Score: {obj.metadata.score:.4f}")
    print()


# --- 3. Hybrid Search (best of both) ---
print("=" * 60)
print("HYBRID SEARCH: 'structured deposit risk Singapore SDIC'")
print("=" * 60)

results = collection.query.hybrid(
    query="structured deposit risk Singapore SDIC",
    alpha=0.5,  # 0.5 = equal weight to vector and keyword
    limit=3,
    return_metadata=wvc.query.MetadataQuery(score=True)
)

for obj in results.objects:
    print(f"  [{obj.properties['document_type']}] {obj.properties['title']}")
    print(f"  Hybrid Score: {obj.metadata.score:.4f}")
    print()


# --- 4. Filtered Hybrid Search (jurisdiction-specific) ---
print("=" * 60)
print("FILTERED HYBRID: Singapore compliance docs only")
print("=" * 60)

results = collection.query.hybrid(
    query="investment product suitability assessment requirements",
    alpha=0.6,
    limit=3,
    filters=wvc.query.Filter.by_property("jurisdiction").equal("SG") &
            wvc.query.Filter.by_property("document_type").equal("compliance"),
    return_metadata=wvc.query.MetadataQuery(score=True)
)

for obj in results.objects:
    print(f"  [{obj.properties['jurisdiction']}] {obj.properties['title']}")
    print(f"  Content preview: {obj.properties['content'][:100]}...")
    print()
```

### Step 5: RAG — Generative Search (The Power Move)

```python
# --- RAG: Retrieve + Generate in a single call ---
print("=" * 60)
print("RAG QUERY: RM asking about client portfolio diversification")
print("=" * 60)

# Grouped task: all retrieved docs are sent to LLM together
response = collection.generate.hybrid(
    query="How should a Singapore client with a concentrated SGD portfolio diversify into global fixed income?",
    alpha=0.7,
    limit=4,
    grouped_task=(
        "You are an HSBC wealth advisory assistant. Based on the retrieved "
        "documents, provide a concise advisory summary for a relationship "
        "manager preparing for a client meeting. Include:\n"
        "1. Recommended diversification approach\n"
        "2. Specific product suggestions\n"
        "3. Relevant compliance requirements\n"
        "4. Key risks to highlight\n"
        "Cite the source documents by title."
    ),
)

print("GENERATED ADVISORY BRIEF:")
print("-" * 40)
print(response.generated)
print()
print("SOURCE DOCUMENTS USED:")
for obj in response.objects:
    print(f"  - {obj.properties['title']} ({obj.properties['document_type']})")


# --- Per-object generation: transform each doc individually ---
print()
print("=" * 60)
print("PER-OBJECT GENERATION: Summarize each doc for the RM")
print("=" * 60)

response = collection.generate.near_text(
    query="structured deposits Singapore",
    limit=2,
    single_prompt=(
        "Summarize this document in 2 bullet points for a "
        "relationship manager preparing for a client meeting: "
        "{content}"
    ),
)

for obj in response.objects:
    print(f"\n  Document: {obj.properties['title']}")
    print(f"  Summary: {obj.generated}")
```

### Step 6: Production Patterns — Metadata Filtering + Reranking

```python
# --- Production pattern: Metadata-enriched retrieval ---

def search_wealth_knowledge(
    query: str,
    jurisdiction: str = None,
    doc_types: list = None,
    product_category: str = None,
    alpha: float = 0.6,
    limit: int = 5,
) -> dict:
    """
    Production-grade search function with metadata filtering.
    This is what the LangGraph agent would call as a tool.
    """
    # Build dynamic filters
    filters = None
    filter_parts = []
    
    if jurisdiction:
        filter_parts.append(
            wvc.query.Filter.by_property("jurisdiction").equal(jurisdiction)
        )
    
    if doc_types:
        filter_parts.append(
            wvc.query.Filter.by_property("document_type").contains_any(doc_types)
        )
    
    if product_category:
        filter_parts.append(
            wvc.query.Filter.by_property("product_category").equal(product_category)
        )
    
    if filter_parts:
        filters = filter_parts[0]
        for f in filter_parts[1:]:
            filters = filters & f
    
    # Execute hybrid search
    results = collection.query.hybrid(
        query=query,
        alpha=alpha,
        limit=limit,
        filters=filters,
        return_metadata=wvc.query.MetadataQuery(score=True, distance=True),
    )
    
    # Format for LLM context
    retrieved_docs = []
    for obj in results.objects:
        retrieved_docs.append({
            "title": obj.properties["title"],
            "content": obj.properties["content"],
            "document_type": obj.properties["document_type"],
            "jurisdiction": obj.properties["jurisdiction"],
            "score": obj.metadata.score,
            "source_url": obj.properties.get("source_url", ""),
        })
    
    return {
        "query": query,
        "num_results": len(retrieved_docs),
        "documents": retrieved_docs,
    }


# Example: Singapore RM searching for compliance info
result = search_wealth_knowledge(
    query="What suitability checks are required before recommending structured products?",
    jurisdiction="SG",
    doc_types=["compliance", "product_sheet"],
    limit=3,
)

print(f"Found {result['num_results']} documents:")
for doc in result["documents"]:
    print(f"  [{doc['document_type']}] {doc['title']} (score: {doc['score']:.3f})")
```

### Step 7: Cleanup

```python
# Always close the connection
client.close()
```

---

## How Weaviate Works Under the Hood

Understanding the internals helps you make better architecture decisions.

### HNSW Index (Hierarchical Navigable Small World)

Weaviate uses a custom implementation of HNSW for approximate nearest neighbor search. HNSW organizes vectors into a multi-layer graph:

- **Top layers** have fewer nodes with long-range connections (for fast navigation)
- **Bottom layers** have all nodes with short-range connections (for precise results)

At query time, the algorithm enters at the top layer, greedily navigates toward the query vector, then descends layer by layer, refining the neighborhood at each level.

Key parameters you control:
- `ef_construction` (build-time): Higher values create a more connected graph (better recall, slower build). Default: 128. For banking (accuracy matters): 256.
- `ef` (query-time): Higher values explore more nodes (better recall, slower query). Default: 64. For banking: 128.
- `max_connections`: Edges per node. Default: 32. More connections = better recall but more memory.

### Inverted Index (BM25)

Weaviate also maintains a traditional inverted index for keyword search. When you run a hybrid query, both the HNSW vector search and the BM25 keyword search run in parallel, and results are fused using reciprocal rank fusion (RRF).

The `alpha` parameter controls the fusion:
- `alpha = 0.0` → pure keyword (BM25)
- `alpha = 0.5` → equal weight
- `alpha = 1.0` → pure vector

### Vector Quantization

For production at scale, Weaviate supports:
- **PQ (Product Quantization):** Compresses vectors to reduce memory usage by ~4x with minimal recall loss
- **SQ (Scalar Quantization):** Simpler compression, good for most use cases
- **RQ (Residual Quantization):** New in v1.34/1.35 — better recall/compression tradeoff for flat indexes

---

## Production Deployment: Kubernetes Architecture

For HSBC's production deployment, Weaviate runs on Kubernetes:

```yaml
# weaviate-helm-values.yaml (simplified)
replicas: 3                    # 3-node cluster for HA
resources:
  requests:
    cpu: "4"
    memory: "16Gi"
  limits:
    cpu: "8"
    memory: "32Gi"

storage:
  size: 100Gi
  storageClassName: gp3        # AWS EBS gp3 for consistent IOPS

env:
  PERSISTENCE_DATA_PATH: /var/lib/weaviate
  CLUSTER_HOSTNAME: weaviate-node
  ENABLE_MODULES: text2vec-openai,generative-openai
  DEFAULT_VECTORIZER_MODULE: text2vec-openai
  
  # Security (banking requirement)
  AUTHENTICATION_OIDC_ENABLED: true
  AUTHORIZATION_ADMINLIST_ENABLED: true
  
monitoring:
  enabled: true                # Prometheus metrics endpoint
```

### Operational Considerations for Banking

1. **Backup strategy:** Weaviate supports S3-compatible backups. Schedule daily backups, retain for 30 days (regulatory requirement).

2. **Monitoring:** Export Prometheus metrics to Grafana. Key metrics: query latency P99, import throughput, memory usage, vector count per collection.

3. **Replication:** Weaviate supports replication factor per collection. For critical collections (compliance docs), set replication factor to 3.

4. **TTL (v1.35+):** Use Object TTL for market research documents that should expire after a defined period. Compliance documents should have no TTL (retain indefinitely).

---

## Connecting Weaviate to LangGraph: The Agent Pattern

Here's how the Weaviate search function becomes a tool in a LangGraph-based agent:

```python
from langchain_core.tools import tool
from langchain_weaviate import WeaviateVectorStore
from langgraph.graph import StateGraph, END

@tool
def search_wealth_products(
    query: str,
    jurisdiction: str = "SG",
) -> str:
    """Search HSBC wealth product knowledge base.
    Use this tool when the RM needs information about
    products, eligibility, or features."""
    
    result = search_wealth_knowledge(
        query=query,
        jurisdiction=jurisdiction,
        doc_types=["product_sheet"],
        alpha=0.7,
    )
    
    context = "\n\n".join([
        f"[{d['title']}]: {d['content']}"
        for d in result["documents"]
    ])
    return context


@tool
def search_compliance(
    query: str,
    jurisdiction: str = "SG",
) -> str:
    """Search compliance and regulatory requirements.
    Use this tool when checking suitability rules,
    regulatory requirements, or risk disclosures."""
    
    result = search_wealth_knowledge(
        query=query,
        jurisdiction=jurisdiction,
        doc_types=["compliance"],
        alpha=0.5,  # Lower alpha — compliance needs exact keyword match
    )
    
    context = "\n\n".join([
        f"[{d['title']}]: {d['content']}"
        for d in result["documents"]
    ])
    return context
```

These tools are then registered with the LangGraph supervisor agent, which routes RM queries to the appropriate tool based on intent classification.

---

## Weaviate vs. pgvector: When to Use Each

A common question: "We already have PostgreSQL. Why not just use pgvector?"

| Factor | Weaviate | pgvector |
|--------|----------|----------|
| **Hybrid search** | Native (BM25 + vector) | Manual implementation required |
| **Scale** | Billions of vectors, distributed | Millions, single-node |
| **Indexing** | HNSW with PQ/SQ compression | HNSW or IVFFlat |
| **Multi-tenancy** | Built-in | Schema-per-tenant (manual) |
| **RAG integration** | Native generative modules | None — external orchestration |
| **Filtering** | Pre-filtering (accurate counts) | Post-filtering (unpredictable) |
| **Ops complexity** | Separate service to manage | Part of existing Postgres |
| **Best for** | Primary vector store, production RAG | Small-scale, existing Postgres stack |

**My recommendation for HSBC:** Use Weaviate as the primary vector store for the RAG platform, and keep pgvector as a lightweight vector capability within existing PostgreSQL services for simpler use cases (e.g., product similarity for cross-sell recommendations within the transactional database).

---

## Best Practices for Banking RAG with Weaviate

### 1. Schema Design
- Use `skip_vectorization=True` for properties that shouldn't influence semantic search (IDs, URLs, dates, classification labels)
- Include rich metadata (jurisdiction, document_type, source_version) for runtime filtering
- Use `tokenization="field"` for exact-match properties like product codes

### 2. Chunking Strategy
- Use semantic chunking (not fixed-size) — split at paragraph/section boundaries that preserve meaning
- Include document title and section header as prefix in each chunk for context
- Maintain parent-child relationships: store both the chunk and a reference to the full document ID

### 3. Embedding Model Selection
- For English-only wealth content: `text-embedding-3-small` (OpenAI) or Cohere's `embed-english-v3.0`
- For multilingual (HSBC serves 57 markets): `text-embedding-3-large` or Cohere's `embed-multilingual-v3.0`
- Consider Mistral's embedding model given HSBC's partnership

### 4. Security & Governance
- Enable OIDC authentication — integrate with HSBC's identity provider
- Configure RBAC — compliance team gets read access to all collections; RM-facing tools get read access only to approved collections
- Audit logging: log all queries with user identity, retrieved document IDs, and timestamps
- No PII in the vector store — store client data references (client_id), not client data itself

### 5. Monitoring
- Track retrieval quality: % of queries where the top-3 results contain the correct answer (measure weekly with evaluation set)
- Track latency: P50 < 100ms, P99 < 500ms for hybrid search
- Track freshness: alert if any document in the compliance collection is older than its source system version

---

## Conclusion: The Bigger Picture

Weaviate is not just a database — it's the retrieval foundation of your AI platform. In the context of HSBC's wealth management AI strategy, it sits at the intersection of three critical capabilities:

1. **Knowledge retrieval** — finding the right information from thousands of product sheets, compliance documents, and research reports
2. **Regulatory compliance** — ensuring that every AI-generated recommendation is grounded in auditable source documents with proper jurisdiction filtering
3. **Scalable AI infrastructure** — running on Kubernetes within the bank's own cloud, integrated with the enterprise model governance framework

For engineering leaders building production AI systems in financial services, the vector database choice is one of the most consequential infrastructure decisions you'll make. Weaviate's combination of hybrid search, multi-tenancy, self-hosting capability, and native RAG integration makes it a strong choice for the regulated, multi-jurisdictional, high-stakes environment that banking demands.

The prototype code in this article runs in under 5 minutes. The production architecture behind it takes 3–6 months to build properly. The governance framework around it is what makes it trustworthy.

Start with the prototype. Build toward the architecture. Never skip the governance.

---

*This article was prepared as part of an engineering leadership deep-dive for AI solutions in wealth management. The prototype code uses Weaviate v4.20.x Python client with OpenAI embeddings. For production deployment at HSBC scale, substitute with Mistral embeddings per the enterprise partnership and deploy on internal Kubernetes infrastructure.*

---

**Further Reading:**
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Advanced RAG Techniques — Weaviate Blog](https://weaviate.io/blog/advanced-rag)
- [Weaviate Finance Case Study](https://weaviate.io/case-studies/finance)
- [MAS FEAT Principles](https://www.mas.gov.sg/development/fintech/fairness-ethics-accountability-transparency)
- [LangGraph Agent Orchestration](https://www.langchain.com/langgraph)
