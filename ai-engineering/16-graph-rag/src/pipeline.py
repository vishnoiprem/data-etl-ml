"""Top-level GraphRAGPipeline — wires together ingestion, indices, retrieval, generation."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from loguru import logger

from .bm25_index import BM25Index
from .config import get_settings
from .embeddings import _get_model  # noqa: F401  — warm-load the model
from .generation import Answer, AnswerGenerator
from .graph_builder import build_graph
from .graph_store import GraphStore
from .ingestion import Doc, load_corpus, read_jsonl
from .llm import LLMClient, get_llm
from .retrievers import (
    BM25Retriever,
    GraphRetriever,
    HybridRetriever,
    RetrievalResult,
    Retriever,
    VectorRetriever,
)
from .vector_index import VectorIndex


STRATEGIES = ("vector", "bm25", "graph", "hybrid")


@dataclass
class EvalRow:
    question: str
    expected_doc_ids: list[str]
    expected_keywords: list[str]
    kind: str  # "single-hop" | "two-hop" | "adversarial"
    strategy: str
    cited_doc_ids: list[str]
    cited_chunk_ids: list[str]
    answer_excerpt: str
    keyword_hit_rate: float
    citation_precision: float
    refused: bool


@dataclass
class EvalReport:
    rows: list[EvalRow] = field(default_factory=list)

    def by_strategy(self) -> dict[str, list[EvalRow]]:
        out: dict[str, list[EvalRow]] = {s: [] for s in STRATEGIES}
        for r in self.rows:
            out.setdefault(r.strategy, []).append(r)
        return out

    def markdown_table(self) -> str:
        lines = [
            "| Strategy | Eval set | n | Citation precision | Keyword hit rate | Refused |",
            "|---|---|---|---|---|---|",
        ]
        for kind in ("single-hop", "two-hop", "adversarial"):
            for strat in STRATEGIES:
                rows = [r for r in self.rows if r.strategy == strat and r.kind == kind]
                if not rows:
                    continue
                n = len(rows)
                cp = sum(r.citation_precision for r in rows) / n
                kh = sum(r.keyword_hit_rate for r in rows) / n
                rf = sum(1 for r in rows if r.refused) / n
                lines.append(
                    f"| {strat} | {kind} | {n} | {cp:.0%} | {kh:.0%} | {rf:.0%} |"
                )
        return "\n".join(lines)

    def save_jsonl(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for r in self.rows:
                f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")


class GraphRAGPipeline:
    """End-to-end orchestrator. Built once via `.build(corpus_dir)`; query forever."""

    def __init__(self) -> None:
        self.chunks: list[Doc] = []
        self.vector_index = VectorIndex()
        self.bm25_index = BM25Index()
        self.graph = GraphStore()
        self.llm: LLMClient = get_llm()
        self.generator = AnswerGenerator(self.llm)
        self._retrievers: dict[str, Retriever] = {}

    # ---- build / load --------------------------------------------------

    def build(self, corpus_dir: Path) -> None:
        s = get_settings()
        logger.info(f"Loading corpus from {corpus_dir}")
        self.chunks = load_corpus(corpus_dir)
        logger.info(f"  → {len(self.chunks)} chunks from {len({c.doc_id for c in self.chunks})} docs")
        logger.info("Building vector index ...")
        self.vector_index.build(self.chunks)
        logger.info("Building BM25 index ...")
        self.bm25_index.build(self.chunks)
        logger.info("Building knowledge graph ...")
        self.graph = build_graph(self.chunks, self.llm)
        self._wire_retrievers()
        # Persist
        self.vector_index.save("vector")
        self.bm25_index.save("bm25")
        self.graph.save(s.graph_path())
        # Also dump chunks.jsonl for the graph retriever to read at load time
        chunks_dump = s.chunks_path("chunks")
        with chunks_dump.open("w", encoding="utf-8") as f:
            for c in self.chunks:
                f.write(json.dumps({"doc_id": c.doc_id, "chunk_id": c.chunk_id, "text": c.text, "title": c.title}) + "\n")
        logger.info("Pipeline built and persisted to ./data")

    def load(self) -> None:
        s = get_settings()
        logger.info("Loading persisted indices ...")
        self.vector_index.load("vector")
        self.bm25_index.load("bm25")
        self.graph.load(s.graph_path())
        chunks_path = s.chunks_path("chunks")
        self.chunks = [Doc(**d) for d in read_jsonl(chunks_path)]
        # Re-populate the vector index's internal _chunks (load() does this)
        # but the graph retriever also needs a VectorIndex for chunk text lookup,
        # so we re-use self.vector_index.
        self._wire_retrievers()
        logger.info("Pipeline loaded.")

    def _wire_retrievers(self) -> None:
        self._retrievers = {
            "vector": VectorRetriever(self.vector_index),
            "bm25": _BM25AsRetriever(self.bm25_index),
            "graph": GraphRetriever(self.graph, self.vector_index),
            "hybrid": HybridRetriever(
                {
                    "vector": self._retrievers.get("vector") or VectorRetriever(self.vector_index),
                    "bm25": _BM25AsRetriever(self.bm25_index),
                    "graph": GraphRetriever(self.graph, self.vector_index),
                }
            ),
        }
        # The hybrid dict above is built from any pre-existing retrievers + new
        # ones; re-build cleanly:
        self._retrievers["hybrid"] = HybridRetriever(
            {
                "vector": VectorRetriever(self.vector_index),
                "bm25": _BM25AsRetriever(self.bm25_index),
                "graph": GraphRetriever(self.graph, self.vector_index),
            }
        )

    # ---- query ---------------------------------------------------------

    def retrieve(self, question: str, strategy: str = "hybrid") -> RetrievalResult:
        if strategy not in self._retrievers:
            raise ValueError(f"Unknown strategy {strategy!r}. Choose from {STRATEGIES}.")
        return self._retrievers[strategy].retrieve(question)

    def query(self, question: str, strategy: str = "hybrid") -> Answer:
        result = self.retrieve(question, strategy=strategy)
        return self.generator.generate(result)

    # ---- eval ----------------------------------------------------------

    def eval(self, eval_path: Path) -> EvalReport:
        rows = read_jsonl(eval_path)
        report = EvalReport()
        for row in rows:
            question = row["question"]
            expected_docs = set(row.get("expected_doc_ids", []))
            expected_kw = [k.lower() for k in row.get("expected_keywords", [])]
            kind = row.get("kind", "single-hop")
            for strat in STRATEGIES:
                result = self.retrieve(question, strategy=strat)
                answer = self.generator.generate(result)
                cited_docs = result.doc_ids()
                cited_chunks = result.chunk_ids()
                if expected_docs:
                    cp = len([d for d in cited_docs if d in expected_docs]) / max(1, len(cited_docs))
                else:
                    cp = 0.0
                lower = answer.text.lower()
                if expected_kw:
                    kh = sum(1 for k in expected_kw if k in lower) / len(expected_kw)
                else:
                    kh = 0.0
                refused = "i don't have that information" in lower or "i don't know" in lower
                report.rows.append(
                    EvalRow(
                        question=question,
                        expected_doc_ids=sorted(expected_docs),
                        expected_keywords=row.get("expected_keywords", []),
                        kind=kind,
                        strategy=strat,
                        cited_doc_ids=cited_docs,
                        cited_chunk_ids=cited_chunks,
                        answer_excerpt=answer.text[:160],
                        keyword_hit_rate=kh,
                        citation_precision=cp,
                        refused=refused,
                    )
                )
        return report


# ─────────────────────────────────────────────────────────────────────────────
# Small adapter so BM25Index exposes the Retriever protocol via composition
# ─────────────────────────────────────────────────────────────────────────────

from .bm25_index import BM25Index as _BM25  # noqa: E402
from .retrievers import BM25Retriever as _BM25R  # noqa: E402


def _BM25AsRetriever(idx: BM25Index) -> _BM25R:
    return _BM25R(idx)
