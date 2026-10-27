---
title: "The 20-Question Test That Replaces 'Which Model Should I Use?'"
subtitle: "A worksheet for comparing candidates on the dimensions that actually predict whether the thing works in your hands."
tags:
  - ai-evaluation
  - evaluation-framework
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - ai-engineering
  - checklist
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1505
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 88
hard_fail: false
distinctness_angle: "Scoring worksheet — a 20-line weighted evaluation sheet with explicit column semantics and a worked scoring example; no narrative device beyond the sheet"
sources_count: 9
author_experience_placeholders: 1
---

Every "which model should I use" conversation eventually collapses into two words: "it depends."

This is true and useless. Here is a worksheet that makes the depends concrete — 20 lines, each with a column meaning, each with a threshold you can check mechanically.

## How to use the sheet

Fill in one row per candidate. One column per line. Three columns: **candidate**, **measured value**, **pass/fail**.

Two rules before you start:

- **Lines 1–4 are gates, not scores.** Fail any one and the candidate is out. No averaging rescues a gate failure.
- **Lines 5–20 are scored.** Weight them by your own priorities, then total.

The weights below are a starting point, not a recommendation. Change them before you start, not after you see the numbers.

## The worksheet

### Gates — all four must pass

| # | Line | Threshold | What it catches |
|---|---|---|---|
| 1 | Can you trace the output back to the steps that produced it? | Yes | Procedural failure hidden in a plausible answer |
| 2 | Can you enforce your critical rule outside the model? | Yes | Reliance on in-context compliance |
| 3 | Does it work at the volume and catalog size you will run at? | Yes | Scale collapse |
| 4 | Is there a deterministic check that catches the failure you cannot afford? | Yes | Silent degradation |

Gate 1 and gate 2 are not hypothetical preferences. A 2026 paper on agent evaluation observes that procedural failures "can look plausible in the final response" — agents claiming tools they never invoked, skipping mandatory compliance calls, calling tools out of order — and a 2026 long-context agentic benchmark recommends "enforcing hard controls outside the model," compiling policies into deterministic tool-call guards rather than trusting in-context adherence. That benchmark's best configuration scored 36.2% strict pass@1: the best system still failed nearly two of every three tasks.

Gate 4 is where silent failures live. In a 2026 source-attribution study, link validity exceeded 94% and relevance exceeded 80% across 14 models, while factual accuracy ranged from 24.4% to 76.8%. Everything cheaply checkable stayed green; the claim-level check did not.

### Scored lines

**Correctness on your task set (weight 20).** Twenty to thirty questions drawn from your own closed work. Not a public benchmark. A 2025 evaluation-ecosystem paper argues the unit of evaluation is the "contextual unit" — the behavior of a person using AI in context — and a 2025 software-engineering agent survey states directly that benchmark scores should guide rather than determine tool choice.

**Retrieval quality, if you retrieve (weight 15).** Score the retrieval stage separately from generation. A 2026 RAG metrics study found human evaluators agreed with each other at a Pearson correlation of 0.85 — the practical ceiling for any proxy — and that faithfulness and hallucination metrics correlated weakly as overall metrics. Separating the stages tells you which half to fix.

**Cost per successful run (weight 15).** At your volume, on your task distribution. The long-context agentic benchmark is instructive here: one configuration reached 21.5% on roughly 13K generated tokens per trial, another spent close to 60K tokens at about three times the dollar cost for the same band, and several mid-pack configurations burned 45–55K tokens to score in single digits. Tokens are not a proxy for quality.

**Latency at p95 (weight 10).** Not the average. The tail is what your users feel.

**Order sensitivity (weight 10).** Swap the presentation order and re-run. A 2023 NeurIPS paper found GPT-4 judges agreeing with human preference on more than 80% of comparisons while exhibiting position, verbosity, and self-enhancement biases. A companion paper showed the order effect concretely: under one setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. If your ranking flips, you have a coin.

**Position sensitivity (weight 10).** Move the relevant context to the middle and re-run. The 2023 TACL paper "Lost in the Middle" found models perform best at the beginning or end and "significantly degrades when models must access relevant information in the middle" — and long-context models were not exempt.

**Selection accuracy at your catalog size (weight 8).** If you route across tools, test at real size. A 2025 retrieval-based tool-selection study found that presenting every schema dropped accuracy to 13.62% while retrieving the relevant one raised it to 43.13%, and that accuracy degraded beyond roughly 100 candidates as retrieval precision fell.

**Failure transparency (weight 5).** Does it tell you when it is unsure or when a step was skipped? A candidate that fails loudly is cheaper to run than one that fails quietly.

**Maintainability (weight 4).** Can your team debug it? Can you pin a version, reproduce a result, and explain a decision six months from now?

**Total: 20 + 15 + 15 + 10 + 10 + 10 + 8 + 5 + 4 = 97** (normalise to 100, or add a line for regulatory fit at your discretion)

## Worked scoring

Two candidates, a RAG system for internal documentation.

**Gates.** Both pass gates 1 and 2. Candidate A fails gate 3 — its tool catalog handles 40 tools cleanly but the team expects 150 within two quarters. Candidate B passes. A is eliminated before scoring.

That is the point of gates. The 13.62% figure from the all-tools condition is not a hypothetical risk; it is the measurement of what happens when you exceed the comfortable size.

**Scored lines.** Candidate B: correctness 18/20, retrieval 12/15, cost 11/15, latency 7/10, order sensitivity 8/10, position sensitivity 5/10, selection accuracy 5/8, failure transparency 4/5, maintainability 3/4. Total 73/97, or 75/100.

The number is not the output. The output is the shape. Position sensitivity at 5/10 says the system depends on how the retrieved context is ordered — a concrete engineering task, not a verdict.

## Adding lines for your domain

The worksheet is deliberately generic. Three additions worth making:

**Regulatory fit.** If a rule must hold on every run, it belongs in the gates, not the scored lines. A 2026 agent-evaluation paper describes human review as "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions" in healthcare, finance, privacy, legal, and security settings — which is a domain-specific line you cannot borrow from anyone else.

**Evidence verifiability.** If the output will be published or acted on, add a line for whether the output can be checked against retrieved source content. The 2026 source-attribution work is the reference: verify the claim, not the link.

**Human-in-the-loop cost.** Add the hours your reviewers will spend per week. The 2026 agent-evaluation paper is candid that human review is costly, slow, and hard to reproduce at every step — the design question is where to place it, not whether to place it.

## What this cannot settle

The worksheet is my construction. No published study validates it, and the weights are placeholders you should replace before use.

The underlying numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 agent-evaluation work updates the picture and still finds LLM judges unreliable as a sole authority. Several of the strongest sources are arXiv preprints. And a worksheet has a structural bias toward things you can measure — which is why the human-in-the-loop cost line exists, and why gate 1 asks a question about traceability rather than performance.

## Where to start this week

1. Copy the twenty lines into a file and delete the ones that do not apply to your decision.
2. Set your four gates before you score anything.
3. Build a 30-question task set from your last three closed tickets.
4. Run the order-swap and position-move checks on your leading candidate.
5. Re-score after 90 days; the weights will have changed by then, and that is worth noticing.

## Sources

- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation as a ceiling; weak faithfulness/hallucination correlation; separate retrieval from generation.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: 13.62% all-tools vs 43.13% retrieved; 2,133.84 → 1,084 tokens; degradation beyond ~100 candidates.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; human review essential for domain context, rubrics, escalation; cost of human review.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; hard controls outside the model; 13K vs 60K tokens and ~3× cost; reasoning-effort variance.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: link validity >94%, relevance >80%, factual accuracy 24.4–76.8%; link-works ≠ claim-supported.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases.
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation in long contexts.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: "contextual unit" framing; field testing; risk-proportional stakeholder involvement.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: benchmark scores guide rather than determine; selection dimensions; contamination.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Which line on this sheet could you not fill in for your current tool — and what does that absence tell you?
