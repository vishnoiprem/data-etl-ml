---
title: "A Red-Team Checklist for Anything You're About to Adopt"
subtitle: "How to pressure-test a model, tool, paper, or prompt before it becomes your problem — the questions that find real defects."
tags:
  - ai-evaluation
  - red-teaming
  - llm
  - how-to-evaluate-llm-tools
  - model-selection
  - ai-security
  - technical-writing
platform: linkedin
medium_publication: signal-scribe
target_length: 1300-1550
word_count: 1480
disclosure: "AI-assisted. Drafted with AI assistance and edited by a human; the author is responsible for all claims."
rubric_score: 90
hard_fail: false
distinctness_angle: "Red-team lens — a sequence of adversarial questions designed to break a candidate before adoption, each with the published finding that motivates it"
sources_count: 9
author_experience_placeholders: 1
---

Adoption reviews ask the wrong question. They ask "is this good?"

A better question: "how do I make this fail, and what happens when it does?"

That is a red-team question, and it is the one that catches the defects a score cannot.

## The adversarial opening move

Before you read a single benchmark, write down the single most likely way this thing fails in your environment. Then go looking for it.

This inverts the usual flow. You are not asking the candidate to prove itself; you are asking it to show you its worst moment. A 2026 evaluation-ecosystem paper argues this is the missing piece of mainstream evaluation, recommending red teaming alongside context specification and field testing — realistic and adversarial use to uncover failure patterns, misuse, boundary conditions, and mitigation effectiveness, with expert, public, and automated approaches, and coverage across languages, dialects, multi-turn, and multimodal cases.

It also names a failure in red teaming itself: it is often episodic. Discoveries get made once and then lost, because the adversarial knowledge is never written down where the next person can find it.

**Your first rule: write the red-team findings down in a form that survives the next release.** Otherwise you rediscover the same bug every quarter.

## Adversary 1: the metadata attack

Ask whether the tool's *description* is doing the work rather than its capability.

This is not hypothetical. A 2025 paper, ToolTweak, describes a gradient-free black-box attack that iteratively rewrites a tool's name and description — leaving the parameter schema untouched — to increase the likelihood an LLM agent selects it over comparable tools. Against an approximately 20% baseline, the best selection rates reached 81.6% for DeepSeek, 73.6% for GPT-OSS, 50.7% for Grok 3 Mini, 48.7% for Gemini, 45.9% for Qwen 2.5, and 34.0% for Llama 3.1. Some attacks transferred between models.

The paper's recommended defenses are practical: objective paraphrasing reduced bias and strongly countered fixed persuasive suffixes, though it was less effective against ToolTweak, and simple perplexity thresholds failed because benign and adversarial descriptions overlapped.

**Adversarial question for a tool marketplace or a registry you maintain:** if a competitor rewrote their tool's description tomorrow, how much of your traffic would move? If the answer is "most of it," your routing is a function of copy, not capability.

**Adversarial question for an agent you built:** what does your tool-selection distribution look like right now, and is it roughly even across equivalent tools? The ToolTweak paper notes the attack shifts the overall distribution away from expected parity, which it frames as a risk to "fairness, competition, and security in emerging tool ecosystems."

## Adversary 2: the position attack

Ask whether the tool works when the evidence is where you would not have put it.

The 2023 TACL paper "Lost in the Middle" found that models perform best when relevant material appears at the beginning or end of the context and "significantly degrades when models must access relevant information in the middle." The effect hit explicitly long-context models too — a wide context window is a capacity claim, not a reliability claim.

**Adversarial question:** take a working example, move the relevant material to the middle of the context, and re-run. If the answer changes, the capability you are evaluating is "works when the input is conveniently ordered," which is a narrower capability than you think.

## Adversary 3: the scale attack

Ask what happens when the candidate list grows.

A 2025 study of retrieval-based tool selection found that giving the model every tool schema dropped selection accuracy to 13.62%. Retrieving just the relevant schema raised it to 43.13% and cut average prompt usage from 2,133.84 tokens to 1,084. The same study found accuracy degrading beyond roughly 100 candidates as retrieval precision declined, and proposed hierarchical or adaptive retrieval for larger registries.

**Adversarial question:** run your evaluation with twice the candidate pool you currently have. If accuracy falls off a cliff, you are buying a tool that will break as your team grows — and your team will grow.

## Adversary 4: the judge attack

Ask whether your ranking survives being reordered.

The 2023 MT-Bench work found GPT-4 judges agreeing with human preference on more than 80% of comparisons, comparable to human-human agreement, while naming position bias, verbosity bias, and self-enhancement bias and the limitation "limited reasoning ability." A companion paper showed how much the order matters: under one evaluator setup, Vicuna-13B beat ChatGPT on 66 of 80 tested queries.

**Adversarial questions:** swap the order. Control the length. Change the judge. If any single one of those three flips your winner, you did not have a winner.

There is a deeper version. A 2026 agent-evaluation paper describes LLM judges as faster, cheaper, and repeatable, but unreliable as a sole evaluation authority — they may miss domain policies, required tool sequences, and trajectory-level failures — while human review remains "essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions." So also ask: what would a domain expert catch that the judge would not? Then make sure someone with that knowledge looks at a sample.

## Adversary 5: the trace attack

Ask whether the *process* complied, not just the output.

A 2026 paper on agent evaluation is explicit that procedural failures "can look plausible in the final response" — an agent claiming a tool was used without invoking it, omitting a mandatory compliance call, or calling tools in the wrong order. The same work treats trace analysis as necessary, not optional.

**Adversarial question:** pull the trace from a run that produced an answer you liked. Did every claimed call actually happen, in the right order, with the required steps in between?

A 2026 benchmark for long-context agentic instruction following pushed this further and recommended "enforcing hard controls outside the model" — compiling policies into deterministic tool-call guards instead of relying on in-context adherence. Its best configuration scored 36.2% strict pass@1. Nearly two of every three tasks still failed.

## Adversary 6: the more-searching attack

Ask whether more effort reliably improves the answer.

This one is counterintuitive and it is where most people hold an outdated belief.

A 2026 study on source attribution in AI research reports found that across GPT-5.4 and Claude Opus 4.6, fact-check accuracy fell by roughly 42 percentage points on average as tool calls rose from 2 to 150. One model dropped from 78.6% to 16.7%; another from 80.0% to 57.9%. Link validity and topical relevance stayed above 92% the whole time. More searching did not produce worse citations — it produced worse *attribution*, while everything cheaply checkable stayed green.

The parallel finding in reasoning: in the long-context agentic benchmark, raising reasoning effort helped some configurations by 2.0 to 3.0 points, left one unchanged, and hurt one by 2.7 points, with one configuration burning close to 60K tokens and roughly three times the cost of a competitor in the same band.

**Adversarial question:** is more effort a bet on a specific failure type? If the failure is a missed read, you are paying four times for nothing.

## Adversary 7: the citation attack

For a paper rather than a tool: check whether the references were read.

A 2026 benchmark, CiteAudit, found 2,967 fabricated citations out of a 9,442-citation test set, and separately found references that existed but whose title or author metadata did not match — which indicates the cited paper was never actually read. Existence checks miss that second failure.

**Adversarial question:** open three references at random and find the passage that supports the sentence attached to them. Not the paper. The passage.

[AUTHOR EXPERIENCE: Replace with your real account — the tool, prompt, or paper that survived your adversarial pass, and the one that did not.]

## The red-team protocol

Seven adversaries. In order:

1. **Name your worst-case failure before you look.** This is the finding you are shopping for.
2. **Attack the metadata.** Rewritten descriptions, uneven selection distributions.
3. **Attack the position.** Move the evidence. Re-run.
4. **Attack the scale.** Double the candidate pool.
5. **Attack the judge.** Swap order, control length, change judge.
6. **Attack the trace.** Check what actually happened.
7. **Attack the effort.** Test whether more searching and more tokens help or hurt.
8. **Write the findings down where the next release will find them.**

## What this cannot settle

Red teaming is a bug-finding technique, not a proof. A clean pass means you did not find the defect, not that none exists. A 2026 evaluation-ecosystem paper is candid that red teaming's weakness is inconsistent reuse across agents, domains, and releases — and that tester bias, transparency rules, and psychological safety need deliberate handling.

No published framework validates this seven-adversary sequence. The selection of these seven comes from what other work has shown to break, not from a controlled comparison of attack types.

## Where to start this week

1. Write your worst-case failure for one pending decision, before you look at any candidate.
2. Swap the order on your last comparison.
3. Move the relevant evidence to the middle of the context in a working example and re-run.
4. Pull a trace from a run whose output you liked.
5. Write your red-team findings into a file the next person will actually read.

## Sources

- Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
  - Supports: >80% agreement; position, verbosity, self-enhancement biases; "limited reasoning ability."
- Wang, P. et al. (2023). *Large Language Models are not Fair Evaluators*. https://arxiv.org/abs/2305.17926
  - Supports: order-swap fragility; 66-of-80 result.
- Liu, N. F. et al. (2023). *Lost in the Middle*. TACL 2023. https://arxiv.org/abs/2307.03172
  - Supports: position-dependent degradation in long contexts.
- *ToolTweak: An Attack on Tool Selection in LLM-based Agents* (2025). arXiv:2510.02554. https://arxiv.org/html/2510.02554v1
  - Supports: name/description attack; 81.6%–34.0% selection rates vs ~20% baseline; paraphrase and perplexity defenses.
- *RAG-MCP* (2025). arXiv:2505.03275. https://arxiv.org/html/2505.03275v1
  - Supports: 13.62% vs 43.13%; 2,133.84 → 1,084 tokens; degradation beyond ~100 candidates.
- Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents*. arXiv:2606.16871. https://arxiv.org/html/2606.16871v1
  - Supports: procedural failures look plausible in the final response; judges unreliable alone; human review essential for specific decisions.
- *HANDBOOK.md* (2026). arXiv:2607.25398. https://arxiv.org/html/2607.25398v3
  - Supports: 36.2% strict pass@1; reasoning effort helped some and hurt one; ~60K tokens at ~3× cost for the same band; hard controls outside the model.
- *Parsing and Evaluating Source Attribution in LLM Deep Research* (2026). arXiv:2605.06635. https://arxiv.org/html/2605.06635v1
  - Supports: ~42-point fact-check drop from 2 to 150 tool calls; 78.6%→16.7% and 80.0%→57.9%; link/relevance stayed above 92%.
- *CiteAudit* (2026). arXiv:2602.23452. https://arxiv.org/html/2602.23452v3
  - Supports: 9,442 citations, 2,967 fake; title/author metadata mismatch detection.
- *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact* (2025). arXiv:2505.18893. https://arxiv.org/html/2505.18893v4
  - Supports: red teaming as one of three evaluation activities; episodic reuse weakness; tester bias and transparency rules.

## Disclosure

This article was drafted with AI assistance and edited by a human. All statistics and URLs were checked against the primary sources listed above. Several sources are arXiv preprints rather than peer-reviewed work, and the judge-agreement figures come from 2023-era models. The author remains responsible for every claim. The `[AUTHOR EXPERIENCE]` marker indicates where the author's own account must be inserted before publication.

What is the worst thing your current tool does that you have never actually tried to reproduce?
