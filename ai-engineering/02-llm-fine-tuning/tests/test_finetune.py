"""Smoke tests for the LoRA + DPO demos."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from src.dpo_demo import init_policies, dpo_loss, train_dpo
from src.lora_demo import (
    FrozenBaseClassifier, LoRAAdapter, evaluate, featurize, train_lora,
)


def test_lora_lifts_accuracy():
    rng = np.random.default_rng(0)
    # Synthetic: 2 classes, dim 32. The classes differ in 1st quadrant of features.
    n = 80
    X = rng.normal(size=(n, 32)).astype(np.float32)
    y = (X[:, 0] > 0).astype(np.int64)

    base = FrozenBaseClassifier.random(feat_dim=32, n_classes=2, seed=42)
    pre = evaluate(base, None, X, y)

    adapter = LoRAAdapter.init(feat_dim=32, n_classes=2, rank=2, seed=0)
    train_lora(base, adapter, X, y, epochs=100, lr=0.5, log_every=10000)
    post = evaluate(base, adapter, X, y)
    assert post > pre, f"LoRA should help: {pre} -> {post}"


def test_dpo_increases_separation():
    pairs = [{"prompt": "p", "chosen": "good", "rejected": "bad"} for _ in range(5)]
    theta, ref, losses, seps = train_dpo(pairs, epochs=50, lr=0.3)
    assert seps[-1] > seps[0]
    assert losses[-1] < losses[0]
