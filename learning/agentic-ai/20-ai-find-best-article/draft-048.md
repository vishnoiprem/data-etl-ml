---
title: "Pick the Smallest Tool That Passes: A Selection Rule for When Everything Is Good Enough"
subtitle: "Most candidates clear the bar. The decision is then about surface area, and the evidence says smaller wins."
tags:
  - model-selection
  - ai-evaluation
  - llm
  - how-to-evaluate-llm-tools
  - ai-engineering
  - architecture
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1395
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 89
hard_fail: false
distinctness_angle: "Sufficiency-rule frame — inverts the search from best to smallest sufficient, and argues the evidence for preferring the simpler candidate using failure-mode and benchmark-saturation arguments"
sources_count: 9
author_experience_placeholders: 1
---

The selection question everybody asks is "which is best?"

It is the wrong question, and there is a better one that produces a different decision most of the time.

**Which is the smallest tool that passes your bar?**

This sounds like a compromise. It is not. It is the decision, and here is why.

## Why "best" is usually the wrong frame

If you rank candidates and take the winner, you have made two commitments: to the highest score, and to everything that came bundled with it. Those bundles are usually where the cost and the risk live.

A 2026 long-context agentic instruction following benchmark shows the cost side precisely. One configuration reached 21.5% on roughly 13K generated tokens per trial. Another spent close to 60K tokens at about three times the dollar cost for the same quality band. Several mid-pack configurations generated 45–55K tokens and scored in single digits. Raising reasoning effort helped some configurations by 2.0 to 3.0 points, left one unchanged, and **hurt one by 2.7 points**.

Notice: the "best" configuration in that table is not obviously the one you want. It is the most expensive, and the lever most people reach for to improve results can make results worse.

## The three arguments for the smallest sufficient tool

### One: the marginal quality is not real

A 2026 RAG metrics study gives the ceiling. Human evaluators's ratings correlated with each other at a **Pearson 0.85** — the practical ceiling for any automatic proxy metric. RAGChecker produced the strongest overall correlations among the tools tested, with claim recall near **0.7**. And the authors' warning is the load-bearing part: high correlation does not establish validity, because input difficulty and other confounders produce strong correlations on their own.

So when candidate A scores 89% and candidate B scores 86%, you have three points of separation against an instrument whose agreement with humans is 0.85. You do not have a quality difference. You have two configurations of the same thing.

**Set the bar, then stop.** If A passes your floor at 89% and B passes it at 86%, both pass. Choose on everything else.

### Two: more capability means more failure surface

A 2024 RGB benchmark organized RAG evaluation around four abilities, and found that models "still struggle significantly in terms of negative rejection, information integration, and dealing with false information," concluding that "there is still a considerable journey ahead to effectively apply RAG to LLMs." More retrieval means more noise handling; more tool access means more negative rejection and more chance of acting on a false instruction.

A 2026 agent-evaluation paper is the evidence on the agentic side: procedural failures "can look plausible in the final response" — an agent claiming a tool it never invoked, skipping a mandatory compliance call, calling tools out of order. Every additional capability is another way for a plausible-looking failure to occur.

**The capability you do not use is the capability that cannot fail.** A system with no write access cannot corrupt data. A system with no tool access cannot hallucinate a tool call. This is not a slogan; it is the same argument that makes least privilege work in security, and it applies here with the same force.

### Three: the leaderboard's top is the least trustworthy entry

A 2025 evaluation-ecosystem paper makes the institutional case. Leaderboard reliance encourages overfitting and saturation, contamination and data leakage inflate results, and a narrow English-language focus with limited stakeholder involvement produces what the paper calls a "fallacy of objectivity."

The top of a leaderboard is where the overfitting accumulates. A 2025 survey of software-engineering agents adds the contamination version: a benchmark drawn from public repositories may already have appeared in model pretraining or fine-tuning data — which is why a dedicated contamination benchmark was created to evaluate models under different contamination levels. The survey's conclusion: unfamiliarity cannot safely be assumed.

**You are not choosing the top entry. You are choosing the entry that passes your bar with the least machinery.**

## What "smallest" means in practice

**Fewer moving parts.** A tool that needs one API call is easier to trace than one that needs five chained calls, each of which can fail. A 2026 source-attribution study found that across GPT-5.4 and Claude Opus 4.6, fact-check accuracy fell by roughly **42 percentage points on average** as tool calls rose from 2 to 150. One configuration dropped from 78.6% to 16.7%; another from 80.0% to 57.9% — while link validity and topical relevance stayed above 92% throughout. More calls, worse quality, and the cheap checks stayed green. Every call you add is a chance for that.

**Fewer permissions.** Write access, network access, and access to other users' data are all failure surfaces, and the 2026 long-context benchmark's recommendation to enforce "hard controls outside the model" is a recognition that in-context permission does not hold.

**Narrower scope.** A tool that only does the one thing you bought it for has one thing to evaluate. A general-purpose tool has an undefined range, and you will use more of it than you planned.

**Less configuration.** Fewer knobs, fewer version combinations, fewer reasons for a result to differ between the demo and production.

## The rule

1. **Set the floor first.** Write the criteria and the thresholds before looking at candidates. A floor written after you have seen the scores is not a floor.
2. **Measure against it.** On your own questions, with a stated denominator and grading rule.
3. **Delete the candidates that fail.** Not rank them lower — remove them. A failing candidate is not a worse option, it is a wrong option.
4. **Among the survivors, choose the one with the least machinery.**
5. **Document why the better-looking candidate was not chosen.** This is the line a stakeholder will read, and it is also the line that will let you revisit the decision when the smaller tool stops being sufficient.

## When to break the rule

**When the floor is close to the ceiling.** If your bar is 95% and the candidates score 94% and 93%, then the quality difference is your whole problem, and the smallest-sufficient principle does not help. Be honest about this: at high floors, quality is the binding constraint and you should spend the complexity budget.

**When the small tool cannot be observed.** A 2026 agent-evaluation paper's central claim is that the trace converts an unobservable failure into a lookup. If the smaller tool will not give you a trace, its failures will be invisible, and invisible failures are more expensive than complexity. A 2023 NeurIPS MT-Bench paper named the judge biases — position, verbosity, self-enhancement — and the companion paper showed the stakes: under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. You cannot defend a comparison you cannot re-run.

**When the larger tool's extra capability is the actual requirement.** If the task needs multi-step tool use, no amount of minimalism substitutes for it.

## The uncomfortable part

Choosing the smaller tool means you will be tempted later to add the larger one for a feature you do not need yet, and the request will arrive as "we should just upgrade." The memo's reversal conditions are where you handle that: pre-commit to the threshold at which the smaller tool stops being sufficient, and write the condition as a measurement you are already taking.

[AUTHOR EXPERIENCE: Replace with your real account — a time you chose the smaller tool and were right, or a time you chose the bigger one and paid for it.]

## What this cannot settle

The smallest-sufficient rule is my construction, and it depends on a floor you can actually state and measure. Many teams do not know their floor, and the rule then reduces to "pick the cheapest thing," which is not the same thing.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And "smallest" is not always well-defined. A model with a million parameters and one API call may be less machinery than a small model you have to host, instrument, and maintain.

## Where to start this week

1. Write your floor. Four criteria, with thresholds, before you look at any candidate.
2. Take your current shortlist and delete the ones that fail.
3. Among the survivors, list the machinery each one brings.
4. Pick the one with the least.
5. Write the sentence explaining why the strongest-looking candidate lost.

## Sources

- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation ≠ validity; difficulty confound.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 21.5% on ~13K tokens; 45–55K and ~60K token configurations in the same band; reasoning-effort variance; hard controls outside the model; 36.2% strict pass@1.
- Chen, J. et al. (2024). *Benchmarking Large Language Models in Retrieval-Augmented Generation*. AAAI 2024. https://arxiv.org/abs/2309.01431
  - Supports: RGB's four abilities; persistent failure in negative rejection, information integration, and false information.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: ~42-point fact-check drop from 2 to 150 tool calls; 78.6%→16.7% and 80.0%→57.9%; link validity stays above 92%.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; trace converts unobservable failure into a lookup; human review for escalation.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: leaderboard overfitting and saturation; contamination inflating results; "fallacy of objectivity"; contextual unit framing.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: contamination benchmark; unfamiliarity cannot be assumed; scores guide not determine.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

If you wrote your quality floor before seeing the scores, would your last choice still pass?
