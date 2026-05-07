"""FastAPI service for the RAG pipeline.

Run with:
    uvicorn src.api.main:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.config import settings
from src.generation.rag_pipeline import RagPipeline


app = FastAPI(
    title="AskAcme — Enterprise RAG API",
    description="Grounded enterprise knowledge Q&A with citations.",
    version="1.0.0",
)
_pipeline: RagPipeline | None = None


def get_pipeline() -> RagPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RagPipeline()
    return _pipeline


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    user_groups: list[str] | None = None  # in real systems, derived from auth, not user input


class SourceModel(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    source: str
    score: float
    text_preview: str


class AskResponse(BaseModel):
    question: str
    answer: str
    refused: bool
    refusal_reason: str | None = None
    sources: list[SourceModel]
    telemetry: dict


@app.get("/health")
def health():
    return {"status": "ok", "mode": settings.AI_ENGINEERING_MODE}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    try:
        pipeline = get_pipeline()
        filters = {"acl_groups": req.user_groups} if req.user_groups else None
        result = pipeline.ask(req.question, filters=filters)
        return AskResponse(
            question=result.question,
            answer=result.answer,
            refused=result.refused,
            refusal_reason=result.refusal_reason,
            sources=[SourceModel(**s.__dict__) for s in result.sources],
            telemetry=result.telemetry,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
