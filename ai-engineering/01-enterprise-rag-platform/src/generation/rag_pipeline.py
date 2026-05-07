"""RAG orchestration — the heart of the platform.

This is the place where retrieval + reranking + refusal + generation come
together. It's intentionally framework-free (no LangChain / LlamaIndex)
to keep the moving parts visible and testable.

Pipeline:
    query
      → query rewrite (optional)
      → hybrid retrieve (top-K_retrieve)
      → rerank (top-K_rerank)
      → refusal gate (low-score → "I don't know")
      → build prompt with citations
      → generate
      → citation validation
      → return answer + sources + telemetry
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from src.config import settings
from src.embedding.embedder import Embedder, get_embedder
from src.generation.llm import LLM, SYSTEM_PROMPT, build_user_prompt, get_llm
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.hybrid import HybridRetriever, RetrievalResult
from src.retrieval.reranker import Reranker, get_reranker
from src.retrieval.vector_store import VectorStore, get_vector_store


@dataclass
class Source:
    chunk_id: str
    doc_id: str
    title: str
    source: str
    score: float
    text_preview: str


@dataclass
class Answer:
    question: str
    answer: str
    sources: list[Source]
    refused: bool = False
    refusal_reason: str | None = None
    telemetry: dict = field(default_factory=dict)


class RagPipeline:
    """End-to-end RAG pipeline."""

    def __init__(
        self,
        embedder: Embedder | None = None,
        vector_store: VectorStore | None = None,
        bm25: BM25Retriever | None = None,
        reranker: Reranker | None = None,
        llm: LLM | None = None,
    ):
        self.embedder = embedder or get_embedder()
        self.vector_store = vector_store or get_vector_store(dim=self.embedder.dim)
        self.bm25 = bm25 or BM25Retriever()
        self.reranker = reranker or get_reranker()
        self.llm = llm or get_llm()
        self.hybrid = HybridRetriever(self.embedder, self.vector_store, self.bm25)

    # ---------- Retrieval ---------------------------------------------------

    def retrieve(self, question: str, filters: dict | None = None) -> list[RetrievalResult]:
        results = self.hybrid.retrieve(
            question, top_k=settings.RETRIEVE_TOP_K, filters=filters
        )
        if not results:
            return []
        results = self.reranker.rerank(question, results, top_k=settings.RERANK_TOP_K)
        return results

    # ---------- Generation --------------------------------------------------

    def _refusal_gate(self, results: list[RetrievalResult]) -> tuple[bool, str | None]:
        if not results:
            return True, "No documents matched the query."
        top = results[0].score
        if top < settings.REFUSAL_SCORE_THRESHOLD:
            return True, f"Top reranker score {top:.2f} below threshold {settings.REFUSAL_SCORE_THRESHOLD}."
        return False, None

    @staticmethod
    def _validate_citations(answer_text: str, valid_chunk_ids: set[str]) -> dict:
        """Check that citations in the answer reference real chunks."""
        cited = set(re.findall(r"\[([a-f0-9]{8,32})\]", answer_text))
        invalid = cited - valid_chunk_ids
        return {
            "cited_chunks": list(cited),
            "invalid_chunks": list(invalid),
            "had_citations": bool(cited),
        }

    # ---------- Public ------------------------------------------------------

    def ask(self, question: str, filters: dict | None = None) -> Answer:
        t0 = time.time()
        telemetry: dict[str, Any] = {"mode": settings.AI_ENGINEERING_MODE}

        retrieved = self.retrieve(question, filters=filters)
        telemetry["retrieve_top_k"] = len(retrieved)
        telemetry["retrieve_ms"] = int((time.time() - t0) * 1000)

        # Refusal gate
        refused, reason = self._refusal_gate(retrieved)
        if refused:
            logger.info(f"Refusing: {reason}")
            return Answer(
                question=question,
                answer="I don't know based on available documents.",
                sources=[],
                refused=True,
                refusal_reason=reason,
                telemetry=telemetry,
            )

        # Build prompt
        contexts = [
            {
                "chunk_id": r.chunk.chunk_id,
                "text": r.chunk.text,
                "source": r.chunk.source,
                "title": r.chunk.title,
            }
            for r in retrieved
        ]
        user_prompt = build_user_prompt(question, contexts)

        t1 = time.time()
        llm_resp = self.llm.generate(system=SYSTEM_PROMPT, user=user_prompt)
        telemetry["llm_ms"] = int((time.time() - t1) * 1000)
        telemetry["in_tokens"] = llm_resp.in_tokens
        telemetry["out_tokens"] = llm_resp.out_tokens
        telemetry["model"] = llm_resp.model

        # Citation validation
        valid_ids = {r.chunk.chunk_id for r in retrieved}
        cite_check = self._validate_citations(llm_resp.text, valid_ids)
        telemetry["citations"] = cite_check

        sources = [
            Source(
                chunk_id=r.chunk.chunk_id,
                doc_id=r.chunk.doc_id,
                title=r.chunk.title,
                source=r.chunk.source,
                score=r.score,
                text_preview=r.chunk.text[:200] + ("…" if len(r.chunk.text) > 200 else ""),
            )
            for r in retrieved
        ]

        telemetry["total_ms"] = int((time.time() - t0) * 1000)
        return Answer(
            question=question,
            answer=llm_resp.text,
            sources=sources,
            telemetry=telemetry,
        )
