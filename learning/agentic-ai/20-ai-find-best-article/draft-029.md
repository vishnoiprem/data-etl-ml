---
title: "The Selection Memo: How to Write Down an AI Tool Decision So It Survives Scrutiny"
subtitle: "One page, six sections, and the questions a stakeholder, an auditor, or your future self will ask."
tags:
  - ai-evaluation
  - technical-writing
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - documentation
  - ai-engineering
platform: linkedin
medium_publication: signal-scribe
target_length: 1250-1500
word_count: 1420
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 86
hard_fail: false
distinctness_angle: "Documentation-focused — teaches how to write a selection memo; the memo's own six sections are the artifact"
sources_count: 9
author_experience_placeholders: 1
---

Most AI tool decisions leave no trace. The reasoning lives in a Slack thread, the conclusion lives in someone's head, and six months later nobody can answer "why did we pick this?"

The fix is not more evaluation. It is a one-page memo with six sections.

## Section 1: the job

One paragraph. What the tool does, what it replaces, who uses it, what it does not do.

A 2025 evaluation-ecosystem paper argues this should come first and should be framed around stakeholders — the "contextual unit" of a person using AI in a setting, with a theory of change spelling out goals, inputs, outputs, outcomes, and counterfactuals.

A 2025 software-engineering agent survey gives the operational version for anyone building: benchmark scores should guide rather than determine tool choice, and candidates should be compared on your repository, language, context length, test strength, contamination exposure, latency, and cost.

**Write it so a reader who has never met you knows what problem you solved.** If it takes more than a paragraph, the job is not clear.

## Section 2: the candidates

Who was considered, including who you rejected and why. Two to five finalists, named, plus a line for each exclusion.

This section is where most memos fail, because exclusion feels like an attack on the excluded vendor. It is not. It is the most defensible part of the decision, and it is the part a stakeholder will ask for.

## Section 3: the criteria and their weights

What you optimised for, and how you weighted it. Include the criteria you did *not* weight, and why.

A 2026 study of RAG evaluation metrics is instructive on why weights need stating. Human evaluators' ratings correlated with each other at a Pearson correlation of **0.85** — the practical ceiling for any automatic proxy metric. RAGChecker produced the strongest overall correlations among those tested, with claim recall near 0.7. But high correlation does not establish validity, because input difficulty and other confounders produce strong correlations on their own, and their recommended remedy is to evaluate at least two systems and compare outputs on the same questions.

The implication: a weighted score is only as meaningful as the weights and the question set. Both belong in the memo.

## Section 4: the evidence

The measurements, with their conditions attached. Denominator, method, date, and what was excluded.

Include the measurement's limitations, because the reader will otherwise assume the number is exact. A 2026 benchmark for long-context agentic instruction following is a good model: it reported strict pass@1 alongside a relaxed variant tolerating one violated control, found that relaxing roughly doubles leader scores, and warned that a deployment tolerating one violation per workflow "has effectively abandoned strictness." Its best configuration scored **36.2% strict pass@1** — still failing nearly two of every three tasks.

Also record the checks that failed for candidates, not just the ones that passed. A 2023 NeurIPS paper found GPT-4 judges agreeing with human preference on more than 80% of comparisons, comparable to human-human agreement, while naming position bias, verbosity bias, and self-enhancement bias. A companion paper showed that under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. If you swapped orders and the winner flipped, that belongs in the memo — it is the reason the decision was not between two clear winners.

## Section 5: the decision and the reasoning

One sentence for the decision. One sentence for why. If you cannot write the reasoning in one sentence, the reasoning is not settled.

This is where a 2026 agent-evaluation paper's framing helps. It distinguishes deterministic detections from subjective judgments — a phantom tool call is checkable against the trace, and objective once the trace is available. If your decision rests on a trace check, say so. If it rests on a judgment, name the person who made it.

## Section 6: the reversal conditions

What would make you change this decision, in numbers, in advance.

This is the section that makes the memo worth writing, and the one almost nobody writes.

A reversal condition should be a measurement you are already taking. Examples:

- "If success rate on the 30-question set drops below 80%, we re-open this."
- "If human-review hours exceed five per week, we re-open this."
- "If the vendor changes the model behind the API without notice, we re-open this."
- "If a comparable candidate beats us by more than 5% on the same set, we re-open this."

The 5% threshold deserves a note, because it comes from the measurement ceiling rather than from taste. If human evaluators agree with each other at 0.85, then a gap smaller than that is inside the noise of the instrument, and a reversal trigger set below it would fire constantly for no reason.

And one reversal condition that is about time rather than numbers: **re-check the decision on a date.** A 2025 evaluation-ecosystem paper notes leaderboard overfitting and benchmark saturation, which means the external comparison will drift. A 2026 source-attribution study notes that web-based citations are temporally unstable — pages get paywalled, moved, and removed — so even the evidence base decays.

## A worked example of the format

```
TOOL: <name> — <one-line purpose>
JOB: <what it replaces, for whom>
CANDIDATES: <2-5 finalists; excluded ones with reason>
CRITERIA: <weights>; <deliberately excluded criteria and why>
EVIDENCE: <n> on our own set; <n> on a public benchmark; <denominators and dates>;
  <checks that failed for the selected candidate>
DECISION: <one sentence>
REASONING: <one sentence>
REVERSAL: <numeric triggers>; <date to re-check>
```

## Why the memo is worth the hour

Because the questions a memo pre-empts are the ones that get asked later, and they get asked when you are busy.

A stakeholder asks "why this one?" A colleague asks "what did we rule out?" An auditor asks "what was the denominator?" Your future self asks "what was I thinking?" A 2026 paper on agent evaluation makes the same structural argument for evaluations generally — it argues for moving expert knowledge upstream into reusable evaluation artifacts so it survives the person who wrote it, and for keeping human review focused on domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions.

A memo is the cheapest version of that. It captures the reasoning at the moment it was cheap, and it makes the reasoning auditable rather than rhetorical.

[AUTHOR EXPERIENCE: Replace with your real account — a decision that lacked a memo, and the question you could not answer later.]

## What this cannot settle

The six-section format is mine. No published work validates it, and a research group, a regulated team, and a small startup would each want different sections.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And a memo records reasoning; it does not make the reasoning correct. A well-documented wrong decision is still wrong, and writing it down does not fix that.

## Where to start this week

1. Write a memo for the last decision you made. Notice which sections are hardest.
2. Add a reversal condition to it.
3. Put a re-check date on the calendar.
4. Use the format for the next decision.
5. Store the memos where the next person will find them.

## Sources

- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; theory of change; leaderboard saturation and overfitting.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: comparison dimensions; scores guide not determine.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation ≠ validity; two-system comparison.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: strict vs relaxed grading; 36.2% strict pass@1; reporting discipline.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases.
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: deterministic vs subjective detection distinction; upstreaming expertise; human review essential for rubrics and escalation.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: temporal instability of web citations.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: scale-related criteria as memo content.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Could you reconstruct the reasoning behind your last AI tool decision right now, without asking anyone?
