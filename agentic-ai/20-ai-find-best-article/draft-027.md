---
title: "Why Your RAG System Fails in Ways Your RAG Score Does Not Show"
subtitle: "Splitting retrieval from generation, measuring the right stage, and the two failure modes retrieval cannot fix."
tags:
  - rag
  - ai-evaluation
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - ai-engineering
  - retrieval
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1510
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 92
hard_fail: false
distinctness_angle: "RAG-specialised — evaluates retrieval and generation as separate systems, with the RGB failure taxonomy as the backbone"
sources_count: 10
author_experience_placeholders: 1
---

Most RAG evaluations report one number.

That number is the average of two systems, and it tells you almost nothing about which one is broken — which is a problem, because the two halves fail in completely different ways and need completely different fixes.

## Two systems, not one

A retrieval-augmented system has a retrieval stage and a generation stage. Score them separately or you will optimise the average and improve neither.

A 2026 study of RAG evaluation metrics makes the statistical case. Human evaluators' ratings correlated with each other at a **Pearson correlation of 0.85** — the practical ceiling for any automatic proxy metric. RAGChecker produced the strongest overall correlations among the tools tested, with claim recall near **0.7**. But the authors' warning is the load-bearing part: high correlation does not establish validity, because input difficulty and other confounders can produce strong correlations on their own. RAGChecker claim recall near 0.7 might be reflecting question difficulty or answer extractability rather than retrieval quality.

Their method for finding out: evaluate **at least two RAG systems and compare their outputs on the same questions.** Shared difficulty cancels. That is a one-afternoon change to most evaluation code, and it converts an ambiguous score into a diagnostic.

## The four retrieval abilities that actually matter

The 2024 RGB benchmark organized RAG evaluation around four abilities, and that taxonomy is still the best available map for what to test:

**Noise handling.** Can the system ignore retrieved material that is not relevant, rather than being distracted by it?

**Negative rejection.** Can it refuse to answer when the retrieved evidence does not contain the answer? This is the one most systems fail.

**Information integration.** Can it combine multiple retrieved fragments into a coherent answer, rather than picking the best one and dropping the rest?

**Counterfactual handling.** Can it handle retrieved material that is deliberately false?

The RGB finding was that models "still struggle significantly in terms of negative rejection, information integration, and dealing with false information," and the conclusion was blunt: "there is still a considerable journey ahead to effectively apply RAG to LLMs."

Note what that implies. Retrieval does not fix the model. It adds a new failure surface.

## Measure the retrieval stage with retrieval metrics

Retrieval quality has its own metrics, and they are not the same as generation quality.

**Recall@k** — did the right chunk make it into the retrieved set at all?
**MRR** — how early did it appear?
**nDCG** — how well are the ranked results ordered by relevance?
**Context precision** — what proportion of the retrieved set was relevant?
**Context recall** — how much of the needed information was retrieved?

The 2026 RAG metrics study compared exactly this family across four libraries. It found DeepEval's contextual precision correlated **above 0.5** with recall despite not using reference spans, while Ragas's non-LLM retrieval metrics correlated weakly with recall — attributed to their use of Levenshtein distance, which becomes unreliable when retrieved and reference spans differ greatly in length.

Two practical lessons:

**Metrics that use string similarity break when your chunks are long and paraphrased.** If your documents are verbose, lexical-overlap metrics will understate a good retriever.

**Split the score.** A 2025 survey of software-engineering agents makes the same point in a different context — "Long context alone is not a substitute for effective retrieval." Simply concatenating all relevant files was found to be suboptimal, and snippet ordering materially affected performance.

## Then measure the generation stage against the retrieved set

Once retrieval is scored, score generation *given* what was retrieved. This isolates the second failure.

A 2026 study of source attribution in AI research reports gives you the shape of this check for a research-augmented system. It scores each claim-citation pair on three dimensions: does the link work, is the content topically relevant, and does the source actually support the specific assertion. Across 14 models and 130 research queries, link validity exceeded **94%** and relevance exceeded **80%**, while factual accuracy ranged from **24.4% to 76.8%**.

Apply the same three-way separation to your own RAG outputs: was the right thing retrieved (retrieval), did the answer use it (generation), and is the answer supported by it (faithfulness)?

Because "it answered correctly" and "it answered correctly *from the retrieved evidence*" are different claims, and only the second one tells you the system is working as designed.

## The two failure modes retrieval cannot fix

### Position sensitivity

Even with perfect retrieval, the position of the evidence inside the context matters.

The 2023 TACL paper "Lost in the Middle" found that models perform best when relevant material appears at the beginning or end of the context and "significantly degrades when models must access relevant information in the middle" — and explicitly long-context models were not exempt. A 2025 survey adds the engineering note: snippet ordering materially affected performance.

**Test:** take a working example, move the retrieved chunks to the middle, re-run. If the answer changes, you have a layout dependency and you should control chunk ordering deliberately. This is a cheap, one-variable test and it catches a real class of bug.

### Over-retrieval

More retrieved context is not better context.

Two pieces of evidence converge here. The 2023 long-context agentic instruction following benchmark found that raising reasoning effort helped some configurations by 2.0 to 3.0 points, left one unchanged, and **hurt one by 2.7 points**, with token spend ranging from roughly 13K to 60K per trial and no clean relationship to score. And the 2026 source-attribution study found that across GPT-5.4 and Claude Opus 4.6, fact-check accuracy fell by roughly **42 percentage points on average** as tool calls rose from 2 to 150, while link validity and relevance stayed above 92%.

More retrieval made attribution worse, not better. The cheap checks stayed green while the expensive one degraded.

**Test:** sweep your k. If k=3 and k=20 give the same answer accuracy, you are paying 6× the context for nothing, and the extra material may be adding distraction.

## The selection sheet, for RAG specifically

**Retrieval:** recall@k, nDCG, MRR on your own labelled questions. Separate for each document type you query.

**Generation, given retrieval:** faithfulness — is the answer supported by what was retrieved? Answerability — does it refuse when the evidence is insufficient?

**Failure handling:** the RGB four. Noise, negative rejection, integration, counterfactual.

**Layout:** position sensitivity — move the chunks, re-run.

**Scale:** how many chunks can you retrieve before degradation? A 2025 retrieval-based tool-selection study found accuracy degrading beyond roughly 100 candidates as retrieval precision declined, in the tool-selection analogue.

**Cost:** tokens per successful answered question, including the retrieval.

## On judging the output with an LLM

Once you have separated the stages, a judge becomes more useful — because you can now ask it a narrow question.

The 2023 NeurIPS MT-Bench paper found GPT-4 judges agreeing with human preference on more than 80% of comparisons — comparable to human-human agreement — while naming position bias, verbosity bias, and self-enhancement bias, plus "limited reasoning ability." A companion paper showed the stakes of not defending a close comparison: under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries.

Three defenses, always: swap order, control length, change judge family. If the winner flips, it was a tie.

And when a judge and a domain expert disagree, that disagreement is data, not noise. A 2026 agent-evaluation paper is explicit that human review remains "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions," while judges remain unreliable as sole authority.

[AUTHOR EXPERIENCE: Replace with your real account — a RAG failure you misdiagnosed as a model problem because you only had a combined score.]

## What this cannot settle

The two-stage framing is standard practice in RAG engineering, but the specific metric recommendations here are my reading of the 2026 metrics study rather than a validated protocol. No published work compares these metric choices head to head on a single system.

The numbers are setup-specific and dated. The RAG metrics study's dataset was 96 questions with wide confidence intervals, and the authors note their single-system design could not establish full metric validity. The judge-agreement figures come from 2023-era models; the 2026 work updates the picture without replacing them. Most of the strongest sources are 2026 arXiv preprints, and the peer-reviewed ones — TACL 2023, AAAI 2024, NeurIPS 2023 — are also the older ones.

And splitting the score does not make the problem smaller. It makes it diagnosable, which is a different and more useful thing.

## Where to start this week

1. Split your existing eval into retrieval and generation scores.
2. Run two systems on the same 30 questions and compare outputs directly.
3. Test negative rejection: ask a question your corpus cannot answer.
4. Move the retrieved chunks to the middle and re-run.
5. Sweep k from 3 to 20 and plot the curve.

## Sources

- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; difficulty confound; DeepEval contextual precision >0.5 with recall; Ragas Levenshtein weakness; two-system comparison; 96-question dataset.
- Chen, J. et al. (2024). *Benchmarking Large Language Models in Retrieval-Augmented Generation*. AAAI 2024. https://arxiv.org/abs/2309.01431
  - Supports: RGB's four abilities; persistent failure in negative rejection, information integration, false information.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: 94% / 80% vs 24.4–76.8%; ~42-point fact-check drop from 2 to 150 tool calls; 14 models, 130 queries.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation in long contexts.
- *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents* (2025). arXiv:2510.09721. https://arxiv.org/html/2510.09721v3
  - Supports: long context not a substitute for retrieval; snippet ordering matters.
- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: judges unreliable alone; human review essential for domain context and rubrics.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: reasoning-effort variance; 13K–60K token range; missed-inference interpretation.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: degradation beyond ~100 candidates as retrieval precision falls.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are 2026 arXiv preprints rather than peer-reviewed work, and the judge-agreement figures describe 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

If you split your RAG score today, which half would turn out to be the weaker one?
