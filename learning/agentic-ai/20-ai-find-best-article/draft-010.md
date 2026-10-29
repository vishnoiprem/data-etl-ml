---
title: "The Model Is Not the Product: What AI Tool Selection Is Actually About"
subtitle: "A historical shift from ranking candidates to designing the selection process — and what each era got wrong."
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
word_count: 1530
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 87
hard_fail: false
distinctness_angle: "Historical arc — three eras of AI evaluation (static leaderboard, LLM-as-judge, trajectory/human-in-the-loop) with what each era over-trusted"
sources_count: 10
author_experience_placeholders: 1
---

For about three years, "which model is best" meant "which model is at the top of the leaderboard."

That era ended. Not because the leaderboards got worse — because we got better at seeing what they were measuring, and what they were not.

Here is the arc, because each era's mistake is still present in most teams' current practice.

## Era one: the leaderboard

The idea was sound. Benchmarks made comparison possible, reproducible, and free of vibes. The 2023 NeurIPS MT-Bench paper is a good example of the form working well: it built a multi-turn benchmark with 3K expert votes and 30K conversations with human preferences, and showed that MT-Bench and conventional benchmarks were complementary rather than redundant.

What the era got wrong was scope. A leaderboard measures a task. A deployment is a context.

A 2025 evaluation-ecosystem paper makes the structural critique: static datasets and constrained tasks poorly reflect deployment conditions, obscuring emergent behaviors and context-specific failures. Overreliance on leaderboards encourages overfitting and benchmark saturation. Contamination and data leakage can inflate results. Weak internal and external validity and narrow English-language focus create what the paper calls a "fallacy of objectivity."

A 2025 survey of software-engineering agents is more concrete. Early suites like HumanEval and MBPP measured small function-generation tasks; newer ones use real GitHub issues, pull requests, and executable test environments. And the same survey notes that a cited analysis found many issues counted as solved on SWE-bench were actually resolved incorrectly — passing benchmark tests is not the same as production-quality repair.

The failure mode of era one: **the number travels further than the context that produced it.** A model name and a score get quoted in a slide; the evaluation conditions stay behind.

## Era two: the judge

When static benchmarks ran out of headroom, the field started using models to grade models. This was a genuine methodological advance — MT-Bench itself showed a strong judge (GPT-4) agreeing with human preference on more than 80% of comparisons, which is comparable to agreement between humans.

What era two got wrong was the assumption that agreement implied validity.

The 2023 MT-Bench paper named the biases in its own method: position bias, verbosity bias, and self-enhancement bias, where a judge favors outputs written by itself or its own model family, plus the limitation "limited reasoning ability." A companion paper, "Large Language Models are not Fair Evaluators," showed how much the order of presentation matters — under one setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. Its calibration framework included a human-in-the-loop component, using "balanced position diversity entropy" to detect when examples were hard enough to warrant human judgment.

A 2026 agent-evaluation paper is blunter about the limits. LLM judges are faster, cheaper, and repeatable, but unreliable as a sole evaluation authority: they may miss domain policies, required tool sequences, and trajectory-level failures.

And a 2026 study of RAG metrics made the statistical version of the point. Two human evaluators correlated at 0.85 with each other — the practical ceiling. RAGChecker's recall-oriented metrics correlated best, with claim recall near 0.7. But high correlation does not establish validity, because difficulty and other confounders produce strong correlations on their own. Their methodological fix is elegant: evaluate at least two systems and compare outputs on the same questions, so shared difficulty cancels.

The failure mode of era two: **we stopped distinguishing "the judge agrees" from "the judge measures the right thing."** Both are true to be necessary. Only one is sufficient.

## Era three: trajectories and humans

The current era evaluates what the system *does*, not what the output says, and it puts humans back where humans are actually needed.

The 2026 agent-evaluation paper is the clearest statement. Static benchmarks do not adequately test multi-turn tool use, policy adherence, recovery, or procedural consistency, and a model can pass a fixed benchmark and then fail operationally through "missing tool calls, hallucinated tool use, policy drift, unsafe reframing, manipulation paths, or over-refusal." Interactive trajectory benchmarks are closer to real behavior but do not fully specify how experts curate adversarial risks or connect evidence to repeatable scoring. Human review remains "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions" — while being costly, slow, and hard to reproduce at every step. The proposed resolution is to move expert knowledge upstream into reusable evaluation artifacts.

Trace analysis is the mechanism. Procedural failures "can look plausible in the final response" — an agent claiming a tool it never invoked, skipping a mandatory compliance call, calling tools in the wrong order — which is why the trace, not the answer, is the object of inspection.

The 2026 long-context agentic benchmark shows what rigor looks like at the leading edge. It reports strict pass@1 alongside a relaxed variant tolerating one failed criterion, notes that relaxing roughly doubles leader scores, and warns that a deployment tolerating one violated control per workflow "has effectively abandoned strictness." Its best configuration scored 36.2% strict pass@1 — failing nearly two of every three tasks. It also found that raising reasoning effort helped some configurations by 2.0 to 3.0 points, left one unchanged, and hurt one by 2.7 points, while token spend ranged from roughly 13K to 60K per trial with no clean relationship to score. Its recommendation: enforce hard controls outside the model, in deterministic tool-call guards, rather than relying on in-context adherence.

The failure mode of era three: **cost.** Human review does not scale, so teams quietly fall back to era two's judges while believing they have moved on.

## Where we are, and what to do

The interesting thing is that all three eras are still running in the same organization. The team reads leaderboards (era one), builds an LLM-judge eval (era two), and asks one engineer to spot-check outputs (era three, badly).

The synthesis is not to pick an era. It is to assign each method to the job it is actually good at.

**Static benchmarks** — good for: comparing general capability across candidates. Bad for: deciding what to ship. Use them to narrow a list of ten to three.

**LLM judges** — good for: cheap repeatable screening of large volumes. Bad for: final calls, close comparisons, regulated decisions. Their three named biases are fixable, and you should fix them: swap the order, control length, use a judge from a different family.

**Human review** — good for: domain context, subtle policy interpretation, risk criteria, rubrics, escalation. Bad for: every single run. Encode the expert's rules once, in a reusable rubric, and let the human review the cases the rubric flags.

**Trace analysis** — good for: procedural correctness. Bad for: nothing. This is the cheapest and most-skipped method in the entire list.

## The part that does not fit any era

A 2026 study on source attribution in AI research reports found something that belongs to all three eras at once. Across 14 models and 130 research queries, link validity exceeded 94% and topical relevance exceeded 80% — while factual accuracy ranged from 24.4% to 76.8%. Then the striking result: across GPT-5.4 and Claude Opus 4.6, fact-check accuracy fell by roughly 42 percentage points on average as tool calls rose from 2 to 150, even as link validity and relevance stayed above 92% throughout.

More searching produced more accessible, on-topic sources and worse attribution. The cheap checks stayed green. The expensive one degraded.

A parallel result appeared in the agentic benchmark: more reasoning tokens did not buy compliance, and in one case actively hurt.

**The through-line of all three eras:** more effort is not reliably better, and more confident-looking output is not reliably more correct. The tools that evaluate better are the ones that check the thing that is actually hard to check.

## The method that survives all three eras

A 2026 benchmark called CiteAudit makes the point in a different domain. Across 9,442 citations, 2,967 were fabricated — and separately, some references existed but their title or author metadata did not match, indicating the paper was never read. A 2026 study on source attribution makes the parallel case: check the claim against the retrieved content, not whether the link resolves.

Selection follows the same shape. Do not pick the artifact that scored highest. Pick the artifact, and the measurement, that survive the checks you cannot skip.

[AUTHOR EXPERIENCE: Replace with your real account — the era your team is stuck in, and a specific decision that went wrong because of it.]

## What this cannot settle

The three-era framing is my construction, not a published taxonomy. The boundaries between eras are blurred in practice, and the sources here span 2023 to 2026, which makes the "progression" a narrative I imposed as much as a trend the field took.

The numbers are setup-specific. The judge agreement figures are from 2023-era models; the 2026 work updates the picture without replacing them. Several of the most useful sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones, which biases the arc toward "we knew this earlier than the preprints suggest."

The history also does not tell you what to do on Monday. For that, use the assignments above, and pick the method that matches the decision you are actually making.

## Where to start this week

1. Narrow your candidate list with a public benchmark, then stop using it.
2. Fix your judge: swap order, control length, second judge family.
3. Build one reusable rubric with a domain expert. Use it more than once.
4. Start storing traces. This is a one-afternoon change.
5. Pick one tool and one paper and run the claim-level check on both.

## Sources

- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: static-task limits; leaderboard overfitting and saturation; contamination inflating results; "fallacy of objectivity"; three-activity evaluation model.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; 3K expert votes / 30K conversations; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result; position-diversity-entropy human trigger.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: era-three framing; procedural failures look plausible in the final response; human review essential for specific decisions; moving expertise upstream.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation ≠ validity; two-system comparison.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: strict vs relaxed grading; 36.2% strict pass@1; reasoning-effort variance; 13K–60K tokens; hard controls outside the model.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; ~42-point fact-check drop from 2 to 150 tool calls.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; metadata mismatch reveals unread papers.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: HumanEval/MBPP → repository-level suites; SWE-bench reliability caveat; contamination via DyCodeEval; scores guide not determine.
- *A New Evaluation Ecosystem* / *A Comprehensive Survey* — see entries above.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Which era is your team's evaluation actually in — and do you know when it moved?
