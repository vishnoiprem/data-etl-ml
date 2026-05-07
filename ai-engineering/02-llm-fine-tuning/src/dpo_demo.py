"""DPO (Direct Preference Optimization) demo.

DPO replaces the RLHF reward-model + PPO loop with a closed-form objective.
Given preference pairs (prompt p, chosen y_w, rejected y_l), we directly
optimize:

    L_DPO = - log σ( β * ( log π_θ(y_w|p) − log π_ref(y_w|p)
                          − log π_θ(y_l|p) + log π_ref(y_l|p) ) )

where π_θ is the model being tuned, π_ref is the frozen reference, and
β controls how far we drift from the reference.

Intuition:
  - We don't need to learn an explicit reward function; the difference of
    log-probs IS the reward.
  - The KL constraint to π_ref is baked into the loss via β.
  - One supervised pass through preference pairs replaces the entire RLHF stack.

For the demo we use scalar "policies" — each (prompt, response) pair has a
trainable score s_θ(p, y) and a frozen reference score s_ref(p, y). Same
gradients, same dynamics, no GPU needed.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from loguru import logger


def sigmoid(x: np.ndarray | float) -> np.ndarray | float:
    return 1.0 / (1.0 + np.exp(-x))


@dataclass
class ScalarPolicy:
    """A toy stand-in for the policy log-prob.

    For each (prompt, response) pair we keep a scalar that represents
    log π(y|p). Real DPO works on actual log-probs from a transformer.
    """
    scores: dict[tuple[str, str], float]

    def logp(self, prompt: str, response: str) -> float:
        return self.scores.get((prompt, response), 0.0)


def init_policies(pairs: list[dict], seed: int = 0) -> tuple[ScalarPolicy, ScalarPolicy]:
    rng = np.random.default_rng(seed)
    # Reference: random log-probs (frozen)
    ref = {}
    for r in pairs:
        ref[(r["prompt"], r["chosen"])] = float(rng.normal(0, 0.1))
        ref[(r["prompt"], r["rejected"])] = float(rng.normal(0, 0.1))
    # Theta: starts equal to reference (no drift initially)
    theta = dict(ref)
    return ScalarPolicy(theta), ScalarPolicy(ref)


def dpo_loss(theta: ScalarPolicy, ref: ScalarPolicy, pairs: list[dict], beta: float = 0.5) -> float:
    losses = []
    for r in pairs:
        p, yw, yl = r["prompt"], r["chosen"], r["rejected"]
        margin = beta * (
            (theta.logp(p, yw) - ref.logp(p, yw)) -
            (theta.logp(p, yl) - ref.logp(p, yl))
        )
        losses.append(-np.log(np.clip(sigmoid(margin), 1e-9, 1.0)))
    return float(np.mean(losses))


def reward_separation(theta: ScalarPolicy, ref: ScalarPolicy, pairs: list[dict]) -> float:
    """Mean implicit reward of chosen minus rejected (β=1)."""
    seps = []
    for r in pairs:
        rw = theta.logp(r["prompt"], r["chosen"]) - ref.logp(r["prompt"], r["chosen"])
        rl = theta.logp(r["prompt"], r["rejected"]) - ref.logp(r["prompt"], r["rejected"])
        seps.append(rw - rl)
    return float(np.mean(seps))


def step(theta: ScalarPolicy, ref: ScalarPolicy, pairs: list[dict], lr: float = 0.1, beta: float = 0.5):
    """Manual gradient descent step on the DPO loss."""
    grads: dict[tuple[str, str], float] = {}
    for r in pairs:
        p, yw, yl = r["prompt"], r["chosen"], r["rejected"]
        margin = beta * (
            (theta.logp(p, yw) - ref.logp(p, yw)) -
            (theta.logp(p, yl) - ref.logp(p, yl))
        )
        # dL/dmargin = -(1 - σ(margin))
        dmargin = -(1.0 - sigmoid(margin))
        # margin = β · (θ(yw) - θ(yl))   (ref terms are constants)
        # → dL/dθ(yw) = β · dmargin    ;  dL/dθ(yl) = -β · dmargin
        grads[(p, yw)] = grads.get((p, yw), 0.0) + beta * dmargin
        grads[(p, yl)] = grads.get((p, yl), 0.0) - beta * dmargin

    for k, g in grads.items():
        theta.scores[k] = theta.scores.get(k, 0.0) - lr * g


def train_dpo(pairs: list[dict], epochs: int = 200, lr: float = 0.2, beta: float = 0.5):
    theta, ref = init_policies(pairs)
    losses, seps = [], []
    for epoch in range(epochs):
        step(theta, ref, pairs, lr=lr, beta=beta)
        losses.append(dpo_loss(theta, ref, pairs, beta=beta))
        seps.append(reward_separation(theta, ref, pairs))
        if epoch % 20 == 0:
            logger.info(f"epoch {epoch:3d}  loss={losses[-1]:.4f}  reward_separation={seps[-1]:+.3f}")
    return theta, ref, losses, seps


def load_pairs(path: Path) -> list[dict]:
    pairs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))
    return pairs
