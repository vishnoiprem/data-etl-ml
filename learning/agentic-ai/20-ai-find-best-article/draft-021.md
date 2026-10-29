---
title: "Choose the Tool After You Choose the Failure You Can Afford"
subtitle: "Reverse-order selection: define the unacceptable outcome first, and the candidate list almost writes itself."
tags:
  - ai-evaluation
  - ai-strategy
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - ai-engineering
  - risk
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1460
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 89
hard_fail: false
distinctness_angle: "Reverse-order argument — starts from the unacceptable failure and works backwards to the candidate list; examples inverted from the usual order"
sources_count: 10
author_experience_placeholders: 1
---

Every tool-selection process I have watched begins with the candidates.

Here is the one I use instead: begin with the failure you cannot afford, and work backwards. By the end, most candidates have disqualified themselves and you have not run a single benchmark.

## Why the forward order wastes the day

Starting with candidates means starting with an open question. You have four options and no criteria, so you evaluate everything against everything, read four comparison charts, and end up with a ranking you cannot defend.

The reverse order is different because it converts an open question into a closed one. A 2025 evaluation-ecosystem paper puts this at the center of its argument: the unit of evaluation is not the model but the "contextual unit" — the adaptive behavior of a person using AI in a specific setting — and the recommended first step is to define a theory of change with stakeholders before comparing anything. Goals, inputs, outputs, outcomes, counterfactuals.

Translated: before you know what you are buying, you should be able to say what would make you regret buying it.

## Step one: name the failure in a sentence with a consequence

Not "accuracy." Not "reliability." A sentence with a consequence in it.

*"A wrong answer gets emailed to a customer without anyone reading it."*
*"A required compliance check gets skipped and the audit trail says it ran."*
*"The agent charges a refund it was not authorised to charge."*

Each of these names a different failure family, and each family rules out different candidates before you look at a benchmark.

A 2026 paper on agent evaluation identifies the second of those precisely. Procedural failures "can look plausible in the final response" — an agent claiming a tool it never invoked, omitting a mandatory compliance call, calling tools in the wrong order. If your sentence sounds like the second one, you do not need a better model. You need a trace and a deterministic guard. A 2026 long-context agentic benchmark reached the same conclusion and made it concrete: enforce "hard controls outside the model," compiling policies into deterministic tool-call guards rather than relying on in-context adherence. Its best configuration still scored 36.2% strict pass@1, and it noted that tolerating one violated control roughly doubles leader scores.

## Step two: derive the disqualifiers from the failure

Here is where the reverse order pays. Each failure family produces its own disqualifier, and disqualifiers are cheaper than scores.

**The silent-wrong-answer failure.** You need a deterministic check that catches the wrong answer before it reaches the customer. If a candidate offers no way to verify its output — no citation, no source, no check you can run — it is out. The evidence here is unusually direct. A 2026 study of source attribution in AI research reports found link validity above 94% and topical relevance above 80% across 14 models and 130 research queries, while claim-level factual accuracy ranged from 24.4% to 76.8%. A candidate that hands you a working link and an on-topic page has given you almost nothing to catch the failure with. A candidate that gives you a claim-level check has given you the thing you need.

**The skipped-compliance-call failure.** You need a trace, and you need the check enforced outside the model. Trace analysis is not optional in this regime — the 2026 agent-evaluation work treats it as necessary because procedural failures can look plausible in the final response. The same paper describes the cost side: human review remains "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions," while LLM judges are "unreliable as the sole evaluation authority" because of position bias, verbosity bias, self-enhancement bias, and limited reasoning ability. So: encode the compliance rule as a deterministic guard, and let a human review a sample rather than every run.

**The unauthorised-action failure.** You need permissions that are enforced by the system, not requested by the model. Here a specific 2025 finding is relevant, because it shows that an agent's choice reflects more than capability. ToolTweak demonstrated a gradient-free black-box attack that rewrites a tool's name and description — schema untouched — to swing selection likelihood. Against an approximately 20% baseline, best selection rates reached 81.6% for one model and 34.0% for another, and the attack shifted the overall distribution away from expected parity. The lesson for selection: if your agent has many comparable tools, the routing result reflects the descriptions as much as the tools, and you should audit your metadata before you trust any routing data.

**The just-slightly-wrong-number failure.** Here you need a benchmark you can trust and a task set of your own. A 2025 survey of software-engineering agents says benchmark scores should guide rather than determine tool choice, and that you should compare candidates on your repository, language, context length, test strength, contamination exposure, latency, and cost. A 2026 RAG metrics study adds the measurement caveat: two human evaluators correlated at a Pearson correlation of 0.85 — the practical ceiling for any proxy — RAGChecker's claim recall sat near 0.7, and high correlation does not establish validity, because difficulty and other confounders produce strong correlations on their own. Their method: evaluate at least two systems on the same questions.

## Step three: the candidate list is now much shorter

Run this for a real shortlist and watch what happens.

*"A wrong answer reaches a customer without review."* — Disqualifier: no output verification. This removes the cheapest, highest-scoring candidate immediately. It has the best benchmark numbers and no way to catch its own mistakes.

*"A skipped compliance call."* — Disqualifier: no trace, no external enforcement. This removes the candidate with the best context window. Its long-context weakness is irrelevant next to the fact that you cannot see what it did.

*"An unauthorised refund."* — Disqualifier: no permission boundary, plus a metadata audit of the tool registry.

Two of four gone, without a benchmark. The remaining two are now competing on a question you actually care about — your task set, your reviewers, your cost.

## Step four: choose what you can defend

You now have a decision you can explain in one sentence: "We picked B because A has no way to verify its output, and our failure is a wrong answer reaching a customer."

That is a sentence you can put in a design doc, repeat in six months, and use when the vendor ships a new version.

The general principle is old and the evidence supports it: a 2025 survey of software-engineering agents recommends comparing candidates against your own context — target repository, language, context length, test strength, contamination exposure, latency, cost — and adding verifiers or human review where the work is security-sensitive or maintenance-critical.

And one last check before you commit, because it is cheap and it disqualifies more candidates than any score: **swap the order.** The 2023 NeurIPS MT-Bench paper found GPT-4 judges agreeing with human preference on more than 80% of comparisons, comparable to human-human agreement, while naming position bias, verbosity bias, and self-enhancement bias. A companion paper showed that under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. If your winner flips when you reorder the comparison, you have a tie, and you should tiebreak on cost and blast radius rather than on a number that just moved.

## For papers, the same reverse order

Start from the failure you cannot afford in your own writing.

*"I publish a claim the source does not support, and it takes months for someone to notice."* → Disqualifier: no verifiable passage. A 2026 benchmark called CiteAudit found 2,967 fabricated references out of 9,442, and separately found references that exist but whose title or author metadata does not match — which means the cited paper was never read. The source-attribution study makes the same case from the other direction: verify the claim against retrieved content, not against link validity.

*"I cite a paper for a method, and it turns out the method does not work at our scale."* → Disqualifier: no failure accounting. A 2026 long-context agentic benchmark showed why that matters — reporting a relaxed pass@1 that tolerates one violated control roughly doubles leader scores, and a strict best score of 36.2% means the leading system still failed nearly two of every three tasks.

[AUTHOR EXPERIENCE: Replace with your real account — a candidate you eliminated from the failure sentence alone, before running anything.]

## What this cannot settle

The reverse-order method is my construction. No published work validates it, and some failures are only visible after you have seen a candidate's behavior.

The numbers are setup-specific and dated. The judge figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And a failure-first method can over-index on catastrophic scenarios. If your actual failure is a slightly clunky output, you have spent the day engineering a control for a problem you did not have.

## Where to start this week

1. Write the failure sentence for one pending decision. Include the consequence.
2. Derive the disqualifier. Eliminate without benchmarking.
3. Swap the order on whatever survives.
4. Write down the one-sentence justification for your choice.
5. Set a 90-day re-check.

## Sources

- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; theory of change before comparison.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; judges unreliable alone; human review essential for specific decisions.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; relaxed grading roughly doubles scores; hard controls outside the model.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; 14 models, 130 queries; claim-level verification design.
- *ToolTweak* (2025). arXiv:2510.02554. https://arxiv.org/html/2510.02554v1
  - Supports: name/description attack; 81.6%–34.0% vs ~20% baseline; distribution shift.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation ≠ validity; two-system comparison.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: scores guide not determine; comparison dimensions; verifiers for security-critical work.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases.
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; metadata mismatch detection.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

What is the failure sentence for the tool you chose most recently — and could you have written it before you started shopping?
