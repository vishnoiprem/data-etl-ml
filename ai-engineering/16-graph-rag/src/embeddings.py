"""Lazy sentence-transformers loader. Singleton per process."""
from __future__ import annotations

import numpy as np
from loguru import logger

from .config import get_settings


_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer  # type: ignore

        s = get_settings()
        logger.info(f"Loading embedding model: {s.embed_model}")
        _model = SentenceTransformer(s.embed_model)
    return _model


def embed(texts: list[str]) -> np.ndarray:
    """Return L2-normalised embeddings, shape (len(texts), dim)."""
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    model = _get_model()
    vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(vecs, dtype=np.float32)
