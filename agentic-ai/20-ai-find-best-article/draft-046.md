---
title: "The Cost of Being Wrong: How to Put a Number on Errors Before You Pick a Tool"
subtitle: "Turn quality into money, compare tools on expected loss, and stop arguing about whose accuracy is better."
tags:
  - ai-evaluation
  - model-selection
  - llm
  - how-to-evaluate-llm-tools
  - data-engineering
  - risk
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1415
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 89
hard_fail: false
distinctness_angle: "Expected-loss frame — converts accuracy differences into money so that candidates with different error severities can be compared, with a worked expected-loss table"
sources_count: 9
author_experience_placeholders: 1
---

Two candidates differ by 4 percentage points on your evaluation set. Is that worth anything?

It depends entirely on what a wrong answer costs, and almost nobody computes that number, which is why the argument goes to whoever is most confident.

## Four inputs, one number

To convert an accuracy difference into money, you need four figures:

**Volume.** How many times the system produces an output per month. 100,000 decisions a month is a different instrument from 100.

**Error rate.** The gap between the candidates on your own set. If A is 88% and B is 84%, the difference is 4 points — which is 4,000 extra errors per month at 100,000 volume, before you weigh severity.

**Error severity.** Not one number: three. A minor error, a normal error, a severe error. A wrong summary a reviewer catches is not a wrong summary a customer acts on.

**Detection rate.** The fraction of errors caught before they cause harm. This is the most neglected input, because it is the one you control: review, deterministic checks, confidence thresholds, escalation paths.

The result is an expected loss per month, and it is the only comparison figure that matters when severity differs between candidates.

## Why severity is usually not uniform

Most accuracy metrics assume every error costs the same. That assumption is wrong in a specific, common way: **the errors are not distributed uniformly, and the errors that survive detection are the expensive ones.**

Here is the argument from the literature.

A 2026 agent-evaluation paper is blunt that procedural failures "can look plausible in the final response" — an agent claiming a tool it never invoked, skipping a mandatory compliance call, calling tools out of order. It separates deterministic detections, which are checkable against the trace and objective once the trace is available, from subjective judgments. The structural point: errors that are invisible in the output are exactly the errors a review process is most likely to miss, and those are frequently the severe ones.

A 2026 benchmark for long-context agentic instruction following reported strict pass@1 alongside a relaxed variant tolerating one violated control, and found that relaxing roughly doubles leader scores — best configuration **36.2% strict pass@1**, still failing nearly two of every three tasks. A violated control is not a stylistic slip; it is a policy or process breach, and it is the kind of error that becomes severe downstream.

And a 2025 paper on real-world capabilities found that "Reviewing Work and Data Structuring are not captured at all" by the metrics it evaluated — benchmarks "often prioritize abstract notions of correctness over qualities that matter to users." Reviewing is where severe errors get caught. If your evaluation set has no review items, your error severity model has no evidence behind it.

## The expected-loss table

```
Volume per month:                  100,000
Candidate A error rate:            12%
Candidate B error rate:            16%

Error severity (monthly cost per occurrence):
  Minor      $1        detected 80%   →  $0.20 expected
  Normal     $20       detected 60%   →  $8.00 expected
  Severe     $400      detected 20%   → $320.00 expected

A: 12,000 errors → 2,400 minor, 9,600 normal, 0 severe (assumption: no severe errors)
   Monthly expected loss: 2,400 × $0.20 + 9,600 × $8.00 = $480 + $76,800 = $77,280

B: 16,000 errors → same split, plus 1 severe per 1,000 outputs
   Monthly expected loss: $81,920 + 100 severe × $320 = $81,920 + $32,000 = $113,920
```

The 4-point accuracy difference costs $36,640 more per month, and most of that gap comes from the severe errors — a small fraction of the failures. A tool that scores 4 points worse but produces fewer undetected severe errors can be the cheaper choice. **You cannot see that from an accuracy number.**

The arithmetic above is illustrative, not a measurement. But the structure is what matters: severity and detection are separate axes, and both belong in the comparison.

## Where the inputs come from

**Volume** is easy and is usually wrong. People estimate it from memory. Pull the actual count from logs.

**Error rate** comes from your own set. A 2026 RAG metrics study gives the floor for how much you can trust a proxy: human evaluators' ratings correlated with each other at **Pearson 0.85**, the practical ceiling for any automatic proxy metric, and high correlation does not establish validity because input difficulty and other confounders can produce strong correlations on their own. If your 4-point difference is inside that noise, the expected-loss calculation is decoration.

**Severity** comes from post-mortems, not from a spreadsheet. Take the last ten incidents and what each cost. A 2026 source-attribution study shows the pattern of invisible failure clearly: link validity above **94%** and topical relevance above **80%**, while factual accuracy ranged from **24.4% to 76.8%**. Everything visible was healthy; the claim was still unsupported a third to three-quarters of the time. Whatever your analogue is, it is invisible in the surface check.

**Detection rate** comes from your own pipeline. Measure it: take a known set of seeded errors and see how many get caught before harm.

## The comparison that comes out

| | Candidate A | Candidate B |
|---|---|---|
| Error rate | 12% | 16% |
| Errors per month | 12,000 | 16,000 |
| Undetected severe errors / month | 0 | 100 |
| Monthly expected loss | $77,280 | $113,920 |
| Monthly inference cost | $X | $Y |
| **Monthly total cost of ownership** | **$X + 77,280** | **$Y + 113,920** |

One number per candidate, and the number includes inference cost so the trade is explicit. A 2026 long-context benchmark showed why the cost side needs care: one configuration reached 21.5% on roughly 13K generated tokens per trial, another spent close to 60K tokens for the same band at about three times the dollar cost. Raising reasoning effort helped some configurations by 2.0 to 3.0 points, left one unchanged, and hurt one by **2.7 points**. Cost per token is not cost per success, and cost per success is not cost of ownership.

## The three questions that turn this into a decision

**Do severe errors exist in this task at all?** If no, collapse to one severity and the calculation gets simpler.

**Can you raise detection rather than lower error rate?** Review capacity, deterministic guards, escalation. A 2026 long-context benchmark recommends enforcing "hard controls outside the model," compiling policies into deterministic tool-call guards rather than relying on in-context adherence. A 2026 agent-evaluation paper makes the same argument from the evaluation side: human review is "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions." Moving detection from 20% to 60% can beat any accuracy improvement available from switching vendors.

**Is the error rate gap even real?** Swap the order of your judge, control for length, change judge family. The 2023 NeurIPS MT-Bench paper found GPT-4 as a judge agreeing with human preference on more than 80% of comparisons while naming position bias, verbosity bias, and self-enhancement bias, plus "limited reasoning ability." The companion paper showed that under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. A 4-point gap from a single-order comparison is not an input to this model.

## What this cannot settle

The expected-loss structure is my construction. No published work validates this specific calculation, and the numbers above are illustrative placeholders with plausible shapes, not measurements of any real system.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And severity is not a stable number. It changes with regulation, customer expectations, and how visible a failure becomes. The memo should carry a date on the severity assumption and a trigger for revisiting it.

## Where to start this week

1. Pull the real monthly volume from logs.
2. Find the last ten incidents and what each cost.
3. Pick one candidate and compute its expected monthly loss.
4. Check whether raising detection is cheaper than switching tools.
5. Write the severity assumption and the date you will revisit it.

## Sources

- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; deterministic vs subjective detection; human review essential for domain context, risk criteria, and escalation.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; strict vs relaxed grading roughly doubling scores; 21.5% on ~13K tokens; 45–55K and ~60K token configurations; reasoning-effort variance; hard controls outside the model.
- *Evaluating LLM Metrics Through Real-World Capabilities* (2025). arXiv:2505.08253. https://arxiv.org/html/2505.08253v1
  - Supports: "Reviewing Work" and "Data Structuring" not captured; benchmarks prioritize abstract correctness.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; correlation ≠ validity; difficulty confound.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% link validity and 80% relevance vs 24.4–76.8% claim accuracy.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: comparison dimensions including latency and cost; scores guide not determine.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; leaderboard overfitting and saturation.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

What did the last ten incidents in your system actually cost?
