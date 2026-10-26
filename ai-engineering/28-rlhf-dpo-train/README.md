# RLHF / DPO training loop (toy)

The full alignment path: SFT → reward model → policy with KL constraint. DPO (Direct Preference Optimization) is the modern replacement for the PPO-with-reward-model loop. The key insight: instead of training a reward model and then doing RL against it, DPO optimizes the policy directly on preference data with a closed-form objective that has an implicit reward + KL constraint.

## Shape

```
            preference data
            (prompt, chosen, rejected)
                     │
                     ▼
            ┌─────────────────────┐
            │  policy π_θ         │  forward: get chosen/rejected logits
            │  reference π_ref    │  (frozen SFT model)
            └────────┬────────────┘
                     ▼
       loss = -log σ(β · (log π_θ(chosen|x) - log π_θ(rejected|x)
                          - log π_ref(chosen|x) + log π_ref(rejected|x)))
                     │
                     ▼
              optimizer step
```

## What I built

- `train/dpo.py` — `log_prob()` + `dpo_loss()` returning `(loss, r_chosen, r_rejected)`.
- The DPO loss in numerically stable form: `-logaddexp(0, -beta * margin)`.
- A `__main__` smoke test that runs 6 pseudo-training steps and watches the loss drop, the chosen-reward margin grow.
- `beta=0.1` is the KL constraint strength — high beta = stay close to the reference, low beta = more freedom.

## Real numbers

- DPO vs PPO: 2-3x cheaper to train (no separate reward model, no rollouts).
- DPO is unstable on out-of-distribution prompts — pair with a KL warmup.
- Typical beta range: 0.1-0.5; tune per task.
- Reward margin: > 0.5 logits by end of training = good separation; < 0.1 = undertrained.

## What I learned the hard way

- **The reference model is sacred.** If you accidentally update its weights, the KL constraint collapses and the policy can drift arbitrarily. Keep it frozen, log its hash at training start.
- **Beta is the most important hyperparameter.** Too low and the policy wanders off into nonsense; too high and it never improves over the SFT model. Sweep it.
- **Preference data quality > quantity.** 10K high-quality (chosen, rejected) pairs beats 1M noisy ones. Invest in labeling.
- **DPO is not magic for hard reasoning tasks.** For math, code, and multi-step reasoning, RL with a verifiable reward (RLOO, GRPO) often beats DPO.

## When to use

- You have a clear "good vs bad" preference signal (human raters, LLM-as-judge).
- The base model is already instruction-tuned (start from SFT, not from a base LM).
- You want a stable, reproducible alignment recipe (DPO is more reproducible than PPO).

## When NOT to use

- Cold-start from a base model (do SFT first).
- Verifiable reward tasks (math, code) — use GRPO or RLOO instead.
- When you don't have preference data (use rejection-sampling fine-tuning instead).

## Run

```bash
pip install -r requirements.txt
make smoke
```

---

## What this is NOT

- **Not a PPO-with-reward-model implementation.** DPO
  is the modern replacement. PPO needs a separate
  reward model, rollouts, and a value head; DPO
  drops all three. If you have a PPO setup, keep it;
  if you're starting new, start with DPO.
- **Not SFT.** RLHF / DPO is the *second* stage of
  alignment. The first is supervised fine-tuning on
  instruction-response data. Don't cold-start from
  a base LM with DPO.
- **Not a magic alignment fix.** DPO optimizes a
  *preference* signal; if the preference data is
  noisy or the "good" side is genuinely bad, DPO
  will faithfully align to a bad target. The
  preference data is the ceiling.
- **Not reasoning alignment.** For math / code /
  multi-step reasoning, RL with a *verifiable*
  reward (RLOO, GRPO) often beats DPO. DPO is
  best for "this style of answer is better" tasks
  where there's no objective correctness signal.

---

## Related directories

- [`../29-fsdp-flash-train/`](../29-fsdp-flash-train/) —
  the distributed-training patterns (FSDP, FlashAttention)
  that this single-GPU build is a stripped-down
  version of.
- [`../31-constitutional-ai/`](../31-constitutional-ai/) —
  the alternative alignment approach (RLAIF with a
  constitution instead of human preferences).
- [`../25-deepseek-moe-train/`](../25-deepseek-moe-train/) —
  the MoE training patterns that you'd combine
  with DPO for a DeepSeek-style model.
- [`../32-llm-eval-harness/`](../32-llm-eval-harness/) —
  the eval framework that measures whether the
  DPO-trained model is actually better than the
  SFT-only baseline.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
