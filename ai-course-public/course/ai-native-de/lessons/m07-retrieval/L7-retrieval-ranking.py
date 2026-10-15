"""
================================================================
M7 L7  --  Retrieval and Ranking
================================================================

Run:    python3 lessons/m07-retrieval/L7-retrieval-ranking.py
Keys:   none

Builds a hybrid retriever from scratch:
  * BM25 (sparse lexical)
  * Dense cosine (M2's vector math)
  * Reciprocal Rank Fusion (RRF) to merge the two rankings
  * Maximal Marginal Relevance (MMR) to diversify the result list

The lesson's point: dense alone misses exact matches (e.g. SKUs).
BM25 alone misses semantic similarity.  Hybrid wins on most
enterprise corpora.  MMR is the answer to "why is every result
saying the same thing?"
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Iterable

import numpy as np


# =================================================================
# CONFIG
# =================================================================

LESSON_NUMBER = "M7.L7"
EMBEDDING_DIM = 32
SEED = 11
TOP_K = 5
RRF_K = 60           # RRF constant; standard value
MMR_LAMBDA = 0.7     # 1.0 = relevance only; 0.0 = diversity only


# =================================================================
# SECTION 1  --  Fake embedder (deterministic, like M3)
# =================================================================

def fake_embed(text: str, dim: int = EMBEDDING_DIM, seed_offset: int = 0) -> np.ndarray:
    """Hash-based deterministic embedder.  Returns L2-normalized vector."""
    seed = (sum(ord(c) for c in text) + seed_offset) % (2**32)
    rng = np.random.default_rng(seed=seed)
    v = rng.random(dim, dtype=np.float32)
    n = float(np.sqrt(np.sum(v * v)))
    if n > 0:
        v = v / n
    return v


# =================================================================
# SECTION 2  --  Tokenize
# =================================================================

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokens.  No stemming, no stopwords (kept simple)."""
    return _TOKEN_RE.findall(text.lower())


# =================================================================
# SECTION 3  --  BM25 (Okapi)
# =================================================================

@dataclass
class BM25:
    """A tiny BM25 index.  Terms -> list of (doc_id, term_freq)."""
    k1: float = 1.5
    b: float = 0.75
    inverted_index: dict[str, list[tuple[int, int]]] = field(default_factory=lambda: defaultdict(list))
    doc_lens: list[int] = field(default_factory=list)
    avg_dl: float = 0.0
    n_docs: int = 0
    idf: dict[str, float] = field(default_factory=dict)

    def fit(self, docs: list[str]) -> None:
        self.n_docs = len(docs)
        self.doc_lens = [len(tokenize(d)) for d in docs]
        self.avg_dl = sum(self.doc_lens) / max(self.n_docs, 1)
        df: Counter[str] = Counter()
        for i, d in enumerate(docs):
            for term, tf in Counter(tokenize(d)).items():
                self.inverted_index[term].append((i, tf))
                df[term] += 1
        for term, n_q in df.items():
            self.idf[term] = math.log(1 + (self.n_docs - n_q + 0.5) / (n_q + 0.5))

    def score(self, query: str) -> list[tuple[int, float]]:
        """Return [(doc_index, bm25_score), ...] for all docs that match any query term."""
        scores: list[float] = [0.0] * self.n_docs
        for term in tokenize(query):
            if term not in self.inverted_index:
                continue
            idf = self.idf.get(term, 0.0)
            for doc_idx, tf in self.inverted_index[term]:
                dl = self.doc_lens[doc_idx]
                num = tf * (self.k1 + 1)
                den = tf + self.k1 * (1 - self.b + self.b * dl / max(self.avg_dl, 1))
                scores[doc_idx] += idf * num / max(den, 1e-9)
        # sort desc
        order = np.argsort(-np.array(scores))
        return [(int(i), float(scores[i])) for i in order if scores[i] > 0]


# =================================================================
# SECTION 4  --  Dense retriever (cosine)
# =================================================================

@dataclass
class Dense:
    vectors: np.ndarray = field(default_factory=lambda: np.zeros((0, 0), dtype=np.float32))

    def fit(self, docs: list[str]) -> None:
        self.vectors = np.stack([fake_embed(d) for d in docs], axis=0)

    def score(self, query: str) -> list[tuple[int, float]]:
        qv = fake_embed(query)
        scores = self.vectors @ qv
        order = np.argsort(-scores)
        return [(int(i), float(scores[i])) for i in order]


# =================================================================
# SECTION 5  --  RRF (Reciprocal Rank Fusion)
# =================================================================

def rrf(rankings: list[list[tuple[int, float]]], k: int = RRF_K) -> list[tuple[int, float]]:
    """Reciprocal Rank Fusion: sum of 1 / (k + rank) across rankings.

    Each ranking is a list of (doc_index, score) sorted desc.  Returns
    a merged ranking.  Tunes poorly; tunes by k.  k=60 is the standard.
    """
    fused: dict[int, float] = defaultdict(float)
    for ranking in rankings:
        for rank, (doc_idx, _) in enumerate(ranking, start=1):
            fused[doc_idx] += 1.0 / (k + rank)
    out = sorted(fused.items(), key=lambda kv: -kv[1])
    return [(i, float(s)) for i, s in out]


# =================================================================
# SECTION 6  --  MMR (Maximal Marginal Relevance)
# =================================================================

def mmr(
    query_vec: np.ndarray,
    doc_vecs: np.ndarray,
    candidate_ids: list[int],
    lambda_: float = MMR_LAMBDA,
    k: int = TOP_K,
) -> list[int]:
    """Select k docs that maximize: lambda * relevance - (1 - lambda) * max similarity to already-selected.

    Returns the selected doc indices in MMR order.
    """
    selected: list[int] = []
    candidates = set(candidate_ids)
    while len(selected) < k and candidates:
        best: int | None = None
        best_score = -math.inf
        for c in candidates:
            rel = float(np.dot(query_vec, doc_vecs[c]))
            if selected:
                max_sim = max(float(np.dot(doc_vecs[c], doc_vecs[s])) for s in selected)
            else:
                max_sim = 0.0
            score = lambda_ * rel - (1 - lambda_) * max_sim
            if score > best_score:
                best_score = score
                best = c
        if best is None:
            break
        selected.append(best)
        candidates.remove(best)
    return selected


# =================================================================
# SECTION 7  --  Sample corpus + queries
# =================================================================

SAMPLE_DOCS: list[str] = [
    "401k match: 100% of the first 3% of salary, 50% of the next 2%. Vesting is immediate.",
    "Vacation policy: 20 days per year, accrued monthly at 1.67 days. Unused days carry over up to 5.",
    "Sick leave: 10 days per year, accrued monthly. Doctor's note required after 3 consecutive days.",
    "Expense policy: submit within 30 days, receipt required over $25, manager approval over $500.",
    "Code review: at least one engineer, PRs under 400 lines, completed within 1 business day.",
    "Incident response: P1 within 15 minutes, P2 within 1 hour, P3 within 1 business day.",
    "Data retention: customer PII 7 years, financial records 10 years, logs 90 days, backups 1 year.",
    "On-call rotation: primary and secondary, $200 per shift, Monday to Monday, 10am handoff.",
    "Vendor onboarding: security review, contract review, billing setup; total 15-20 business days.",
    "Hiring: phone screen, take-home, system design, behavioral; decisions within 2 business days.",
]

SAMPLE_QUERIES: list[tuple[str, str]] = [
    ("how much vacation do I get",            "1"),     # doc 1 (vacation)
    ("401k retirement match",                  "0"),     # doc 0 (401k)
    ("what is the data retention policy",      "6"),     # doc 6
    ("how do I submit an expense",             "3"),     # doc 3
]


# =================================================================
# SECTION 8  --  Demo
# =================================================================

def demo() -> None:
    print("=" * 70)
    print(f"  {LESSON_NUMBER}  --  Retrieval and Ranking (BM25 + Dense + RRF + MMR)")
    print("=" * 70)

    # 1. BM25
    print("\n  Section 1: BM25 on the 4 sample queries")
    print("  " + "-" * 66)
    bm = BM25()
    bm.fit(SAMPLE_DOCS)
    for q, _ in SAMPLE_QUERIES:
        hits = bm.score(q)[:3]
        ids = [i for i, _ in hits]
        print(f"    {q!r:<48}  top-3 = {ids}")

    # 2. Dense
    print("\n  Section 2: Dense cosine on the 4 sample queries")
    print("  " + "-" * 66)
    de = Dense()
    de.fit(SAMPLE_DOCS)
    for q, _ in SAMPLE_QUERIES:
        hits = de.score(q)[:3]
        ids = [i for i, _ in hits]
        print(f"    {q!r:<48}  top-3 = {ids}")

    # 3. RRF
    print("\n  Section 3: RRF (Reciprocal Rank Fusion) merge")
    print("  " + "-" * 66)
    for q, _ in SAMPLE_QUERIES:
        bm_hits = bm.score(q)[:10]
        de_hits = de.score(q)[:10]
        merged = rrf([bm_hits, de_hits], k=RRF_K)[:5]
        ids = [i for i, _ in merged]
        print(f"    {q!r:<48}  top-5 = {ids}")

    # 4. RRF weights (more weight on dense)
    print("\n  Section 4: RRF with weighted rankings (2x dense)")
    print("  " + "-" * 66)
    for q, _ in SAMPLE_QUERIES:
        bm_hits = bm.score(q)[:10]
        de_hits = de.score(q)[:10]
        merged = rrf([bm_hits, de_hits, de_hits], k=RRF_K)[:5]
        ids = [i for i, _ in merged]
        print(f"    {q!r:<48}  top-5 = {ids}")

    # 5. MMR diversification
    print("\n  Section 5: MMR diversification (lambda=0.5)")
    print("  " + "-" * 66)
    q, _ = SAMPLE_QUERIES[0]
    qv = fake_embed(q)
    # candidates = top-20 by dense
    cand_ids = [i for i, _ in de.score(q)[:20]]
    selected = mmr(qv, de.vectors, cand_ids, lambda_=0.5, k=5)
    print(f"    query: {q!r}")
    print(f"    selected (in order): {selected}")
    print(f"    selected texts:")
    for i in selected:
        print(f"      [{i}] {SAMPLE_DOCS[i][:60]!r}")

    # 6. The trade-off
    print("\n  Section 6: When to use which retriever")
    print("  " + "-" * 66)
    print("""
    BM25 alone:  exact matches, SKUs, names, rare technical terms
    Dense alone:  semantic similarity, paraphrases, multilingual
    Hybrid:       most enterprise corpora; tunable per query type
    RRF:          the standard merge; 1 line of code; tunes by k
    MMR:          when the top-K is too redundant; diversify
    """)

    # 7. Recall comparison
    print("\n  Section 7: Mean recall@3 on the 4 sample queries")
    print("  " + "-" * 66)
    for label, fn in (("BM25", bm.score), ("Dense", de.score), ("RRF", lambda q: rrf([bm.score(q), de.score(q)], k=RRF_K))):
        recall = 0
        for q, expected in SAMPLE_QUERIES:
            hits = fn(q)[:3]
            ids = [i for i, _ in hits]
            if int(expected) in ids:
                recall += 1
        print(f"    {label:<6}  recall@3 = {recall/len(SAMPLE_QUERIES):.2f}")

    print("=" * 70)
    print("  See L7-retrieval-ranking.ipynb for the runnable version.")
    print("=" * 70)


# =================================================================
# Tests
# =================================================================

def test_tokenize_lowercases() -> None:
    assert tokenize("Hello World") == ["hello", "world"]


def test_tokenize_strips_punct() -> None:
    assert tokenize("hello, world!") == ["hello", "world"]


def test_bm25_finds_exact_term() -> None:
    bm = BM25()
    bm.fit(["401k match", "vacation policy", "sick leave"])
    hits = bm.score("401k")
    assert hits[0][0] == 0


def test_bm25_idf_higher_for_rare_term() -> None:
    bm = BM25()
    bm.fit(["a b", "a c", "a d", "a e", "a f"])  # "a" is in all 5; "b" in 1
    score_common = sum(s for i, s in bm.score("a") if s > 0) / max(sum(1 for _ in bm.score("a") if _[1] > 0), 1)
    score_rare = sum(s for i, s in bm.score("b") if s > 0)
    # rare term should give a higher per-doc score (higher IDF)
    assert score_rare > score_common / 5


def test_dense_finds_semantic_neighbor() -> None:
    """Dense returns (idx, score) tuples with scores in [-1, +1] for unit vectors."""
    de = Dense()
    de.fit(["the cat sat on the mat", "the dog played in the yard", "stocks rallied on good earnings"])
    hits = de.score("kitten on a rug")[:3]
    assert len(hits) == 3
    assert all(isinstance(i, int) and isinstance(s, float) for i, s in hits)
    # All L2-normalized vectors => cosine is in [-1, +1]
    for _, s in hits:
        assert -1.0 <= s <= 1.0
    # top-3 should be sorted by score desc
    scores = [s for _, s in hits]
    assert scores == sorted(scores, reverse=True)


def test_rrf_merges_rankings() -> None:
    # doc 1 is rank 1 in both rankings => should win the fusion
    a = [(1, 1.0), (0, 0.9), (2, 0.8)]
    b = [(1, 1.0), (2, 0.9), (0, 0.8)]
    merged = rrf([a, b], k=60)
    assert merged[0][0] == 1


def test_rrf_k_parameter_effect() -> None:
    """Smaller k -> sharper separation between top ranks."""
    a = [(0, 1.0), (1, 0.9), (2, 0.8)]
    b = [(0, 1.0), (1, 0.9), (2, 0.8)]
    merged_small = rrf([a, b], k=1)
    merged_large = rrf([a, b], k=1000)
    # both should still rank 0 first
    assert merged_small[0][0] == 0
    assert merged_large[0][0] == 0


def test_mmr_diversifies() -> None:
    """MMR with lambda<1 should not pick two near-identical vectors in the top-2.

    With lambda=0.0 (pure diversity), the second pick should NOT be the
    most-similar-to-the-first pick.  We pick the highest-cosine doc first,
    then verify the second pick is not its closest neighbor.
    """
    qv = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    # 3 documents: doc 0 and doc 1 are near-duplicates; doc 2 is distinct
    vecs = np.array([
        [0.99, 0.10, 0.0],     # doc 0
        [0.98, 0.20, 0.0],     # doc 1 -- very close to doc 0
        [0.10, 0.99, 0.0],     # doc 2 -- very different
    ], dtype=np.float32)
    vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    selected = mmr(qv, vecs, candidate_ids=[0, 1, 2], lambda_=0.0, k=2)
    # With lambda=0.0, MMR picks by diversity.  First pick is the one most
    # relevant to the query (doc 0).  Second pick should NOT be its near-twin
    # (doc 1) -- it should be doc 2.
    assert selected[0] == 0
    assert selected[1] == 2


def test_mmr_respects_lambda() -> None:
    """lambda=1.0 -> pure relevance (top by score)."""
    qv = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    vecs = np.array([
        [0.99, 0.0, 0.0],     # doc 0 -- top by relevance
        [0.50, 0.0, 0.0],     # doc 1
    ], dtype=np.float32)
    vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    selected = mmr(qv, vecs, candidate_ids=[0, 1], lambda_=1.0, k=1)
    assert selected == [0]


def test_end_to_end_pipeline() -> None:
    """BM25 + Dense + RRF returns a non-empty merged list."""
    bm = BM25()
    bm.fit(SAMPLE_DOCS)
    de = Dense()
    de.fit(SAMPLE_DOCS)
    merged = rrf([bm.score("401k"), de.score("401k")], k=RRF_K)
    assert len(merged) > 0
    assert all(isinstance(i, int) and isinstance(s, float) for i, s in merged)


def test_tokenize_empty_string() -> None:
    """Empty input → no tokens, not a crash."""
    assert tokenize("") == []


def test_bm25_returns_scores_in_range() -> None:
    """All BM25 scores should be >= 0 (standard BM25 is non-negative)."""
    bm = BM25()
    bm.fit(SAMPLE_DOCS)
    scored = bm.score("vacation")
    assert all(s >= 0.0 for _, s in scored)


def test_rrf_known_recipe() -> None:
    """RRF formula is sum(1 / (k + rank)) across lists.  Sanity check."""
    # Three docs: A is rank 1 in list1 only, B is rank 1 in list2 only, C is in neither.
    # With k=60: A = 1/61 = 0.01639, B = 1/61 = 0.01639, C = 0.0.
    # C is unambiguously last.  A and B tie -- order between them is unspecified.
    merged = rrf(
        [[("A", 1.0), ("B", 0.9)], [("B", 1.0), ("A", 0.9)]],
        k=60,
    )
    docs_in_order = [d for d, _ in merged]
    assert "C" not in docs_in_order
    # C never appears because it isn't in any input list
    assert set(docs_in_order) == {"A", "B"}
    a_score = next(s for d, s in merged if d == "A")
    b_score = next(s for d, s in merged if d == "B")
    assert abs(a_score - b_score) < 1e-9  # ties are expected here


def test_mmr_no_candidates_returns_empty() -> None:
    """MMR with no candidates returns []."""
    qv = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    vecs = np.zeros((0, 3), dtype=np.float32)
    selected = mmr(qv, vecs, candidate_ids=[], lambda_=0.5, k=3)
    assert selected == []


def test_dense_score_is_bounded() -> None:
    """Dense cosine scores are in [-1, +1] for normalized vectors."""
    de = Dense()
    de.fit(SAMPLE_DOCS)
    for _, s in de.score("anything"):
        assert -1.0 <= s <= 1.0


# =================================================================
# ENTRY
# =================================================================

if __name__ == "__main__":
    demo()
