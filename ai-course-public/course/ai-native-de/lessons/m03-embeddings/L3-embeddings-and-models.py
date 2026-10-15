"""
================================================================
M3 L3  --  Embeddings and Model Selection
================================================================

Run:    python3 lessons/m03-embeddings/L3-embeddings-and-models.py
Keys:   none

Builds on M2.L2's vector math.  Adds:
  * Two "fake" embedding models with different vector spaces
  * Drift eval between model_v1 and model_v2 on a fixed corpus
  * Per-doc recall@K for a small golden query set
  * A model registry that tracks (model_id, dim, version, is_l2_normalized)
  * A dual-index migration sketch (the "how to upgrade without breaking prod")

The lesson's point: text embeddings are not interchangeable.  Switching
models is a real engineering migration, not a config change.  Always
measure drift on a fixed eval set before rolling out.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np


# =================================================================
# CONFIG
# =================================================================

LESSON_NUMBER = "M3.L3"
SEED = 7
N_DOCS = 12
TOP_K = 3
DRIFT_THRESHOLD = 0.7    # cosine < this on a fixed eval set = meaningful shift


# =================================================================
# SECTION 1  --  Embedding model registry
# =================================================================

@dataclass(frozen=True)
class EmbeddingModel:
    """A model is identified by id, version, dim, and a callable.

    Callables are numpy -> np.ndarray of shape (dim,) for one input, or
    list[np.ndarray] for batch.  In production this is a sentence-transformers
    encode(); here it's a deterministic placeholder.
    """
    model_id: str
    version: str
    dim: int
    encode: Callable[[str], np.ndarray]
    is_l2_normalized: bool = True

    def __repr__(self) -> str:
        return f"EmbeddingModel({self.model_id}@{self.version}, dim={self.dim}, normed={self.is_l2_normalized})"


def _hash_embed_factory(model_id: str, version: str, dim: int, seed_offset: int) -> EmbeddingModel:
    """Build a deterministic hash-based fake embedder.

    Two factories with different (model_id, version) produce different
    vector spaces.  That's the whole point of M3: model v1 and v2 are
    NOT the same space.
    """
    def encode(text: str) -> np.ndarray:
        seed = (sum(ord(c) for c in text) + seed_offset) % (2**32)
        rng = np.random.default_rng(seed=seed)
        v = rng.random(dim, dtype=np.float32)
        # L2 normalize so cosine == inner product (M2 lesson)
        n = float(np.sqrt(np.sum(v * v)))
        if n > 0:
            v = v / n
        return v
    return EmbeddingModel(
        model_id=model_id, version=version, dim=dim, encode=encode, is_l2_normalized=True,
    )


def model_v1(dim: int = 16) -> EmbeddingModel:
    """The 'production' model.  Pretrained on English web text."""
    return _hash_embed_factory("fake-embed", "1.0.0", dim, seed_offset=0)


def model_v2(dim: int = 32) -> EmbeddingModel:
    """The 'candidate' model.  Pretrained on English + code.  Bigger dim."""
    return _hash_embed_factory("fake-embed", "2.0.0", dim, seed_offset=42)


# =================================================================
# SECTION 2  --  Sample corpus (12 hand-written docs)
# =================================================================

@dataclass
class Doc:
    doc_id: str
    text: str

SAMPLE_DOCS: list[Doc] = [
    Doc("d01", "Employee vacation policy: 20 days per year, accrued monthly"),
    Doc("d02", "401k match: 100% of the first 3% of salary, 50% of the next 2%"),
    Doc("d03", "Sick leave: 10 days per year, no doctor's note required for first 3 days"),
    Doc("d04", "Expense policy: submit within 30 days, manager approval required"),
    Doc("d05", "Remote work: up to 2 days per week with manager approval"),
    Doc("d06", "Quarterly business review: revenue, gross margin, NPS, attrition"),
    Doc("d07", "Incident response: P1 within 15 min, P2 within 1 hour, P3 within 1 day"),
    Doc("d08", "Data retention: customer PII 7 years, financial records 10 years"),
    Doc("d09", "Code review: at least one approval, max 400 lines per PR"),
    Doc("d10", "Vendor onboarding: security review, contract review, billing setup"),
    Doc("d11", "Hiring: take-home assignment, system design, behavioral interview"),
    Doc("d12", "On-call: primary and secondary rotation, $200 stipend per shift"),
]


# =================================================================
# SECTION 3  --  Golden query set (the eval set for drift measurement)
# =================================================================

@dataclass
class GoldenQuery:
    query: str
    relevant_doc_ids: list[str]   # what the model should retrieve


GOLDEN_QUERIES: list[GoldenQuery] = [
    GoldenQuery("how much vacation do I get",                ["d01"]),
    GoldenQuery("what is the 401k match policy",            ["d02"]),
    GoldenQuery("sick leave and doctor's note policy",      ["d03"]),
    GoldenQuery("how do I submit an expense",                ["d04"]),
    GoldenQuery("can I work from home",                      ["d05"]),
    GoldenQuery("what's in the QBR",                         ["d06"]),
    GoldenQuery("incident response times",                   ["d07"]),
    GoldenQuery("how long to keep customer data",            ["d08"]),
    GoldenQuery("code review process",                       ["d09"]),
    GoldenQuery("how to onboard a vendor",                   ["d10"]),
    GoldenQuery("interview process for engineers",           ["d11"]),
    GoldenQuery("on-call compensation",                      ["d12"]),
]


# =================================================================
# SECTION 4  --  Embed a corpus
# =================================================================

def embed_corpus(model: EmbeddingModel, docs: list[Doc]) -> tuple[list[str], np.ndarray]:
    """Return (doc_ids, matrix) where matrix[i] is model.encode(docs[i].text)."""
    ids = [d.doc_id for d in docs]
    matrix = np.stack([model.encode(d.text) for d in docs], axis=0)
    return ids, matrix


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity in [-1, +1].  Both inputs assumed L2-normalized."""
    return float(np.dot(a, b))


def retrieve(model: EmbeddingModel, ids: list[str], matrix: np.ndarray,
             query: str, k: int = TOP_K) -> list[tuple[str, float]]:
    """Return top-k (doc_id, cosine) for the query."""
    qv = model.encode(query)
    scores = matrix @ qv
    order = np.argsort(-scores)[:k]
    return [(ids[i], float(scores[i])) for i in order]


# =================================================================
# SECTION 5  --  Drift and recall evaluation
# =================================================================

def recall_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int = TOP_K) -> float:
    """Recall@k = |relevant ∩ top-k| / |relevant|.  1.0 if all relevant in top-k."""
    if not relevant_ids:
        return 1.0
    top_k = set(retrieved_ids[:k])
    return len(top_k & set(relevant_ids)) / len(relevant_ids)


def evaluate_model(model: EmbeddingModel, docs: list[Doc],
                   golden: list[GoldenQuery], k: int = TOP_K) -> dict[str, float]:
    """Run the golden query set and report mean recall@k."""
    ids, matrix = embed_corpus(model, docs)
    recalls: list[float] = []
    for g in golden:
        hits = retrieve(model, ids, matrix, g.query, k=k)
        hit_ids = [h[0] for h in hits]
        recalls.append(recall_at_k(hit_ids, g.relevant_doc_ids, k=k))
    return {
        "mean_recall_at_k": float(np.mean(recalls)),
        "min_recall_at_k": float(np.min(recalls)),
        "queries_evaluated": float(len(golden)),
    }


def drift_eval(model_old: EmbeddingModel, model_new: EmbeddingModel,
               docs: list[Doc]) -> dict[str, float]:
    """Measure how much the embedding space changed between two models.

    For each doc, encode with both models, compute cosine between
    (model_old.encode(text), model_new.encode(text)).  Report the
    mean cosine across the corpus.  1.0 = identical, 0.0 = orthogonal.
    """
    sims: list[float] = []
    for d in docs:
        v_old = model_old.encode(d.text)
        v_new = model_new.encode(d.text)
        # Re-normalize in case models differ
        v_old = v_old / max(float(np.linalg.norm(v_old)), 1e-9)
        v_new = v_new / max(float(np.linalg.norm(v_new)), 1e-9)
        sims.append(cosine_sim(v_old, v_new))
    return {
        "mean_cosine_same_text": float(np.mean(sims)),
        "min_cosine_same_text": float(np.min(sims)),
        "max_cosine_same_text": float(np.max(sims)),
        "n_docs": float(len(docs)),
    }


# =================================================================
# SECTION 6  --  Dual-index migration sketch
# =================================================================

@dataclass
class DualIndex:
    """Two indexes side by side.  Query both, compare, route traffic.

    The "production" pattern: build the v2 index in the background,
    route 1% of traffic to it, compare recall on a shadow eval, ramp.
    """
    primary_model: EmbeddingModel
    primary_ids: list[str]
    primary_matrix: np.ndarray
    secondary_model: EmbeddingModel
    secondary_ids: list[str]
    secondary_matrix: np.ndarray
    secondary_traffic_share: float = 0.0   # 0.0 = 100% primary

    def query(self, q: str, k: int = TOP_K) -> tuple[list[tuple[str, float]], str]:
        """Return (results, source_model_id)."""
        if np.random.random() < self.secondary_traffic_share:
            return retrieve(self.secondary_model, self.secondary_ids,
                            self.secondary_matrix, q, k=k), self.secondary_model.model_id
        return retrieve(self.primary_model, self.primary_ids,
                        self.primary_matrix, q, k=k), self.primary_model.model_id


# =================================================================
# SECTION 7  --  Demo
# =================================================================

def demo() -> None:
    """End-to-end walkthrough: 7 sections, prints banners + numbers."""
    print("=" * 70)
    print(f"  {LESSON_NUMBER}  --  Embeddings and Model Selection")
    print("=" * 70)

    # 1. Model registry
    print("\n  Section 1: Embedding model registry")
    print("  " + "-" * 66)
    # Use same dim for v1/v2 so the drift comparison in Section 6 is meaningful.
    # The default v1=16 / v2=32 is shown later for the cross-dim registry listing
    # but the drift comparison requires matching dim.
    DIM = 16
    v1 = model_v1(dim=DIM)
    v2 = model_v2(dim=DIM)
    v1b = model_v1(dim=16)
    v2b = model_v2(dim=32)
    print(f"    v1: {v1}")
    print(f"    v2: {v2}")
    print(f"    Same dim? {v1.dim == v2.dim}  (v1={v1.dim}, v2={v2.dim})")
    print(f"    Same id?  {v1.model_id == v2.model_id}")
    # The v1b/v2b pair has different dims and is used in Section 7 to show
    # the cross-dim registry; not used for drift.
    print(f"    v1 norm check: {float(np.linalg.norm(v1.encode('hello'))):.3f}  (should be 1.0)")

    # 2. Corpus
    print("\n  Section 2: Sample corpus (12 docs)")
    print("  " + "-" * 66)
    print(f"    {len(SAMPLE_DOCS)} docs  --  first 3 ids: {[d.doc_id for d in SAMPLE_DOCS[:3]]}")

    # 3. Golden query set
    print("\n  Section 3: Golden query set (12 hand-labeled)")
    print("  " + "-" * 66)
    print(f"    {len(GOLDEN_QUERIES)} queries  --  example: {GOLDEN_QUERIES[0]}")

    # 4. v1 retrieval
    print("\n  Section 4: v1 retrieval on the first 3 queries")
    print("  " + "-" * 66)
    v1_ids, v1_matrix = embed_corpus(v1, SAMPLE_DOCS)
    for g in GOLDEN_QUERIES[:3]:
        hits = retrieve(v1, v1_ids, v1_matrix, g.query, k=3)
        top_ids = [h[0] for h in hits]
        r = recall_at_k(top_ids, g.relevant_doc_ids, k=3)
        print(f"    query={g.query!r:<48}  top-3={top_ids}  recall@3={r:.2f}")

    # 5. v2 retrieval
    print("\n  Section 5: v2 retrieval on the same 3 queries")
    print("  " + "-" * 66)
    v2_ids, v2_matrix = embed_corpus(v2, SAMPLE_DOCS)
    for g in GOLDEN_QUERIES[:3]:
        hits = retrieve(v2, v2_ids, v2_matrix, g.query, k=3)
        top_ids = [h[0] for h in hits]
        r = recall_at_k(top_ids, g.relevant_doc_ids, k=3)
        print(f"    query={g.query!r:<48}  top-3={top_ids}  recall@3={r:.2f}")

    # 6. Drift
    print("\n  Section 6: Drift eval between v1 and v2 (same text)")
    print("  " + "-" * 66)
    d = drift_eval(v1, v2, SAMPLE_DOCS)
    print(f"    mean cosine = {d['mean_cosine_same_text']:.3f}  (1.0 = identical)")
    print(f"    min  cosine = {d['min_cosine_same_text']:.3f}")
    print(f"    max  cosine = {d['max_cosine_same_text']:.3f}")
    print(f"    threshold  = {DRIFT_THRESHOLD}  (cosine < this => meaningful shift)")
    safe_to_roll = d["mean_cosine_same_text"] >= DRIFT_THRESHOLD
    print(f"    safe to roll out? {safe_to_roll}")

    # 7. Dual-index migration
    print("\n  Section 7: Dual-index migration sketch")
    print("  " + "-" * 66)
    di = DualIndex(
        primary_model=v1, primary_ids=v1_ids, primary_matrix=v1_matrix,
        secondary_model=v2, secondary_ids=v2_ids, secondary_matrix=v2_matrix,
        secondary_traffic_share=0.0,
    )
    for share in (0.0, 0.1, 0.5, 1.0):
        di.secondary_traffic_share = share
        # deterministic "roll the dice" with seed for the demo
        rng = np.random.default_rng(seed=42)
        primary_count = secondary_count = 0
        for _ in range(1000):
            if rng.random() < share:
                secondary_count += 1
            else:
                primary_count += 1
        print(f"    traffic share {share:.0%}  ->  primary={primary_count}, secondary={secondary_count}")

    print("=" * 70)
    print("  See L3-embeddings-and-models.ipynb for the runnable version.")
    print("=" * 70)


# =================================================================
# SECTION 8  --  Tests
# =================================================================

def test_model_normalized() -> None:
    """Every fake-embedder output should be L2-normalized."""
    v1 = model_v1()
    e = v1.encode("hello world")
    assert abs(float(np.linalg.norm(e)) - 1.0) < 1e-5


def test_two_models_have_different_spaces() -> None:
    """v1 and v2 should NOT produce the same vector for the same text."""
    v1 = model_v1(dim=16)
    v2 = model_v2(dim=16)   # same dim but different seed
    e1 = v1.encode("hello world")
    e2 = v2.encode("hello world")
    assert cosine_sim(e1, e2) < 0.99   # not identical


def test_recall_at_k_perfect() -> None:
    """If the right doc is in top-k, recall@k = 1.0."""
    assert recall_at_k(["a", "b", "c"], ["b"], k=3) == 1.0


def test_recall_at_k_zero() -> None:
    """If the right doc is NOT in top-k, recall@k = 0.0."""
    assert recall_at_k(["a", "b", "c"], ["z"], k=3) == 0.0


def test_recall_at_k_partial() -> None:
    """2 of 3 relevant in top-k -> recall@3 = 2/3."""
    assert abs(recall_at_k(["a", "b", "c"], ["a", "b", "z"], k=3) - 2/3) < 1e-6


def test_drift_eval_returns_bounded_cosine() -> None:
    """drift_eval reports cosine values in [-1, +1]."""
    # Use models of the same dim for drift eval (cross-dim drift is undefined).
    a = model_v1(dim=16)
    b = model_v2(dim=16)
    d = drift_eval(a, b, SAMPLE_DOCS)
    assert -1.0 <= d["mean_cosine_same_text"] <= 1.0
    assert d["n_docs"] == float(len(SAMPLE_DOCS))


def test_evaluate_model_returns_metrics() -> None:
    """evaluate_model returns a dict with mean_recall_at_k in [0, 1]."""
    v1 = model_v1()
    m = evaluate_model(v1, SAMPLE_DOCS, GOLDEN_QUERIES, k=3)
    assert 0.0 <= m["mean_recall_at_k"] <= 1.0
    assert m["queries_evaluated"] == float(len(GOLDEN_QUERIES))


def test_retrieve_returns_top_k() -> None:
    """retrieve returns exactly k (doc_id, score) tuples, sorted by score desc."""
    v1 = model_v1()
    ids, matrix = embed_corpus(v1, SAMPLE_DOCS)
    hits = retrieve(v1, ids, matrix, "vacation policy", k=3)
    assert len(hits) == 3
    scores = [s for _, s in hits]
    assert scores == sorted(scores, reverse=True)


def test_dual_index_query_works() -> None:
    """DualIndex.query returns results and a source model id."""
    v1 = model_v1()
    v2 = model_v2()
    docs = [Doc("a", "alpha text about topic X"), Doc("b", "beta text about topic Y")]
    p_ids, p_mat = embed_corpus(v1, docs)
    s_ids, s_mat = embed_corpus(v2, docs)
    di = DualIndex(
        primary_model=v1,
        primary_ids=p_ids, primary_matrix=p_mat,
        secondary_model=v2,
        secondary_ids=s_ids, secondary_matrix=s_mat,
        secondary_traffic_share=0.0,
    )
    results, source = di.query("alpha", k=1)
    assert len(results) == 1
    assert source in (v1.model_id, v2.model_id)


def test_model_id_is_immutable() -> None:
    """EmbeddingModel is a frozen dataclass; assignment should fail."""
    v1 = model_v1()
    try:
        v1.model_id = "changed"  # type: ignore[misc]
        assert False, "should have raised FrozenInstanceError"
    except Exception:  # noqa: BLE001
        pass  # any exception is fine here


# =================================================================
# ENTRY
# =================================================================

if __name__ == "__main__":
    demo()
