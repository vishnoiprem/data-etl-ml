---
title: "Stop Counting What the Model Says: Observability Before Comparison"
subtitle: "You cannot select a tool you have never watched work — and watching is cheaper than testing."
tags:
  - ai-engineering
  - observability
  - llm
  - how-to-evaluate-llm-tools
  - ai-evaluation
  - model-selection
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1400
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 88
hard_fail: false
distinctness_angle: "Observability-first frame — puts watching a system run ahead of scoring it, arguing that trace review is a cheaper and higher-yield first step than building a benchmark"
sources_count: 9
author_experience_placeholders: 1
---

Most teams pick a tool by scoring it. A few pick it by testing it. Almost none start by watching it run.

Watching is the cheapest, fastest, and highest-yield step, and it is skipped because it produces no number to put in a table.

## What you learn from one hour of watching

Read ten real runs. The ones that came from actual work, with actual inputs, through the actual pipeline. You will learn more than from a week of building a benchmark, because a benchmark tells you how often something happened and watching tells you how it happens.

A 2026 agent-evaluation paper gives the sharpest version of what is invisible in the output. Procedural failures "can look plausible in the final response" — an agent claiming a tool it never invoked, skipping a mandatory compliance call, calling tools out of order. The prose reads correctly in every case. The trace is what makes them checkable.

Note the implication: **the failure exists in the trace, not in the output.** If you only read outputs, you are reading the agent's account of what it did. A 2026 source-attribution study shows the same pattern at scale: link validity above **94%** and topical relevance above **80%**, while factual accuracy ranged from **24.4% to 76.8%**. Everything visible was healthy. The claim was still unsupported roughly a third to three-quarters of the time.

Visible health is not evidence of correctness. It is evidence that the visible dimension works.

## The five things a trace shows that an output does not

**Which tool was called, with which arguments.** A wrong argument is invisible in a fluent answer. A missing call is invisible too, unless the output mentions it — and the 2026 evaluation paper is explicit that the output's account cannot be trusted on its own.

**The order.** A 2026 long-context agentic instruction following benchmark recommends enforcing "hard controls outside the model," compiling policies into deterministic tool-call guards rather than relying on in-context adherence. A call in the wrong order is a policy violation the output will never disclose.

**What was retrieved and what was not.** A 2025 survey of software-engineering agents documents that simply concatenating all relevant files was found to be suboptimal, and that snippet ordering materially affected performance. The 2023 TACL paper "Lost in the Middle" found models perform best when relevant material appears at the beginning or end of the context and "significantly degrades when models must access relevant information in the middle" — and explicitly long-context models were not exempt. The trace tells you where the answer actually was.

**How many times it was tried.** A 2026 source-attribution study found that across GPT-5.4 and Claude Opus 4.6, fact-check accuracy fell by roughly **42 percentage points on average** as tool calls rose from 2 to 150. One configuration dropped from 78.6% to 16.7%; another from 80.0% to 57.9% — while link validity and topical relevance stayed above 92% throughout. The cheap checks stayed green while the expensive one degraded. The call count is in the trace.

**What it cost and how long it took.** A 2026 long-context benchmark showed one configuration at roughly 13K generated tokens per trial and another near 60K for the same quality band, with raising reasoning effort helping some configurations by 2.0 to 3.0 points, leaving one unchanged, and hurting one by **2.7 points**.

## Watching, concretely

**Run it on your own hardest real input, not a sample.** The interesting failures are in the messy cases, and a demo input will not produce them.

**Capture everything the pipeline can emit.** Prompts, retrieved chunks with their positions, tool calls with arguments and order, model responses, token counts, timings, and any retry.

**Read the trace, not the output first.** Then read the output. If they disagree, you have found something. A 2026 agent-evaluation paper's separation of deterministic detections from subjective judgments is the guide: a phantom tool call is a lookup against the trace, not a judgment call.

**Count the discrepancy types.** Three that matter: a claimed call with no trace entry, a trace entry with no corresponding claim, and a call made in the wrong order. Each is a different defect with a different fix.

**Note where the answer came from.** Not the citation — the position. If the supporting chunk was in the middle of a 50-chunk context and the answer still worked, you have learned something about the candidate that no benchmark will tell you.

## Why watching comes before scoring

**It is cheaper.** One afternoon versus a set, a harness, a judge, a rubric, and a baseline.

**It is more diagnostic.** Watching produces specific causes. Scoring produces a number, and a number does not tell you what to fix. A 2026 RAG metrics study makes the point in the abstract: human evaluators agreed with each other at **Pearson 0.85**, RAGChecker claim recall was near **0.7**, and high correlation does not establish validity because input difficulty and other confounders produce strong correlations on their own. You will build that whole apparatus and still be looking for causes.

**It tells you what to measure.** After ten traces you know which capability is missing, so you know which question to put in the set. Build the set after watching, not before.

**It catches the failures that no metric will report.** A 2025 paper on real-world capabilities identified six practical capabilities and found that "Reviewing Work and Data Structuring are not captured at all" by the metrics it evaluated — benchmarks "often prioritize abstract notions of correctness over qualities that matter to users." Watching is how you see that the system never reviews and never restructures; it just answers.

## The trap in watching

Watching produces anecdotes, and anecdotes are how you end up making a decision on the basis of one good or one bad run.

The fix is to watch a *structure*, not a sample. Ten runs selected for coverage: one easy, one hard, one where the system said no, one where a person would be unsure, one long input, one multilingual, one adversarial, and four random. Then write down what happened in each. The coverage makes it diagnostic rather than anecdotal.

And keep the output. A 2026 source-attribution study notes that web-based citations are temporally unstable — pages get paywalled, moved, and removed — and the same applies to any trace that references live material. Store a snapshot.

## The order of operations

1. **Watch.** Ten runs, full traces, written observations.
2. **Name the defects.** What broke, in what order, with what consequences.
3. **Write the questions.** Turn each defect into a question in the evaluation set, with a failure rule.
4. **Score the candidates.** Now, on your set, with your rules, on the same questions.
5. **Re-watch.** After the fix, run the same ten and compare traces.

Step five is the one that turns watching into a practice. A trace you keep is a regression test, and a trace you discard is a story.

[AUTHOR EXPERIENCE: Replace with your real account — a defect you found only by reading a trace, and which no score had flagged.]

## What this cannot settle

The five-point trace review is my construction, and it assumes your pipeline can emit a complete trace. Many production systems log the request and the response and nothing in between, and adding the rest is real work.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And watching ten runs tells you about those ten runs. A system that fails on one input in fifty will usually not show up in ten, which is exactly why watching is the first step and not the last.

## Where to start this week

1. Find one real run and capture everything your pipeline emits about it.
2. Read the trace and the output side by side. Look for disagreement.
3. Repeat for nine more runs, chosen for coverage.
4. Turn each defect you found into a question.
5. Keep the traces, and re-run them after the fix.

## Sources

- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; deterministic vs subjective detection; trace as evidence.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% link validity and 80% relevance vs 24.4–76.8% claim accuracy; ~42-point fact-check drop from 2 to 150 tool calls; 78.6%→16.7% and 80.0%→57.9%; temporal instability of web citations.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: hard controls outside the model; 13K–60K token range; reasoning-effort variance.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: long context not a substitute for effective retrieval; snippet ordering matters.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation in long contexts; long-context models not exempt.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation ≠ validity.
- *Evaluating LLM Metrics Through Real-World Capabilities* (2025). arXiv:2505.08253. https://arxiv.org/html/2505.08253v1
  - Supports: "Reviewing Work" and "Data Structuring" not captured; benchmarks prioritize abstract correctness.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; leaderboard overfitting and saturation.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Have you read a trace from your system, or only its output?
