---
title: "How to Read an AI Vendor Comparison Without Being Sold To"
subtitle: "Six checks that turn a marketing table into an evaluation — and the specific tells that a table was engineered rather than measured."
tags:
  - ai-evaluation
  - vendor-evaluation
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - procurement
  - ai-engineering
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1470
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 88
hard_fail: false
distinctness_angle: "Vendor-comparison audit — six forensic checks applied to vendor-produced comparison tables, with the tell-tale signs of an engineered comparison"
sources_count: 10
author_experience_placeholders: 1
---

Vendor comparison tables are not measurements. They are documents.

Produced by a party with revenue at stake, selecting benchmarks favorable to their product, omitting the candidates that lost, and — usually without saying so — using whatever evaluation methodology made their product look best.

None of that makes them useless. It makes them inputs to an evaluation rather than the output of one. Here is how to convert one.

## Check one: what was the denominator?

A percentage without a denominator is a marketing artifact.

A 2026 benchmark for long-context agentic instruction following illustrates why this matters concretely. It reported strict pass@1 alongside a relaxed variant tolerating one violated control, and found that relaxing roughly doubles leader scores. The authors warned that a deployment tolerating one violated control per workflow "has effectively abandoned strictness."

Same system, same work, two numbers — and the difference between them is larger than most vendor comparisons claim between products.

**What to look for in a vendor table:** the number of items evaluated, the number of attempts, whether failures were retried, and whether a strict or relaxed criterion was used.

## Check two: which candidates were omitted?

Every vendor table is a survivorship study.

A 2025 software-engineering agent survey makes the broader point about the underlying benchmarks: scores should guide rather than determine tool choice, and you should compare candidates on your repository, language, context length, test strength, contamination exposure, latency, and cost. A table that shows four products on one benchmark tells you nothing about the other forty.

**What to look for:** how many competitors were evaluated in total, versus how many appear in the table. If a table lists two of eleven, that is information.

## Check three: was contamination checked?

Public benchmarks are, increasingly, training data.

A 2025 survey of software-engineering agents notes that a benchmark drawn from public repositories may already have appeared in model pretraining or fine-tuning data, which is why a dedicated contamination benchmark exists to evaluate models under different contamination levels. The survey's conclusion is direct: unfamiliarity cannot safely be assumed.

**What to look for:** any mention of held-out or private test sets, or of contamination controls. Silence here is not proof of contamination, but it means the score is a claim about a public dataset rather than about your problem.

## Check four: was an LLM judge used, and were its biases handled?

This is where vendor tables most often mislead, because the biases systematically favor particular systems.

The 2023 NeurIPS MT-Bench paper named them in its own method: position bias, verbosity bias, and self-enhancement bias — where a judge favors outputs written by itself or its own model family — plus the limitation "limited reasoning ability." Its headline result is genuinely useful: GPT-4 as a judge agreed with human preference on more than 80% of comparisons, comparable to agreement between humans.

But the companion paper showed how fragile a close comparison can be. Changing the presentation order of two answers changes the ranking they receive; under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. A table built on one judge, one order, one prompt can therefore be wrong in a direction the vendor cannot control.

**What to look for:** whether the judge was from a different family than the candidate being judged, whether order was randomized, and whether length was controlled. A table with none of these is measuring verbosity and position along with quality.

## Check five: was retrieval measured separately?

For any RAG product, a single end-to-end score hides the half that is usually broken.

A 2026 study of RAG evaluation metrics is the technical case for separating them. Human evaluators' ratings correlated with each other at a Pearson correlation of 0.85 — the practical ceiling for any proxy metric. RAGChecker's recall-oriented metrics correlated best, with claim recall near 0.7. But the authors explicitly warned that high correlation does not establish validity, because input difficulty and other confounders produce strong correlations on their own, and their recommendation was to evaluate at least two systems and compare outputs on the same questions.

Separately, the 2024 RGB benchmark found that models with retrieval attached "still struggle significantly in terms of negative rejection, information integration, and dealing with false information." Retrieval is not a fix.

**What to look for:** separate retrieval and generation numbers. If a table has only one combined score, ask for the breakdown.

## Check six: was the failure mode observed?

A table shows you what worked. It usually does not show what broke.

A 2026 paper on agent evaluation is blunt about this gap. Static benchmarks do not adequately test multi-turn tool use, policy adherence, recovery, or procedural consistency, and a model can pass a fixed benchmark and then fail operationally through "missing tool calls, hallucinated tool use, policy drift, unsafe reframing, manipulation paths, or over-refusal." Its recommendation is to look at trajectories and traces, because procedural failures "can look plausible in the final response."

A 2026 source-attribution study shows the same gap in a different domain. Across 14 models and 130 research queries, link validity exceeded 94% and relevance exceeded 80% — everything looks great — while factual accuracy ranged from 24.4% to 76.8%. And fact-check accuracy fell by roughly 42 percentage points on average across two frontier models as tool calls rose from 2 to 150, even as link and relevance stayed above 92%. Deeper checking made attribution worse, not better.

**What to look for:** any failure taxonomy, any trace inspection, any statement about what was *not* tested.

## The synthesis: what a vendor table can and cannot tell you

**It can tell you:** which candidates the vendor believes are strong, on which benchmarks, under which methodology.

**It cannot tell you:** whether the methodology was favorable, whether omitted candidates would have changed the ranking, whether your data resembles the benchmark, whether the number's denominator supports the percentage, or what happens when the system is used at your scale rather than the demo scale.

A 2025 evaluation-ecosystem paper put the general case: overreliance on leaderboards encourages overfitting and benchmark saturation, contamination and data leakage can inflate results, and leaderboards can overstate differences while obscuring common failure modes. The same paper notes that benchmarks can lag behind agentic capabilities entirely.

## So what do you do with the table?

Treat it as a shortlist generator and nothing more.

**Take the top two names and check the methodology against the six questions above.** If the table does not say which metric was used, which judge, which order, what the denominator was, and what was omitted, you do not have a ranking — you have a marketing claim, and the correct response is to run your own evaluation.

**Build the twenty questions from your own closed work.** That is the only input that reflects your data. A 2026 RAG metrics study makes the methodological point explicit: evaluate at least two systems on the same questions so that shared question difficulty cancels out. Run two candidates, not one, so you have something to compare.

**Run the cheap disqualifiers before the expensive tests.** Swap the order. Move the evidence to the middle of the context — the 2023 TACL paper "Lost in the Middle" found models perform best at the beginning or end and "significantly degrades when models must access relevant information in the middle," including in explicitly long-context models. Double your candidate pool, because a 2025 retrieval-based tool-selection study found accuracy degrading beyond roughly 100 candidates as retrieval precision declined.

**Then check the references in the vendor's own documentation.** A 2026 benchmark called CiteAudit found 2,967 fabricated citations out of 9,442, and separately found references that exist but whose title or author metadata does not match — meaning the cited work was never read. If the vendor's methodology section cites studies that do not say what it claims, you have your answer.

[AUTHOR EXPERIENCE: Replace with your real account — a vendor table you checked, and what it turned out to be measuring.]

## What this cannot settle

The six checks are my construction. No published work validates them, and vendor tables vary so much that no checklist covers every case.

The numbers are setup-specific and dated. The judge-agreement figures are from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

The checks also cannot tell you whether a vendor is being honest. They can tell you whether the table supports the claim being made, which is a different and more answerable question.

## Where to start this week

1. Take one vendor table you have recently relied on. Run all six checks.
2. Find its denominator.
3. Find out how many candidates were omitted.
4. Build twenty questions from your own work and run two candidates on them.
5. Swap the order.

## Sources

- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: strict vs relaxed grading roughly doubling leader scores; 36.2% strict pass@1; hard controls outside the model.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: scores guide not determine; comparison dimensions; contamination via DyCodeEval.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation ≠ validity; two-system comparison.
- Chen, J. et al. (2024). *Benchmarking Large Language Models in Retrieval-Augmented Generation*. AAAI 2024. https://arxiv.org/abs/2309.01431
  - Supports: persistent failure in negative rejection, information integration, false information.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: static benchmarks miss operational failure; trace analysis necessary; judges unreliable alone.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; ~42-point fact-check drop from 2 to 150 tool calls.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation in long contexts.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: degradation beyond ~100 candidates as retrieval precision falls.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; metadata mismatch detection.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: leaderboard overfitting, saturation, contamination; benchmarks lagging agentic capabilities.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

What is the denominator in the vendor table you trust most?
