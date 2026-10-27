---
title: "The One-Sentence Test for Any AI Tool, Paper, or Prompt"
subtitle: "Before you invest another hour: can you state what this is for, what breaks, and who checks?"
tags:
  - ai-evaluation
  - decision-making
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - technical-decisions
  - ai-engineering
platform: linkedin
medium_publication: signal-scribe
target_length: 1250-1500
word_count: 1440
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 85
hard_fail: false
distinctness_angle: "Single-question frame — one compound sentence that must be completable about any candidate, with three sub-tests inside it"
sources_count: 9
author_experience_placeholders: 1
---

Before you spend an hour on a candidate, answer one question in one sentence:

**"This is for [job], it fails by [mechanism], and [who] catches it."**

If you cannot fill all three blanks, you are not ready to evaluate the thing. And you might not need to.

That is the whole method. Everything below explains why those three blanks are the ones that matter, and what the published evidence says about each.

## Blank one: the job

A candidate without a named job is a candidate without an evaluation.

The framing comes from a 2025 evaluation-ecosystem paper, which argues that the unit of evaluation is not the model but the "contextual unit" — the adaptive behavior of people using AI in a setting. The recommended practice is to define a theory of change with stakeholders before comparing anything: goals, inputs, outputs, outcomes, and counterfactuals.

Translated into the blank: *"This is for drafting incident summaries from our ticket queue, and the person who checks them is the on-call engineer."*

Specific enough to test. "This is for content generation" is not a job, because nothing about it constrains the evaluation.

A 2025 survey of software-engineering agents shows what a well-specified job implies. Ordinary instruction-tuned models suit straightforward generation, explanation, or small edits. Structured or long-context models suit repository relationships and carefully ordered context. Supervised fine-tuning suits behavior that must consistently follow domain workflows or patch formats. Preference alignment or reinforcement learning suits objectives that are hard to express through demonstrations, like security, efficiency, or correctness under executable feedback. The job statement picks the row.

## Blank two: the mechanism

Not "it can fail." Every candidate can fail. *How* it fails, specifically.

This is where the published failure modes earn their place, because each one gives you a named, checkable mechanism.

**Silent failure.** The output is wrong and nothing flags it. A 2026 source-attribution study measured this gap precisely across 14 models and 130 research queries: link validity exceeded 94% and relevance exceeded 80%, while claim-level accuracy ranged from 24.4% to 76.8%. The link works. The page is on topic. The claim is still unsupported. → *Mechanism: no claim-level check.*

**Procedure failure.** The output looks fine; the process did something forbidden. A 2026 paper on agent evaluation is explicit that procedural failures "can look plausible in the final response" — an agent claiming a tool it never invoked, skipping a mandatory compliance call, calling tools out of order. → *Mechanism: no trace inspection.*

**Position failure.** It works when the evidence is where the model likes it. The 2023 TACL paper "Lost in the Middle" found models perform best at the beginning or end of the context and "significantly degrades when models must access relevant information in the middle" — explicitly long-context models included. → *Mechanism: no position test.*

**Scale failure.** It works at twenty tools and breaks at two hundred. A 2025 retrieval-based tool-selection study found that giving a model every tool schema dropped selection accuracy to 13.62%, while retrieving the relevant schema raised it to 43.13% and cut average prompt usage from 2,133.84 tokens to 1,084 — and that accuracy degraded beyond roughly 100 candidates as retrieval precision declined. → *Mechanism: no routing layer.*

**Comparison failure.** The ranking is an artifact. The 2023 NeurIPS MT-Bench paper found GPT-4 judges agreeing with human preference on more than 80% of comparisons while naming position bias, verbosity bias, and self-enhancement bias, plus "limited reasoning ability." A companion paper showed that under one setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. → *Mechanism: no order swap, no length control, single judge.*

**Over-investment failure.** More effort made it worse. Across GPT-5.4 and Claude Opus 4.6 in a 2026 source-attribution study, fact-check accuracy fell by roughly 42 percentage points on average as tool calls rose from 2 to 150 — one model from 78.6% to 16.7%, another from 80.0% to 57.9% — while link and relevance stayed above 92%. In a 2026 long-context agentic benchmark, raising reasoning effort helped some configurations by 2.0 to 3.0 points, left one unchanged, and hurt one by 2.7 points, with token spend ranging from roughly 13K to 60K per trial and no clean relationship to score. → *Mechanism: no depth budget.*

Pick the one your candidate actually has. A paper, by the way, has its own mechanism: the claim may not be supported by the cited source. A 2026 benchmark called CiteAudit found 2,967 fabricated references out of 9,442, and separately found references that exist but whose title or author metadata does not match — meaning the citing work never read the source.

## Blank three: the catcher

Who or what notices when it fails?

The answer decides how much of the rest you need to do, because the cost of a candidate is largely the cost of its failures.

A 2026 agent-evaluation paper describes the division of labor directly. LLM judges are faster, cheaper, and repeatable, but unreliable as a sole evaluation authority — they may miss domain policies, required tool sequences, and trajectory-level failures. Human review remains "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions," and is costly, slow, and hard to reproduce at every step. The proposed resolution is to move expert knowledge upstream into reusable evaluation artifacts, so a domain expert's judgment is compiled once and reused.

So the catcher is one of four things, and each has a different price:

- **A deterministic check.** Cheapest and fastest. A 2026 long-context agentic benchmark recommends enforcing "hard controls outside the model," compiling policies into deterministic tool-call guards rather than relying on in-context adherence. Its best configuration still scored 36.2% strict pass@1, and it noted that tolerating one violated control roughly doubles leader scores — which is what a weak catcher looks like in a number.
- **A domain expert on a sample.** Reliable and slow. Use a rubric, and measure the expert's agreement with another expert: in a 2026 RAG metrics study, two human evaluators correlated at a Pearson correlation of 0.85, which is the realistic ceiling and therefore a number worth knowing.
- **An LLM judge at scale.** Cheap and repeatable, with three named biases you must correct for.
- **Nobody.** This is the honest answer for some candidates, and it is disqualifying in any domain where the failure matters. It is occasionally fine where the failure is genuinely trivial and recoverable.

**If blank three is "nobody," stop.** Do not evaluate the candidate on quality. There is no decision to make.

## The sentence, with a worked example

*"This is for answering internal policy questions from our 40k-document wiki, it fails by retrieving the wrong policy version and citing it confidently, and our compliance reviewer catches it two days later — at which point it has already been quoted in three Slack threads."*

Three blanks, all filled. And now the next questions are answerable:

- **Is two days of detection latency acceptable?** Probably not, for a policy system. Add a version check on the retrieved document. That is a deterministic catcher, and it moves the candidate to a different cost class.
- **Is the retrieval failing because of position or because of the index?** Test both. The 2023 TACL result says position is a live possibility; a 2026 RAG metrics study says score the retrieval stage separately from generation, because human agreement tops out at 0.85 and RAGChecker's claim recall sat near 0.7 while still possibly reflecting question difficulty rather than retrieval quality. Their method: evaluate at least two systems on the same questions.
- **Should a human still review it?** The 2026 agent-evaluation work says human review stays essential for domain context and escalation decisions, especially in regulated settings.

One sentence, and the whole evaluation has a shape.

## The same sentence for papers and prompts

**Paper:** *"This is for justifying a design decision in our pipeline, it fails by reporting a benchmark result that its own methodology does not support, and I catch it by reading the failure definition."*

That is checkable, and it is the check most people skip. The 2026 long-context agentic benchmark's strict-versus-relaxed distinction shows why: tolerating one violated control roughly doubles leader scores, so a paper that does not say which number it is reporting is not giving you a result.

**Prompt:** *"This is for structuring incident write-ups, it fails by dropping the severity field when the input is unusual, and the on-call engineer notices at triage."*

The catcher here is a person, which means you have a human-in-the-loop cost to price, and the 2026 agent-evaluation paper's guidance applies: encode the rule once so it does not need a person every time.

[AUTHOR EXPERIENCE: Replace with your real account — a candidate that passed every check and still failed, and what you had not written down.]

## What this cannot settle

The one-sentence test is my construction. No published work validates it, and it is a compression, not a proof — a candidate that passes it can still be wrong.

The numbers are setup-specific and dated. The judge-agreement figures are from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

The test will not tell you which candidate is best. It tells you which candidates deserve the next hour, which is a more useful answer and the one the sentence is actually built to produce.

## Where to start this week

1. Write the one sentence for the candidate you are currently considering.
2. If blank three is "nobody," stop and fix that first.
3. Name the mechanism from the list above that your candidate actually has.
4. Test that one mechanism. One test, not six.
5. Fill the sentence for the candidate you rejected last time, and see which blank was empty.

## Sources

- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: "contextual unit"; theory of change with stakeholders; field testing.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: model selection by task complexity; scores guide not determine.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; ~42-point drop from 2 to 150 tool calls; 78.6%→16.7% and 80.0%→57.9%.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; judges unreliable alone; human review essential for specific decisions; upstreaming expertise.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; strict vs relaxed grading; reasoning-effort variance; 13K–60K tokens; hard controls outside the model.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; difficulty confound; two-system comparison.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation in long contexts.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: 13.62% vs 43.13%; 2,133.84 → 1,084 tokens; degradation beyond ~100 candidates.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; metadata mismatch reveals unread papers.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Which blank is empty for the candidate you are evaluating right now?
