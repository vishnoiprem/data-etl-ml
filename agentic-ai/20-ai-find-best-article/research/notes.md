# Research Notes — Evaluating and Selecting the "Best" Tool, Paper, Model, or Prompt

Access date for all sources: **2026-10-26**

Every entry records: the URL, what the source actually says (in the source's own terms where quoted), and what it can and cannot support in an article. Anything I could not open or verify is marked `[UNVERIFIED]`.

---

## R1 — LLM-as-a-judge: how well it works and where it breaks

**Source:** Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" — https://arxiv.org/abs/2306.05685
**Accessed:** 2026-10-26 (arXiv abstract page)

**What it supports:**
- A strong judge (GPT-4) reached "over 80% agreement" with both controlled and crowdsourced human preferences, described as comparable to agreement between humans.
- Named biases: position/order bias, verbosity bias, self-enhancement bias (judge favors its own outputs or its own model family).
- Stated limitation: "limited reasoning ability."
- Resources: MT-bench with "3K expert votes" and "30K conversations with human preferences."

**What it does NOT support:** It does not claim judges are reliable as a sole authority. It does not claim agreement is higher than human-human agreement. It does not give per-task agreement rates for any specific model family beyond GPT-4.

**Use in article:** the strongest single number for "an LLM judge is decent, not infallible," plus the three named biases as concrete failure modes to design around (swap order, control length, use a different judge).

---

## R2 — Evaluator order bias, quantified

**Source:** Wang et al., "Large Language Models are not Fair Evaluators" — https://arxiv.org/abs/2305.17926
**Accessed:** 2026-10-26

**What it supports:**
- Changing the order in which two candidate answers are presented changes the ranking they receive.
- Concrete example from the paper: "Vicuna-13B could beat ChatGPT on 66 over 80 tested queries" under a particular evaluator setup.
- A calibration framework with three parts: multiple-evidence calibration, balanced-position calibration, human-in-the-loop calibration.
- "Balanced position diversity entropy" is used as a difficulty signal that triggers human assistance.

**What it does NOT support:** This paper is *not* about benchmark data contamination. Any draft must not attribute contamination findings to this source.

**Use in article:** the "swap the order" fix for judge bias, and the escape hatch: when answers are close and order-sensitive, escalate to a human.

---

## R3 — Long context is not reliable context

**Source:** Liu et al., "Lost in the Middle: How Language Models Use Long Contexts" — https://arxiv.org/abs/2307.03172
**Accessed:** 2026-10-26 (TACL 2023)

**What it supports:**
- Evaluated multi-document QA and key-value retrieval.
- "Performance can degrade significantly when changing the position of relevant information."
- Models perform best when relevant material is at the beginning or end, and "significantly degrades when models must access relevant information in the middle."
- The weakness affected explicitly long-context models too — a large context window does not guarantee use of all positions.

**What it does NOT support:** Nothing about benchmark saturation, statistical rigor, or human evaluation. Do not attribute those to this source.

**Use in article:** the "position the evidence where you need it" rule; the reason a big context window is not a quality argument.

---

## R4 — RAG does not rescue a weak model, and retrieval is only half the problem

**Source:** Chen et al., "Benchmarking Large Language Models in Retrieval-Augmented Generation" — https://arxiv.org/abs/2309.01431
**Accessed:** 2026-10-26 (AAAI 2024)

**What it supports:**
- The RGB benchmark organizes RAG evaluation into four abilities: "noise robustness, negative rejection, information integration, and counterfactual robustness."
- Finding: "they still struggle significantly in terms of negative rejection, information integration, and dealing with false information."
- Conclusion: "there is still a considerable journey ahead to effectively apply RAG to LLMs."

**What it does NOT support:** The abstract does not report nDCG, recall@k, MRR, or a general claim that "RAG quality is limited by retrieval quality." Do not put that claim on this source. (For retrieval-metric specifics, use R5.)

**Use in article:** the point that bolting retrieval onto a model does not make it reliable; you must test the *combination* on *your* data.

---

## R5 — RAG metrics disagree with each other and with humans

**Source:** "Evaluating RAG Metrics in Applied Contexts: An Experiment, Its Lessons, and the Path Forward" — https://arxiv.org/html/2607.07302v1
**Accessed:** 2026-10-26

**What it supports:**
- Compared metrics from Ragas, DeepEval, RAGChecker, Opik, plus BLEU, METEOR, ROUGE, BERTScore F1, and word-level recall.
- Two human evaluators' ratings had a **Pearson correlation of 0.85** with each other and served as the reference.
- RAGChecker produced the strongest overall-metric correlations, particularly recall-oriented metrics; RAGChecker claim recall was **near 0.7**.
- METEOR correlated relatively well with human scores despite being sometimes described as obsolete.
- Hallucination/faithfulness metrics correlated **weakly** as overall metrics, partly attributed to lack of access to reference answers.
- Opik moderation did not correlate with the reference scores.
- DeepEval contextual precision correlated **above 0.5** with recall despite not using reference spans.
- Ragas's non-LLM retrieval metrics correlated weakly with recall; proposed explanation is reliance on Levenshtein distance, which breaks when retrieved and reference spans differ greatly in length.
- Methodological caution: high correlation alone does not establish validity, because input difficulty and other confounders can produce strong correlations. A single-system design cannot establish full metric validity; the authors recommend evaluating **at least two RAG systems**.
- Dataset size: **96 questions**, so confidence intervals were relatively wide.

**What it does NOT support:** It does not establish that RAGChecker is "the best metric." It explicitly warns against that inference. It does not license claims about metrics on systems other than the one studied.

**Use in article:** the strongest support for "don't trust a single score," the "at least two systems, compare outputs" technique, and the meta-lesson that a metric can correlate with human ratings for reasons that have nothing to do with what it claims to measure.

---

## R6 — Tool selection is a retrieval problem, and it breaks down at scale

**Source:** "RAG-MCP: Mitigating Prompt Bloat in LLM Tool Selection via Retrieval" — https://arxiv.org/html/2505.03275v1
**Accessed:** 2026-10-26 (dated May 6, 2025)

**What it supports:**
- Method: retrieve the most relevant MCP server from a semantic index before invoking the LLM, instead of presenting every tool schema.
- Tool-selection accuracy rose to **43.13%**, versus **18.20%** for keyword matching and **13.62%** for an all-tools prompt.
- Average prompt usage fell to **1,084 tokens**, versus **1,646** for keyword filtering and **2,133.84** when all tools were included — roughly a 49% reduction versus the latter.
- Completion tokens: 78.14 (RAG-MCP) vs 23.60 (keyword filtering) vs 162.25 (all tools).
- **Scaling limit:** performance degraded beyond roughly **100 candidates** as retrieval precision declined; the authors propose hierarchical or adaptive retrieval for larger registries.

**What it does NOT support:** It does not establish 43% as a general accuracy figure for tool selection; it is specific to their setup and tool pool. It does not support claims about MCP specifically in the abstract sense.

**Use in article:** the "how many tools is too many" number (~100) is concrete and citable. The 13.62% vs 43.13% contrast shows that a naive "paste all the schemas" approach is a real failure mode.

---

## R7 — Tool descriptions steer routing, and can be weaponized

**Source:** "ToolTweak: An Attack on Tool Selection in LLM-based Agents" — https://arxiv.org/html/2510.02554v1
**Accessed:** 2026-10-26 (dated Oct 2, 2025)

**What it supports:**
- A gradient-free, black-box attack that iteratively rewrites a tool's **name and description** (schema unchanged) to increase the likelihood the agent selects it over comparable tools.
- Against an approximately 20% baseline, best selection rates rose to **81.6% (DeepSeek), 73.6% (GPT-OSS), 50.7% (Grok 3 Mini), 48.7% (Gemini), 45.9% (Qwen 2.5), 34.0% (Llama 3.1)**.
- Some attacks transferred between models; the target model's architecture was the dominant factor.
- The attack shifts the overall selection distribution away from expected parity, raising risks to "fairness, competition, and security in emerging tool ecosystems."
- Defenses: objective paraphrasing reduced bias and strongly countered fixed persuasive suffixes, but was less effective against ToolTweak. Simple perplexity thresholds failed because benign and adversarial descriptions overlapped; combining length and perplexity appeared more promising.

**What it does NOT support:** It does not prove that any specific marketplace is currently compromised. It does not establish a general rate of malicious descriptions in the wild.

**Use in article:** the argument for metadata hygiene when you pick a tool, and the reason "the agent chose it" is not evidence of "it's the best one." Also the best source for a *counterargument* section: routing outcomes reflect descriptions, not just capability.

---

## R8 — Static benchmarks miss how agents actually fail

**Source:** Bousetouane, "Human-on-the-Bridge: Scalable Evaluation for AI Agents" — https://arxiv.org/html/2606.16871v1
**Accessed:** 2026-10-26 (dated Jun 15, 2026)

**What it supports:**
- Static benchmarks are useful for standardized comparison but do not adequately test multi-turn tool use, policy adherence, recovery, or procedural consistency.
- A model can do well on a fixed benchmark yet fail operationally through "missing tool calls, hallucinated tool use, policy drift, unsafe reframing, manipulation paths, or over-refusal."
- Interactive/trajectory benchmarks are closer to real agent behavior but don't fully specify how experts curate adversarial risks or connect evidence to repeatable scoring.
- Human-in-the-loop review preserves expert judgment — especially in healthcare, finance, privacy, legal, security — but is costly, slow, and hard to reproduce when every trajectory needs manual review. Human review "remains essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions."
- LLM-as-judge: faster, cheaper, repeatable, but unreliable as sole evaluation authority; limitations include "position bias, verbosity bias, self-enhancement bias, and judge reasoning limitations." Judges may miss domain policies, required tool sequences, and trajectory-level failures.
- Red teaming is effective at finding unexpected vulnerabilities but often episodic, with inconsistent reuse across agents, domains, and releases.
- Trace analysis is necessary because "procedural failures can look plausible in the final response" — claiming a tool was used without invoking it, omitting mandatory compliance calls, calling tools in the wrong order.
- Scale of their own study: 47 configurations, 470 trials, 23,500 turns.
- **Self-caveat:** subjective juror scores are not calibrated to human experts, and the selected non-factorial design limits definitive cross-configuration rankings.

**Use in article:** the strongest support for "read the trace, not the answer," and the "encode the expert's rules upstream" idea. The self-caveat is itself good material for a limitations section.

---

## R9 — Metrics miss the capabilities people actually need

**Source:** Miller & Tang, "Evaluating LLM Metrics Through Real-World Capabilities" — https://arxiv.org/html/2505.08253v1
**Accessed:** 2026-10-26 (dated May 13, 2025)

**What it supports:**
- "A fundamental mismatch" between benchmarks and real-world use; benchmarks "often focus on narrow, isolated tasks that do not capture the full spectrum of how people interact with AI."
- Automated or reference-based metrics "can obscure ambiguous or context-sensitive errors," including hallucinations and stylistic mismatches.
- Of six practical capabilities identified, "Reviewing Work and Data Structuring are not captured at all" by the evaluated metrics.
- Criterion mismatch: metrics emphasize correctness while often overlooking clarity, relevance, efficiency, tool coverage, and user interpretability; benchmarks "often prioritize abstract notions of correctness over qualities that matter to users."
- Leaderboards may "overstate differences while obscuring common failure modes."
- Recommendations: smaller curated datasets, transparent annotation protocols, published prompts/rubrics/annotation standards, human raters for subjective judgments, objective reference answers paired with confidence intervals, multi-turn interactions.
- **Note:** the paper does *not* report a numerical correlation coefficient between general LLM metrics and human judgments — its argument is conceptual.

**What it does NOT support:** Any numeric correlation between metrics and human judgment. Do not invent one.

**Use in article:** "reviewing work" and "structuring data" being invisible to benchmarks is a strong, specific point about capability coverage gaps. The self-reported/selective-disclosure criticism supports "read the methodology, not the score."

---

## R10 — Truthfulness is not a scaling property

**Source:** Lin, Hilton & Evans, "TruthfulQA: Measuring How Models Mimic Human Falsehoods" — https://arxiv.org/abs/2109.07958
**Accessed:** 2026-10-26 (ACL 2022)

**What it supports:**
- 817 questions across 38 categories.
- The strongest tested model was truthful on **58%** of questions; human performance was **94%**.
- Larger models were generally *less* truthful, reversing the usual scale/performance relationship.
- Conclusion: "scaling up models alone is less promising" than other objectives.

**What it does NOT support:** It does not report benchmark saturation or contamination percentages. It does not say anything about 2026 models — the result is from 2021-2022 and the models tested then are far weaker than current ones. Use it as a *structural* point (capability and truthfulness are different axes), not as a current-model claim.

**Use in article:** the argument that "bigger" and "better" are different axes, so a single ranking hides tradeoffs. Must be dated explicitly in the body.

---

## R11 — Instruction tuning: task count and generalization

**Source:** Chung et al., "Scaling Instruction-Finetuned Language Models" — https://arxiv.org/abs/2210.11416
**Accessed:** 2026-10-26

**What it supports:**
- Instruction finetuning on instruction-phrased datasets improves performance and generalization to unseen tasks.
- Evaluated across zero-shot, few-shot, and CoT prompting, and across MMLU, BBH, TyDiQA, MGSM, and open-ended generation.
- Flan-PaLM 540B finetuned on 1.8K tasks outperformed PaLM 540B by "+9.4% on average" and reached "75.2% on five-shot MMLU."
- Public Flan-T5 checkpoints performed strongly in few-shot settings relative to larger models such as PaLM 62B.

**What it does NOT support:** The abstract does not contain the numbered "Finding 1" / "Finding 2" results, the model-by-prompt interaction detail, or any statement about which single prompt is best. I did not retrieve the full PDF text, so I cannot cite those findings. `[UNVERIFIED]` if needed.

**Use in article:** a smaller task-tuned model can beat a larger untuned one on a narrow task — useful for the "match the tool to the task" argument. Cite the specific numbers.

---

## R12 — A working agent: benchmark scores, cost, and reasoning effort don't move together

**Source:** "HANDBOOK.md: A Benchmark for Long-Context Agentic Instruction Following" — https://arxiv.org/html/2607.25398v3
**Accessed:** 2026-10-26

**What it supports:**
- Evaluations "measure reading." The authors argue a long document in an agentic setting must keep details "operative dozens of tool calls after they were read."
- Strict vs relaxed grading: a relaxed "pass@1 (N−1)" metric tolerates one failed criterion and roughly doubles leader scores. The authors caution that "a deployment tolerating one violated control per workflow has effectively abandoned strictness."
- **Reasoning effort is not monotonically better:** raising effort helped Opus 4.8 (+3.0 points), Sonnet 4.6 (+2.7), and Fable 5 (+2.0), left GPT-5.5 unchanged, and hurt GLM 5.2 (−2.7). Interpretation given: additional deliberation converts into compliance only when the underlying error was a "missed inference rather than a missed read."
- **Token spend does not buy compliance:** GPT-5.5 reached 21.5% on roughly 13K generated tokens per trial; Opus 4.8 (max) spent close to 60K tokens and about three times the dollar cost for the same band. Several mid-pack configurations generated 45–55K tokens yet scored in single digits. GLM 5.2 was cited at 12.7% for well under a dollar per trial.
- Best configuration scored **36.2%** strict pass@1 — "still failed nearly two of every three tasks."
- Recommendation: "enforcing hard controls outside the model," e.g. compiling policies into deterministic tool-call guards, rather than relying on in-context adherence.

**Caveat:** this is a single benchmark with a specific, difficult task (long-horizon instruction following with strict control checks). The percentages are not general model rankings.

**Use in article:** cost-vs-score data and the "reasoning effort can make it worse" result are both strong. The 36.2% figure is a good humility anchor: even the best config on a hard agentic task fails most of the time.

---

## R13 — How to pick a model for software work (survey)

**Source:** "A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents" — https://arxiv.org/html/2510.09721v3
**Accessed:** 2026-10-26 (dated Oct 23, 2025)

**What it supports:**
- Benchmarks moved from small function-generation tasks (HumanEval, MBPP) to real GitHub issues, pull requests, cross-file dependencies, and actual test environments (SWE-bench, DevEval, RepoCOD, R2E-Eval, SWE-smith, SWE-rebench).
- Strongest design combines a real repository, an issue spec, environment setup, cross-file dependencies, and tests that decide whether the patch works.
- **SWE-bench is not fully reliable:** a cited analysis found many issues counted as solved were actually resolved incorrectly, motivating stronger validation in agent refinement loops. Passing benchmark tests should not automatically be equated with production-quality repair.
- Evaluation broadened to maintainability, efficiency, security, test generation, refactoring, environment setup, collaboration; some use formal verification (Lean type checking, proof generation, verifier-guided refinement).
- Contamination: DyCodeEval was created to evaluate models under different contamination levels; a benchmark drawn from public repositories may already have appeared in pretraining or fine-tuning data, so "unfamiliarity cannot safely be assumed."
- Practical model selection by task complexity: ordinary instruction-tuned LLMs for straightforward generation/explanation/small edits; structured or long-context models when repository relationships and ordered context matter; supervised fine-tuning when behavior must consistently follow domain-specific workflows or patch formats; preference alignment/RL when the objective is hard to express through demonstrations (security, efficiency, correctness under executable feedback).
- Tool choice is determined by needed feedback: repository navigation, AST/dependency graphs, search, editors, terminals, compilers, test runners, static analyzers, Docker, debuggers, language servers, formal verifiers, simulators, multimodal input. "Long context alone is not a substitute for effective retrieval": concatenating all relevant files was suboptimal and snippet ordering materially affected performance.
- Agent capability groups: planning/decomposition, reasoning/self-refinement, memory, tool use. Effective systems combine role specialization, repository exploration, iterative execution, validation, recovery.
- **The bottom line for our article:** "Benchmark scores should guide—rather than determine—tool choice." Compare candidates on the target repository, language, context length, test strength, contamination exposure, latency, and cost. For security-sensitive or maintenance-critical work, add verifiers or human review.

**Use in article:** the single most quotable practitioner framework for model selection by task type, and the strongest caution against leaderboard-driven decisions.

---

## R14 — Real-world evaluation is socio-technical, and leaderboards overfit

**Source:** "A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact" — https://arxiv.org/html/2505.18893v4
**Accessed:** 2026-10-26 (dated May 30, 2025)

**What it supports:**
- Moving beyond static, single-turn, in-silico benchmarks to what emerges when people use AI in context.
- Capturing first-order effects (outputs) and second-/third-order effects (behavior shifts, workforce changes, societal impact).
- Centering the "contextual unit" — adaptive behavior of people using AI in a setting — rather than the model.
- Benchmark challenges: static datasets poorly reflect deployment; benchmark metrics emphasize accuracy or policy violations, translating poorly to second-order questions; overreliance on leaderboards encourages overfitting and benchmark saturation; contamination and data leakage can inflate results; weak internal/external validity, narrow English-language focus, limited stakeholder involvement, and mathematical stand-ins for complex social phenomena create a "fallacy of objectivity"; benchmarks can lag agentic capabilities.
- Recommended approach — value-sensitive design across three activities:
  1. **Context specification:** define a theory of change with stakeholders (goals, inputs, outputs, outcomes, counterfactuals); operationalize concepts; involve affected groups proportionally to risk.
  2. **Field testing:** observe real users across repeated sessions under semi-controlled conditions; randomization and blinding plus surveys, logs, performance metrics, annotation of interactive outputs; naturalistic but safe scenarios.
  3. **Red teaming:** realistic and adversarial use to uncover failure patterns, misuse, boundary conditions, mitigation effectiveness; expert, public, and automated approaches; multilingual, dialectal, multi-turn, multimodal coverage; psychological safety protections; tester bias; transparency rules; track effectiveness over time.
- Ecosystem recommendations: shared testing hubs across academia, industry, civil society, government, public; organizations supply evaluation questions, individuals contribute context and participate, independent testers provide credibility, researchers formalize metrics; preserve qualitative work rather than treating it as secondary; automate valuable activities over time.

**Use in article:** the "contextual unit" idea and the argument that the unit of evaluation is the person-plus-system, not the model. Strong material for a "what to actually measure" section.

---

## R15 — A plausible reference list is not evidence you read the sources

**Source:** "CiteAudit: You Cited It, But Did You Read It? A Benchmark for Citation Faithfulness" — https://arxiv.org/html/2602.23452v3
**Accessed:** 2026-10-26 (dated May 1, 2026)

**What it supports:**
- Tests whether a citation corresponds to an actual publication and whether core metadata (title, authors, venue, year, identifiers) matches authoritative records.
- Detects fully fabricated references and subtler errors ("title mismatch," "author mismatch") that reveal the cited paper was not read accurately.
- Benchmark totals: **9,442 citations** (6,475 real, 2,967 fake). Generated test set: 3,586 real + 2,500 hallucinated. Real-world test set: 2,889 authentic + 467 naturally occurring errors. Generated hallucinations: 1,000 title, 1,000 author, 500 metadata.
- Framework: five roles (extraction, memory, web search, scholar retrieval, judgment); memory-match threshold 0.92.
- Multi-agent system achieved **0.966 accuracy / 0.959 F1** on generated data and **0.949 accuracy / 0.838 F1** on real-world data; F1 exceeded the next-best system by **0.267** on real-world citations.
- Field-level problems: baselines accepted them because the underlying paper existed.
- Commercial and open models showed a recurring trade-off: either missing fabricated references or falsely rejecting valid ones.
- GPTZero comparison: similar behavior on generated and real-world hallucinations (p = 0.994).
- **Caveat the authors state:** the benchmark's author-run annotation and potential indexing gaps mean independent replication and broader source coverage remain important.

**Use in article:** the strongest available support for "check the claim against the source, not just the link." The existence-check-vs-claim-support distinction is the point.

---

## R16 — Links that work and match the topic still don't support the claim

**Source:** "Parsing and Evaluating Source Attribution in LLM Deep Research" — https://arxiv.org/html/2605.06635v1
**Accessed:** 2026-10-26 (dated May 7, 2026)

**What it supports:**
- Pipeline: a Markdown AST parser extracts claim–citation pairs without relying on model inference; the content behind each cited URL is retrieved and extracted; each pair is scored on three dimensions — **Link Works** (URL accessible), **Relevant Content** (topically aligned with the claim), **Fact Check** (the source actually supports the specific factual assertions).
- Tested on **14 models** and **130 research queries**, using rubric-based LLM judges calibrated through human review.
- Results: link validity exceeded **94%**, relevance exceeded **80%**, while factual accuracy ranged from **39% to 77%**; the full model-level Fact Check range was **24.4% to 76.8%**.
- Open-source models struggled to produce properly cited reports: success **17%–40%**, versus **83%–100%** for frontier models.
- **Link and relevance stayed strong even when specific claims were unsupported** — a user may reach a working, on-topic page that does not substantiate the assertion.
- **More searching hurt factual synthesis:** across GPT-5.4 and Claude Opus 4.6, Fact Check fell by about **42 percentage points on average** as tool calls rose from 2 to 150. GPT-5.4 dropped from **78.6% to 16.7%**; Claude Opus 4.6 from **80.0% to 57.9%**. Link Works and Relevant Content stayed above 92% throughout.
- Model tendencies: OpenAI models generated more citations with lower factual accuracy; Anthropic models were generally less successful but more accurate; Claude Opus 4.5 led the model table with **76.8%** Fact Check.
- Common link failures: HTTP 404, blocked or paywalled pages, timeouts.
- Authors' cautions: LLM judges retain biases; web-based citations are temporally unstable.

**What it does NOT support:** These figures are for AI research-report generation specifically, not for human reading habits. Do not generalize "AI-written reports are 60% wrong" to a blanket claim.

**Use in article:** the "link works ≠ claim supported" distinction, and the counterintuitive "more research is not better" finding. The 42-point drop as tool calls go 2→150 is one of the best hooks in the dataset.

---

## R17 — Data citation for LLM systems (provenance, unresolved)

**Source:** "Data Citation for Large Language Models: A Challenge" — https://arxiv.org/html/2608.25663v1
**Accessed:** 2026-10-26 — **listed from search results; contents NOT opened or verified.**

**Status:** `[UNVERIFIED]`
**Known only:** the search result snippet states that data citation in LLM systems is a challenge and that data sources are available at inference time, making it "the first to tackle and the most immediately tractable" of several challenges.
**Rule:** do not cite this for any specific claim beyond the existence of the problem. If a draft needs provenance depth, use R15 and R16, which are verified.

---

## R18 — Bandit-driven prompt selection (not retrievable)

**Source:** Manakina & Bogdanov, "Learning to Grade Efficiently: A Bandit-Driven Prompt-Selection Framework for Low-Cost LLM Essay Scoring" — https://arxiv.org/pdf/2608.23814
**Accessed:** 2026-10-26 — **PDF fetched but returned raw binary; prose not extracted.**

**Status:** `[UNVERIFIED]` for all numbers and findings.
**Verified metadata only:** title, authors (Olga Manakina, Igor Bogdanov), arXiv v1, DOI 10.48550/arXiv.2608.23814.
**Rule:** may cite the existence of a bandit/online-learning approach to prompt selection, and the general framing of prompt selection as an online learning task rather than offline hyperparameter optimization. **May not** cite any performance number, savings figure, or specific result.

---

## Sources I searched for but could not verify usefully

- The paper at https://arxiv.org/abs/2307.03172 was retrieved under R3 and is about long-context position, **not** about "benchmark saturation / statistical issues / human evaluation" as I first guessed. Corrected in R3.
- https://arxiv.org/abs/2309.01431 was retrieved under R4 and is about the RGB benchmark's four RAG abilities, **not** about nDCG/recall@k/MRR. Corrected in R4.
- https://arxiv.org/abs/2210.11416 (R11) yielded only the abstract; the numbered "Finding 1"/"Finding 2" claims remain `[UNVERIFIED]`.
- HELMET is cited *within* R12's related-work discussion; the HANDBOOK.md paper does not summarize HELMET's methodology. Do not attribute HELMET-specific claims without fetching HELMET itself.

---

## Cross-source synthesis for the article (the spine of the argument)

These are the recurring, cross-validated findings that most drafts will draw on. Each is supported by at least two independent sources.

**Finding A — Rankings are not the same as fitness.**
R9 (leaderboards "overstate differences while obscuring common failure modes"; metrics miss "Reviewing Work" and "Data Structuring" entirely) + R10 (58% vs 94% truthfulness; larger models can be *less* truthful) + R13 (benchmark scores should guide, not determine, tool choice) + R8 (a model can ace a static benchmark and fail operationally).

**Finding B — Automated judging has known, nameable failure modes.**
R1 (position, verbosity, self-enhancement bias; "limited reasoning ability") + R2 (order swap flips rankings; 66 of 80 queries) + R8 (judges unreliable as sole authority; may miss domain policies and required tool sequences) + R16 (LLM judges retain biases).

**Finding C — Presence is not support.**
R15 (citation existence vs metadata mismatch; 9,442 citations; 0.838 F1 real-world) + R16 (Link Works >94% but Fact Check 24.4–76.8%; "users may reach a working, on-topic page that does not substantiate the associated assertion") + R5 (metric correlates for reasons other than what it measures).

**Finding D — More context, more citations, more reasoning tokens ≠ better output.**
R3 (lost in the middle) + R16 (Fact Check falls ~42 points as tool calls go 2→150) + R12 (reasoning effort helped some models and hurt GLM 5.2 by 2.7 points; token spend did not buy compliance) + R13 (long context alone is not a substitute for effective retrieval).

**Finding E — Read the trace, not the answer.**
R8 (procedural failures "can look plausible in the final response"; phantom tool calls, wrong order, omitted compliance calls) + R12 (enforce hard controls outside the model) + R4 (RAG models still struggle with negative rejection, information integration, false information).

**Finding F — Scale breaks selection.**
R6 (accuracy degrades beyond ~100 tool candidates as retrieval precision declines) + R7 (descriptions steer routing) + R5 (evaluate at least two systems and compare outputs on the same questions).

**Finding G — Human review has a specific, non-negotiable job.**
R8 (human review "remains essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions" — but is costly and slow) + R9 (human raters for subjective judgments) + R14 (field testing with real users; stakeholder involvement scaled to risk).

---

## What this research does NOT establish (important for the limitations section)

- There is no published, validated "how to pick the best article/tool/paper" algorithm. Any framework in these drafts is a **synthesis**, not a finding. Say so.
- Every number above comes from a specific setup. 43.13% tool-selection accuracy, 36.2% strict pass@1, 76.8% Fact Check, 58% truthfulness — none of these are universal constants. Each must be attributed with its source and context.
- Most sources are preprints. R8, R12, R15, R16 are 2026 arXiv preprints that have not (as far as I can tell) been peer-reviewed. R1 (NeurIPS 2023), R3 (TACL 2023), R4 (AAAI 2024), R10 (ACL 2022), R11 (ICLR 2023) are peer-reviewed. This distinction belongs in the article.
- LLM-as-judge numbers (R1, R2) are from 2023-era models. The bias mechanisms are structural, but the specific agreement rates are dated. R16 and R8 (2026) update the picture.
