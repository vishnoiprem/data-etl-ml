# GenAI / LLMs / Agents / Vector DBs / RAG Question Prep — "Familiarity with Generative AI, LLMs, AI agents, vector databases, or RAG architectures is a strong plus"

> **Purpose:** Full preparation file for the GenAI/agents/RAG qualification line on the role's "What you bring" list. Second in the qualifications series after `ml-mlops-ai-platform-question-prep.md`. Tests the *applied* AI depth — can you design, debug, and safely ship AI features, not just talk about them?

---

## The Question

- **Round:** Onsite 1 (technical panel — Vu Bui, Que Tran, Son Dao) and Onsite 2 (Duke Nguyen, VP Engineering); almost always asked as a follow-up to the ML/MLOps line
- **Source:** Job posting, "AI & Leadership" qualifications, line 49 of `README.md`
- **Verbatim:** *"Familiarity with Generative AI, LLMs, AI agents, vector databases, or RAG architectures is a strong plus."*
- **Likely probes:**
  - "Walk me through a RAG system you designed."
  - "When is RAG the wrong choice?"
  - "How do you debug wrong RAG answers?"
  - "How do you choose embedding model + chunking + retriever?"
  - "What is hybrid retrieval? When does it win?"
  - "Reranker — when, and at what cost?"
  - "How do you scale an agent safely?"
  - "What is prompt injection and how do you defend?"
  - "Build vs buy a vector DB?"
  - "Function calling vs agents — when to use which?"
  - "How do you evaluate an LLM feature end to end?"

---

## Framework Used

- **Strategic:** **Job → Data → Retrieve → Reason → Guard → Measure** (the GenAI app spine)
- **Tactical:** **Retrieve-vs-Generate debugging** (the question that breaks most teams)
- **Anchor sentence:** *"RAG is not magic. It's a contract: the right context, in the right shape, for the right model, with the right guardrails — measured against an eval set you actually trust."*

🔵 **Hook: "Job first. Retrieval before generation. Citation before answer. Eval before ship."**

---

## 60–90 Second Spoken Answer (lead with this)

> GenAI features aren't one thing — they're a **pipeline**: job-to-be-done, data, retrieval, reasoning, guardrails, measurement. I always start with the **job**, then the **eval set** — before the model, before the vector DB.
>
> For retrieval, I default to **hybrid** — BM25 for exact codes and IDs, dense vectors for semantic similarity, metadata filters for tenant and freshness. I rerank only when the eval says it pays for the latency. The right chunking depends on the data: small chunks for code and tables, larger for prose, with overlap.
>
> For agents, I follow **least-privilege**: smallest action space, read-only defaults, explicit confirmation for mutations, full audit log, retries with idempotency. Tool outputs and retrieved text are **untrusted input** — that's where prompt injection comes from.
>
> For Katalon specifically: AI is the product, so the AI plane is the *first* plane, not an add-on. RAG over tenant test context with strict isolation. Failure triage, flakiness, test selection, requirements coverage — each one an eval set before it ships.
>
> A "strong plus" means I can design, debug, and ship these safely — not just explain them on a whiteboard.

⏱️ ~95 seconds.

---

## The GenAI Application Spine (memorize this)

```
1. JOB-TO-BE-DONE
   Task + user + decision + cost of being wrong
        │
        ▼
2. DATA
   Governed source, tenant-scoped, PII/secret scan
        │
        ▼
3. RETRIEVE
   Hybrid (BM25 + vector) + metadata filter + tenant filter + rerank
        │
        ▼
4. REASON
   Prompt + tools + schema-constrained output + abstention
        │
        ▼
5. GUARD
   System/user split, output validation, kill switch, audit
        │
        ▼
6. MEASURE
   Offline (golden) + online (shadow/canary) + safety
        │
        ▼
7. ITERATE
   Feedback → eval refresh → prompt/data update → re-eval
```

🔵 **Hook: "If you can't draw this from memory, you don't own the system."**

---

## When RAG Wins (and When It Doesn't)

| Use case | RAG? | Why |
|---|---|---|
| Knowledge changes often (docs, support, product) | ✅ Yes | Freshness without retraining |
| Citations matter (failure analysis, support) | ✅ Yes | Grounded, defensible |
| Multi-tenant isolation required | ✅ Yes | Tenant-scoped retrieval |
| Precise logic over tables/numbers | ⚠️ Maybe | Often tool-calling + SQL beats RAG |
| Knowledge base fits in context (small, stable) | ❌ No | Just inline it |
| Latency budget is very tight + task is narrow | ❌ No | Small fine-tuned model often wins |
| Retrieval quality is fundamentally bad | ❌ No | Smaller fine-tuned model beats hallucination |

🔵 **Hook: "RAG is the default for enterprise knowledge, not the only tool."**

---

## RAG Design Decisions (the ones that actually matter)

### Chunking

| Content type | Chunk size | Overlap | Why |
|---|---|---|---|
| Code / stack traces | Small (200–500 tokens) | 10–20% | Functions, error lines, frames |
| Tables / structured | By row or block | Header in each chunk | Avoid splitting across rows |
| Prose / docs | Medium (500–1,000 tokens) | 15–25% | Preserve paragraph context |
| Conversations | By turn, with summary | Speaker metadata | Preserve attribution |

**Rule:** chunk by *semantic unit*, not by token count alone. Test on a sample.

### Embedding model

| Need | Pick (illustrative) | Trade-off |
|---|---|---|
| English prose, semantic similarity | OpenAI text-embedding-3, Voyage, Cohere | Cost vs quality |
| Code / structured | Code-specific (e.g., Voyage Code) | Specialized, narrower domain |
| Multilingual | Multilingual e5, BGE-M3 | Lower per-language quality |
| On-prem / private | BGE, Instructor, GTE | You operate it |

**Rule:** benchmark on **your** data, not on a public leaderboard.

### Retrieval

| Strategy | When | Cost |
|---|---|---|
| **Vector only** | Semantic similarity, prose | Low |
| **BM25 only** | Exact codes, IDs, error strings | Low |
| **Hybrid (BM25 + vector)** | Most enterprise cases | Med |
| **Hybrid + reranker (cross-encoder)** | Quality matters more than latency | High |
| **Multi-hop / agentic retrieval** | Complex questions, many sub-queries | Very high |

**Rule:** start hybrid, add reranker only if eval says it pays.

🔵 **Hook: "Most RAG failures are retrieval. Look there first."**

---

## Debugging RAG: Retrieve vs Generate

**Step 1 — Was the right chunk in top-k?**

| Answer | Diagnosis | Fix |
|---|---|---|
| No | Retrieval problem | Re-chunk, hybrid search, tune embeddings, add metadata filters, add reranker |
| Yes | Generation problem | Tighten prompt, reduce irrelevant context, require citations, stronger model |

**Step 2 — If generation problem, what kind?**

| Symptom | Likely cause | Fix |
|---|---|---|
| Hallucinated facts | Model filling gaps | Stricter context, "say I don't know" rule, abstention threshold |
| Wrong tone / style | Prompt drift | Refine prompt, few-shot examples |
| Lost in middle | Context too long | Cap top-k, compress, restructure |
| Stuck on one source | No diversity | MMR, multi-query, query rewrite |
| Cited chunk not relevant | Retrieval ranker | Add reranker, better embeddings |

**Step 3 — Measure both layers separately.**

- Retrieval: recall@k, MRR, nDCG, evidence coverage
- Generation: groundedness, citation correctness, faithfulness, helpfulness

🔵 **Hook: "Most teams debug generation when the bug is retrieval. 80% of failures are upstream."**

---

## Reranker Decision

| Signal | Use reranker? |
|---|---|
| Top-1 accuracy is the bottleneck | Yes |
| Latency budget < 300ms p95 | No (or async) |
| Cost per query matters | No (or selectively) |
| Long-context queries | Yes (compress before rerank) |
| High-stakes (legal, financial) | Yes |

**Default:** don't add a reranker until the eval says it wins. Always re-evaluate the cost/latency trade.

🔵 **Hook: "Rerankers are a force multiplier, not a default."**

---

## Hybrid Retrieval (concrete recipe)

```python
# Pseudocode for hybrid retrieval
def hybrid_retrieve(query, tenant_id, k=20):
    # Tenant filter applied BEFORE scoring, not after top-k
    candidates = []

    # BM25 for exact codes / IDs / error strings
    bm25 = bm25_search(query, filter={"tenant_id": tenant_id}, k=k*2)
    candidates.extend(bm25)

    # Dense for semantic similarity
    dense = vector_search(query, filter={"tenant_id": tenant_id}, k=k*2)
    candidates.extend(dense)

    # Reciprocal rank fusion or weighted sum
    fused = reciprocal_rank_fusion(candidates)

    # Optional: rerank top-N
    top = fused[:50]
    if RERANKER_ENABLED:
        top = reranker.rerank(query, top)[:k]
    else:
        top = top[:k]

    return top
```

**Rule:** tenant filter is the *first* predicate, not a post-hoc cleanup.

🔵 **Hook: "Tenant filter before scoring. If it's after top-k, you have a leak."**

---

## Prompt Injection: Defense in Depth

**Threat model:** Attacker hides instructions in untrusted content (logs, scripts, docs, support tickets, web pages, retrieved chunks).

| Layer | Defense |
|---|---|
| **Architectural** | Treat retrieved text as *data*, never as system instruction. Separate system policy from user content structurally. |
| **Authorization** | Filter on tenant/project *before* scoring, not after top-k. |
| **Tools** | Limit tools by tenant/role/action. Read-only defaults. |
| **Redaction** | Strip secrets and high-risk PII before submission. |
| **Output** | Validate structured outputs against a schema. Defend downstream renderers against generated HTML/script. |
| **Monitoring** | Log prompt, retrieved IDs, safety actions, outcome. Don't log raw sensitive content by default. |
| **Recovery** | Kill switch by feature/tenant/model. Rollback to last-known-good. |

🔵 **Hook: "Prompt injection is an input-trust problem, not a prompt-cleverness problem."**

---

## Function Calling vs Agents

| Pattern | When | Example |
|---|---|---|
| **Function calling (1 LLM → N tool calls)** | Task fits in one reasoning pass, tools are well-bounded | "Get the tenant's last 10 failures, classify each" |
| **Multi-step agent** | Task needs planning, retries, or branching | "Investigate failure, query logs, propose fix, draft PR" |
| **Multi-agent** | Distinct roles, parallelizable, complex | Planner + Executor + Reviewer (rarely worth it) |

**Default:** function calling. **Move to agent only when:** the task genuinely needs planning, the action space is small and authorized, and the failure cost is bounded.

🔵 **Hook: "Most 'agents' are function calls with extra steps. Add autonomy only when the value exceeds the risk."**

---

## Agent Safety Architecture

```
User intent
    │
    ▼
Planner (proposes plan)
    │
    ▼
Policy Engine
  - tenant/role/action/object authorization
  - rate limits, budget caps, step caps
    │
    ▼
Typed Tools (read test, read result, search history, draft change)
    │
    ▼
Confirmation Gate (for mutations, broad-impact actions)
    │
    ▼
Executor + Immutable Audit Log
    │
    ▼
Verification (post-condition checks, idempotency)
```

**Rules:**
- Read-only defaults
- Confirmation before any mutation with broad impact
- Idempotency keys for side effects
- Cap on steps and spend per request
- Full trace: inputs, plan, tool calls, outputs, decision
- Replayable from log for incident review

🔵 **Hook: "An agent without a policy engine is a script with a vocabulary."**

---

## Vector DB Decision

| Question | Default answer |
|---|---|
| Do you already have Postgres? | pgvector — one less system |
| < 10M vectors, simple needs? | pgvector or your existing search |
| Need hybrid + rich filtering? | OpenSearch, Elasticsearch, Weaviate |
| Need very low latency at scale? | Pinecone (managed), Qdrant (self-host) |
| Need multi-tenant with row-level policy? | Whichever integrates with your existing auth + row-level controls |
| Don't want to operate it? | Managed (Pinecone, Vertex Vector Search) |

**Rule:** don't add a vector DB until you've outgrown pgvector or your existing search system. Always confirm tenant-isolation story.

🔵 **Hook: "Vector DB is rarely the bottleneck. Isolation, retrieval quality, and ops are."**

---

## Evaluating an LLM Feature (end-to-end)

| Layer | What | Metrics |
|---|---|---|
| **Retrieval** | Right chunks in top-k | recall@k, MRR, nDCG, evidence coverage, cross-tenant leakage = 0 |
| **Generation** | Faithful, cited, useful | groundedness, citation correctness, helpfulness, harmful rate |
| **Product** | User accepts, decision improves | acceptance, edit-distance, time-to-decision, override, escalation |
| **Reliability** | Stable, fast, cheap | p50/p95, timeout rate, fallback rate, $/request |
| **Safety** | No leaks, no harmful actions | PII leakage, prompt-injection success, unauthorized tool action |

**Process:**
1. Build stratified, versioned golden set
2. Calibrate LLM-as-judge against humans (Cohen's kappa > 0.7)
3. Red-team before release
4. Shadow in production
5. Canary by tenant
6. Monitor drift, calibration, slice regressions
7. Refresh eval set on a schedule

🔵 **Hook: "No golden set, no LLM feature. Same as no runbook, no on-call."**

---

## Common Probes — Pre-Rehearsed Answers

### Q1: "Walk me through a RAG system you designed."

🟢 *[STAR-R, ~90s. Anchor on: job-to-be-done, hybrid retrieval choice, why hybrid, chunking, eval set, what failed offline, what failed in canary, verified outcome. Don't bluff metrics.]*

### Q2: "When is RAG the wrong choice?"

🟢 *"Three cases. (1) Knowledge base is small enough to fit in context. (2) The task is precise logic over tables/numbers — use tool-calling + SQL. (3) Retrieval quality is fundamentally bad and a smaller fine-tuned model would do better. RAG is the default for enterprise knowledge, not the only tool."*

### Q3: "How do you debug wrong RAG answers?"

🟢 *"Separate retrieval from generation. Was the right chunk in top-k? If no, it's retrieval — re-chunk, hybrid search, tune embeddings, add metadata filters, add reranker. If yes, it's generation — tighten prompt, reduce irrelevant context, require citations, stronger model. 80% of failures are retrieval. Look there first."*

### Q4: "How do you choose embedding model + chunking + retriever?"

🟢 *"Three answers tied to the data, not the leaderboard. (1) Chunk by semantic unit — small for code, larger for prose, by row for tables, with overlap. (2) Embedding — benchmark on your data; for code use code-specific; for multilingual use multilingual e5/BGE-M3. (3) Retriever — start hybrid (BM25 + vector), add reranker only if eval says it pays. Always test on a stratified sample of your real data."*

### Q5: "What is hybrid retrieval? When does it win?"

🟢 *"BM25 for exact codes, IDs, error strings + dense vectors for semantic similarity, fused via reciprocal rank fusion. Wins when the data mixes exact identifiers (test IDs, error codes, function names) with semantic descriptions (failure summaries, requirement text). Most enterprise RAG is hybrid. Vector-only is fashion, not a default."*

### Q6: "Reranker — when and at what cost?"

🟢 *"When top-1 accuracy is the bottleneck AND latency budget allows AND cost per query allows. Cost: rerankers (cross-encoders) add 50–200ms p95 and meaningful token cost. Default: don't add one until eval says it pays. Always re-evaluate the trade."*

### Q7: "How do you scale an agent safely?"

🟢 *"Least-privilege action space. Read-only defaults. Explicit confirmation for mutations with broad impact. Idempotency keys for side effects. Cap on steps and spend per request. Full trace log — inputs, plan, tool calls, outputs, decision. Replayable for incident review. Policy engine between planner and tools. Treat tool outputs and retrieved text as untrusted input."*

### Q8: "What is prompt injection and how do you defend?"

🟢 *"Malicious instructions hidden in untrusted content — logs, scripts, docs, support tickets, web pages, retrieved chunks. Defense in depth: treat retrieved text as data, never as system instruction; separate system policy from user content structurally; tenant filter *before* scoring; limit tools by tenant/role/action; redact secrets; validate outputs against schema; defend downstream renderers; kill switch."*

### Q9: "Build vs buy a vector DB?"

🟢 *"Decision drivers: scale, filtering needs, ops burden, where source data and access controls already live. pgvector or your warehouse's vector features if scale fits. Dedicated vector DB (Pinecone, Weaviate, Qdrant) when you need very large scale, sub-100ms latency, advanced filtering, or hybrid search. Don't add a system to add a system. Always confirm tenant-isolation story."*

### Q10: "Function calling vs agents — when to use which?"

🟢 *"Function calling when the task fits in one reasoning pass and tools are well-bounded. Multi-step agent when the task genuinely needs planning, retries, or branching. Multi-agent rarely worth it. The trap: building an 'agent' for what is really a function call with extra steps. Add autonomy only when the value exceeds the risk."*

### Q11: "How do you evaluate an LLM feature end-to-end?"

🟢 *"Three layers. Offline — stratified, versioned golden set with retrieval metrics (recall@k, MRR, evidence coverage) + generation metrics (groundedness, citation correctness, helpfulness). LLM-as-judge calibrated against humans on a sample (Cohen's kappa > 0.7). Pre-release — red-team for safety, injection, PII. Online — shadow, canary by tenant, A/B on verified task outcome. No golden set, no LLM feature."*

### Q12: "Your RAG answer cited a chunk that doesn't actually support the claim. What went wrong?"

🟢 *"Two failure modes. (1) Generation hallucinating a citation — the model is making up support. (2) Retrieval returning an irrelevant chunk the model is forced to use. Diagnose by checking citation accuracy on a stratified sample. Fix: tighter prompt requiring quote-then-answer; add a citation-validity check that requires the cited chunk to contain the claim; or filter low-confidence citations."*

### Q13: "How do you handle 'I don't know' in a RAG system?"

🟢 *"Abstention is a feature, not a failure. When confidence is below an empirically-set threshold, when no supporting evidence is retrieved, when tenant policy forbids the retrieval, or when the input is ambiguous — say so. Better an honest 'I don't know' than a confident hallucination. Track abstention quality — too many = underuse, too few = overconfident."*

### Q14: "How do you keep an LLM feature cheap?"

🟢 *"Cache aggressively (with version key + tenant key). Compress context. Cap top-k. Use smaller models for sub-tasks (classification, extraction) and bigger models only for synthesis. Batch async where possible. Set per-tenant budgets. Measure $/resolved task, not $/request. The trick: most LLM cost is in irrelevant context, not in the model."*

### Q15: "What's the difference between a chat model and an agent?"

🟢 *"A chat model is one model → one response. An agent is a model + planning + tools + memory + state. The value of an agent is taking actions in the world. The risk is exactly the same. The architectural discipline — policy engine, typed tools, audit log, confirmation gates — is what makes an agent safe. Without that, it's a chat model with permissions, which is a security incident waiting to happen."*

---

## Anti-Patterns (red-flag answers)

- ❌ "We just send the whole doc to GPT" — cost, latency, relevance, privacy, injection surface
- ❌ "We use RAG for everything" — sometimes tool-calling + SQL is the right answer
- ❌ "Accuracy is 92%" without baseline or eval
- ❌ "RAG solves hallucination" — RAG reduces, doesn't remove; still need eval + abstention
- ❌ "Fine-tune the model" as a first move — usually RAG + better prompts win first
- ❌ "We add a vector DB" before outgrowing pgvector
- ❌ "The agent handles it" — without a policy engine, that's wishful thinking
- ❌ "Our LLM judge is reliable" — calibrated how often? against whom?
- ❌ Inventing tools, metrics, or your past results

---

## Three Things Katalon Is Hiring For (tied to this line)

Per Section 1 of `Katalon_Head_of_Data_Interview_Prep.md`:

1. **Builder-leader** — hands-on credible. *Demonstrated by:* naming a real RAG system and its failures.
2. **AI-readiness owner** — RAG, eval, governance. *Demonstrated by:* the retrieve-vs-generate split, the eval harness, the agent safety architecture.
3. **Cross-functional translator** — speak CFO / lawyer / engineer. *Demonstrated by:* framing cost and risk in business language.

🔵 **This qualification IS the "have you actually shipped AI" test. One real story beats five whiteboard answers.**

---

## Practice Log

| Date | Time | Mode | Self-score (1–4) | Notes |
|---|---|---|---|---|
| | | (cold / timed / peer) | | |
| | | | | |

---

## Linked Material

- **Main prep doc:** `Katalon_Head_of_Data_Interview_Prep.md` Section 9 (AI-ready platform + failure analysis)
- **Sister files:**
  - `ml-mlops-ai-platform-question-prep.md` (qualification 48 — the platform layer)
  - `ai-adoption-question-prep.md` (responsibility 5 — the adoption loop)
  - `governance-question-prep.md` (responsibility 3 — GDPR/CCPA + AI governance)
  - `example-question-prep.md` (template)
- **Stories bank:** Section 21 — find S4 (AI prototype → production)
- **Flashcards:** Section 23
- **Scoring rubric:** Section 20

---

## Checklist Before Walking In

- [ ] 90-second answer said aloud, no notes
- [ ] GenAI application spine (7 steps) said in 30 sec
- [ ] RAG vs not-RAG decision table in head
- [ ] Hybrid retrieval recipe (BM25 + vector + filter + optional rerank) ready
- [ ] Chunking table by content type
- [ ] Retrieve-vs-generate debugging framework ready
- [ ] Prompt injection defense layers (architectural, auth, tools, redaction, output, monitoring, recovery)
- [ ] Agent safety architecture (planner → policy → tools → confirmation → executor) ready
- [ ] "Function calling vs agents" answer ready
- [ ] LLM evaluation layers (retrieval / generation / product / reliability / safety)
- [ ] One real RAG/agent story (S4) rehearsed
- [ ] No invented tools, metrics, or your past results

---

## Closing Sentence (if asked "anything else?")

> GenAI is the easiest place to ship a demo and the hardest place to ship a product. The difference is the **discipline**: golden set before model, retrieval before generation, citations before answers, policy before tools, eval before promotion, rollback before regret. **RAG is a contract. Agents are a privilege. Both must be earned.**
