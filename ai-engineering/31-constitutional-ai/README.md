# Anthropic-style Constitutional AI loop (toy)

Self-critique + revision, the Anthropic way. A principle set, a judge that scores against it, a revision loop that doesn't run forever, and a red-team suite that hits the final model with the awkward prompts. The output is better; the cost is more eval runs.

## Shape

```
            response  ──►  judge
                            │
                            ▼
                  ┌───────────────────┐
                  │  principle set    │  (the "constitution")
                  │  5-50 rules       │
                  └─────────┬─────────┘
                            ▼
                  critiques: list[violated, reason]
                            │
                            ▼
                  any violated? ──yes──► revise
                            │ no
                            ▼
                       return
                            │
                  max_rounds > 0? ──yes──► loop
                            │ no
                            ▼
                       return (best effort)
```

## What I built

- `eval/constitution.py` — `CONSTITUTION` (5 sample principles) + `Critique` + `Revision` + `keyword_judge()` + `revise()`.
- `revise()` runs up to `max_rounds` (default 3) iterations: judge all 5 principles, on first violation reword and try again, on clean exit return immediately.
- The toy judge is a keyword-based heuristic; the README and docstring make clear the real impl uses an LLM judge.
- Smoke test: 4 sample responses (benign, harmful, borderline, refused) — the loop correctly revises the harmful one, passes the benign ones, and notes which principle was violated.

## Real numbers

- Constitutional AI: typically 2-4 critique-revise rounds before convergence.
- Cost: each round = 1 judge call + (sometimes) 1 revision call = 2x model cost.
- Win rate vs base model on harm benchmarks: +15-25% on standard red-team suites (BBQ, HarmBench).
- Regression risk: revision can drift toward over-refusal. Track "appropriate refusal rate" alongside "harmful completion rate."

## What I learned the hard way

- **The constitution needs to be specific.** "Be helpful" is useless. "Don't provide instructions for violent wrongdoing" is enforceable.
- **The judge is the bottleneck.** If the judge is the same model as the responder, you get self-bias (it agrees with itself). Use a stronger model for judging.
- **Revisions can over-refuse.** Without a "appropriate refusal" signal, the model learns to refuse everything. Track it.
- **The red-team suite is non-optional.** The constitution is what you tell the model; the red-team is what you measure. They must be independent sets.

## When to use

- You're shipping to a regulated industry (health, finance, legal, children).
- You have a real eval harness to measure before/after.
- The cost of over-refusal is low (or you have a separate signal for it).

## When NOT to use

- High-stakes refusals are unacceptable (medical, emergency-response — the model should err on the side of answering, not refusing).
- You don't have a held-out red-team set (you'll just be measuring the same constitution).
- Cheap models where the cost of 2x evaluation is a real budget hit.

## Run

```bash
pip install -r requirements.txt
make smoke
```

---

## What this is NOT

- **Not RLHF.** Constitutional AI replaces the
  human-rater step with a *principle-based judge*
  (RLAIF — RL from AI Feedback). The training
  pipeline is different; the result is similar
  (a model that's better aligned to a written
  policy). Use CAI when the policy is stable and
  documentable; use RLHF when the policy is too
  nuanced to write down.
- **Not a substitute for a red-team.** The
  constitution is what you tell the model; the
  red-team is what you measure. They must be
  *independent sets* — measuring on the same
  constitution the model was trained against
  measures memorization, not safety.
- **Not safe-by-default.** "Be helpful" is not
  enforceable. A constitution of 5 vague
  principles produces a model that is no safer
  than the base. The constitution has to be
  specific (the worked example: "Don't provide
  instructions for violent wrongdoing").
- **Not free.** Each critique-revise round is a
  model call; 2-4 rounds per response = 2-4x the
  inference cost. For high-volume serving, the
  cost matters. For low-volume, high-stakes
  use, the cost is the right trade.

---

## Related directories

- [`../28-rlhf-dpo-train/`](../28-rlhf-dpo-train/) —
  the human-feedback alignment training; the
  alternative to CAI when the policy can't be
  written down.
- [`../32-llm-eval-harness/`](../32-llm-eval-harness/) —
  the eval framework that measures the
  before/after on the red-team suite.
- [`../37-frontier-research-pipeline/`](../37-frontier-research-pipeline/) —
  the research pipeline that ablation-tests
  different constitution sizes / phrasings.
- [`../04-fm-evaluation/`](../04-fm-evaluation/) —
  the broader eval framework that includes
  safety benchmarks (BBQ, HarmBench) in
  addition to capability ones.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
