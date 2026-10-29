---
title: "You Don't Need a Better Model. You Need a Better Evaluation."
subtitle: "Why the bottleneck in AI tool selection is measurement, and what to build first."
tags:
  - ai-evaluation
  - evaluation-infrastructure
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - ai-engineering
  - platform
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1520
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 91
hard_fail: false
distinctness_angle: "Diagnostic-first argument — the bottleneck is the measurement layer, not the candidate layer; structured as 'build the evaluator before you build the catalogue'"
sources_count: 9
author_experience_placeholders: 1
---

Teams spend a quarter evaluating model candidates. Then they pick one, ship it, and six weeks later they cannot tell whether a regression came from the model, the prompt, the data, or a flaky Tuesday.

The problem was not the candidate. It was that nobody built the measurement layer.

## The measurement layer is the product

A 2026 study comparing RAG evaluation metrics produced a number worth sitting with: two human evaluators' ratings correlated with each other at a Pearson correlation of **0.85**.

That is the ceiling. Not a theoretical limit — the observed agreement between two people rating the same outputs. Every automatic metric you deploy is trying to approximate that number, and the study found the most promising one still fell short of explaining it: RAGChecker's claim recall sat near 0.7, and the authors warned that high correlation does not establish validity, because question difficulty and other confounders can produce strong correlations on their own.

Read that again. Your metric can track human judgments at 0.85 and still be measuring difficulty rather than quality.

Their recommended workaround is the single most useful methodological trick in the literature: **evaluate at least two systems and compare their outputs on the same questions.** Shared question difficulty cancels out. Everything else does not.

## What a measurement layer actually contains

If you are serious about this, you need five components. Most teams have one or two.

### One: a task set from your own work

Not a public benchmark. Twenty to thirty questions drawn from tickets you have already closed, queries that have already been answered, documents you already know the answer about.

A 2025 evaluation-ecosystem paper is explicit that static datasets poorly reflect deployment conditions, and argues the unit of evaluation is the "contextual unit" — the behavior of a person using AI in a setting. A 2025 survey of software-engineering agents puts the operational version: benchmark scores should guide rather than determine tool choice, and you should compare candidates on your repository, your language, your context length, your test strength, contamination exposure, latency, and cost.

Contamination deserves its own line, because it is not equally distributed. A benchmark drawn from public repositories may already have appeared in pretraining or fine-tuning data, which is why a dedicated contamination benchmark exists at all. Unfamiliarity cannot be assumed.

### Two: a human baseline, measured once

Do not assume human agreement is high. Measure it. Have two people rate the same 30 outputs and compute the correlation.

This number is worth more than any vendor benchmark, because it tells you what your automatic metrics are actually worth. If your metric correlates at 0.6 with a human baseline of 0.85, you are capturing most of the available signal. If it correlates at 0.2, your metric is decorative.

### Three: a fixed rubric with a stated failure definition

A 2026 benchmark for long-context agentic instruction following showed why this matters. It reported strict pass@1 alongside a relaxed variant tolerating one violated control, and noted that relaxing roughly doubles leader scores. The authors warned that a deployment tolerating one violated control per workflow "has effectively abandoned strictness."

Every score you produce needs a denominator. "92% correct" is meaningless without knowing what counted as incorrect.

### Four: a trace store

Because the answer is not the whole event.

A 2026 paper on agent evaluation is blunt: procedural failures "can look plausible in the final response." Agents claim tools they never invoked, skip mandatory compliance calls, call tools in the wrong order — and the prose reads fine. That work treats trace analysis as necessary rather than optional, and distinguishes deterministic detections (a phantom tool call, checkable against the trace) from subjective judgments.

The same work recommends moving expert knowledge upstream into reusable evaluation artifacts instead of reviewing every trajectory. Its own study ran 47 configurations, 470 trials, and 23,500 turns, and still noted that subjective juror scores were not calibrated to human experts.

### Five: a scheduled re-check

Benchmarks decay, models get replaced, and the web moves.

A 2026 study on source attribution in AI research reports that web-based citations are temporally unstable — pages get paywalled, moved, and removed. A 2025 evaluation-ecosystem paper makes the same point about leaderboards: overreliance on them encourages overfitting and benchmark saturation, and contamination and data leakage can inflate results.

A measurement layer with no re-check is a snapshot pretending to be a monitor.

## Why the candidates are not the bottleneck

Here is the argument for building the evaluator first.

**Because the measurement determines which candidates are even distinguishable.** The 2023 NeurIPS MT-Bench paper found GPT-4 judges agreeing with human preference on more than 80% of comparisons — comparable to human-human agreement — while naming position bias, verbosity bias, and self-enhancement bias, plus "limited reasoning ability." A companion paper showed the fragility in rankings: under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. If your measurement flips under a reordering, you are choosing between noise and noise.

**Because the scale changes the answer.** A 2025 study of retrieval-based tool selection found that giving a model every tool schema dropped selection accuracy to 13.62%, while retrieving the relevant schema raised it to 43.13% and cut average prompt usage from 2,133.84 tokens to 1,084 — and that accuracy degraded beyond roughly 100 candidates as retrieval precision fell. Your tool list is part of your system, and your system changes.

**Because context layout changes the answer.** The 2023 TACL paper "Lost in the Middle" found models perform best at the beginning or end of the context and "significantly degrades when models must access relevant information in the middle," including in explicitly long-context models. A model that passes your eval and fails in production often differs only in where the evidence landed.

**Because more effort is not reliably better.** In the long-context agentic benchmark, raising reasoning effort helped some configurations by 2.0 to 3.0 points, left one unchanged, and hurt one by 2.7 points, while token spend ranged from roughly 13K to 60K per trial with no clean relationship to score. In a 2026 source-attribution study, fact-check accuracy fell by roughly 42 percentage points on average across two frontier models as tool calls rose from 2 to 150, even as link validity and topical relevance stayed above 92%. More searching, less accurate attribution.

None of these are model problems. They are measurement and configuration problems.

## The order of work

**Week 1.** Build the 30-question task set. Stop here if you cannot; everything downstream is theater without it.

**Week 2.** Two humans rate the 30 outputs. Compute the correlation. That number is your ceiling.

**Week 3.** Run two candidates. Swap the presentation order. If the winner flips, your evaluator is not ready.

**Week 4.** Add trace storage. Add a rubric with an explicit failure definition. Add a scheduled re-check.

**Month 2.** Now buy the tool. You will know more about which candidate to buy from the four weeks of evaluator work than from any leaderboard you could have read.

## For papers, the same layer

A reference list is a measurement layer that nobody verifies.

A 2026 benchmark called CiteAudit found 2,967 fabricated citations out of 9,442, and — more usefully for a selection decision — found references that exist but whose title or author metadata does not match, which signals the cited paper was never read. A separate 2026 study on source attribution separated link validity (above 94%) and topical relevance (above 80%) from actual claim support, which ranged from 24.4% to 76.8%.

Your evaluator for a paper is three checks: does it exist, does the metadata match, can you find the passage that supports the sentence.

[AUTHOR EXPERIENCE: Replace with your real account — the evaluation you never built, and the regression you could never diagnose because of it.]

## What this cannot settle

No published work validates a specific "measurement layer" recipe. The five components are my synthesis. The ordering reflects my judgment about sequencing, not a measured result.

The numbers are setup-specific and dated. The 0.85 human-human correlation comes from a 96-question dataset with wide confidence intervals, and the authors explicitly note that a single-system design cannot establish full metric validity. The judge agreement figures are from 2023-era models. Most of the 2026 sources are arXiv preprints. A 2025 paper also notes that the capabilities "Reviewing Work" and "Data Structuring" are not captured at all by the metrics it evaluated — so your measurement layer has known blind spots, and knowing them is part of building it well.

## Where to start this week

1. Write down the 30 questions from your own closed work. Today.
2. Get two people to rate the same 30 outputs. Compute the correlation. Write it down.
3. Run two candidates through the same 30 and swap the order.
4. Find one place where you currently have no trace and start storing one.
5. Add a recurring re-check to the calendar.

## Sources

- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation ≠ validity; 96-question dataset; two-system comparison method.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation in long contexts.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: 13.62% vs 43.13%; 2,133.84 → 1,084 tokens; degradation beyond ~100 candidates.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; trace analysis; 47 configurations / 470 trials / 23,500 turns; juror scores not calibrated to experts; moving expert knowledge upstream.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: strict vs relaxed grading roughly doubling scores; 36.2% strict pass@1; reasoning-effort variance; 13K–60K token range.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; ~42-point fact-check drop from 2 to 150 tool calls; temporal instability of web citations.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; title/author metadata mismatch reveals unread papers.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: leaderboard overfitting, saturation, contamination; field testing; contextual unit framing.
- *Evaluating LLM Metrics Through Real-World Capabilities* (2025). arXiv:2505.08253. https://arxiv.org/html/2505.08253v1
  - Supports: "Reviewing Work" and "Data Structuring" not captured by evaluated metrics.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: benchmark scores guide rather than determine; selection dimensions; contamination.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

How long would it take you to detect a model regression today — and what would you compare against?
