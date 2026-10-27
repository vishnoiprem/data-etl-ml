---
title: "The Three-Column Comparison That Replaces the Leaderboard"
subtitle: "Task fit, failure visibility, and change cost — the only three things a comparison needs, and why the fourth column is always price."
tags:
  - ai-evaluation
  - comparison-method
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - ai-engineering
  - technical-decisions
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1490
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 89
hard_fail: false
distinctness_angle: "Comparison-table redesign — argues a specific three-column table structure and shows what each column looks like when honestly filled in"
sources_count: 10
author_experience_placeholders: 1
---

Every AI tool comparison has the same four columns: quality, price, speed, and a logo.

Here is the problem. "Quality" is a number from someone else's benchmark. "Price" is the vendor's number. "Speed" is a median that does not describe your traffic. And the logo tells you nothing at all.

Three columns would do the job better, and all three are things you can measure yourself.

## Column one: task fit

Not "how good is it." "How good is it *on your 20 questions*."

A 2025 software-engineering agent survey states the principle plainly: benchmark scores should guide rather than determine tool choice, and candidates should be compared on your repository, your language, your context length, your test strength, contamination exposure, latency, and cost. Every one of those is a description of your context, not of the tool.

For a non-coding workflow, the equivalent list is: your document types, your input lengths, your language, your edge cases, your volume, your latency budget, your tolerance for a manual review step.

**What the column looks like when filled in honestly:** a percentage out of 20–30, on your frozen question set, with the question set named. If the vendor's number appears here, the column is not doing its job.

The measurement caveat matters. A 2026 RAG metrics study found human evaluators' ratings correlated with each other at a Pearson correlation of 0.85 — the practical ceiling for any automatic proxy. RAGChecker produced the strongest overall correlations among those tested, with claim recall near 0.7, but the authors warned that high correlation does not establish validity, because difficulty and other confounders produce strong correlations on their own. Their fix: evaluate at least two systems on the same questions, so shared difficulty cancels.

So if two candidates sit within roughly 15% on this column, write "tie" rather than picking one.

## Column two: failure visibility

**How would you find out it is wrong, and how long would it take?**

This is the column that changes decisions, and it is the one no vendor table has, because a visible failure is a bad advertisement.

Two documented failure shapes, and they need different answers.

**Silent failure.** The output is wrong, and nothing tells you. A 2026 study of source attribution in AI research reports measured this across 14 models and 130 research queries: link validity exceeded **94%** and relevance exceeded **80%**, while claim-level factual accuracy ranged from **24.4% to 76.8%**. The cheap, visible signals stayed green. The expensive check failed a third to three-quarters of the time.

**Procedural failure.** The output is fine; the process did something it should not have. A 2026 paper on agent evaluation is blunt: procedural failures "can look plausible in the final response." Agents claim tools they never invoked, omit mandatory compliance calls, and call tools in the wrong order — and the prose reads correctly.

**What the column looks like when filled in honestly:** a mechanism and a duration. "Returns the source passage, reviewable in 10 minutes." "Traces every tool call, violations surface in the trace." "No verification available; detection depends on a human noticing a bad answer, historically about two weeks."

The third row is a legitimate answer. It just usually comes with a cost that should be in column one.

## Column three: change cost

**What does it cost to leave, or to change your mind later?**

This is the column teams never write down, and it is where the real money hides.

Three components:

**Migration.** Data format, schema, integration surface, retraining of anyone who learned the old way. A 2025 survey notes that repository-level work now demands executable environments, cross-file dependencies, and tests that decide whether a patch works — the integration surface of modern AI tooling is not a chat box, and the switching cost is correspondingly higher than a feature comparison suggests.

**Lock-in through routing.** A 2025 paper, ToolTweak, showed that a tool's name and description — not its schema, not its implementation — can be rewritten by a gradient-free black-box attack to swing an agent's selection likelihood. Against an approximately 20% baseline, best selection rates reached 81.6% for one model and 34.0% for another, and the attack shifted the overall selection distribution away from expected parity. If your agent routes across tools, your routing is partly a function of metadata, and migrating means re-earning that routing.

**Evaluation debt.** A 2026 long-context agentic instruction following benchmark showed how a scoring convention can inflate a result: tolerating one violated control roughly doubles leader scores. If your current numbers were produced under a relaxed convention, switching to a strict one makes everything look worse, and you will need to re-baseline before you can compare anything. Budget for that.

**What the column looks like when filled in honestly:** an estimate in days and a description of what is hard to move. "Two weeks to rewrite the integration, no re-training needed for the downstream team." "Three weeks including re-baselining under strict scoring."

## The comparison, filled in

| | Candidate A | Candidate B |
|---|---|---|
| Task fit (on your 30 questions) | 78% (24/31 correct) | 74% (23/31) — within noise, treat as tie |
| Failure visibility | Cites sources; reviewable in 10 min | No verification; detection via customer report, ~2 weeks |
| Change cost | 2 weeks integration, no data migration | 4 weeks including re-baselining under strict scoring |
| Price | $X | $Y |

Note what happened. Column one says tie. Column two says the tie is not really a tie, because one candidate's errors are visible within an hour and the other's are visible after a customer complains. Column three says the more expensive option is cheaper to leave.

If price is $10/month apart, column two wins on any plausible valuation of a week of undetected errors.

**A note on how to fill column one when two candidates are close.** Do not run them sequentially on different days with different questions. A 2026 source-attribution study found that fact-check accuracy fell by roughly 42 percentage points on average across two frontier models as tool calls rose from 2 to 150, while link validity and relevance stayed above 92% — deeper checking made attribution worse. The parallel lesson for evaluation: run both systems on the same questions, at the same time, with the same settings, and compare outputs directly. Their own recommendation in the metrics study is to evaluate at least two systems and compare their outputs on the same questions.

## And a check that belongs under the table

**Swap the order.** If the two candidates are being compared by a judge rather than by your own rubric, the comparison is order-dependent. The 2023 NeurIPS MT-Bench paper found GPT-4 judges agreeing with human preference on more than 80% of comparisons — comparable to human-human agreement — while naming position bias, verbosity bias, and self-enhancement bias, plus "limited reasoning ability." The companion paper showed that under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries.

Three defenses: swap order, control length, change judge family. If the winner flips under any of them, column one is a tie and you should be reading column two.

## What this cannot settle

The three-column structure is my redesign. No published work validates it, and a different practitioner might weight the columns differently — though I would argue failure visibility is under-weighted nearly everywhere.

The numbers are setup-specific and dated. The judge figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

The 15% tie threshold is judgment, not measurement. And three columns cannot capture everything a decision needs — regulatory fit, for instance, which is not a matter of degree but a gate. Add it as a fourth column when it applies.

## Where to start this week

1. Build your 30-question set and freeze it.
2. Run two candidates on it, same day, same settings.
3. Fill in failure visibility honestly, including "no verification available."
4. Estimate change cost in days for both.
5. Swap the order if a judge made the comparison.

## Sources

- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: comparison dimensions; repository-level integration surface; scores guide not determine.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation ≠ validity; two-system comparison.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; ~42-point fact-check drop from 2 to 150 tool calls.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; judge biases.
- *ToolTweak* (2025). arXiv:2510.02554. https://arxiv.org/html/2510.02554v1
  - Supports: name/description attack; 81.6%–34.0% vs ~20% baseline; distribution shift.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: strict vs relaxed grading roughly doubling scores; re-baselining cost.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases.
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; field testing; leaderboard overfitting.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: fabricated-reference rates as evidence for verification design.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Fill in the failure-visibility column for the tool you use most — can you actually complete that cell?
