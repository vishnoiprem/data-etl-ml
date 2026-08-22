"""Offline retrieval metrics.

Retrieval quality and answer quality are evaluated separately. If you only
measure the final answer, you cannot tell whether a bad answer came from missing
evidence (a retrieval problem) or from bad reading of good evidence (a generation
problem) - and those have completely different fixes.

Every metric here is computed at a cutoff ``k``, because that is what the user
actually sees and what fits the context budget.
"""

import math


def _dcg(relevances: list[int]) -> float:
    """Discounted cumulative gain: relevance, discounted by how far down it sits."""
    return sum(rel / math.log2(position + 2) for position, rel in enumerate(relevances))


def evaluate_search(retrieved: list[str], relevant: list[str], k: int = 5) -> dict[str, float]:
    """Precision@k, Recall@k, MRR@k and NDCG@k for one query.

    ``retrieved`` is deduplicated first, preserving order: a system that returns
    the same document three times should not be able to inflate its own precision.
    """
    seen: set[str] = set()
    ranked = [doc_id for doc_id in retrieved if not (doc_id in seen or seen.add(doc_id))]

    top_k = ranked[:k]
    truth = set(relevant)
    hits = [doc_id for doc_id in top_k if doc_id in truth]

    # Precision divides by k, not by len(top_k). Returning 2 results and getting
    # 1 right is P@5 = 0.2, not 0.5 - otherwise a system can raise its score just
    # by returning fewer results.
    precision = len(hits) / k if k else 0.0
    recall = len(hits) / len(truth) if truth else 0.0

    # Reciprocal rank of the first relevant hit, inside the same cutoff.
    reciprocal_rank = next(
        (1 / position for position, doc_id in enumerate(top_k, start=1) if doc_id in truth),
        0.0,
    )

    gains = [1 if doc_id in truth else 0 for doc_id in top_k]
    ideal = _dcg(sorted(gains, reverse=True))
    ndcg = _dcg(gains) / ideal if ideal else 0.0

    return {
        "k": k,
        "precision_at_k": round(precision, 3),
        "recall_at_k": round(recall, 3),
        "mrr": round(reciprocal_rank, 3),
        "ndcg_at_k": round(ndcg, 3),
    }
