# Month 6: AI + Vector Search at Scale — 30 Days of Hands-On Projects
### Theme: "Production-grade vector AI"

**Data system:** Pinecone / Weaviate / Qdrant / Chroma
**Tools:** Python 3.10+, vector DB SDKs, hybrid search libs, cross-encoder re-rankers
**Setup time:** 30 min
**Time per project:** 30-90 min
**Total time:** ~32 hours over 30 days
**Capstone:** Ship your own AI SaaS. Get 10 paying users. Demo Day.

---

## Setup (do this once, before Day 151)

```bash
mkdir ai-daily && cd ai-daily
python -m venv venv && source venv/bin/activate
pip install openai pinecone-client weaviate-client qdrant-client chromadb cohere \
            sentence-transformers streamlit fastapi uvicorn python-dotenv

# Get free API keys
# Pinecone: https://www.pinecone.io (free Starter plan)
# Weaviate: https://console.weaviate.io (free 14-day sandbox)
# Qdrant: https://qdrant.tech (free 1GB cloud)
# Cohere: https://cohere.com (free trial API)
```

---

## Day 151: Pinecone Basics (Insert, Search, Delete) (45 min)

```python
# day151_pinecone.py
import os
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
client = OpenAI()

INDEX = "ai-daily"

def setup_index():
    if INDEX not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(INDEX)

def embed(text: str) -> list[float]:
    return client.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding

def upsert(index, items: list[dict]):
    """items: [{'id': '...', 'text': '...', 'metadata': {...}}]"""
    vectors = [
        {"id": it["id"], "values": embed(it["text"]), "metadata": it.get("metadata", {})}
        for it in items
    ]
    index.upsert(vectors=vectors, batch_size=100)

def search(index, query: str, k: int = 5, filter: dict = None) -> list[dict]:
    qvec = embed(query)
    return index.query(vector=qvec, top_k=k, include_metadata=True, filter=filter).matches

# Demo
index = setup_index()
upsert(index, [
    {"id": "doc_1", "text": "How to deploy to Kubernetes", "metadata": {"category": "devops"}},
    {"id": "doc_2", "text": "Python OOM debugging", "metadata": {"category": "python"}},
    {"id": "doc_3", "text": "PostgreSQL performance tuning", "metadata": {"category": "db"}},
])
for m in search(index, "memory issues in production"):
    print(f"  {m.score:.3f}  {m.metadata}")
```

**Stretch:** Bulk upsert with async, namespaces, sparse-dense vectors.
**Architect note:** Pinecone is the most "managed" vector DB — zero ops, pay-per-use. Best for "I don't want to run a database" workloads.

---

## Day 152: Weaviate Schema Design (60 min)

```python
# day152_weaviate.py
import weaviate
import os
from openai import OpenAI

client = weaviate.Client(
    url=os.environ["WEAVIATE_URL"],
    auth_client_secret=weaviate.AuthApiKey(os.environ["WEAVIATE_API_KEY"]),
    additional_headers={"X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"]},  # server-side vectorization
)

def create_schema():
    schema = {
        "classes": [{
            "class": "Document",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {"model": "text-embedding-3-small", "type": "text"}
            },
            "properties": [
                {"name": "title", "dataType": ["text"]},
                {"name": "body", "dataType": ["text"]},
                {"name": "category", "dataType": ["string"], "moduleConfig": {
                    "text2vec-openai": {"skip": True}  # don't vectorize category
                }},
                {"name": "createdAt", "dataType": ["date"]},
            ],
        }]
    }
    if not client.schema.exists("Document"):
        client.schema.create(schema)

def add_doc(title: str, body: str, category: str):
    return client.data_object.create({
        "title": title, "body": body, "category": category,
        "createdAt": "2026-01-15T00:00:00Z",
    }, "Document")

def search(query: str, category: str = None) -> list[dict]:
    where = {"path": ["category"], "operator": "Equal", "valueText": category} if category else None
    result = client.query.get("Document", ["title", "body", "category"]).with_near_text({
        "concepts": [query],
    }).with_where(where).with_limit(5).do()
    return result["data"]["Get"]["Document"]

# create_schema()
# add_doc("Python OOM", "How to debug memory issues", "python")
# print(search("memory debugging", category="python"))
```

**Stretch:** Multi-tenancy, replication, custom vectorizer module.
**Architect note:** Weaviate's server-side vectorization saves round-trips — but ties you to their infrastructure. For multi-model, use client-side.

---

## Day 153: Qdrant Payloads + Filtering (45 min)

```python
# day153_qdrant.py
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams, Filter, FieldCondition, MatchValue
from openai import OpenAI
import os
import uuid

qdrant = QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"])
client = OpenAI()
COLLECTION = "ai-daily"

def setup():
    if not qdrant.collection_exists(COLLECTION):
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )

def embed(text: str) -> list[float]:
    return client.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding

def upsert(items: list[dict]):
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embed(it["text"]),
            payload={"title": it["title"], "tags": it.get("tags", []), "year": it.get("year", 2026)},
        )
        for it in items
    ]
    qdrant.upsert(collection_name=COLLECTION, points=points, wait=True)

def search(query: str, year: int = None, tags: list[str] = None, k: int = 5) -> list:
    must = []
    if year:
        must.append(FieldCondition(key="year", match=MatchValue(value=year)))
    if tags:
        for tag in tags:
            must.append(FieldCondition(key="tags", match=MatchValue(value=tag)))
    return qdrant.search(
        collection_name=COLLECTION,
        query_vector=embed(query),
        query_filter=Filter(must=must) if must else None,
        limit=k,
    )

# setup()
# upsert([{"title": "K8s deployment", "tags": ["devops"], "year": 2025}])
# for r in search("kubernetes", year=2025, tags=["devops"]):
#     print(f"  {r.score:.3f}  {r.payload['title']}")
```

**Stretch:** Payload indexing for fast filters, snapshot backup, geo queries.
**Architect note:** Qdrant has the best filtering performance of any vector DB. For "filter then search" workloads, choose Qdrant.

---

## Day 154: Chroma for Local Dev (30 min)

```python
# day154_chroma.py
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI

# Persistent client (saves to disk)
client = chromadb.PersistentClient(path="./chroma_db")
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="sk-...", model_name="text-embedding-3-small"
)
collection = client.get_or_create_collection("docs", embedding_function=openai_ef)

def add(docs: list[dict]):
    collection.add(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        metadatas=[d.get("metadata", {}) for d in docs],
    )

def search(query: str, n: int = 5, where: dict = None) -> dict:
    return collection.query(query_texts=[query], n_results=n, where=where)

# Demo
add([
    {"id": "1", "text": "Python OOM debugging", "metadata": {"tag": "python"}},
    {"id": "2", "text": "K8s deployment guide", "metadata": {"tag": "devops"}},
])
print(search("memory issues", n=2, where={"tag": "python"}))
```

**Stretch:** Switch to client-server mode, custom embedding function, distance functions.
**Architect note:** Chroma is the "SQLite of vector DBs" — perfect for dev and small prod (<1M vectors). For serious scale, migrate to Qdrant/Weaviate.

---

## Day 155: Embedding Model Comparison (60 min)

```python
# day155_embed_compare.py
import os
import time
import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer

models = {
    "openai-small": None,  # special
    "openai-large": None,
    "bge-small": "BAAI/bge-small-en-v1.5",
    "bge-large": "BAAI/bge-large-en-v1.5",
    "e5-large": "intfloat/e5-large-v2",
    "mpnet": "sentence-transformers/all-mpnet-base-v2",
}

texts = ["how to debug a memory leak", "fix OOM in production",
         "kubernetes pod crash loop", "best hiking trails in colorado",
         "machine learning model deployment", "..."]
query = "python memory debugging"

client = OpenAI()
results = {}

# OpenAI models
for name, model_id in [("openai-small", "text-embedding-3-small"), ("openai-large", "text-embedding-3-large")]:
    t0 = time.time()
    resp = client.embeddings.create(model=model_id, input=texts + [query])
    vectors = [d.embedding for d in resp.data]
    elapsed = time.time() - t0
    cost = len(texts) * {"text-embedding-3-small": 0.00002, "text-embedding-3-large": 0.00013}[model_id]
    # Compute similarity
    qvec = np.array(vectors[-1])
    sims = [np.dot(qvec, np.array(v)) / (np.linalg.norm(qvec) * np.linalg.norm(v)) for v in vectors[:-1]]
    results[name] = {"elapsed": elapsed, "cost": cost, "top_sims": sorted(sims, reverse=True)[:3]}

# Open-source models
for name, model_id in models.items():
    if models[name] is None:
        continue
    model = SentenceTransformer(model_id)
    t0 = time.time()
    vectors = model.encode(texts + [query])
    elapsed = time.time() - t0
    sims = [(vectors[-1] @ v) / (np.linalg.norm(vectors[-1]) * np.linalg.norm(v)) for v in vectors[:-1]]
    results[name] = {"elapsed": elapsed, "cost": 0, "top_sims": sorted(sims, reverse=True)[:3]}

for name, r in results.items():
    print(f"{name:18s} {r['elapsed']*1000:6.1f}ms  cost=${r['cost']:.5f}  top3={r['top_sims']}")
```

**Stretch:** Long-context embeddings (8K), multilingual comparison, MTEB benchmark scores.
**Architect note:** `text-embedding-3-small` is the workhorse. `bge-large-en-v1.5` is the best OSS option. Always benchmark on *your* data — generic scores don't predict your quality.

---

## Day 156: Vector Index Types (HNSW vs IVFFlat) (60 min)

```python
# day156_index_types.py
"""
HNSW vs IVFFlat — when to use each.

HNSW (Hierarchical Navigable Small World):
  Pros: best recall, fast queries
  Cons: high memory, slow indexing
  Use when: recall matters, queries >> indexing
  Params: M (edges per node), ef_construction (build quality), ef (query quality)

IVFFlat (Inverted File with Flat):
  Pros: low memory, fast indexing
  Cons: lower recall, slower queries
  Use when: memory-constrained, large batches
  Params: nlist (centroid count), nprobe (search width)

PQ (Product Quantization):
  Pros: 10-30x compression
  Cons: recall loss
  Use when: scale > 100M vectors
"""

# In Qdrant:
HNSW_CONFIG = {
    "hnsw_config": {
        "m": 16,            # edges per node (default 16, range 4-64)
        "ef_construct": 100, # build-time accuracy (default 100, range 50-200)
        "full_scan_threshold": 10000,  # use full scan below this size
    },
    "optimizer_config": {
        "indexing_threshold": 20000,  # build HNSW after this many vectors
    }
}

# In Pinecone: only HNSW is exposed (managed)
# In Weaviate: HNSW is default
# In pgvector: IVFFlat (default) or HNSW (since pgvector 0.5)

# Benchmark with your data
import time
import numpy as np
import random

def random_vectors(n: int, dim: int = 1536) -> np.ndarray:
    return np.random.randn(n, dim).astype("float32")

vectors = random_vectors(100_000)
print(f"Memory for 100k x 1536 float32: {vectors.nbytes / 1e9:.2f} GB")
# ~0.6 GB
# HNSW: ~3-5x = 2-3 GB
# IVFFlat: ~0.7 GB
# PQ-8: ~0.1 GB
```

**Stretch:** DiskANN (Microsoft), ScaNN (Google), pgvector HNSW benchmark.
**Architect note:** For <1M vectors, the index type doesn't matter much. For >10M, choose based on memory budget and recall requirements.

---

## Day 157: WEEKEND — Multi-DB Benchmark (3 hours)

Benchmark all 4 vector DBs on the same dataset:
- 100K random vectors
- Same queries
- Measure: insert speed, query latency (p50/p95/p99), recall@10
- Cost: $/month for 1M vectors
- Generate comparison report

**Architect note:** Benchmarks without recall measurement are misleading. Always measure recall — a 10ms query that returns the wrong results is worse than a 100ms query that returns the right ones.

---

## Day 158: Metadata Filtering (45 min)

```python
# day158_filtering.py
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams, Filter, FieldCondition, Range
from openai import OpenAI
import os
import uuid

qdrant = QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"])
COLLECTION = "products"
client = OpenAI()

def setup():
    if not qdrant.collection_exists(COLLECTION):
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )

def add_products():
    products = [
        {"name": "Hiking boots", "category": "footwear", "price": 120, "in_stock": True, "rating": 4.5},
        {"name": "Running shoes", "category": "footwear", "price": 90, "in_stock": True, "rating": 4.2},
        {"name": "Tent", "category": "camping", "price": 200, "in_stock": False, "rating": 4.7},
        {"name": "Backpack", "category": "camping", "price": 80, "in_stock": True, "rating": 4.4},
    ]
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=client.embeddings.create(model="text-embedding-3-small", input=p["name"]).data[0].embedding,
            payload=p,
        )
        for p in products
    ]
    qdrant.upsert(collection_name=COLLECTION, points=points)

def search_with_filters(query: str, **filters) -> list:
    must = []
    if "category" in filters:
        must.append(FieldCondition(key="category", match={"value": filters["category"]}))
    if "max_price" in filters:
        must.append(FieldCondition(key="price", range=Range(lte=filters["max_price"])))
    if "in_stock" in filters:
        must.append(FieldCondition(key="in_stock", match={"value": filters["in_stock"]}))
    return qdrant.search(
        collection_name=COLLECTION,
        query_vector=client.embeddings.create(model="text-embedding-3-small", input=query).data[0].embedding,
        query_filter=Filter(must=must) if must else None,
        limit=10,
    )

# setup(); add_products()
# for r in search_with_filters("shoes for hiking", category="footwear", max_price=150, in_stock=True):
#     print(f"  {r.score:.3f}  ${r.payload['price']}  {r.payload['name']}")
```

**Stretch:** Compound filters (AND/OR/NOT), geo filters, hybrid scalar + vector.
**Architect note:** Index your filter fields! Without a payload index, Qdrant falls back to scan — which is O(N).

---

## Day 159: Hybrid Search (Vector + Keyword) (60 min)

```python
# day159_hybrid.py
"""
Hybrid search: combine BM25 (keyword) + vector (semantic).
Two strategies:
  1. Two retrievers, fuse results (RRF)
  2. Single retriever with sparse + dense vectors
"""

from qdrant_client.models import PointStruct, VectorParams, Distance, SparseVector
import os
from openai import OpenAI
from qdrant_client import QdrantClient

# Use Qdrant with named vectors: dense + sparse
COLLECTION = "hybrid"
qdrant = QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"])
client = OpenAI()

def setup():
    if not qdrant.collection_exists(COLLECTION):
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config={
                "dense": VectorParams(size=1536, distance=Distance.COSINE),
            },
            sparse_vectors_config={
                "sparse": {},  # BM25-like
            },
        )

def add_doc(text: str, doc_id: str):
    from fastembed import SparseTextEmbedding
    sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
    sparse = list(sparse_model.embed([text]))[0]
    dense = client.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding
    qdrant.upsert(collection_name=COLLECTION, points=[PointStruct(
        id=doc_id, vector={"dense": dense, "sparse": SparseVector(indices=sparse.indices.tolist(), values=sparse.values.tolist())},
        payload={"text": text},
    )])

def hybrid_search(query: str, k: int = 5, dense_weight: float = 0.5) -> list:
    from fastembed import SparseTextEmbedding
    sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
    q_sparse = list(sparse_model.embed([query]))[0]
    q_dense = client.embeddings.create(model="text-embedding-3-small", input=query).data[0].embedding
    return qdrant.search(
        collection_name=COLLECTION,
        query_vector={"dense": q_dense, "sparse": SparseVector(indices=q_sparse.indices.tolist(), values=q_sparse.values.tolist())},
        limit=k,
    )

# setup()
# for i, doc in enumerate(["Python OOM", "K8s deployment", "PostgreSQL tuning"]):
#     add_doc(doc, str(i))
# for r in hybrid_search("memory debugging"):
#     print(f"  {r.score:.3f}  {r.payload['text']}")
```

**Stretch:** Reciprocal Rank Fusion, per-field weighting, learned fusion.
**Architect note:** Hybrid is the right default for most search systems. Pure vector misses keywords (error codes, SKUs); pure BM25 misses semantics.

---

## Day 160: Re-ranking with Cross-Encoders (45 min)

```bash
pip install sentence-transformers
```

```python
# day160_rerank.py
from sentence_transformers import CrossEncoder
import os
from openai import OpenAI
from day151_pinecone import search  # hypothetical

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def search_with_rerank(query: str, candidates_k: int = 20, top_k: int = 5) -> list[dict]:
    # Step 1: retrieve candidates with vector search
    candidates = search(query, k=candidates_k)
    # Step 2: re-rank with cross-encoder
    pairs = [(query, c.metadata.get("text", "")) for c in candidates]
    scores = reranker.predict(pairs)
    # Step 3: sort by reranker score
    ranked = sorted(zip(candidates, scores), key=lambda x: -x[1])
    return [{"text": c.metadata.get("text"), "vector_score": c.score, "rerank_score": float(s)}
            for c, s in ranked[:top_k]]

# for r in search_with_rerank("kubernetes pod stuck"):
#     print(f"  v={r['vector_score']:.2f}  r={r['rerank_score']:.2f}  {r['text'][:60]}")
```

**Stretch:** Cohere Rerank 3 (best quality), ColBERT late interaction, custom cross-encoder fine-tune.
**Architect note:** Re-ranking adds 50-200ms latency. Worth it for 2-stage retrieval (vector → rerank). Not worth it for real-time (sub-100ms) systems.

---

## Day 161: Multi-Vector Search (Per-Field) (60 min)

```python
# day161_multivector.py
"""
Per-field embeddings: vectorize title and body separately.
Search can use either, or combine.
"""

import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from openai import OpenAI
import uuid

qdrant = QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"])
client = OpenAI()
COLLECTION = "multivec"

def setup():
    if not qdrant.collection_exists(COLLECTION):
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config={
                "title": VectorParams(size=1536, distance=Distance.COSINE),
                "body": VectorParams(size=1536, distance=Distance.COSINE),
            },
        )

def add(title: str, body: str):
    title_vec = client.embeddings.create(model="text-embedding-3-small", input=title).data[0].embedding
    body_vec = client.embeddings.create(model="text-embedding-3-small", input=body).data[0].embedding
    qdrant.upsert(collection_name=COLLECTION, points=[PointStruct(
        id=str(uuid.uuid4()),
        vector={"title": title_vec, "body": body_vec},
        payload={"title": title, "body": body},
    )])

def search_title(query: str, k: int = 5):
    """Search only by title (good for short queries)."""
    return qdrant.search(
        collection_name=COLLECTION,
        query_vector=("title", client.embeddings.create(model="text-embedding-3-small", input=query).data[0].embedding),
        limit=k,
    )

def search_body(query: str, k: int = 5):
    """Search only by body (good for long queries)."""
    return qdrant.search(
        collection_name=COLLECTION,
        query_vector=("body", client.embeddings.create(model="text-embedding-3-small", input=query).data[0].embedding),
        limit=k,
    )
```

**Stretch:** ColBERT-style multi-vector, weighted combination, late interaction.
**Architect note:** Multi-vector costs more storage but gives much better recall for long documents. Use when doc >500 tokens.

---

## Day 162: Sparse + Dense (SPLADE) (60 min)

```python
# day162_splade.py
"""
SPLADE: Sparse Lexical AnD Expansion model.
Generates sparse vectors that combine keyword and semantic.
Often outperforms BM25 and dense alone.
"""

from fastembed import SparseTextEmbedding
import numpy as np

model = SparseTextEmbedding(model_name="prithivida/splade-pp-v2")

def embed_sparse(text: str) -> dict:
    embeddings = list(model.embed([text]))[0]
    return {"indices": embeddings.indices.tolist(), "values": embeddings.values.tolist()}

def search_splade(query: str, docs: list[str], k: int = 5) -> list[tuple[int, float]]:
    qvec = embed_sparse(query)
    scores = []
    for i, doc in enumerate(docs):
        dvec = embed_sparse(doc)
        # Dot product on shared indices
        d = dict(zip(dvec["indices"], dvec["values"]))
        score = sum(qvec["values"][j] * d.get(qvec["indices"][j], 0) for j in range(len(qvec["indices"])))
        scores.append((i, score))
    return sorted(scores, key=lambda x: -x[1])[:k]

# Demo
docs = ["Python OOM debugging", "Kubernetes deployment", "PostgreSQL tuning"]
for i, score in search_splade("memory leak python", docs):
    print(f"  {score:.3f}  {docs[i]}")
```

**Stretch:** SPLADE in Qdrant (named sparse vector), SPLADE-Mini (faster).
**Architect note:** SPLADE combines the best of BM25 (interpretable, keyword-matching) and dense (semantic, expansion). Beats both on most benchmarks.

---

## Day 163: Late Interaction (ColBERT) (60 min)

```python
# day163_colbert.py
"""
ColBERT: Contextualized Late Interaction over BERT.
Each token gets its own embedding; similarity = max-sim over tokens.
Slower but much more accurate.
"""

# pip install colbert-ai
# Requires a GPU and ~5GB model download

from colbert import Searcher
from colbert.infra import Run, RunConfig

# Setup (one-time)
# with Run().context(RunConfig(experiment="ai-daily")):
#     searcher = Searcher(index="docs", collection="./docs.tsv")

# Query
# results = searcher.search("memory leak debugging", k=5)
# for passage_id, rank, score in zip(*results):
#     print(f"  rank={rank} score={score:.2f} id={passage_id}")
```

**Stretch:** ColBERTv2 (better quality), PLAID index (10× faster), RAGatouille.
**Architect note:** ColBERT is the highest-quality retrieval for short queries on long documents. Cost: 100× more storage. Use only when quality matters more than cost.

---

## Day 164: WEEKEND — Search Quality Benchmark (3 hours)

Build a search quality benchmark:
- 50 labeled queries with expected results
- 4 systems: BM25, dense, hybrid, hybrid+rerank
- Metrics: nDCG@10, MRR, recall@20, latency
- Run on your document corpus
- Visualize in Streamlit
- Identify the winning config

**Architect note:** Quality benchmarks should be run weekly. Drift happens as documents change, embeddings shift, and queries evolve.

---

## Day 165: Sharding Strategies (45 min)

```python
# day165_sharding.py
"""
Sharding strategies for vector DBs:

1. Hash sharding (by vector ID)
   - Even distribution
   - No semantic locality
   - Used by: Milvus

2. Range sharding (by vector value)
   - Semantic locality
   - Skew risk (hotspots)
   - Used by: Weaviate

3. Tenant sharding (by tenant_id)
   - Strong isolation
   - Operational simplicity
   - Used by: Pinecone, Qdrant

4. Time-based sharding (by created_at)
   - Easy to expire old data
   - Hot shards for recent data
   - Used by: log analytics

In Qdrant, use sharding method: "auto" (default) or custom.
"""

# In Qdrant Cloud, set shards during collection creation:
# qdrant.create_collection(
#     collection_name="...",
#     shard_number=4,  # 4 shards
#     replication_factor=2,  # 2 replicas
#     vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
# )
```

**Stretch:** Custom shard key, geo sharding, time-window sharding.
**Architect note:** Sharding is a deployment decision. For <10M vectors, single-node is fine. For 100M+, plan sharding strategy before collection creation.

---

## Day 166: Replication + Read Replicas (45 min)

```python
# day166_replication.py
"""
Replication strategies:

1. Synchronous (RPO=0):
   - Wait for all replicas before ack
   - Higher write latency
   - Used by: Pinecone, Weaviate

2. Asynchronous (RPO > 0):
   - Ack after primary writes
   - Replica lag
   - Used by: most self-hosted

3. Read-from-replica:
   - Read scale
   - Stale reads possible
   - Used by: Qdrant
"""

# In Qdrant:
# qdrant.create_collection(
#     collection_name="...",
#     replication_factor=3,  # 3 replicas total (1 primary + 2)
#     vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
# )

# Read from a specific replica (Qdrant):
# qdrant.search(
#     collection_name="...",
#     query_vector=[...],
#     read_consistency="majority",  # or "quorum" or "all"
# )
```

**Stretch:** Cross-region replicas, follower reads, replica selection by load.
**Architect note:** Replication factor 3 is the production default. Higher = more durability, more cost. 2 is risky (split-brain).

---

## Day 167: Backup + Restore (45 min)

```python
# day167_backup.py
"""
Vector DB backup strategies:

1. Qdrant snapshots:
   qdrant snap create --collection <name> --snapshot <snapshot_name>
   qdrant snap restore --collection <name> --snapshot <snapshot_name>

2. Pinecone: managed backups (Pinecone Console)
3. Weaviate: backups via API or file system
4. Chroma: just copy the persistence directory
"""

# Qdrant snapshot via API
from qdrant_client import QdrantClient

qdrant = QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"])

def backup(collection: str) -> str:
    """Create a snapshot, return its name."""
    info = qdrant.create_snapshot(collection_name=collection)
    return info.name

def restore(collection: str, snapshot: str):
    """Restore from a named snapshot."""
    qdrant.recover_snapshot(collection_name=collection, snapshot_name=snapshot)

def list_snapshots(collection: str) -> list[str]:
    return [s.name for s in qdrant.list_snapshots(collection_name=collection)]

# backup("products")
# restore("products", "snapshot-abc123")
```

**Stretch:** Automated daily backups, off-region replication, point-in-time recovery.
**Architect note:** Vector DB backups are easy to forget. If you lose your vector index, you've lost your search. Test restores quarterly.

---

## Day 168: Cost Optimization (45 min)

```python
# day168_cost.py
"""
Vector DB cost levers (from biggest to smallest):

1. Embedding dimensions
   - 1536 (full) → 512 (MTEB-tuned) → 256 (aggressive)
   - Storage: 3x reduction at 512, 6x at 256
   - Quality: -2% at 512, -5% at 256 (varies by task)

2. Quantization
   - None (float32) → int8 → binary
   - Storage: 4x reduction at int8, 32x at binary
   - Quality: -1% at int8, -10% at binary

3. Index type
   - HNSW (best recall) → IVFFlat (cheaper) → DiskANN (cheapest at scale)

4. Replicas
   - 1 (no HA) → 2 (risky) → 3 (production)

5. Region
   - us-east-1 (cheapest) → eu-west-1 (+20%) → ap-southeast (+30%)

6. Reserved vs on-demand
   - Pinecone: ~40% savings on annual commit
"""

# Matryoshka embeddings (variable dimension)
# OpenAI text-embedding-3-* supports 256, 512, 1024, 1536 dims
def matryoshka_embed(text: str, dim: int = 512) -> list[float]:
    from openai import OpenAI
    client = OpenAI()
    return client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        dimensions=dim,  # request smaller embedding
    ).data[0].embedding

# Quantization in Qdrant
# qdrant.create_collection(
#     collection_name="...",
#     quantization_config={
#         "scalar": {"type": "int8", "quantile": 0.99, "always_ram": True}
#     },
#     vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
# )
```

**Stretch:** Cost-per-query tracking, embedding caching, batching.
**Architect note:** Matryoshka embeddings (variable-dim) is the cheapest quality win. 512 dims is the sweet spot for most use cases.

---

## Day 169: Multi-Tenancy with Namespaces (45 min)

```python
# day169_multitenant.py
import os
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
INDEX = "multi-tenant"

def setup():
    if INDEX not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(INDEX)

def upsert_for_tenant(index, tenant_id: str, items: list[dict]):
    vectors = [
        {"id": f"{tenant_id}:{it['id']}", "values": it["embedding"], "metadata": it["metadata"]}
        for it in items
    ]
    index.upsert(vectors=vectors, namespace=tenant_id)

def search_for_tenant(index, tenant_id: str, query_embedding: list[float], k: int = 5):
    return index.query(
        vector=query_embedding,
        top_k=k,
        namespace=tenant_id,  # restrict to this tenant
        include_metadata=True,
    )

# index = setup()
# upsert_for_tenant(index, "tenant_a", [{"id": "1", "embedding": [...], "metadata": {...}}])
# search_for_tenant(index, "tenant_a", [...])  # only sees tenant_a's data
```

**Stretch:** Per-tenant quotas, soft delete + restore, tenant-level encryption.
**Architect note:** Namespaces are the simplest multi-tenancy. For strong isolation, use separate indexes per tenant (more ops but stricter).

---

## Day 170: Vector DB Monitoring (45 min)

```python
# day170_monitoring.py
"""
Key metrics to monitor in a vector DB:

1. Latency
   - p50, p95, p99 query latency
   - Index build time
   - Replica lag

2. Throughput
   - Queries/sec
   - Inserts/sec
   - Recall@10 (drift indicator)

3. Resource
   - CPU, memory, disk
   - Vector cache hit rate
   - Network bytes

4. Cost
   - $/day per tenant
   - Storage growth
   - API calls
"""

import time
import numpy as np
from prometheus_client import Histogram, Counter, Gauge, start_http_server

query_latency = Histogram("vdb_query_latency_seconds", "Query latency", ["collection"])
query_count = Counter("vdb_queries_total", "Queries", ["collection", "status"])
recall_at_10 = Gauge("vdb_recall_at_10", "Recall@10 (last test)", ["collection"])
index_size = Gauge("vdb_index_size_vectors", "Number of vectors", ["collection"])

start_http_server(8001)  # Prometheus scrapes /metrics

def monitored_search(collection: str, query_fn, ground_truth: list = None):
    start = time.time()
    try:
        results = query_fn()
        query_count.labels(collection=collection, status="ok").inc()
        if ground_truth:
            retrieved = {r.id for r in results}
            recall = len(retrieved & set(ground_truth)) / len(ground_truth)
            recall_at_10.labels(collection=collection).set(recall)
        return results
    except Exception:
        query_count.labels(collection=collection, status="error").inc()
        raise
    finally:
        query_latency.labels(collection=collection).observe(time.time() - start)
```

**Stretch:** Alert on recall drop, PagerDuty for p99 > SLO, weekly capacity report.
**Architect note:** Recall drift is the silent killer. Embedding model changes, index rebuilds, and data distribution shifts all affect recall silently. Monitor continuously.

---

## Day 171: WEEKEND — Production-Ready Search Service (3 hours)

Build a search service with:
- Qdrant Cloud backend
- FastAPI + Streamlit
- Multi-tenant (Day 169)
- Hybrid search (Day 159)
- Re-ranking (Day 160)
- Cost tracking
- Backup automation (Day 167)
- Health check + metrics
- 100+ QPS load tested
- Deploy to Fly.io

**Architect note:** A production search service has 5+ failure modes. Test each: bad query, empty index, slow network, full disk, corrupt snapshot.

---

## Day 172: Multi-Modal Embeddings (CLIP) (60 min)

```python
# day172_clip.py
import torch
from transformers import CLIPModel, CLIPProcessor
from PIL import Image
import numpy as np

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

def embed_image(path: str) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    inputs = processor(images=img, return_tensors="pt")
    with torch.no_grad():
        emb = model.get_image_features(**inputs)
    e = emb[0].numpy()
    return e / np.linalg.norm(e)

def embed_text(text: str) -> np.ndarray:
    inputs = processor(text=[text], return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        emb = model.get_text_features(**inputs)
    e = emb[0].numpy()
    return e / np.linalg.norm(e)

# Same vector space for text and image
def search_by_text(query: str, image_db: list[tuple[str, np.ndarray]], k: int = 5):
    qvec = embed_text(query)
    scores = [(p, float(np.dot(qvec, v))) for p, v in image_db]
    return sorted(scores, key=lambda x: -x[1])[:k]
```

**Stretch:** CLIP in production vector DB, multi-modal RAG, image+text queries.
**Architect note:** CLIP is the "universal language" for image search. Index your product photos with CLIP, search with text — magic.

---

## Day 173: Image + Text Search (60 min)

```python
# day173_image_text.py
"""
Combined image + text search:
  - Search images by text query (CLIP)
  - Search images by similar image (CLIP)
  - Search images that match a long description (CLIP + captioning)
  - Search images that contain specific text (OCR + BM25)
"""

import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from day172_clip import embed_image
from openai import OpenAI
import uuid

qdrant = QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"])
client = OpenAI()
COLLECTION = "media"

def setup():
    if not qdrant.collection_exists(COLLECTION):
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config={
                "clip": VectorParams(size=512, distance=Distance.COSINE),  # CLIP base = 512
            },
        )

def add_image(path: str, caption: str = None):
    if caption is None:
        # Auto-caption with GPT-4V
        import base64
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "Describe this image in 1 sentence."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ]}],
        )
        caption = resp.choices[0].message.content
    qdrant.upsert(collection_name=COLLECTION, points=[PointStruct(
        id=str(uuid.uuid4()), vector={"clip": embed_image(path).tolist()},
        payload={"path": path, "caption": caption},
    )])
    return caption

def search_by_text(query: str, k: int = 5):
    from day172_clip import embed_text
    return qdrant.search(
        collection_name=COLLECTION,
        query_vector=("clip", embed_text(query).tolist()),
        limit=k,
    )
```

**Stretch:** Hybrid image+keyword search, visual similarity for product discovery, video frame search.
**Architect note:** Image+text search is the #1 use case in e-commerce. Build it once, sell it to every retailer.

---

## Day 174: Cross-Lingual Search (45 min)

```python
# day174_xlingual.py
"""
Cross-lingual search: search in one language, results in another.
OpenAI embeddings are inherently multilingual.
"""
import os
from openai import OpenAI
from day151_pinecone import setup_index, upsert, search

client = OpenAI()
index = setup_index()

# Index documents in multiple languages
upsert(index, [
    {"id": "1", "text": "How to debug Python memory issues", "metadata": {"lang": "en"}},
    {"id": "2", "text": "Cómo depurar problemas de memoria en Python", "metadata": {"lang": "es"}},
    {"id": "3", "text": "Pythonメモリのデバッグ方法", "metadata": {"lang": "ja"}},
    {"id": "4", "text": "Comment déboguer les problèmes de mémoire Python", "metadata": {"lang": "fr"}},
])

# Search in English, get results in any language
for m in search(index, "memory debugging"):
    print(f"  {m.score:.3f}  [{m.metadata['lang']}]  {m.metadata.get('text', '')}")
```

**Stretch:** Per-language re-rankers, translation caching, multi-lingual embedding model comparison.
**Architect note:** OpenAI's `text-embedding-3-small` is great for cross-lingual up to 50 languages. For more, use `bge-m3` or `e5-mistral-7b`.

---

## Day 175: Personalized Ranking (60 min)

```python
# day175_personal.py
"""
Personalize vector search results:
  1. Get vector candidates
  2. Re-rank with user history
  3. Return personalized top-K
"""
import os
from openai import OpenAI
from day151_pinecone import setup_index, search
import json

client = OpenAI()
index = setup_index()

def personalized_search(query: str, user_id: str, history: list[dict], k: int = 5) -> list[dict]:
    # Step 1: vector search (20 candidates)
    candidates = search(index, query, k=20)
    # Step 2: LLM re-rank based on user history
    history_text = "\n".join(
        f"- clicked: {h.get('title', '')} (tags: {h.get('tags', [])})" for h in history[-30:]
    )
    cand_text = "\n".join(f"{i}. {c.metadata.get('title', c.id)} (tags: {c.metadata.get('tags', [])})"
                          for i, c in enumerate(candidates))
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"""Re-rank these candidates for user {user_id}.

User history (last 30 interactions):
{history_text}

Query: {query}

Candidates:
{cand_text}

Return JSON: {{"ranking": [3, 0, 5, 1, 2, 4], "reasoning": "..."}}"""}],
        response_format={"type": "json_object"},
    )
    result = json.loads(resp.choices[0].message.content)
    return [candidates[i] for i in result["ranking"][:k]]
```

**Stretch:** Bandit exploration, embedding-based personalization, privacy-preserving (no raw history).
**Architect note:** Personalization works best with rich user history. With <10 interactions, fall back to popularity-based ranking.

---

## Day 176: A/B Test Search Quality (60 min)

```python
# day176_ab_test.py
"""
A/B test search systems in production:
  1. Bucket users (50/50 split)
  2. System A: vector only
  3. System B: hybrid + rerank
  4. Track: clicks, dwell time, conversions
  5. Statistical significance test
"""
import hashlib
import random
from dataclasses import dataclass

@dataclass
class ABConfig:
    name: str
    weight: float
    config: dict

class ABTest:
    def __init__(self, configs: list[ABConfig], experiment: str = "search-v1"):
        self.configs = configs
        self.experiment = experiment

    def bucket(self, user_id: str) -> ABConfig:
        """Deterministic bucketing — same user always gets same bucket."""
        h = hashlib.md5(f"{self.experiment}:{user_id}".encode()).hexdigest()
        r = (int(h, 16) % 1000) / 1000
        cumulative = 0
        for cfg in self.configs:
            cumulative += cfg.weight
            if r < cumulative:
                return cfg
        return self.configs[-1]

    def track(self, user_id: str, event: str, value: float = 1.0):
        cfg = self.bucket(user_id)
        # Send to analytics (Mixpanel, Amplitude, etc.)
        print(f"  [{cfg.name}] {user_id} {event}={value}")

# Setup
test = ABTest([
    ABConfig("vector_only", 0.5, {"rerank": False, "hybrid": False}),
    ABConfig("hybrid_rerank", 0.5, {"rerank": True, "hybrid": True}),
])

def search(user_id: str, query: str):
    cfg = test.bucket(user_id)
    if cfg.config["hybrid"]:
        # Use hybrid search
        results = hybrid_search(query)
    else:
        results = vector_search(query)
    if cfg.config["rerank"]:
        results = rerank(query, results)
    return results

# search("u_123", "python memory leak")
# test.track("u_123", "click", position=2)
```

**Stretch:** Multi-variant tests, sequential testing, automatic promotion.
**Architect note:** A/B test search needs >1000 users per bucket for statistical significance. Below that, use offline evaluation.

---

## Day 177: Capstone MVP (90 min)

Start your capstone. Pick a problem:
- **Idea 1: "Notion-style wiki search"** — semantic + keyword over your team's docs
- **Idea 2: "Customer support copilot"** — answers over your support history
- **Idea 3: "Code search engine"** — semantic search over your codebase
- **Idea 4: "Legal document Q&A"** — search and chat over contracts
- **Idea 5: "Personal knowledge base"** — upload PDFs, search and chat

**Day 177 deliverable:** Working MVP with:
- One core feature (search OR chat)
- Local deployment
- 1 demo dataset
- README + demo video script

**Architect note:** Your capstone is your *interview portfolio*. Pick something that shows real engineering depth, not just "I called an API."

---

## Day 178: WEEKEND — Capstone Polish (3 hours)

Polish your capstone:
- Add auth (Clerk, Supabase, or simple JWT)
- Add multi-tenancy (or per-user)
- Add Stripe for payments ($5/mo or $50/mo plan)
- Add landing page (Carrd or custom)
- Add analytics (PostHog or Plausible)
- Add error tracking (Sentry)
- Deploy to Fly.io / Vercel
- Write launch post (blog + Twitter)

**Architect note:** A polished product > a feature-rich one. Pay $20 for a domain, $20 for an icon, $20 for a logo. The little things matter.

---

## Day 179: Record Demo Video + Launch Post (60 min)

Record a 2-3 minute demo:
- Loom (free) or QuickTime
- Show the problem
- Show the solution
- Show 1-2 killer features
- Show pricing

Write a launch post (500-1500 words):
- The problem you solved
- The technical approach
- A demo GIF
- Pricing
- Call to action

Post to:
- Twitter (tag relevant people)
- Hacker News (Show HN)
- LinkedIn
- Reddit (r/SideProject, r/Entrepreneur, niche subs)
- Indie Hackers
- Your personal blog

**Architect note:** Launch day is the most important day. Be vulnerable, be specific, be helpful. Don't oversell.

---

## Day 180: CAPSTONE LAUNCH — Demo Day (6 hours)

**Goal:** Ship your AI SaaS. Get 10 paying users. Demo Day live stream.

**Your day:**
1. **Morning:** Final deployment, end-to-end test, monitoring check
2. **Noon:** Launch to your network (email list, social, communities)
3. **Afternoon:** Live demo stream (Twitter Spaces, Discord, or YouTube)
4. **Evening:** Onboard first 5-10 users, fix critical issues
5. **Night:** Celebrate. 180 days. You did it.

**Success criteria:**
- [ ] Live, deployed, accessible
- [ ] Working end-to-end flow (signup → pay → use)
- [ ] 10+ trial users
- [ ] 3+ paying users
- [ ] Public demo video
- [ ] Public launch post
- [ ] GitHub repo with code
- [ ] Portfolio updated

**Architect note:** Day 180 isn't the end — it's the beginning. The 6-month course got you to "I can build AI products." Now you have 5-10 years to build something that matters.

---

## Month 6 + Course Summary

**Built:**
- 30 projects (vector DBs, multi-modal, hybrid search, capstone)
- 1 production-grade search service
- 1 AI SaaS with paying users
- 180 projects total
- 1,500+ hours of hands-on AI engineering

**Time:** ~35 hours over 30 days
**Cost:** ~$30 in API + cloud + domain fees (potentially earning back with your SaaS)

**Key skills learned:**
- 4 production vector DBs (Pinecone, Weaviate, Qdrant, Chroma)
- Embedding model selection
- Hybrid search (BM25 + vector + rerank)
- Multi-modal embeddings (CLIP)
- Cross-lingual, personalization
- A/B testing, monitoring, cost optimization
- Shipping a real product (capstone)

**What you have:**
- 180 deployed AI projects
- 6 monthly capstones (all live)
- 1 capstone SaaS (with paying users)
- Public GitHub with 180 repos
- Portfolio website
- Demo video
- Job-ready or SaaS-ready

---

## What's Next?

You're no longer a "person learning AI." You're an AI engineer.

**Paths from here:**
- **Job path:** Apply to Anthropic, OpenAI, Google DeepMind, Vercel, or 100s of AI startups hiring AI engineers. Your portfolio speaks.
- **SaaS path:** Grow your capstone to $1K, $10K, $100K MRR. Most successful AI SaaS founders started exactly where you are.
- **Consulting path:** $200-500/hour for AI integration work. You have 180 examples to show clients.
- **Open-source path:** Build in public. The maintainers of the libraries you used (Pinecone, LangChain, OpenAI) started here.

**Keep building. Ship daily. 180 was the start.**

---

## See Also

- `month-1-projects.md` — Full code for all 30 Month 1 projects (PostgreSQL)
- `month-2-projects.md` — Full code for all 30 Month 2 projects (REST APIs)
- `month-3-projects.md` — Full code for all 30 Month 3 projects (Documents & Search)
- `month-4-projects.md` — Full code for all 30 Month 4 projects (Files & Media)
- `month-5-projects.md` — Full code for all 30 Month 5 projects (Real-Time Streams)
- `month-6-projects.md` — Full code for all 30 Month 6 projects (Vector Search at Scale)
- `180-day-overview.html` — Visual calendar

**You did it. Welcome to AI engineering.** 🎉
