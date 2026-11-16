"""Hybrid retrieval over the trade-finder corpus.

Three pieces, each independently inspectable:

**BM25** — lexical scoring, implemented here rather than pulled from a
dependency. The corpus is small (a few hundred documents) and the ranking
behaviour is worth being able to read.

**Dense** — ``sentence-transformers`` embeddings. Optional: if the package or
the model weights are missing, the retriever degrades to BM25-only and says so
in ``dense_enabled`` rather than failing. A sourcing decision should never die
because an embedding model is not downloaded.

**RRF fusion** — reciprocal rank fusion, the same approach as the repo's
enterprise-search agent. It combines rankings without needing the two score
scales to be comparable, which they are not (BM25 is unbounded, cosine is
0-1).
"""

from __future__ import annotations

import math
import re
import time
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

from .config import EMBEDDING_MODEL_NAME, RRF_K
from .corpus import Document

_TOKEN_RE = re.compile(r"[a-z0-9]+")

#: Words that appear in nearly every document and carry no signal. The
#: corpus is small, so IDF alone does not fully suppress these.
_STOPWORDS = frozenset(
    """
    a an the and or of to in on at for with is are was were be been being
    it its this that these those as by from per unit units usd
    """.split()
)


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens, with stopwords removed."""
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]


# --------------------------------------------------------------------------- #
# BM25
# --------------------------------------------------------------------------- #


@dataclass
class BM25Index:
    """A plain BM25 index over the corpus.

    k1 controls term-frequency saturation, b controls how much document
    length is normalised. The defaults are the ones from the original BM25
    paper and work well on short, similar-length documents.
    """

    documents: list[Document]
    k1: float = 1.5
    b: float = 0.75
    _tf: list[Counter[str]] = field(default_factory=list, init=False)
    _df: Counter[str] = field(default_factory=Counter, init=False)
    _doc_len: list[int] = field(default_factory=list, init=False)
    _avg_len: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self._tf = []
        self._df = Counter()
        self._doc_len = []
        for doc in self.documents:
            tokens = tokenize(f"{doc.title} {doc.text}")
            counts = Counter(tokens)
            self._tf.append(counts)
            self._doc_len.append(len(tokens))
            for term in counts:
                self._df[term] += 1
        self._avg_len = (sum(self._doc_len) / len(self._doc_len)) if self._doc_len else 0.0

    def _idf(self, term: str) -> float:
        n = len(self.documents)
        df = self._df.get(term, 0)
        # Robertson/Sparck-Jones IDF with +1 smoothing, floored at zero.
        return max(0.0, math.log(1 + (n - df + 0.5) / (df + 0.5)))

    def score(self, query: str) -> list[float]:
        """BM25 score for every document, in corpus order."""
        terms = tokenize(query)
        scores = [0.0] * len(self.documents)
        if not terms:
            return scores
        for idx, counts in enumerate(self._tf):
            length = self._doc_len[idx]
            denom_len = self.k1 * (1 - self.b + self.b * (length / self._avg_len)) if self._avg_len else self.k1
            total = 0.0
            for term in terms:
                tf = counts.get(term, 0)
                if tf == 0:
                    continue
                idf = self._idf(term)
                total += idf * (tf * (self.k1 + 1)) / (tf + denom_len)
            scores[idx] = total
        return scores

    def search(self, query: str, top_k: int = 10) -> list[tuple[Document, float]]:
        scores = self.score(query)
        ranked = sorted(
            ((doc, s) for doc, s in zip(self.documents, scores, strict=True)),
            key=lambda pair: (-pair[1], pair[0].doc_id),
        )
        return [(doc, s) for doc, s in ranked[:top_k] if s > 0.0]


# --------------------------------------------------------------------------- #
# Dense
# --------------------------------------------------------------------------- #


class DenseIndex:
    """Cosine-similarity search over sentence-transformer embeddings.

    Construction is lazy and failure-tolerant: if the package is missing or
    the model cannot be loaded, ``available`` stays False and callers fall
    back to lexical-only retrieval.
    """

    def __init__(self, documents: Sequence[Document], model_name: str = EMBEDDING_MODEL_NAME):
        self.documents = list(documents)
        self.model_name = model_name
        self.available = False
        self.reason: str | None = None
        self._embeddings = None
        self._model = None

    def build(self) -> bool:
        """Try to load the model and embed the corpus. Never raises."""
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as exc:
            self.reason = f"sentence-transformers unavailable: {exc}"
            return False
        try:
            self._model = SentenceTransformer(self.model_name)
            corpus_texts = [f"{d.title}. {d.text}" for d in self.documents]
            self._embeddings = self._model.encode(
                corpus_texts, normalize_embeddings=True, show_progress_bar=False
            )
        except Exception as exc:
            self.reason = f"embedding model {self.model_name!r} could not be loaded: {exc}"
            self._model = None
            self._embeddings = None
            return False
        self.available = True
        return True

    def search(self, query: str, top_k: int = 10) -> list[tuple[Document, float]]:
        if not self.available or self._embeddings is None:
            return []
        try:
            vector = self._model.encode([query], normalize_embeddings=True, show_progress_bar=False)
            scores = (self._embeddings @ vector[0]).tolist()
        except Exception as exc:  # pragma: no cover - runtime encode failure
            self.reason = f"dense encode failed: {exc}"
            self.available = False
            return []
        ranked = sorted(
            ((doc, float(s)) for doc, s in zip(self.documents, scores, strict=True)),
            key=lambda pair: (-pair[1], pair[0].doc_id),
        )
        return ranked[:top_k]


# --------------------------------------------------------------------------- #
# Filters
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Filters:
    """Pre-filters applied before fusion.

    A supplier that cannot ship to the destination market, or whose route
    does not clear the margin floor, should not appear in the results at all
    — filtering after ranking would leave an irrelevant document in the top-k.
    """

    dest_country: str | None = None
    category: str | None = None
    min_margin: float | None = None
    max_lead_time_days: int | None = None
    doc_types: tuple[str, ...] | None = None

    def allows(self, doc: Document) -> bool:
        meta = doc.metadata
        if self.doc_types is not None and doc.doc_type not in self.doc_types:
            return False
        if self.dest_country and meta.get("dest_country") != self.dest_country:
            # Supplier and reputation docs are not route-scoped, so they are
            # not excluded by a destination filter.
            if doc.doc_type == "product":
                return False
        if self.category and meta.get("category") != self.category:
            if doc.doc_type == "product":
                return False
        if self.min_margin is not None:
            margin = meta.get("margin_pct")
            if margin is not None and margin < self.min_margin:
                return False
        if self.max_lead_time_days is not None:
            lead = meta.get("lead_time_days")
            if lead is not None and lead > self.max_lead_time_days:
                return False
        return True


# --------------------------------------------------------------------------- #
# Results and fusion
# --------------------------------------------------------------------------- #


@dataclass
class SearchHit:
    doc: Document
    score: float
    rank: int = 0
    lexical_rank: int | None = None
    dense_rank: int | None = None
    lexical_score: float | None = None
    dense_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc.doc_id,
            "doc_type": self.doc.doc_type,
            "title": self.doc.title,
            "text": self.doc.text,
            "source_path": self.doc.source_path,
            "source_line": self.doc.source_line,
            "metadata": self.doc.metadata,
            "score": round(self.score, 6),
            "rank": self.rank,
            "lexical_rank": self.lexical_rank,
            "dense_rank": self.dense_rank,
            "lexical_score": (
                round(self.lexical_score, 6) if self.lexical_score is not None else None
            ),
            "dense_score": (
                round(self.dense_score, 6) if self.dense_score is not None else None
            ),
        }


def reciprocal_rank_fusion(
    rankings: Iterable[Sequence[Document]], k: int = RRF_K
) -> list[tuple[Document, float]]:
    """Fuse multiple ranked lists by reciprocal rank.

    RRF ignores the raw score magnitudes and uses only the rank positions, so
    a BM25 score of 14.2 and a cosine similarity of 0.83 can be combined
    without one swamping the other.
    """
    fused: dict[str, float] = {}
    docs: dict[str, Document] = {}
    for ranking in rankings:
        for position, doc in enumerate(ranking, start=1):
            fused[doc.doc_id] = fused.get(doc.doc_id, 0.0) + 1.0 / (k + position)
            docs[doc.doc_id] = doc
    return sorted(
        ((docs[doc_id], score) for doc_id, score in fused.items()),
        key=lambda pair: (-pair[1], pair[0].doc_id),
    )


# --------------------------------------------------------------------------- #
# Retriever
# --------------------------------------------------------------------------- #


class HybridRetriever:
    """BM25 + dense, fused with RRF, with pre-filters."""

    def __init__(
        self,
        documents: Sequence[Document],
        *,
        use_dense: bool = True,
        model_name: str = EMBEDDING_MODEL_NAME,
        dense_timeout_s: float = 120.0,
    ):
        self.documents = list(documents)
        self.bm25 = BM25Index(self.documents)
        self.dense = DenseIndex(self.documents, model_name=model_name)
        self.dense_requested = use_dense
        self.dense_timeout_s = dense_timeout_s
        self._dense_built = False
        self._dense_build_seconds: float | None = None

    # -- dense availability ------------------------------------------------ #

    def _ensure_dense(self) -> None:
        if self._dense_built or not self.dense_requested:
            return
        self._dense_built = True
        started = time.perf_counter()
        self.dense.build()
        self._dense_build_seconds = time.perf_counter() - started

    @property
    def dense_enabled(self) -> bool:
        return self.dense.available

    @property
    def dense_reason(self) -> str | None:
        return self.dense.reason

    # -- search ------------------------------------------------------------ #

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        filters: Filters | None = None,
        candidate_k: int = 20,
    ) -> dict[str, Any]:
        """Run a hybrid search.

        Returns the hits plus the per-stage timing breakdown and a flag
        saying whether dense retrieval actually ran.
        """
        self._ensure_dense()
        filters = filters or Filters()
        stages: list[dict[str, Any]] = []

        started = time.perf_counter()
        lexical = self.bm25.search(query, top_k=max(candidate_k, top_k))
        lexical_ms = (time.perf_counter() - started) * 1000
        stages.append(
            {
                "name": "bm25",
                "status": "success" if lexical else "empty",
                "latency_ms": round(lexical_ms, 3),
                "details": {"hits": len(lexical)},
            }
        )

        dense: list[tuple[Document, float]] = []
        dense_ms = 0.0
        if self.dense.available:
            started = time.perf_counter()
            dense = self.dense.search(query, top_k=max(candidate_k, top_k))
            dense_ms = (time.perf_counter() - started) * 1000
        stages.append(
            {
                "name": "dense",
                "status": "success" if dense else ("skipped" if not self.dense.available else "empty"),
                "latency_ms": round(dense_ms, 3),
                "details": {
                    "hits": len(dense),
                    "enabled": self.dense.available,
                    "reason": self.dense.reason,
                },
            }
        )

        lexical_docs = [doc for doc, _ in lexical]
        dense_docs = [doc for doc, _ in dense]
        fused = reciprocal_rank_fusion([r for r in (lexical_docs, dense_docs) if r])

        lexical_scores = {doc.doc_id: s for doc, s in lexical}
        dense_scores = {doc.doc_id: s for doc, s in dense}
        lexical_ranks = {doc.doc_id: i for i, (doc, _) in enumerate(lexical, start=1)}
        dense_ranks = {doc.doc_id: i for i, (doc, _) in enumerate(dense, start=1)}

        hits: list[SearchHit] = []
        for doc, score in fused:
            if not filters.allows(doc):
                continue
            hits.append(
                SearchHit(
                    doc=doc,
                    score=score,
                    rank=len(hits) + 1,
                    lexical_rank=lexical_ranks.get(doc.doc_id),
                    dense_rank=dense_ranks.get(doc.doc_id),
                    lexical_score=lexical_scores.get(doc.doc_id),
                    dense_score=dense_scores.get(doc.doc_id),
                )
            )
            if len(hits) >= top_k:
                break

        stages.append(
            {
                "name": "fusion",
                "status": "success",
                "latency_ms": 0.0,
                "details": {"rrf_k": RRF_K, "fused_candidates": len(fused), "returned": len(hits)},
            }
        )

        return {
            "query": query,
            "hits": hits,
            "dense_enabled": self.dense.available,
            "dense_reason": self.dense.reason,
            "stages": stages,
            "total_latency_ms": round(sum(s["latency_ms"] for s in stages), 3),
            "filters_applied": {
                "dest_country": filters.dest_country,
                "category": filters.category,
                "min_margin": filters.min_margin,
                "max_lead_time_days": filters.max_lead_time_days,
                "doc_types": list(filters.doc_types) if filters.doc_types else None,
            },
        }


def build_retriever(
    documents: Sequence[Document], *, use_dense: bool = True
) -> HybridRetriever:
    """Convenience constructor used by the API and the demo script."""
    return HybridRetriever(documents, use_dense=use_dense)
