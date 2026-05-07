# 07 — Prompt & Context Engineering Platform

> **Customer problem:** Prompts are scattered across 30+ codebases — untested, untracked, and frequently regressing. Treat prompts as **first-class production artifacts**: versioned, evaluated, A/B tested, and deployed through environments like any other code.

This project implements a **prompt registry** with version control, environment promotion, A/B testing with Bayesian significance, and dynamic context assembly with token budgeting.

---

## 1. Theory: Why prompts deserve infrastructure

Prompts in 2026 are:
- **The instruction set** for the model — semantically equivalent to source code
- **The fastest-changing artifact** in any GenAI system (faster than data, much faster than weights)
- **The leading cause of production regressions** (silent edits in code, no rollback, no eval)

Yet most teams treat them as inline strings. The cost: regressions go undetected, A/B tests are run by intuition, and "what prompt was in production on Tuesday" is unanswerable.

The fix is the same one we used for code 30 years ago — **versioning + environments + tests**.

## 2. The four capabilities

| Capability | Why | This project |
|---|---|---|
| **Versioning** | Roll back; reproduce; audit | `registry.py` — content-hash IDs |
| **Templates** | Reuse; consistency; safety | `templates.py` — Jinja-style fill |
| **Context assembly** | Token budget; freshness; relevance | `context.py` — budget-aware packer |
| **A/B testing** | Ship improvements with confidence | `experiments.py` — Bayesian beta-binomial |

## 3. Versioning model

A prompt is `(template, defaults, metadata)`. We hash the rendered shape (not the variable values) to get a deterministic version ID.

```
prompt_id      = "rag.answer.v3"
content_hash   = sha256(template + sorted(default_keys))   # the version
environments   = {dev: "abcd1234", staging: "abcd1234", prod: "ef567890"}
```

Promotion is just pointing an environment label at a different content_hash. Rollback is one DynamoDB update. Every render of the prompt records `(env, content_hash, variables_hash)` for traceability.

## 4. A/B testing — Bayesian beta-binomial

Frequentist A/B (chi-squared, sequential testing) breaks for small samples and forces "wait until significance." Bayesian beta-binomial:
- Models success rate as Beta(α + successes, β + failures)
- Posterior P(B > A) is computed analytically
- Stop when `P(B > A) > 0.95` OR `P(B > A) < 0.05`
- Naturally handles peeking and small samples

Implementation in `experiments.py` with no SciPy dependency (closed-form integration of two Betas via Monte Carlo or numerical integration).

## 5. Context assembly

For RAG and agent prompts, the runtime variable is *which chunks make it in*. The packer:
1. Reserves tokens for system + question + few-shot examples
2. Greedily packs retrieved chunks by score until the budget is hit
3. Drops or truncates chunks that don't fit, never silently
4. Emits a `pack_report` with what was included and dropped (auditable)

## 6. Architecture (production)

```
   developer
      │ commits prompt_v4 to git
      ▼
   ┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │ git PR   │──▶ │ Eval gate    │──▶ │ Registry     │──▶ │ Bedrock      │
   │ + tests  │    │ (project 04) │    │ (DynamoDB)   │    │ Prompt Mgmt  │
   └──────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                              │
                                              ▼
                              env labels: dev, staging, prod
                              promote = update label pointer
```

## 7. Quick Start

```bash
pip install -r requirements.txt
make demo
```

The demo:
1. Registers two versions of a "summarize ticket" prompt (v1 vs v2).
2. Promotes v1 to `prod` and v2 to `staging`.
3. Runs an A/B simulation, computes Bayesian posterior, declares a winner.
4. Demonstrates context-budget packing with chunks that don't all fit.

## 8. What "Done" Looks Like

| Metric | Target |
|---|---|
| Prompts in registry | 100% of prod use cases |
| Avg time-to-rollback | < 60 s |
| A/B experiments / quarter | ≥ 8 |
| % experiments shipped without regression | ≥ 90% |
| Avg quality lift on shipped wins | ≥ 5pp |
