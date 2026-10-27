---
title: "Freeze the Model, Then Choose: How to Separate Model Changes From Prompt Changes"
subtitle: "One variable at a time — and why most A/B tests on AI systems change two things at once."
tags:
  - ai-evaluation
  - llm
  - how-to-evaluate-llm-tools
  - ai-engineering
  - model-selection
  - experiments
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1410
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 90
hard_fail: false
distinctness_angle: "Single-variable experiment frame — makes attribution of a score change the whole subject, with a controlled comparison design and a worked attribution table"
sources_count: 9
author_experience_placeholders: 1
---

Most teams cannot explain why their AI system's score moved last week.

They changed the prompt. The model also changed. The retrieval index was rebuilt. Two of those moved and nobody knows which one did it.

This is not a rare mistake. It is the default state of most evaluations, and it makes every result unusable for the next decision.

## The rule

**One variable per run.**

Everything else pinned: model version, prompt text, retrieval index snapshot, temperature, tool versions, the question set. Then change exactly one thing and measure.

This is so obviously right that it is worth asking why it is skipped. The answer is that holding variables constant is tedious and boring, while the change is fun. The tedious part is where the information is.

## Why a two-variable change destroys the result

Consider the two most common paired changes.

**Prompt and model together.** The new model is better, the new prompt is better, and the score rose 8 points. Which one? If the answer is "both," you have learned that the combination is 8 points better and nothing about either. Next time you must change both again, and your search space is the product of the two.

**Prompt and retrieval index together.** Worse, because retrieval changes are invisible in the output. A 2025 survey of software-engineering agents documents that simply concatenating all relevant files was found to be suboptimal, and that snippet ordering materially affected performance. If you rebuilt the index and reordered the chunks in the same run, the retrieval effect is confounded with the prompt effect, and neither is separately observable.

**Prompt and tool configuration together.** The 2026 long-context agentic benchmark made the same recommendation from the enforcement side: enforce "hard controls outside the model," compiling policies into deterministic tool-call guards rather than relying on in-context adherence. Guards are a lever. Changing guards and prompt simultaneously means you cannot tell which one relaxed your grading rule.

## The control design that works

Four runs, two variables, four cells.

```
                    Prompt A      Prompt B
Model X               r11           r12
Model Y               r21           r22
```

Two effects you can now separate: the prompt effect, and the model effect. And the interaction, if the numbers disagree with additivity.

A 2026 RAG metrics study recommends the two-system comparison as the minimum useful design: evaluate at least two systems and compare their outputs on the same questions, so shared difficulty cancels and what remains is the difference between the systems. The four-cell design is the same idea with the difference computed in each direction, and it costs one more run than the two-cell version.

## Why the shared question set is what makes it work

Both systems see the same questions. That is what lets difficulty cancel.

The 2026 metrics study also shows the ceiling you are working against. Human evaluators' ratings correlated with each other at **Pearson 0.85** — the practical ceiling for any automatic proxy metric. RAGChecker produced the strongest overall correlations among the tools tested, with claim recall near **0.7**. But the authors' warning is the load-bearing part: high correlation does not establish validity, because input difficulty and other confounders can produce strong correlations on their own.

Read that as a design constraint. If your instrument's noise floor is 0.85 correlation with humans, then a 2-point score difference is inside the instrument's error. Set your run count and your decision threshold accordingly, or you will be reading noise and calling it a finding.

## Pinning, concretely

**Model version.** The exact identifier, not the family name. A 2026 source-attribution study found that across GPT-5.4 and Claude Opus 4.6, fact-check accuracy fell by roughly **42 percentage points on average** as tool calls rose from 2 to 150 — one configuration dropping from 78.6% to 16.7%, another from 80.0% to 57.9%, while link validity and topical relevance stayed above 92% throughout. Two lessons for experiment design: capability drifts within a single run, and the cheap checks stay green while the load-bearing one degrades. Pin the exact version and pin the call count.

**Prompt text.** The literal string, hashed and stored. Not a paraphrase in a wiki.

**Retrieval index.** A snapshot identifier plus the chunk hashes. The 2023 TACL paper "Lost in the Middle" found that models perform best when relevant material appears at the beginning or end of the context and "significantly degrades when models must access relevant information in the middle" — and explicitly long-context models were not exempt. If your chunk ordering changed between runs, you changed a variable that has a documented large effect.

**Tool versions and schemas.** A 2026 agent-evaluation paper is blunt that procedural failures "can look plausible in the final response" — an agent claiming a tool it never invoked, skipping a mandatory compliance call, calling tools out of order. If the tool list changed, the trace is not comparable.

**The question set.** The same items, the same order, the same snapshot of any external content. A 2026 source-attribution study notes that web-based citations are temporally unstable — pages get paywalled, moved, and removed — so a question set that depends on live pages is not a fixed input.

## Reading the results

**Check for an interaction before you believe either effect.** If prompt B beats prompt A on model X but loses on model Y, the prompt change was model-specific and you should not deploy it as a general improvement.

**Do not trust a difference smaller than your instrument's noise floor.** With human agreement at 0.85, treat small gaps as ties.

**If the judge is involved, swap the order.** The 2023 NeurIPS MT-Bench paper found GPT-4 as a judge agreeing with human preference on more than 80% of comparisons while naming position bias, verbosity bias, and self-enhancement bias, plus "limited reasoning ability." The companion paper showed the stakes: under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. A 3-point difference from a single-order comparison is not a finding.

**Report the denominator.** A 2026 long-context benchmark reported strict pass@1 alongside a relaxed variant tolerating one violated control, and found that relaxing roughly doubles leader scores — best configuration **36.2% strict pass@1**, still failing nearly two of every three tasks. Same run, two definitions, a factor of two.

## The one-week version

| Day | Run |
|---|---|
| 1 | Pin everything. Store the prompt hash, model ID, index snapshot, tool versions. |
| 2 | Baseline run on the fixed question set. |
| 3 | Change one variable. Run again. |
| 4 | Change a second variable. Run again. |
| 5 | Compare on the same set. Compute the effect per variable. |
| 6 | Swap judge order on the two closest runs. |
| 7 | Write the memo: which variable moved the number, and by how much. |

Five runs, one week, and every future decision has a reusable control.

[AUTHOR EXPERIENCE: Replace with your real account — a change that improved the score, and which variable was actually responsible.]

## What this cannot settle

The four-cell design is my construction, and it assumes a question set large enough to detect the effect you care about. With twenty items, most effects are below the resolution of the design.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And holding the model fixed removes the thing most teams actually want to change. The discipline is worth more than the initial speed-up, but it will feel like slowing down.

## Where to start this week

1. Hash and store your current prompt, model ID, and index snapshot.
2. Run your set once and record the baseline.
3. Change one thing. Run it again.
4. Compute the delta, and compare it to your noise floor.
5. Never again change two things at once.

## Sources

- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; difficulty confound; correlation ≠ validity; two-system comparison.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: long context not a substitute for retrieval; snippet ordering materially affects performance.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: strict vs relaxed grading roughly doubling scores; 36.2% strict pass@1; hard controls outside the model.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: ~42-point fact-check drop from 2 to 150 tool calls; 78.6%→16.7% and 80.0%→57.9%; temporal instability of web citations.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation in long contexts; long-context models not exempt.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; trace-based detection.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: leaderboard overfitting and saturation; contextual unit framing.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

When your score moved last month, how many things changed at the same time?
