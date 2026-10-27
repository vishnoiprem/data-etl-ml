---
title: "A Working Method for Choosing AI Models, Tools, and Papers"
subtitle: "Nine questions, asked in order, that take a shortlist from vague to decided in an afternoon."
tags:
  - ai-evaluation
  - decision-framework
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - ai-engineering
  - technical-decisions
platform: linkedin
medium_publication: signal-scribe
target_length: 1350-1600
word_count: 1520
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 88
hard_fail: false
distinctness_angle: "Nine-question sequential protocol with explicit ordering rationale and a worked example run end to end; each question mapped to one published finding"
sources_count: 10
author_experience_placeholders: 1
---

A shortlist of four candidates. An afternoon. Here is what I ask, in this order, and why the order is the whole trick.

The order matters because each question makes the next one cheaper. Ask them out of order and you burn a day on a candidate that question two would have eliminated.

## Q1. What job, in one sentence?

*"I need this to do X. The failure I cannot afford is Y."*

This is not a warm-up. A 2025 evaluation-ecosystem paper argues that the unit of evaluation is not the model but the "contextual unit" — the behavior of a person using AI in a setting — and recommends specifying a theory of change with stakeholders before comparing anything: goals, inputs, outputs, outcomes, counterfactuals.

A job statement with a named failure also tells you the *type* of candidate to look for, which is where the second question comes from.

## Q2. What kind of candidate does this job need?

Not "which model" — which *category*, and the categories have different selection criteria.

A 2025 survey of software-engineering agents lays out the matching directly. Straightforward generation, explanation, or small edits want an ordinary instruction-tuned model. Repository relationships and carefully ordered context want a structured or long-context model. Behavior that must consistently follow domain workflows or patch formats wants supervised fine-tuning. Objectives that are hard to express through demonstrations — security, efficiency, correctness under executable feedback — want preference alignment or reinforcement learning.

That survey also gives the single most quotable line for this whole question: **benchmark scores should guide rather than determine tool choice.** Compare candidates on your repository, your language, your context length, your test strength, contamination exposure, latency, and cost.

## Q3. Where will the failure show up?

Three places. Which one applies determines most of the remaining work.

**In the answer.** Then quality scoring is the right instrument, with the caveats in Q5.

**In the process.** Then you need traces, not scores. A 2026 paper on agent evaluation is explicit: procedural failures "can look plausible in the final response." Agents claim tools they never invoked, skip mandatory compliance calls, call tools in the wrong order. The prose reads fine.

**In the evidence.** Then you need retrieval scored separately, and you need to know about position. The 2023 TACL paper "Lost in the Middle" found models perform best when relevant material appears at the beginning or end of the context and "significantly degrades when models must access relevant information in the middle" — explicitly long-context models included. A 2025 survey adds the engineering version: "Long context alone is not a substitute for effective retrieval," and snippet ordering materially affected performance.

## Q4. What can you actually catch, and how fast?

**The catcher determines the cost of the candidate.**

A 2026 agent-evaluation paper gives the division. LLM judges are faster, cheaper, and repeatable, but unreliable as a sole evaluation authority — they may miss domain policies, required tool sequences, and trajectory-level failures. Human review remains "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions," and it is costly, slow, and hard to reproduce at every step. Its recommendation: move expert knowledge upstream into reusable evaluation artifacts.

A 2026 long-context agentic benchmark makes the same point from the enforcement side, recommending "hard controls outside the model" — deterministic tool-call guards rather than in-context compliance.

So the answers are: a deterministic check, a domain expert on a sample, a judge at scale, or nobody. If the answer is nobody, stop here. There is no decision to make.

## Q5. How good is your measurement, really?

This is the question that most people skip, and it is the one that decides whether the rest of the afternoon is worth anything.

A 2026 study of RAG evaluation metrics gives the number: two human evaluators' ratings correlated at a Pearson correlation of **0.85**. That is the practical ceiling for a proxy metric. RAGChecker produced the strongest overall correlations, with claim recall near 0.7. But the authors warned that high correlation does not establish validity, because question difficulty and other confounders produce strong correlations on their own — and their own dataset was 96 questions, wide confidence intervals.

The method for getting past this: evaluate at least two systems and compare their outputs on the same questions, so shared difficulty cancels.

**Rule of thumb: if your candidates are within roughly 15% on your metric, your metric did not separate them.** Go to a shadow run.

## Q6. Does the ranking survive a swap?

One test. Swap the presentation order of the two candidates and re-run.

The 2023 NeurIPS MT-Bench paper found GPT-4 judges agreeing with human preference on more than 80% of comparisons — comparable to human-human agreement — while naming position bias, verbosity bias, and self-enhancement bias, plus "limited reasoning ability." A companion paper, "Large Language Models are not Fair Evaluators," showed the stakes: under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries.

Three cheap defenses, run together: swap the order, control for length, change the judge family. If the winner flips under any of them, you have a tie, not a winner.

## Q7. What happens at your actual size?

If you route across tools, test at the size you will operate at.

A 2025 retrieval-based tool-selection study found that presenting every tool schema dropped selection accuracy to **13.62%**, while retrieving the relevant schema raised it to **43.13%** and cut average prompt usage from 2,133.84 tokens to 1,084. Accuracy degraded beyond roughly **100 candidates** as retrieval precision declined.

A 2025 paper, ToolTweak, adds a sharper warning: a gradient-free black-box attack that rewrites a tool's name and description — schema untouched — drove selection rates against an approximately 20% baseline up to 81.6% on one model and 34.0% on another, shifting the overall distribution away from expected parity. If your routing is metadata-sensitive, the routing result tells you about your metadata, not about capability.

## Q8. What does more effort buy?

Only run this if the candidate is close, because it is the most expensive question.

Two 2026 results say effort is not reliably positive. In the source-attribution work, across GPT-5.4 and Claude Opus 4.6, fact-check accuracy fell by roughly **42 percentage points on average** as tool calls rose from 2 to 150, while link validity and topical relevance stayed above 92%. In the long-context agentic benchmark, raising reasoning effort helped some configurations by 2.0 to 3.0 points, left one unchanged, and hurt one by 2.7 points, with token spend ranging from roughly 13K to 60K per trial and no clean relationship to score.

Both point at the same distinction the benchmark's authors draw: deliberation converts into compliance only when the underlying error was a missed inference rather than a missed read. Diagnose first, then spend.

## Q9. Does the evidence in the write-up hold up?

This is the question for papers, and it should be asked of vendors too.

A 2026 benchmark called CiteAudit found 2,967 fabricated citations out of 9,442, and separately found references that exist but whose title or author metadata does not match — meaning the citing work never read the source. A 2026 source-attribution study makes the parallel case for claims: link validity above **94%** and relevance above **80%**, while claim-level accuracy ranged from **24.4% to 76.8%**.

**Check the claim against the retrieved content, not the metadata.** Pull the passage. If it is not there, the sentence does not go in the article.

## The whole method, condensed

1. Job and unacceptable failure, in one sentence.
2. Right category, not right leaderboard entry.
3. Where the failure will show up.
4. What catches it, and how fast.
5. How good your measurement actually is.
6. Does the ranking survive a swap.
7. Does it work at your size.
8. What does more effort buy.
9. Does the evidence hold up.

Nine questions, an afternoon, and a decision you can defend six months later — because you can point at which question the answer came from.

[AUTHOR EXPERIENCE: Replace with your real account — the candidate that passed all nine, and the one that failed the question you would have skipped.]

## What this cannot settle

The sequence is my construction. No published study validates the ordering, and a different practitioner would likely order Q5 and Q6 differently.

The numbers are setup-specific and dated. The judge-agreement figures are from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024, ICLR 2023 — are also the older ones.

The 15% tie threshold is judgment, not measurement. And the method cannot tell you which candidate is best — only which questions the answer is hiding behind.

## Where to start this week

1. Answer Q1 for one pending decision. One sentence.
2. Answer Q2 and stop looking at candidates of the wrong category.
3. Answer Q4. If it is "nobody," stop.
4. Run Q6 on your last comparison.
5. Put a 90-day re-check on the calendar.

## Sources

- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; theory of change.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: candidate-category matching; scores guide not determine; long context not a substitute for retrieval; snippet ordering.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures; judge limits; human review essential; upstreaming expertise.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: missed-inference vs missed-read; reasoning-effort variance; 13K–60K tokens; hard controls outside the model.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; 96-question dataset; two-system comparison.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases.
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: 13.62% vs 43.13%; 2,133.84 → 1,084 tokens; degradation beyond ~100 candidates.
- *ToolTweak* (2025). arXiv:2510.02554. https://arxiv.org/html/2510.02554v1
  - Supports: name/description attack; 81.6%–34.0% vs ~20% baseline; distribution shift.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; ~42-point drop from 2 to 150 tool calls.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; metadata mismatch detection.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Which of the nine questions would you have skipped — and what did it cost you?
