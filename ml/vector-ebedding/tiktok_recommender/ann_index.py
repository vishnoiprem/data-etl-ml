import os
import pickle
import numpy as np
import faiss

class ANNIndex:
    """
    Cosine-sim ANN via IndexFlatIP + L2-normalization.
    Use the same `dimension` as your model's embed_dim.
    """
    def __init__(self, dimension: int = 32):
        self.dimension = int(dimension)
        self.index = faiss.IndexFlatIP(self.dimension)
        self._size = 0

    @staticmethod
    def _as_float32(a: np.ndarray) -> np.ndarray:
        return np.ascontiguousarray(a.astype(np.float32, copy=False))

    def build_index(self, item_embeddings: np.ndarray):
        """
        Normalize and add embeddings. Shape: (n_items, d).
        """
        emb = self._as_float32(item_embeddings)
        if emb.ndim != 2 or emb.shape[1] != self.dimension:
            raise ValueError(f"Expected (n, {self.dimension}) got {emb.shape}")
        faiss.normalize_L2(emb)  # in-place
        self.index.add(emb)
        self._size = emb.shape[0]

    def save_index(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        faiss.write_index(self.index, path)

    def load_index(self, path: str):
        self.index = faiss.read_index(path)
        # Best-effort: infer dimension from loaded index
        self.dimension = self.index.d

    def search(self, query_embedding: np.ndarray, k: int = 10):
        """
        query_embedding: shape (d,) or (1, d).
        Returns (indices, scores) where scores are cosine sims.
        """
        q = self._as_float32(query_embedding)
        if q.ndim == 1:
            q = q[None, :]
        if q.shape[1] != self.dimension:
            raise ValueError(f"Query dim {q.shape[1]} != index dim {self.dimension}")
        faiss.normalize_L2(q)
        distances, indices = self.index.search(q, k)
        return indices[0], distances[0]

    def add_with_mappings(self, item_embeddings: np.ndarray, ids: list):
        """
        Add more items later with your own external IDs.
        Maintains an internal idx_to_id list.
        """
        if not hasattr(self, "idx_to_id"):
            self.idx_to_id = []
        emb = self._as_float32(item_embeddings)
        if emb.ndim != 2 or emb.shape[1] != self.dimension:
            raise ValueError(f"Expected (n, {self.dimension}) got {emb.shape}")
        faiss.normalize_L2(emb)
        self.index.add(emb)
        self.idx_to_id.extend(ids)
        self._size += emb.shape[0]

    def save_mappings(self, idx_to_id, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(idx_to_id, f)

    def load_mappings(self, path: str):
        with open(path, "rb") as f:
            return pickle.load(f)
