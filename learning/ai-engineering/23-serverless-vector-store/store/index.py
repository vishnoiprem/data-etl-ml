"""
Toy IVF (Inverted File) index for vector search.

The same idea behind FAISS-IVF and Pinecone's pod-based index:
- Cluster all vectors into nlist centroids (k-means once, offline).
- At query time, find the nprobe closest centroids, scan their vectors.

Captures the trade-off in a small file. Real impl: FAISS, ScaNN, or
Pinecone's pod server.
"""
from __future__ import annotations
import heapq
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class IVFIndex:
    nlist: int                       # number of clusters
    dim: int
    centroids: np.ndarray            # (nlist, dim)
    # inverted list: cluster_id -> list of (vector_id, vector)
    postings: dict[int, list[tuple[int, np.ndarray]]]

    def add(self, ids: list[int], vectors: np.ndarray):
        """Assign each vector to its nearest centroid."""
        if vectors.shape[1] != self.dim:
            raise ValueError(f"dim mismatch: index={self.dim}, got={vectors.shape[1]}")
        assignments = nearest_centroids(vectors, self.centroids)
        for vid, vec, cid in zip(ids, vectors, assignments):
            self.postings[cid].append((vid, vec))

    def search(self, query: np.ndarray, top_k: int = 10, nprobe: int = 8) -> list[tuple[int, float]]:
        """Search top-K nearest vectors in the nprobe closest clusters."""
        if query.ndim == 1:
            query = query[None, :]
        c_dists = euclidean(query[0], self.centroids)
        # nprobe closest centroids (smallest distance)
        probe_ids = np.argpartition(c_dists, min(nprobe, len(c_dists) - 1))[:nprobe]

        # min-heap of size top_k
        heap: list[tuple[float, int]] = []
        for cid in probe_ids:
            for vid, vec in self.postings[int(cid)]:
                d = float(euclidean(query[0], vec))
                if len(heap) < top_k:
                    heapq.heappush(heap, (-d, vid))
                elif -heap[0][0] > d:
                    heapq.heapreplace(heap, (-d, vid))

        return [(vid, -neg) for neg, vid in sorted(heap, reverse=True)]


# --- Reference math ---------------------------------------------------------

def euclidean(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Pairwise euclidean distance. Real impl: SIMD / BLAS."""
    if b.ndim == 1:
        return float(np.linalg.norm(a - b))
    return np.linalg.norm(a[None, :] - b, axis=1)


def cosine(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Pairwise cosine distance (1 - cos sim)."""
    a_n = a / (np.linalg.norm(a) + 1e-12)
    if b.ndim == 1:
        return float(1.0 - np.dot(a_n, b / (np.linalg.norm(b) + 1e-12)))
    b_n = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-12)
    return 1.0 - a_n @ b_n.T


def nearest_centroids(vectors: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    """For each vector, return the index of the closest centroid."""
    # Naive O(n * nlist * dim). Real impl: batched matmul.
    d = np.linalg.norm(vectors[:, None, :] - centroids[None, :, :], axis=2)
    return np.argmin(d, axis=1)


def build_ivf(vectors: np.ndarray, nlist: int, n_iter: int = 20, seed: int = 0) -> IVFIndex:
    """Toy k-means to build centroids. Real impl: FAISS k-means."""
    rng = np.random.default_rng(seed)
    n, dim = vectors.shape
    init = rng.choice(n, size=nlist, replace=False)
    centroids = vectors[init].astype(np.float32).copy()
    for _ in range(n_iter):
        # assign
        a = nearest_centroids(vectors, centroids)
        # update
        new_centroids = np.zeros_like(centroids)
        counts = np.zeros(nlist, dtype=np.int64)
        for v, c in zip(vectors, a):
            new_centroids[c] += v
            counts[c] += 1
        nonzero = counts > 0
        new_centroids[nonzero] /= counts[nonzero, None]
        # re-seed empty clusters
        empty = ~nonzero
        if empty.any():
            new_centroids[empty] = vectors[rng.choice(n, size=empty.sum(), replace=False)]
        if np.allclose(new_centroids, centroids, atol=1e-6):
            break
        centroids = new_centroids

    postings: dict[int, list[tuple[int, np.ndarray]]] = defaultdict(list)
    return IVFIndex(nlist=nlist, dim=dim, centroids=centroids, postings=postings)


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    # 5000 fake 64-dim vectors in 10 clusters
    centers = rng.uniform(-1, 1, size=(10, 64))
    vecs = centers[rng.choice(10, size=5000)] + rng.normal(0, 0.1, size=(5000, 64))
    ids = list(range(5000))

    index = build_ivf(vecs, nlist=10)
    index.add(ids, vecs)

    # Query with one of the original vectors
    q = vecs[0]
    hits = index.search(q, top_k=5, nprobe=2)
    print(f"top-5 for vec[0]: {hits}")
