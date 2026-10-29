---
title: "The Evaluation Stack: A Layered Model for Choosing AI Tools"
subtitle: "Seven layers, each with one question, each with a known failure mode — build them in order and the choice makes itself."
tags:
  - ai-evaluation
  - evaluation-framework
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - systems-thinking
  - ai-engineering
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1500
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 89
hard_fail: false
distinctness_angle: "Layered-stack architecture — seven evaluation layers bottom-up (data, retrieval, generation, trace, human, cost, time), each with one question and one published failure mode"
sources_count: 9
author_experience_placeholders: 1
---

Selection decisions fail at a specific layer, and teams rarely know which one.

They argue about the wrong layer. Two engineers disagreeing about model quality when the real problem is that their retrieval index has 11,000 near-duplicate chunks is a conversation that cannot resolve, because one of them is talking about layer two and the other about layer four.

Here is a stack. Seven layers. One question each.

## Layer 1: Data

**Question: is the data the candidate will see representative of the work it will do?**

Everything above this layer is conditional on it.

A 2025 evaluation-ecosystem paper argues the unit of evaluation is not the model but the "contextual unit" — the adaptive behavior of a person using AI in a setting — and recommends defining a theory of change with stakeholders before any technical comparison: goals, inputs, outputs, outcomes, counterfactuals. If your inputs do not resemble your inputs, no result above means anything.

**Failure mode:** you evaluate on a public test set and ship on a private one, then spend a month explaining the gap.

## Layer 2: Retrieval

**Question: does the system find the right material?**

Score this separately from generation. Always.

The 2026 study of RAG evaluation metrics is the technical case. Human evaluators correlated with each other at a Pearson correlation of 0.85 — the ceiling for any proxy. RAGChecker's recall-oriented metrics correlated best, with claim recall near 0.7. The authors' critical finding is that high correlation does not establish validity, because question difficulty can produce strong correlations on its own, and their method for removing that confound is to evaluate at least two systems on the same questions.

Meanwhile, the 2024 RGB benchmark showed that even with retrieval attached, models "still struggle significantly in terms of negative rejection, information integration, and dealing with false information." Retrieval is necessary and insufficient.

**Failure mode:** a combined score that tells you the system is at 78% but not which half is broken.

## Layer 3: Context position

**Question: does the result hold when the evidence is not conveniently placed?**

The 2023 TACL paper "Lost in the Middle" found that models perform best when relevant material sits at the beginning or end of the context and "significantly degrades when models must access relevant information in the middle." Explicitly long-context models showed the same weakness.

**Failure mode:** the eval passes because your documents happen to be ordered the way the model likes. Production does not.

## Layer 4: Generation

**Question: does the output say the right thing?**

This is the layer everyone jumps to, and it is the one with the most measurement error.

The 2023 NeurIPS MT-Bench paper found GPT-4 judges agreeing with human preference on more than 80% of comparisons — comparable to human-human agreement — while naming position bias, verbosity bias, and self-enhancement bias, plus "limited reasoning ability." A companion paper showed what happens when you do not defend a close comparison: under one setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries.

**Three defenses, all cheap:** swap the order. Control length. Change the judge.

**Failure mode:** a 6% score gap that reverses when you re-run.

## Layer 5: Trace

**Question: did the system do what the answer says it did?**

This layer is skipped most often and it is the cheapest to add.

A 2026 paper on agent evaluation notes that procedural failures "can look plausible in the final response" — an agent claiming it invoked a tool it never called, skipping a mandatory compliance call, ordering tool calls incorrectly. The same work treats trace analysis as necessary, and distinguishes deterministic detections (checkable against the trace) from subjective judgments. A 2026 long-context agentic benchmark went further and recommended enforcing "hard controls outside the model" — deterministic tool-call guards rather than in-context compliance.

**Failure mode:** the output is graded correct while the process violated your policy, and you find out in the audit.

## Layer 6: Human review

**Question: does a domain expert, looking at a sample, agree with the score?**

Not "is there a human in the loop" — a human who can detect the failures you care about, working on a sample, with the score attached.

The 2026 agent-evaluation paper is precise about the division. LLM judges are faster, cheaper, repeatable, and unreliable as sole authority — they may miss domain policies, required tool sequences, and trajectory-level failures. Human review remains "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions," and it is costly, slow, and hard to reproduce at every step. The recommendation is to move that expertise upstream into reusable artifacts instead of eliminating it.

**Failure mode:** assuming the judge is right because it is faster than the expert, and discovering the gap during an incident.

## Layer 7: Cost and time

**Question: does this hold at your volume, in your latency budget, at a price you can live with?**

This layer is where procurement conversations actually happen, and where benchmarks are least useful.

The 2026 long-context agentic benchmark showed how cleanly cost and score decouple. One configuration reached 21.5% on roughly 13K generated tokens per trial. Another spent close to 60K tokens at about three times the dollar cost for the same band. Several mid-pack configurations generated 45–55K tokens and scored in single digits. Raising reasoning effort helped some configurations by 2.0 to 3.0 points, left one unchanged, and hurt one by 2.7 points.

**Failure mode:** a candidate that wins on score and loses on price, chosen because nobody ran the cost column.

## Building the stack in order

The order matters more than the content.

**Layers 1 and 2 first.** No amount of layer-4 precision compensates for a layer-1 mismatch. Most evaluation crises are diagnosed here and then misfiled as model problems.

**Layer 3 next, because it is free.** Move the evidence. If the answer changes, you have found a real dependency for the cost of one re-run.

**Layers 4 and 5 together.** They are cheap, and the trace usually explains the generation failures.

**Layer 6 before you commit**, not after. A domain expert who disagrees with your eval once will not raise their hand the second time.

**Layer 7 last**, because it only matters once the earlier layers are sound.

## The stack applied to papers

Reading a paper is a stack with the same layers, and the same failure modes.

**Data layer:** does the benchmark resemble your problem? A paper strong on a benchmark you do not care about is a poor benchmark for you.

**Retrieval layer:** does the paper separate retrieval from generation, or report a combined number?

**Position layer:** does it report where in the context the evidence sat? A 2023 TACL result says that matters.

**Generation layer:** does it report the strict number or the relaxed one? The 2026 long-context benchmark noted that tolerating one violated control roughly doubles leader scores, which is worth knowing about any leaderboard you read.

**Trace layer:** can you see the steps, or only the result? The 2026 agent-evaluation work argues this is the difference between "the output looked right" and "the process was right."

**Human layer:** who signed off, and were they calibrated?

**Citation layer:** does the bibliography support the sentences? A 2026 benchmark called CiteAudit found 2,967 fabricated references out of 9,442, and separately found references that exist but whose title or author metadata does not match — which means the paper was never read. A 2026 source-attribution study found link validity above 94% and relevance above 80% while claim-level accuracy ranged from 24.4% to 76.8%.

[AUTHOR EXPERIENCE: Replace with your real account — which layer a decision you got wrong actually failed at.]

## What this cannot settle

The seven-layer structure is my synthesis. No published work validates it, and the layer boundaries are my judgment. A different practitioner would draw them differently.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints. And a stack has a structural bias toward what you can measure — the human layer and the cost layer are the hardest, which is probably why they get skipped.

The stack also does not tell you what to do when two layers conflict. A cheap layer-4 result with a broken layer-5 trace is not a good system, even though it scores well.

## Where to start this week

1. Name the layer a past decision actually failed at. Not the one you assumed.
2. Move the evidence to the middle of your context in a working example and re-run.
3. Start storing traces for one agent. One afternoon.
4. Get one domain expert to review a sample against your score. Log the disagreement rate.
5. Add the cost column to your comparison table.

## Sources

- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation ≠ validity; two-system comparison; faithfulness metrics correlate weakly.
- Chen, J. et al. (2024). *Benchmarking Large Language Models in Retrieval-Augmented Generation*. AAAI 2024. https://arxiv.org/abs/2309.01431
  - Supports: RGB's four abilities; persistent failure in negative rejection, information integration, false information.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation, including in long-context models.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; trace analysis; judges unreliable alone; human review essential for specific decisions; upstreaming expertise.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; strict vs relaxed grading; reasoning-effort variance; 13K–60K token range; hard controls outside the model.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; title/author metadata mismatch detection.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; claim-level verification design.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: "contextual unit"; theory-of-change framing; field testing; leaderboard overfitting and contamination.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Which layer have you been arguing about when you should have been fixing the layer below it?
