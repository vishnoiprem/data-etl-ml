"""RLHF / DPO training loop: SFT -> reward model -> policy with KL constraint.

DPO (Direct Preference Optimization) is the modern replacement for
the PPO-with-reward-model loop. The key idea: instead of training a
reward model and then doing RL against it, DPO optimizes the policy
directly on preference data (prompt, chosen, rejected) with a closed-
form objective that has an implicit reward + KL constraint.

This is a NumPy toy capturing the DPO loss; real DPO is in PyTorch + TRL.
"""
from __future__ import annotations
import numpy as np


def log_prob(logits: np.ndarray, target: int) -> float:
    """log p(target | logits) under a softmax policy."""
    z = logits - logits.max()
    log_softmax = z - np.log(np.exp(z).sum())
    return float(log_softmax[target])


def dpo_loss(
    policy_chosen_logits: np.ndarray,    # [V]
    policy_rejected_logits: np.ndarray,  # [V]
    ref_chosen_logits: np.ndarray,
    ref_rejected_logits: np.ndarray,
    chosen_id: int,
    rejected_id: int,
    beta: float = 0.1,
) -> tuple[float, float, float]:
    """Returns (loss, chosen_reward_margin, rejected_reward_margin)."""
    pi_logr_chosen = log_prob(policy_chosen_logits, chosen_id) - log_prob(ref_chosen_logits, chosen_id)
    pi_logr_rejected = log_prob(policy_rejected_logits, rejected_id) - log_prob(ref_rejected_logits, rejected_id)
    # Implicit reward: r = beta * (logp_policy - logp_ref)
    r_chosen = beta * pi_logr_chosen
    r_rejected = beta * pi_logr_rejected
    # DPO loss: -log_sigmoid(beta * (logr_chosen - logr_rejected))
    margin = pi_logr_chosen - pi_logr_rejected
    loss = -np.logaddexp(0.0, -beta * margin)  # numerically stable
    return float(loss), float(r_chosen), float(r_rejected)


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    V = 1000   # vocab size
    chosen_id, rejected_id = 42, 99

    # Pretend we sampled from a reference model (the SFT model)
    ref_logits = rng.standard_normal(V) * 0.5

    # At step 0, policy == ref
    policy_logits = ref_logits.copy()
    loss0, r_c0, r_r0 = dpo_loss(policy_logits, policy_logits, ref_logits, ref_logits, chosen_id, rejected_id)
    print(f"step 0: loss={loss0:.4f}, r_chosen={r_c0:.4f}, r_rejected={r_r0:.4f}")

    # Pretend the policy is starting to drift (we nudge logits toward chosen_id)
    for step in range(1, 6):
        policy_logits[chosen_id] += 0.5
        policy_logits[rejected_id] -= 0.5
        loss, r_c, r_r = dpo_loss(policy_logits, policy_logits, ref_logits, ref_logits, chosen_id, rejected_id)
        print(f"step {step}: loss={loss:.4f}, r_chosen={r_c:.4f}, r_rejected={r_r:.4f}, margin={r_c-r_r:.4f}")
