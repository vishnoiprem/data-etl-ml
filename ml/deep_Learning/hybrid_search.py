# pip install sentence-transformers numpy rank-bm25
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import numpy as np

# ── Document corpus ──
documents = [
    "ERR-503 gateway timeout error in production server",
    "Authentication service experiencing high latency",
    "How to debug timeout issues in microservices",
    "Python tutorial for machine learning beginners",
    "ERR-503 connection refused by upstream service",
    "Network latency troubleshooting best practices",
    "Introduction to REST API design patterns",
]

# ── Pipeline 1: BM25 Keyword Search ──
tokenized_docs = [doc.lower().split() for doc in documents]
bm25 = BM25Okapi(tokenized_docs)

def bm25_search(query, top_k=5):
    scores = bm25.get_scores(query.lower().split())
    ranked = np.argsort(scores)[::-1][:top_k]
    return [(idx, scores[idx]) for idx in ranked if scores[idx] > 0]

# ── Pipeline 2: Semantic Search ──
model = SentenceTransformer("all-MiniLM-L6-v2")
doc_embeddings = model.encode(documents)

def semantic_search_pipeline(query, top_k=5):
    q_emb = model.encode([query])
    sims = np.dot(doc_embeddings, q_emb.T).flatten()
    ranked = np.argsort(sims)[::-1][:top_k]
    return [(idx, sims[idx]) for idx in ranked]

# ── Reciprocal Rank Fusion ──
def reciprocal_rank_fusion(rankings_list, k=60):
    """
    Merge multiple ranked lists using RRF.
    RRF_score(d) = Σ  1 / (k + rank_i(d))
    """
    rrf_scores = {}
    for rankings in rankings_list:
        for rank, (doc_idx, _) in enumerate(rankings):
            if doc_idx not in rrf_scores:
                rrf_scores[doc_idx] = 0.0
            rrf_scores[doc_idx] += 1.0 / (k + rank + 1)

    return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

# ── Hybrid Search ──
def hybrid_search(query, top_k=5):
    print(f"\n{'='*60}")
    print(f"🔍 Hybrid Search: '{query}'")
    print(f"{'='*60}")

    # Run both pipelines
    bm25_results = bm25_search(query, top_k)
    sem_results = semantic_search_pipeline(query, top_k)

    print(f"\n📋 BM25 Results:")
    for idx, score in bm25_results:
        print(f"  [{score:.3f}] {documents[idx]}")

    print(f"\n🧠 Semantic Results:")
    for idx, score in sem_results[:top_k]:
        print(f"  [{score:.3f}] {documents[idx]}")

    # Fuse with RRF
    fused = reciprocal_rank_fusion([bm25_results, sem_results])

    print(f"\n⚡ Hybrid (RRF) Results:")
    for doc_idx, rrf_score in fused[:top_k]:
        print(f"  [RRF: {rrf_score:.4f}] {documents[doc_idx]}")

# ── Run it ──
hybrid_search("ERR-503 timeout in authentication service")
hybrid_search("how to fix slow API response times")

# The first query benefits from BM25 matching "ERR-503" exactly
# AND semantic understanding that "timeout" relates to "latency"
# The hybrid result combines both signals for superior ranking
