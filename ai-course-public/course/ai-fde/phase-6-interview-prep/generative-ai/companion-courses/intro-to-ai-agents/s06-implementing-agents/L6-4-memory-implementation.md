# L6.4: Memory implementation — the 3-tier production pattern

> **FDE framing in one line:** the 3-tier memory turns a stateless function into a stateful system. Short-term (in the prompt), long-term (in a vector DB), episodic (summarized past sessions). The implementation details that decide whether the agent remembers or forgets.

## The 3 things you'll learn

1. The 3 memory tiers: short-term (in the prompt), long-term (in a vector DB), episodic (summarized past sessions) — and what each tier is for.
2. The retrieval pattern: cosine similarity with dedup, recency bias, and the compose-prompt boundary. What the memory stores is what the model sees.
3. The memory cost-quality trade-off: more retrieval = better context = higher cost. The FDE picks the minimum retrieval that achieves the target accuracy.

## Concept

The agent's memory is what the model sees. The 3-tier memory is the production pattern: short-term in the prompt (the current conversation), long-term in a vector DB (facts the agent has accumulated), episodic in summaries (past sessions). **Each tier serves a different time horizon; the FDE composes them at the start of each agent run.**

The 3 memory tiers:

1. **Short-term (in the prompt).** The `messages` list — the current conversation, the current tool calls, the current observations. Bounded by the model's context window (200K tokens for GPT-5, 200K for Claude Sonnet 4.5, 1M for Gemini 2.5 Pro). The short-term memory is what the model sees on every step; the FDE's job is to keep it bounded (a 1M-token prompt is too expensive to send on every step).
2. **Long-term (in a vector DB).** The knowledge the agent has accumulated across runs — customer preferences, past decisions, domain facts. Stored as embeddings in Pinecone, Weaviate, Qdrant, or pgvector. Retrieved on demand via cosine similarity. The long-term memory is what the agent remembers across sessions.
3. **Episodic (summarized past sessions).** The summaries of past agent runs — "last week the customer asked about X, the agent did Y, the outcome was Z." Stored as a list of structured summaries. Retrieved when the customer returns with a related question. The episodic memory is what the agent remembers across months.

The retrieval pattern is the bridge between short-term and long-term:

1. **Embed the query.** Embed the current goal + last observation with the same embedding model used to embed the stored vectors.
2. **Cosine similarity search.** Retrieve the top-K vectors with cosine similarity > threshold (typically 0.7).
3. **Deduplication.** Drop near-duplicates (cosine similarity > 0.9 to each other). Without it, the top-K returns 5 copies of the same fact.
4. **Recency bias.** Weight more recent vectors higher. Without it, the retrieval returns the oldest matching fact, which is often stale.
5. **Compose the prompt.** Append the retrieved facts to the messages list, prefixed with a "retrieved context" header. The model sees the retrieved context as part of the system prompt.

The memory cost-quality trade-off: more retrieval = better context = higher cost. The FDE picks the minimum retrieval that achieves the target accuracy. The default: K=5 facts, threshold=0.7, dedup at 0.9, recency weight 0.3. A higher K (10 facts) improves accuracy 5% but doubles the prompt cost; a lower K (3 facts) cuts cost 40% but drops accuracy 10%.

## The pattern

The 3-tier memory as a class:

```python
import math
from collections import Counter
from typing import Callable

class MemoryStore:
    """The 3-tier memory: short-term + long-term + episodic."""

    def __init__(self, vector_db, embed_fn: Callable, episodic_log: list = None):
        self.short_term = []  # list of messages
        self.long_term = vector_db  # Pinecone / Weaviate / Qdrant / pgvector
        self.embed = embed_fn
        self.episodes = episodic_log or []  # list of structured summaries

    def retrieve(self, query: str, k: int = 5, threshold: float = 0.7) -> list[str]:
        """Retrieve top-K facts from long-term with dedup + recency bias."""
        query_vec = self.embed(query)
        raw = self.long_term.query(query_vec, top_k=k * 3)  # Over-fetch for dedup
        # Filter by threshold
        filtered = [r for r in raw if r.score >= threshold]
        # Dedup (drop near-duplicates)
        deduped = []
        for r in filtered:
            if all(cosine(r.embedding, d.embedding) < 0.9 for d in deduped):
                deduped.append(r)
        # Recency bias
        recency_weighted = sorted(deduped, key=lambda r: r.score * 0.7 + recency_score(r.timestamp) * 0.3, reverse=True)
        return [r.text for r in recency_weighted[:k]]

    def append_episode(self, summary: dict):
        """Append a structured summary to the episodic store."""
        self.episodes.append(summary)
        # Cap the episodic store at MAX_EPISODES (e.g., 1000)
        if len(self.episodes) > 1000:
            self.episodes = self.episodes[-1000:]

    def compose_prompt(self, goal: str, system_prompt: str) -> list[dict]:
        """Compose the short-term window: system + retrieved context + current conversation."""
        retrieved = self.retrieve(goal)
        episode_summary = self._summarize_recent_episodes(n=3)
        return [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"## Retrieved context (from long-term memory)\n{chr(10).join(retrieved)}"},
            {"role": "system", "content": f"## Recent episodes\n{episode_summary}"},
            {"role": "user", "content": goal},
        ]

    def _summarize_recent_episodes(self, n: int = 3) -> str:
        """Summarize the N most recent episodes."""
        recent = self.episodes[-n:]
        return "\n".join(f"- {ep['summary']}" for ep in recent)
```

The cosine similarity (production-grade):

```python
def cosine(a: dict, b: dict) -> float:
    """Cosine similarity between two sparse embeddings."""
    dot = sum(a.get(t, 0) * b.get(t, 0) for t in a)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    return dot / (mag_a * mag_b) if mag_a and mag_b else 0.0

def recency_score(timestamp: float, now: float = None) -> float:
    """Recency score: 1.0 for now, decaying exponentially. Half-life = 30 days."""
    now = now or time.time()
    age_days = (now - timestamp) / 86400
    return 0.5 ** (age_days / 30)
```

The pattern that wins interviews is the "3 tiers + compose-prompt + cost-quality" pattern. The candidate who says "the 3-tier memory is short-term (in the prompt, bounded by context window), long-term (in a vector DB, retrieved on demand with cosine + dedup + recency), episodic (summarized past sessions, retrieved when the customer returns). The compose-prompt function is the boundary: what the memory stores is what the model sees. The cost-quality trade-off: K=5, threshold=0.7, dedup at 0.9, recency weight 0.3. The wrong choice is to put the entire vector DB in the prompt (cost blowout). The wrong choice is to retrieve nothing (agent can't pursue multi-step goals). The right choice is the 3 tiers with on-demand retrieval" is the candidate who demonstrates the memory-mindset.

## Code or example

The PacificFreight memory implementation:

```python
PF_MEMORY = MemoryStore(
    vector_db=PineconeClient(index="pf-long-term"),
    embed_fn=openai_embed("text-embedding-3-small"),  # 1536-dim embeddings
    episodic_log=EpisodicLog(persist_path="episodes.jsonl"),  # 1000 most recent episodes
)

# At the start of a CS-drafter run:
def cs_drafter_with_memory(email: str, agent: SingleAgent) -> dict:
    # Compose the prompt with retrieved context + recent episodes
    messages = PF_MEMORY.compose_prompt(goal=email, system_prompt=CS_DRAFTER_SYSTEM_PROMPT)
    # ... run the agent loop with these messages
    # At the end: append the episode to episodic log
    PF_MEMORY.append_episode({
        "timestamp": time.time(),
        "customer_id": extract_customer_id(email),
        "summary": summarize_run(messages),
        "outcome": final_answer,
        "thumbs_up": None,  # Set later when Mei gives feedback
    })
```

The memory cost-quality curve:

```python
# K=3, threshold=0.7: 60% accuracy on multi-step tasks, 100 tokens retrieved, $0.001/turn
# K=5, threshold=0.7: 75% accuracy, 200 tokens retrieved, $0.002/turn
# K=10, threshold=0.7: 80% accuracy, 500 tokens retrieved, $0.005/turn
# K=20, threshold=0.7: 82% accuracy, 1000 tokens retrieved, $0.010/turn
# K=5, threshold=0.5: 70% accuracy (more noise), 350 tokens retrieved, $0.003/turn
# The default K=5, threshold=0.7 is the sweet spot: 75% accuracy at $0.002/turn.
```

The mid-run retrieval refresh (the 2026 production pattern):

```python
def run_agent_with_memory_refresh(goal: str, agent: SingleAgent, memory: MemoryStore) -> dict:
    """Run the agent. Refresh long-term memory every 3 turns."""
    messages = memory.compose_prompt(goal, agent.system_prompt)
    for turn in range(1, agent.max_turns + 1):
        if agent.cost.breached():
            return {"error": "cost_ceiling_breached"}
        output = agent.model.fn(messages)
        agent.cost.record(agent.model, len(str(messages)) // 4, len(output) // 4)
        messages.append({"role": "assistant", "content": output})
        step = parse_step(output)
        if step["type"] == "final":
            memory.append_episode(summarize_run(messages))
            return {"answer": step["answer"], "turns": turn}
        if step["type"] == "malformed":
            messages.append({"role": "tool", "content": json.dumps({"_ok": False, "_err": "malformed"})})
            continue
        result = agent.tools.call(step["tool"], step["args"])
        messages.append({"role": "tool", "content": json.dumps(result)})
        # Refresh long-term memory every 3 turns
        if turn % 3 == 0:
            retrieved = memory.retrieve(messages[-1]["content"])
            messages.append({"role": "system", "content": f"## Refreshed context\n{chr(10).join(retrieved)}"})
    return {"error": "max_turns_reached"}
```

## Production addendum

The memory implementation question is the answer to "how do you implement agent memory." The 60-second script:

> "3 tiers. Short-term: the messages list in the prompt, bounded by the context window. Long-term: a vector DB (Pinecone, Weaviate, Qdrant, pgvector) with cosine retrieval + dedup + recency bias. Episodic: structured summaries of past sessions. The compose-prompt function is the boundary: what the memory stores is what the model sees. **The cost-quality trade-off: K=5 facts, threshold=0.7, dedup at 0.9, recency weight 0.3 is the default.** Refresh long-term every 3 turns. The wrong choice is to put the entire vector DB in the prompt (cost blowout). The wrong choice is to retrieve nothing (agent can't pursue multi-step goals). The right choice is the 3 tiers with on-demand retrieval and mid-run refresh."

This is the difference between a candidate who says "the agent has memory" and a candidate who says "3 tiers (short-term + long-term + episodic), compose-prompt boundary, K=5 with dedup + recency, mid-run refresh every 3 turns." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-8-6-agent-memory.py` — the full 3-tier memory with cosine retrieval.
- **Reference implementation**: `course/hardcode/level-5-agentic-workflows/10-multi-agent-orchestrator.py` — production-grade memory with pgvector + Redis.
- **Phase 2 module**: `course/ai-fde/phase-2-core-build/service/retrieval_v2.py` — the hybrid retrieval (BM25 + dense + RRF) backing the long-term memory.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — the shared state object as the cross-agent memory.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — memory as a system design pattern.

## The 3 questions this lecture preps you for

1. **"How do you implement agent memory?"** Answer: 3 tiers — short-term (messages list in the prompt, bounded by context window), long-term (vector DB with cosine + dedup + recency), episodic (structured summaries). The compose-prompt function is the boundary; what the memory stores is what the model sees.
2. **"What is the retrieval pattern that ties short-term to long-term?"** Answer: 5 steps — embed the query, cosine similarity search with threshold, dedup near-duplicates, recency bias, compose the prompt. The default K=5, threshold=0.7, dedup at 0.9, recency weight 0.3 is the production sweet spot.
3. **"What is the memory cost-quality trade-off?"** Answer: more retrieval = better context = higher cost. K=3 is 60% accuracy at $0.001/turn; K=5 is 75% at $0.002; K=10 is 80% at $0.005. The default K=5 is the sweet spot. The FDE tunes K based on the eval set; the cost is the constraint; the accuracy is the goal.

## Read next

`L6-5-guardrails-and-cost-control.md` — the 5th lecture. The 5 production guardrails: loop detector, schema validator, cost ceiling, idempotency, audit log. The 3-level cost ceiling: per-run, per-tenant, per-process. The cost as the first-class metric.