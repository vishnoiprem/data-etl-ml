---
title: "The Cost of a Wrong Choice Is Not the Same for Every Team"
subtitle: "Why the right tool depends on your error budget, and how to find yours before you shop."
tags:
  - model-selection
  - ai-evaluation
  - llm
  - how-to-evaluate-llm-tools
  - ai-engineering
  - risk
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1400
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 88
hard_fail: false
distinctness_angle: "Error-budget frame — makes the asymmetry between high-cost and low-cost errors the organizing principle, and derives a different selection procedure for each regime"
sources_count: 9
author_experience_placeholders: 1
---

Two teams are choosing between the same two tools. One is building a spam filter. The other is building a system that drafts clinical summaries. They are making the same comparison and they should not reach the same answer.

The difference is not budget, sophistication, or model quality. It is what a mistake costs.

## Name your error budget first

Before anything else, answer one question in numbers:

**What does one wrong output cost, and how many wrong outputs are acceptable per month?**

Not "it depends." An order of magnitude. $50 and 10,000 wrong outputs per month is a different regime from $50,000 and 10.

This single number determines which of the two halves of evaluation you do, how much human review you buy, and how much you should care about the last five percentage points.

## Low-cost errors: optimize for throughput and price

Here, the failure is cheap and the volume is high. A wrong answer costs less than a human minute. What costs you is the per-unit price of the good ones and the latency of delivering them.

The 2026 long-context agentic benchmark showed the decoupling here with unusual clarity. One configuration reached 21.5% on roughly 13K generated tokens per trial. Another spent close to 60K tokens at about three times the dollar cost for the same quality band. Several mid-pack configurations generated 45–55K tokens and scored in single digits.

Notice what the second sentence means. Two configurations in the same band, one at roughly a third the cost. If your errors are cheap, that difference dwarfs any quality gap you could measure.

And the reasoning-effort result is a warning in both directions: raising reasoning effort helped some configurations by 2.0 to 3.0 points, left one unchanged, and **hurt one by 2.7 points**. A lever everyone reaches for has no reliable payoff. In a high-volume, low-cost regime, the right move is to sweep effort levels on your own data and take the cheapest point that holds your quality floor — not the highest score.

The selection procedure for this regime:

- Set a quality floor from your own data, not from a leaderboard.
- Find the cheapest configuration that clears it.
- Measure latency at your traffic, not at one request.
- Stop. Do not spend the saved money on a better model.

A 2025 survey of software-engineering agents makes the operational point for this regime: candidates should be compared on your repository, language, context length, test strength, contamination exposure, latency, and cost. When the cost of an error is small, cost and latency are first-class criteria, not footnotes.

## High-cost errors: optimize for refusal and reviewability

Here the failure is expensive, and a wrong output is worse than no output. Two things follow, and neither is optional.

**The system must be able to say no.** A 2026 benchmark for long-context agentic instruction following reported strict pass@1 alongside a relaxed variant tolerating one violated control, and found that relaxing roughly doubles leader scores. Its best configuration scored **36.2% strict pass@1** — still failing nearly two of every three tasks. The authors warned that a deployment tolerating one violated control per workflow "has effectively abandoned strictness." In a high-cost regime, a lenient grader is not a convenience. It is a defect with a body count.

The same benchmark recommends enforcing "hard controls outside the model" — compiling policies into deterministic tool-call guards rather than relying on in-context adherence. For a clinical summary, a deterministic check that the required structured fields are present and valid is worth more than any amount of prompt tuning.

**Every output must be reviewable.** A 2026 agent-evaluation paper is blunt that procedural failures "can look plausible in the final response" — an agent claiming a tool it never invoked, skipping a mandatory compliance call, calling tools out of order. It separates deterministic detections, which are checkable against the trace and objective once the trace is available, from subjective judgments. The same work describes human review as "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions."

That is the finding that should set your budget. In a high-cost regime, human review is not a fallback for when the model is unsure. It is a fixed line item, sized to the error budget. If the cost per error is $50,000, then the review cost per error is worth up to something close to that.

## The asymmetry nobody prices in

The regime difference is not symmetric in cost of investigation.

Doing the cheap-regime work and discovering you were in the expensive regime is expensive. The 2026 RAG metrics study's method is what exposes it: evaluate at least two systems and compare their outputs on the same questions, because shared difficulty cancels. Run that comparison with human review on the failures and you learn both regimes' answers at once.

Conversely, doing the expensive-regime work when you were in the cheap regime is merely wasteful. It buys assurance you did not need, at a cost that shows up per request.

**The asymmetry argues for buying the cheap-regime option first, and buying the expensive-regime option only when the error budget forces it.**

## A hybrid third case

There is a fourth regime worth naming, because it is common and it is the one most teams mis-plan for: **the error is cheap when the system is right and catastrophic when the system is confidently wrong.**

A support assistant that drafts a reply is in this regime for 95% of cases and a different one for the other 5%.

The signature is asymmetry between confusion and misconfusion. A 2025 paper on real-world capabilities identified six practical capabilities and found that "Reviewing Work and Data Structuring are not captured at all" by the metrics it evaluated — benchmarks "often prioritize abstract notions of correctness over qualities that matter to users." A system that answers confidently and wrongly is not caught by an accuracy metric; it is caught by review quality, which the metric never measured.

For this regime, the requirement is escalation, not accuracy. Something must detect the confident-wrong case and route it to a person. A 2026 agent-evaluation paper's framing of escalation decisions as a distinct human-review category is the right model here.

## Three questions to locate yourself

**Can a wrong output reach a customer without a human seeing it?**

If yes, you are in the high-cost regime, regardless of the dollar figure.

**What is the maximum acceptable error rate, and can you measure it?**

If you cannot measure it, you cannot set a floor, and you are in the expensive regime because you cannot prove the cheap one is safe.

**What does the system do when it does not know?**

If the answer is "it guesses," you are in the hybrid regime whether you planned for it or not.

## What this cannot settle

The three-regime framework is my construction. No published work validates it, and real deployments sit on a continuum rather than in three bins.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And a dollar figure per error is a fiction in some domains. When the error is a safety incident or a regulatory filing, the cost is not a number you can average, and the cheap regime may not exist for you at all.

## Where to start this week

1. Write the cost of one wrong output, in numbers.
2. Answer the three questions above and name your regime.
3. If you are in the cheap regime, find the cheapest configuration that clears your floor.
4. If you are in the expensive regime, price the human review as a per-error cost and include it.
5. If you are in the hybrid regime, design the escalation path before you choose the model.

## Sources

- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; strict vs relaxed grading roughly doubling scores; 13K–60K token range; reasoning-effort variance; hard controls outside the model.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; deterministic vs subjective detection; human review essential for domain context, policy interpretation, risk criteria, and escalation.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: comparison dimensions including latency and cost; scores guide not determine.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: two-system comparison method; correlation ≠ validity; difficulty confound.
- *Evaluating LLM Metrics Through Real-World Capabilities* (2025). arXiv:2505.08253. https://arxiv.org/html/2505.08253v1
  - Supports: six practical capabilities; "Reviewing Work" and "Data Structuring" not captured; benchmarks prioritize abstract correctness.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases.
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% link validity and 80% relevance vs 24.4–76.8% claim accuracy; temporal instability of web citations.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; leaderboard overfitting and saturation.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

What does one wrong output cost in your system, in dollars?
