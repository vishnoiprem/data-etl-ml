"""
Tiny cross-encoder rerank service.

Exposes /rerank that takes a query + top-K candidates and returns them
re-ordered by a cross-encoder score, plus the score distribution so
the caller can pick a threshold that matches its recall/precision budget.

Real impl: BGE-reranker, ms-marco-MiniLM, or Cohere's API.
"""
from __future__ import annotations
from statistics import mean
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Rerank Service")


class Candidate(BaseModel):
    id: str
    text: str
    metadata: dict = {}


class RerankRequest(BaseModel):
    query: str
    candidates: list[Candidate]
    top_k: Optional[int] = None  # if None, return all reranked


class ScoredCandidate(BaseModel):
    id: str
    text: str
    score: float
    rank: int
    metadata: dict


class RerankResponse(BaseModel):
    ranked: list[ScoredCandidate]
    score_dist: dict


def fake_cross_encoder_score(query: str, doc: str) -> float:
    """
    Toy scoring function. Real impl uses a cross-encoder model:
    `model.predict([(query, doc)])`.
    This toy uses token overlap as a placeholder.
    """
    q = set(query.lower().split())
    d = set(doc.lower().split())
    if not q or not d:
        return 0.0
    return len(q & d) / len(q | d)


@app.post("/rerank", response_model=RerankResponse)
def rerank(req: RerankRequest):
    pairs = [(req.query, c.text) for c in req.candidates]
    scores = [fake_cross_encoder_score(q, d) for q, d in pairs]

    ranked_with_scores = sorted(zip(req.candidates, scores), key=lambda x: -x[1])
    if req.top_k:
        ranked_with_scores = ranked_with_scores[: req.top_k]

    ranked = [
        ScoredCandidate(
            id=c.id, text=c.text, score=s, rank=i, metadata=c.metadata
        )
        for i, (c, s) in enumerate(ranked_with_scores)
    ]

    return RerankResponse(
        ranked=ranked,
        score_dist={
            "n": len(scores),
            "mean": round(mean(scores), 4) if scores else 0,
            "p10": round(sorted(scores)[max(0, len(scores) // 10)], 4) if scores else 0,
            "p50": round(sorted(scores)[len(scores) // 2], 4) if scores else 0,
            "p90": round(sorted(scores)[min(len(scores) - 1, int(len(scores) * 0.9))], 4) if scores else 0,
        },
    )


@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "rerank"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("service.app:app", host="0.0.0.0", port=8090, reload=True)
