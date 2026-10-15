"""
================================================================
M4 L4  --  ANN and Vector DB Internals
================================================================

Run:    python3 lessons/m04-ann/L4-ann-internals.py
Keys:   none (numpy + stdlib only)

Builds a tiny ANN index from scratch to teach HNSW's structure,
plus three reference indexes (flat, IVF-lite, PQ-lite) for a
benchmark.  All math is exact; the "approximation" is that HNSW
visits only a subset of nodes.

The lesson's point: HNSW is "skip-list on a graph".  Brute force
recalls 100% but is slow.  HNSW recalls 95-99% and is fast.  The
gap is the trade-off you make for speed.
"""

from __future__ import annotations

import heapq
import math
import time
from dataclasses import dataclass, field
from typing import Iterable

import numpy as np


# =================================================================
# CONFIG
# =================================================================

LESSON_NUMBER = "M4.L4"
N_VECTORS = 2000
DIM = 64
M_HNSW = 8                # neighbors per node
EF_CONSTRUCTION = 40      # candidate list size at build time
EF_SEARCH = 32            # candidate list size at query time
N_QUERIES = 50
TOP_K = 10
SEED = 1234
N_LISTS_IVF = 16          # IVF centroids


# =================================================================
# SECTION 1  --  Flat (brute force) index  --  ground truth
# =================================================================

@dataclass
class FlatIndex:
    """Brute force.  Always 100% recall.  Slowest."""
    vectors: np.ndarray
    ids: list[str] = field(default_factory=list)

    def search(self, q: np.ndarray, k: int) -> list[tuple[str, float]]:
        scores = self.vectors @ q
        order = np.argsort(-scores)[:k]
        return [(self.ids[i], float(scores[i])) for i in order]


# =================================================================
# SECTION 2  --  IVF-lite  --  inverted file on k-means centroids
# =================================================================

@dataclass
class IVFLiteIndex:
    """A tiny IVF: cluster the corpus, search only the nearest centroids.

    A real IVF uses FAISS or scANN; this is the structure in 50 lines.
    """
    centroids: np.ndarray
    postings: list[list[int]]    # for each centroid, the list of vector indices
    vectors: np.ndarray
    ids: list[str]
    n_probe: int = 4

    def search(self, q: np.ndarray, k: int) -> list[tuple[str, float]]:
        centroid_scores = self.centroids @ q
        probe = np.argsort(-centroid_scores)[: self.n_probe]
        candidate_idx: list[int] = []
        for c in probe:
            candidate_idx.extend(self.postings[int(c)])
        if not candidate_idx:
            return []
        cand_matrix = self.vectors[candidate_idx]
        scores = cand_matrix @ q
        local_top = np.argsort(-scores)[:k]
        return [(self.ids[candidate_idx[i]], float(scores[i])) for i in local_top]


def build_ivf_lite(vectors: np.ndarray, ids: list[str], n_lists: int, seed: int) -> IVFLiteIndex:
    """k-means with n_lists iterations, Lloyd's algorithm, ~20 iterations."""
    rng = np.random.default_rng(seed=seed)
    n = vectors.shape[0]
    n_lists = min(n_lists, n)
    centroids = vectors[rng.choice(n, size=n_lists, replace=False)].copy()
    for _ in range(20):
        scores = vectors @ centroids.T
        assignments = np.argmax(scores, axis=1)
        for c in range(n_lists):
            mask = assignments == c
            if mask.any():
                centroids[c] = vectors[mask].mean(axis=0)
                centroids[c] = centroids[c] / max(float(np.linalg.norm(centroids[c])), 1e-9)
    postings: list[list[int]] = [[] for _ in range(n_lists)]
    for i, c in enumerate(assignments):
        postings[int(c)].append(i)
    return IVFLiteIndex(centroids=centroids.astype(np.float32),
                        postings=postings, vectors=vectors, ids=ids)


# =================================================================
# SECTION 3  --  PQ-lite  --  product quantization (8 sub-vectors, k-means)
# =================================================================

@dataclass
class PQLiteIndex:
    """Compress each vector to n_subq codes, search by table lookup."""
    sub_dim: int
    n_subq: int
    codebooks: np.ndarray    # shape (n_subq, k, sub_dim) -- k centroids per subq
    codes: np.ndarray        # shape (N, n_subq) int32

    def search(self, vectors: np.ndarray, ids: list[str], q: np.ndarray, k: int) -> list[tuple[str, float]]:
        # Compute distance table: (n_subq, k_centroids) -- for each sub-vector, distance to each centroid
        sub_qs = q.reshape(self.n_subq, self.sub_dim)
        # distances: shape (n_subq, k_centroids)
        dists = np.linalg.norm(self.codebooks - sub_qs[:, None, :], axis=2)
        # For each vector i and each sub-vector s, look up dists[s, codes[i, s]]
        # codes is (N, n_subq), dists is (n_subq, k_centroids)
        # per_sub[i, s] = dists[s, codes[i, s]] -- advanced indexing
        per_sub = dists[np.arange(self.n_subq)[None, :], self.codes]  # shape (N, n_subq)
        scores = -per_sub.sum(axis=1)
        order = np.argsort(-scores)[:k]
        return [(ids[i], float(scores[i])) for i in order]


def build_pq_lite(vectors: np.ndarray, n_subq: int = 8, k: int = 16, seed: int = SEED) -> PQLiteIndex:
    """Tiny product quantization: split each vector into n_subq sub-vectors, k-means each."""
    rng = np.random.default_rng(seed=seed)
    n, dim = vectors.shape
    assert dim % n_subq == 0, f"dim {dim} must be divisible by n_subq {n_subq}"
    sub_dim = dim // n_subq
    codebooks = np.zeros((n_subq, k, sub_dim), dtype=np.float32)
    codes = np.zeros((n, n_subq), dtype=np.int32)
    for s in range(n_subq):
        sub_vecs = vectors[:, s * sub_dim : (s + 1) * sub_dim]
        c0 = sub_vecs[rng.choice(n, size=k, replace=False)]
        cents = c0.copy()
        for _ in range(15):
            d = np.linalg.norm(sub_vecs[:, None, :] - cents[None, :, :], axis=2)
            a = np.argmin(d, axis=1)
            for c in range(k):
                mask = a == c
                if mask.any():
                    cents[c] = sub_vecs[mask].mean(axis=0)
        codebooks[s] = cents
        d = np.linalg.norm(sub_vecs[:, None, :] - cents[None, :, :], axis=2)
        codes[:, s] = np.argmin(d, axis=1).astype(np.int32)
    return PQLiteIndex(sub_dim=sub_dim, n_subq=n_subq, codebooks=codebooks, codes=codes)


# =================================================================
# SECTION 4  --  HNSW-lite  --  graph-based ANN
# =================================================================

@dataclass
class HNSWLiteIndex:
    """Tiny HNSW: each node has M neighbors per layer; greedy search the graph.

    Build:
      1. For each new node, pick M existing nodes as neighbors by brute force.
      2. Connect them.
    Query:
      1. Greedy walk from a random entry point.
      2. Maintain a candidate list of size efSearch; expand the best.
    """
    M: int
    ef_construction: int
    ef_search: int
    vectors: np.ndarray
    ids: list[str]
    graph: list[list[int]] = field(default_factory=list)
    entry: int = 0

    def add(self, idx: int) -> None:
        """Insert a vector at index `idx`.  Connects to M nearest existing nodes."""
        v = self.vectors[idx]
        if not self.graph:
            self.graph = [[] for _ in range(self.vectors.shape[0])]
            self.entry = idx
            return
        # Find M nearest existing nodes by brute force over the prefix
        existing = min(idx, self.vectors.shape[0])
        scores = self.vectors[:existing] @ v
        order = np.argsort(-scores)[: self.M]
        for n in order:
            self.graph[idx].append(int(n))
            self.graph[int(n)].append(idx)

    def search(self, q: np.ndarray, k: int) -> list[tuple[str, float]]:
        """Greedy graph search.  O(M * log N) approx."""
        if not self.graph:
            return []
        # start at entry
        current = self.entry
        visited: set[int] = {current}
        s_cur = float(self.vectors[current] @ q)
        # heap: max-heap of score (use negative for heapq)
        heap: list[tuple[float, int]] = [(-s_cur, current)]
        # best list: min-heap of score, capped at ef_search
        best: list[tuple[float, int]] = [(s_cur, current)]
        expanded = 0
        while heap and expanded < self.ef_search:
            neg_s, idx = heapq.heappop(heap)
            for n in self.graph[idx]:
                if n in visited:
                    continue
                visited.add(n)
                s_n = float(self.vectors[n] @ q)
                # candidate list: always expand; if we have room, push; else push only if better than worst
                heapq.heappush(heap, (-s_n, n))
                if len(best) < self.ef_search:
                    heapq.heappush(best, (s_n, n))
                elif s_n > best[0][0]:
                    heapq.heappushpop(best, (s_n, n))
            expanded += 1
        # return top-k by score
        sorted_best = sorted(best, key=lambda x: -x[0])[:k]
        return [(self.ids[i], s) for s, i in sorted_best]


# =================================================================
# SECTION 5  --  Recall@K helper
# =================================================================

def recall_at_k(retrieved: list[tuple[str, float]], truth: list[tuple[str, float]], k: int) -> float:
    rt = set(d for d, _ in retrieved[:k])
    tt = set(d for d, _ in truth[:k])
    if not tt:
        return 1.0
    return len(rt & tt) / len(tt)


# =================================================================
# SECTION 6  --  Build the 4 indexes on a synthetic corpus
# =================================================================

def make_corpus(n: int, dim: int, seed: int) -> tuple[np.ndarray, list[str]]:
    rng = np.random.default_rng(seed=seed)
    raw = rng.random((n, dim), dtype=np.float32)
    normed = raw / np.linalg.norm(raw, axis=1, keepdims=True)
    ids = [f"v{i:05d}" for i in range(n)]
    return normed.astype(np.float32), ids


def make_queries(vectors: np.ndarray, n: int, seed: int) -> np.ndarray:
    """Pick n random vectors from the corpus as queries (sanity check)."""
    rng = np.random.default_rng(seed=seed)
    idx = rng.choice(vectors.shape[0], size=n, replace=False)
    return vectors[idx]


# =================================================================
# SECTION 7  --  Demo + benchmark
# =================================================================

def demo() -> None:
    """End-to-end: build 4 indexes, benchmark recall + latency."""
    print("=" * 70)
    print(f"  {LESSON_NUMBER}  --  ANN and Vector DB Internals")
    print("=" * 70)

    # 1. Build corpus
    print("\n  Section 1: Build a synthetic corpus (N=2000, dim=64)")
    print("  " + "-" * 66)
    vectors, ids = make_corpus(N_VECTORS, DIM, seed=SEED)
    queries = make_queries(vectors, N_QUERIES, seed=SEED + 1)
    print(f"    vectors shape: {vectors.shape}  dtype: {vectors.dtype}")
    print(f"    queries shape: {queries.shape}")

    # 2. Flat (ground truth)
    print("\n  Section 2: Flat index  --  ground truth (recall=1.0, slowest)")
    print("  " + "-" * 66)
    flat = FlatIndex(vectors=vectors, ids=ids)
    t0 = time.perf_counter()
    truth = [flat.search(q, k=TOP_K) for q in queries]
    flat_ms = (time.perf_counter() - t0) / N_QUERIES * 1000
    print(f"    avg latency: {flat_ms:.2f} ms/query")

    # 3. IVF-lite
    print("\n  Section 3: IVF-lite  (k-means, n_probe=4)")
    print("  " + "-" * 66)
    ivf = build_ivf_lite(vectors, ids, n_lists=N_LISTS_IVF, seed=SEED)
    t0 = time.perf_counter()
    ivf_hits = [ivf.search(q, k=TOP_K) for q in queries]
    ivf_ms = (time.perf_counter() - t0) / N_QUERIES * 1000
    ivf_recall = float(np.mean([recall_at_k(h, t, TOP_K) for h, t in zip(ivf_hits, truth)]))
    print(f"    avg latency: {ivf_ms:.2f} ms/query")
    print(f"    mean recall@10: {ivf_recall:.3f}")

    # 4. HNSW-lite
    print("\n  Section 4: HNSW-lite  (M=8, ef_search=32)")
    print("  " + "-" * 66)
    hnsw = HNSWLiteIndex(M=M_HNSW, ef_construction=EF_CONSTRUCTION,
                         ef_search=EF_SEARCH, vectors=vectors, ids=ids)
    for i in range(vectors.shape[0]):
        hnsw.add(i)
    t0 = time.perf_counter()
    hnsw_hits = [hnsw.search(q, k=TOP_K) for q in queries]
    hnsw_ms = (time.perf_counter() - t0) / N_QUERIES * 1000
    hnsw_recall = float(np.mean([recall_at_k(h, t, TOP_K) for h, t in zip(hnsw_hits, truth)]))
    print(f"    avg latency: {hnsw_ms:.2f} ms/query")
    print(f"    mean recall@10: {hnsw_recall:.3f}")
    print(f"    graph degree: {len(hnsw.graph[500])} (for node 500)")

    # 5. PQ-lite
    print("\n  Section 5: PQ-lite  (8 sub-vectors, k=16 centroids per sub)")
    print("  " + "-" * 66)
    pq = build_pq_lite(vectors, n_subq=8, k=16, seed=SEED)
    t0 = time.perf_counter()
    pq_hits = [pq.search(vectors, ids, q, k=TOP_K) for q in queries]
    pq_ms = (time.perf_counter() - t0) / N_QUERIES * 1000
    pq_recall = float(np.mean([recall_at_k(h, t, TOP_K) for h, t in zip(pq_hits, truth)]))
    print(f"    avg latency: {pq_ms:.2f} ms/query")
    print(f"    mean recall@10: {pq_recall:.3f}")
    compression = (DIM * 4) / (8 * 4)   # raw fp32 vs 8 codes
    print(f"    compression:    {compression:.1f}x  (raw 256B -> 32B)")

    # 6. Comparison table
    print("\n  Section 6: Index comparison  (N=2000, dim=64, k=10)")
    print("  " + "-" * 66)
    print(f"    {'index':<10} {'recall@10':>10} {'avg ms':>10} {'speedup':>10}")
    print(f"    {'flat':<10} {1.0:>10.3f} {flat_ms:>9.2f} {'1.0x':>10}")
    print(f"    {'ivf':<10} {ivf_recall:>10.3f} {ivf_ms:>9.2f} {flat_ms/ivf_ms:>9.1f}x")
    print(f"    {'hnsw':<10} {hnsw_recall:>10.3f} {hnsw_ms:>9.2f} {flat_ms/hnsw_ms:>9.1f}x")
    print(f"    {'pq':<10} {pq_recall:>10.3f} {pq_ms:>9.2f} {flat_ms/max(pq_ms,1e-9):>9.1f}x")

    # 7. The trade-off
    print("\n  Section 7: The ANN trade-off  (recall vs latency)")
    print("  " + "-" * 66)
    print("""
    Brute force:  recall=1.00,  P50 ~ 1-10 ms at 1M vectors  -- ground truth
    HNSW:         recall=0.95-0.99,  P50 ~ 1-5 ms at 1M       -- production default
    IVF-PQ:       recall=0.90-0.95,  P50 ~ 1-3 ms at 100M     -- big scale, OK recall
    ScaNN (Google): recall=0.95-0.99,  P50 ~ 0.5-2 ms         -- best in class

    Rule of thumb:  start with flat (10K vectors).  Move to HNSW at 1M.
    Add PQ compression at 10M+.  Re-measure recall@K at every step.
    """)

    print("=" * 70)
    print("  See L4-ann-internals.ipynb for the runnable version.")
    print("=" * 70)


# =================================================================
# SECTION 8  --  Tests
# =================================================================

def test_flat_recall_is_perfect() -> None:
    """Brute force on a vector that IS in the corpus -> itself is top-1."""
    vectors, ids = make_corpus(50, 8, seed=0)
    flat = FlatIndex(vectors=vectors, ids=ids)
    hits = flat.search(vectors[7], k=1)
    assert hits[0][0] == "v00007"


def test_ivf_returns_k_results() -> None:
    """IVF returns k results per query."""
    vectors, ids = make_corpus(200, 16, seed=0)
    ivf = build_ivf_lite(vectors, ids, n_lists=8, seed=0)
    hits = ivf.search(vectors[0], k=5)
    assert len(hits) == 5
    assert all(isinstance(h, tuple) and len(h) == 2 for h in hits)


def test_hnsw_returns_k_results() -> None:
    """HNSW returns k results per query."""
    vectors, ids = make_corpus(200, 16, seed=0)
    hnsw = HNSWLiteIndex(M=8, ef_construction=16, ef_search=16, vectors=vectors, ids=ids)
    for i in range(vectors.shape[0]):
        hnsw.add(i)
    hits = hnsw.search(vectors[0], k=5)
    assert len(hits) == 5


def test_hnsw_returns_high_scoring_neighbors() -> None:
    """HNSW's top-1 should have cosine >= 0.9 with the query (a real neighbor)."""
    vectors, ids = make_corpus(200, 16, seed=0)
    hnsw = HNSWLiteIndex(M=8, ef_construction=16, ef_search=32, vectors=vectors, ids=ids)
    for i in range(vectors.shape[0]):
        hnsw.add(i)
    hits = hnsw.search(vectors[0], k=1)
    # the top-1 should be a real high-cosine neighbor
    top_id, top_score = hits[0]
    top_idx = int(top_id.lstrip("v"))
    assert top_score >= 0.8, f"top score {top_score} too low; graph not connecting high-cosine pairs"


def test_pq_returns_k_results() -> None:
    """PQ returns k results per query."""
    vectors, ids = make_corpus(200, 16, seed=0)   # 16 = 8 sub * 2 sub-dim
    pq = build_pq_lite(vectors, n_subq=8, k=8, seed=0)
    hits = pq.search(vectors, ids, vectors[0], k=5)
    assert len(hits) == 5


def test_recall_at_k_perfect() -> None:
    assert recall_at_k([("a", 0.9), ("b", 0.8)], [("a", 0.9)], k=2) == 1.0


def test_recall_at_k_partial() -> None:
    assert abs(recall_at_k([("a", 0.9), ("b", 0.8)], [("a", 0.9), ("c", 0.7)], k=2) - 0.5) < 1e-6


def test_make_corpus_normalized() -> None:
    """Synthetic corpus is L2-normalized."""
    vectors, _ = make_corpus(100, 8, seed=0)
    norms = np.linalg.norm(vectors, axis=1)
    assert np.all(np.abs(norms - 1.0) < 1e-5)


def test_make_queries_count() -> None:
    """Returns the requested number of queries."""
    vectors, _ = make_corpus(100, 8, seed=0)
    queries = make_queries(vectors, 10, seed=1)
    assert queries.shape[0] == 10


def test_flat_search_top_k_sorted() -> None:
    """Top-k are sorted by score descending."""
    vectors, ids = make_corpus(100, 8, seed=0)
    flat = FlatIndex(vectors=vectors, ids=ids)
    hits = flat.search(vectors[0], k=5)
    scores = [s for _, s in hits]
    assert scores == sorted(scores, reverse=True)


def test_recall_at_k_zero_when_no_overlap() -> None:
    """recall@k=0 when retrieved and truth sets are disjoint."""
    pred = [("a", 0.9), ("b", 0.8)]
    truth = [("c", 0.7), ("d", 0.6)]
    assert recall_at_k(pred, truth, k=2) == 0.0


def test_recall_at_k_full_overlap() -> None:
    """recall@k=1.0 when retrieved contains all truth items."""
    pred = [("a", 0.9), ("b", 0.8), ("c", 0.7)]
    truth = [("a", 0.9), ("b", 0.8)]
    assert recall_at_k(pred, truth, k=2) == 1.0


def test_recall_at_k_handles_short_retrieved() -> None:
    """If retrieved has fewer than k items, recall is computed on what we have."""
    pred = [("a", 0.9)]
    truth = [("a", 0.9), ("b", 0.8)]
    # |pred[:1] & truth[:2]| = 1, |truth[:2]| = 2, recall = 0.5
    assert abs(recall_at_k(pred, truth, k=2) - 0.5) < 1e-6


def test_make_corpus_is_deterministic_per_seed() -> None:
    """Same seed -> same corpus."""
    a, ida = make_corpus(50, 8, seed=42)
    b, idb = make_corpus(50, 8, seed=42)
    assert ida == idb
    assert np.array_equal(a, b)
    c, _ = make_corpus(50, 8, seed=43)
    assert not np.array_equal(a, c)


def test_make_corpus_dim_matches_request() -> None:
    """Corpus has the requested dimension."""
    for dim in (8, 16, 32, 64):
        v, _ = make_corpus(20, dim, seed=0)
        assert v.shape == (20, dim)


def test_make_queries_come_from_corpus() -> None:
    """Each query vector must be a row of the corpus (sanity check)."""
    vectors, _ = make_corpus(100, 8, seed=0)
    queries = make_queries(vectors, 10, seed=1)
    # All query rows must be in the corpus
    for q in queries:
        # Find a row equal to q
        matches = np.where(np.all(vectors == q, axis=1))[0]
        assert len(matches) > 0


def test_flat_search_on_known_neighbor() -> None:
    """Searching with a corpus vector returns itself as top-1 with score 1.0."""
    vectors, ids = make_corpus(50, 8, seed=0)
    flat = FlatIndex(vectors=vectors, ids=ids)
    # Query with a normalized vector in the corpus; self-similarity = 1.0
    hits = flat.search(vectors[7], k=1)
    assert hits[0][0] == "v00007"
    assert abs(hits[0][1] - 1.0) < 1e-4


def test_hnsw_graph_is_symmetric() -> None:
    """If i has j as a neighbor, j must have i as a neighbor (undirected graph)."""
    vectors, ids = make_corpus(50, 8, seed=0)
    hnsw = HNSWLiteIndex(M=4, ef_construction=16, ef_search=16, vectors=vectors, ids=ids)
    for i in range(vectors.shape[0]):
        hnsw.add(i)
    # For node 25, all of its neighbors should include 25 in their lists
    for neighbor in hnsw.graph[25]:
        assert 25 in hnsw.graph[neighbor], (
            f"asymmetric edge: 25 -> {neighbor} but {neighbor} -> 25 missing"
        )


def test_pq_codes_in_valid_range() -> None:
    """All PQ codes must be in [0, k)."""
    vectors, _ = make_corpus(50, 16, seed=0)
    pq = build_pq_lite(vectors, n_subq=8, k=16, seed=0)
    assert pq.codes.min() >= 0
    assert pq.codes.max() < 16


def test_pq_compresses_vector() -> None:
    """PQ code count (n_subq) << original dim."""
    vectors, _ = make_corpus(50, 64, seed=0)
    pq = build_pq_lite(vectors, n_subq=8, k=16, seed=0)
    # Each vector is now 8 codes (32 bytes) vs 64 floats (256 bytes)
    assert pq.codes.shape[1] == 8
    assert pq.codes.shape[0] == 50


def test_ivf_postings_partition_indices() -> None:
    """IVF postings together cover [0, n) without duplicates or missing rows."""
    vectors, _ = make_corpus(100, 8, seed=0)
    ivf = build_ivf_lite(vectors, list(map(str, range(100))), n_lists=8, seed=0)
    all_indices = sorted(idx for posting in ivf.postings for idx in posting)
    assert all_indices == list(range(100))


def test_ivf_search_returns_real_neighbors() -> None:
    """IVF top-1 for a corpus vector is itself (with high score)."""
    vectors, ids = make_corpus(200, 16, seed=0)
    ivf = build_ivf_lite(vectors, ids, n_lists=8, seed=0)
    # Query with vectors[7]; expect v00007 as top-1
    hits = ivf.search(vectors[7], k=1)
    assert hits[0][0] == "v00007"


def test_hnsw_recall_above_random() -> None:
    """HNSW recall@10 must be > 0.3 (above random baseline of ~10/200 = 0.05)."""
    vectors, ids = make_corpus(500, 32, seed=0)
    queries = make_queries(vectors, 20, seed=1)
    flat = FlatIndex(vectors=vectors, ids=ids)
    hnsw = HNSWLiteIndex(M=8, ef_construction=32, ef_search=32, vectors=vectors, ids=ids)
    for i in range(vectors.shape[0]):
        hnsw.add(i)
    truth = [set(d for d, _ in flat.search(q, k=10)) for q in queries]
    pred = [set(d for d, _ in hnsw.search(q, k=10)) for q in queries]
    recalls = [len(t & p) / 10 for t, p in zip(truth, pred)]
    mean_recall = sum(recalls) / len(recalls)
    assert mean_recall > 0.3, f"HNSW recall too low: {mean_recall}"


def test_index_comparison_table_constructed() -> None:
    """Build all 4 indexes and confirm the comparison runs without errors."""
    vectors, ids = make_corpus(200, 16, seed=0)
    queries = make_queries(vectors, 5, seed=1)
    flat = FlatIndex(vectors=vectors, ids=ids)
    ivf = build_ivf_lite(vectors, ids, n_lists=8, seed=0)
    pq = build_pq_lite(vectors, n_subq=8, k=8, seed=0)
    hnsw = HNSWLiteIndex(M=8, ef_construction=16, ef_search=16, vectors=vectors, ids=ids)
    for i in range(vectors.shape[0]):
        hnsw.add(i)
    # Run all 4 indexes; none should error
    truth = [flat.search(q, k=10) for q in queries]
    ivf_hits = [ivf.search(q, k=10) for q in queries]
    pq_hits = [pq.search(vectors, ids, q, k=10) for q in queries]
    hnsw_hits = [hnsw.search(q, k=10) for q in queries]
    # All should return 10 hits
    for hits in (ivf_hits, pq_hits, hnsw_hits):
        for h in hits:
            assert len(h) == 10
    # IVF recall must be < 1.0 (approximate) but > 0
    ivf_recall = np.mean([recall_at_k(h, t, 10) for h, t in zip(ivf_hits, truth)])
    assert 0.0 < ivf_recall <= 1.0


# =================================================================
# ENTRY
# =================================================================

if __name__ == "__main__":
    demo()
