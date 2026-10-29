---
title: "The Selection Meeting Is the Wrong Room: Where AI Tool Decisions Actually Get Made"
subtitle: "A diagnosis of how decisions get talked into a winner, and a relocation of the work to where it survives."
tags:
  - ai-evaluation
  - model-selection
  - technical-writing
  - llm
  - how-to-evaluate-llm-tools
  - ai-engineering
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1405
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 87
hard_fail: false
distinctness_angle: "Process-and-venue frame — locates the failure of tool decisions in the meeting format itself, then argues for relocating evaluation to an asynchronous artifact-and-log practice"
sources_count: 9
author_experience_placeholders: 1
---

The selection meeting does not decide anything. It ratifies.

Four people, forty minutes, three slides, and a conclusion that was reached before anyone walked in. The meeting exists to convert a private impression into a shared document — which is useful, but it is not a decision procedure.

Here is what goes wrong, and where the work should go instead.

## Symptom one: the loudest anecdote wins

The most persuasive input in a selection meeting is a story about one incident. One output that was wrong in a way that embarrassed someone. One demo that was flawless.

Neither is a measurement, and the asymmetry is brutal: a bad anecdote is vivid, specific, and attributable, while the thirty-question set that would settle the question is abstract and requires work nobody wants to do in a meeting.

A 2025 survey of software-engineering agents makes the operational point: benchmark scores should guide rather than determine tool choice, and candidates should be compared on your repository, language, context length, test strength, contamination exposure, latency, and cost. Every item on that list requires measurement, and none of them arrive in a slide.

## Symptom two: the demo is mistaken for the distribution

Demos are made to look good. That is the job of the person running them, and it is not deception — it is selection of the case.

A 2025 survey of software-engineering agents documents the arc from small function-generation tasks like HumanEval and MBPP to repository-level suites with real GitHub issues, pull requests, cross-file dependencies, and executable test environments. The progression exists because the small clean tasks did not represent the work.

A 2025 evaluation-ecosystem paper puts the general claim: static datasets and constrained tasks poorly reflect deployment conditions, and the unit of evaluation should be the "contextual unit" — the adaptive behavior of people using AI in a setting. A demo is the opposite of a contextual unit. It is one curated instance with an attentive audience and no consequence.

## Symptom three: the number on the slide is inherited

Somebody read a leaderboard at some point. The number is in the deck. Nobody in the room knows the grading rule.

A 2026 benchmark for long-context agentic instruction following reported strict pass@1 alongside a relaxed variant tolerating one violated control, and found that relaxing roughly doubles leader scores. Its best configuration scored **36.2% strict pass@1** — still failing nearly two of every three tasks. If the slide carries the relaxed number, the room is comparing a 36% system against a 70% system and calling the difference a 2× gap.

A 2026 study of RAG evaluation metrics adds the deeper problem: human evaluators' ratings correlated with each other at **Pearson 0.85**, RAGChecker claim recall was near **0.7**, and high correlation does not establish validity because input difficulty and other confounders produce strong correlations on their own. Any slide number without a denominator and a grading rule is a shape, not a quantity.

## Symptom four: the meeting cannot produce evidence

This is the structural problem. A meeting can compare claims. It cannot generate data. Every attempt to make the meeting itself the experiment — "let's try a few prompts live" — produces a result about three hand-picked prompts, with a confounding variable (the person typing) that nobody controls for.

The 2026 metrics study's method is the opposite: evaluate at least two systems and compare their outputs on the same questions, so shared difficulty cancels. That is an offline activity, done before the meeting, and it takes an afternoon.

## Symptom five: the decision has no owner in the room

The 2023 NeurIPS MT-Bench paper found GPT-4 as a judge agreeing with human preference on more than 80% of comparisons — comparable to agreement between humans — while naming position bias, verbosity bias, and self-enhancement bias, plus "limited reasoning ability." The companion paper showed that under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. A ranking that flips on ordering is a property of the procedure, not the models.

In a meeting, this shows up as a decision that "everyone agrees on" and that nobody could reconstruct three months later. Ask who ran the evaluation. If nobody in the room did, the meeting produced a preference, not a decision.

## Where the work should go

Relocate evaluation out of the meeting and into an artifact, and let the meeting ratify the artifact.

**Before the meeting: generate the evidence.** The evaluation set, the two candidate runs, the human correlation baseline, the cost-per-successful-run figure, the trace review. All offline, all on the same questions, all before anyone discusses preference.

**The artifact.** A one-page memo with the job, the candidates including the excluded ones with reasons, the criteria and their weights, the evidence with denominators and dates, the decision in one sentence, the reasoning in one sentence, and the reversal conditions in numbers plus a re-check date.

**In the meeting: read the memo, challenge it, record the reversals.** Twenty minutes, and the only questions worth asking are the ones the memo cannot answer — a criterion nobody weighted, a risk the memo omits, a reversal condition set at the wrong threshold.

**After the meeting: the memo is the record.** A 2026 agent-evaluation paper makes the structural argument for evaluations generally: move expert knowledge upstream into reusable artifacts so it survives the person who wrote it, and keep human review focused on domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions. The memo is that artifact in miniature.

## What the relocation costs

Honest accounting, because a relocation is also a trade.

**It takes longer before you have an answer.** An afternoon of evaluation instead of forty minutes of discussion. If the real decision window is a week, that fits. If it is tomorrow, it does not, and you should write that down as a known risk rather than pretend the meeting was rigorous.

**It requires someone to own the measurement.** Not everyone enjoys building evaluation sets. But the work is a bounded, well-specified job, and a 2025 evaluation-ecosystem paper's point about the "contextual unit" being the real subject of evaluation means the set cannot be outsourced to a generic benchmark.

**It exposes disagreements that the meeting would have smoothed over.** Which is a cost and a benefit, but mostly a benefit. A disagreement surfaced at the memo stage is cheap to resolve. A disagreement buried in a group decision is expensive to discover.

**It is less fun.** Nobody enjoys an afternoon of writing down failure rules. Nobody enjoys a meeting either, though the meeting is a different kind of unpleasant.

## The one-line version

Decide in a document, ratify in a meeting.

If the meeting can change the decision, the meeting was the evaluation, and it was not a good one. If the meeting can only challenge the document, then the document was the evaluation, and it was a good one.

[AUTHOR EXPERIENCE: Replace with your real account — a selection meeting where the real evidence was assembled after the decision, and how that turned out.]

## What this cannot settle

The relocation pattern is my construction. No published work validates it, and organizations with a genuine need for consensus — a regulated sign-off, a multi-department rollout — have reasons for the meeting that the diagnosis does not address.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And a memo can be a polished rationalization of a decision already made. The relocation only helps if the memo is written before the meeting and cannot be edited afterwards without a new version.

## Where to start this week

1. Look at the last decision memo you have. Does it exist?
2. If not, write one for a live decision before the next meeting.
3. Move all data collection out of the meeting. Agenda: challenge the document.
4. Add a reversal-conditions section with numeric triggers.
5. Put a re-check date on the calendar.

## Sources

- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: HumanEval/MBPP to repository-level suites; comparison dimensions; scores guide not determine.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; static-task limits; leaderboard overfitting and saturation.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; strict vs relaxed grading roughly doubling scores.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation ≠ validity; two-system comparison.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: upstreaming expertise into reusable artifacts; human review essential for domain context, policy interpretation, rubrics, and escalation.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% link validity and 80% relevance vs 24.4–76.8% claim accuracy.
- *Evaluating LLM Metrics Through Real-World Capabilities* (2025). arXiv:2505.08253. https://arxiv.org/html/2505.08253v1
  - Supports: benchmarks prioritize abstract correctness over user-relevant qualities; leaderboard distortion.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

When you next pick a tool, will the meeting be where the evidence was generated, or where the evidence was challenged?
