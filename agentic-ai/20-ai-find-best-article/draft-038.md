---
title: "Your Eval Set Is Worth More Than Your Model Choice"
subtitle: "The asset that compounds while everything else churns — and how to build one in an afternoon."
tags:
  - ai-evaluation
  - data-engineering
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - ai-engineering
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1420
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 90
hard_fail: false
distinctness_angle: "Asset-accumulation frame — treats the evaluation set as compounding capital, contrasting it with the perishable model score, and giving a build recipe with a versioning scheme"
sources_count: 9
author_experience_placeholders: 1
---

Here is an asymmetry that should shape how you spend your next week.

The model score you spend three days obtaining will be stale in three months. The evaluation set you build in an afternoon will still be useful in three years, and it will get more useful every time you use it.

One is a photograph. The other is a measurement instrument.

## What the literature says about the instrument

A 2026 study of RAG evaluation metrics gives the number that should set your expectations. Human evaluators' ratings correlated with each other at a **Pearson correlation of 0.85** — the practical ceiling for any automatic proxy metric. RAGChecker produced the strongest overall correlations among the tools tested, with claim recall near **0.7**. But the authors' warning is the load-bearing part: high correlation does not establish validity, because input difficulty and other confounders can produce strong correlations on their own.

RAGChecker claim recall near 0.7 might be tracking question difficulty or answer extractability rather than retrieval quality.

Now notice what this means for a selection decision. If your instrument has a correlation ceiling of 0.85 against human preference, then:

- A difference smaller than that is not a difference you have measured.
- The instrument's own properties — how it treats difficulty, whether it needs reference answers — determine which comparisons it can make at all.
- Improving the instrument improves every future decision more than picking a marginally better model once.

The 2026 metrics study also found that faithfulness and hallucination metrics correlated weakly as overall metrics, attributed partly to their lack of access to reference answers, and that one moderation metric did not correlate with the reference scores at all. Instrument design, not just instrument choice, is where the return is.

## What the set buys you

**It makes two-system comparison possible.** The 2026 study's own recommendation: evaluate at least two systems and compare their outputs on the same questions. Shared difficulty cancels. This is a one-afternoon change to most evaluation code, and it converts an ambiguous score into a diagnostic. You can only do it if you have a shared set.

**It defends against the failures a score cannot show.** A 2026 benchmark for long-context agentic instruction following reported strict pass@1 alongside a relaxed variant tolerating one violated control, and found that relaxing roughly doubles leader scores — best configuration **36.2% strict pass@1**, still failing nearly two of every three tasks. A set built on your own tasks, with your own failure definition, does not get inflated when someone else relaxes the grader.

**It exposes judge dependence.** The 2023 NeurIPS MT-Bench paper found GPT-4 as a judge agreeing with human preference on more than 80% of comparisons — comparable to human-human agreement — while naming position bias, verbosity bias, and self-enhancement bias, plus "limited reasoning ability." The companion paper showed the stakes: under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. With your own set, you can run the order-swap test yourself in an afternoon and see whether your candidate survives it.

**It surfaces coverage gaps.** A 2025 paper on real-world capabilities identified six practical capabilities and found that "Reviewing Work and Data Structuring are not captured at all" by the metrics it evaluated — benchmarks "often prioritize abstract notions of correctness over qualities that matter to users." A set you build from your own work will contain the capabilities you need, because you will have written the questions.

## The build

**Start from closed work, not from a task description.** Twenty-five to thirty items drawn from work already finished. The questions come with answers attached, which is what makes them usable for automated proxies.

**Include the hard ones.** The set's power comes from being representative, and representative means it contains the messy inputs, the ambiguous cases, and the ones you already know are hard. A set of easy items measures nothing.

**Include the capability gaps.** If you need the system to review a document and decide whether it is wrong, there must be items where the required output is a judgment, not an answer. Otherwise you will find out about the gap in production. A 2025 survey of software-engineering agents documents the arc from small function-generation tasks like HumanEval and MBPP to repository-level suites with real GitHub issues, pull requests, cross-file dependencies, and executable test environments — the small clean tasks were superseded because they did not represent the work.

**Write the failure rule per item.** A 2026 evaluation-ecosystem paper argues that leaderboard reliance encourages overfitting and saturation, and that the unit of evaluation is not the model but the "contextual unit" — a person using AI in a setting. Your set is the contextual unit made concrete.

**Keep a hard set and a fresh set.** A 2025 survey of software-engineering agents notes a benchmark drawn from public repositories may already have appeared in pretraining or fine-tuning data — which is why a dedicated contamination benchmark was created to evaluate models under different contamination levels. Unfamiliarity cannot safely be assumed. If your set is public, treat it as contaminated and keep a second set of fresh items you have never shared.

**Version it.** Every set gets a date and a number. When a number moves, you need to know whether the set changed or the system did.

**Record the provenance of each item.** Which document, which date, which was chosen because it broke something. A 2026 benchmark called CiteAudit found 2,967 fabricated citations out of 9,442 in its test set, and separately references that exist but whose title or author metadata does not match — a signal the citing work never read the source. Provenance is what lets you audit your own set instead of inheriting someone else's.

## The four rules that keep it alive

**Never delete a failing item.** A hard item is the most valuable thing in the set. Deleting it converts the instrument into a rubber stamp.

**Add items when a surprise appears.** A new failure mode is a new item, added before the fix ships.

**Re-run the whole set on every candidate.** Not a subset. A subset changes the denominator, and you saw what the denominator does to a score.

**Measure the human baseline once a year.** Two people, 30 outputs, one correlation. That number is the ceiling, and it tells you whether your instrument is still measuring anything.

[AUTHOR EXPERIENCE: Replace with your real account — a question set that caught a failure a leaderboard score had missed.]

## What this cannot settle

The build recipe is my construction, drawn from one recommendation in the 2026 metrics study rather than a validated protocol. Twenty-five to thirty items will not support fine statistical comparison, and a serious evaluation will need more.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And a set measures only what someone thought to write down. The instrument is still a human artifact, and the coverage gap it inherits is the coverage gap of whoever built it.

## Where to start this week

1. Open your last finished project and list ten questions whose answers you already know.
2. Add ten more that you know were hard.
3. Write the failure rule for each in one line.
4. Version the file. Date it.
5. Run one candidate against it and write down the failures.

## Sources

- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; difficulty confound; weak faithfulness and hallucination correlation; two-system comparison.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; strict vs relaxed grading roughly doubling scores.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: HumanEval/MBPP to repository-level suites; contamination benchmark; unfamiliarity cannot be assumed.
- *Evaluating LLM Metrics Through Real-World Capabilities* (2025). arXiv:2505.08253. https://arxiv.org/html/2505.08253v1
  - Supports: six practical capabilities; "Reviewing Work" and "Data Structuring" not captured; benchmarks prioritize abstract correctness.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; leaderboard overfitting and saturation.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations and 2,967 fabricated; metadata mismatch as an unread-source signal; provenance auditing.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: human review essential for rubrics and domain context; reusable evaluation artifacts.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Do you have a question set, or do you have a score?
