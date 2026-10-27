---
title: "Which AI Tool Is Right Depends on Which Role Is Doing the Picking"
subtitle: "Four people in your organization need four different selection criteria — and using the wrong one is how teams fight."
tags:
  - ai-evaluation
  - team-decisions
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - technical-leadership
  - ai-engineering
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1490
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 88
hard_fail: false
distinctness_angle: "Persona-based lens — four roles (analyst, ML engineer, agent builder, team lead) each with a distinct selection rule set, plus a mediation protocol"
sources_count: 9
author_experience_placeholders: 1
---

The same shortlist of AI tools produces four different arguments in the same building.

The data scientist wants the best retrieval quality. The ML engineer wants reproducibility. The agent builder wants reliable tool-calling. The team lead wants a number they can put in a budget deck.

They are not having a disagreement about facts. They are answering four different questions, and nobody said so out loud.

## The role decides the criteria

Here is the uncomfortable part: there is no single "best tool" to find, because "best" is a function of the role that will live with the tool. Give each role its own criteria and the arguments resolve.

### The data analyst: retrieval quality first

This person's failure is a wrong number, and they will not know until a report ships.

Their criteria: **retrieval quality, then generation quality, then cost.** In that order, always.

The reason is technical. A 2026 study of RAG evaluation metrics found human evaluators agreeing with each other at a Pearson correlation of 0.85 — the practical ceiling for a proxy metric. Against that reference, RAGChecker's recall-oriented metrics correlated best, with claim recall near 0.7. But the study's warning matters more than the number: high correlation does not establish validity, because difficulty and other confounders can produce strong correlations on their own. Their method for avoiding this: evaluate at least two systems and compare outputs on the same questions.

The analyst's rule: **split the score.** Retrieval and generation, separately, always. The 2024 RGB benchmark found models "still struggle significantly in terms of negative rejection, information integration, and dealing with false information" even with retrieval attached, so a combined score hides which half is broken.

### The ML engineer: reproducibility and traceability

This person's failure is a result they cannot reproduce, a model version they cannot pin, a decision they cannot explain six months later.

Their criteria: **can you pin the version, re-run the result, and explain the output?** If the answer to any of those is no, the score is irrelevant.

A 2026 paper on agent evaluation is the sharpest expression of this. It argues that the unit of evaluation is the "contextual unit" — the behavior of a person using AI in context — and that static benchmarks do not adequately test multi-turn tool use, policy adherence, recovery, or procedural consistency. A model can ace a fixed benchmark and then fail operationally through "missing tool calls, hallucinated tool use, policy drift, unsafe reframing, manipulation paths, or over-refusal."

The engineer's rule: **the trace is the deliverable.** If you cannot show which steps ran, in what order, you do not have a result — you have an anecdote.

### The agent builder: tool-routing behavior at scale

This person's failure is a routing decision made wrongly, at 3am, by a model that had every tool description in its context.

Their criteria: **selection accuracy at your real catalog size, and prompt cost per call.**

A 2025 study of retrieval-based tool selection gives the numbers. Presenting every tool schema to the model dropped selection accuracy to 13.62%. Retrieving just the relevant schema raised it to 43.13% and cut average prompt usage from 2,133.84 tokens to 1,084. The same work found accuracy degrading beyond roughly 100 candidates as retrieval precision declined, which is a scaling limit, not a tuning problem.

The builder's rule: **test at the size you'll run at.** A registry of 20 and a registry of 200 are different systems.

And a second rule, from darker research. A 2025 paper, ToolTweak, showed that a gradient-free black-box attack that rewrites a tool's *name and description* — schema untouched — drove selection rates against an approximately 20% baseline up to 81.6% on one model and 34.0% on another. The builder's rule: **an agent's choice is evidence about the description, not only about the capability.** Audit your registry's metadata.

### The team lead: cost, risk, and who signs off

This person's failure is a procurement mistake that surfaces in a review six months out.

Their criteria: **cost per successful run, blast radius, and who is accountable when it fails.**

A 2026 long-context agentic benchmark shows how easily cost and quality decouple. One configuration reached 21.5% on roughly 13K generated tokens per trial. Another spent close to 60K tokens at about three times the dollar cost for the same band. Several mid-pack configurations generated 45–55K tokens and scored in single digits. The best configuration overall reached 36.2% strict pass@1 — still failing nearly two of every three tasks.

The lead's rule: **a candidate that fails in a way you can trace is cheaper than one that fails quietly.** The 2026 agent-evaluation work puts the same idea in evaluation terms: human review stays "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions," while LLM judges remain unreliable as a sole authority because of position bias, verbosity bias, self-enhancement bias, and limited reasoning.

## The protocol that stops the argument

The four roles do not need to agree on a winner. They need to agree on the order of operations.

**Step 1: the analyst sets the task set.** 20–30 questions from real closed work. This is the only part that is not negotiable, because it is the only part that reflects your data.

**Step 2: the ML engineer gates on traceability.** Candidates that cannot be pinned, re-run, and explained are eliminated regardless of score. This removes most of the argument, because most arguments are about scores.

**Step 3: the agent builder gates on scale.** Test routing at your projected catalog size. This kills candidates that would work today and break next quarter.

**Step 4: the analyst scores retrieval and generation separately.** No combined number. If the gap is inside measurement noise — which the 0.85 human-human correlation suggests it usually is — call it a tie.

**Step 5: the lead decides the tiebreaker on cost and blast radius.** Not on score. The tie is real, and cost and blast radius are the dimensions the lead owns.

**Step 6: everyone agrees on the escalation trigger in advance.** Regulated domain; scores inside the noise band; a judge rather than a human signing off. A 2023 paper on fair LLM evaluation is instructive here: when two answers are close and order-sensitive, the "balanced position diversity entropy" measure triggers human assistance. Write that trigger down before you see the numbers.

## Two checks that apply to every role

**Swap the order.** The 2023 NeurIPS MT-Bench paper found GPT-4 judges agreeing with human preference on more than 80% of comparisons — comparable to human-human agreement — while exhibiting position, verbosity, and self-enhancement biases. A companion paper showed the stakes: under one setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. Any ranking that flips when you swap is not a ranking.

**Move the evidence.** The 2023 TACL paper "Lost in the Middle" found models perform best at the beginning or end of the context and "significantly degrades when models must access relevant information in the middle" — including in explicitly long-context models. If the result depends on where the evidence sits, you have a layout dependency.

## And for papers

Papers get picked by a different role, but the same protocol works.

The **analyst** asks whether the benchmark resembles your data. The **engineer** asks whether the failure accounting is rigorous — a 2026 long-context agentic benchmark noted that relaxing a strict criterion roughly doubles leader scores, which is a useful thing to know about any leaderboard you read. The **agent builder** asks whether the trace is inspectable. The **lead** asks what it costs you to act on the claim.

And everyone should run the same citation check. A 2026 benchmark called CiteAudit found 2,967 fabricated references out of 9,442 — and, more usefully, found references that existed but whose title or author metadata did not match, indicating the paper was never read. A second 2026 study on source attribution found link validity above 94% and relevance above 80% while factual accuracy ranged from 24.4% to 76.8%. Working links, on-topic pages, unsupported claims.

[AUTHOR EXPERIENCE: Replace with your real account — a tool decision where two roles wanted different things, and how the disagreement was actually resolved.]

## What this cannot settle

This four-role framing is my construction, not a validated model of team decision-making. No study tests it.

The underlying numbers are setup-specific and dated. Judge agreement comes from 2023-era models; the 2026 work updates the picture without replacing them. Most of the 2026 sources are preprints, and the peer-reviewed ones — NeurIPS for the judge work, TACL for the long-context work, AAAI for the RAG benchmark, ACL for TruthfulQA — are also the older ones. A 2025 evaluation-ecosystem paper also warns that leaderboards can overstate differences while obscuring common failure modes, which is another reason the analyst's task set comes first.

The framing cannot resolve a genuine disagreement about which risk to accept. It can only make the disagreement explicit, which is where it has to start.

## Where to start this week

1. Ask each role on your team to write their top two criteria, separately, without talking.
2. Build the task set from real closed work. 20–30 items.
3. Gate on traceability and scale before you score anything.
4. Swap the order on whatever comparison you ran last.
5. Put the escalation trigger in writing before the next evaluation.

## Sources

- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker claim recall near 0.7; correlation ≠ validity; evaluate at least two systems.
- Chen, J. et al. (2024). *Benchmarking Large Language Models in Retrieval-Augmented Generation*. AAAI 2024. https://arxiv.org/abs/2309.01431
  - Supports: persistent failure in negative rejection, information integration, false information.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: 13.62% vs 43.13%; 2,133.84 → 1,084 tokens; degradation beyond ~100 candidates.
- *ToolTweak* (2025). arXiv:2510.02554. https://arxiv.org/html/2510.02554v1
  - Supports: name/description attack; 81.6%–34.0% vs ~20% baseline; distribution shift.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: static benchmarks miss operational failure; trace analysis necessary; human review essential for specific decisions; judge biases.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; 13K vs 60K tokens at ~3× cost; strict vs relaxed grading.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases.
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result; position-diversity-entropy human trigger.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation in long contexts.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; metadata mismatch reveals unread papers.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% link validity vs 24.4–76.8% factual accuracy.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; leaderboards overstate differences and hide common failure modes.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Whose criteria were used the last time your team picked a tool — and whose were quietly ignored?
