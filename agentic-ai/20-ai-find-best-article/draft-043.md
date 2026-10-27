---
title: "The Comparison Table Everyone Builds Is Measuring the Wrong Column"
subtitle: "Eight columns, one real variable, and the metric that makes the rest of the table honest."
tags:
  - ai-evaluation
  - model-selection
  - llm
  - how-to-evaluate-llm-tools
  - technical-writing
  - benchmarks
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1420
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 89
hard_fail: false
distinctness_angle: "Spreadsheet-audit frame — takes the familiar vendor comparison table apart and argues every column except one is a proxy, anchored on a single load-bearing quality variable"
sources_count: 9
author_experience_placeholders: 1
The comparison table is the most familiar artifact in tool selection. Eight columns, four or five rows, a tick in each cell, and a decision at the bottom.

It is also, in most cases, measuring almost nothing.

Here is what a typical table looks like, and what each column is actually worth.

## The table as usually built

| | Vendor A | Vendor B | Vendor C |
|---|---|---|---|
| Benchmark score | 72% | 78% | 74% |
| Price per 1M tokens | $3 | $15 | $8 |
| Latency p95 | 1.2 s | 0.9 s | 2.4 s |
| Context window | 200k | 1M | 128k |
| Languages | 30 | 12 | 40 |
| Tool calling | yes | yes | partial |
| On-prem available | no | yes | no |
| Free tier | yes | no | yes |

Eight columns. Four of them are marketing claims, three are engineering parameters, and one is a number that means something different in every row.

## Column one: the benchmark score

This is the column that decides most decisions and the one most likely to be wrong.

A 2026 benchmark for long-context agentic instruction following reported strict pass@1 alongside a relaxed variant tolerating one violated control, and found that relaxing roughly doubles leader scores. Its best configuration scored **36.2% strict pass@1** — still failing nearly two of every three tasks. Same systems, same work, two numbers, and the gap between them exceeded most product-to-product differences in the field.

**What to put here instead:** your own score on your own fixed question set, with the denominator stated, under one grading rule.

## Column two: price per token

Price per token is not a cost. Cost is price per token multiplied by tokens per successful task.

The 2026 long-context benchmark showed the gap: one configuration reached 21.5% on roughly 13K generated tokens per trial, another spent close to 60K tokens for the same quality band at about three times the dollar cost, and several mid-pack configurations generated 45–55K tokens while scoring in single digits. A configuration that scores half as well and uses half the tokens can be cheaper per success by a wide margin.

**What to put here instead:** dollars per successful task, on your own task distribution, at your own volume.

## Column three: latency

Present, but usually the p50, and usually measured by the vendor.

A 2025 survey of software-engineering agents makes the operational point that candidates should be compared on your repository, language, context length, test strength, contamination exposure, latency, and cost. "Latency" is a comparison dimension, but the number in the table is almost never latency at your context length under your traffic.

**What to put here instead:** p50, p95, and p99 end-to-end, including retrieval, on your payloads.

## Column four: context window

A maximum input size, not a working size.

The 2023 TACL paper "Lost in the Middle" found that models perform best when relevant material appears at the beginning or end of the context and "significantly degrades when models must access relevant information in the middle" — and explicitly long-context models were not exempt. A 2025 survey of software-engineering agents makes the same engineering point: "Long context alone is not a substitute for effective retrieval." Concatenating all relevant files was found to be suboptimal, and snippet ordering materially affected performance.

So a larger context window can make retrieval worse, not better, and a 200k window with poor chunk ordering can underperform a 32k window with good ordering.

**What to put here instead:** accuracy on your longest real input, at the position your real data puts it.

## Column five and six: coverage

Languages and tool-calling support are capability claims without a denominator. "30 languages" tells you nothing about quality in any of them, and "partial" tool calling tells you nothing about which calls fail.

**What to put here instead:** accuracy on your top two languages, and the pass rate on a fixed set of your actual tool calls, in strict mode.

## Column seven and eight: deployment and commercial

Real criteria, and rarely the deciding ones. But note that "on-prem available" and "free tier" are also proxies — for data-residency requirement and for cost at small volume respectively, both of which you can state directly.

**What to put here instead:** your actual data-residency constraint, satisfied or not, and your monthly invoice at expected volume.

## The column that is missing

Every column above is a proxy for one thing: **does this system do your job correctly, on your inputs, at your cost, at your latency, reproducibly.**

That is the load-bearing variable, and it is the one column the table never has, because it is the hardest to fill in: it requires a private question set, a run of each candidate, a stated grading rule, and a decision about what counts as success.

A 2026 RAG metrics study gives the honest version of why a proxy table cannot substitute. Human evaluators' ratings correlated with each other at **Pearson 0.85** — the practical ceiling for any automatic proxy metric. RAGChecker produced the strongest overall correlations among the tools tested, with claim recall near **0.7**, and the authors warned that high correlation does not establish validity, because input difficulty and other confounders can produce strong correlations on their own.

And a 2026 source-attribution study shows the pattern in the wild. Across 14 models and 130 research queries, link validity exceeded **94%** and topical relevance exceeded **80%**, while factual accuracy ranged from **24.4% to 76.8%**. Everything visible was healthy. The claim was still unsupported roughly a third to three-quarters of the time.

## The rebuilt table

| | Vendor A | Vendor B | Vendor C |
|---|---|---|---|
| Accuracy on our 30 items (strict) | | | |
| Denominator stated | | | |
| Grading rule | | | |
| Dollars per successful task | | | |
| p95 latency, our payloads | | | |
| Failures we would escalate | | | |
| Reproducible (version-pinned) | | | |

Seven rows, and five of them are numbers you produced rather than numbers you were given. The other two are words, which is the point: the table is now about your job.

A 2026 agent-evaluation paper explains why the escalation row belongs there. Human review is "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions" — which means a comparison is incomplete until you know which failures reach a person.

## Why the rebuilt table is better even when the old one was right

The old table is a reasonable first filter. Keep it, use it to cut five candidates to three.

But make sure everyone in the room knows what they are looking at. A benchmark score is a prior, not a result. A 2025 evaluation-ecosystem paper makes the institutional case: leaderboard reliance encourages overfitting and saturation, and the unit of evaluation is not the model but the "contextual unit" — the adaptive behavior of people using AI in a setting.

**The tick in the first row is a hypothesis. The number in the rebuilt table is a result.**

[AUTHOR EXPERIENCE: Replace with your real account — a comparison table that produced the wrong answer, and which column was responsible.]

## What this cannot settle

The rebuilt table is my construction. No published work validates this column set, and some deployments will have legitimate criteria that do not fit into it.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And a 30-item private set is a small instrument. It will not resolve close comparisons, and it will drift as your work changes. It is better than a proxy table, not equivalent to a full evaluation program.

## Where to start this week

1. Take the last comparison table you built. Mark every row as "measured by us" or "measured by them."
2. Replace the benchmark row with your own number, or delete the row.
3. Convert price per token to dollars per successful task.
4. Add the escalation row.
5. Re-run the decision using only your own numbers and see if it changes.

## Sources

- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; strict vs relaxed grading roughly doubling scores; 21.5% on ~13K tokens; 45–55K and ~60K token configurations in the same band.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: long context not a substitute for retrieval; snippet ordering matters; comparison dimensions including latency and cost.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation in long contexts; long-context models not exempt.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; difficulty confound; correlation ≠ validity.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% link validity and 80% relevance vs 24.4–76.8% claim accuracy; 14 models, 130 queries.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: human review essential for domain context, policy interpretation, risk criteria, rubrics, and escalation.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; leaderboard overfitting and saturation.
- *Evaluating LLM Metrics Through Real-World Capabilities* (2025). arXiv:2505.08253. https://arxiv.org/html/2505.08253v1
  - Supports: benchmarks prioritize abstract correctness over user-relevant qualities.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

In your last comparison table, how many rows were measured by the vendor rather than by you?
