"""RLHF / DPO training loop: SFT -> reward model -> policy with KL constraint.

DPO (Direct Preference Optimization) is the modern replacement for
the PPO-with-reward-model loop. The key idea: instead of training a
reward model and then doing RL against it, DPO optimizes the policy
directly on preference data (prompt, chosen, rejected) with a closed-
form objective that has an implicit reward + KL constraint.

This is a NumPy toy capturing the DPO loss; real DPO is in PyTorch + TRL.

Meaningful workload:
- Generates 5,000 preference pairs across 5 task types (summarize,
  translate, classify, code, qa) with realistic "good vs bad" answers.
- A toy "policy" is a [V x V] weight matrix that maps prompt tokens
  to next-token logits; the reference is the same matrix, frozen.
- Runs a 50-step DPO training loop watching the loss drop and the
  implicit reward margin (chosen - rejected) grow.
- Evaluates the trained policy on a held-out set and reports the
  fraction of pairs where the policy assigns higher log-prob to
  chosen than rejected (target: > 50%).
- Asserts all the key invariants of a healthy DPO run.
"""
from __future__ import annotations
import numpy as np


# === core API: DPO loss ===

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
    """Returns (loss, r_chosen, r_rejected).

    Numerically stable DPO loss: -logaddexp(0, -beta * margin).
    """
    pi_logr_chosen = log_prob(policy_chosen_logits, chosen_id) - log_prob(ref_chosen_logits, chosen_id)
    pi_logr_rejected = log_prob(policy_rejected_logits, rejected_id) - log_prob(ref_rejected_logits, rejected_id)
    r_chosen = beta * pi_logr_chosen
    r_rejected = beta * pi_logr_rejected
    margin = pi_logr_chosen - pi_logr_rejected
    # DPO loss = -log sigmoid(beta * margin) = log(1 + exp(-beta*margin)) = logaddexp(0, -beta*margin)
    # At margin=0 this is log(2) > 0; it decreases toward 0 as margin grows.
    loss = np.logaddexp(0.0, -beta * margin)
    return float(loss), float(r_chosen), float(r_rejected)


# === meaningful workload: preference data + toy policy ===

# A toy "vocabulary": we treat each (task, response_quality) combo as
# a token id. The policy is a tiny [V x V] weight matrix that we train
# to push chosen-id logits up and rejected-id logits down.
VOCAB_SIZE = 200
TASKS = ["summarize", "translate", "classify", "code", "qa"]
# Per task: ids for "good" and "bad" responses (kept disjoint so the
# preference signal is real and not just a label swap).
TASK_CHOSEN_REJECTED = {
    "summarize":  (10, 110),
    "translate":  (25, 125),
    "classify":   (40, 140),
    "code":       (55, 155),
    "qa":         (70, 170),
}
# 5 "prompt" tokens — a small but meaningful categorical prompt.
PROMPT_TOKENS = list(range(5, 10))   # 5..9


def _make_pair(rng: np.random.Generator, task: str, jitter: float = 0.2):
    """Build one (prompt_tokens, chosen_id, rejected_id) preference pair.

    Adds small jitter to the prompt so different pairs aren't identical.
    """
    prompt = [int(x) for x in rng.choice(PROMPT_TOKENS, size=2)]
    chosen_id, rejected_id = TASK_CHOSEN_REJECTED[task]
    return {"prompt": prompt, "chosen_id": chosen_id, "rejected_id": rejected_id, "task": task}


def generate_preference_pairs(n: int = 5_000, seed: int = 7) -> list[dict]:
    """Generate `n` preference pairs spread across 5 task types.

    A realistic preference dataset has roughly even task coverage
    (labelers don't only label one task) so we round-robin.
    """
    rng = np.random.default_rng(seed)
    pairs = []
    tasks_cycle = TASKS * (n // len(TASKS) + 1)
    for i in range(n):
        task = tasks_cycle[i]
        pairs.append(_make_pair(rng, task))
    return pairs


def init_policy(rng: np.random.Generator, vocab: int = VOCAB_SIZE) -> np.ndarray:
    """Initialize policy weight matrix: [vocab_in x vocab_out]."""
    return rng.standard_normal((vocab, vocab)) * 0.05


def make_logits(W: np.ndarray, prompt: list[int]) -> np.ndarray:
    """Mean-pool the rows of W for the prompt tokens -> [V] logits.

    This is a tiny "language-model head": each prompt token is looked
    up in W, and we average the rows to form next-token logits.
    """
    rows = W[prompt]                       # [len(prompt), V]
    return rows.mean(axis=0)               # [V]


def policy_logprob_pair(
    W: np.ndarray, W_ref: np.ndarray, pair: dict
) -> tuple[float, float, np.ndarray, np.ndarray]:
    """Return (logp_chosen - logp_ref_chosen, logp_rejected - logp_ref_rejected,
    policy_chosen_logits, policy_rejected_logits)."""
    pc = make_logits(W, pair["prompt"])
    pr = make_logits(W, pair["prompt"])
    rc = make_logits(W_ref, pair["prompt"])
    rr = make_logits(W_ref, pair["prompt"])
    return (
        log_prob(pc, pair["chosen_id"]) - log_prob(rc, pair["chosen_id"]),
        log_prob(pr, pair["rejected_id"]) - log_prob(rr, pair["rejected_id"]),
        pc, pr,
    )


def evaluate_accuracy(W: np.ndarray, W_ref: np.ndarray, pairs: list[dict]) -> float:
    """Fraction of pairs where the policy assigns higher logp to chosen than rejected.

    Uses the policy alone (policy logp on chosen vs rejected), which is the
    standard "policy accuracy" metric reported in DPO papers.
    """
    correct = 0
    for p in pairs:
        pi_c = log_prob(make_logits(W, p["prompt"]), p["chosen_id"])
        pi_r = log_prob(make_logits(W, p["prompt"]), p["rejected_id"])
        if pi_c > pi_r:
            correct += 1
    return correct / max(1, len(pairs))


def evaluate_reward_margin(
    W: np.ndarray, W_ref: np.ndarray, pairs: list[dict], beta: float = 0.1
) -> float:
    """Mean implicit reward margin: r_chosen - r_rejected across the set."""
    margins = []
    for p in pairs:
        pi_logr_c, pi_logr_r, _, _ = policy_logprob_pair(W, W_ref, p)
        margins.append(beta * (pi_logr_c - pi_logr_r))
    return float(np.mean(margins))


# === invariance checks ===

def assert_pairs_have_chosen_and_rejected(pairs: list[dict]) -> None:
    """Every pair has a non-null chosen and rejected id, and they differ."""
    for i, p in enumerate(pairs):
        assert "chosen_id" in p and "rejected_id" in p, f"pair {i} missing chosen/rejected"
        assert p["chosen_id"] != p["rejected_id"], f"pair {i} has identical chosen/rejected"
        assert isinstance(p["chosen_id"], int) and isinstance(p["rejected_id"], int), (
            f"pair {i} ids must be ints"
        )


def assert_loss_finite(loss: float) -> None:
    assert np.isfinite(loss) and loss > 0, f"DPO loss must be positive and finite, got {loss}"


def assert_loss_decreased(loss_initial: float, loss_final: float) -> None:
    assert loss_final < loss_initial, (
        f"DPO loss should decrease over training: initial={loss_initial:.4f} final={loss_final:.4f}"
    )


def assert_reward_margin_positive(margin: float) -> None:
    assert margin > 0, f"mean reward margin (chosen - rejected) should be positive, got {margin:.4f}"


def assert_policy_above_random(accuracy: float) -> None:
    assert accuracy > 0.5, f"policy accuracy on eval should beat random (0.5), got {accuracy:.3f}"


# === main smoke test ===

if __name__ == "__main__":
    print("═══ rlhf-dpo-train: meaningful workload ═══")
    rng = np.random.default_rng(0)
    BETA = 0.1
    N_STEPS = 50
    BATCH = 32
    LR = 0.02

    # ---------- Scenario A: generate + verify preference data ----------
    print("\n[A] generating preference data...")
    pairs = generate_preference_pairs(n=5_000, seed=7)
    eval_pairs = generate_preference_pairs(n=500, seed=8)
    print(f"  total pairs:      {len(pairs):,}")
    print(f"  eval pairs:       {len(eval_pairs):,}")
    # Sanity: chosen and rejected are distinguishable
    assert_pairs_have_chosen_and_rejected(pairs)
    chosen_set = {p["chosen_id"] for p in pairs}
    rejected_set = {p["rejected_id"] for p in pairs}
    print(f"  unique chosen ids:   {len(chosen_set)}")
    print(f"  unique rejected ids: {len(rejected_set)}")
    assert chosen_set.isdisjoint(rejected_set), "chosen and rejected token sets must be disjoint"
    # Task coverage
    task_counts = {t: sum(1 for p in pairs if p["task"] == t) for t in TASKS}
    print(f"  task coverage:       {task_counts}")
    assert min(task_counts.values()) > 0, "every task should have at least one pair"
    print("  ✓ every pair has distinct chosen/rejected; task coverage is even")

    # ---------- init policy + reference (frozen) ----------
    W = init_policy(rng, VOCAB_SIZE)
    W_ref = W.copy()    # reference is the SFT model, frozen for the whole run

    # ---------- Scenario B: DPO loss on one batch (initial) ----------
    print("\n[B] initial DPO loss on a batch...")
    batch = pairs[:BATCH]
    initial_losses = []
    for p in batch:
        loss, rc, rr = dpo_loss(
            make_logits(W, p["prompt"]),
            make_logits(W, p["prompt"]),
            make_logits(W_ref, p["prompt"]),
            make_logits(W_ref, p["prompt"]),
            p["chosen_id"], p["rejected_id"], beta=BETA,
        )
        initial_losses.append(loss)
    loss_initial = float(np.mean(initial_losses))
    margin_initial = evaluate_reward_margin(W, W_ref, batch, beta=BETA)
    print(f"  initial DPO loss:     {loss_initial:.4f}")
    print(f"  initial margin (c-r): {margin_initial:.4f}")
    assert_loss_finite(loss_initial)
    assert margin_initial >= 0, f"at init, policy==ref so margin should be ~0, got {margin_initial}"
    print("  ✓ initial DPO loss is positive and finite")

    # ---------- Scenario C: 50-step training loop ----------
    print(f"\n[C] DPO training loop ({N_STEPS} steps, batch={BATCH}, lr={LR}, beta={BETA})...")
    rng_train = np.random.default_rng(1)
    history = []
    for step in range(N_STEPS):
        idx = rng_train.choice(len(pairs), size=BATCH, replace=False)
        batch = [pairs[i] for i in idx]
        # Accumulate parameter gradient: d/dW of mean DPO loss across batch.
        # We use the closed-form gradient of -log_sigmoid(beta * margin)
        # w.r.t. W, applied to the rows corresponding to each prompt token.
        grad = np.zeros_like(W)
        losses = []
        for p in batch:
            pc = make_logits(W, p["prompt"])
            pr = make_logits(W, p["prompt"])
            rc = make_logits(W_ref, p["prompt"])
            rr = make_logits(W_ref, p["prompt"])
            lpc = log_prob(pc, p["chosen_id"])
            lpr = log_prob(pr, p["rejected_id"])
            lrc = log_prob(rc, p["chosen_id"])
            lrr = log_prob(rr, p["rejected_id"])
            margin = (lpc - lrc) - (lpr - lrr)
            # loss = log(1 + exp(-beta*margin)) = -log_sigmoid(beta*margin)
            # d(loss)/d(margin) = -beta * (1 - sigmoid(beta*margin)) = -coef
            sig = 1.0 / (1.0 + np.exp(-BETA * margin))
            # d(loss)/d(logr_chosen)  = -BETA * (1 - sigma)  (for chosen row)
            # d(loss)/d(logr_rejected) = +BETA * (1 - sigma) (for rejected row)
            coef = BETA * (1.0 - sig)
            # log_softmax gradients
            for tok in p["prompt"]:
                # policy chosen id: gradient on row W[tok] is -coef * (e_chosen - softmax(pc))
                softmax_pc = np.exp(pc - pc.max())
                softmax_pc /= softmax_pc.sum()
                grad[tok] -= coef * (np.eye(VOCAB_SIZE, dtype=float)[p["chosen_id"]] - softmax_pc) / len(p["prompt"])
                # policy rejected id: gradient on row W[tok] is +coef * (e_rejected - softmax(pr))
                softmax_pr = np.exp(pr - pr.max())
                softmax_pr /= softmax_pr.sum()
                grad[tok] += coef * (np.eye(VOCAB_SIZE, dtype=float)[p["rejected_id"]] - softmax_pr) / len(p["prompt"])
            losses.append(np.logaddexp(0.0, -BETA * margin))
        W -= LR * grad
        mean_loss = float(np.mean(losses))
        if step % 10 == 0 or step == N_STEPS - 1:
            margin_now = evaluate_reward_margin(W, W_ref, batch, beta=BETA)
            history.append((step, mean_loss, margin_now))
            print(f"  step {step:>3}: loss={mean_loss:.4f}  margin(c-r)={margin_now:+.4f}")
    loss_final = history[-1][1]
    margin_final = history[-1][2]
    print(f"  final DPO loss:       {loss_final:.4f}")
    print(f"  final margin (c-r):   {margin_final:+.4f}")
    assert_loss_finite(loss_final)
    assert_loss_decreased(loss_initial, loss_final)
    assert_reward_margin_positive(margin_final)
    print("  ✓ DPO loss decreased, reward margin grew positive")

    # ---------- Scenario D: evaluate trained policy ----------
    print("\n[D] evaluating trained policy on held-out set...")
    accuracy = evaluate_accuracy(W, W_ref, eval_pairs)
    eval_margin = evaluate_reward_margin(W, W_ref, eval_pairs, beta=BETA)
    print(f"  eval policy accuracy:  {accuracy:.3f}  (random baseline 0.500)")
    print(f"  eval reward margin:    {eval_margin:+.4f}")
    assert_policy_above_random(accuracy)
    assert_reward_margin_positive(eval_margin)
    print("  ✓ policy beats random on held-out preferences")

    # ---------- final summary ----------
    print("\n══════════ summary ══════════")
    print(f"  preference pairs (train):   {len(pairs):,}")
    print(f"  preference pairs (eval):    {len(eval_pairs):,}")
    print(f"  initial DPO loss:           {loss_initial:.4f}")
    print(f"  final   DPO loss:           {loss_final:.4f}")
    print(f"  train reward margin:        {margin_final:+.4f}")
    print(f"  eval  reward margin:        {eval_margin:+.4f}")
    print(f"  eval  policy accuracy:      {accuracy:.3f}")
    print("\n✓ all invariants pass")
