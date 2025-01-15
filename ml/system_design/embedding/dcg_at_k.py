import  numpy as np

def dcg_at_k(relevance_scores, k):
    relevance_scores = relevance_scores[:k]
    return sum(rel / np.log2(idx + 2) for idx, rel in enumerate(relevance_scores))

# Simulated relevance scores
relevance_scores = [3, 2, 3, 0, 1]
k = 5
print(f"DCG@{k}: {dcg_at_k(relevance_scores, k):.4f}")