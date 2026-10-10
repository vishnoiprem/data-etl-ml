# 52. LangChain

- **Role:** AI Engineer / Software Engineer (LLM Framework / Agent Infrastructure)
- **Tech stack:** Python, TypeScript, LangChain/LangGraph, React, FastAPI, Postgres, Redis, OpenAI/Anthropic APIs, vector DBs (Pinecone, Weaviate, Qdrant), LangSmith
- **Comp band:** $200K-$420K (well-funded, AI infra)
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation | 1 week | ~50% advance |
| 2. **Technical phone screen** | 60-90 min coding + LLM app design | 1-2 weeks | ~35% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, LLM deep-dive, behavioral | 1-2 days | ~30% advance |
| 4. **Hiring committee** | Panel review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Verbal + written | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Why LangChain?"
**Answer:** Three-bet: (1) LangChain is the most widely-adopted LLM framework — you've shipped with it, you understand the abstraction choices, (2) LangGraph (stateful agents) is a serious product beyond just chains, (3) LangSmith (observability) is the cash cow that funds the OSS.
**Tip:** Mention you've actually used LangChain + LangSmith in production. Negative signal: never having run `langchain` CLI.

### Q1.2: "Tell me about an LLM app you built"
**Answer:** Walk through a real app: problem statement, architecture (chains, agents, retrieval, tools), model choices, eval approach, deployment. Be specific. LangChain wants practitioners, not theorists.

## Stage 2: Technical phone screen

### Q2.1: Coding — "Implement a basic agent loop (ReAct)"
**Answer:**
```python
def react_agent(llm_call, tools, max_iters=5):
    history = []
    for _ in range(max_iters):
        prompt = render_react_prompt(history, tools)
        response = llm_call(prompt)
        thought, action, action_input = parse_response(response)
        history.append((thought, action, action_input))
        if action == "Finish":
            return action_input
        obs = tools[action](**action_input)
        history.append(("Observation", obs))
    return None
```
**Tip:** Real LangChain agents are richer (tool selection, error handling, retries, output parsing). Mention LangGraph for production.

### Q2.2: LLM — "How would you build a RAG pipeline that handles 1M documents?"
**Answer:** Three pillars: (1) **chunking** with overlap + metadata, (2) **embeddings** (batched, async, parallel), (3) **retrieval** (vector + BM25 + reranker). Discuss: chunk size tradeoff, embedding model selection, hybrid search, eval set, latency budget.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement a sliding-window chunker.
- **Q3.1.2:** Build a simple agent loop (above).
- **Q3.1.3:** Implement BM25 from scratch (search relevance).

### Round 3.2: System design
- **Q3.2.1:** "Design LangSmith — observability for LLM apps." Talk: ingestion (SDK), storage (run/span tree, prompts, completions, tool calls, retrievals), query (trace viewer, feedback, datasets), cost tracking.
- **Q3.2.2:** "Design a multi-tenant LLM app platform." Discuss: per-tenant API keys, rate limits, model routing, fallback chains, observability, eval suite.

### Round 3.3: LLM deep-dive
- **Q3.3.1:** "How do you evaluate a RAG system end-to-end?" Discuss: retrieval metrics (recall@k, MRR), answer metrics (faithfulness, relevance, BLEU/ROUGE), LLM-as-judge, human eval, A/B testing.
- **Q3.3.2:** "How do you build an agent that uses tools reliably?" Talk: function calling + output parsing, error handling, retry strategies, human-in-the-loop, eval suite for tool-use accuracy.

### Round 3.4: Behavioral
- **Q3.4.1:** "Tell me about a production LLM app you took from prototype to scale."
- **Q3.4.2:** "Why are frameworks valuable? What would you build differently?"

## Stage 4: Hiring committee
LangChain is a hot AI infra company. The committee looks for: production LLM experience (not just demos), framework/infrastructure chops (you should be opinionated about abstractions), and a builder mentality. Red flags: never having built a real LLM app, weak on retrieval eval, never having used LangSmith.

## Stage 5: Offer
Base is at the high end ($200K-$300K), equity is meaningful (private, growing fast, raised Series B at $1B+ valuation). Negotiation: equity refreshers + sign-on.

## Tips for the LangChain loop
1. **Build a real LangChain + LangGraph app before the interview** — even a small RAG project counts.
2. **Use LangSmith** — set up tracing, run an eval, talk about it.
3. **Brute-force agent design** — ReAct, function calling, plan-and-execute, multi-agent patterns.
4. **Have opinions on chunking, retrieval, eval** — these are daily bread-and-butter.
5. **Be ready to compare LangChain vs LlamaIndex vs Haystack** — they'll ask.
6. **Practice the "design observability for LLM apps" round** — LangSmith is their biggest product.
7. **Show your GitHub** — they love seeing OSS contributions.

## Real candidate report
> "Phone screen was agent loop coding + RAG design. Onsite had a tough 'design LangSmith' round — they really pushed on the trace data model. The behavioral round was easier than expected. Offer: $240K + 0.03% equity, signed in 4 days." — Levels.fyi, 2025

## Sources
- [LangChain careers](https://www.langchain.com/careers)
- [LangChain blog](https://blog.langchain.dev)
- [LangSmith docs](https://docs.smith.langchain.com)
- [LangChain GitHub](https://github.com/langchain-ai/langchain)
- [LangChain Glassdoor](https://www.glassdoor.com/Interview/LangChain-Interview-Questions-E3509100.htm)
