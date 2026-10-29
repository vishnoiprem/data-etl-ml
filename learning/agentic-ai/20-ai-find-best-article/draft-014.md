---
title: "Why Your AI Tool Evaluation Keeps Failing, and What to Build Instead"
subtitle: "Six failure patterns in evaluation infrastructure, each with the published finding that predicts it."
tags:
  - ai-evaluation
  - evaluation-infrastructure
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - ai-engineering
  - debugging
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1480
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 89
hard_fail: false
distinctness_angle: "Symptom-to-cause diagnostic — six named evaluation-infrastructure failure patterns, each paired with the published finding that predicts it and the fix"
sources_count: 10
author_experience_placeholders: 1
---

When an AI evaluation goes wrong, it usually goes wrong in one of six ways, and the symptom is always the same: the number looks fine and the decision is wrong.

Here are the six, how to recognize each, and what to build.

## Pattern 1: the metric tracks the humans for the wrong reason

**Symptom:** your eval correlates well with human ratings, and the ranking still disagrees with what experts say.

**Why it happens:** correlation and validity are different things. A 2026 study of RAG evaluation metrics is the sharpest statement of this. Two human evaluators' ratings correlated at a Pearson correlation of 0.85 — the practical ceiling for any proxy. RAGChecker produced the strongest overall correlations, with claim recall near 0.7. But the authors warn that high correlation does not establish validity, because input difficulty and other confounders can produce strong correlations on their own.

They also found something worth knowing: RAGChecker claim recall was near 0.7, raising the concern that it may reflect question difficulty or answer extractability rather than retrieval quality alone.

**What to build:** the two-system comparison. Evaluate at least two RAG systems and compare their outputs on the same questions, so shared difficulty cancels. The same paper also recommends evaluating against more than one system generally, and notes its own single-system design could not establish full metric validity.

## Pattern 2: the ranking reverses when you rerun

**Symptom:** you re-ran the eval and got a different winner. Not a small shift — a different winner.

**Why it happens:** the judge has position, verbosity, and self-enhancement biases, and comparisons are order-dependent.

The 2023 NeurIPS MT-Bench paper names all three biases and the limitation "limited reasoning ability." Its finding that GPT-4 agreed with human preference on more than 80% of comparisons is genuinely good — and it is measured against a comparison method that the same paper shows is fragile.

The companion paper, "Large Language Models are not Fair Evaluators," showed that changing presentation order changes rankings: under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. Its calibration framework included a human-in-the-loop component triggered by "balanced position diversity entropy," a measure of example difficulty.

**What to build:** order-randomized evaluation as the default. Run every comparison in both orders and report the disagreement rate. If your eval has a 10% flip rate, a 6% gap means nothing.

## Pattern 3: the score is right and the process was wrong

**Symptom:** output quality holds up, and something else breaks. A skipped compliance call. A tool that was claimed but never invoked. A tool called in the wrong order.

**Why it happens:** you are grading the answer instead of the trajectory.

A 2026 paper on agent evaluation is explicit: procedural failures "can look plausible in the final response." The examples it names are precise — claiming a tool was used without invoking it, omitting mandatory compliance calls, calling tools in the wrong order. The same work argues trace analysis is necessary rather than optional, and distinguishes deterministic detections (a phantom tool call, checkable against the trace) from subjective judgments.

**What to build:** trace storage, from day one. A 2026 long-context agentic benchmark went further and recommended enforcing "hard controls outside the model" — compiling policies into deterministic tool-call guards rather than trusting in-context adherence. Its best configuration scored 36.2% strict pass@1. It also noted that relaxing the strict criterion to tolerate one violated control roughly doubles leader scores, which means your relaxed score and your strict score are different measurements and you should know which you are reporting.

## Pattern 4: it worked in the eval and fails in production

**Symptom:** the eval passes. Production produces garbage.

**Why it happens:** three separate things, and you should check all three.

**Input mismatch.** A 2025 evaluation-ecosystem paper argues the unit of evaluation is the "contextual unit" — the behavior of people using AI in context — and recommends field testing with real users across repeated sessions, alongside context specification with stakeholders and red teaming. A 2025 software-engineering agent survey puts it operationally: benchmark scores should guide rather than determine tool choice, and you should compare candidates on your repository, language, context length, test strength, contamination exposure, latency, and cost.

**Contamination.** The same survey notes that a benchmark drawn from public repositories may already have appeared in pretraining or fine-tuning data — which is why a dedicated contamination benchmark exists at all. Unfamiliarity cannot safely be assumed.

**Position.** The 2023 TACL paper "Lost in the Middle" found models perform best when relevant material appears at the beginning or end of the context and "significantly degrades when models must access relevant information in the middle," including in explicitly long-context models. Your eval data probably has a different ordering convention than production data.

**What to build:** a production-shaped eval. Real inputs, real ordering, real volume. And a contamination check on the benchmark you are leaning on.

## Pattern 5: more effort made it worse

**Symptom:** you gave the model more tools, more tokens, more reasoning budget, and the result got worse.

**Why it happens:** because the effort was aimed at the wrong failure.

In a 2026 study of source attribution in AI research reports, across GPT-5.4 and Claude Opus 4.6, fact-check accuracy fell by roughly 42 percentage points on average as tool calls rose from 2 to 150. One model dropped from 78.6% to 16.7%, another from 80.0% to 57.9%. Link validity and topical relevance stayed above 92% the whole time — the model kept finding accessible, on-topic pages and got worse at attributing specific facts.

In the long-context agentic benchmark, raising reasoning effort helped some configurations by 2.0 to 3.0 points, left one unchanged, and hurt one by 2.7 points, while token spend ranged from roughly 13K to 60K per trial with no clean relationship to score.

**What to build:** a diagnostic that tells you which failure you have. Missed inference or missed read? The 2026 benchmark's authors interpret it exactly this way — deliberation converts into compliance only when the underlying error was a "missed inference rather than a missed read." If it is a missed read, more reasoning cannot help and you are paying four times for nothing.

## Pattern 6: the candidate list grows and nothing works

**Symptom:** selection quality dropped after you added tools, and you assumed the model got worse.

**Why it happens:** because you put everything in the context.

A 2025 study of retrieval-based tool selection measured this directly. Presenting every tool schema to the model dropped selection accuracy to 13.62%. Retrieving just the relevant schema raised it to 43.13% and cut average prompt usage from 2,133.84 tokens to 1,084. The same work found accuracy degrading beyond roughly 100 candidates as retrieval precision declined, and proposed hierarchical or adaptive retrieval for larger registries.

A second 2025 paper explains why this is not merely a scale problem. ToolTweak demonstrated a gradient-free black-box attack that rewrites a tool's name and description — leaving the parameter schema untouched — to increase the likelihood an agent selects it. Against an approximately 20% baseline, best selection rates reached 81.6% for one model and 34.0% for another. The attack shifts the overall selection distribution away from expected parity, which the paper frames as a risk to "fairness, competition, and security in emerging tool ecosystems."

**What to build:** a routing layer, and a metadata audit. If a competitor rewrote their description tomorrow, how much of your traffic moves?

## The six patterns, in one line each

| Pattern | Symptom | Build this |
|---|---|---|
| 1 | Metric correlates, decision disagrees | Two-system comparison on the same questions |
| 2 | Rerun flips the winner | Order-randomized eval with a reported flip rate |
| 3 | Output fine, process wrong | Trace storage and deterministic guards |
| 4 | Eval passes, production fails | Production-shaped eval, contamination check, position test |
| 5 | More effort, worse result | Missed-inference vs missed-read diagnostic |
| 6 | More tools, worse selection | Routing layer plus metadata audit |

## For papers, the same six

Pattern 1 becomes: does the paper's metric measure what it claims? Pattern 2 becomes: does the ranking depend on evaluation order? Pattern 3 becomes: does the paper's method survive trace-level inspection? Pattern 4 becomes: does the benchmark resemble your data? Pattern 5 becomes: did the authors' added complexity buy anything? Pattern 6 becomes: does the bibliography hold up?

And the specific citation check that pattern 3 demands: a 2026 benchmark called CiteAudit found 2,967 fabricated citations out of 9,442, and separately found references that exist but whose title or author metadata does not match — which means the cited paper was never read. A 2026 source-attribution study makes the same case from the other side: link validity above 94%, relevance above 80%, claim-level accuracy 24.4%–76.8%. Check the claim, not the link.

[AUTHOR EXPERIENCE: Replace with your real account — which pattern your last evaluation hit, and how long it took you to notice.]

## What this cannot settle

The six-pattern taxonomy is my synthesis. No published work validates it, and a given real failure often looks like two patterns at once. The mapping from symptom to cause is judgment, not measurement.

The numbers are setup-specific and dated. The judge figures come from 2023-era models; the 2026 agent-evaluation work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024, ICLR 2023 — are also the older ones.

And pattern coverage is not diagnosis. If your eval disagrees with production, the cause might be a seventh pattern I have not named.

## Where to start this week

1. Identify which pattern your last evaluation hit.
2. Run your comparison in both presentation orders and compute the flip rate.
3. Start storing traces for one agent.
4. Check your benchmark for contamination before trusting it.
5. Add a "missed inference or missed read?" line to your eval report.

## Sources

- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7 and the difficulty confound; correlation ≠ validity; two-system comparison.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result; position-diversity-entropy trigger.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; trace analysis; judges unreliable alone; human review essential.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; relaxed grading roughly doubles scores; reasoning-effort variance; missed-inference vs missed-read interpretation; 13K–60K tokens; hard controls outside the model.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; ~42-point drop from 2 to 150 tool calls; 78.6%→16.7% and 80.0%→57.9%.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: 13.62% vs 43.13%; 2,133.84 → 1,084 tokens; degradation beyond ~100 candidates.
- *ToolTweak* (2025). arXiv:2510.02554. https://arxiv.org/html/2510.02554v1
  - Supports: name/description attack; 81.6%–34.0% vs ~20% baseline; distribution shift; metadata defenses.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation in long contexts.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; metadata mismatch detection.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; field testing; leaderboard overfitting and contamination.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: contamination via DyCodeEval; scores guide not determine; selection dimensions.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Which of the six patterns did your last evaluation hit — and how long did it take to see it?
