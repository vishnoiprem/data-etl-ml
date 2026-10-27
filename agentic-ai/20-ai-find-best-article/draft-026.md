---
title: "Agentic AI Is Not Chat With Extra Steps: How to Evaluate What Actually Changed"
subtitle: "A selection method for systems that take actions — where the answer is not the deliverable and the trace is."
tags:
  - agentic-ai
  - ai-evaluation
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - ai-engineering
  - agents
platform: linkedin
medium_publication: signal-scribe
target_length: 1350-1600
word_count: 1540
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 92
hard_fail: false
distinctness_angle: "Agentic-system specialisation — a selection method built for action-taking systems; evaluates trajectories, tool calls, and recovery rather than output text"
sources_count: 11
author_experience_placeholders: 1
---

An agent that answers badly has wasted your token budget.
An agent that acts badly has changed your systems.

That asymmetry should change how you evaluate it, and most of the tooling still does not.

## The output is not the deliverable

When you choose a chatbot, the output is the thing. When you choose an agent, the output is a summary of things that happened, and the things that happened are the deliverable.

A 2026 paper on agent evaluation makes this the central distinction, and it is blunt about the consequence. Static benchmarks do not adequately test multi-turn tool use, policy adherence, recovery, or procedural consistency. A model can score well on a fixed benchmark and then fail operationally through "missing tool calls, hallucinated tool use, policy drift, unsafe reframing, manipulation paths, or over-refusal."

Read that list again. Every entry is invisible in the final text.

## What to evaluate instead

### 1. The trajectory, not the answer

A 2026 long-context agentic instruction following benchmark made this the core of its design, and its framing is useful: existing evaluations "measure reading," whereas an agentic setting requires details to "remain operative dozens of tool calls after they were read."

So: score the sequence. Did the right calls happen, in the right order, with the required calls present?

The same benchmark's grading discipline is a model for how to do this. It reported strict pass@1 alongside a relaxed variant tolerating one violated control, and noted that relaxing roughly doubles leader scores — a deployment tolerating one violation per workflow "has effectively abandoned strictness." Its best configuration scored **36.2% strict pass@1**, meaning even the best system failed nearly two of every three tasks.

That number should calibrate every agentic claim you read. Including vendor claims.

### 2. The phantom call

The failure the 2026 agent-evaluation paper highlights: an agent claims it used a tool it never invoked.

This is deterministically checkable. If you have the trace, you know. The paper treats this class of finding as objective once the trace is available, which is the key point — it is not a judgment call, it is a lookup.

**Rule: if your agent reports tool use, the trace is a required artifact.** Not a nice-to-have for debugging. The output of an agent that calls tools is not trustworthy without it.

### 3. The omitted call

Sometimes the failure is an action that should have happened and did not. A mandatory compliance check, a verification step, a confirmation before an irreversible action.

The 2026 long-context agentic benchmark's recommendation is the right engineering answer: enforce "hard controls outside the model," compiling policies into deterministic tool-call guards rather than relying on in-context adherence. Prompt it harder and you get a system that fails about a third of the time. Guard it in code and the failure rate is a property of your code.

### 4. The recovery

Can it recover when a step fails?

Static benchmarks almost never test this, which the 2026 agent-evaluation paper lists among the gaps static benchmarks do not cover. If your agent calls an API that times out, what happens? If a tool returns garbage, does it try again, try something else, or confidently proceed?

**Test it by breaking it.** Give the agent a tool that fails on purpose, on purpose, and see what it does. That is a test you can write in an afternoon and it will find more than a benchmark will.

### 5. The routing decision

Does it pick the right tool?

A 2025 study of retrieval-based tool selection gives the scale. Presenting every tool schema to the model dropped selection accuracy to **13.62%**; retrieving just the relevant schema raised it to **43.13%** and cut average prompt usage from 2,133.84 tokens to 1,084. The same work found accuracy degrading beyond roughly **100 candidates** as retrieval precision declined.

And a 2025 paper, ToolTweak, shows that routing is not purely a capability signal. A gradient-free black-box attack rewriting a tool's name and description — schema unchanged — drove selection rates against an approximately 20% baseline up to 81.6% on one model and 34.0% on another, shifting the overall distribution away from expected parity. The paper's framing: risks to "fairness, competition, and security in emerging tool ecosystems."

**So: audit your registry metadata.** If a competitor rewrote their description tomorrow, how much of your agent's traffic moves? If a lot, your routing is a function of copy.

### 6. The effort spent

Does more thinking help?

The 2026 long-context agentic benchmark found that raising reasoning effort helped some configurations by 2.0 to 3.0 points, left one unchanged, and **hurt one by 2.7 points**, with token spend ranging from roughly 13K to 60K per trial and no clean relationship to score. One configuration reached 21.5% on about 13K tokens; another spent close to 60K for the same band at roughly three times the cost.

The authors' interpretation is the useful bit: deliberation converts into compliance only when the underlying error was a "missed inference rather than a missed read." Diagnose which you have before you spend.

### 7. The claim support

For agents that produce reports or take research actions, check the claims against the sources.

A 2026 study of source attribution in AI research reports separated three checks — link works, content relevant, source supports the claim — and across 14 models and 130 research queries found link validity above **94%** and relevance above **80%**, while factual accuracy ranged from **24.4% to 76.8%**. It also found that fact-check accuracy fell by roughly **42 percentage points on average** across two frontier models as tool calls rose from 2 to 150, even as link and relevance stayed above 92%. More searching, worse attribution.

## The agent selection sheet

| Dimension | What to measure | Source of truth |
|---|---|---|
| Task fit | Success rate on your real task set, scored strictly | Your frozen question set |
| Trajectory correctness | Required calls present, in order | The trace |
| Safety | Irreversible actions gated | Deterministic guards, not prompts |
| Recovery | Behavior on tool failure | A deliberately broken tool |
| Routing | Selection accuracy at your registry size | Selection test at real scale |
| Attribution | Claim supported by retrieved content | The source, not the link |
| Cost | Tokens and dollars per successful run | Your logs |

Two rows do not produce a number: safety and recovery. They produce a yes or a no, and a no ends the evaluation.

## On the human reviewer

A 2026 agent-evaluation paper is precise about where human review belongs. LLM judges are faster, cheaper, and repeatable, but unreliable as a sole evaluation authority — they may miss domain policies, required tool sequences, and trajectory-level failures. Human review remains "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions," and it is costly, slow, and hard to reproduce at every step.

Its proposal is the one I would steal: move expert knowledge upstream into reusable evaluation artifacts. Encode the domain expert's rules once, apply them on every run, and let the expert review what the rules flag. That paper's own study ran 47 configurations, 470 trials, and 23,500 turns — which is only feasible because the rules were compiled, not re-derived each time.

And for judging output quality at scale, a 2026 RAG metrics study gives you the honest ceiling: two human evaluators' ratings correlated with each other at a Pearson correlation of **0.85**. RAGChecker's recall-oriented metrics correlated best, with claim recall near 0.7, but high correlation does not establish validity, because difficulty and other confounders produce strong correlations on their own. Their method: evaluate at least two systems on the same questions.

## A note on leaderboards

Judge-based leaderboards need specific defenses. The 2023 NeurIPS MT-Bench paper found GPT-4 judges agreeing with human preference on more than 80% of comparisons — comparable to human-human agreement — while naming position bias, verbosity bias, and self-enhancement bias. The companion paper showed that under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. Swap order, control length, change judge family. If the winner flips, you had a tie.

[AUTHOR EXPERIENCE: Replace with your real account — an agent action that changed a system, and which of the seven checks would have caught it.]

## What this cannot settle

This agentic focus is my choice, not a claim that agents are the most important case. For a document-summarisation tool, most of these checks are irrelevant.

The numbers are setup-specific and dated. The judge figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And no published framework validates a seven-row selection sheet for agentic systems. The 2026 agent-evaluation paper explicitly notes its own juror scores were not calibrated to human experts and that its non-factorial design limits definitive rankings.

## Where to start this week

1. Require traces for one agent. Store them.
2. Write a strict definition of success for one task — no tolerated violations.
3. Break a tool on purpose and watch what the agent does.
4. Audit your tool registry's descriptions.
5. Check one report's claims against one source.

## Sources

- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: static-benchmark gaps; operational failure modes; trace analysis; judges unreliable alone; human review essential; upstreaming expertise; 47 configurations / 470 trials / 23,500 turns; juror calibration caveat.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: "measure reading" framing; strict vs relaxed grading; 36.2% strict pass@1; reasoning-effort variance; 13K–60K tokens; missed-inference interpretation; hard controls outside the model.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: 13.62% vs 43.13%; 2,133.84 → 1,084 tokens; degradation beyond ~100 candidates.
- *ToolTweak* (2025). arXiv:2510.02554. https://arxiv.org/html/2510.02554v1
  - Supports: name/description attack; 81.6%–34.0% vs ~20% baseline; distribution shift; metadata defenses.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; ~42-point fact-check drop from 2 to 150 tool calls; 14 models, 130 queries.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation ≠ validity; two-system comparison.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases.
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation for long-context agent work.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; red teaming; field testing.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: executable environments, validation loops, recovery as agent capabilities.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Which of the seven checks have you never run against an agent you actually run?
