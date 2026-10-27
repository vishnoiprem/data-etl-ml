---
title: "What to Read, What to Run, What to Throw Away: A Practical Selection Method"
subtitle: "A three-bucket system for AI tools, papers, and prompts — with the evidence thresholds that put an item in each bucket."
tags:
  - ai-evaluation
  - triage
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - ai-engineering
  - research-workflow
platform: linkedin
medium_publication: signal-scribe
target_length: 1250-1500
word_count: 1450
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 86
hard_fail: false
distinctness_angle: "Triage / three-bucket system — READ, RUN, DISCARD with explicit evidence thresholds for moving an item between buckets"
sources_count: 9
author_experience_placeholders: 1
---

Every week, more things arrive that might be worth your attention: a paper, a model release, a tool, a prompt someone swears by, a blog post with a chart.

The problem is not finding candidates. The problem is that all candidates arrive looking equally plausible, so you either over-invest in the wrong ones or you default to ignoring everything.

Three buckets solve it. Here is the triage.

## Bucket one: read

**Threshold: it makes a claim you are about to repeat, and you can find the passage that supports it.**

This is a narrow threshold and it is the point. Most things you read are background. Background reading does not need a verification budget.

A 2026 source-attribution study measured exactly this gap. Across 14 models and 130 research queries, link validity exceeded 94% and topical relevance exceeded 80% — so almost every citation looked fine on both cheap checks — while claim-level factual accuracy ranged from 24.4% to 76.8%. The passage exists, or it does not.

The discipline that keeps bucket one small: a reference that exists but whose title or author metadata does not match indicates the citing work never read the source. A 2026 benchmark called CiteAudit found 2,967 fabricated citations out of 9,442, and separately identified that metadata-mismatch class, which is the more dangerous one because it survives an existence check.

**Bucket one test:** open it. Find the passage. If the passage supports your sentence, it goes in bucket one. If it does not, either change the sentence or move it.

## Bucket two: run

**Threshold: it is a candidate for something you will actually do, and it has not yet earned the right to be trusted.**

Bucket two is where evaluation happens, and it is where people get it wrong — by running too many things, or by skipping the run entirely.

**Run one thing at a time, and run it on your own data.** A 2025 evaluation-ecosystem paper argues the unit of evaluation is the "contextual unit" — the adaptive behavior of a person using AI in a setting — and recommends defining a theory of change with stakeholders before comparing anything: goals, inputs, outputs, outcomes, counterfactuals. A 2025 survey of software-engineering agents makes the operational version: benchmark scores should guide rather than determine tool choice, and candidates should be compared on your repository, language, context length, test strength, contamination exposure, latency, and cost.

**Run it twice, in different orders.** This is the cheapest test in the whole system and it disqualifies more candidates than anything else. The 2023 NeurIPS MT-Bench paper found GPT-4 judges agreeing with human preference on more than 80% of comparisons — comparable to human-human agreement — while naming position bias, verbosity bias, and self-enhancement bias, plus "limited reasoning ability." A companion paper showed what happens if you skip this: under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries.

**Run it at the size you will operate at.** A 2025 study of retrieval-based tool selection found that presenting every tool schema dropped selection accuracy to 13.62%, while retrieving the relevant schema raised it to 43.13% and cut average prompt usage from 2,133.84 tokens to 1,084 — and that accuracy degraded beyond roughly 100 candidates as retrieval precision fell. Twenty tools and two hundred tools are different systems.

**Run it with the trace on.** A 2026 paper on agent evaluation notes that procedural failures "can look plausible in the final response" — claiming a tool that was never invoked, skipping a compliance call, ordering calls wrongly. The output can look fine and the process be wrong.

**Bucket two exit:** a candidate either enters bucket one (verified, in use) or bucket three. There is no permanent bucket two, because a candidate that keeps sitting there is a candidate that is costing you attention without earning it.

## Bucket three: throw away

**Threshold: it failed a check that it had no reason to fail, or it addresses a job you do not have.**

This bucket is the one people avoid, because throwing something away feels like a mistake. It is not. The most expensive thing in an attention budget is a candidate that sits in limbo for two years.

**Throwing away for scale reasons.** If the 100-candidate limit applies to your case and the candidate has no routing strategy, it is out. No amount of prompt tuning fixes a registry-size problem.

**Throwing away for cost reasons.** In a 2026 long-context agentic instruction following benchmark, one configuration reached 21.5% on roughly 13K generated tokens per trial, while another spent close to 60K tokens at about three times the dollar cost for the same band. Several mid-pack configurations generated 45–55K tokens and scored in single digits. If a candidate is in the same band as a cheaper one, it is out regardless of its headline number.

**Throwing away for scoring reasons.** If the candidate wins only because it got a better position, a longer answer, or a judge from its own family, it is out. The 2023 MT-Bench paper names all three biases explicitly, and the companion fairness paper quantified how much order alone can move a result.

**Throwing away for job reasons.** A 2026 RAG benchmark found models "still struggle significantly in terms of negative rejection, information integration, and dealing with false information" even with retrieval attached — which means some candidates are the right tool for a different job. A method that solves a problem you do not have is not a candidate; it is a distraction with a good score.

**Throwing away for unverified reasons.** If you cannot find the passage, you cannot use the claim — but you can still use the tool. Bucket three is about claims and candidates, and it helps to keep those separate.

## The triage, applied in order

**Step 1.** Everything lands in bucket two. Nothing is judged on arrival.

**Step 2.** Run the cheapest disqualifier first: swapped order, then moved evidence position, then doubled candidate pool. The 2023 TACL paper "Lost in the Middle" is why position is on this list — models perform best at the beginning or end of the context and "significantly degrades when models must access relevant information in the middle," including in explicitly long-context models. A candidate that fails when you move the evidence has a layout dependency, and production will move the evidence.

**Step 3.** Anything that survives the cheap disqualifiers gets the expensive one: your own task set, two systems on the same questions, and a human in the loop if the domain warrants it. A 2026 RAG metrics study found human evaluators agreeing with each other at a Pearson correlation of 0.85 — the practical ceiling for a proxy metric — and RAGChecker's claim recall near 0.7, while warning that high correlation does not establish validity, because difficulty and other confounders produce strong correlations on their own. Their method: evaluate at least two systems on the same questions.

**Step 4.** Promote to bucket one or demote to bucket three. Do not leave things in bucket two.

**Step 5.** Schedule a re-check of bucket one. Rankings decay, models get replaced, and web pages move — a 2026 source-attribution study notes that web-based citations are temporally unstable, with pages paywalled, moved, and removed.

## Why the three buckets work

Because they make the *default* action cheap.

Most systems of this kind make the default "investigate," which means you investigate everything, which means you investigate nothing well. The three buckets make the default "run the cheap disqualifier," and they make the expensive path conditional on surviving it.

That is also, roughly, the shape of good evaluation practice as described in the literature. A 2026 agent-evaluation paper argues for human review placed exactly where it is expensive but necessary — "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions" — while acknowledging it is costly, slow, and hard to reproduce at every step, and recommending that expert knowledge be compiled upstream into reusable evaluation artifacts so it can be applied many times without re-deriving it.

Bucket one, bucket two, bucket three: read, run, discard. Each one has a threshold. Each threshold is a check you can actually perform.

[AUTHOR EXPERIENCE: Replace with your real account — a candidate that sat in limbo for months, and which bucket it belonged in.]

## What this cannot settle

The bucket structure is my construction. No published work validates it, and the thresholds are judgment calls rather than measurements. A reasonable person would set the boundaries elsewhere.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And the triage does not handle the case it is hardest about: the candidate that is genuinely good for a job you will have in six months. Some things belong in a holding pattern, not a bucket.

## Where to start this week

1. Put everything on your current shortlist into one of the three buckets. Most of it will go to three.
2. Run the swapped-order test on the survivors.
3. Promote exactly one thing to bucket one this week.
4. Delete the limbo list.
5. Set a re-check reminder for bucket one.

## Sources

- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; 14 models, 130 queries; temporal instability of web citations.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; title/author metadata mismatch reveals unread papers.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; theory of change; field testing; leaderboard overfitting.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: scores guide not determine; selection dimensions; contamination.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation ≠ validity; two-system comparison.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation in long contexts.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: 13.62% vs 43.13%; 2,133.84 → 1,084 tokens; degradation beyond ~100 candidates.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 13K vs 60K tokens at ~3× cost for the same band; 36.2% strict pass@1.
- Chen, J. et al. (2024). *Benchmarking Large Language Models in Retrieval-Augmented Generation*. AAAI 2024. https://arxiv.org/abs/2309.01431
  - Supports: persistent failure in negative rejection, information integration, false information.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; human review essential for specific decisions; upstreaming expertise.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

How many candidates are currently sitting in your limbo bucket?
