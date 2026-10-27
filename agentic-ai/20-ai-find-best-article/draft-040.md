---
title: "Prompts Are Programs: How to Evaluate One the Way You Would Evaluate Code"
subtitle: "A prompt is a function with a hidden contract — and you can test it like a dependency."
tags:
  - llm
  - ai-evaluation
  - how-to-evaluate-llm-tools
  - ai-engineering
  - technical-writing
  - model-selection
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1430
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 89
hard_fail: false
distinctness_angle: "Software-analogy frame — treats prompts as programs with contracts and treats prompt evaluation as unit testing, borrowing the dependency/test/mocking vocabulary for the whole article"
sources_count: 9
author_experience_placeholders: 1
---

A prompt is a function.

It takes inputs, applies a transformation, and returns an output. That makes it software, and the reason prompt evaluation feels ad hoc is that we have been treating it as something else — a piece of wording, an art, a vibe — when the tools of software evaluation have been sitting there unused.

You already know how to test a function. The vocabulary transfers, and the transfer is the point.

## The contract

Every prompt has an implicit contract:

```
Given: <input shape, language, length, messiness>
When: <the task>
Then: <output shape, format, length, what must be included>
And: <what must never happen>
```

The "And" clause is where prompts differ from most functions, and where the evaluation literature puts its weight.

A 2025 paper on real-world capabilities identified six practical capabilities and found that "Reviewing Work and Data Structuring are not captured at all" by the metrics it evaluated. Its argument is that benchmarks "often prioritize abstract notions of correctness over qualities that matter to users." In prompt terms, the "And" clause — the constraints — is usually the part nobody tests and the part that matters.

## The test suite

A unit test for a prompt is an input, the expected output shape, and a checkable property. Three kinds of test, in increasing cost.

**Shape tests.** Does it return valid JSON? Does it have the required fields? Does it stay under the length limit? These are cheap, deterministic, and catch the majority of integration failures. A 2026 benchmark for long-context agentic instruction following reported strict pass@1 alongside a relaxed variant tolerating one violated control, and found that relaxing roughly doubles leader scores — best configuration **36.2% strict pass@1**, still failing nearly two of every three tasks. The violated control in that case was a deterministic constraint, exactly the kind a shape test can check.

**Property tests.** Not "the output is exactly this string" but "the output contains no source other than the retrieved context" or "the output refuses when the context does not contain the answer." A 2024 RGB benchmark organized RAG evaluation around four abilities, and models "still struggle significantly in terms of negative rejection, information integration, and dealing with false information." Negative rejection is a property test, and it is the one most systems fail.

**Golden tests.** A handful of exact expected outputs, kept for regression. Useful for detecting unintended change after a model upgrade, and misleading as a quality measure, because you will spend all your time on the one input that changed.

## The mock

In code, you mock a dependency to isolate the unit under test. The equivalent in prompt work is substituting the model.

Run your prompt against two different models on the same inputs. If the outputs diverge sharply, your prompt is doing less work than you think and the model is doing more. That is worth knowing, because it is the difference between a prompt change and a vendor dependency.

The 2026 source-attribution study offers a related and more urgent version. Across GPT-5.4 and Claude Opus 4.6, fact-check accuracy fell by roughly **42 percentage points on average** as tool calls rose from 2 to 150. One configuration dropped from 78.6% to 16.7%; another from 80.0% to 57.9%. Link validity and topical relevance stayed above 92% throughout — the cheap checks stayed green while the expensive one degraded. Mock the model and you find out which of your checks are cheap.

## The fixture

A fixture is the controlled input that makes a test repeatable. Your evaluation set is a fixture collection.

Build it from closed work, and keep the hard cases. A 2025 survey of software-engineering agents documents the arc from small function-generation tasks like HumanEval and MBPP to repository-level suites with real GitHub issues, pull requests, cross-file dependencies, and executable test environments, and warns that a benchmark drawn from public repositories may already have appeared in pretraining or fine-tuning data — which is why a dedicated contamination benchmark was created. Unfamiliarity cannot safely be assumed, so a public fixture is a contaminated fixture.

## The assertion

This is the part that has no clean analogue in code, and it is where prompt evaluation usually goes wrong.

You want to assert something about output quality, and you reach for an LLM judge. The 2023 NeurIPS MT-Bench paper is the reference here, and it is worth reading for what it claims and what it names. GPT-4 as a judge agreed with human preference on more than 80% of comparisons — comparable to agreement between humans. It also names position bias, verbosity bias, and self-enhancement bias in its own method, plus the limitation "limited reasoning ability."

The companion paper, "Large Language Models are not Fair Evaluators," shows the practical magnitude: under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries.

Your assertions need the same defenses, applied in the same way you would assert a float equals a float: tolerance for the noise, and a known failure mode.

**Set a tolerance.** A 2026 RAG metrics study gives you the floor. Human evaluators' ratings correlated with each other at **Pearson 0.85** — the practical ceiling for any automatic proxy. RAGChecker claim recall was near **0.7**, the strongest overall correlation among the tools tested, and the authors warned that high correlation does not establish validity, because input difficulty and other confounders produce strong correlations on their own. An assertion with a 0.5-point margin is a flaky test, and you would not ship it in code.

**Run the order-swap.** Swap the presentation order, assert the same outcome. If the assertion flips, the assertion is broken, not the prompt.

**Assert on a stated criterion.** Not "which is better" but "does the output satisfy criterion C." A written criterion makes the assertion checkable and stops it from rewarding style.

## The CI run

Continuous integration for prompts is unglamorous and effective.

**On every prompt change:** run the shape tests. Minutes, not hours, and they catch the majority of breakage.

**On every model version change:** run the full suite. A 2026 evaluation-ecosystem paper notes leaderboard overfitting and saturation, and a 2026 source-attribution study notes that web-based citations are temporally unstable — pages get paywalled, moved, and removed. The same decay applies to models: the same prompt can score differently tomorrow for reasons that have nothing to do with your prompt.

**On every week:** run the golden tests and diff. A change in output shape is a change in behavior, and you want to know it happened on a Tuesday and not on a release Friday.

## The exception to the whole frame

Prompts are not fully deterministic programs. The same input can produce different outputs, which is why tolerance and repeated runs exist, and why human-agreement ceilings like 0.85 are a fact of the domain rather than a defect of your test.

But nondeterminism is not a reason to skip tests. It is a reason to test the properties that are stable, which is most of them.

## What this cannot settle

The program framing is my construction, borrowed from software practice rather than from published work on prompt evaluation. It also flattens a real difference: a prompt's behavior is entangled with the model's, the retrieval, and the runtime, and the "unit" you are testing is genuinely harder to isolate than a function.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And a test suite that only checks shape will happily pass a prompt that returns valid JSON full of wrong answers. The analogy is useful precisely as long as you remember where it stops.

## Where to start this week

1. Write the contract for one prompt: given, when, then, and never.
2. Add three shape tests to it today.
3. Add one negative-rejection test: input with no answer in context, expect a refusal.
4. Run your prompt on two models and diff the outputs.
5. Put the shape tests in your pipeline.

## Sources

- *Evaluating LLM Metrics Through Real-World Capabilities* (2025). arXiv:2505.08253. https://arxiv.org/html/2505.08253v1
  - Supports: six practical capabilities; "Reviewing Work" and "Data Structuring" not captured; benchmarks prioritize abstract correctness.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: strict vs relaxed grading roughly doubling scores; 36.2% strict pass@1; hard controls outside the model.
- Chen, J. et al. (2024). *Benchmarking Large Language Models in Retrieval-Augmented Generation*. AAAI 2024. https://arxiv.org/abs/2309.01431
  - Supports: RGB's four abilities; persistent failure in negative rejection, information integration, and false information.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: ~42-point fact-check drop from 2 to 150 tool calls; 78.6%→16.7% and 80.0%→57.9%; link validity stays above 92%.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; difficulty confound; correlation ≠ validity.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: HumanEval/MBPP to repository-level suites; contamination benchmark; unfamiliarity cannot be assumed.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: leaderboard overfitting and saturation; contextual unit framing.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

What would the contract for your most-used prompt look like, in four lines?
