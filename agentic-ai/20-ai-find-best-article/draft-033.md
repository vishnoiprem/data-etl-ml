---
title: "Buy the Workflow, Not the Model: A Selection Rule That Handles Vendor Churn"
subtitle: "Why a model is the replaceable part of the decision, and what to buy instead."
tags:
  - ai-engineering
  - model-selection
  - llm
  - how-to-evaluate-llm-tools
  - ai-evaluation
  - architecture
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1410
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 87
hard_fail: false
distinctness_angle: "Churn-hedging frame — evaluates the durability of a choice rather than its quality, and inverts the usual question from 'which model wins' to 'what survives a model change'"
sources_count: 9
author_experience_placeholders: 1
---

Nobody has ever regretted a wrong choice that took three weeks to undo.

They regret the choice that took three months to undo, because by then it was in five code paths, a hiring plan, and a customer's contract.

So the question that matters is not "which tool is best?" It is "which parts of this decision will still be true after the vendor ships something new?"

## The parts that churn and the parts that do not

Model quality churns. It churns on a schedule you cannot see, with no changelog, and it can move in either direction.

Three things do not churn:

**Your evaluation set.** Thirty questions from your own closed work, with the answers they require, and the note of what each one is for. The 2026 source-attribution study shows why this matters even for research tooling: across 14 models and 130 research queries, link validity exceeded **94%** and relevance exceeded **80%**, while factual accuracy ranged from **24.4% to 76.8%**. A benchmark that looks healthy on the cheap dimensions can fail on the one that counts. Your set must be judged on the dimension you care about, by you.

**Your decision rules.** Which metric you read first, what you treat as a tie, what change causes you to re-open the decision. These are yours, and no vendor can invalidate them.

**Your interface layer.** The thin piece of code between your application and the model. If you own it, a model change is a config change.

Everything else — which model, which provider, which host — is a lease, and leases end.

## The evidence that the lease is short

The 2026 source-attribution study also found that fact-check accuracy fell by roughly **42 percentage points on average** as tool calls rose from 2 to 150, across GPT-5.4 and Claude Opus 4.6. One configuration dropped from 78.6% to 16.7%; another from 80.0% to 57.9%. Link validity and topical relevance stayed above 92% throughout.

Two lessons. First, capability drifts within a single agent's run, not just between releases. Second, the cheap signals stay green while the load-bearing one degrades — which is exactly the shape of a vendor change you will not notice.

A 2025 evaluation-ecosystem paper adds the structural version. Leaderboard reliance encourages overfitting and saturation, and the "contextual unit" of evaluation — a person using AI in a setting — has to be watched over time rather than sampled once. A decision made from a single snapshot is a decision about a moment.

## The rule

**Buy the workflow. Rent the model.**

Concretely: the thing you own is the harness — prompts, retrieval, evaluation set, decision rules, logs, and the interface. The thing you rent is the weights and the serving.

If the harness is portable, a model swap is a settings change. If the harness is welded to one vendor's SDK, tool-calling schema, and pricing page, a model swap is a project.

## The four questions that tell you which one you have

**Could you run the same 30 questions against a competitor's model in an afternoon?**

If the answer is no, the interface is the problem. A 2026 RAG metrics study's method is the standard to aim for: evaluate at least two systems on the same questions, so shared difficulty cancels and the difference is visible. You cannot do that if swapping means rewriting.

**Do you own the logs?**

A 2026 agent-evaluation paper is the sharpest statement of what a log buys you. Procedural failures "can look plausible in the final response" — an agent claiming a tool it never invoked, skipping a mandatory compliance call, calling tools out of order. It separates deterministic detections, which are checkable against the trace, from subjective judgments. Without the trace you are reading the agent's account of what it did. If the trace lives in the vendor's console and cannot be exported, the account is all you have.

**Could you reconstruct the run six months from now?**

The model version, the prompt, the retrieval index, the tool versions. A result you cannot reconstruct is a story, and a story does not survive a vendor change or a new hire.

**Would the reversal condition fire on a vendor change?**

A 2026 benchmark for long-context agentic instruction following reported strict pass@1 alongside a relaxed variant tolerating one violated control, and found relaxing roughly doubles leader scores — best configuration **36.2% strict pass@1**, still failing nearly two of three tasks. Note what it implies: a vendor can ship a model that passes your relaxed check while failing your real one, and the headline will look fine.

The 2023 NeurIPS MT-Bench paper names why a close comparison needs defending: GPT-4 judges agreed with human preference on more than 80% of comparisons, comparable to human-human agreement, while exhibiting position bias, verbosity bias, and self-enhancement bias, plus "limited reasoning ability." A companion paper showed Vicuna-13B beating ChatGPT on 66 of 80 queries under one evaluator setup. If a vendor change moves your score by less than that margin, you are reading the judge, not the model.

## The migration test

A 2026 study of RAG evaluation metrics puts a floor under your own metric: human evaluators agreed with each other at **Pearson 0.85**. RAGChecker's claim recall near **0.7** was the strongest overall correlation among the tools tested, and the authors warned that high correlation does not establish validity, because input difficulty alone can produce strong correlations.

Use it as a threshold. If a candidate beats another by less than your instrument's noise floor, you do not have a preference, and you should be choosing on everything else: cost, latency, portability, and how long the vendor's roadmap suggests your price holds.

A 2025 survey of software-engineering agents makes the same argument from the other end: benchmark scores should guide rather than determine tool choice, and candidates should be compared on your repository, your language, your context length, your test strength, contamination exposure, latency, and cost. None of those are weights. All of them are yours.

## What to buy on Monday

**Build the interface layer first.** A single module that takes a task and returns a structured result, with one function that swaps the model. It is a day of work and it converts every future comparison into a config change.

**Write the evaluation set before the shortlist.** Thirty questions, from closed work, with the expected answers. Reuse it for every candidate and every future swap.

**Write the reversal conditions.** Numeric, and dated. Include "the vendor changed the model behind the API without notice" — because they will, and you want the trigger to be a rule rather than an argument.

**Log everything you can export.** Prompt, retrieved passages, tool calls with arguments and order, model version, token counts. Storage is cheap; the ability to re-run is not.

**Keep two suppliers warm.** Not as a hedge against failure — as a hedge against you losing the ability to compare. A system you cannot re-evaluate is a system you have already stopped evaluating.

[AUTHOR EXPERIENCE: Replace with your real account — a model or vendor change that cost you more than the migration would have.]

## What this cannot settle

The buy-the-workflow rule is my construction. No published work validates it, and for a high-volume, latency-critical product the modelling cost of a portable interface may exceed the cost of the lock-in it avoids.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And portability has a price. A thin interface layer still needs engineering, still needs testing, and still needs to be maintained when the underlying vendor SDK changes shape. A workflow you can move is not automatically a workflow that is better.

## Where to start this week

1. Find every place your code calls a model directly. Count them.
2. Write the evaluation set for the workflow you care about most.
3. Add a model-version field to your logs and backfill what you can.
4. Write down your reversal conditions, including the vendor-change trigger.
5. Try one swap on a non-critical path and see what breaks.

## Sources

- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; ~42-point fact-check drop from 2 to 150 tool calls; 78.6%→16.7% and 80.0%→57.9%.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; deterministic vs subjective detection; trace as evidence.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; leaderboard overfitting and saturation.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation ≠ validity; two-system comparison.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; strict vs relaxed grading roughly doubling scores.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: scores guide not determine; comparison dimensions including latency and cost.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: metadata-mismatch detection of unread sources as an ownership check.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

If the vendor changed the model tomorrow, how many of your code paths would break?
