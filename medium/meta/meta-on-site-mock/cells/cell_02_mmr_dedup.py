import numpy as np

def pure_relevance_top_k(query_emb, chunk_embs, chunks, k=3):
    """Baseline: just take top-k by cosine sim, no diversity."""
    sims = chunk_embs @ query_emb
    top_k_idx = np.argsort(-sims)[:k]
    return [chunks[i] for i in top_k_idx], sims[top_k_idx]

# Create a scenario where 3 chunks are very similar to each other (duplicates)
np.random.seed(7)
query_emb = np.random.randn(D)
query_emb /= np.linalg.norm(query_emb)

chunk_embs = np.random.randn(N, D)
chunk_embs /= np.linalg.norm(chunk_embs, axis=1, keepdims=True)

# Make chunks 0, 1, 2 nearly identical (simulate duplicates)
chunk_embs[1] = chunk_embs[0] + 0.01 * np.random.randn(D)
chunk_embs[2] = chunk_embs[0] + 0.01 * np.random.randn(D)
chunk_embs[1] /= np.linalg.norm(chunk_embs[1])
chunk_embs[2] /= np.linalg.norm(chunk_embs[2])

chunks = [f"chunk_{i}: content variant {i}" for i in range(N)]

print("=" * 60)
print("PURE RELEVANCE (no diversity penalty) - picks duplicates:")
print("=" * 60)
top_k_relevant, sims = pure_relevance_top_k(query_emb, chunk_embs, chunks, k=3)
for c, s in zip(top_k_relevant, sims):
    print(f"  {c}  (sim={s:.3f})")

print()
print("=" * 60)
print("MMR (lambda=0.7) - picks diverse chunks:")
print("=" * 60)
top_k_mmr = mmr_rerank(query_emb, chunk_embs, chunks, lambda_=0.7, k=3)
for c in top_k_mmr:
    print(f"  {c}")
