"""Two-stage ranking: fuse the channels, then rerank the survivors.

Stage 1 (fusion) is about recall - get every good candidate into one list.
Stage 2 (rerank) is about precision - get the best candidate to position one.
"""

from collections import defaultdict

from .models import SearchResult
from .text import overlap_ratio, tokenize

# Weights for the rerank score. They sum to 1.0 so the result is always 0..1 and
# can be reported directly as confidence.
WEIGHT_FUSION = 0.50  # do the retrievers agree this is relevant?
WEIGHT_TITLE = 0.30   # a title match is strong evidence of topical intent
WEIGHT_BODY = 0.20    # body match is weaker: long documents mention many things


def reciprocal_rank_fusion(
    result_lists: list[list[SearchResult]], constant: int = 60
) -> list[SearchResult]:
    """Merge ranked lists using ranks instead of scores.

    A TF-IDF cosine of 0.3 and a connector score of 0.3 do not mean the same
    thing, so adding or averaging raw scores across channels is meaningless. RRF
    only reads each document's *position*, which every channel defines the same
    way. Documents found by several queries or channels accumulate score, which
    is what makes agreement between retrievers count for something.

    ``constant`` (conventionally 60) flattens the curve so rank 1 does not
    dominate ranks 2-5 outright.
    """
    fused_scores: dict[str, float] = defaultdict(float)
    best_hit: dict[str, SearchResult] = {}

    for results in result_lists:
        for rank, hit in enumerate(results, start=1):
            doc_id = hit.document.id
            fused_scores[doc_id] += 1 / (constant + rank)
            # Keep the strongest single appearance of each document as the
            # representative. This is also the deduplication step: one entry per
            # document id, no matter how many queries or channels returned it.
            if doc_id not in best_hit or hit.retrieval_score > best_hit[doc_id].retrieval_score:
                best_hit[doc_id] = hit

    fused = []
    for doc_id, score in fused_scores.items():
        representative = best_hit[doc_id]
        fused.append(
            SearchResult(
                document=representative.document,
                retrieval_score=representative.retrieval_score,
                query=representative.query,
                channel=representative.channel,
                fusion_score=score,
            )
        )

    fused.sort(key=lambda hit: hit.fusion_score, reverse=True)
    for rank, hit in enumerate(fused, start=1):
        hit.rank = rank
    return fused


def rerank(query: str, candidates: list[SearchResult], top_k: int = 5) -> list[SearchResult]:
    """Score candidates against the *original* query and keep the best `top_k`.

    Reranking uses the user's original wording, not the rewritten query: the
    rewrite exists to widen recall, but precision should be judged against what
    the user actually asked.

    The fusion score is normalized to 0..1 before it is blended. Raw RRF scores
    live around 0.016-0.06, so mixing them directly with 0..1 overlap ratios
    would let term overlap decide every ranking and make the fusion weight
    decorative.
    """
    if not candidates:
        return []

    query_terms = tokenize(query)
    largest_fusion = max(hit.fusion_score for hit in candidates) or 1.0

    for hit in candidates:
        hit.rerank_score = (
            WEIGHT_FUSION * (hit.fusion_score / largest_fusion)
            + WEIGHT_TITLE * overlap_ratio(query_terms, hit.document.title)
            + WEIGHT_BODY * overlap_ratio(query_terms, hit.document.text)
        )

    # Tie-break on document id so equal scores always produce the same order.
    # Non-deterministic ranking makes evaluation numbers impossible to trust.
    candidates.sort(key=lambda hit: (-hit.rerank_score, hit.document.id))

    top = candidates[:top_k]
    for rank, hit in enumerate(top, start=1):
        hit.rank = rank
    return top
