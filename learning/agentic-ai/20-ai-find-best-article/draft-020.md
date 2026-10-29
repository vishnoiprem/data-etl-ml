---
title: "Why 'Just Use the Best Model' Is the Most Expensive Sentence in AI"
subtitle: "The hidden cost of a default choice — and a framework for deciding when a default is right and when it is laziness."
tags:
  - ai-evaluation
  - ai-strategy
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - technical-leadership
  - ai-engineering
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1490
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 87
hard_fail: false
distinctness_angle: "Argument-first piece — the cost of defaults, framed as an economic and organisational decision rather than an evaluation method; defaults as the default"
sources_count: 9
author_experience_placeholders: 1
---

"Just use the best model."

It is the most common sentence in AI tool selection, and it is expensive in a way that does not show up in the invoice.

## What a default actually costs

A default is not free. It is a decision you have delegated to someone else's evaluation, and you have inherited someone else's criteria.

Three costs, in increasing order of how long they take to notice.

**The performance cost.** The default is optimized for a public average, and your job is not the public average. A 2025 evaluation-ecosystem paper argues the unit of evaluation is not the model but the "contextual unit" — the behavior of a person using AI in a setting — and that static datasets poorly reflect deployment conditions. A 2025 software-engineering agent survey is more direct: benchmark scores should guide rather than determine tool choice, and candidates should be compared on your repository, language, context length, test strength, contamination exposure, latency, and cost.

None of those seven dimensions are what a leaderboard ranks. A default gets you the answer to a question you did not ask.

**The measurement cost.** Here is the number that should end the argument for most teams. In a 2026 study of RAG evaluation metrics, two human evaluators' ratings correlated with each other at a Pearson correlation of **0.85**. That is the practical ceiling for any automatic proxy metric you deploy. RAGChecker produced the strongest overall correlations among those tested, with claim recall near 0.7 — and the authors explicitly warned that high correlation does not establish validity, because question difficulty and other confounders produce strong correlations on their own.

So a default gives you a score with an unknown relationship to your actual quality. You have not saved the evaluation; you have taken the evaluation on loan, without knowing the interest rate.

**The coupling cost.** This is the one nobody names. A default creates a dependency you did not design.

A 2025 paper, ToolTweak, showed that a tool's *name and description* — not its schema, not its implementation — can be rewritten by a gradient-free black-box attack to swing selection likelihood. Against an approximately 20% baseline, the best rates reached 81.6% for one model and 34.0% for another. The attack shifts the overall selection distribution away from expected parity, which the paper frames as a risk to "fairness, competition, and security in emerging tool ecosystems."

The same logic applies to your model default. If a vendor's marketing copy is what routes traffic to their tool, then your traffic routing is a function of their copy. The 2026 source-attribution study gives a parallel data point in a different domain: across 14 models, link validity exceeded 94% and topical relevance exceeded 80% — so the cheap, visible signals all looked healthy — while claim-level accuracy ranged from 24.4% to 76.8%. What looks like quality on the surface was frequently not quality underneath.

## When a default is right

I want to be clear that "just use the best model" is sometimes correct. It is wrong as a principle and right as a shortcut under specific conditions.

**A default is right when the job is generic and the error is cheap.** Summarizing a meeting transcript, drafting a reply to a routine question. A 2023 paper on instruction finetuning is the useful reference here: instruction finetuning on instruction-phrased datasets improves performance and generalization to unseen tasks, and Flan-PaLM 540B finetuned on 1.8K tasks outperformed PaLM 540B by "+9.4% on average" and reached "75.2% on five-shot MMLU." When the task family is well-covered and a mistake costs a rewrite, a strong general model is genuinely the right answer.

**A default is right when you have no capacity to evaluate.** Not ideal — but the real alternative to a default is often no tool at all. Running the strongest general model beats running nothing.

**A default is right when the failure is genuinely trivial.** If the worst outcome is a slightly awkward email, spend your evaluation budget elsewhere.

## When a default is wrong

**When the failure is procedural.** A 2026 paper on agent evaluation notes that procedural failures "can look plausible in the final response" — an agent claiming a tool it never invoked, skipping a mandatory compliance call, calling tools in the wrong order. A 2026 long-context agentic instruction following benchmark went further and recommended enforcing "hard controls outside the model," compiling policies into deterministic tool-call guards rather than relying on in-context adherence. Its best configuration scored **36.2% strict pass@1** — still failing nearly two of every three tasks — and it noted that relaxing the strict criterion to tolerate one violated control roughly doubles leader scores. In that regime, model choice is the wrong lever entirely. Architecture is.

**When the failure is in the evidence.** If the wrong thing gets retrieved and cited confidently, the model is not the variable. The 2023 TACL paper "Lost in the Middle" is relevant: models perform best at the beginning or end of the context and "significantly degrades when models must access relevant information in the middle," including in explicitly long-context models. A 2025 survey adds that long context alone is not a substitute for effective retrieval, and that snippet ordering materially affected performance.

**When the domain is regulated.** A 2026 agent-evaluation paper is explicit that human review remains "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions" in healthcare, finance, privacy, legal, and security settings — while acknowledging that doing it at every step is costly, slow, and hard to reproduce. Where the cost of a human's judgment is high, you want the review, not the default.

**When scale is the failure mode.** A 2025 retrieval-based tool-selection study found that presenting every tool schema dropped selection accuracy to **13.62%**, while retrieving the relevant schema raised it to **43.13%** and cut average prompt usage from 2,133.84 tokens to 1,084. Accuracy degraded beyond roughly **100 candidates** as retrieval precision declined. A default that assumes a small world stops working as your world grows.

## The framework: default, adapt, or replace

**Default** when the job is generic, the error is cheap, and you lack evaluation capacity. Use the strongest general model. Do not spend a week on this.

**Adapt** when the job is specific but the category is clear. Match the candidate type to the task — instruction-tuned for straightforward work, long-context for ordered-context problems, supervised fine-tuning for consistent domain behavior, preference alignment for objectives that are hard to demonstrate. Then test on your own task set, with the cheap disqualifiers: swapped order, moved evidence position, doubled candidate pool.

**Replace** — or build — when the failure is procedural, when a hard control is required, or when the domain demands expert review. Here you are not choosing a model, you are designing a system. A 2026 agent-evaluation paper's recommendation is the right one: move expert knowledge upstream into reusable evaluation artifacts rather than reviewing every trajectory.

## A note on cost, since the default usually looks cheaper

Defaults look cheap on the invoice and are often more expensive in tokens. In the long-context agentic benchmark, one configuration reached 21.5% on roughly 13K generated tokens per trial, while another spent close to 60K tokens at about three times the dollar cost for the same band. Several mid-pack configurations generated 45–55K tokens and scored in single digits. Raising reasoning effort helped some configurations by 2.0 to 3.0 points, left one unchanged, and hurt one by 2.7 points.

And in a 2026 source-attribution study, across GPT-5.4 and Claude Opus 4.6, fact-check accuracy fell by roughly 42 percentage points on average as tool calls rose from 2 to 150 — while link validity and topical relevance stayed above 92% throughout. More searching, less accurate attribution.

**The general pattern:** effort and token spend are not quality. Neither is a default.

[AUTHOR EXPERIENCE: Replace with your real account — a default you inherited, and what it actually cost.]

## What this cannot settle

The default/adapt/replace framing is mine. No published work validates it, and the boundaries between the three are judgment calls.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024, ICLR 2023, ACL 2022 — are also the older ones. The 2022 instruction-finetuning numbers describe models that no longer lead the field; the point is structural, not current.

And the framework does not tell you which default to pick. It tells you whether picking a default is a decision or an abdication.

## Where to start this week

1. List the AI defaults your team uses without having evaluated.
2. Pick the one whose failure would be most expensive.
3. Build 20 questions from real closed work and test it.
4. Decide: default, adapt, or replace.
5. Put a 90-day re-check on the calendar for whatever you chose.

## Sources

- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; static tasks poorly reflect deployment.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: category matching by task complexity; scores guide not determine; long context not a substitute for retrieval.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation ≠ validity.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; ~42-point drop from 2 to 150 tool calls.
- *ToolTweak* (2025). arXiv:2510.02554. https://arxiv.org/html/2510.02554v1
  - Supports: name/description attack; 81.6%–34.0% vs ~20% baseline; distribution shift; metadata defenses.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures; human review essential for specific decisions; upstreaming expertise.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; 13K vs 60K tokens at ~3× cost; reasoning-effort variance; hard controls outside the model; strict vs relaxed grading.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: 13.62% vs 43.13%; 2,133.84 → 1,084 tokens; degradation beyond ~100 candidates.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation.
- Chung, H. W. et al. (2022). *Scaling Instruction-Finetuned Language Models*. ICLR 2023. https://arxiv.org/abs/2210.11416
  - Supports: instruction finetuning improves generalization; 1.8K tasks, +9.4% average, 75.2% five-shot MMLU.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Which of your team's AI defaults have never been evaluated — and which one would hurt most if it failed?
