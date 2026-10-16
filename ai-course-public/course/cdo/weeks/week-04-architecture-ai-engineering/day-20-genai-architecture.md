# Lesson 20: GenAI architecture

> **Week 4 · Day 20 · 90 min**
> **Deliverable:** The GenAI architecture — RAG, agents, evaluation, guardrails.

## 🎯 Architect Level
Staff.

## 🧠 Concept

GenAI architecture has 4 components that traditional ML doesn't have:

1. **Retrieval (RAG).** The model is augmented with context from a vector store or search index. The vector store is a new architectural primitive.
2. **Agents.** The model can call tools, run code, query APIs. The orchestration layer is the new platform.
3. **Evaluation.** The model output is graded against ground truth or human preference. The eval harness is the new test suite.
4. **Guardrails.** The model output is filtered for safety, PII, brand, accuracy. The guardrail is the new WAF.

The reference architecture:

```
User → App → [Guardrail in] → Agent / Chain
  → LLM (OpenAI / Anthropic / OSS) ← Prompt + Context
  → Tool calls (search, code, API) → External systems
  → [Eval + Guardrail out] → Response
```

The single biggest mistake is to **start with agents before you have a working RAG**. Agents compound every error in the RAG layer. If the RAG is wrong 30% of the time, the agent is wrong 60%+ of the time. Sequence: RAG first, agents second.

The second biggest mistake is to **skip evaluation**. "It looks good" is not a metric. The eval harness must be in place before the first user touches the system. Eval dimensions: faithfulness, relevance, harmlessness, task completion, latency, cost.

The third biggest mistake is to **not have guardrails**. The model will hallucinate. The model will leak PII. The model will produce harmful content. The guardrail is the difference between a demo and a product.

The build-vs-buy shape:
- **LLM**: rent (OpenAI, Anthropic, Cohere, OSS) — don't fine-tune for the first 12 months
- **Vector store**: buy (Pinecone, Weaviate, Qdrant, pgvector)
- **Orchestration**: build (LangChain, LlamaIndex, custom) — but standardize the patterns
- **Eval**: build (custom harness with vendor OSS) — this is your IP
- **Guardrails**: build (in-house) + rent (vendor) — defense in depth

## 🛠️ Build It

**Spec:** Design the GenAI architecture for the retailer's document intelligence use case (RAG over product specs, contracts, ops manuals).

**Acceptance:**
- 4 components (retrieval, agent, eval, guardrail) named
- 1-2 technologies per component
- Build-vs-buy per component
- Eval dimensions named
- 1 paragraph on the "why" for the most-debated choice (e.g., which LLM, which vector store)

**Starter:** Use the `apex-rag-omni` work in this repo as a live reference. The user has built a RAG system with FastAPI + pgvector + OpenAI + Anthropic. Walk the interviewer through it.

**Solution (GenAI architecture, abridged):**

| Component | Choice | Why | Build vs. buy |
|---|---|---|---|
| LLM | OpenAI + Anthropic (multi-model) | Vendor diversification; routing by task | Rent |
| Vector store | pgvector (start), Pinecone (scale) | Start with Postgres, scale out | Buy + build |
| Orchestration | LangChain (start), custom (scale) | Open standards; replace per use case | Build |
| Eval | Custom harness (faithfulness, relevance, latency) | IP lives here | Build |
| Guardrails | LLM-as-judge + keyword + PII filter | Defense in depth | Build + buy |

**Eval dimensions:** faithfulness (1-5), relevance (1-5), latency p50/p95, cost per query, refusal rate. Run on golden set of 200 Q/A pairs, refresh weekly.

## 🏛️ Architect Notes

- **Trade-off:** Multi-model vs. single model. Default: multi-model. Different tasks need different models. Don't put all your tokens on one vendor.
- **Capacity / cost:** A GenAI platform costs $XM in infra + 4-6 engineers. Below that, the platform is a demo.
- **When NOT to use:** Don't fine-tune before you have a working RAG. Don't build agents before you have eval. Don't ship without guardrails.
- **Production checklist:**
  - [ ] 4 components (RAG, agent, eval, guardrail) named
  - [ ] 1-2 technologies per component
  - [ ] Build-vs-buy per component
  - [ ] Eval dimensions named
  - [ ] Most-debated choice justified
  - [ ] Cost per query estimated

## 🌙 Reflect

- Which GenAI use case is your strongest "we shipped it in production"? Pre-write the answer.
- Which guardrail would the CTO push hardest on?
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Case Study 4 — The 10M-Customer Platform.