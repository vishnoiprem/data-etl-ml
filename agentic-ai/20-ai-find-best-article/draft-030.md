---
title: "The Best Tool Is the One You Can Explain: Why Explainability Is the First Selection Criterion"
subtitle: "Ranking tools by explainability first, and the evidence that untraceable systems are unselectable — not just risky."
tags:
  - ai-evaluation
  - explainability
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - ai-engineering
  - governance
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1470
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 89
hard_fail: false
distinctness_angle: "Explainability-first argument — inverts the usual ordering so that traceability is the first filter, not the last consideration"
sources_count: 10
author_experience_placeholders: 1
---

Most selection frameworks start with quality and end with cost. This one starts with a different question entirely: **if this fails, will you be able to find out why?**

That question should be answered before you compare any scores, and the reason is not governance theater. It is that untraceable systems are unselectable.

## The argument

A selection process is a measurement process. You choose one candidate over others by observing differences. If the system under test will not tell you what it did, then:

- You cannot tell whether a good result was luck or correctness.
- You cannot tell whether a bad result is a candidate problem or a configuration problem.
- You cannot tell whether a regression came from the model, the prompt, the data, or a Tuesday.
- You cannot reproduce the result for the person who asks six months from now.

None of those are governance concerns. They are the mechanics of not being able to run an evaluation at all.

## What the evidence says about opacity as a failure mode

A 2026 paper on agent evaluation is the clearest statement, and it is about the output rather than the internals. Procedural failures "can look plausible in the final response." An agent can claim it used a tool it never invoked, omit a mandatory compliance call, and call tools in the wrong order — and the prose reads correctly.

The same work separates deterministic detections from subjective judgments. A phantom tool call or an omitted compliance action is checkable against the trace, and objective once the trace is available. This is the point: **the trace converts an unobservable failure into a lookup.** Without it, you are reading the agent's account of what it did.

And a 2026 long-context agentic instruction following benchmark made the same recommendation from the enforcement side: enforce "hard controls outside the model," compiling policies into deterministic tool-call guards rather than relying on in-context adherence. Its best configuration scored **36.2% strict pass@1** — still failing nearly two of every three tasks — and it noted that relaxing the strict criterion to tolerate one violated control roughly doubles leader scores. Opacity is also where the grading inflation lives.

The opacity problem shows up in a second domain too, which is instructive. A 2026 study of source attribution in AI research reports scored each claim-citation pair on three dimensions — link works, content relevant, source supports the claim. Link validity exceeded **94%** and relevance exceeded **80%**, while factual accuracy ranged from **24.4% to 76.8%**. The visible surface was healthy. The supported content was not.

## So make explainability the first filter

Not a criterion you weigh. A criterion you pass. Here is the filter in five questions, and any "no" ends the evaluation.

**Can you see what it retrieved?** Not the count — the content. If you cannot read what was retrieved, you cannot check whether the answer had support.

**Can you see what it did?** Every tool call, with arguments and order. If a tool call is missing from the trace, the output's account of it is unverifiable.

**Can you see where the answer came from?** Claim-level attribution, not a link. The 2026 source-attribution study's three-way separation is the right shape: link validity is nearly worthless on its own, and relevance is nearly worthless on its own.

**Can you pin the version?** The model, the prompt, the retrieval index, the tool versions. A result you cannot reproduce is a story.

**Can you change one thing and see what moved?** This is the one that determines whether you have an evaluation or a demo. If every change produces a new opaque result, you cannot attribute anything.

That fifth question is where the literature on judgment bias becomes operational. The 2023 NeurIPS MT-Bench paper found GPT-4 judges agreeing with human preference on more than 80% of comparisons — comparable to human-human agreement — while naming position bias, verbosity bias, and self-enhancement bias, plus "limited reasoning ability." The companion paper showed the stakes: under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. An opaque system cannot be defended against a single-order comparison. A traceable one can be re-run in both orders in an afternoon.

## Explainability is not the same as transparency theatre

It is worth being precise, because "explainability" gets used to mean two different things and the second one is a trap.

**Not this:** a generated rationale that explains the output. Models produce fluent justifications that need not correspond to how the answer was produced, and they cost tokens and latency to generate.

**This:** access to the intermediate state — what was retrieved, what was called, what was assembled — so a human or a rule can check the work.

The second is what makes selection possible. The first is decoration.

## The explainable-first comparison sheet

| Question | What to record | Why it gates |
|---|---|---|
| Retrieval visible? | The retrieved passages, not a count | Without it, no support check is possible |
| Tool calls visible? | Call, arguments, order | Procedural failures are otherwise invisible |
| Claim attribution visible? | Which source supports which claim | Link validity alone is nearly worthless |
| Version pinned? | Model, prompt, index, tool versions | Reproducibility |
| Single-variable changes attributable? | One change → one measurable delta | Without this, no evaluation loop exists |

**The fifth row is the one most teams fail.** If you change the prompt and the retrieval index at the same time, and the score moves, you have learned nothing. That is not an unusual situation. That is most evaluations.

A 2026 RAG metrics study offers the technique that makes attribution work: evaluate at least two systems and compare their outputs on the same questions, so shared question difficulty cancels out and you can see which system did what differently.

## The cost of explainability, honestly

It is not free, and a memo that hides this will be resented.

**Latency and tokens.** Storing and returning traces costs something. For most systems the cost is storage and serialization, not model time — but if your system must re-derive state, it can be expensive.

**Schema rigidity.** Traceable systems expose a stable interface. That interface is a constraint on the vendor and a constraint on you, and it is real.

**Some systems resist it.** Closed platforms offer limited introspection. This is a legitimate reason to reject a candidate, and it should be a rejection, not a discount.

**The benefit, though, is compounding.** A traceable system can be re-evaluated for free, compared against a new candidate for free, and explained to a colleague for free. A 2026 agent-evaluation paper makes a version of this point about evaluation infrastructure generally — move expert knowledge upstream into reusable artifacts so it can be applied repeatedly without re-deriving it. A trace is the same idea applied to a single system.

And it changes the shape of the human-review decision. That paper describes human review as "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions" while also being "costly, slow, and hard to reproduce" at every step. With a trace, the reviewer reads a transcript instead of guessing. That is the difference between a review that scales and one that does not.

## For papers, the same filter

A paper you cannot trace is a paper you cannot build on.

A 2026 benchmark called CiteAudit tested this directly. Of 9,442 citations, 2,967 were fabricated outright. More usefully, it detected references that exist but whose title or author metadata does not match — which signals the citing work never read the source. A 2026 source-attribution study makes the parallel case for claims: link validity above 94%, relevance above 80%, claim-level accuracy 24.4%–76.8%.

**The traceable-paper test:** can you find the passage? Can you see the failure definition? Can you see the denominator? Can you tell which part of the result came from which part of the method?

A 2026 long-context agentic benchmark models the third one well — reporting strict pass@1 alongside a relaxed variant, and being explicit that relaxing roughly doubles leader scores.

[AUTHOR EXPERIENCE: Replace with your real account — a system you could not trace, and what that cost you.]

## What this cannot settle

The five-question filter is my construction. No published work validates it, and not every valuable system is fully traceable — a closed consumer product may be entirely adequate for a low-stakes job, and rejecting it for opacity alone would be over-strict.

The numbers are setup-specific and dated. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — NeurIPS 2023, TACL 2023, AAAI 2024 — are also the older ones.

And explainability does not make a system correct. It makes a system debuggable, and debuggable systems are the only ones you can responsibly select. That is a smaller claim than "the traceable one is better," and it is the one the evidence supports.

## Where to start this week

1. Ask your current tool for its retrieved passages. If you cannot get them, that is finding one.
2. Pull the tool-call trace from one recent run and look for calls the output claimed but the trace does not show.
3. Pin the versions behind your current setup. Write them down.
4. Change one thing and re-run. See whether you can attribute the delta.
5. Add a traceability row to your comparison sheet.

## Sources

- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; deterministic vs subjective detection; trace as evidence; human review essential for domain context and escalation; upstreaming expertise.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; strict vs relaxed grading; hard controls outside the model.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; three-way separation of link, relevance, and claim support.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; two-system comparison method; correlation ≠ validity.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; metadata mismatch reveals unread papers.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: contextual unit framing; field testing; leaderboard overfitting.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: validation loops and observable tool use in agent workflows.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: scale criteria and prompt-cost measurement.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Can you get the retrieved passages from the tool you use most — right now, without asking anyone?
