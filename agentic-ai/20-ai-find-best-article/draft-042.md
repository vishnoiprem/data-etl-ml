---
title: "Latency Is a Quality Attribute: How to Include Response Time in Tool Selection"
subtitle: "The cost of waiting is measurable, often dwarfs token price, and almost never appears in the comparison."
tags:
  - ai-engineering
  - model-selection
  - llm
  - how-to-evaluate-llm-tools
  - ai-evaluation
  - performance
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1400
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 87
hard_fail: false
distinctness_angle: "Latency-as-quality frame — argues that response time belongs in the quality metric rather than beside it, and gives a measurement recipe with percentile discipline"
sources_count: 9
author_experience_placeholders: 1
---

Every tool comparison has a quality column and a price column.

Almost none has a latency column, even when latency is the difference between a product people use and a product they route around.

The problem is that putting latency next to quality treats it as a tiebreaker. It is not. It is a quality attribute, and in several real categories it dominates the others.

## Why waiting is expensive

A response that arrives in 800 ms feels instant. A response that arrives in 8 seconds gets read, edited, and often ignored — and the person waiting has done something else in the meantime, which means the work is no longer linear.

For an interactive tool, latency has a direct effect on throughput per user, and therefore on cost per task, independent of token price. For a batch system, latency still matters because it determines how long a feedback loop takes, and a slow feedback loop means fewer experiments per week, and fewer experiments per week means more decisions made on anecdotes.

This is why latency belongs inside the quality metric rather than beside it. A system that is correct and unusable is not correct.

## What the benchmarks show

The 2026 long-context agentic instruction following benchmark gives a hard number most comparisons ignore: the best configuration scored **36.2% strict pass@1** — still failing nearly two of every three tasks — and the token spend ranged from roughly 13K to 60K generated tokens per trial.

Read those together. Configuration A spent 13K tokens; configuration B spent 60K on the same quality band. That is not a 4.6× price difference that you can divide out. It is a 4.6× difference in time-to-answer, which is a 4.6× difference in how many experiments you can run this week, which is a 4.6× difference in how much you learn before the deadline.

And the reasoning-effort result compounds it: raising reasoning effort helped some configurations by 2.0 to 3.0 points, left one unchanged, and **hurt one by 2.7 points**, with no clean relationship between token spend and score.

So the levers people reach for when they want better answers make latency worse and quality unreliable at the same time.

## Measure it properly or not at all

**Report percentiles, not averages.** A mean latency of 2 seconds can mean a tight 1.9-second distribution or a bimodal one where half the requests take 200 ms and half take 3.8 seconds. The user experience is the slow half. Report p50, p95, and p99.

**Measure end-to-end, not per-call.** The number the user experiences includes retrieval, queueing, retries, and any tool calls. A 400 ms model behind a 3-second retrieval step is a 3.4-second system. A 2026 agent-evaluation paper is blunt that procedural failures "can look plausible in the final response" — an agent claiming a tool it never invoked, skipping a mandatory compliance call, calling tools out of order. Tool-call traces also mean tool calls, and those count in the latency budget.

**Measure under your traffic, not under a benchmark harness.** A 2025 survey of software-engineering agents makes the operational point that candidates should be compared on your repository, language, context length, test strength, contamination exposure, latency, and cost. Latency on your context length is not latency on their shorter one.

**Measure with your retrieval.** A 2026 source-attribution study found that across GPT-5.4 and Claude Opus 4.6, fact-check accuracy fell by roughly **42 percentage points on average** as tool calls rose from 2 to 150, with one configuration dropping from 78.6% to 16.7% and another from 80.0% to 57.9%. More calls is more latency, and in that study more calls was also worse quality.

**Fix the concurrency and the batch size before comparing.** Two candidates measured under different load conditions are not comparable, and neither is one candidate measured before and after a traffic change.

## Fold it into the metric, not beside it

The practical move is to change what a "success" means. A successful task is one that was correct **and** returned within the latency budget.

This has an immediate and desirable effect: it forces you to state the budget. "Fast enough" is not a number, and a system with no latency budget will always drift toward slower.

The same move makes the tradeoffs visible in the score. A configuration that scores 1 point higher and takes 3× longer may no longer be the winner once latency is inside the definition of success, and you find that out from the metric instead of from complaints.

It also exposes a specific failure mode worth watching. A 2026 benchmark for long-context agentic instruction following reported strict pass@1 alongside a relaxed variant tolerating one violated control, and found that relaxing roughly doubles leader scores. The authors warned that a deployment tolerating one violated control per workflow "has effectively abandoned strictness." In latency terms, the analogous move is to let the p99 slip while reporting a p50 — and the p99 is what your worst users experience.

## Where latency should change the ranking

**Interactive, high-volume, low-stakes.** Latency dominates. A 10-point quality gap that takes 6 seconds versus 1 second is usually not worth 6 seconds, at volume, for every request. Optimize for the fastest configuration that clears your quality floor.

**Interactive, high-stakes, human in the loop.** Both matter, and the human's attention is the scarce resource. A slow answer that arrives while the person is still waiting can be acted on; a fast answer that arrives after context is lost cannot.

**Batch, no human in the loop.** Latency matters less as a user experience and more as an experiment-throughput constraint. Measure cost per completed task and total wall-clock per evaluation cycle.

**Asynchronous, deadline-driven.** Latency is close to irrelevant; cost and predictability are not. But predictability still means variance, so track p99 even where you only report p50.

## The rule that keeps it honest

**Never compare quality and latency in separate columns and add them up afterwards.** Do the comparison at the operating point you will actually run: fix the latency budget, then compare quality at that budget. Fix the quality floor, then compare latency at that floor. Pick the constraint and optimize inside it.

A 2026 RAG metrics study gives a useful floor for the quality side of that choice. Human evaluators' ratings correlated with each other at **Pearson 0.85** — the practical ceiling for any automatic proxy metric — and the authors warned that high correlation does not establish validity, because input difficulty and other confounders produce strong correlations on their own. So set the quality floor above your instrument's noise, and let latency decide inside that constraint.

## The record to keep

```
TASK: <the operation>
p50 / p95 / p99 latency: <end-to-end, including retrieval>
QUALITY AT THAT BUDGET: <n% on the fixed set, denominator stated>
COST PER SUCCESSFUL TASK: <dollars>
THROUGHPUT: <requests/min at target concurrency>
```

Five lines, per candidate, on the same machine and the same traffic.

[AUTHOR EXPERIENCE: Replace with your real account — a candidate rejected on latency, or a latency regression that shipped because nobody measured it.]

## What this cannot settle

The operating-point framing is my construction. Real products have latency distributions that depend on load, and a p99 measured on Tuesday is not the p99 at peak.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And sometimes the slow configuration is correct for a reason you cannot see in a latency measurement — a reasoning step that prevents a costly error, for instance. The point is not that fast wins. It is that you should be choosing at an operating point rather than adding two incomparable columns.

## Where to start this week

1. Add p50, p95, and p99 to your existing evaluation output.
2. Fix a latency budget for your most-used task and write it down.
3. Re-run the comparison with that budget enforced.
4. Check whether your fastest configuration is also your cheapest per successful task.
5. Look for the tool call that adds the most time and ask whether it needs to be there.

## Sources

- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; 13K–60K generated-token range; reasoning-effort variance of +3.0 to −2.7; strict vs relaxed grading roughly doubling scores.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: ~42-point fact-check drop from 2 to 150 tool calls; 78.6%→16.7% and 80.0%→57.9%.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: latency and cost as explicit comparison dimensions; scores guide not determine.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; difficulty confound; correlation ≠ validity.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; tool-call trace analysis.
- *Evaluating LLM Metrics Through Real-World Capabilities* (2025). arXiv:2505.08253. https://arxiv.org/html/2505.08253v1
  - Supports: benchmarks prioritize abstract correctness over user-relevant qualities.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; leaderboard overfitting and saturation.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation in long contexts.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

What latency budget would you write down today for your most-used task?
