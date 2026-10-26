import numpy as np

def mmr_rerank(query_emb, chunk_embs, chunks, lambda_=0.7, k=8):
    """
    Maximal Marginal Relevance reranking.

    Args:
        query_emb:   [D]            - query embedding vector
        chunk_embs:  [N, D]         - all candidate chunk embeddings
        chunks:      list of N      - the actual chunk texts/metadata
        lambda_:     float          - relevance vs diversity tradeoff (0.7 = favor relevance)
        k:           int            - number of chunks to return

    Returns:
        list of k chunks that are relevant AND diverse

    Complexity: O(k * N * D) - fine for k=8, N=50.
    For N=10k+, use approximate MMR via HNSW.
    """
    selected = []
    candidates = list(range(len(chunks)))

    # Pre-compute cosine similarity of each chunk to query (assumes normalized vectors)
    sim_to_query = chunk_embs @ query_emb  # [N]

    while len(selected) < k and candidates:
        if not selected:
            # First pick: most relevant to query
            best = max(candidates, key=lambda i: sim_to_query[i])
        else:
            # Score each candidate: relevance - diversity penalty
            scores = []
            for i in candidates:
                # max similarity to ANY already-selected chunk
                max_sim_to_selected = max(
                    chunk_embs[i] @ chunk_embs[j]
                    for j in selected
                )
                mmr_score = (lambda_ * sim_to_query[i]
                           - (1 - lambda_) * max_sim_to_selected)
                scores.append((mmr_score, i))
            best = max(scores)[1]

        selected.append(best)
        candidates.remove(best)

    return [chunks[i] for i in selected]


# TEST IT
np.random.seed(42)
N, D = 10, 64
query_emb = np.random.randn(D)
query_emb /= np.linalg.norm(query_emb)  # normalize for cosine sim

chunk_embs = np.random.randn(N, D)
chunk_embs /= np.linalg.norm(chunk_embs, axis=1, keepdims=True)  # normalize

chunks = [f"chunk_{i}: this is some text about topic {i}" for i in range(N)]

result = mmr_rerank(query_emb, chunk_embs, chunks, lambda_=0.7, k=3)
print("Top 3 MMR-selected chunks:")
for i, c in enumerate(result):
    print(f"  {i+1}. {c}")
print()
print("Without MMR, you'd just take top-3 by cosine sim to query -")
print("which often returns 3 near-duplicates. MMR forces diversity.")
