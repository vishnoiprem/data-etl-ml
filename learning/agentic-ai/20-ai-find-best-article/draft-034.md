---
title: "Nobody Reads the Metric Definition: The Most Skipped Step in AI Tool Evaluation"
subtitle: "What you are actually measuring, stated in one sentence you have never written down."
tags:
  - ai-evaluation
  - llm
  - how-to-evaluate-llm-tools
  - benchmarks
  - technical-writing
  - model-selection
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1385
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 89
hard_fail: false
distinctness_angle: "Single-missing-step frame — takes the most-skipped element of evaluation (the metric definition) and shows that every other failure follows from it, with the metric-definition sentence as the artifact"
sources_count: 9
author_experience_placeholders: 1
---

Every evaluation has a metric definition. Almost nobody writes it down.

They read the paper's abstract, note the number, compare it to a rival's number, and choose. The number is a proxy for a proxy for a proxy, and nobody has checked what the innermost one means.

Here is what happens when the metric definition is written down, in the form it should take.

## The one sentence

**"This score measures [X] on [Y] for [Z], and does not measure [W]."**

That is the whole artifact. Four slots. It takes ten minutes.

A 2025 paper on real-world capabilities shows exactly what an unwritten definition hides. It identified six practical capabilities and found that "Reviewing Work and Data Structuring are not captured at all" by the metrics it evaluated. The paper's argument is that benchmarks "often prioritize abstract notions of correctness over qualities that matter to users." Those two capabilities were not underperforming. They were not being measured, and no score would have shown it.

A metric definition written down would have caught that in one sentence: "does not measure review quality."

## Why a proxy drifts

A 2026 study of RAG evaluation metrics gives the sharpest version of the problem. Human evaluators' ratings correlated with each other at **Pearson 0.85** — the practical ceiling for any automatic proxy metric. RAGChecker produced the strongest overall correlations among the tools tested, with claim recall near **0.7**. But the authors' warning is the load-bearing part: high correlation does not establish validity, because input difficulty and other confounders can produce strong correlations on their own. RAGChecker claim recall near 0.7 might be tracking question difficulty or answer extractability rather than retrieval quality.

That is a proxy drift with numbers attached. The metric correlates well with humans, and measures something other than retrieval.

The same study also found that faithfulness and hallucination metrics correlated weakly as overall metrics, attributed partly to their lack of access to reference answers, and that one moderation metric did not correlate with the reference scores at all. Those metrics have definitions that are hard to state in a way that is not trivially true, and it shows in their behavior.

## The three-word test

For every number you plan to quote, fill in the X slot with a noun phrase and check three words:

**Does it measure the outcome, or a step toward it?**

Answer accuracy and task completion are steps. Reduced review time and fewer escalations are outcomes. A 2025 evaluation-ecosystem paper makes the general claim that static datasets and constrained tasks poorly reflect deployment conditions, and that the unit of evaluation should be the "contextual unit" — the adaptive behavior of people using AI in a setting. If your metric is answer accuracy, you are measuring a step.

**Does it change when the outcome changes?**

If improving the thing you care about does not move the number, the number is decoration. A 2026 agent-evaluation paper is blunt that procedural failures "can look plausible in the final response" — an agent claiming a tool it never invoked, skipping a compliance call, calling tools out of order. The prose reads correctly. Any metric reading the prose gives a passing grade.

**Is anyone accountable for the failure it misses?**

A metric that no one has to act on will not be acted on. A 2025 survey of software-engineering agents makes the operational point: benchmark scores should guide rather than determine tool choice, and candidates should be compared on your repository, language, context length, test strength, contamination exposure, latency, and cost. The metric exists to move a decision.

## Denominator as part of the definition

The X slot is not enough. The Y slot carries the grading convention.

A 2026 benchmark for long-context agentic instruction following reported strict pass@1 alongside a relaxed variant tolerating one violated control, and found that relaxing roughly doubles leader scores. Its best configuration scored **36.2% strict pass@1** — still failing nearly two of every three tasks. The authors warned that a deployment tolerating one violated control per workflow "has effectively abandoned strictness."

Same system, same work, two metrics, and the gap between them exceeded most product-to-product differences in the field. Writing "tolerates one violated control" into the metric definition is the difference between knowing and not knowing.

The Y slot also includes the population. Whose outputs, from which task distribution, in which language, under which input messiness. A 2025 survey of software-engineering agents documents the arc from small function-generation tasks like HumanEval and MBPP to repository-level suites with real GitHub issues, pull requests, cross-file dependencies, and executable test environments — because the small clean tasks did not represent the work.

## The judge belongs in the definition too

If a number comes from an LLM judge, the judge is part of the X slot.

The 2023 NeurIPS MT-Bench paper found GPT-4 as a judge agreeing with human preference on more than 80% of comparisons — comparable to agreement between humans — while naming position bias, verbosity bias, and self-enhancement bias in its own method, plus the limitation "limited reasoning ability." The companion paper, "Large Language Models are not Fair Evaluators," showed the practical magnitude: under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. That is a ranking that is a property of the measurement.

Your metric definition should say who judged, whether order was randomized, whether length was controlled, and whether the judge was from a different family than the candidate. A close margin with none of those is not a result.

## The written definition, and what it catches

Once the definition exists, four checks become possible that were impossible before.

**Task fit.** The 2025 evaluation-ecosystem paper argues the unit of evaluation is not the model but the "contextual unit" — a person using AI in a setting. If the Y slot says "single-turn, clean inputs," you have described a different job.

**Contamination.** A 2025 survey of software-engineering agents notes a benchmark drawn from public repositories may already have appeared in pretraining or fine-tuning data — which is why a dedicated contamination benchmark was created to evaluate models under different contamination levels. Unfamiliarity cannot safely be assumed.

**Claim support.** A 2026 benchmark called CiteAudit found 2,967 fabricated citations out of 9,442 in its test set, and references that exist but whose title or author metadata does not match — a signal the citing work never read the source. A 2026 source-attribution study found link validity above **94%** and relevance above **80%** while factual accuracy ranged from **24.4% to 76.8%**. Everything visible was healthy; the claim was still unsupported roughly a third to three-quarters of the time. A definition that names what the number means makes that gap visible.

**Cost.** A 2026 RAG metrics study recommends evaluating at least two systems and comparing outputs on the same questions, because shared difficulty cancels. Two systems, one definition, one comparison — and a cost-per-successful-run figure computed on your own distribution.

## The artifact

```
METRIC: <noun phrase — what is measured>
POPULATION: <whose outputs, from which tasks, which language>
GRADING: <what counts as failure, how many tolerated>
JUDGE: <who judged; order randomized; length controlled; different family>
PROXY FOR: <the outcome you actually want>
DOES NOT MEASURE: <the capability you are worried it misses>
```

Six lines. It takes one sitting.

Write it before you collect any data, not after, because after is when the number starts to feel like the answer.

[AUTHOR EXPERIENCE: Replace with your real account — a metric definition you wrote late, and what it revealed that the score had hidden.]

## What this cannot settle

The six-line artifact is my construction. No published work validates it, and some metrics are genuinely multi-dimensional, where forcing a single noun phrase distorts more than it clarifies.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And a written definition does not make a metric valid. It makes the metric's claim auditable. You can write a precise definition of a bad metric, and then discover the badness by measuring the thing the metric says it measures.

## Where to start this week

1. Write the six lines for the metric you trust most.
2. Fill in DOES NOT MEASURE. If you cannot name a capability, the metric may be fine — or you may not know your job well enough yet.
3. Ask one paper what counts as a failure and how many are tolerated.
4. Find out who judged.
5. Re-read your last decision memo against the definition.

## Sources

- *Evaluating LLM Metrics Through Real-World Capabilities* (2025). arXiv:2505.08253. https://arxiv.org/html/2505.08253v1
  - Supports: six practical capabilities; "Reviewing Work and Data Structuring are not captured at all"; benchmarks prioritize abstract correctness.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; difficulty confound; weak faithfulness and hallucination correlation; two-system comparison.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; strict vs relaxed grading roughly doubling scores; "effectively abandoned strictness."
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; static-task limits; leaderboard overfitting.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: HumanEval/MBPP to repository-level suites; contamination benchmark; scores guide not determine.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; deterministic vs subjective detection.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fabricated; metadata mismatch reveals unread sources.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% link validity and 80% relevance vs 24.4–76.8% claim accuracy.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Could you write the metric definition for the number you trust most, right now?
