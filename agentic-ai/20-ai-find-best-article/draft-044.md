---
title: "What Breaks When You Add the Second Candidate: The Hidden Cost of Comparison"
subtitle: "A/B testing an AI system is not free, and the bill arrives as a maintenance cost you did not plan for."
tags:
  - ai-engineering
  - ai-evaluation
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - experiments
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1400
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 86
hard_fail: false
distinctness_angle: "Second-candidate frame — takes the cost of maintaining a comparison itself as the subject, and argues the two-system requirement is a permanent organizational commitment"
sources_count: 9
author_experience_placeholders: 1
---

The literature is clear on the method: evaluate at least two systems and compare their outputs on the same questions, so shared difficulty cancels and the difference between the systems is what remains.

What the literature does not say is what it costs to keep two systems alive.

This is a real cost, it is recurring, and it is the reason many teams end up with one candidate and no evidence.

## What the second candidate actually costs

**A maintained interface.** Two candidates means two API surfaces, two parameter sets, two error shapes, two sets of quirks. A 2025 survey of software-engineering agents documents that in practice the comparison dimensions are not only quality but language, context length, test strength, contamination exposure, latency, and cost — each of which is a place where two candidates behave differently and need different handling.

**A maintenance burden that persists after the decision.** The moment you have two candidates, every prompt change, every retrieval change, and every model upgrade has to be run against both, or your comparison history becomes a set of incomparable snapshots. A 2026 source-attribution study notes that web-based citations are temporally unstable — pages get paywalled, moved, and removed — and the same decay applies to any external dependency in either candidate.

**A share of the team's attention.** Every time someone asks "why did we pick this one?", the answer requires the second candidate. Keeping it runnable is what makes the answer available.

**A temptation you will lose to.** The second candidate is always slightly worse, slightly more expensive, or slightly more annoying. There will be a week when shipping would be easier with one candidate, and the correct answer — keep both, because the comparison is the evidence — will look like slow progress.

## Why the cost is worth it

A 2026 RAG metrics study makes the strongest case for keeping a permanent second system, and it is not about the initial decision.

**The comparison method is the only way to validate your metric.** The study's own finding is that human evaluators' ratings correlated with each other at a **Pearson correlation of 0.85** — the practical ceiling for any automatic proxy metric. RAGChecker produced the strongest overall correlations among the tools tested, with claim recall near **0.7**. But the authors' warning is the load-bearing part: high correlation does not establish validity, because input difficulty and other confounders can produce strong correlations on their own. RAGChecker claim recall near 0.7 might be tracking question difficulty or answer extractability rather than retrieval quality.

**You can only check that claim by running two systems on the same questions and seeing whether the metric separates them.** One system cannot test a metric. A metric always looks fine against a single system, because a metric that always said "fine" would also be perfectly correlated with a single system's ratings.

**The second system is your regression detector.** When you upgrade a model or change a prompt, you need to know whether the change helped or hurt. One system gives you a number with no reference. Two give you a delta. A 2026 benchmark for long-context agentic instruction following reported strict pass@1 alongside a relaxed variant tolerating one violated control and found that relaxing roughly doubles leader scores — best configuration **36.2% strict pass@1**, still failing nearly two of every three tasks. You cannot detect a shift in your grading convention with a single number either.

**The second system is your hedge against vendor drift.** A 2026 source-attribution study found that across GPT-5.4 and Claude Opus 4.6, fact-check accuracy fell by roughly **42 percentage points on average** as tool calls rose from 2 to 150, with one configuration dropping from 78.6% to 16.7% and another from 80.0% to 57.9% — while link validity and topical relevance stayed above 92% throughout. The lesson generalizes: capability changes under you, and the cheap signals stay green. A second, pinned, comparable system is how you see the change.

**It is the defense for every close call.** The 2023 NeurIPS MT-Bench paper found GPT-4 as a judge agreeing with human preference on more than 80% of comparisons — comparable to human-human agreement — while naming position bias, verbosity bias, and self-enhancement bias, plus "limited reasoning ability." The companion paper showed the stakes: under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. When the margin is inside that noise, the only real defense is that you have two systems and a shared question set, and you re-ran in both orders.

## The cheaper way to hold a second candidate

You do not need two production systems. You need two things that can be run on the same questions.

**Pin a reference candidate at a known version.** Not a second integration — a pinned snapshot, documented, with a note on how to run it. Its cost is storage, not engineering.

**Share the question set, not the code.** Write the evaluation harness so that a candidate is a configuration, not a fork. If adding a candidate means writing new code, you will not add the second one.

**Automate the comparison.** A script that runs both candidates over the fixed set and writes both outputs to a dated file. The 2026 metrics study's method is simple enough to automate, and an automated comparison is the only kind that survives a busy quarter.

**Version everything about the run.** Prompt hash, model identifier, retrieval snapshot, tool versions. A 2026 agent-evaluation paper is blunt that procedural failures "can look plausible in the final response" — an agent claiming a tool it never invoked, skipping a mandatory compliance call, calling tools out of order. Without pinned versions, a comparison from last quarter cannot be re-run and a delta cannot be attributed.

## The failure mode to watch

There is a specific way this goes wrong, and it is worse than not having a second candidate at all.

**The second candidate becomes the fallback, and the fallback becomes the thing you measure.** You run the comparison once, the second system is clearly behind, and then every subsequent run only measures the first. Now you have a system and a stale artifact, and the artifact looks like evidence because it is formatted like evidence.

The fix is procedural: the comparison must run on a schedule, not on demand. Weekly for a system you are actively changing. Monthly for a settled one. And the second candidate's outputs must be archived with dates so the history is inspectable.

A 2026 source-attribution study gives the sharpest illustration of the alternative. Everything visible in that research was healthy — link validity above **94%**, topical relevance above **80%** — while factual accuracy ranged from **24.4% to 76.8%**. A static artifact with no re-run looks exactly like that: structurally intact, quietly wrong.

## The decision to actually make

If your team has never run a two-system comparison, the question is not "should we add a second candidate." It is "what is the smallest comparison we could run this week, and can we run it again next week?"

The smallest version is: one reference candidate at a pinned version, one current candidate, twenty questions from your own closed work, one script, one dated output file. That is a day of work and it produces the only kind of evidence that gets better over time.

[AUTHOR EXPERIENCE: Replace with your real account — a comparison you set up and then let lapse, or one that saved a decision.]

## What this cannot settle

The two-system requirement comes from one recommendation in the 2026 metrics study rather than a validated standard, and it assumes you can hold a reference candidate at a stable version — which not every organization can do.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And the maintenance cost is real even in the cheap form. A pinned reference candidate still needs someone to keep the version available, and a comparison script still needs someone to fix it when the harness changes.

## Where to start this week

1. Write 20 questions from your own closed work.
2. Pick a reference candidate and pin its version.
3. Write the script that runs both and writes dated outputs.
4. Schedule the comparison. Recurring, not optional.
5. Run it once, and note what it cost you.

## Sources

- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: two-system comparison as the recommended method; 0.85 human-human correlation; RAGChecker recall near 0.7; difficulty confound; correlation ≠ validity.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; strict vs relaxed grading roughly doubling scores.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: ~42-point fact-check drop from 2 to 150 tool calls; 78.6%→16.7% and 80.0%→57.9%; temporal instability of web citations; 94% / 80% vs 24.4–76.8%.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: comparison dimensions beyond quality; scores guide not determine.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; trace-based detection; reusable evaluation artifacts.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; leaderboard overfitting and saturation.
- *Evaluating LLM Metrics Through Real-World Capabilities* (2025). arXiv:2505.08253. https://arxiv.org/html/2505.08253v1
  - Supports: benchmarks prioritize abstract correctness over user-relevant qualities.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

How many candidate systems could you actually run on the same 20 questions this week?
