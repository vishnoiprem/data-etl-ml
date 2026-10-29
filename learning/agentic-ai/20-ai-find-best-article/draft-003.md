---
title: "The Three Questions That Decide Which AI Tool You Ship"
subtitle: "What job, what breaks, who signs off — a minimal selection protocol for models, tools, and papers."
tags:
  - ai-evaluation
  - decision-framework
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - technical-leadership
  - ai-engineering
platform: linkedin
medium_publication: signal-scribe
target_length: 1250-1500
word_count: 1400
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 88
hard_fail: false
distinctness_angle: "Three-question frame (job / breaks / signs off) as the entire organizing device, with each question carrying its own sub-rules; comparative-table variant"
sources_count: 9
author_experience_placeholders: 1
---

Most "how do I choose" advice fails because it starts with the candidates. You scroll a leaderboard, collect names, and then reverse-engineer a job to fit whichever one looked best.

Start with the job instead. Three questions, in order.

## Question 1: What job, exactly?

Not "what do you want to use it for." What job, with inputs and outputs named.

A 2025 evaluation-ecosystem paper makes this argument formally. Evaluation should center on the "contextual unit" — the adaptive behavior of people using AI in a setting — rather than on the model. The recommended method is to define a theory of change with stakeholders: goals, inputs, outputs, outcomes, and counterfactuals. Name what happens if you get it wrong. Name who is affected.

That single sentence does most of the work that a scoring rubric pretends to do.

Here is where a job statement earns its keep. "Improve code quality" is not a job. "Turn an incoming Jira ticket into a patch that passes the repo's existing test suite, with no human edits beyond review" is a job — and that second version immediately tells you to check whether your candidate can invoke the test runner.

A 2025 survey of software-engineering agents makes the matching explicit. Straightforward generation, explanation, or small edits want an ordinary instruction-tuned model. Repository relationships and carefully ordered context want a structured or long-context model. Behavior that must consistently follow domain workflows or patch formats wants supervised fine-tuning. Security, efficiency, or correctness under executable feedback wants preference alignment or reinforcement learning, because those objectives are hard to express through demonstrations.

### The sub-rule: write the failure, not the feature

A job without a named failure has no selection criteria hiding inside it.

Use this form: *"We need X to do Y. The failure we cannot afford is Z. The evidence that Z is not happening is W."*

That last clause is what makes the job testable. Without W you cannot select, you can only hope.

## Question 2: What breaks?

Two candidates with similar scores differ in how they fail. And the difference in cost is often larger than the difference in score.

### It breaks silently

The output is plausible and wrong, with nothing flagging it.

A 2026 study on source attribution in AI research reports separated three checks and found the gap: link validity above 94%, relevance above 80%, and factual accuracy ranging from 24.4% to 76.8%. The same study found that across two frontier models, fact-check accuracy fell by roughly 42 percentage points on average as tool calls rose from 2 to 150 — more searching made attribution worse, while link and relevance stayed above 92% throughout.

The pattern: the checks that are easy to automate stay high, and the check that requires actually reading the source degrades under load.

**Your rule:** for each silent-failure candidate, name the deterministic check that would catch it. A candidate with no catchable check is a candidate you cannot deploy.

### It breaks in the middle of long context

A 2023 TACL paper, "Lost in the Middle," found models perform best when relevant material sits at the beginning or end of the context and "significantly degrades when models must access relevant information in the middle." Long-context models were not exempt.

**Your rule:** move the evidence and re-run. If the answer changes when you move the source, you have a layout dependency. Pin the layout.

### It breaks procedurally

The answer is fine. The process was not allowed to do that.

A 2026 paper on agent evaluation notes that procedural failures "can look plausible in the final response" — claiming a tool was used without invoking it, skipping a mandatory compliance call, calling tools in the wrong order. A companion benchmark for long-context agentic instruction following reached 36.2% strict pass@1 with its best configuration and recommended enforcing "hard controls outside the model."

**Your rule:** if the unacceptable failure is procedural, no amount of output-quality scoring will save you. You need a trace and a deterministic guard.

### It breaks at scale

A 2025 study of retrieval-based tool selection found that showing a model every tool schema dropped selection accuracy to 13.62%, while retrieving the relevant schema raised it to 43.13% and cut average prompt usage from 2,133.84 tokens to 1,084. It also found accuracy degrading beyond roughly 100 candidates as retrieval precision declined.

**Your rule:** test at the scale you will run at.

### It breaks in the comparison itself

The 2023 MT-Bench work found GPT-4 judges agreeing with human preference on more than 80% of comparisons — comparable to human-human agreement — while naming position bias, verbosity bias, and self-enhancement bias. The companion fairness paper showed how fragile close comparisons are: under one setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries.

**Your rule:** swap order, control length, change judge. If the winner flips, you never had a winner.

## Question 3: Who signs off?

This is the question that decides how much of the above you need to do yourself.

A 2026 agent-evaluation paper is precise about the division of labor. LLM judges are faster, cheaper, and repeatable, but unreliable as a sole evaluation authority — they have position, verbosity, and self-enhancement biases, limited reasoning ability, and may miss domain policies, required tool sequences, and trajectory-level failures. Human review remains "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions" — and is costly, slow, and hard to reproduce at every step.

So the third question has three possible answers:

**If the reviewer is a domain expert whose judgment you cannot encode**, stop trying to build a metric. Give them a rubric, a sample, and a disagreement rate, and measure their agreement with each other. A 2026 RAG metrics study found two human evaluators correlated at 0.85 with each other — that is your realistic ceiling, and a useful thing to publish.

**If the reviewer is an LLM judge**, you owe it three defenses: swapped order, controlled length, and a second judge from a different family. And you owe yourself an escalation trigger — the point where a human looks.

**If the reviewer is a deterministic check**, prefer it to everything. A unit test, a schema constraint, or a lookup table will beat any judge. A 2026 benchmark made the same argument from the guard side, recommending hard controls enforced outside the model.

## The three questions, side by side

| Question | If you cannot answer it | What to do instead |
|---|---|---|
| What job? | You are shopping, not selecting. | Write the job statement with a named failure and a named piece of evidence. |
| What breaks? | You will find out in production. | Take the top two candidates and test the specific failure you named. |
| Who signs off? | You will build a metric nobody trusts. | Choose judge, expert, or deterministic check, and configure the corresponding defenses. |

## Reading a paper runs the same three questions

**What job?** Are you looking for a technique to copy, a baseline to compare against, or a claim to challenge? A paper strong on a benchmark you do not care about is a poor benchmark for you.

**What breaks?** Check the citation practice, not just the results. A 2026 benchmark called CiteAudit found that across 9,442 citations, 2,967 were fabricated outright — and separately that some references existed but their title and author metadata did not match, which signals the paper was never read. Existence checks miss the second failure.

**Who signs off?** For a claim you intend to publish, the signer is you. A 2026 study on source attribution recommends evaluating claims against retrieved source content rather than checking that a link exists, and notes that web citations are temporally unstable — pages get paywalled, moved, and removed.

[AUTHOR EXPERIENCE: Replace with your real account — the tool you shipped, who actually signed off in practice, and whether that was the person you expected.]

## What this cannot settle

These three questions are a synthesis, not a validated instrument. No published study tests them as a selection protocol. The question order is my judgment.

Every number is setup-specific and dated. The judge agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Several of the strongest sources are arXiv preprints rather than peer-reviewed papers.

What the questions cannot settle: whether a given paper is worth your attention on aesthetic or taste grounds. They can settle whether it earns a slot.

## What to do this week

1. Answer question 1 for one decision you have pending. One sentence, with a named failure.
2. Answer question 2 by testing the top two candidates against that specific failure.
3. Answer question 3 out loud: judge, expert, or deterministic check.
4. Swap the order on your last comparison and see if the winner holds.
5. Set a 90-day reminder to re-check the choice.

## Sources

- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; limited reasoning ability.
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-dependent comparisons; 66-of-80 result.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation in long contexts.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human agreement as a realistic ceiling.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: 13.62% vs 43.13%; 2,133.84 → 1,084 tokens; degradation beyond ~100 candidates.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: judge limitations; human review essential for domain context, rubrics, escalation; cost of human review.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; hard controls outside the model.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% link validity vs 24.4–76.8% fact check; ~42-point drop from 2 to 150 tool calls; temporal instability of web citations.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; metadata mismatch reveals unread papers.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: "contextual unit"; theory of change; leaderboard overfitting and contamination.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: model selection by task complexity; benchmark scores guide rather than determine.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources recorded above. Several sources are arXiv preprints rather than peer-reviewed work, and the judge-agreement figures come from 2023-era models; the author notes both rather than presenting them as current. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Who actually signs off on the tools you choose — and is that the person you designed the evaluation for?
