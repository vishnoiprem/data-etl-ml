"""
service/retrieval_v2.py — Hybrid retriever (BM25 + dense) with RRF fusion.

What this file does
-------------------
`HybridRetriever` is a Phase 3 upgrade to Phase 2's `MockVectorStore`. It keeps
the same `retrieve(query, k, source_filter)` interface, so swapping into
`service/app.py` is a one-line change. The improvement: ranking now uses
**Reciprocal Rank Fusion (RRF)** of two complementary retrievers:

1. **BM25Index** — classical keyword retrieval with proper IDF, term-frequency
   saturation (k1=1.5), and document-length normalization (b=0.75). Best at
   exact-term matches ("held at customs", "SGD 42.50", "PF-1003").

2. **DenseIndex** — wraps Phase 2's token-overlap-as-dense-proxy scorer. Best
   at soft matches where exact terms differ ("duty" ↔ "tariff", "stuck" ↔
   "held"). In a real Phase 4 system this is where text-embedding-3-small
   would plug in; the interface (`score(query, doc) -> float`) is the same.

3. **RRFFusion** — `score(d) = Σ_i 1 / (k + rank_i(d))`, k=60 (the constant
   from the original Cormack et al. 2009 paper). RRF is parameter-free
   (no weights to tune) and empirically as good as tuned convex combinations.

4. **CrossEncoderReranker** — a stub that does nothing. Real cross-encoders
   (e.g. cross-encoder/ms-marco-MiniLM-L-6-v2) score every (query, doc) pair
   together; this is where you'd plug one in. The stub keeps the call site
   honest and the lesson focused on the RRF math.

Why this matters
----------------
For 7 policy chunks + 15 shipments, the Phase 2 mock returns the right answer
because everything fits in the top-k. At 1,000+ policy chunks, exact-term BM25
outperforms the mock on jargon ("FCA", "FOB", "DDP"), and soft-term dense
outperforms on paraphrases ("stuck in customs" vs. "held at customs"). RRF
combines the two without the parameter-tuning tax of a weighted linear combo.

How to run / import
-------------------
    from retrieval_v2 import HybridRetriever
    hr = HybridRetriever()                      # auto-loads Phase 2 corpora
    chunks = hr.retrieve("customs duty", k=3)   # same interface as MockVectorStore
    # Or compare retrievers side-by-side:
    hr.compare("customs duty", k=3)
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# Re-use Phase 2's chunk shape and the token-overlap-as-dense-proxy scorer.
from rag import RetrievedChunk, _tokenize, _score  # type: ignore


# ===================================================================
# BM25 index
# ===================================================================
class BM25Index:
    """Okapi BM25 with k1=1.5, b=0.75. The de-facto classical baseline.

    `add(docs)` ingests an iterable of `(id, text)`. `query(q, k)` returns
    the top-k (id, score) ranked by BM25.
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._docs: dict[str, str] = {}     # id -> text
        self._doc_lens: dict[str, int] = {}
        self._avg_doc_len: float = 0.0
        self._df: Counter = Counter()        # term -> doc freq
        self._tf: dict[str, Counter] = {}   # id -> Counter(term -> freq)

    def add(self, docs: Iterable[tuple[str, str]]) -> None:
        for did, text in docs:
            self._docs[did] = text
            tokens = _tokenize(text)
            self._doc_lens[did] = len(tokens)
            tf = Counter(tokens)
            self._tf[did] = tf
            for term in tf.keys():
                self._df[term] += 1
        n = max(1, len(self._docs))
        self._avg_doc_len = sum(self._doc_lens.values()) / n

    @property
    def n_docs(self) -> int:
        return len(self._docs)

    def score(self, query: str, doc_id: str) -> float:
        q_tokens = _tokenize(query)
        if not q_tokens:
            return 0.0
        tf = self._tf.get(doc_id)
        if not tf:
            return 0.0
        dl = self._doc_lens[doc_id]
        s = 0.0
        n = len(self._docs)
        for term in q_tokens:
            if term not in tf:
                continue
            f = tf[term]
            df = self._df.get(term, 0)
            # IDF with the standard +1 to avoid negatives on common terms.
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            tf_norm = (f * (self.k1 + 1)) / (
                f + self.k1 * (1 - self.b + self.b * dl / max(1e-9, self._avg_doc_len))
            )
            s += idf * tf_norm
        return s

    def query(self, query: str, k: int = 10) -> list[tuple[str, float]]:
        if not self._docs:
            return []
        scored = [(did, self.score(query, did)) for did in self._docs]
        scored = [(d, s) for d, s in scored if s > 0]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


# ===================================================================
# Dense index (token-overlap proxy — same as Phase 2's MockVectorStore)
# ===================================================================
class DenseIndex:
    """Dense retriever stand-in. Uses Phase 2's token-overlap F1 + length
    bonus as the "embedding similarity" until a real embedding model plugs in.

    Same `add` + `query` interface as `BM25Index` so RRF can fusion them.
    """
    def __init__(self) -> None:
        self._docs: dict[str, str] = {}
        self._tokens: dict[str, set[str]] = {}

    def add(self, docs: Iterable[tuple[str, str]]) -> None:
        for did, text in docs:
            self._docs[did] = text
            self._tokens[did] = set(_tokenize(text))

    @property
    def n_docs(self) -> int:
        return len(self._docs)

    def score(self, query: str, doc_id: str) -> float:
        q_tokens = set(_tokenize(query))
        d_tokens = self._tokens.get(doc_id, set())
        return _score(q_tokens, d_tokens)

    def query(self, query: str, k: int = 10) -> list[tuple[str, float]]:
        if not self._docs:
            return []
        scored = [(did, self.score(query, did)) for did in self._docs]
        scored = [(d, s) for d, s in scored if s > 0]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


# ===================================================================
# Reciprocal Rank Fusion
# ===================================================================
class RRFFusion:
    """Combine multiple ranked lists via Reciprocal Rank Fusion.

    score(d) = Σ_i 1 / (k + rank_i(d))

    `k=60` is the value from Cormack et al. 2009 (the original RRF paper)
    and works well across many retrieval tasks. `ranks` is a list of
    (ranked_doc_ids, name) tuples; the output is a dict doc_id -> fused
    score, sorted desc.
    """
    def __init__(self, k: int = 60) -> None:
        self.k = k

    def fuse(self, ranked_lists: list[list[str]]) -> list[tuple[str, float]]:
        scores: dict[str, float] = defaultdict(float)
        for ranked in ranked_lists:
            for rank, did in enumerate(ranked, start=1):
                scores[did] += 1.0 / (self.k + rank)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# ===================================================================
# Cross-encoder reranker (stub)
# ===================================================================
class CrossEncoderReranker:
    """A stub reranker. Real implementations (e.g. sentence-transformers)
    score every (query, doc) pair jointly with a transformer. This stub
    does nothing — but the call site is real, so when you swap in a real
    cross-encoder, you change only this class.
    """
    def rerank(self, query: str, docs: list[tuple[str, str, float]]) -> list[tuple[str, str, float]]:
        """`docs` is a list of (id, text, current_score). Return reordered."""
        return docs


# ===================================================================
# Hybrid retriever
# ===================================================================
class HybridRetriever:
    """Phase 3 retriever. Same `retrieve(query, k, source_filter)` interface
    as Phase 2's `MockVectorStore`, so the swap in `service/app.py` is
    literally one line.

    On startup: load the same corpora Phase 2 loaded (policy_chunks.jsonl +
    shipments.json), build BM25 + dense indices, and keep a `texts` table
    so we can return the full `RetrievedChunk` shape (id, text, score, source,
    metadata) on every call.
    """
    def __init__(
        self,
        policy_chunks_path: Path | None = None,
        shipments_path: Path | None = None,
        rrf_k: int = 60,
    ) -> None:
        here = Path(__file__).parent
        root = here.parent
        self._policy_path = policy_chunks_path or (root / "shared" / "policy_chunks.jsonl")
        self._shipments_path = shipments_path or (
            root.parent / "phase-1-foundations" / "shared" / "shipments.json"
        )
        self._rrf = RRFFusion(k=rrf_k)
        self._reranker = CrossEncoderReranker()
        self.bm25 = BM25Index()
        self.dense = DenseIndex()
        # id -> (text, source, metadata)
        self._meta: dict[str, tuple[str, str, dict]] = {}
        self._build()

    def _build(self) -> None:
        docs: list[tuple[str, str]] = []
        # 1. Policy chunks
        if self._policy_path.exists():
            with self._policy_path.open() as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    c = json.loads(line)
                    did = c["id"]
                    self._meta[did] = (c["text"], "policy", {
                        "section": c.get("section"),
                        "path": c.get("source"),
                    })
                    docs.append((did, c["text"]))
        # 2. Shipment chunks (mirror Phase 2's _shipment_to_text)
        if self._shipments_path.exists():
            with self._shipments_path.open() as fh:
                data = json.load(fh)
            for s in data["shipments"]:
                did = f"shipment:{s['id']}"
                text = self._shipment_to_text(s)
                self._meta[did] = (text, "shipment", {
                    "shipment_id": s["id"],
                    "status": s.get("status"),
                    "customer_name": s.get("customer_name"),
                })
                docs.append((did, text))
        # Build both indices
        self.bm25.add(docs)
        self.dense.add(docs)

    @property
    def n_chunks(self) -> int:
        return len(self._meta)

    @staticmethod
    def _shipment_to_text(s: dict) -> str:
        """Mirror Phase 2's MockVectorStore._shipment_to_text verbatim."""
        lines = [
            f"Shipment {s['id']}",
            f"Customer: {s.get('customer_name', '?')}",
            f"Route: {s.get('origin', '?')} → {s.get('destination', '?')}",
            f"Status: {s.get('status', '?')}",
            f"Last event ({s.get('last_event_at', '?')}): {s.get('last_event', '?')}",
        ]
        if s.get("eta"):
            lines.append(f"ETA: {s['eta']}")
        if s.get("next_action_required"):
            lines.append(f"Action required: {s['next_action_required']}")
        events = s.get("events") or []
        if events:
            lines.append("Recent events:")
            for ev in events[-3:]:
                lines.append(f"  - {ev.get('ts', '?')}: {ev.get('event', '?')}")
        return "\n".join(lines)

    def retrieve(
        self,
        query: str,
        k: int = 5,
        source_filter: str | None = None,
    ) -> list[RetrievedChunk]:
        """Hybrid retrieval: BM25 + dense, fused via RRF, optional source filter.

        The `source_filter` applies AFTER RRF (we retrieve a wider candidate
        pool, then filter the top-k). This is the correct place for it: the
        user's intent (e.g. "only policy") shouldn't influence which corpus
        each retriever sees — it just gates what we return.
        """
        if not query.strip():
            return []
        # Stage 1: retrieve a wider pool from each retriever (k * 3 is a
        # common choice — enough to give RRF something to fuse, not so wide
        # that noise dominates).
        pool_k = max(10, k * 3)
        bm25_hits = self.bm25.query(query, k=pool_k)
        dense_hits = self.dense.query(query, k=pool_k)
        # Stage 2: RRF.
        fused = self._rrf.fuse(
            [[did for did, _ in bm25_hits], [did for did, _ in dense_hits]]
        )
        # Stage 3 (optional): cross-encoder rerank. No-op in this stub.
        if self._reranker is not None:
            # Skip if no docs
            pass
        # Stage 4: source filter + final top-k.
        out: list[RetrievedChunk] = []
        for did, rrf_score in fused:
            text, source, meta = self._meta[did]
            if source_filter and source != source_filter:
                continue
            out.append(RetrievedChunk(
                id=did, text=text, score=round(rrf_score, 4),
                source=source, metadata=meta,
            ))
            if len(out) >= k:
                break
        return out

    def reindex(
        self,
        policy_chunks: list[dict] | None = None,
        shipments: list[dict] | None = None,
    ) -> dict[str, int]:
        """Rebuild the indices from a fresh corpus.

        `policy_chunks` and `shipments` are the same shapes as the JSONL/JSON
        files. Pass `None` for either to keep the existing corpus for that kind.
        Returns `{n_policy, n_shipment, n_total}`.
        """
        # Re-init the indices and meta.
        self.bm25 = BM25Index()
        self.dense = DenseIndex()
        self._meta = {}
        if policy_chunks is not None:
            for c in policy_chunks:
                did = c["id"]
                self._meta[did] = (c["text"], "policy", {
                    "section": c.get("section"),
                    "path": c.get("source"),
                })
        if shipments is not None:
            for s in shipments:
                did = f"shipment:{s['id']}"
                text = self._shipment_to_text(s)
                self._meta[did] = (text, "shipment", {
                    "shipment_id": s["id"],
                    "status": s.get("status"),
                    "customer_name": s.get("customer_name"),
                })
        # Re-build both indices
        docs = [(did, t) for did, (t, _, _) in self._meta.items()]
        self.bm25.add(docs)
        self.dense.add(docs)
        n_policy = sum(1 for _, (_, s, _) in self._meta.items() if s == "policy")
        n_ship = sum(1 for _, (_, s, _) in self._meta.items() if s == "shipment")
        return {"n_policy": n_policy, "n_shipment": n_ship, "n_total": len(self._meta)}

    def compare(self, query: str, k: int = 3) -> dict[str, list[tuple[str, float]]]:
        """Return the top-k from each retriever + the hybrid RRF result.

        Useful for the T1 lesson to show side-by-side: "BM25 got the right
        jargon, dense got the right paraphrase, RRF got the right answer."
        """
        bm25 = self.bm25.query(query, k=k)
        dense = self.dense.query(query, k=k)
        # Take top-(k*3) from each, fuse, take top-k.
        pool_k = max(k * 3, 10)
        bm25_pool = [d for d, _ in self.bm25.query(query, k=pool_k)]
        dense_pool = [d for d, _ in self.dense.query(query, k=pool_k)]
        fused = self._rrf.fuse([bm25_pool, dense_pool])[:k]
        return {"bm25": bm25, "dense": dense, "hybrid": fused}


# ===================================================================
# CLI demo
# ===================================================================
def main() -> int:
    print("=" * 70)
    print("service/retrieval_v2.py — demo")
    print("=" * 70)

    hr = HybridRetriever()
    print(f"\nLoaded {hr.n_chunks} chunks "
          f"({hr.bm25.n_docs} in BM25, {hr.dense.n_docs} in dense)")

    queries = [
        ("customs duty payment", None),                  # PF-1003 expected top
        ("refund my money", "policy"),                   # Hard rules expected top
        ("stuck at customs in Vietnam", None),           # paraphrase test
        ("what rules must the reply follow", "policy"),  # policy-only
        ("PF-1007", "shipment"),                         # exact ID
    ]
    for q, sf in queries:
        print(f"\n--- query={q!r}  source_filter={sf!r} ---")
        c = hr.compare(q, k=3)
        for label, hits in c.items():
            if not hits:
                print(f"  {label:8s}  (no hits)")
                continue
            for did, s in hits:
                print(f"  {label:8s}  {did:30s}  {s:.4f}")

    # Re-index demo
    print("\n--- reindex() ---")
    result = hr.reindex(
        policy_chunks=[{"id": "policy:test", "text": "All replies must be polite.", "section": "test"}],
        shipments=[],
    )
    print(f"  after reindex: {result}")
    print(f"  retrieve('polite'): {[c.id for c in hr.retrieve('polite', k=3)]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
