"""
history_search.py — semantic search over the agent's own iteration history.

The agent's tool-use schema now has a 4th tool: `query_history(question)`.
When the agent calls it, we:

  1. Embed the question with a sentence-transformer model.
  2. Compare against the pre-computed embeddings of every past
     iteration's summary.
  3. Return the top-5 most similar summaries.

This is **agentic RAG over its own log** — the agent can ask
"what worked in Finance before?" and get a real answer from
its prior experience, not just a rule.

Production swap:
  Use Mosaic AI Vector Search (managed) instead of the local
  sentence-transformer + numpy index. The CLI is the same:
  query the index, get top-k. We keep the local index for
  the smoke test and for environments where Vector Search
  isn't yet provisioned.

Schema:
  history_index/
    embeddings.npy  (N x 384 float32)
    meta.jsonl      (one row per iteration: {iter_no, listing_id,
                                              category, summary,
                                              quality_score, ...})

Update flow:
  - After every iteration, the driver calls `add_iteration(...)`
    to append the new summary's embedding to the index.
  - On driver boot, `load_index()` reads both files.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class HistoryHit:
    """One result of a query_history() call."""
    iter_no: int
    listing_id: str
    category: str
    summary: str
    quality_score: float
    similarity: float

    def to_dict(self) -> dict:
        return {
            "iter_no": self.iter_no,
            "listing_id": self.listing_id,
            "category": self.category,
            "summary": self.summary,
            "quality_score": self.quality_score,
            "similarity": round(self.similarity, 3),
        }


# ============================================================
# Embedding model — lazy + cached
# ============================================================

_EMBED_MODEL = None
_EMBED_DIM = 384  # all-MiniLM-L6-v2 output dim


def _get_model():
    """Lazy-load the sentence-transformer. Falls back to a hash-based
    pseudo-embedding if the library is missing (so the smoke test
    doesn't need it).
    """
    global _EMBED_MODEL
    if _EMBED_MODEL is not None:
        return _EMBED_MODEL
    try:
        from sentence_transformers import SentenceTransformer
        _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        return _EMBED_MODEL
    except ImportError:
        logger.warning("sentence-transformers not installed; using hash pseudo-embeddings")
        return None


def _embed(text: str) -> np.ndarray:
    """Embed a string. Falls back to a deterministic hash pseudo-embedding
    if sentence-transformers is missing — these are 384-dim, L2-normalized,
    and stable across calls, so the smoke test still works.
    """
    model = _get_model()
    if model is not None:
        return np.asarray(model.encode([text])[0], dtype=np.float32)
    # Hash pseudo-embedding: 384 dims, each seeded by a different
    # hash bucket of the text. Stable, fast, not great quality.
    import hashlib
    out = np.zeros(_EMBED_DIM, dtype=np.float32)
    for i in range(_EMBED_DIM):
        h = hashlib.sha1(f"{i}:{text}".encode("utf-8")).digest()
        out[i] = (h[0] / 255.0) - 0.5
    norm = np.linalg.norm(out)
    if norm > 0:
        out /= norm
    return out


# ============================================================
# Index
# ============================================================

class HistoryIndex:
    """In-process vector index over iteration summaries.

    Persists to two files: `embeddings.npy` (N x 384 float32) and
    `meta.jsonl` (N JSON objects). On boot, `load()` rebuilds.
    """

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = Path(persist_dir or os.getenv("M100_HISTORY_DIR", ".m100_history"))
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings: np.ndarray = np.zeros((0, _EMBED_DIM), dtype=np.float32)
        self.meta: list[dict] = []

    @property
    def size(self) -> int:
        return len(self.meta)

    # ----- I/O --------------------------------------------------------

    def load(self) -> None:
        """Rebuild the index from disk. Silent if files don't exist."""
        emb_path = self.persist_dir / "embeddings.npy"
        meta_path = self.persist_dir / "meta.jsonl"
        if emb_path.exists():
            self.embeddings = np.load(emb_path)
        if meta_path.exists():
            self.meta = [json.loads(line) for line in meta_path.read_text().splitlines() if line]
        logger.info("history index: loaded %d entries from %s", self.size, self.persist_dir)

    def save(self) -> None:
        """Persist to disk. Idempotent."""
        emb_path = self.persist_dir / "embeddings.npy"
        meta_path = self.persist_dir / "meta.jsonl"
        np.save(emb_path, self.embeddings)
        with meta_path.open("w") as f:
            for row in self.meta:
                f.write(json.dumps(row) + "\n")

    # ----- mutators ---------------------------------------------------

    def add_iteration(
        self,
        *,
        iter_no: int,
        listing_id: str,
        category: str,
        summary: str,
        quality_score: float,
    ) -> None:
        """Append one iteration. Updates in-memory + persists."""
        emb = _embed(summary)
        if self.embeddings.size == 0:
            self.embeddings = emb.reshape(1, -1)
        else:
            self.embeddings = np.vstack([self.embeddings, emb])
        self.meta.append({
            "iter_no": iter_no,
            "listing_id": listing_id,
            "category": category,
            "summary": summary,
            "quality_score": quality_score,
        })
        self.save()  # write-through — a crash doesn't lose the index

    # ----- query ------------------------------------------------------

    def query(self, question: str, top_k: int = 5) -> list[HistoryHit]:
        """Return the top-k most similar past iterations.

        Uses cosine similarity (embeddings are L2-normalized, so
        the inner product is the cosine). For small N (<10k) this
        is a single matrix multiply — fast enough for the agent.
        """
        if self.size == 0:
            return []
        q = _embed(question)
        sims = self.embeddings @ q  # (N,)
        # argsort descending, take top_k
        top_idx = np.argsort(-sims)[:top_k]
        hits: list[HistoryHit] = []
        for i in top_idx:
            row = self.meta[int(i)]
            hits.append(HistoryHit(
                iter_no=int(row["iter_no"]),
                listing_id=row["listing_id"],
                category=row["category"],
                summary=row["summary"],
                quality_score=float(row["quality_score"]),
                similarity=float(sims[int(i)]),
            ))
        return hits

    def format_results(self, question: str, top_k: int = 5) -> str:
        """Format query results for the agent's tool-use response.

        We return plain text (not JSON) because the agent's FM API
        call gets a string back. The agent decides what to do with it.
        """
        hits = self.query(question, top_k=top_k)
        if not hits:
            return f"(no prior history found for question: {question!r})"
        lines = [f"Top {len(hits)} past iterations for: {question!r}"]
        for h in hits:
            lines.append(
                f"  - iter {h.iter_no} [{h.category} sim={h.similarity:.2f} "
                f"q={h.quality_score:.2f}]: {h.summary}"
            )
        return "\n".join(lines)
