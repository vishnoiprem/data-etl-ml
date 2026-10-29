"""Pydantic request/response schemas."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    chunk_id: str
    source: str
    score: float


class RetrievedChunk(BaseModel):
    chunk_id: str
    text: str
    score: float


class TraceSummary(BaseModel):
    trace_id: str
    created_at: datetime
    prompt_version: str
    user_query: str
    token_usage: int
    latency_ms: int
    status: str
    feedback: Optional[str] = None


class TraceDetail(TraceSummary):
    prompt: str
    retrieved_chunks: List[RetrievedChunk]
    model_response: str
    citations: List[Citation]


class PageMeta(BaseModel):
    next_cursor: Optional[str] = None
    has_more: bool


class TracePage(BaseModel):
    items: List[TraceSummary]
    meta: PageMeta


class FeedbackIn(BaseModel):
    rating: str = Field(pattern="^(up|down)$")
    note: Optional[str] = None


class FeedbackOut(BaseModel):
    trace_id: str
    rating: str
    note: Optional[str] = None
    created_at: datetime
