"""DeepSeek-style Mixture-of-Experts: top-k routing + load balancing.

The toy captures the two losses that matter for MoE training:
1. Routing loss: encourage balanced expert assignment (so one expert
   doesn't get all the tokens while others sit idle).
2. Auxiliary load-balancing: a soft constraint on the fraction of
   tokens routed to each expert.

Real DeepSeek uses 8-160 experts, top-2 routing, and a learned gate.
This is a 4-expert / top-1 toy in pure NumPy.
"""
from __future__ import annotations
import numpy as np


def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


def top1_route(x: np.ndarray, Wg: np.ndarray) -> np.ndarray:
    """x: [N, D], Wg: [D, E]. Returns expert_id per token."""
    logits = x @ Wg                         # [N, E]
    return logits.argmax(axis=-1)           # [N]


def load_balance_loss(router_prob: np.ndarray, top_ids: np.ndarray, n_experts: int) -> float:
    """Encourages uniform token distribution across experts.

    router_prob: [N, E] - probability of routing to each expert (pre-argmax).
    top_ids: [N] - which expert each token actually went to.
    """
    # P_e = average routing prob per expert (what the gate "wants")
    P = router_prob.mean(axis=0)                              # [E]
    # f_e = fraction of tokens actually routed to expert e
    f = np.bincount(top_ids, minlength=n_experts) / len(top_ids)  # [E]
    return float((P * f).sum() * n_experts)                   # scalar


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    N, D, E = 1024, 64, 4
    x = rng.standard_normal((N, D))
    Wg = rng.standard_normal((D, E)) * 0.1  # small init -> balanced

    # Simulate one forward pass
    logits = x @ Wg
    probs = softmax(logits, axis=-1)
    top = top1_route(x, Wg)

    # Show initial load distribution
    counts = np.bincount(top, minlength=E)
    print(f"initial expert load: {counts.tolist()}  (ideal: {N//E} each)")

    lb = load_balance_loss(probs, top, E)
    print(f"load-balance loss (lower = better balanced): {lb:.4f}")

    # Simulate 100 training steps: nudge the gate to favor underexpert
    for step in range(100):
        logits = x @ Wg
        probs = softmax(logits, axis=-1)
        top = top1_route(x, Wg)
        # Pseudo-gradient: increase logits for the least-loaded expert
        loads = np.bincount(top, minlength=E)
        least = int(loads.argmin())
        Wg[:, least] += 0.01

    final = np.bincount(top, minlength=E)
    print(f"final expert load:   {final.tolist()}")
    print(f"stddev: {final.std():.1f}  (0 = perfect balance)")
