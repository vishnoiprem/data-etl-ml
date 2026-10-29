"""Embedding adapter — Local (sentence-transformers) and AWS (Bedrock Titan).

The two backends share an interface so the rest of the pipeline doesn't care
which one is in use. This is a pattern we repeat throughout the codebase:
**adapters at the edge, business logic in the middle**.

A `HashingEmbedder` fallback is included for sandboxed/air-gapped environments
where sentence-transformers can't download model weights. It produces
deterministic but semantically weak embeddings — fine for demos, not for prod.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import Sequence

import numpy as np
from loguru import logger

from src.config import settings


class Embedder(ABC):
    """Embedding model interface."""

    dim: int  # embedding dimensionality

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> np.ndarray:
        """Return shape (len(texts), dim) array of float32 embeddings."""


class HashingEmbedder(Embedder):
    """Deterministic, dependency-free fallback embedder.

    Uses the hashing-trick over character n-grams + word unigrams. Combined
    with L2 normalization, this is roughly equivalent to a hashed TF-IDF
    representation. Quality is far below a transformer embedder, but it is
    fully offline and fast enough that the demo always runs.
    """

    def __init__(self, dim: int = 512, ngrams: tuple[int, ...] = (3, 4, 5)):
        self.dim = dim
        self.ngrams = ngrams

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def _features(self, text: str) -> Counter:
        text = text.lower()
        feats: Counter = Counter()
        for w in self._tokens(text):
            feats[f"w::{w}"] += 1
        # char n-grams over the whole string
        s = re.sub(r"\s+", " ", text)
        for n in self.ngrams:
            for i in range(len(s) - n + 1):
                feats[f"c{n}::{s[i:i+n]}"] += 1
        return feats

    def _vec(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        for feat, count in self._features(text).items():
            h = int(hashlib.md5(feat.encode()).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h >> 32) & 1 else -1.0
            # log-tf weighting
            v[idx] += sign * (1.0 + math.log(count))
        norm = float(np.linalg.norm(v))
        if norm > 0:
            v /= norm
        return v

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.vstack([self._vec(t) for t in texts])


class LocalEmbedder(Embedder):
    """Sentence-transformers backend. Free, runs on CPU. Good enough for dev + small-scale prod."""

    def __init__(self, model_name: str | None = None):
        from sentence_transformers import SentenceTransformer
        self.model_name = model_name or settings.LOCAL_EMBEDDING_MODEL
        logger.info(f"Loading local embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        emb = self.model.encode(
            list(texts),
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,  # cosine-friendly
        )
        return emb.astype(np.float32)


class BedrockEmbedder(Embedder):
    """Amazon Bedrock backend (Titan Text Embeddings v2). Production default for AWS mode."""

    def __init__(self, model_id: str | None = None):
        import boto3
        self.model_id = model_id or settings.BEDROCK_EMBEDDING_MODEL
        self.client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
        self.dim = 1024  # Titan v2 default; configurable to 256/512/1024

    def _embed_one(self, text: str) -> np.ndarray:
        body = json.dumps({
            "inputText": text,
            "dimensions": self.dim,
            "normalize": True,
        })
        resp = self.client.invoke_model(modelId=self.model_id, body=body)
        payload = json.loads(resp["body"].read())
        return np.array(payload["embedding"], dtype=np.float32)

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        # Bedrock Titan embeddings is a single-text-per-call API; for true
        # batch throughput, use Bedrock Batch Inference for ingestion (50% cheaper).
        return np.vstack([self._embed_one(t) for t in texts]) if texts else \
               np.zeros((0, self.dim), dtype=np.float32)


def get_embedder() -> Embedder:
    """Factory: return the right embedder for the current mode.

    Order of preference:
      AWS mode    → BedrockEmbedder
      LOCAL mode  → LocalEmbedder (sentence-transformers), with HashingEmbedder
                    as fallback if model weights cannot be loaded.
    """
    if settings.is_aws:
        return BedrockEmbedder()
    try:
        return LocalEmbedder()
    except Exception as e:
        logger.warning(
            f"Falling back to HashingEmbedder ({e.__class__.__name__}: {e}). "
            "For production-quality embeddings, install sentence-transformers "
            "and ensure HuggingFace is reachable, or use AWS mode."
        )
        return HashingEmbedder(dim=512)
