---
title: "Ranking Without a Reference: How to Choose When Every Score Is a Proxy"
subtitle: "A relative-comparison method for when no absolute quality bar exists, built on the one technique that survives confounds."
tags:
  - ai-evaluation
  - benchmarks
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - data-engineering
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1425
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 90
hard_fail: false
distinctness_angle: "No-ground-truth frame — solves the case where absolute quality is unmeasurable, centering the two-system differential comparison and forced-choice pairwise ranking as the core method"
sources_count: 9
author_experience_placeholders: 1
---

Sometimes there is no right answer to compare against.

No pass mark, no human baseline, no ground truth, no rubric that settles it. Two systems sit on your desk, both plausible, and every number you can compute is a proxy for something you cannot directly observe.

This is the normal case, not the edge case. The method that survives it is differential, not absolute.

## Rank by difference, not by level

Run every candidate on the same questions. Compare outputs pairwise. Read the pairs.

That is the entire method, and it is not a consolation prize. It is better than an absolute score, because it removes the thing that makes absolute scores unreliable: input difficulty.

A 2026 study of RAG evaluation metrics makes this precise. Human evaluators' ratings correlated with each other at a **Pearson correlation of 0.85** — the practical ceiling for any automatic proxy metric. RAGChecker produced the strongest overall correlations among the tools tested, with claim recall near **0.7**. But the authors' warning is the load-bearing part: high correlation does not establish validity, because input difficulty and other confounders can produce strong correlations on their own. RAGChecker claim recall near 0.7 might be tracking question difficulty or answer extractability rather than retrieval quality.

The fix is structural. Evaluate at least two systems and compare their outputs on the same questions. Shared difficulty cancels. What is left is the difference between the systems, which is the only thing you were trying to learn.

## Why the single score kept misleading

Consider what a leaderboard number actually is: the average of many items of wildly varying difficulty, on inputs you did not choose, judged by a procedure you did not design.

Three specific failure sources, each documented.

**Grading leniency.** A 2026 benchmark for long-context agentic instruction following reported strict pass@1 alongside a relaxed variant that tolerates one violated control, and found that relaxing roughly doubles leader scores. Its best configuration scored **36.2% strict pass@1** — still failing nearly two of every three tasks. The authors warned that a deployment tolerating one violated control per workflow "has effectively abandoned strictness." The same systems, the same work, two numbers, and the gap between them exceeded most product-to-product differences in the field.

**Judge bias.** The 2023 NeurIPS MT-Bench paper names position bias, verbosity bias, and self-enhancement bias in its own method, alongside the finding that GPT-4 as a judge agreed with human preference on more than 80% of comparisons, comparable to agreement between humans. The companion paper, "Large Language Models are not Fair Evaluators," showed the magnitude: under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries.

**Coverage gaps.** A 2025 paper on real-world capabilities identified six practical capabilities and found that "Reviewing Work and Data Structuring are not captured at all" by the metrics it evaluated. Benchmarks "often prioritize abstract notions of correctness over qualities that matter to users."

Differential comparison does not fix these. It makes them less likely to flip your decision, because a bias that applies to both candidates shifts them together and largely cancels.

## The pairwise protocol

**One question, two outputs, blind labels.** Randomize which system produced which output. Not "usually A first" — actually randomize, and record the order.

**Read both before either.** The 2023 NeurIPS paper's position bias is not subtle; it is large enough to have been named as a limitation in the same paper that established the method. If you read A's output first, you know what you are looking for in B.

**Score the pair, not the output.** Which is better, or is it a tie. Forcing a tie option is what keeps a near-miss from becoming a fake preference.

**Do it for every pair, not every item.** With three candidates you have three pairs. With four, six. The pairwise count grows faster than the candidate count, so keep the shortlist at three.

**Compute a win rate, and treat close results as ties.** If candidate A beats B on 14 of 20 and C beats B on 15 of 20, A and C are not distinguishable, and you should be choosing on cost, latency, or portability instead.

## When pairwise is not enough

Differential comparison has a failure mode: it tells you which is better and nothing about how much better, and it is weak when the candidates are similar.

Add a third measurement for magnitude. **Cost per successful answered question**, computed on your own task distribution. The 2026 long-context benchmark showed the decoupling clearly: one configuration reached 21.5% on roughly 13K generated tokens per trial, another spent close to 60K tokens for the same band at about three times the dollar cost, and several mid-pack configurations spent 45–55K tokens scoring in single digits. Raising reasoning effort helped some configurations by 2.0 to 3.0 points, left one unchanged, and hurt one by **2.7 points**. Two candidates in the same quality band can differ by 3× in cost, and no quality score will show that.

And add a third for the cases where reading the pair is not enough. A 2026 agent-evaluation paper separates deterministic detections from subjective judgments: a phantom tool call or an omitted compliance action is checkable against the trace and objective once the trace is available. It also describes human review as "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions." When two outputs look equivalent and the difference is in a policy nuance, a person decides.

## Forcing a choice when everything ties

If the win rates are inside the noise floor, you have four options, and picking on quality is no longer available.

**Pick the cheaper one.** Quality is tied; cost is not.

**Pick the more traceable one.** A 2026 agent-evaluation paper's central claim is that procedural failures can look plausible in the final response, and the trace is what converts an unobservable failure into a lookup. When quality is indistinguishable, the candidate you can debug is the better bet.

**Pick the more reversible one.** A 2026 source-attribution study notes that web-based citations are temporally unstable — pages get paywalled, moved, and removed. The same decay applies to models, pricing, and vendor APIs.

**Pick the one with the better second-order properties.** Latency at your traffic. Failure modes you can detect. A 2025 survey of software-engineering agents makes the operational version: candidates should be compared on your repository, language, context length, test strength, contamination exposure, latency, and cost. When quality is tied, that list is the decision.

## One trap in pairwise

Pairwise comparison drifts toward a candidate that is *different* rather than one that is *better*, if the output style is what you are noticing. This is verbosity bias in disguise, and it is named in the same 2023 NeurIPS paper that names the others. It is also why the same paper's human-agreement figure — above 80%, comparable to human-human agreement — is a ceiling rather than a guarantee. Human reviewers have the bias too.

Counter it by scoring against a written criterion, not against your impression of the better answer. The metric definition does double duty here: a stated criterion for "what good looks like on this question" turns the pair into a checkable comparison.

## The minimum viable protocol

1. Three candidates, same 20 questions, same day.
2. Blind pairwise comparisons, order randomized, tie allowed.
3. Win-rate matrix, not a single number.
4. Treat differences under your instrument's noise floor as ties.
5. Break ties on cost, then traceability, then reversibility.
6. Write down which pair decided it and why — that sentence is the memo.

[AUTHOR EXPERIENCE: Replace with your real account — a comparison decided by a pairwise read rather than a score, and whether it held up.]

## What this cannot settle

The pairwise protocol is my construction, built on one recommendation from the 2026 metrics study rather than a validated standard. It also assumes a common question set, which breaks when candidates solve different problems.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And pairwise comparison only ever tells you about the candidates you put in front of each other. It is a ranking, not a search, and a candidate you never tested cannot win it.

## Where to start this week

1. Pick three candidates. Not five.
2. Pick 20 questions from your own closed work.
3. Run all three on all 20, same day.
4. Build the win-rate matrix.
5. Break the tie on cost, traceability, or reversibility — and write down which one broke it.

## Sources

- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; difficulty confound; correlation ≠ validity; two-system comparison as the recommended remedy.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; strict vs relaxed grading roughly doubling scores; 13K–60K tokens; reasoning-effort variance.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *Evaluating LLM Metrics Through Real-World Capabilities* (2025). arXiv:2505.08253. https://arxiv.org/html/2505.08253v1
  - Supports: "Reviewing Work" and "Data Structuring" not captured; benchmarks prioritize abstract correctness.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: deterministic vs subjective detection; trace as evidence; human review essential for domain context, policy interpretation, and escalation.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: comparison dimensions; scores guide not determine.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: temporal instability of web citations; 94% / 80% vs 24.4–76.8%.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; leaderboard overfitting and saturation.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

When your last comparison came out close, what did you use to break the tie?
