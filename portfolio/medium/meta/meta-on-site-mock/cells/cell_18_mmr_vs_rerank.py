"""
Cell 18: MMR vs Cross-Encoder Rerank — the L6 trade-off

The interview question:
'Your hybrid search returns 50 candidates. Pipeline to top 8 for LLM.
 Do you use MMR (intra-list diversity), cross-encoder rerank, or both?
 What's the latency / cost / quality trade-off?'

L6 answer structure:
- MMR is FREE diversity (post-vector-search, no extra model)
- Cross-encoder costs ~80ms but boosts precision 30-50%
- The pipeline: vector top 50 -> MMR top 25 -> cross-encoder top 8
- Cost: $1/1k searches (Cohere) vs $0 for MMR
"""
import numpy as np
import time
from collections import defaultdict

np.random.seed(42)
DIM = 128
N_CORPUS = 5000
N_QUERIES = 200

# Simulate a corpus with cluster structure (10 topics, 500 docs each)
print("=" * 70)
print("SETUP: 5000 docs across 10 topical clusters (realistic RAG)")
print("=" * 70)

doc_clusters = []
doc_texts = []
for cluster_id in range(10):
    base = np.random.randn(DIM)
    for doc_id in range(500):
        # Add noise so docs in same cluster are similar but not identical
        emb = base + 0.3 * np.random.randn(DIM)
        doc_clusters.append(cluster_id)
        doc_texts.append(f"doc_c{cluster_id}_{doc_id}")
        if doc_id == 0:
            # First doc of each cluster: also keep the cluster center
            pass

# Index it as a numpy matrix for fast cosine
all_embs = np.array([
    np.random.randn(DIM) * 0.3 + np.eye(10)[c].mean() * np.ones(DIM) * 0
    for c in doc_clusters
]).astype(np.float32)
# Simpler: regenerate
all_embs = np.random.randn(N_CORPUS, DIM).astype(np.float32)
for i, c in enumerate(doc_clusters):
    # Make docs in same cluster have a shared direction
    cluster_dir = np.zeros(DIM)
    cluster_dir[c * (DIM // 10):(c+1) * (DIM // 10)] = 1.0
    all_embs[i] = cluster_dir + 0.4 * np.random.randn(DIM)

# Normalize for cosine
norms = np.linalg.norm(all_embs, axis=1, keepdims=True)
all_embs_norm = all_embs / norms

print(f"  Corpus: {N_CORPUS} docs, dim={DIM}, 10 clusters of 500 each")

# ════════════════════════════════════════════════════════════════
# STAGE 1: Naive vector top-K (no rerank, no MMR)
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STAGE 1: Naive vector top-8 (no MMR, no rerank)")
print("=" * 70)

def vector_top_k(query_emb, k=8):
    """Naive: cosine sim, top k. O(N) scan."""
    sims = all_embs_norm @ query_emb
    top_idx = np.argsort(-sims)[:k]
    return top_idx, sims[top_idx]

# Generate queries with known ground truth
queries = []
true_relevant_clusters = []
for _ in range(N_QUERIES):
    # Query points to a specific cluster
    target_cluster = np.random.randint(10)
    q = np.zeros(DIM)
    q[target_cluster * (DIM // 10):(target_cluster+1) * (DIM // 10)] = 1.0
    q += 0.2 * np.random.randn(DIM)
    q = q / np.linalg.norm(q)
    queries.append(q)
    true_relevant_clusters.append(target_cluster)

queries = np.array(queries)

# Measure: Recall@8 = how often the true cluster is represented in top 8
def recall_at_k(top_idx, true_cluster):
    """Fraction of top-k results that are in the true cluster."""
    hits = sum(1 for i in top_idx if doc_clusters[i] == true_cluster)
    return hits / len(top_idx)

# Run baseline
t0 = time.perf_counter()
naive_recalls = []
for q, true_c in zip(queries, true_relevant_clusters):
    top_idx, _ = vector_top_k(q, k=8)
    naive_recalls.append(recall_at_k(top_idx, true_c))
naive_ms = (time.perf_counter() - t0) * 1000 / N_QUERIES
naive_recall = np.mean(naive_recalls)
print(f"  Latency:        {naive_ms:.2f}ms per query")
print(f"  Recall@8:       {naive_recall:.3f}  (fraction of top-8 in true cluster)")

# ════════════════════════════════════════════════════════════════
# STAGE 2: MMR rerank (FREE diversity, no extra model)
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STAGE 2: MMR rerank (top 50 -> top 8 with diversity)")
print("=" * 70)

def mmr(query_emb, candidate_idx, candidate_sims, lambda_=0.7, k=8):
    """Maximal Marginal Relevance. Trade off relevance vs diversity."""
    selected = []
    candidates = set(range(len(candidate_idx)))
    cand_embs = all_embs_norm[candidate_idx]

    for _ in range(min(k, len(candidate_idx))):
        best_idx, best_score = -1, -np.inf
        for i in candidates:
            rel = candidate_sims[i]
            if not selected:
                div = 0.0
            else:
                div = max(float(cand_embs[i] @ cand_embs[s].T) for s in selected)
            score = lambda_ * rel - (1 - lambda_) * div
            if score > best_score:
                best_score, best_idx = score, i
        selected.append(best_idx)
        candidates.remove(best_idx)
    return candidate_idx[selected]

# Run MMR
t0 = time.perf_counter()
mmr_recalls = []
for q, true_c in zip(queries, true_relevant_clusters):
    # Get top 50
    sims = all_embs_norm @ q
    top_50 = np.argsort(-sims)[:50]
    top_50_sims = sims[top_50]
    # MMR to 8
    top_8 = mmr(q, top_50, top_50_sims, lambda_=0.7, k=8)
    mmr_recalls.append(recall_at_k(top_8, true_c))
mmr_ms = (time.perf_counter() - t0) * 1000 / N_QUERIES
mmr_recall = np.mean(mmr_recalls)
print(f"  Latency:        {mmr_ms:.2f}ms per query (top 50 -> 8)")
print(f"  Recall@8:       {mmr_recall:.3f}")

# ════════════════════════════════════════════════════════════════
# STAGE 3: Cross-encoder rerank (the expensive precision boost)
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STAGE 3: Cross-encoder rerank (the precision booster)")
print("=" * 70)
print("""
Cross-encoder scores (query, doc) jointly. ~50x more accurate than
bi-encoder cosine for relevance, but ~100x slower.

Production: Cohere rerank-v3, BGE-reranker, monoT5.
Cost: $1 / 1000 searches (Cohere).
Latency: 50-150ms for top 50 candidates on GPU.
""")

def fake_cross_encoder(query_emb, candidate_idx):
    """Simulate cross-encoder: tighter relevance signal than cosine.
    In prod this is a real model; here we add a 'cross-encoder bonus'
    for docs in the true cluster (the cross-encoder learns this)."""
    sims = all_embs_norm[candidate_idx] @ query_emb
    # Add a bonus for cluster match (simulating what cross-encoder learns)
    bonus = np.array([
        0.3 if doc_clusters[i] == np.argmax(query_emb[:DIM//10] * 10) else 0
        for i in candidate_idx
    ])
    return sims + bonus

# Run cross-encoder
t0 = time.perf_counter()
ce_recalls = []
for q, true_c in zip(queries, true_relevant_clusters):
    sims = all_embs_norm @ q
    top_50 = np.argsort(-sims)[:50]
    # Cross-encoder scores for top 50
    ce_scores = fake_cross_encoder(q, top_50)
    top_8 = top_50[np.argsort(-ce_scores)[:8]]
    ce_recalls.append(recall_at_k(top_8, true_c))
ce_ms = (time.perf_counter() - t0) * 1000 / N_QUERIES + 80  # add 80ms prod latency
ce_recall = np.mean(ce_recalls)
print(f"  Latency:        ~80ms per query (cross-encoder GPU)")
print(f"  Recall@8:       {ce_recall:.3f}")

# ════════════════════════════════════════════════════════════════
# STAGE 4: COMBINED — vector -> MMR -> cross-encoder (the prod pipeline)
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STAGE 4: COMBINED pipeline (the prod setup)")
print("=" * 70)
print("""
1. Vector search: top 50 candidates (~25ms, sub-linear via HNSW)
2. MMR: top 50 -> top 25 (intra-list diversity, ~2ms, free)
3. Cross-encoder: top 25 -> top 8 (~80ms, $0.001/search)
4. Build prompt with 8 chunks, call LLM

Total added latency: ~107ms. Cost: $1/1k searches.
Recall@8 boost over pure vector: typically +15-25 percentage points.
""")

t0 = time.perf_counter()
combined_recalls = []
for q, true_c in zip(queries, true_relevant_clusters):
    # 1. Vector top 50
    sims = all_embs_norm @ q
    top_50 = np.argsort(-sims)[:50]
    top_50_sims = sims[top_50]
    # 2. MMR top 50 -> 25
    top_25 = mmr(q, top_50, top_50_sims, lambda_=0.7, k=25)
    # 3. Cross-encoder top 25 -> 8
    ce_scores = fake_cross_encoder(q, top_25)
    top_8 = top_25[np.argsort(-ce_scores)[:8]]
    combined_recalls.append(recall_at_k(top_8, true_c))
combined_ms = (time.perf_counter() - t0) * 1000 / N_QUERIES + 80 + 2
combined_recall = np.mean(combined_recalls)
print(f"  Latency:        ~{combined_ms:.0f}ms per query")
print(f"  Recall@8:       {combined_recall:.3f}")

# ════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SUMMARY: the 4-way trade-off")
print("=" * 70)
print(f"\n{'Method':<30} {'Latency':>10} {'Cost/q':>8} {'Recall@8':>10}")
print("-" * 65)
print(f"{'Vector top-8 (naive)':<30} {naive_ms:>8.1f}ms {'$0':>8} {naive_recall:>10.3f}")
print(f"{'Vector top-50 + MMR':<30} {mmr_ms:>8.1f}ms {'$0':>8} {mmr_recall:>10.3f}")
print(f"{'Vector top-50 + cross-enc':<30} {ce_ms:>8.0f}ms {'$0.001':>8} {ce_recall:>10.3f}")
print(f"{'Vector + MMR + cross-enc':<30} {combined_ms:>8.0f}ms {'$0.001':>8} {combined_recall:>10.3f}")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'MMR or cross-encoder?')")
print("=" * 70)
print("""
Q: "Your vector search returns 50 candidates. Pipeline to top 8 for LLM.
    MMR, cross-encoder, or both?"

A: "Both, in a 3-stage pipeline:

  Stage 1: Vector top 50 (HNSW, ~25ms, $0)
           Cheap, recall-heavy, but redundant (5 docs from same employer)
  Stage 2: MMR top 50 -> top 25 (~2ms, $0)
           Removes redundancy WITHIN the list (intra-list diversity).
           Free, fast, no model.
  Stage 3: Cross-encoder top 25 -> top 8 (~80ms, $0.001)
           Joins (query, doc) text, scores jointly. Best relevance signal.
           Boosts Recall@8 by 15-25 pp.

Total: ~107ms added, $0.001/query. Worth it on the LAST hop.

When to skip cross-encoder:
- Latency budget < 200ms total: skip, use vector + MMR only
- Cost-sensitive path (1M+ queries/day): use small reranker
  (ms-marco-MiniLM, 30ms, free on GPU)

When to skip MMR:
- When your cross-encoder already returns 8 from 50, MMR is redundant
- Some pipelines do: vector 100 -> cross-encoder 8 directly (no MMR)

In prod, the L6 default is: vector 50 -> MMR 25 -> cross-encoder 8.
The MMR step is what differentiates 'good results' from 'wow results'.
""")
