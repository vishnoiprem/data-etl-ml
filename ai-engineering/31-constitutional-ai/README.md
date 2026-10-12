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

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
