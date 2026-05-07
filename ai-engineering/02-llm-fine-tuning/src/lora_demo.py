"""LoRA demo on a toy classifier — the *math* of LoRA without GPUs.

Real LoRA fine-tunes a transformer's attention/MLP weight matrices. The
mechanics are:

    Original layer:    y = W x
    LoRA layer:        y = W x + (B A) x        with A ∈ R^{r×k}, B ∈ R^{d×r}
    Trainable params:  only A and B; W is frozen.

Here we apply the *same* idea to a tiny logistic-regression classifier
trained on character-bigram features extracted from declaration-page text.
The "frozen base" is a generic classifier; the "LoRA adapter" is a low-rank
update that specializes it for our specific 4-class taxonomy.

This is structurally identical to LoRA on a transformer — same loss function,
same parameter count saving — just on a much smaller model so it runs in
seconds on CPU.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from loguru import logger

LABELS = ["auto", "home", "life", "renters"]
LABEL_TO_IDX = {l: i for i, l in enumerate(LABELS)}


def featurize(texts: list[str], dim: int = 256) -> np.ndarray:
    """Hashed character-bigram features. Stand-in for transformer hidden states."""
    X = np.zeros((len(texts), dim), dtype=np.float32)
    for i, t in enumerate(texts):
        t = re.sub(r"\s+", " ", t.lower())
        for j in range(len(t) - 1):
            bg = t[j:j+2]
            h = hash(bg) % dim
            X[i, h] += 1
        norm = np.linalg.norm(X[i])
        if norm > 0:
            X[i] /= norm
    return X


def softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


@dataclass
class FrozenBaseClassifier:
    """The 'base model' — a classifier we treat as frozen."""
    W: np.ndarray             # (n_classes, feat_dim)
    b: np.ndarray             # (n_classes,)

    @classmethod
    def random(cls, feat_dim: int, n_classes: int, seed: int = 42) -> "FrozenBaseClassifier":
        rng = np.random.default_rng(seed)
        return cls(
            W=rng.normal(0, 0.01, size=(n_classes, feat_dim)).astype(np.float32),
            b=np.zeros(n_classes, dtype=np.float32),
        )

    def logits(self, X: np.ndarray) -> np.ndarray:
        return X @ self.W.T + self.b


@dataclass
class LoRAAdapter:
    """The LoRA adapter — trainable low-rank update added to the base."""
    A: np.ndarray   # (rank, feat_dim)
    B: np.ndarray   # (n_classes, rank)
    rank: int

    @classmethod
    def init(cls, feat_dim: int, n_classes: int, rank: int = 4, seed: int = 0) -> "LoRAAdapter":
        rng = np.random.default_rng(seed)
        # Standard LoRA init: A is random Gaussian, B is zero.
        # This makes the adapter start as a no-op so training is stable.
        return cls(
            A=rng.normal(0, 1.0 / feat_dim, size=(rank, feat_dim)).astype(np.float32),
            B=np.zeros((n_classes, rank), dtype=np.float32),
            rank=rank,
        )

    def logits_delta(self, X: np.ndarray) -> np.ndarray:
        """ΔY = X @ A^T @ B^T  (the low-rank update)."""
        return X @ self.A.T @ self.B.T

    def num_params(self) -> int:
        return self.A.size + self.B.size


def train_lora(
    base: FrozenBaseClassifier,
    adapter: LoRAAdapter,
    X: np.ndarray,
    y: np.ndarray,
    epochs: int = 200,
    lr: float = 0.1,
    log_every: int = 20,
) -> list[float]:
    """Vanilla SGD on the cross-entropy loss, updating ONLY A and B."""
    losses = []
    n = X.shape[0]
    for epoch in range(epochs):
        # Forward
        z_base = base.logits(X)                     # frozen
        delta = X @ adapter.A.T                     # (n, r)
        z = z_base + delta @ adapter.B.T            # (n, c)
        p = softmax(z)
        # Cross-entropy loss
        ll = -np.log(np.clip(p[np.arange(n), y], 1e-12, 1.0)).mean()
        losses.append(float(ll))

        # Backward — only adapter params
        # dL/dz = (p - y_onehot) / n
        y_oh = np.zeros_like(p)
        y_oh[np.arange(n), y] = 1.0
        dz = (p - y_oh) / n                          # (n, c)
        # dz = X @ A^T @ B^T, so:
        dB = dz.T @ delta                            # (c, r)
        dA = adapter.B.T @ dz.T @ X                  # (r, k)

        adapter.B -= lr * dB
        adapter.A -= lr * dA

        if epoch % log_every == 0:
            logger.info(f"epoch {epoch:3d}  loss={ll:.4f}")
    return losses


def evaluate(base: FrozenBaseClassifier, adapter: LoRAAdapter | None,
             X: np.ndarray, y: np.ndarray) -> float:
    z = base.logits(X)
    if adapter is not None:
        z = z + adapter.logits_delta(X)
    pred = z.argmax(axis=1)
    return float((pred == y).mean())
