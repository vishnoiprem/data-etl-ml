---
title: "A Decision Tree for Picking AI Tools, Papers, and Prompts"
subtitle: "Start with one question and follow the branches — every branch ends in a concrete next action."
tags:
  - ai-evaluation
  - decision-tree
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - ai-engineering
  - technical-decisions
platform: linkedin
medium_publication: signal-scribe
target_length: 1250-1500
word_count: 1430
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 87
hard_fail: false
distinctness_angle: "Decision tree — the whole article is a branching flow with explicit terminal actions at each leaf, no linear step list"
sources_count: 9
author_experience_placeholders: 1
---

Selection advice usually arrives as a list, and lists are hard to apply at 4pm on a Thursday with four candidates on your screen.

A tree is easier. One question at the top, branches that narrow, and every leaf ends in an action you can take.

Here is one.

## Start: what are you choosing?

This splits everything.

### Branch A: you are choosing a paper

**A1: Do you already know why you want it?** If no — stop. Read three abstracts first, then come back. A 2026 source-attribution study found that across 14 models, link validity exceeded 94% and topical relevance exceeded 80%, but factual accuracy at the claim level ranged from 24.4% to 76.8%. The cheap checks always pass. Knowing what claim you need is what lets you run the expensive one.

**A2: Does the paper's benchmark resemble your problem?** If no — the leaf is *read for method, not for result*. The method might still be what you need; the number almost certainly is not.

**A3: Does it report strict or relaxed grading?** If you cannot tell, look at the failure definition. A 2026 long-context agentic benchmark noted that relaxing a criterion to tolerate one violated control roughly doubles leader scores, and warned that a deployment tolerating one violation per workflow "has effectively abandoned strictness." A paper that will not tell you its denominator is not giving you a result.

**A4: Can you verify the references?** Three checks: does it exist, do the title and authors match, does the source support the specific sentence. A 2026 benchmark called CiteAudit found 2,967 fabricated citations out of 9,442 — and separately found references that exist but whose metadata does not match, meaning the cited paper was never read.

**A5 leaf: read it, or don't.** You now know which.

### Branch B: you are choosing a model or tool to run

**B1: Is the output going to be checked by a human, or acted on automatically?**

If **checked by a human** → go to B2.
If **acted on automatically** → go to B3.

The reason for the split: a 2026 paper on agent evaluation found that procedural failures "can look plausible in the final response." An agent can claim a tool it never invoked, skip a compliance call, and produce text a reviewer accepts. When a human is in the loop, you can catch it by reading. When there is no human in the loop, you need the trace checked automatically.

**B2: the human-in-the-loop branch.** A 2026 agent-evaluation paper is explicit about the division of labor. LLM judges are faster, cheaper, and repeatable, but unreliable as a sole evaluation authority — they may miss domain policies, required tool sequences, and trajectory-level failures. Human review remains "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions," and is costly, slow, and hard to reproduce at every step.

So: is the reviewer a domain expert, or can you use a deterministic check?

- **Domain expert** → the leaf is *encode their judgment once, in a rubric, and review a sample against the score.* The same work recommends moving expert knowledge upstream into reusable evaluation artifacts rather than reviewing every trajectory. Log the disagreement rate.
- **Deterministic check** → the leaf is *use the check, and skip the judge entirely for that class of failure.* A 2026 long-context agentic benchmark recommends enforcing "hard controls outside the model" — deterministic tool-call guards — rather than relying on in-context adherence.
- **Neither** → the leaf is *you do not have a defensible selection process yet.* Build one before you buy.

**B3: the automated branch.** No human reads the output. Then two things must be true: the process is verifiable from the trace, and the failure you care about is catchable by a rule.

Go to B4.

**B4: what breaks first?** This is the diagnostic question that decides everything downstream. Find the answer by testing, not by reading documentation.

Test for these four, in this order:

**Does it break silently?** A 2026 source-attribution study measured this precisely: link validity above 94%, relevance above 80%, claim-level accuracy 24.4%–76.8%. A failure with no trace is invisible until someone downstream notices. → Leaf: *build the trace, then the rule that reads it.*

**Does it break in the middle of the context?** The 2023 TACL paper "Lost in the Middle" found models perform best at the beginning or end of the context and "significantly degrades when models must access relevant information in the middle," including in explicitly long-context models. → Leaf: *move the evidence and re-run. If the answer changes, pin the layout before you ship.*

**Does it break at scale?** A 2025 retrieval-based tool-selection study found that showing every tool schema dropped selection accuracy to 13.62%, while retrieving the relevant one raised it to 43.13% and cut prompt usage from 2,133.84 tokens to 1,084 — and that accuracy degraded beyond roughly 100 candidates as retrieval precision fell. → Leaf: *test at your projected size, and plan for retrieval or routing rather than a bigger context.*

**Does the comparison break?** The 2023 NeurIPS MT-Bench paper found GPT-4 judges agreeing with human preference on more than 80% of comparisons — comparable to human-human agreement — while naming position, verbosity, and self-enhancement biases. A companion paper showed that under one setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. → Leaf: *swap order, control length, change judge. If the winner flips, you have a tie, and ties are broken on cost and blast radius.*

**B5: is the gap bigger than the measurement noise?** Here is the number that decides most cases. Two human evaluators' ratings correlated at a Pearson correlation of 0.85 in a 2026 RAG metrics study — that is the practical ceiling for a proxy metric. RAGChecker's claim recall sat near 0.7, and the authors warned that high correlation does not establish validity, because difficulty and other confounders produce strong correlations on their own. Their recommended method: evaluate at least two systems and compare outputs on the same questions.

- **Gap clearly bigger than the noise** → leaf: *buy it, then build the monitoring.*
- **Gap inside the noise** → leaf: *run both in shadow for two weeks and compare cost per successful run.* Not a third metric. A shadow run.

### Branch C: you are choosing a prompt

**C1: is this a task you will run many times?** If no, just write the prompt and move on. If yes, go to C2.

**C2: have you tried two materially different formulations?** A 2022 instruction-finetuning study found that instruction finetuning on instruction-phrased datasets improves performance and generalization to unseen tasks, evaluated across zero-shot, few-shot, and chain-of-thought prompting setups and across MMLU, BBH, TyDiQA, and MGSM. Flan-PaLM 540B finetuned on 1.8K tasks outperformed PaLM 540B by "+9.4% on average" and reached "75.2% on five-shot MMLU." A single formulation tells you almost nothing about the space.

**C3: how many candidates, and is the gap real?** Use the same standard as branch B. Judge agreement, order sensitivity, and the two-system comparison all apply. The 2026 RAG metrics finding is the general one: correlation with human ratings does not mean the metric measures what you think it measures.

**C4 leaf: choose on your own task set, and re-check.** There is a bandit-based framework that treats prompt selection as an online learning problem rather than offline hyperparameter optimization [UNVERIFIED — the paper's contents could not be retrieved, so no result is claimed here].

## The two cross-cutting checks

No matter which branch you land on, run these:

**Swap the order.** If the winner flips, you never had one.

**Read the trace, not the answer.** A 2026 agent-evaluation paper puts it directly: procedural failures can look plausible in the final response.

And one more, which surprises people. A 2026 source-attribution study found that across GPT-5.4 and Claude Opus 4.6, fact-check accuracy fell by roughly 42 percentage points on average as tool calls rose from 2 to 150, while link validity and topical relevance stayed above 92% the whole way. More searching produced worse attribution.

**Budget your depth before you start.** The list you build is not the evidence you have.

[AUTHOR EXPERIENCE: Replace with your real account — a branch you did not know existed, and a candidate that failed a check you had skipped.]

## What this cannot settle

This tree is my construction. No published work validates it, and some branches merge in ways I have not anticipated. The thresholds — "clearly bigger than the noise," "two materially different formulations" — are judgment calls, not measurements.

The numbers are setup-specific and dated. The judge-agreement figures are from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints. And a tree implies a determinism the underlying reality does not have: the same inputs will not always take the same branch.

What the tree cannot do is tell you which paper is worth reading on intellectual grounds. It tells you which slot it earns.

## Where to start this week

1. Identify which branch you are actually on. Write the letter.
2. Answer the first question on that branch before looking at any candidate.
3. Run the swap-order check on whatever comparison you ran last.
4. If you picked a prompt, write one materially different alternative and test both.
5. Set a 90-day reminder.

## Sources

- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases.
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation in long contexts.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation ≠ validity; two-system comparison.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: 13.62% vs 43.13%; 2,133.84 → 1,084 tokens; degradation beyond ~100 candidates.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; judges unreliable alone; human review essential; upstreaming expertise.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: strict vs relaxed grading roughly doubling scores; hard controls outside the model.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; ~42-point fact-check drop from 2 to 150 tool calls.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; metadata mismatch detection.
- Chung, H. W. et al. (2022). *Scaling Instruction-Finetuned Language Models*. ICLR 2023. https://arxiv.org/abs/2210.11416
  - Supports: instruction finetuning improves generalization; zero/few-shot/CoT setups; 1.8K tasks, +9.4% average, 75.2% five-shot MMLU.
- Manakina, O. & Bogdanov, I. (2026). *Learning to Grade Efficiently: A Bandit-Driven Prompt-Selection Framework for Low-Cost LLM Essay Scoring*. arXiv:2608.23814. https://arxiv.org/pdf/2608.23814
  - Status: `[UNVERIFIED]` — only the existence and framing of an online/bandit approach to prompt selection may be cited.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. One source is explicitly marked unverified in both the body and the source list. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Which branch are you on — and did you answer its first question before you started looking at candidates?
