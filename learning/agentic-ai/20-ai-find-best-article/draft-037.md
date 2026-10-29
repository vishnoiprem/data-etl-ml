---
title: "Read the Denominator: The Fastest Way to Catch an Inflated AI Score"
subtitle: "One number, one denominator, five minutes — and the questions that reveal whether the score means anything."
tags:
  - ai-evaluation
  - benchmarks
  - llm
  - how-to-evaluate-llm-tools
  - technical-writing
  - ai-research
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1390
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 91
hard_fail: false
distinctness_angle: "Denominator-focused micro-frame — isolates a single element of a score (the denominator) and makes it the entire article, with a worked re-scoring exercise"
sources_count: 9
author_experience_placeholders: 1
---

A score without a denominator is not a number. It is a shape.

It tells you the ratio, never the size. 90% of 10 is 9. 90% of 10,000 is 9,000. The percentage is identical and the meaning is not.

And in AI evaluation, the denominator is where the inflation hides, because the denominator is almost always described somewhere you have to go looking for.

## The five questions about a denominator

**1. What counts as a failure?**

A 2026 benchmark for long-context agentic instruction following reported strict pass@1 alongside a relaxed variant tolerating one violated control, and found that relaxing roughly doubles leader scores. The authors warned that a deployment tolerating one violated control per workflow "has effectively abandoned strictness." Its best configuration scored **36.2% strict pass@1** — still failing nearly two of every three tasks.

Read that twice. The relaxed number is what appears in headlines. The strict number is what happened. The gap between them exceeded most product-to-product differences in the field.

**2. How many failures are tolerated?**

Same source, same point. "Pass@1" means one attempt. But benchmarks vary the attempt count, and each extra attempt multiplies a partial success rate. If a task succeeds on a third try, is that a pass?

**3. What is the denominator — the items attempted or the items possible?**

A system that declines hard tasks has a small denominator and a flattering rate. A system that attempts everything has a large denominator and a lower rate. Both can be honest. Only one is comparable to a competitor who chose differently.

**4. Are the failures weighted?**

One missed control and one missed required step are the same unit here, and they are not the same unit in your week. Nothing in a percentage tells you which.

**5. What was removed before the number was computed?**

Data that was unrunnable, ambiguous, or contested. Errors that crashed the harness. Items where the reference answer was wrong. Every removal makes the rate better and each one may be invisible.

## Why inflation concentrates in the denominator

A metric is a ratio, and a ratio is a lever. To make a system look better, you can improve the numerator or shrink the denominator. Improving the numerator is expensive. Shrinking the denominator is free.

This is not a claim about intent. It is a structural observation about what a rate rewards, and it is the reason a benchmark score can be technically accurate and still misrepresent the deployment.

The 2026 long-context benchmark is the clean example because it published both numbers instead of one. That choice is what made the inflation visible. Most benchmarks publish one, and you cannot know which one it is unless you go and read the grading rule.

## Worked example: re-score a number you already have

Take a score you are about to quote. Call it S, with a reported rate R.

**Step one: find the grading rule.** Search the paper for the words "strict," "relaxed," "partial," "attempt," "at most," and "tolerate." If you find a relaxed variant, note the delta. If the paper reports both, subtract one from the other. In the 2026 benchmark the delta is roughly a factor of two.

**Step two: find the item count.** If the paper says "success rate" without a denominator, treat the number as unusable for comparison until you find the count. A rate on 12 items has a confidence interval wide enough to contain almost any competitor.

**Step three: find the failure definition.** What is a failure — any error, any violated constraint, a failed downstream check? The 2026 long-context benchmark's distinction between strict and relaxed is exactly this, and it is worth roughly half the score.

**Step four: find the exclusions.** Items dropped for being unrunnable, ambiguous, or out of scope. If the count is not stated, assume it is non-zero and treat the score as an upper bound.

**Step five: apply the ratio test.** Multiply R by the number of items to get the absolute count of successes. Ask whether that number is plausible for the task. In the 2026 benchmark, 36.2% strict pass@1 means the best system fails nearly two of every three tasks — a fact that is invisible in the percentage and obvious in the count.

## The second-order question: the judge denominator

If the number came from an LLM judge, the denominator has a second layer: how many comparisons, and how were they selected?

The 2023 NeurIPS MT-Bench paper found GPT-4 as a judge agreeing with human preference on more than 80% of comparisons — comparable to agreement between humans — while naming position bias, verbosity bias, and self-enhancement bias in its own method, plus the limitation "limited reasoning ability." The companion paper, "Large Language Models are not Fair Evaluators," showed the practical magnitude: under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries.

Eighty comparisons. A ranking that flipped because of ordering. The denominator is 80, and 80 is small enough that the ordering effect dominates.

**Ask: how many comparisons, and were the questions selected or curated?** If they were hand-picked, the rate describes the picked set.

## And the numerator's sibling: what the score does not cover

The denominator tells you the size of what was counted. The coverage tells you what was not counted at all.

A 2025 paper on real-world capabilities identified six practical capabilities and found that "Reviewing Work and Data Structuring are not captured at all" by the metrics it evaluated. The paper's argument is that benchmarks "often prioritize abstract notions of correctness over qualities that matter to users."

A 100% score on a well-defined denominator is still a low-information result if review quality was never in the denominator's scope.

## The three-line denominator record

```
METRIC: <what is measured>
DENOMINATOR: <n items, from what population, with what exclusions>
FAILURE RULE: <what counts as failure; how many tolerated>
ABSOLUTE: <R × n = k successes; k failures>
```

Four lines, one sitting, and it converts every score you quote from a shape into a quantity.

## What this cannot settle

The five questions are my reading of the failure modes the literature documents. A careful statistician would add others — confidence intervals, multiple-comparison corrections, selection effects — and the denominator work is a foundation, not a complete audit.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And a published paper may not disclose its denominator at all. When it does not, the honest conclusion is that the number is not comparable, and no amount of reading will change that.

## Where to start this week

1. Pick the last score you quoted and find its denominator. Write it down.
2. Multiply it out. See the absolute number.
3. Search that paper for "strict," "relaxed," and "exclu" to find the grading rule and the removals.
4. If a judge produced the number, find the comparison count and the order-swap test.
5. Add the four-line denominator record to your next memo.

## Sources

- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; strict vs relaxed grading roughly doubling scores; "effectively abandoned strictness."
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *Evaluating LLM Metrics Through Real-World Capabilities* (2025). arXiv:2505.08253. https://arxiv.org/html/2505.08253v1
  - Supports: six practical capabilities; "Reviewing Work" and "Data Structuring" not captured; benchmarks prioritize abstract correctness.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; difficulty confound; correlation ≠ validity; 96-question dataset with wide confidence intervals.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: contamination exposure as a comparison dimension; HumanEval/MBPP to repository-level suites.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% link validity and 80% relevance vs 24.4–76.8% claim accuracy; selection and coverage contrasts.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; saturation and overfitting.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: fabricated-citation counts as an absolute-versus-rate contrast.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

What is the denominator of the last score you quoted?
