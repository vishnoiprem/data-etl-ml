---
title: "AI Tool Selection for People Who Do Not Build AI"
subtitle: "A different set of criteria for managers, analysts, and domain experts — where the evidence lives and who can actually read it."
tags:
  - ai-evaluation
  - non-technical
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - ai-literacy
  - technical-leadership
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1450
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 86
hard_fail: false
distinctness_angle: "Non-engineer audience — reframes selection for managers, analysts, and domain experts; focuses on what evidence is legible without a technical background"
sources_count: 9
author_experience_placeholders: 1
---

If you do not build AI systems, most of the selection advice written for you is unusable. It is phrased in terms of benchmarks you cannot read and failure modes you cannot test.

Here is a version that works for the person who has to make the call and defend it: managers, analysts, domain experts, and anyone else choosing tools for work that is not primarily about building AI.

## The first thing to understand: you are not choosing a model

You are choosing an arrangement of work.

This is not a semantic point. A 2025 evaluation-ecosystem paper argues that the unit of evaluation is not the model at all but the "contextual unit" — the adaptive behavior of a person using AI in a setting — and that evaluation should capture first-order effects (the outputs) alongside second- and third-order effects (behavior shifts, workforce changes, downstream impact).

For you, this means: the deliverable of a selection process is not "we chose Product X." It is "here is the arrangement, here is what it changes about our work, and here is how we will know if it is working."

## The five questions you can answer without a technical background

### 1. What work changes, and for whom?

Write one sentence: "This replaces [specific current step] for [specific people]."

A 2025 survey of software-engineering agents makes the operational version of the same idea: benchmark scores should guide rather than determine tool choice, and candidates should be compared against your actual context — your repository, language, context length, test strength, contamination exposure, latency, and cost. Translated for a non-engineer: compare against your actual work, in your actual conditions, with your actual constraints.

**The test:** name the step being replaced and the person whose day changes. If you cannot, you are shopping rather than deciding.

### 2. What is the failure you would not tolerate?

One sentence, with a consequence. This is the single most important input to the whole process.

A 2026 paper on agent evaluation gives you a taxonomy of what can go wrong, and the most important entry is the one that is invisible in the output. Procedural failures "can look plausible in the final response" — an agent claiming a tool it never invoked, skipping a mandatory compliance call, calling tools in the wrong order. If your work involves steps that must be performed rather than merely discussed, this is your failure mode, and it is invisible to you by construction.

**The test:** if the output is wrong, would you know within an hour? If not, you need a system that makes you know within an hour, and that is an architecture decision, not a model decision.

### 3. Who is accountable when it fails?

This question is often skipped and it is the one that saves you.

A 2026 agent-evaluation paper is explicit about the division of labor. LLM judges are faster, cheaper, and repeatable, but unreliable as a sole evaluation authority — they may miss domain policies, required tool sequences, and trajectory-level failures. Human review remains "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions," and it is costly, slow, and hard to reproduce at every step.

That gives you four choices, and you can make all of them:

- **A domain expert reviews a sample.** Best for policy interpretation, risk criteria, rubrics, escalation. Costly but bounded.
- **A deterministic check runs every time.** Best for rules that must hold. Cheap, and it scales.
- **A judge screens at volume.** Good for triage. Never the final word.
- **Nobody checks.** Acceptable only where the error is genuinely trivial.

A 2026 long-context agentic instruction following benchmark made the enforcement point concrete: enforce "hard controls outside the model," compiling policies into deterministic tool-call guards rather than relying on the model to comply. Its best configuration scored 36.2% strict pass@1 — still failing nearly two of every three tasks. And it noted that relaxing the strict criterion to tolerate one violated control roughly doubles leader scores. If your rule must hold every time, do not ask a prompt.

**The test:** write down the name of the person or the check that would catch it. "Nobody" is a legitimate answer for a low-stakes tool. It is not an answer for a regulated one.

### 4. What would make you switch away?

Write the trigger in advance: the metric, the failure rate, the cost, the compliance change.

A 2026 RAG metrics study gives you a defensible measurement baseline. Two human evaluators' ratings correlated with each other at a Pearson correlation of 0.85 — the practical ceiling for any automatic proxy metric. Their advice for avoiding a misleading comparison: evaluate at least two systems and compare their outputs on the same questions, so shared question difficulty cancels out.

So: if a vendor says they are 3% better, and 3% is inside the noise, that is not an improvement. Write the trigger as a number, in advance, and attach the measurement method to it.

### 5. Can you afford the review?

A 2026 agent-evaluation paper's own study ran 47 configurations, 470 trials, and 23,500 turns — and still noted that its subjective juror scores were not calibrated to human experts, and that its non-factorial design limits definitive rankings. The honest conclusion from that paper is not that evaluation is impossible. It is that human attention is the scarce resource, and you should spend it where it changes the answer.

**The test:** estimate the reviewer-hours per week. If that number is uncomfortable, move the check earlier in the process rather than cancelling it.

## The one number to remember

If you read only one thing in the evaluation literature, read this: **two people rating the same outputs agreed with each other about 85% of the time.**

Everything else follows. Your metric cannot be more reliable than that. A vendor's 3% claim is inside the noise band of two humans disagreeing 15% of the time. And a tool you have not tested on your own work is a claim, not a result.

## How to read the evidence without a technical background

You do not need to evaluate papers to benefit from them. You need to know which claims are corroborated.

**High confidence, multiple sources:** measurement quality caps decision quality. A 2026 RAG metrics study, a 2026 agent-evaluation paper, and a 2025 evaluation-ecosystem paper all say this from different directions.

**High confidence:** a working link is not verification. A 2026 study of source attribution in AI research reports found link validity above 94% and relevance above 80% across 14 models while claim-level accuracy ranged from 24.4% to 76.8%. A 2026 benchmark called CiteAudit separately found 2,967 fabricated references out of 9,442, plus references that exist but whose metadata does not match — meaning the paper was never read.

**High confidence:** more searching does not mean better answers. In that same 2026 study, fact-check accuracy fell by roughly 42 percentage points on average across two frontier models as tool calls rose from 2 to 150, even as link validity and relevance stayed above 92%.

**Worth knowing, single source:** scale cliffs. A 2025 retrieval-based tool-selection study found selection accuracy falling to 13.62% when every tool schema was in the context, and degrading beyond roughly 100 candidates as retrieval precision declined.

## What to do this month

1. Write the one-sentence work description and the one-sentence unacceptable failure.
2. Name the accountable reviewer or the check. Write it down.
3. Write the switching trigger as a number.
4. Ask each vendor for the same 20 questions from your real work and run them yourself. Two candidates, side by side.
5. Re-read the four findings above before you sign anything.

[AUTHOR EXPERIENCE: Replace with your real account — a tool you chose as a non-engineer, and what you would have checked differently.]

## What this cannot settle

The five questions are my adaptation for a non-technical audience. No published study validates them, and a technical reader would find them thinner than the frameworks they are derived from.

The numbers are setup-specific and dated. The judge-agreement figures are from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And this version is deliberately lossy. It will get you a defensible decision, not a correct one. Where your work involves a failure mode you cannot see, this framework will not tell you what you missed.

## Where to start this week

1. Draft the work sentence and the failure sentence. Together, on one line.
2. Name the catcher. Write the name.
3. Put a switching trigger in writing.
4. Build 20 questions from real closed work.
5. Run two candidates side by side, and read the same outputs yourself.

## Sources

- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; first-, second-, and third-order effects; field testing.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: compare against your actual context; scores guide not determine.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures; judges unreliable alone; human review essential; 47 configurations / 470 trials / 23,500 turns; juror calibration caveat.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; strict vs relaxed grading; hard controls outside the model.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; two-system comparison method.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; ~42-point drop from 2 to 150 tool calls.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; metadata mismatch reveals unread papers.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: 13.62% all-tools accuracy; degradation beyond ~100 candidates.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Who is accountable when the tool you chose last fails — and did you write that down before you chose it?
