---
title: "Six Ways to Be Wrong About Which Paper to Trust"
subtitle: "A paper's headline number hides at least six things — and each one changes whether you should build on it."
tags:
  - reading-papers
  - ai-evaluation
  - llm
  - how-to-evaluate-llm-tools
  - research-literature
  - scientific-writing
  - ai-research
platform: linkedin
medium_publication: signal-scribe
target_length: 1350-1600
word_count: 1520
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 90
hard_fail: false
distinctness_angle: "Paper-trust specific — six distinct ways a paper misleads, each with its own detection; a 'what to check before you cite' structure"
sources_count: 11
author_experience_placeholders: 1
---

Reading a paper is a selection problem, and the failure modes are specific.

A paper's headline number hides at least six things. Each one changes whether you should build on the result, and most of them are visible in an afternoon.

## One: the number is about a different task

The benchmark resembles your problem in the way a stock photo resembles a photograph.

A 2025 survey of software-engineering agents documents the arc from small function-generation tasks like HumanEval and MBPP to repository-level suites with real GitHub issues, pull requests, cross-file dependencies, and executable test environments. A 2025 evaluation-ecosystem paper makes the general claim: static datasets and constrained tasks poorly reflect deployment conditions, and the unit of evaluation should be the "contextual unit" — the adaptive behavior of people using AI in a setting.

**Check:** does the input distribution resemble yours in shape, length, messiness, and language? If the paper's inputs are clean and yours are not, the result describes a cleaner problem than you have.

## Two: the number has a lenient denominator

This is the one that most often flips a result, and it is usually stated somewhere you have to go looking for.

A 2026 benchmark for long-context agentic instruction following reported strict pass@1 alongside a relaxed variant that tolerates one violated control, and found that relaxing roughly doubles leader scores. The authors warned that a deployment tolerating one violated control per workflow "has effectively abandoned strictness." Its best configuration scored **36.2% strict pass@1** — still failing nearly two of every three tasks.

**Check:** what counts as a failure, and how many are tolerated? If the paper reports a relaxed number, the strict number is roughly half of it.

## Three: the number was produced by a judge with named biases

The 2023 NeurIPS MT-Bench paper is where these are named most clearly. GPT-4 as a judge agreed with human preference on more than 80% of comparisons, comparable to agreement between humans — and the paper names position bias, verbosity bias, and self-enhancement bias, plus the limitation "limited reasoning ability."

The companion paper, "Large Language Models are not Fair Evaluators," showed the practical magnitude: under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. That is a ranking that is a property of the measurement, not the models.

**Check:** who judged, was the order randomized, was length controlled, was the judge from a different family than the candidate? A close margin with none of those is not a result.

## Four: the number is not about the thing you care about

A 2025 paper on real-world capabilities identified six practical capabilities and found that "Reviewing Work and Data Structuring are not captured at all" by the metrics it evaluated. Its argument is that benchmarks "often prioritize abstract notions of correctness over qualities that matter to users."

**Check:** read the metric definition, not the task description. If the metric is answer accuracy and you need review quality, the paper does not answer your question.

## Five: the number may be memorized

A 2025 survey of software-engineering agents notes that a benchmark drawn from public repositories may already have appeared in model pretraining or fine-tuning data — which is why a dedicated contamination benchmark was created to evaluate models under different contamination levels. The survey's conclusion: unfamiliarity cannot safely be assumed.

**Check:** is the evaluation set public, and was it public before the model's training cutoff? A paper evaluating on a well-known public benchmark with a recent model should say something about this.

## Six: the number is not the claim

This is the most common and the least noticed.

A 2026 benchmark called CiteAudit found 2,967 fabricated citations out of 9,442 in its test set. More revealing: it found references that exist but whose title or author metadata does not match, which signals the citing work never read the source.

A 2026 study of source attribution in AI research reports is even more direct about the general case. It scored each claim-citation pair on three separate dimensions and found link validity above **94%** and relevance above **80%** while factual accuracy ranged from **24.4% to 76.8%**. Everything visible was healthy. The claim was still unsupported roughly a third to three-quarters of the time.

**Check:** can you find the passage in the source that supports the specific sentence? This is the check that catches all six of the above at once, because it forces you to look at the source rather than the number.

## The one thing that catches everything

Pull the passage.

Not the abstract. Not the summary figure. The passage in the source, next to the claim, that says the thing the paper says it says.

It is slow and it feels pedantic, which is why it is skipped. It is also the only check that is not a proxy. Every number in a paper is a proxy for something, and proxies drift.

## A related finding worth knowing

If you use an AI research tool to find and verify sources, more searching is not better.

Across GPT-5.4 and Claude Opus 4.6 in the 2026 source-attribution study, fact-check accuracy fell by roughly **42 percentage points on average** as tool calls rose from 2 to 150. One model dropped from 78.6% to 16.7%; another from 80.0% to 57.9%. Link validity and topical relevance stayed above 92% throughout — the model kept finding accessible, on-topic pages while getting worse at pinning a specific fact to a specific one.

There is a bandit-based framework treating prompt selection as an online learning problem rather than offline hyperparameter optimization [UNVERIFIED — the paper's contents could not be retrieved, so no result is claimed here].

**The practical version:** decide your research depth before you start, and always do the passage check at the end, no matter how many sources you gathered.

## The check, in one page

| Check | Question | Signal something is wrong |
|---|---|---|
| Task fit | Do the inputs resemble yours? | Clean inputs, messy problem |
| Denominator | What counts as failure, and how many are tolerated? | Only a relaxed number reported |
| Judge | Who judged, was order randomized, was length controlled? | Single judge, single order |
| Metric fit | What does the metric actually measure? | Answer accuracy where you need review quality |
| Contamination | Was the eval set public before the cutoff? | Silent |
| Claim support | Can you find the supporting passage? | You cannot find it |

Six checks, and the last one is a superset of the others in practice.

[AUTHOR EXPERIENCE: Replace with your real account — a paper you trusted that failed one of these six.]

## What this cannot settle

The six are my selection, drawn from the failure modes the literature documents. Other readers would name different ones — statistical power, missing baselines, and hyperparameter tuning budget are all absent from my list.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones. The 2022 instruction-finetuning and 2021 TruthfulQA results I would cite here describe models that no longer lead the field.

And pulling the passage is a check, not a proof. You can find a passage that supports a claim and still misread it.

## Where to start this week

1. Pick the last paper you cited and run all six checks on it.
2. Find the passage for one claim you are least sure about.
3. Ask one paper what counts as a failure. Read the metric definition, not the abstract.
4. Set a research depth budget before your next literature session.
5. Never cite from an abstract alone again.

## Sources

- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: HumanEval/MBPP → repository-level suites; contamination via DyCodeEval; SWE-bench reliability caveat.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; static-task limits; saturation and contamination.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: strict vs relaxed grading roughly doubling scores; 36.2% strict pass@1.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *Evaluating LLM Metrics Through Real-World Capabilities* (2025). arXiv:2505.08253. https://arxiv.org/html/2505.08253v1
  - Supports: "Reviewing Work" and "Data Structuring" not captured; benchmarks prioritise abstract correctness.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; metadata mismatch reveals unread papers.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; ~42-point fact-check drop from 2 to 150 tool calls; 78.6%→16.7% and 80.0%→57.9%.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; correlation ≠ validity; two-system comparison.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: human review essential for domain context, rubrics, and escalation.
- Lin, S., Hilton, J., & Evans, O. (2022). *TruthfulQA*. ACL 2022. https://arxiv.org/abs/2109.07958
  - Supports: capability and truthfulness as separate axes; 58% vs 94%; larger models less truthful.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above, and the one unverified source is marked as such in the body. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Which of these six would have caught the last paper you cited?
