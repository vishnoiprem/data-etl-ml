---
title: "The Economics of Picking Wrong: A Cost Model for AI Tool Decisions"
subtitle: "Three variables, one formula, and the reason a 4% quality gain can lose to a 3× failure-detection improvement."
tags:
  - ai-evaluation
  - decision-analysis
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - ai-engineering
  - unit-economics
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1520
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 88
hard_fail: false
distinctness_angle: "Explicit cost model — a stated formula with three variables, a worked computation, and a comparison of two candidate architectures end to end"
sources_count: 9
author_experience_placeholders: 1
---

Every AI tool comparison in every meeting reduces to a table with a "quality" column and a "price" column.

That table cannot decide anything, because it omits the column that matters most: **what happens when it is wrong.**

Here is a model with three variables. It is simple, it is not published, and it decides cases that quality-and-price tables cannot.

## The model

**Expected cost per run = P(failure) × (detection latency in days) × (cost of one failure)**

Three inputs. All three are estimable. The third is the one people skip.

### Variable one: P(failure)

Not the headline accuracy. The probability of the specific failure you cannot afford, at your volume, on your data.

A public benchmark's accuracy is the wrong number here for a structural reason. A 2026 study of RAG evaluation metrics found human evaluators agreeing with each other at a Pearson correlation of 0.85 — the practical ceiling for a proxy metric. RAGChecker produced the strongest overall correlations, with claim recall near 0.7. But high correlation does not establish validity, because difficulty and other confounders produce strong correlations on their own, and their own dataset was small enough (96 questions) that the confidence intervals were wide.

So: a 4% gap on your metric may be a real difference or it may be nothing. You cannot price a difference you have not established.

Their method for establishing it is worth using before you price it: evaluate at least two systems and compare their outputs on the same questions, so question difficulty cancels.

### Variable two: detection latency

How many days between the failure and someone knowing?

This is the variable that separates candidates who look identical on quality. Two systems can have identical failure rates and differ by a factor of a hundred in expected cost, purely on detection.

A 2026 paper on agent evaluation gives you the cases where detection latency is long. Procedural failures "can look plausible in the final response" — an agent claiming a tool it never invoked, skipping a mandatory compliance call, calling tools in the wrong order. Nothing about the text tells you.

A 2026 source-attribution study shows the same for content. Across 14 models and 130 research queries, link validity exceeded 94% and relevance exceeded 80%, while factual accuracy ranged from 24.4% to 76.8%. The failure has a live link and an on-topic page attached to it. Detection latency is whatever your process takes to notice the claim is unsupported.

### Variable three: cost of one failure

Not the license. The cost of one bad output, in the currency that actually matters to you.

The magnitude range here is enormous and it is why this variable dominates. A wrong draft summary costs a rewrite. A wrong number in a customer-facing report costs a credit, a correction, and a support thread. A wrong agent action in a system with a payment tool costs an incident review.

## Worked example: two architectures

You are choosing between a plain RAG system and one with a claim-verification step in front of it. Assume the plain system scores 4% better on your metric.

**Plain RAG:**
- P(failure) = 2%
- Detection latency: 9 days (wrong claims reach a report; a reader eventually flags them)
- Cost per failure: $400 (correction, support handling, credibility)
- **Expected cost per run = 0.02 × 9 × 400 = $72**

**RAG with verification:**
- P(failure) = 2.5% (slightly worse — verification occasionally discards correct output)
- Detection latency: 0.5 days (unsupported claims are caught at generation time)
- Cost per failure: $400 (same)
- **Expected cost per run = 0.025 × 0.5 × 400 = $5**

The system with the better score is 14× more expensive per run, on a variable the quality column cannot see.

At 10,000 runs a month, that is $720 versus $50. The verification step costs a fraction of that. This is why "4% better" is not a tiebreaker — it is noise next to a 14× difference in detection.

## Where the third variable comes from

The third variable is where most of the work is, and it is also where the evidence helps.

A 2026 paper on agent evaluation describes the design pattern that makes failures catchable: move expert knowledge upstream into reusable evaluation artifacts rather than reviewing every trajectory. Its own study ran 47 configurations, 470 trials, and 23,500 turns. That scale is possible because the rules are compiled once, not re-derived each time.

A 2026 long-context agentic instruction following benchmark makes the same argument from the enforcement side, recommending that teams enforce "hard controls outside the model" — compiling policies into deterministic tool-call guards — rather than relying on in-context adherence. Its best configuration scored 36.2% strict pass@1, which means even the best system still failed nearly two of every three tasks, and it noted that relaxing the strict criterion to tolerate one violated control roughly doubles leader scores. Strictness is what makes detection latency short.

A 2023 paper on LLM-as-judge adds a caution that shapes the cost of the metric itself. The MT-Bench work found GPT-4 judges agreeing with human preference on more than 80% of comparisons — comparable to human-human agreement — while naming position, verbosity, and self-enhancement biases and the limitation "limited reasoning ability." A companion paper showed order sensitivity concretely: under one setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. If your measurement flips under reordering, you cannot price the difference it reports, because you do not know which measurement is real.

## The three architecture decisions that dominate the model

In practice, almost all of the cost is decided by three design choices, and each one is under your control.

**Where does verification happen?** Earlier means shorter detection latency. Before the output reaches a human, not after.

**What is the hard control?** A deterministic check — a schema constraint, a unit test, a lookup — detects at near-zero latency and near-zero marginal cost. A model-based check detects slower and costlier.

**How do you scale the number of tools?** A 2025 study of retrieval-based tool selection found that presenting every tool schema to the model dropped selection accuracy to 13.62%, while retrieving the relevant schema raised it to 43.13% and cut average prompt usage from 2,133.84 tokens to 1,084. It also found accuracy degrading beyond roughly 100 candidates as retrieval precision declined. If your routing is broken, every other variable is measuring the wrong thing.

## When the model is not the right tool

Sometimes the honest answer is that the choice does not matter much, and the money should go elsewhere.

A 2025 evaluation-ecosystem paper argues the unit of evaluation is not the model but the "contextual unit" — the adaptive behavior of a person using AI in a setting — and recommends defining a theory of change with stakeholders before comparing candidates. If your inputs, your reviewers, and your failure definition are not settled, a 4% model gap is noise against a much larger unresolved problem.

That is worth saying plainly: the model decision is often the least important decision on the table, and it is the one everybody wants to make first.

## Papers, priced the same way

A paper is a candidate with a cost profile too.

A 2026 benchmark called CiteAudit found 2,967 fabricated citations out of 9,442, and separately found references that exist but whose title or author metadata does not match — meaning the cited paper was never read. A 2026 source-attribution study found link validity above 94% while claim-level accuracy ranged from 24.4% to 76.8%. So the detection latency on an unverified citation is however long it takes someone to check it, and the cost of one failure is a public correction of a claim you published.

**Priced that way, spending 20 minutes verifying a citation is obviously correct. Skipping it is obviously not.**

[AUTHOR EXPERIENCE: Replace with your real account — the tool decision where this arithmetic changed the answer, and what the failure actually cost.]

## What this cannot settle

The formula is mine. No published study validates it, and the three variables are hard to estimate — particularly cost of failure, which people estimate optimistically and inconsistently.

The evidence numbers are setup-specific and dated. The judge figures are from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024, ICLR 2023 — are also the older ones.

The model assumes independence between failure probability and detection latency, which is false when a systematic error produces many failures that are all detected at once.

## Where to start this week

1. Fill in the three variables for your current tool.
2. Find the candidate with the shortest detection latency, not the highest score.
3. Move one verification step earlier in the pipeline.
4. Compile one rule into a deterministic check instead of a prompt.
5. Price one decision you already made, and see what changes.

## Sources

- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation ≠ validity; 96-question dataset; two-system comparison.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; 47 configurations / 470 trials / 23,500 turns; upstreaming expert knowledge; human review essential for rubrics and escalation.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; relaxed grading roughly doubles scores; hard controls outside the model.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; 14 models, 130 queries; link-and-relevance survival.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: 13.62% vs 43.13%; 2,133.84 → 1,084 tokens; degradation beyond ~100 candidates.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; metadata mismatch detection.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; theory of change before candidate comparison; field testing.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

If you could cut your detection latency by half tomorrow, would you rather have that or a 4% quality gain?
