"""Answer generation with citations."""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from .llm import LLMClient
from .retrievers import RetrievalResult


@dataclass
class Citation:
    chunk_id: str
    doc_id: str
    source: str  # which retrieval strategy produced this chunk


@dataclass
class Answer:
    text: str
    citations: list[Citation]


_PROMPT = """You are a precise, citation-grounded enterprise assistant.
Answer the question using ONLY the context below.  If the context doesn't
contain the answer, say "I don't have that information in the available documentation."
For every claim, cite the relevant doc by its name in [brackets].

Graph trace (entities and relations found, if any):
{graph_trace}

Context:
{context}

Question: {question}

Answer:"""


class AnswerGenerator:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def _format_context(self, result: RetrievalResult) -> str:
        parts: list[str] = []
        for i, hit in enumerate(result.hits, start=1):
            parts.append(f"[{i}] {hit.doc_id} (chunk {hit.chunk_id})\n{hit.text}\n")
        return "\n".join(parts) if parts else "(no context retrieved)"

    def _format_graph_trace(self, result: RetrievalResult) -> str:
        if not result.graph_edges:
            return "(no graph trace)"
        seeds = ", ".join(result.graph_seeds) or "(none)"
        lines = [f"Seed entities: {seeds}", "Edges:"]
        for s, r, t in result.graph_edges:
            lines.append(f"  {s} --[{r}]--> {t}")
        return "\n".join(lines)

    def _strategy_for(self, chunk_id: str, result: RetrievalResult) -> str:
        for strat, ids in result.contributions.items():
            if chunk_id in ids:
                return strat
        return "fused"

    def generate(self, result: RetrievalResult) -> Answer:
        prompt = _PROMPT.format(
            graph_trace=self._format_graph_trace(result),
            context=self._format_context(result),
            question=result.query,
        )
        logger.debug(f"Generation prompt:\n{prompt[:400]}...")
        text = self._llm.complete(prompt)
        citations = [
            Citation(
                chunk_id=h.chunk_id,
                doc_id=h.doc_id,
                source=self._strategy_for(h.chunk_id, result),
            )
            for h in result.hits
        ]
        return Answer(text=text.strip(), citations=citations)
