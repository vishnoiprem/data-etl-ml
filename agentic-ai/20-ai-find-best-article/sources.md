# Source List

Access date for every URL: **2026-10-26**

Each entry maps a URL to the specific claims it supports. Claims listed here are the only claims from these sources that may appear in a draft without being re-verified. Anything else must be labelled `[UNVERIFIED]` or dropped.

Peer-review status is recorded because several of these are preprints and the article should say so.

---

## S1 — LLM-as-a-Judge (MT-Bench)

- **URL:** https://arxiv.org/abs/2306.05685
- **Citation:** Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E. P., Zhang, H., Gonzalez, J. E., & Stoica, I. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.* NeurIPS 2023 Datasets and Benchmarks Track.
- **Status:** Peer-reviewed (NeurIPS 2023 D&B). Last revision Dec 2023.
- **Supports:**
  - A strong judge (GPT-4) achieved "over 80% agreement" with controlled and crowdsourced human preferences, described as comparable to human-human agreement.
  - Three named biases: position/order bias, verbosity bias, self-enhancement bias.
  - Stated limitation: "limited reasoning ability."
  - Dataset scale: MT-bench with "3K expert votes" and "30K conversations with human preferences."
  - MT-bench and conventional benchmarks are complementary.

---

## S2 — Evaluator position bias

- **URL:** https://arxiv.org/abs/2305.17926
- **Citation:** Wang, P., Li, L., Chen, L., Cai, Z., Zhu, D., Lin, B., Cao, Y., Liu, Q., Liu, T., & Sui, Z. (2023). *Large Language Models are not Fair Evaluators.*
- **Status:** Preprint (arXiv). Submitted May 2023, revised Aug 2023.
- **Supports:**
  - Presenting candidate answers in a different order changes the ranking they receive.
  - Concrete result: "Vicuna-13B could beat ChatGPT on 66 over 80 tested queries" under a particular evaluator setup.
  - Three-part calibration framework: multiple-evidence calibration, balanced-position calibration, human-in-the-loop calibration.
  - "Balanced position diversity entropy" as a difficulty trigger for human assistance.
- **Does NOT support:** benchmark contamination claims.

---

## S3 — Long-context position effects

- **URL:** https://arxiv.org/abs/2307.03172
- **Citation:** Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2023). *Lost in the Middle: How Language Models Use Long Contexts.* TACL 2023.
- **Status:** Peer-reviewed (TACL 2023).
- **Supports:**
  - Evaluated on multi-document question answering and key-value retrieval.
  - "Performance can degrade significantly when changing the position of relevant information."
  - Best performance when relevant material is at the beginning or end; "significantly degrades when models must access relevant information in the middle."
  - The weakness affects explicitly long-context models too.
- **Does NOT support:** benchmark saturation, statistical-rigor, or human-evaluation findings.

---

## S4 — RAG benchmark (RGB)

- **URL:** https://arxiv.org/abs/2309.01431
- **Citation:** Chen, J., Lin, H., Han, X., & Sun, L. (2023/2024). *Benchmarking Large Language Models in Retrieval-Augmented Generation.* AAAI 2024.
- **Status:** Peer-reviewed (AAAI 2024).
- **Supports:**
  - RGB organizes RAG evaluation into four abilities: noise robustness, negative rejection, information integration, counterfactual robustness.
  - Six representative LLMs evaluated.
  - Models "still struggle significantly in terms of negative rejection, information integration, and dealing with false information."
  - Conclusion: "there is still a considerable journey ahead to effectively apply RAG to LLMs."
- **Does NOT support:** nDCG / recall@k / MRR figures; the general claim that "RAG quality is limited by retrieval quality."

---

## S5 — RAG metric reliability study

- **URL:** https://arxiv.org/html/2607.07302v1
- **Citation:** *Evaluating RAG Metrics in Applied Contexts: An Experiment, Its Lessons, and the Path Forward.* (2026). arXiv:2607.07302.
- **Status:** Preprint (arXiv). Dated Jul 8, 2026.
- **Supports:**
  - Metrics compared: Ragas, DeepEval, RAGChecker, Opik, plus BLEU, METEOR, ROUGE, BERTScore F1, word-level recall.
  - Two human evaluators' ratings had a Pearson correlation of **0.85** with each other and served as the reference.
  - RAGChecker produced the strongest overall-metric correlations, particularly recall-oriented metrics; RAGChecker claim recall was **near 0.7**.
  - METEOR correlated relatively well with human scores despite being sometimes described as obsolete.
  - Hallucination and faithfulness metrics correlated **weakly** as overall metrics, partly due to no access to reference answers.
  - Opik moderation did not correlate with the reference scores.
  - DeepEval contextual precision correlated **above 0.5** with recall despite not using reference spans.
  - Ragas's non-LLM retrieval metrics correlated weakly with recall; proposed cause is Levenshtein distance failing when retrieved and reference spans differ greatly in length.
  - High correlation alone does not establish validity — input difficulty and confounders can produce strong correlations. Single-system design cannot establish full metric validity; authors recommend evaluating **at least two RAG systems**.
  - Dataset: **96 questions**, wide confidence intervals.
- **Does NOT support:** that any one metric is "the best."

---

## S6 — Retrieval-based tool selection

- **URL:** https://arxiv.org/html/2505.03275v1
- **Citation:** *RAG-MCP: Mitigating Prompt Bloat in LLM Tool Selection via Retrieval.* (2025). arXiv:2505.03275.
- **Status:** Preprint (arXiv). Dated May 6, 2025.
- **Supports:**
  - Method: retrieve the most relevant MCP server from a semantic index before invoking the LLM, rather than presenting every tool schema.
  - Tool-selection accuracy rose to **43.13%**, vs **18.20%** for keyword matching and **13.62%** for an all-tools prompt.
  - Average prompt usage fell to **1,084 tokens**, vs **1,646** (keyword filtering) and **2,133.84** (all tools) — roughly **49% reduction** versus the latter.
  - Completion tokens: 78.14 vs 23.60 vs 162.25.
  - Performance degraded beyond roughly **100 candidates** as retrieval precision declined; authors propose hierarchical or adaptive retrieval for larger registries.
  - Passing only a relevant schema reduces distraction and preserves context for reasoning.
- **Does NOT support:** that 43.13% is a general accuracy figure for tool selection.

---

## S7 — Attack on tool selection

- **URL:** https://arxiv.org/html/2510.02554v1
- **Citation:** *ToolTweak: An Attack on Tool Selection in LLM-based Agents.* (2025). arXiv:2510.02554.
- **Status:** Preprint (arXiv). Dated Oct 2, 2025.
- **Supports:**
  - A gradient-free, black-box attack that iteratively changes a tool's **name and description** (parameter schema unchanged) to raise the likelihood the agent selects it over comparable tools.
  - Against an approximately **20% baseline**, best selection rates rose to **81.6% (DeepSeek), 73.6% (GPT-OSS), 50.7% (Grok 3 Mini), 48.7% (Gemini), 45.9% (Qwen 2.5), 34.0% (Llama 3.1)**.
  - Some attacks transferred across models; target-model architecture was the dominant factor.
  - The attack shifts the selection distribution away from expected parity, creating risks to "fairness, competition, and security in emerging tool ecosystems."
  - Defenses: objective paraphrasing reduced bias and strongly countered fixed persuasive suffixes, but was less effective against ToolTweak. Simple perplexity thresholds failed because benign and adversarial descriptions overlapped; combining length and perplexity appeared more promising.
- **Does NOT support:** that any specific marketplace is currently compromised, or any real-world prevalence rate.

---

## S8 — Agent evaluation and human review

- **URL:** https://arxiv.org/html/2606.16871v1
- **Citation:** Bousetouane, F. (2026). *Human-on-the-Bridge: Scalable Evaluation for AI Agents.* arXiv:2606.16871.
- **Status:** Preprint (arXiv). Dated Jun 15, 2026.
- **Supports:**
  - Static benchmarks do not adequately test multi-turn tool use, policy adherence, recovery, or procedural consistency.
  - A model may pass a fixed benchmark yet fail operationally through "missing tool calls, hallucinated tool use, policy drift, unsafe reframing, manipulation paths, or over-refusal."
  - Interactive/trajectory benchmarks are closer to real behavior but don't fully specify how experts curate adversarial risks or connect evidence to repeatable scoring.
  - Human-in-the-loop review preserves expert judgment — especially in healthcare, finance, privacy, legal, security — but is costly, slow, and hard to reproduce. Human review "remains essential for domain context, subtle policy interpretation, risk criteria, rubrics, and escalation decisions."
  - LLM-as-judge is faster, cheaper, repeatable, but unreliable as sole evaluation authority: "position bias, verbosity bias, self-enhancement bias, and judge reasoning limitations." Judges may miss domain policies, required tool sequences, and trajectory-level failures.
  - Red teaming is effective but often episodic, with inconsistent reuse across agents, domains, releases.
  - Trace analysis is necessary because "procedural failures can look plausible in the final response" — claiming a tool was used without invoking it, omitting mandatory compliance calls, calling tools in the wrong order.
  - Study scale: 47 configurations, 470 trials, 23,500 turns.
  - Author caveat: subjective juror scores are not calibrated to human experts; the non-factorial design limits definitive cross-configuration rankings.
- **Does NOT support:** rankings between specific commercial models.

---

## S9 — Metrics vs real-world capabilities

- **URL:** https://arxiv.org/html/2505.08253v1
- **Citation:** Miller, J. K., & Tang, W. (2025). *Evaluating LLM Metrics Through Real-World Capabilities.* arXiv:2505.08253.
- **Status:** Preprint (arXiv). Dated May 13, 2025.
- **Supports:**
  - "A fundamental mismatch" between benchmarks and real-world use; benchmarks "often focus on narrow, isolated tasks that do not capture the full spectrum of how people interact with AI."
  - Automated/reference-based metrics "can obscure ambiguous or context-sensitive errors," including hallucinations and stylistic mismatches.
  - Of six practical capabilities identified, "Reviewing Work and Data Structuring are not captured at all."
  - Metrics emphasize correctness while overlooking clarity, relevance, efficiency, tool coverage, and user interpretability; benchmarks "often prioritize abstract notions of correctness over qualities that matter to users."
  - Leaderboards may "overstate differences while obscuring common failure modes."
  - Recommendations: smaller curated datasets, transparent annotation protocols, published prompts/rubrics/annotation standards, human raters for subjective judgments, objective reference answers with confidence intervals, multi-turn interactions.
- **Does NOT support:** any numeric correlation coefficient between general LLM metrics and human judgment (the paper's argument is conceptual).

---

## S10 — TruthfulQA

- **URL:** https://arxiv.org/abs/2109.07958
- **Citation:** Lin, S., Hilton, J., & Evans, O. (2022). *TruthfulQA: Measuring How Models Mimic Human Falsehoods.* ACL 2022.
- **Status:** Peer-reviewed (ACL 2022). Submitted 2021.
- **Supports:**
  - **817 questions across 38 categories.**
  - Strongest tested model truthful on **58%** of questions; human performance **94%**.
  - Larger models were generally **less** truthful, reversing the usual scale/performance relationship.
  - "Scaling up models alone is less promising" than other objectives.
- **Does NOT support:** benchmark saturation or contamination figures; any claim about 2026-era models — this is a 2021-2022 study and must be dated in the body.

---

## S11 — Instruction finetuning at scale

- **URL:** https://arxiv.org/abs/2210.11416
- **Citation:** Chung, H. W., Hou, L., Longpre, S., Zoph, B., Tay, Y., Fedus, W., Li, Y., Wang, X., Dehghani, M., Brahma, S., Webson, A., Gu, S. S., Dai, Z., Su, G., Sun, M., Chen, X., Chowdhery, A., Castro-Ros, A., Pellat, M., Robinson, K., Narang, S., Mishra, G., Adams, Y., Vincent, Z., Huang, Y., Andrew, D., Chi, H. K., Dean, J., Devlin, D., Roberts, A., Zhou, D., Le, Q. V., & Wei, J. (2022). *Scaling Instruction-Finetuned Language Models.* ICLR 2023.
- **Status:** Peer-reviewed (ICLR 2023).
- **Supports:**
  - Instruction finetuning on instruction-phrased datasets improves performance and generalization to unseen tasks.
  - Evaluated under zero-shot, few-shot, and CoT prompting; across MMLU, BBH, TyDiQA, MGSM, and open-ended generation.
  - Flan-PaLM 540B, finetuned on **1.8K tasks**, outperformed PaLM 540B by **"+9.4% on average"** and reached **"75.2% on five-shot MMLU."**
  - Public Flan-T5 checkpoints performed strongly in few-shot settings relative to larger models such as PaLM 62B.
- **Does NOT support:** the numbered "Finding 1" / "Finding 2" results, model-by-prompt interaction details, or any statement about which single prompt is best — these were not retrieved (abstract page only). `[UNVERIFIED]`

---

## S12 — Long-context agentic instruction following

- **URL:** https://arxiv.org/html/2607.25398v3
- **Citation:** *HANDBOOK.md: A Benchmark for Long-Context Agentic Instruction Following.* (2026). arXiv:2607.25398.
- **Status:** Preprint (arXiv).
- **Supports:**
  - Existing evaluations "measure reading"; the authors argue agentic long-context work requires details to "remain operative dozens of tool calls after they were read."
  - Strict vs relaxed grading: a relaxed "pass@1 (N−1)" metric tolerating one failed criterion roughly doubles leader scores; the authors warn a deployment tolerating one violated control per workflow "has effectively abandoned strictness."
  - **Reasoning effort is not monotonically better:** helped Opus 4.8 (**+3.0 points**), Sonnet 4.6 (**+2.7**), Fable 5 (**+2.0**); left GPT-5.5 unchanged; **hurt GLM 5.2 (−2.7)**. Authors' interpretation: deliberation converts into compliance only when the error was a "missed inference rather than a missed read."
  - **Token spend does not buy compliance:** GPT-5.5 reached **21.5%** on roughly **13K generated tokens/trial**; Opus 4.8 (max) spent close to **60K tokens** and about **three times the dollar cost** for the same band; several mid-pack configurations generated **45–55K tokens** yet scored in single digits; GLM 5.2 cited at **12.7%** for well under a dollar per trial.
  - Best configuration scored **36.2%** strict pass@1 — "still failed nearly two of every three tasks."
  - Recommendation: "enforcing hard controls outside the model," e.g. compiling policies into deterministic tool-call guards.
- **Does NOT support:** general model rankings — this is one benchmark with one difficult task type.

---

## S13 — Software-engineering agent benchmark survey

- **URL:** https://arxiv.org/html/2510.09721v3
- **Citation:** *A Comprehensive Survey on Benchmarks and Solutions in Software Engineering Agents.* (2025). arXiv:2510.09721.
- **Status:** Preprint (arXiv). Dated Oct 23, 2025.
- **Supports:**
  - Benchmark progression from small function-generation tasks (HumanEval, MBPP) to real GitHub issues, pull requests, cross-file dependencies, and real test environments (SWE-bench, DevEval, RepoCOD, R2E-Eval, SWE-smith, SWE-rebench).
  - Strongest benchmark design combines a real repository, issue specification, environment setup, cross-file dependencies, and tests that determine whether the patch works.
  - **SWE-bench is not fully reliable:** a cited analysis found many issues counted as solved were actually resolved incorrectly; passing benchmark tests should not automatically be equated with production-quality repair.
  - Evaluation broadened to maintainability, efficiency, security, test generation, refactoring, environment setup, collaboration; some use formal verification (Lean type checking, proof generation, verifier-guided refinement).
  - Contamination: DyCodeEval was created to evaluate models under different contamination levels; "unfamiliarity cannot safely be assumed" for benchmarks drawn from public repositories.
  - **Model selection by task complexity:** ordinary instruction-tuned LLMs for straightforward generation/explanation/small edits; structured or long-context models when repository relationships and ordered context matter; supervised fine-tuning when behavior must consistently follow domain-specific workflows or patch formats; preference alignment/RL when the objective is hard to express through demonstrations (security, efficiency, correctness under executable feedback).
  - Tool choice determined by needed feedback: repository navigation, AST/dependency graphs, search, editors, terminals, compilers, test runners, static analyzers, Docker, debuggers, language servers, formal verifiers, simulators, multimodal input. "Long context alone is not a substitute for effective retrieval" — concatenating all relevant files was suboptimal and snippet ordering materially affected performance.
  - Agent capability groups: planning/decomposition, reasoning/self-refinement, memory, tool use; effective systems combine role specialization, repository exploration, iterative execution, validation, recovery.
  - **Bottom line:** "Benchmark scores should guide—rather than determine—tool choice." Compare candidates on target repository, language, context length, test strength, contamination exposure, latency, cost. For security-sensitive or maintenance-critical work, add verifiers or human review.
- **Does NOT support:** specific numeric model comparisons beyond those quoted from the cited SWE-bench analysis.

---

## S14 — Real-world evaluation ecosystem

- **URL:** https://arxiv.org/html/2505.18893v4
- **Citation:** *A New Evaluation Ecosystem Is Necessary to Understand AI's Real World Impact.* (2025). arXiv:2505.18893.
- **Status:** Preprint (arXiv). Dated May 30, 2025.
- **Supports:**
  - Moving beyond static, single-turn, in-silico benchmarks to what emerges when people use AI in context.
  - Capturing first-order effects (outputs) plus second- and third-order effects (behavior shifts, workforce changes, societal impact).
  - Centering the "contextual unit" — adaptive behavior of people using AI in a setting — rather than the model.
  - Benchmark challenges: static datasets poorly reflect deployment; benchmark metrics emphasize accuracy or policy violations, translating poorly to second-order questions; leaderboard overreliance encourages overfitting and benchmark saturation; contamination and data leakage can inflate results; weak internal/external validity, narrow English-language focus, limited stakeholder involvement, and mathematical stand-ins for complex social phenomena create a "fallacy of objectivity"; benchmarks can lag agentic capabilities.
  - Recommended approach — value-sensitive design, three activities:
    - **Context specification:** define a theory of change with stakeholders (goals, inputs, outputs, outcomes, counterfactuals); operationalize concepts; involve affected groups proportionally to risk.
    - **Field testing:** observe real users across repeated sessions under semi-controlled conditions; randomization and blinding plus surveys, logs, performance metrics, annotation of interactive outputs; naturalistic but safe scenarios.
    - **Red teaming:** realistic and adversarial use to uncover failure patterns, misuse, boundary conditions, mitigation effectiveness; expert, public, and automated approaches; multilingual, dialectal, multi-turn, multimodal coverage; psychological safety protections; tester bias; transparency rules; track effectiveness over time.
  - Ecosystem recommendations: shared testing hubs across academia, industry, civil society, government, public; organizations supply evaluation questions, individuals contribute context and participate, independent testers provide credibility, researchers formalize metrics; preserve qualitative work rather than treating it as secondary; automate valuable activities over time.

---

## S15 — Citation faithfulness audit

- **URL:** https://arxiv.org/html/2602.23452v3
- **Citation:** *CiteAudit: You Cited It, But Did You Read It? A Benchmark for Citation Faithfulness.* (2026). arXiv:2602.23452.
- **Status:** Preprint (arXiv). Dated May 1, 2026.
- **Supports:**
  - Tests whether a citation corresponds to an actual publication and whether core metadata (title, authors, venue, year, identifiers) matches authoritative records.
  - Detects fully fabricated references and subtler errors ("title mismatch," "author mismatch") indicating the cited paper was not read accurately.
  - Benchmark totals: **9,442 citations** (6,475 real, 2,967 fake). Generated test set: **3,586 real + 2,500 hallucinated**. Real-world test set: **2,889 authentic + 467** naturally occurring errors. Generated hallucination types: **1,000 title, 1,000 author, 500 metadata**.
  - Framework: five roles (extraction, memory, web search, scholar retrieval, judgment); memory-match threshold **0.92**.
  - Multi-agent system achieved **0.966 accuracy / 0.959 F1** on generated data and **0.949 accuracy / 0.838 F1** on real-world data; real-world F1 exceeded the next-best system by **0.267**.
  - Field-level problems that baselines accepted because the underlying paper existed.
  - Commercial and open models showed a recurring trade-off: either missing fabricated references or falsely rejecting valid ones.
  - GPTZero comparison: similar behavior on generated and real-world hallucinations (p = 0.994).
  - **Author caveat:** author-run annotation and potential indexing gaps mean independent replication and broader source coverage remain important.
- **Does NOT support:** a claim that AI-written reference lists are broadly unreliable for human-authored work.

---

## S16 — Source attribution in LLM deep research

- **URL:** https://arxiv.org/html/2605.06635v1
- **Citation:** *Parsing and Evaluating Source Attribution in LLM Deep Research.* (2026). arXiv:2605.06635.
- **Status:** Preprint (arXiv). Dated May 7, 2026.
- **Supports:**
  - Pipeline: Markdown AST parser extracts claim–citation pairs without model inference; content behind each cited URL retrieved and extracted; each pair scored on **Link Works** (URL accessible), **Relevant Content** (topically aligned with the claim), **Fact Check** (source supports the specific factual assertions).
  - Tested on **14 models** and **130 research queries**, using rubric-based LLM judges calibrated through human review.
  - Link validity exceeded **94%**; relevance exceeded **80%**; factual accuracy ranged **39%–77%**; full model-level Fact Check range **24.4%–76.8%**.
  - Open-source models: properly cited report success **17%–40%** vs **83%–100%** for frontier models.
  - **Link and relevance stayed strong even when specific claims were unsupported** — a user may reach a working, on-topic page that does not substantiate the assertion.
  - **More searching hurt factual synthesis:** across GPT-5.4 and Claude Opus 4.6, Fact Check fell about **42 percentage points on average** as tool calls rose from **2 to 150**. GPT-5.4 dropped **78.6% → 16.7%**; Claude Opus 4.6 **80.0% → 57.9%**. Link Works and Relevant Content stayed above **92%** throughout.
  - Model tendencies: OpenAI models generated more citations with lower factual accuracy; Anthropic models generally less successful but more accurate; Claude Opus 4.5 led the model table with **76.8%** Fact Check.
  - Common link failures: HTTP 404, blocked or paywalled pages, timeouts.
  - Author cautions: LLM judges retain biases; web-based citations are temporally unstable.
- **Does NOT support:** generalizing these percentages to human reading habits or to all AI-written content.

---

## S17 — Data citation for LLMs — UNVERIFIED

- **URL:** https://arxiv.org/html/2608.25663v1
- **Status:** `[UNVERIFIED]` — listed from search results only; page contents not opened or confirmed.
- **May support:** the existence of a data-citation challenge in LLM systems, and the observation that data sources are available at inference time (snippet wording: "the first to tackle and the most immediately tractable").
- **May NOT support:** any specific finding, number, or recommendation.

---

## S18 — Bandit-driven prompt selection — UNVERIFIED

- **URL:** https://arxiv.org/pdf/2608.23814
- **Citation:** Manakina, O., & Bogdanov, I. (2026). *Learning to Grade Efficiently: A Bandit-Driven Prompt-Selection Framework for Low-Cost LLM Essay Scoring.* arXiv:2608.23814.
- **Status:** `[UNVERIFIED]` for all findings and numbers — PDF fetched but returned raw binary; prose not extracted.
- **Verified metadata only:** title, authors, arXiv v1, DOI 10.48550/arXiv.2608.23814.
- **May support:** the existence of a bandit/online-learning approach to prompt selection, and the framing of prompt selection as an online learning task rather than offline hyperparameter optimization.
- **May NOT support:** any performance number, savings figure, or specific experimental result.

---

## Sources explicitly rejected

These appeared in search results and were **not** used. Either they were vendor marketing content, duplicates of better sources, or could not be verified.

- https://www.openlayer.com/blog/llm-as-judge-evaluation-guide — vendor blog; claims not independently verified.
- https://www.confident-ai.com/blog/why-llm-as-a-judge-is-the-best-llm-evaluation-method — vendor blog; headline framing ("85% agreement") conflicts with the peer-reviewed S1 figure and could not be traced to a primary study.
- https://deepeval.com/blog/llm-as-a-judge — vendor blog.
- https://llmboard.ai/ — aggregator leaderboard, not a primary source.
- https://freeacademy.ai/blog/what-is-llm-beginners-guide-2026 — SEO content.
- https://kili-technology.com/blog/rag-evaluation-guide-measuring-retrieval-and-generation-as-separate-problems — vendor blog; superseded by S5.
- https://medium.com/@adnanmasood/closing-the-eval-deployment-gap-in-ai-systems... — personal essay; superseded by S13 and S14.
- https://en.m.wikipedia.org/wiki/Large_language_model — encyclopedia, not a citable source for claims here.
- https://arxiv.org/html/2604.14951v1 (RaTA-Tool) and https://arxiv.org/html/2610.31013v1 (Multi-Tool Selection for Robotic Systems) — 2026 preprints in adjacent areas; S6 and S7 cover the same ground with the numbers actually needed.
- https://arxiv.org/html/2610.30355v1 (CiteAnchor) — 2026 preprint; S15 and S16 give the quantitative evidence needed.
- https://arxiv.org/html/2609.14579v1, https://arxiv.org/html/2605.27444v1, https://arxiv.org/html/2605.27445v1 — RAG evaluation preprints surfaced in search; not fetched, no claims drawn.
- https://arxiv.org/html/2604.03657, https://arxiv.org/html/2610.12601v1, https://arxiv.org/html/2610.31743v1 — prompt-optimization preprints surfaced in search; not fetched, no claims drawn.
- https://arxiv.org/html/2505.18893v4 — **USED**, see S14 (listed here only to note it was reclassified from rejected after fetching).

---

## Citation-count guidance for drafts

- Minimum **6 distinct sources** in the source list.
- Maximum practical **10** — beyond that the piece turns into a literature review.
- Every source listed must be cited inline in the body at least once (no decorative bibliography).
- Every inline citation must appear in the source list (no orphan citations).
- Any claim attributed to S17 or S18 must carry an inline `[UNVERIFIED]` marker.
