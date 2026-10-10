# L2.3: The memory layer

> **FDE framing in one line:** the memory layer is what makes the agent multi-step instead of single-step. Without it, the agent forgets the first observation by the time it makes the 10th call; with it, the agent can pursue a goal across 100 steps and 1M tokens of context.

## In 60 seconds

> "Three tiers. Short-term: the messages list, bounded by the context window. Long-term: a vector DB, retrieved on demand via cosine similarity with dedup and recency bias. Episodic: structured summaries of past sessions, retrieved when the customer returns. The agent loop composes them: retrieve long-term + episodic at the start of the run, append retrieved context to the system prompt, refresh retrieval every 3 turns. **What the memory layer stores is what the model sees; the contract is enforced by what the retrieval returns.** The wrong choice is to put the entire vector DB in the prompt (cost blowout). The wrong choice is to retrieve nothing (agent can't pursue multi-step goals). The right choice is retrieval on demand, with the short-term window bounded and the retrieval relevant."

**The wrong choice is to read past this block.** The right choice is to recite the 60-second script before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. The three tiers of agent memory: short-term (in the prompt), long-term (in a vector DB), episodic (summarized past sessions).
2. The retrieval pattern that ties short-term to long-term: cosine similarity, deduplication, and recency bias.
3. The "memory is the prompt boundary" pattern: what the memory layer stores is what the model sees; the boundary is the agent's contract with the model.

## Concept

The LLM has no memory between calls. Each call is independent; the model has no memory of the last call unless the caller puts the last call's output in the next call's input. The agent loop is the mechanism that puts last call's output in next call's input: the `messages` list. **The messages list is the agent's memory.** Without it, the agent is a stateless function (`answer = LLM(prompt)`); with it, the agent is a stateful loop.

The three tiers of memory correspond to three time horizons:

1. **Short-term (in the prompt).** The `messages` list — the current conversation, the current tool calls, the current observations. Bounded by the model's context window (200K tokens for GPT-5, 200K for Claude Sonnet 4.5, 1M for Gemini 2.5 Pro). The short-term memory is what the model sees on every step. The FDE's job is to keep it bounded: a 1M-token prompt is too expensive to send on every step, and most of the content is not relevant.
2. **Long-term (in a vector DB).** The knowledge the agent has accumulated across runs — customer preferences, past decisions, domain facts. Stored as embeddings in Pinecone, Weaviate, Qdrant, or pgvector. Retrieved on demand via cosine similarity. The long-term memory is what the agent remembers across sessions. The FDE's job is to keep it relevant: a 1M-vector DB is too expensive to search on every step, and most vectors are not relevant to the current task.
3. **Episodic (summarized past sessions).** The summaries of past agent runs — "last week the customer asked about X, the agent did Y, the outcome was Z." Stored as a list of structured summaries. Retrieved when the customer returns with a related question. The episodic memory is what the agent remembers across months. The FDE's job is to keep it concise: a 10K-token episodic dump is too expensive to include in every prompt, and most episodes are not relevant to the current task.

The three tiers compose. A typical agent step looks like:

1. **Retrieve from long-term** — query the vector DB with the current goal + last observation; retrieve the top-K most similar facts (K=5-10).
2. **Retrieve from episodic** — query the episodic store with the current customer + goal; retrieve the top-3 most relevant past sessions.
3. **Compose short-term** — append the retrieved facts and episode summaries to the messages list, prefixed with a "retrieved context" header.
4. **LLM call** — the model sees the short-term window: system prompt + retrieved context + current conversation + tool calls + observations.
5. **Update long-term** — at the end of the run, write the new facts (decisions, preferences, outcomes) to the vector DB.
6. **Update episodic** — at the end of the run, summarize the session and append to the episodic store.

The retrieval pattern that ties short-term to long-term has three components:

1. **Cosine similarity.** Embed the query (current goal + last observation) with the same embedding model used to embed the stored vectors. Retrieve the top-K vectors with cosine similarity > threshold (typically 0.7). The threshold filters noise: a 0.5 similarity is too low (false positives), a 0.9 is too high (false negatives).
2. **Deduplication.** If two retrieved vectors have cosine similarity > 0.9 to each other, drop one. Without it, the top-K often returns 5 copies of the same fact. The dedup is the difference between "5 facts" and "1 fact repeated 5 times."
3. **Recency bias.** Weight more recent vectors higher. Without it, the retrieval returns the oldest matching fact, which is often stale. The recency bias can be a linear weight (newer = higher score) or a recency cutoff (drop vectors older than 90 days).

The "memory is the prompt boundary" pattern is the recognition that **what the memory layer stores is what the model sees**. The model has no other input. If a fact is not in the short-term window, the model does not know it. If a fact is in the vector DB but not retrieved, the model does not know it. If a fact is in the episodic store but the summary is bad, the model does not know it correctly. **The memory layer is the agent's contract with the model; the contract is enforced by what the retrieval returns.**

## The pattern

The three-tier memory as a class:

```python
class MemoryStore:
    """Three-tier memory: short-term window + long-term vector + episodic summaries."""

    def __init__(self, vector_db, embedding_fn):
        self.short_term = []        # list of messages
        self.long_term  = vector_db # Pinecone / Weaviate / pgvector
        self.episodes   = []        # list of structured summaries
        self.embed      = embedding_fn

    def retrieve(self, query: str, k: int = 5) -> list[str]:
        """Retrieve top-K facts from long-term, dedup, recency-bias."""
        query_vec = self.embed(query)
        raw = self.long_term.query(query_vec, top_k=k * 3)  # over-fetch for dedup
        deduped = self._dedup(raw, threshold=0.9)
        recency_weighted = self._recency_bias(deduped)
        return [r.text for r in recency_weighted[:k]]

    def append_episode(self, summary: dict):
        """Append a structured summary to the episodic store."""
        self.episodes.append(summary)
        # Cap the episodic store at MAX_EPISODES (e.g., 1000)
        if len(self.episodes) > MAX_EPISODES:
            self.episodes = self.episodes[-MAX_EPISODES:]

    def compose_prompt(self, goal: str) -> list[dict]:
        """Compose the short-term window: system + retrieved context + current conversation."""
        retrieved = self.retrieve(goal)
        episode_summary = self._summarize_recent_episodes()
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"Retrieved context: {retrieved}"},
            {"role": "system", "content": f"Recent episodes: {episode_summary}"},
            {"role": "user",   "content": goal},
        ]
```

The pattern that wins interviews is the "memory as the prompt boundary" pattern. The candidate who says "the memory layer is what the model sees; the retrieval returns what the model knows; the short-term window is what the model reasons over; the long-term vector DB is what the agent remembers; the episodic summary is what the agent carries across sessions" is the candidate who demonstrates the memory-as-contract mindset.

## Code or example

A minimal three-tier memory, stdlib-only (no real vector DB; bag-of-words cosine similarity):

```python
import math
from collections import Counter

VOCAB = set()  # populated at startup from the long-term corpus

def embed(text: str) -> dict[str, float]:
    """Bag-of-words embedding. Vocabulary built from the long-term corpus."""
    tokens = text.lower().split()
    counts = Counter(t for t in tokens if t in VOCAB)
    total = sum(counts.values()) or 1
    return {t: c / total for t, c in counts.items()}

def cosine(a: dict, b: dict) -> float:
    """Cosine similarity between two sparse embeddings."""
    dot = sum(a.get(t, 0) * b.get(t, 0) for t in a)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    return dot / (mag_a * mag_b) if mag_a and mag_b else 0.0

class LongTermMemory:
    """A minimal long-term memory with cosine retrieval + dedup + recency bias."""

    def __init__(self):
        self.vectors: list[tuple[str, dict, float]] = []  # (text, embedding, timestamp)

    def add(self, text: str):
        self.vectors.append((text, embed(text), time.time()))

    def query(self, query_vec: dict, k: int = 5, threshold: float = 0.3) -> list[tuple[str, float]]:
        scored = [(t, cosine(query_vec, v), ts) for t, v, ts in self.vectors]
        scored = [(t, s, ts) for t, s, ts in scored if s >= threshold]
        scored.sort(key=lambda x: (x[1] * 0.7 + recency_score(x[2]) * 0.3), reverse=True)
        # Dedup: drop near-duplicates
        deduped = []
        for t, s, ts in scored:
            if all(cosine(embed(t), embed(dt)) < 0.9 for dt, _, _ in deduped):
                deduped.append((t, s, ts))
            if len(deduped) >= k:
                break
        return deduped
```

The agent loop with memory:

```python
def run_agent(goal: str, memory: MemoryStore, llm, max_turns: int = 10):
    """Agent loop with three-tier memory."""
    messages = memory.compose_prompt(goal)
    for turn in range(1, max_turns + 1):
        output = llm(messages)
        messages.append({"role": "assistant", "content": output})
        step = parse_step(output)
        if step["type"] == "final":
            memory.append_episode(summarize(messages))
            return step["answer"]
        obs = call_tool(step["tool"], step["args"])
        messages.append({"role": "tool", "content": str(obs)})
        # Mid-run retrieval: refresh long-term context if the conversation drifts
        if turn % 3 == 0:
            retrieved = memory.retrieve(messages[-1]["content"])
            messages.append({"role": "system", "content": f"Refreshed context: {retrieved}"})
    return "max turns reached"
```

## Production addendum

The memory layer is the answer to the "how does the agent remember across steps" interview question. The 60-second script:

> "Three tiers. Short-term: the messages list, bounded by the context window. Long-term: a vector DB, retrieved on demand via cosine similarity with dedup and recency bias. Episodic: structured summaries of past sessions, retrieved when the customer returns. The agent loop composes them: retrieve long-term + episodic at the start of the run, append retrieved context to the system prompt, refresh retrieval every 3 turns. **What the memory layer stores is what the model sees; the contract is enforced by what the retrieval returns.** The wrong choice is to put the entire vector DB in the prompt (cost blowout). The wrong choice is to retrieve nothing (agent can't pursue multi-step goals). The right choice is retrieval on demand, with the short-term window bounded and the retrieval relevant."

This 60-second pitch is the difference between a candidate who says "the agent has memory" and a candidate who says "three tiers, composed by the agent loop, bounded by the short-term window, refreshed on demand." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-8-6-agent-memory.py` — the full three-tier memory with `MemoryStore`.
- **Reference implementation**: `course/hardcode/level-5-agentic-workflows/10-multi-agent-orchestrator.py` — production-grade memory with pgvector + Redis + Anthropic.
- **Phase 2 module**: `course/ai-fde/phase-2-core-build/service/retrieval_v2.py` — the hybrid retrieval pattern (BM25 + dense + RRF) that backs the long-term memory.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — the shared state object as the cross-agent memory.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — the memory layer as a system design pattern.

## The 3 questions this lecture preps you for

1. **"How does the agent remember across steps?"** Answer: three tiers. Short-term = messages list in the prompt, bounded by the context window. Long-term = vector DB with cosine retrieval + dedup + recency bias. Episodic = structured summaries of past sessions. The agent loop composes them at the start of the run and refreshes long-term every 3 turns.
2. **"What is the difference between short-term and long-term memory?"** Answer: short-term is the prompt itself (the model sees it on every step); long-term is the vector DB (the model sees it only when retrieved). Short-term is bounded by the context window (200K tokens); long-term is bounded by the storage budget (10M+ vectors). Short-term is fast (no retrieval); long-term is slow (cosine similarity over millions of vectors).
3. **"What is the memory-as-prompt-boundary pattern?"** Answer: what the memory layer stores is what the model sees. If a fact is not retrieved, the model does not know it. If a fact is in the prompt but the model is distracted by the conversation, the model may not use it. **The memory layer is the agent's contract with the model; the contract is enforced by what the retrieval returns.**

## Read next

`L2-4-the-cost-ceiling.md` — the fourth ingredient and the first guardrail. The cost ceiling is what keeps a confused agent from spending the customer's monthly budget in a single run.