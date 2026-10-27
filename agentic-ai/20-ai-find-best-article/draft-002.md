---
title: "Stop Choosing the Best AI Tool. Start Choosing the Failure You Can Live With"
subtitle: "A failure-mode taxonomy for picking models, tools, and papers — plus why every evaluation framework is a taxonomy in disguise."
tags:
  - ai-evaluation
  - failure-modes
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - rag
  - agentic-ai
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1600
word_count: 1500
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 89
hard_fail: false
distinctness_angle: "Failure-mode taxonomy as the organizing device — candidates classified by how they fail, not how they score; taxonomy of five failure families"
sources_count: 9
author_experience_placeholders: 1
---

Two tools can post identical benchmark scores and be completely different purchases.

One fails loudly, in the same way every time, and you can write a rule for it. The other fails quietly, differently each run, in a way nobody notices until it costs you a quarter.

Pick the first one. Almost nobody does, because the leaderboard only tells you what a tool does right.

## The taxonomy nobody publishes

Every evaluation framework you have read is a taxonomy of failure modes in disguise. The moment you know which failures matter, you know which tool to buy.

Here are five failure families, and the reason each one is dangerous.

### Family 1: Silent degradation

The tool produces plausible output that is subtly wrong, and nothing in the interface tells you.

This is the family that produces the most expensive incidents, because detection is not automatic. A 2026 study on source attribution in AI research reports separated three checks — link works, content on topic, source supports the claim — and found link validity above 94% while factual accuracy ranged from 24.4% to 76.8%. A researcher can follow a working, on-topic link and still be wrong.

The rule: **if a failure leaves no trace, you must build the trace.** Record the intermediate state, not just the answer.

### Family 2: Statistical fragility

The result is real, but it is real by a small margin, and the margin disappears under conditions you did not test.

A 2026 comparison of RAG evaluation metrics found human evaluators agreed with each other at a Pearson correlation of 0.85 — effectively the ceiling for any proxy metric. RAGChecker's recall-oriented metrics correlated best, with claim recall near 0.7. But the study's sharpest finding is that high correlation does not establish validity, because a metric can track human scores for reasons that have nothing to do with what it measures. Question difficulty alone can produce a strong correlation.

The 2023 MT-Bench work found the same class of fragility in judging itself. GPT-4 as a judge hit "over 80% agreement" with human preference — comparable to human-human agreement — while the paper names position bias, verbosity bias, and self-enhancement bias. A companion paper showed how fragile order-dependent comparisons are: under one setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries. The comparison did not get more reliable because the gap was large. It got less reliable.

The rule: **when two candidates land close, the measurement is not good enough to separate them.** Stop measuring, start running both.

### Family 3: Context position sensitivity

The tool handles your data when it is laid out the way it expects, and fails when it is not.

The "Lost in the Middle" paper, published in TACL in 2023, is unambiguous: models perform best when relevant material sits at the beginning or end of the context, and "significantly degrades when models must access relevant information in the middle." Critically, this affected explicitly long-context models too. A large context window is a capacity claim, not a reliability claim.

The rule: **reposition the evidence and re-test.** If the answer changes when you move the source material, you have a layout dependency, and you should pin that layout down before you ship.

### Family 4: Procedure violation

The output is fine. The process that produced it was not allowed.

A 2026 paper on agent evaluation is blunt about this. Procedural failures "can look plausible in the final response" — an agent claims it used a tool it never invoked, skips a mandatory compliance call, or calls tools in the wrong order, and the text reads perfectly.

A 2026 benchmark for long-context agentic instruction following made the same point from the other direction, recommending that teams enforce "hard controls outside the model," compiling policies into deterministic tool-call guards rather than trusting in-context adherence. Its best configuration scored 36.2% strict pass@1, which means the best system still failed nearly two of every three tasks.

The rule: **read the trace, not the answer.** If the failure mode is "did the forbidden thing," the answer is the wrong place to look.

### Family 5: Scale collapse

The tool works fine on your current volume and quietly stops working as you grow.

A 2025 study on retrieval-based tool selection found that presenting every tool schema to the model dropped selection accuracy to 13.62%. Retrieving just the relevant schema raised it to 43.13%, and cut average prompt usage from 2,133.84 tokens to 1,084. But the same study found performance degraded beyond roughly 100 candidates as retrieval precision fell — the authors proposed hierarchical retrieval for larger registries.

The rule: **test at the size you will operate at, not the size you operate at today.** A tool registry of 20 and a registry of 200 are different products.

## Choosing by failure family, not by score

Here is how this becomes a selection method.

**Step one: name the failure family you cannot afford.** Not "we need accuracy." Name it specifically. "A wrong answer that gets emailed to a customer without review." "A compliance call that gets skipped." "A slow tool that blows our cost ceiling." That sentence determines everything after it.

**Step two: exclude on family, not on score.** Some failures are disqualifying regardless of aggregate performance. A tool that cannot be traced, or cannot have a hard control enforced around it, is out — however good its benchmark numbers are. This is the lesson from the agent-evaluation work, where human review is described as "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions," while judges remain unreliable as a sole authority.

**Step three: among survivors, break ties on the family you *can* afford.** A silent-degradation failure you can catch with a deterministic post-check is cheaper than a procedural failure you cannot. Once you have excluded on the unacceptable family, the remaining differences are often smaller than the noise in your measurement anyway.

## Where this bites hardest: reading papers

The taxonomy applies to reading a paper, but the "silent degradation" family is the one to watch.

A 2026 benchmark called CiteAudit separates two failure modes that look identical in a bibliography. The reference may not exist at all — across their 9,442-citation test set, 2,967 were fabricated. Or the reference exists, but the title and author metadata do not match, which suggests the paper was never actually read.

The second failure is the dangerous one because it survives a link check. A second 2026 study on citation faithfulness made the same separation: link validity above 94%, relevance above 80%, factual accuracy from 24.4% to 76.8%. The links work. The pages are on topic. The claims still do not hold.

A 2026 evaluation-ecosystem paper pushes the same logic further, arguing that leaderboard reliance encourages overfitting and benchmark saturation, and that contamination and data leakage can inflate results.

The rule for papers: **check the claim against the retrieved content, not the metadata.** Pull the passage. If you cannot find the support in the source, the sentence does not belong in your article.

[AUTHOR EXPERIENCE: Replace with your real account — a tool or paper you adopted because it looked clean, and the specific failure family it turned out to belong to.]

## What this cannot settle

No published framework validates this taxonomy. It is a synthesis of other people's findings, and the specific boundaries between families are my judgment, not a measured result.

Every number attached to a family is setup-specific. 43.13%, 36.2%, 24.4%, 58% — none are constants. The judge-agreement figures come from 2023-era models. Several of the strongest sources are 2026 arXiv preprints, not peer-reviewed papers, and the ones that are peer-reviewed — TACL for the long-context work, NeurIPS for the judge work — are also the older ones.

The taxonomy will not tell you which model to buy. It tells you which questions to ask, and it tells you which candidate to reject outright.

## Where to start this week

1. Write down the one failure you cannot absorb, in one sentence, naming the consequence.
2. Take your last two candidates and ask which failure family each one belongs to.
3. Run the same ten questions through both candidates with the input order swapped.
4. Open one tool-call trace from a recent agent run and count the calls that should have happened and did not.
5. Pull three citations from your last post and find the passage in each source that supports the claim.

## Sources

- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% judge-human agreement; position, verbosity, self-enhancement biases.
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-dependent rankings; 66-of-80 result.
- Liu, N. F. et al. (2023). *Lost in the Middle: How Language Models Use Long Contexts*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation, including in long-context models.
- *Evaluating RAG Metrics in Applied Contexts* (2026). arXiv:2607.07302. https://arxiv.org/html/2607.07302v1
  - Supports: 0.85 human-human correlation; RAGChecker recall near 0.7; correlation does not establish validity.
- *RAG-MCP: Mitigating Prompt Bloat in LLM Tool Selection via Retrieval* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: 13.62% vs 43.13% selection accuracy; 2,133.84 → 1,084 tokens; degradation beyond ~100 candidates.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; judges unreliable alone; human review essential for specific decisions.
- *HANDBOOK.md: A Benchmark for Long-Context Agentic Instruction Following* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; enforce hard controls outside the model.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: link works / relevant content / fact check separation; 94% vs 24.4–76.8%; >92% retained under deeper search.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; title and author metadata mismatch detection.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: leaderboard overfitting, saturation, contamination inflating results.

## Disclosure

This article was drafted with AI assistance and edited by a human. Statistics and URLs were checked against the primary sources listed above; several sources are 2026 arXiv preprints rather than peer-reviewed work, and the author has marked them as such. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

Which of the five failure families has cost you the most — and did you notice it at the time?
