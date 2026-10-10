# 95. GitHub (Copilot)

- **Role:** AI Engineer (Copilot, Copilot Chat, Copilot Workspace)
- **Tech stack:** Python, C#, TypeScript, Go, PyTorch, Hugging Face, vLLM, ONNX, Transformers, Vector DBs, OpenAI/Anthropic APIs
- **Comp band:** $200K-$500K (IC3-IC4 Senior); IC5 (Senior+) $350K-$800K; IC6 Principal $500K-$1.2M (Levels.fyi 2026, after Microsoft leveling)
- **Cumulative pass rate:** ~1-2%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, role fit, level | 30 min | ~45% advance |
| 2. **Technical phone screen** | 1 coding + 1 ML/LLM | 60 min | ~30% advance |
| 3. **Onsite (4 rounds)** | 1 coding, 1 system design, 1 ML/LLM deep-dive, 1 behavioral | 1-2 days | ~25% advance |
| 4. **Hiring committee** | Microsoft-style loop debrief | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp + level | 1 week | — |

GitHub's Copilot team is the canonical "AI for developers" interview. The loop tests for: (1) LLM application engineering (RAG, agents, prompting), (2) code understanding (the model is reading/writing code), (3) evaluation rigor (how do you know your model is good?), (4) infrastructure (serving LLMs at scale, latency, cost). Since the Microsoft acquisition, the bar is "Microsoft level 63-65" (Senior+).

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your AI/LLM background"
**Answer:** "I built [X] for [Y], working on [RAG, agents, fine-tuning, code models]. Most recently I shipped [Z] which [moved metric / shipped feature]."
**Tip:** Be specific about LLM work. GitHub Copilot is all about LLMs.

### Q1.2: "Why GitHub?"
**Answer:** "Three reasons. First, Copilot is the most successful AI product in history — the data flywheel from 100M+ users is unmatched. Second, Copilot Workspace and the 2026 agentic features (Copilot for PRs, Copilot Chat, code review) are the frontier of AI-for-engineering. Third, GitHub's culture is genuinely developer-first — they ship fast and treat engineers as customers."
**Tip:** Reference Copilot Workspace, Copilot Chat, Copilot for PRs, and the 2026 features (multi-file edits, agent mode, code review).

### Q1.3: "Location + comp"
**Answer:** GitHub is remote-friendly (after Microsoft acquisition). SF, NYC, Berlin, Vancouver are common. Some teams are remote-OK. Comp is Microsoft-band.

## Stage 2: Technical phone screen (60 min)

### Q2.1: Coding — "LRU cache" or "Two Sum + variant"
**Answer:** Standard implementations. GitHub's bar is medium LeetCode.
**Tip:** Don't over-engineer. They want clean code.

### Q2.2: LLM — "How would you build a RAG system for code search?"
**Answer:** "Chunking: split code into semantic units (function, class, block). Embeddings: code-specific model (e.g., CodeBERT, OpenAI text-embedding-3, Voyage Code). Index: hybrid (BM25 + vector). Retrieval: hybrid query, re-rank. Generation: LLM with retrieved code + metadata (file path, language). Eval: golden test set, code-execution-based metrics (does the generated code compile/pass tests?). Be aware of context-window limits, hallucination, and out-of-date docs."
**Tip:** Code-specific embeddings are key. Mention code-aware chunking.

### Q2.3: System design — "Design Copilot's inline suggestion system"
**Answer:** "Client (VS Code extension) streams keystrokes → debounce (200-500ms) → API call with prefix + suffix + recent edits → server: tokenize, call LLM (small, fast, possibly Copilot-tuned Code-Llama or proprietary model), stream tokens → client renders ghost text → on Tab/click, accept and log. Latency target: 200ms first token. Key challenges: latency, cost per user, privacy (code is sensitive)."
**Tip:** Be specific about latency, cost, and privacy. Copilot is shipped at scale.

## Stage 3: Onsite (4 rounds, 1-2 days)

### Round 3.1: Coding
**Q3.1.1:** "Parse a JSON string / tree traversal" — moderate.
**Q3.1.2:** "Design a rate-limited API client" — token bucket, retry, backoff.
**Q3.1.3:** "Implement a simple expression evaluator" — stack or recursive descent.

### Round 3.2: System design
**Q3.2.1:** "Design Copilot Chat (multi-turn coding assistant)." Conversation memory, RAG over the user's repo, file references, multi-file edits, code execution, agent planning. Discuss evaluation and safety.
**Q3.2.2:** "Design a code review AI." Diff parsing, understanding the change, suggesting issues (security, style, bug), inline comments, PR summary. Eval: precision on issue detection, false positive cost.

### Round 3.3: LLM / ML deep-dive
**Q3.3.1:** "Walk me through a RAG system you've built end-to-end." Be specific.
**Q3.3.2:** "How do you fine-tune a code LLM?"
**Answer:** "Data: high-quality code + natural language pairs (Stack-Overflow, docstrings, comments). SFT with task examples (bug fix, refactor, doc). DPO/RLHF with developer preferences. Eval: HumanEval, MBPP, internal golden set, online acceptance rate. Cost vs quality tradeoff vs off-the-shelf models (Copilot uses a mix of fine-tuned and frontier models)."
**Tip:** Reference actual techniques: SFT, DPO, RLHF, eval benchmarks.

### Round 3.4: Behavioral
**Q3.4.1:** "Time you shipped an LLM feature in 1 month." STAR.
**Q3.4.2:** "Time you improved a model's quality metric by 10%+." STAR.
**Q3.4.3:** "How do you handle LLM hallucination in a user-facing product?" — be specific.

## Stage 4: Hiring committee
Microsoft-style calibration. IC3 (Senior SDE) vs IC4 (Senior+) vs IC5 (Principal) is decided here. The bar for IC4 requires independent LLM feature ownership. IC5 requires influence on the Copilot platform or model-serving infra. Committee is cross-org and includes a senior leader.

## Stage 5: Offer
GitHub comp is Microsoft-band: solid base, RSU refresh annually, ESPP. RSU vests over 4 years. Negotiation is moderate. Relocation is well-funded. Team match is usually pre-onsite for some roles. Post-offer you can sometimes swap teams.

## Tips for the GitHub loop
1. **LLM fluency is mandatory** — fine-tuning, RAG, agents, prompting, eval.
2. **Code-aware ML is a differentiator** — code-specific embeddings, ASTs, code execution.
3. **Latency and cost matter** — Copilot serves 100M+ users, every ms and $ counts.
4. **Eval rigor is tested** — have a real answer to "how do you know your model is good?"
5. **Agent design is hot** — Copilot Workspace is multi-step agentic.
6. **Reference 2026 features** — Copilot for PRs, multi-file edits, agent mode, code review.
7. **Show you ship** — GitHub values velocity.

## Real candidate report
> "I interviewed for AI Engineer on Copilot Chat. The system design was on multi-turn coding assistant with file references and RAG over the user's repo. The ML deep-dive was on fine-tuning vs prompting tradeoffs for code. They asked me to whiteboard the eval pipeline. Got IC4 offer at $340K base + $600K RSU/4yr. They moved base by $30K on negotiation." — Blind, 2025

## Sources
- [GitHub Engineering Blog](https://github.blog/engineering/)
- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [Levels.fyi GitHub](https://www.levels.fyi/companies/github)
- [Glassdoor GitHub interviews](https://www.glassdoor.com/Interview/GitHub-Interview-Questions-E422265.htm)
- [LeetCode GitHub tagged](https://leetcode.com/company/github/)