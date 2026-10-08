"""Retrievers: Vector, BM25, Graph, Hybrid (RRF fusion)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from loguru import logger

from .bm25_index import BM25Hit, BM25Index
from .config import get_settings
from .graph_store import GraphStore
from .vector_index import Hit, VectorIndex


@dataclass
class RetrievalResult:
    """Unified retrieval output. `hits` is ordered, best first."""
    query: str
    strategy: str  # "vector" | "bm25" | "graph" | "hybrid"
    hits: list[Hit] = field(default_factory=list)
    # Provenance — populated by graph retriever, kept on every result
    graph_edges: list[tuple[str, str, str]] = field(default_factory=list)
    graph_seeds: list[str] = field(default_factory=list)
    # Per-strategy contributions (for hybrid)
    contributions: dict[str, list[str]] = field(default_factory=dict)

    def chunk_ids(self) -> list[str]:
        return [h.chunk_id for h in self.hits]

    def doc_ids(self) -> list[str]:
        # Preserve order, dedupe
        seen: set[str] = set()
        out: list[str] = []
        for h in self.hits:
            if h.doc_id not in seen:
                seen.add(h.doc_id)
                out.append(h.doc_id)
        return out


class Retriever(ABC):
    name: str = "abstract"

    @abstractmethod
    def retrieve(self, query: str) -> RetrievalResult: ...


# ─────────────────────────────────────────────────────────────────────────────
# Vector
# ─────────────────────────────────────────────────────────────────────────────

class VectorRetriever(Retriever):
    name = "vector"

    def __init__(self, index: VectorIndex) -> None:
        self._idx = index

    def retrieve(self, query: str) -> RetrievalResult:
        hits = self._idx.search(query)
        return RetrievalResult(
            query=query,
            strategy=self.name,
            hits=hits,
            contributions={"vector": [h.chunk_id for h in hits]},
        )


# ─────────────────────────────────────────────────────────────────────────────
# BM25
# ─────────────────────────────────────────────────────────────────────────────

class BM25Retriever(Retriever):
    name = "bm25"

    def __init__(self, index: BM25Index) -> None:
        self._idx = index

    def retrieve(self, query: str) -> RetrievalResult:
        bm25_hits: list[BM25Hit] = self._idx.search(query)
        # Reuse Hit so downstream code is uniform
        hits = [
            Hit(chunk_id=h.chunk_id, doc_id=h.doc_id, text=h.text, score=h.score)
            for h in bm25_hits
        ]
        return RetrievalResult(
            query=query,
            strategy=self.name,
            hits=hits,
            contributions={"bm25": [h.chunk_id for h in hits]},
        )


# ─────────────────────────────────────────────────────────────────────────────
# Graph
# ─────────────────────────────────────────────────────────────────────────────

class GraphRetriever(Retriever):
    """Entity-link the query → seed subgraph → flatten edges to text.

    Output chunks are pulled from the chunks that *cite* any of the surface
    entities in the seed subgraph.  This is the standard "expand, then read"
    GraphRAG pattern (Edge et al., 2024).
    """

    name = "graph"

    def __init__(self, graph: GraphStore, chunks_index: VectorIndex) -> None:
        self._g = graph
        self._chunks = chunks_index

    def retrieve(self, query: str) -> RetrievalResult:
        s = get_settings()
        seeds = self._g.link_query(query)
        if not seeds:
            logger.debug(f"GraphRetriever: no entity seeds for {query!r}")
            return RetrievalResult(query=query, strategy=self.name, graph_seeds=[])
        edges = self._g.subgraph_edges(seeds, depth=s.graph_expand_depth)
        # Surface the seed entities and one-hop neighbours; build a textual
        # "graph trace" we'll prepend to context.
        trace = "\n".join(f"  {s} --[{r}]--> {t}" for s, r, t in edges)
        # Pull the chunks that contain any seed (very cheap "grounding" filter)
        seed_text = " ".join(seeds).lower()
        supporting_hits: list[Hit] = []
        for c in self._chunks._chunks:  # noqa: SLF001 — internal, but demo-scale
            if any(seed.lower() in c.text.lower() for seed in seeds):
                supporting_hits.append(
                    Hit(chunk_id=c.chunk_id, doc_id=c.doc_id, text=c.text, score=1.0)
                )
        # Order by doc appearance in the trace
        order = {doc: i for i, (doc, _, _) in enumerate(edges)}
        supporting_hits.sort(key=lambda h: order.get(h.doc_id, 999))
        return RetrievalResult(
            query=query,
            strategy=self.name,
            hits=supporting_hits[: s.top_k_graph],
            graph_edges=edges,
            graph_seeds=seeds,
            contributions={"graph": [h.chunk_id for h in supporting_hits]},
        )


# ─────────────────────────────────────────────────────────────────────────────
# Hybrid — Reciprocal Rank Fusion
# ─────────────────────────────────────────────────────────────────────────────

class HybridRetriever(Retriever):
    """Reciprocal Rank Fusion over vector + BM25 + graph (Cormack et al., 2009).

    score(d) = Σ_i  1 / (k + rank_i(d))
    where rank_i(d) is the rank of d in strategy i's result list (1-indexed;
    0 if d is not in that strategy's list).
    """

    name = "hybrid"

    def __init__(self, retrievers: dict[str, Retriever]) -> None:
        if not retrievers:
            raise ValueError("HybridRetriever needs at least one sub-retriever")
        self._retrievers = retrievers
        self._chunks_lookup: dict[str, Hit] = {}

    def _chunks_index(self, retrievers: list[Retriever]) -> VectorIndex:
        # We pull the underlying chunks from the vector retriever for text lookup
        for r in retrievers:
            if isinstance(r, VectorRetriever):
                return r._idx  # noqa: SLF001
        raise RuntimeError("HybridRetriever currently requires a VectorRetriever for chunk text lookup")

    def retrieve(self, query: str) -> RetrievalResult:
        s = get_settings()
        per_strategy: dict[str, list[Hit]] = {}
        for name, retr in self._retrievers.items():
            try:
                res = retr.retrieve(query)
            except Exception as e:
                logger.warning(f"Strategy {name} failed: {e}")
                continue
            per_strategy[name] = res.hits
            # Index chunk text
            for h in res.hits:
                self._chunks_lookup[h.chunk_id] = h

        # RRF
        scores: dict[str, float] = {}
        best_rank: dict[str, dict[str, int]] = {}
        for strat, hits in per_strategy.items():
            for rank, h in enumerate(hits, start=1):
                scores[h.chunk_id] = scores.get(h.chunk_id, 0.0) + 1.0 / (s.rrf_k + rank)
                best_rank.setdefault(h.chunk_id, {})[strat] = rank

        ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        fused: list[Hit] = []
        for chunk_id, score in ordered[: s.top_k_vector]:
            hit = self._chunks_lookup.get(chunk_id)
            if hit is None:
                continue
            fused.append(
                Hit(chunk_id=hit.chunk_id, doc_id=hit.doc_id, text=hit.text, score=score)
            )

        # Carry graph provenance from the graph sub-retriever
        graph_edges: list[tuple[str, str, str]] = []
        graph_seeds: list[str] = []
        for name, retr in self._retrievers.items():
            if isinstance(retr, GraphRetriever):
                # We already called .retrieve above, but the result is dropped.
                # Re-run for provenance — cheap for demo-scale graphs.
                gr = retr.retrieve(query)
                graph_edges = gr.graph_edges
                graph_seeds = gr.graph_seeds

        return RetrievalResult(
            query=query,
            strategy=self.name,
            hits=fused,
            graph_edges=graph_edges,
            graph_seeds=graph_seeds,
            contributions={k: [h.chunk_id for h in v] for k, v in per_strategy.items()},
        )
