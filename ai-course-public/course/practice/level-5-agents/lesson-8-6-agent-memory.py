"""
Lesson 8.6: Memory in Agents
====================================
Agent with extract-store-retrieve memory loop.

Run:  python lesson-8-6-agent-memory.py

No external API keys required -- all LLM/DB calls are mocked.

Builds on lesson-8-2 (ReAct loop) and lesson-8-5 (tool catalog).
Lesson 8.6 is about *memory* -- the difference between an agent
that answers one question and an agent that knows the user.

Three memory tiers (per the .md spec):
  1. Short-term -- the current conversation (kept in the prompt).
  2. Long-term  -- facts about the user (preferences, role, location).
                  Stored in a vector DB; retrieved by similarity.
  3. Episodic   -- summaries of past interactions.
                  Stored as (timestamp, summary) pairs.
"""


# =============================================================================
# CONFIG -- All magic numbers live here
# =============================================================================

LESSON_NUMBER = "8.6"
LESSON_TITLE = "Memory in Agents"
DEFAULT_MODEL = "gpt-5-mini"  # 2026-current cheap+smart; mock used for the demo

# Pricing per 1M tokens, 2026-current (per OpenAI, Anthropic, Google public pricing, Q4 2026)
PRICING = {
    "gpt-5":              {"input": 2.50,  "output": 10.00},
    "gpt-5-mini":         {"input": 0.15,  "output": 0.60},
    "claude-sonnet-4.5":  {"input": 3.00,  "output": 15.00},
    "claude-haiku-4.5":   {"input": 0.80,  "output": 4.00},
    "gemini-2.5-pro":     {"input": 1.25,  "output": 5.00},
    "gemini-2.5-flash":   {"input": 0.075, "output": 0.30},
    "llama-4-70b-self":   {"input": 0.10,  "output": 0.10},
}

# How many long-term memories to inject into each prompt.
TOP_K_MEMORIES = 3
# How many episodic summaries to inject.
TOP_K_EPISODES = 2
# How many conversation turns to keep in the short-term window.
SHORT_TERM_WINDOW = 6
# Confidence floor for storing an extracted fact. Below this, the
# extractor said "not sure," so we drop the fact rather than pollute
# the long-term store with low-quality signals.
MIN_CONFIDENCE = 0.5


# =============================================================================
# MOCK EMBEDDINGS -- deterministic bag-of-words over a fixed vocabulary
# =============================================================================
# Real impl: OpenAI text-embedding-3-small ($0.02/1M tokens), or
# a local model (bge-small, e5-small) via sentence-transformers.
# We avoid any external dep: a stable hash-bucket embedding is enough
# to demonstrate the extract-store-retrieve loop.

import hashlib
import math
import re

VOCAB = [
    "python", "javascript", "rust", "go", "java", "typescript",
    "berlin", "singapore", "tokyo", "london", "san francisco", "new york",
    "ml", "ai", "llm", "rag", "agent", "finetune", "embedding",
    "fastapi", "django", "flask", "react", "next", "vue",
    "data", "pipeline", "etl", "warehouse", "lake", "lakehouse",
    "startup", "enterprise", "saas", "consulting", "fde",
    "morning", "evening", "night", "weekend",
    "coffee", "tea", "vegetarian", "vegan", "allergies",
]
_VOCAB_INDEX = {w: i for i, w in enumerate(VOCAB)}
_EMBED_DIM = len(VOCAB)

def mock_embed(text: str) -> list[float]:
    """Deterministic embedding: a sparse vector with 1.0 for each vocab word present.

    The function is intentionally a bag-of-words rather than a real embedding.
    It is enough to demonstrate the loop; replace with a real embedder in prod.
    """
    text = text.lower()
    vec = [0.0] * _EMBED_DIM
    for word, idx in _VOCAB_INDEX.items():
        if word in text:
            vec[idx] = 1.0
    # L2 normalize so cosine similarity is a clean dot product
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]

def cosine_similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


# =============================================================================
# MEMORY STORES -- the 3 tiers
# =============================================================================

from dataclasses import dataclass, field
from typing import Optional
import time

@dataclass
class LongTermMemory:
    """A fact about the user, stored with its embedding for retrieval."""
    fact_id: str
    text: str
    embedding: list[float]
    user_id: str
    created_at: float
    confidence: float
    source_turn: int  # which turn of the conversation extracted this
    tags: list[str] = field(default_factory=list)

@dataclass
class Episode:
    """A summary of a past interaction (or current conversation so far)."""
    episode_id: str
    summary: str
    user_id: str
    created_at: float
    turn_count: int

class MemoryStore:
    """In-memory implementation of the 3-tier memory model.

    In production:
      - Short-term  -> the prompt itself (no separate store).
      - Long-term   -> a vector DB (Qdrant, Weaviate, pgvector).
      - Episodic    -> Postgres or a KV store.
    The interface here is what matters: add, query, summarize.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.short_term: list[dict] = []  # role/content messages
        self.long_term: list[LongTermMemory] = []
        self.episodes: list[Episode] = []

    # -- short-term --------------------------------------------------------
    def add_to_short_term(self, role: str, content: str) -> None:
        self.short_term.append({"role": role, "content": content})
        # Trim to window
        if len(self.short_term) > SHORT_TERM_WINDOW * 2:
            self.short_term = self.short_term[-SHORT_TERM_WINDOW * 2:]

    def get_short_term(self) -> list[dict]:
        return list(self.short_term)

    # -- long-term ---------------------------------------------------------
    def add_to_long_term(self, text: str, *, turn: int, confidence: float,
                          tags: Optional[list[str]] = None) -> Optional[LongTermMemory]:
        if confidence < MIN_CONFIDENCE:
            return None
        fact_id = hashlib.sha256(f"{self.user_id}|{text}|{time.time()}".encode()).hexdigest()[:12]
        mem = LongTermMemory(
            fact_id=fact_id, text=text, embedding=mock_embed(text),
            user_id=self.user_id, created_at=time.time(),
            confidence=confidence, source_turn=turn, tags=tags or [],
        )
        # Dedup: don't store a near-duplicate of an existing fact
        for existing in self.long_term:
            if cosine_similarity(existing.embedding, mem.embedding) > 0.9:
                return existing
        self.long_term.append(mem)
        return mem

    def query_long_term(self, query: str, top_k: int = TOP_K_MEMORIES) -> list[LongTermMemory]:
        if not self.long_term:
            return []
        qvec = mock_embed(query)
        scored = [(cosine_similarity(m.embedding, qvec), m) for m in self.long_term]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:top_k] if _ > 0]

    # -- episodic ----------------------------------------------------------
    def add_episode(self, summary: str, turn_count: int) -> Episode:
        episode_id = hashlib.sha256(f"{self.user_id}|{summary}|{time.time()}".encode()).hexdigest()[:12]
        ep = Episode(episode_id=episode_id, summary=summary, user_id=self.user_id,
                     created_at=time.time(), turn_count=turn_count)
        self.episodes.append(ep)
        return ep

    def get_recent_episodes(self, top_k: int = TOP_K_EPISODES) -> list[Episode]:
        return list(self.episodes[-top_k:])


# =============================================================================
# MOCK LLM -- extracts facts + generates a response
# =============================================================================

def mock_llm_extract_facts(user_message: str) -> list[dict]:
    """Mock fact extractor. Returns [{"text": str, "confidence": float, "tags": [...]}, ...].

    Real impl: a single LLM call with a structured-output prompt
    ("extract 1-3 durable facts about the user from this message").
    For the demo, we use simple pattern matches.
    """
    msg = user_message.lower()
    facts = []
    # Programming language
    for lang in ("python", "javascript", "rust", "go", "java", "typescript"):
        if lang in msg:
            facts.append({"text": f"user works with {lang}", "confidence": 0.9, "tags": ["language"]})
            break
    # Location
    for city in ("berlin", "singapore", "tokyo", "london", "san francisco", "new york"):
        if city in msg:
            facts.append({"text": f"user is in {city}", "confidence": 0.85, "tags": ["location"]})
            break
    # Domain
    for domain in ("ml", "ai", "llm", "rag", "agent", "etl", "data", "saas"):
        if re.search(rf"\b{domain}\b", msg):
            facts.append({"text": f"user works in {domain}", "confidence": 0.75, "tags": ["domain"]})
            break
    # Dietary / preferences
    for pref in ("vegetarian", "vegan", "coffee", "tea"):
        if pref in msg:
            facts.append({"text": f"user prefers {pref}", "confidence": 0.7, "tags": ["preference"]})
            break
    return facts

def mock_llm_respond(user_message: str, memories: list[LongTermMemory],
                     episodes: list[Episode], short_term: list[dict]) -> str:
    """Mock responder. Echoes the user + uses the retrieved memories to 'remember' them.

    Real impl: an LLM call with the system prompt containing the
    short-term window + the top-K long-term memories + the recent
    episodes. We return a templated response that visibly uses the
    memory so the demo can show "I remember you said X."
    """
    memory_lines = [f"- {m.text}" for m in memories]
    ep_lines = [f"- (past) {e.summary}" for e in episodes]
    # The response template intentionally references the memories
    mem_blurb = "; ".join(m.text.replace("user ", "you ") for m in memories) or "no prior context"
    return f"[uses memory: {mem_blurb}] Got it. You said: {user_message!r}"


# =============================================================================
# THE AGENT -- extract-store-retrieve loop
# =============================================================================

def run_turn(store: MemoryStore, user_message: str, turn: int) -> dict:
    """Run one turn of the memory-augmented agent.

    Loop:
      1. RETRIEVE: query long-term + episodic memory with the user message.
      2. RESPOND:  call the LLM with short-term + memories + user message.
      3. EXTRACT:  pull facts from the user message.
      4. STORE:    add the new facts to long-term memory.
      5. UPDATE:   append the turn to short-term memory.

    Returns a dict with the response, the memories that were used,
    and the facts that were stored -- the observability artifact.
    """
    # 1. RETRIEVE
    used_memories = store.query_long_term(user_message)
    recent_episodes = store.get_recent_episodes()
    # 2. RESPOND
    response = mock_llm_respond(user_message, used_memories, recent_episodes, store.get_short_term())
    # 3. EXTRACT
    new_facts = mock_llm_extract_facts(user_message)
    # 4. STORE
    stored = []
    for fact in new_facts:
        m = store.add_to_long_term(fact["text"], turn=turn, confidence=fact["confidence"], tags=fact["tags"])
        if m:
            stored.append(m)
    # 5. UPDATE
    store.add_to_short_term("user", user_message)
    store.add_to_short_term("assistant", response)
    return {
        "turn":      turn,
        "user":      user_message,
        "response":  response,
        "memories_used":   [m.text for m in used_memories],
        "facts_extracted": [f["text"] for f in new_facts],
        "facts_stored":    [m.text for m in stored],
    }


# =============================================================================
# DEMO -- 5-turn conversation, watch the memory grow
# =============================================================================

CONVERSATION = [
    "Hi, I'm a Python developer in Berlin working on ML pipelines.",
    "I prefer coffee and I'm vegetarian.",
    "I'm building a RAG system for a SaaS startup.",
    "Can you help me with a Python question about my Berlin office?",
    "What do you remember about my work with RAG and SaaS?",
]

def demo():
    print("=" * 70)
    print(f"  LESSON {LESSON_NUMBER}: {LESSON_TITLE}")
    print("=" * 70)
    print()
    print("  Three memory tiers, one extract-store-retrieve loop per turn.")
    print("  Short-term -> in-prompt window.  Long-term -> cosine>0.9 deduped vector.")
    print("  Episodic   -> append-only summary, rolled at session boundary.")
    print()

    store = MemoryStore(user_id="USR-DEMO")
    for i, msg in enumerate(CONVERSATION, start=1):
        result = run_turn(store, msg, turn=i)
        print(f"  Turn {i}: {msg!r}")
        print(f"    Retrieved: {result['memories_used'] or '(none yet)'}")
        print(f"    Stored:    {result['facts_stored'] or '(nothing new)'}")
        print(f"    Response:  {result['response']}")
        print()

    # After the conversation, summarize it as an episode
    summary = "User introduced themselves as a Python dev in Berlin working on ML/RAG for a SaaS startup; vegetarian, prefers coffee."
    store.add_episode(summary, turn_count=len(CONVERSATION))
    print(f"  Episode rolled: {summary[:80]}...")
    print()

    # Inspect the final state
    print("  Final memory state:")
    print(f"    Short-term messages: {len(store.short_term)} (window: {SHORT_TERM_WINDOW*2})")
    print(f"    Long-term facts:     {len(store.long_term)}")
    for m in store.long_term:
        print(f"      - {m.text}  (conf={m.confidence:.2f}, turn={m.source_turn})")
    print(f"    Episodes:            {len(store.episodes)}")
    for e in store.episodes:
        print(f"      - {e.summary}")
    print()

    # Test retrieval on a fresh query -- demonstrates the cold-start problem
    print("  Negative test: fresh query 'I need help with TypeScript'")
    used = store.query_long_term("TypeScript")
    print(f"    Retrieved: {[m.text for m in used] or '(no match)'}")
    print(f"    Reading:    'typescript' is absent from the bag-of-words vocab, so the")
    print(f"                query vector is all zeros and cosine is 0 everywhere.")
    print(f"                A real embedder (text-embedding-3-small, bge-small) would")
    print(f"                match on the semantic neighborhood; the mock doesn't.")
    print()

    # Cost model
    print("  LLM cost ceiling (per 1M tokens, 2026):")
    for model, p in PRICING.items():
        print(f"    {model:<22} in=${p['input']:>6.3f}  out=${p['output']:>6.3f}")
    print()

    # Trade-offs
    print("  Design properties:")
    print("    Store signal:   durable facts (language, location) qualify; greetings don't.")
    print("    Dedup:          cosine > 0.9 collapses near-duplicates before they hit the index.")
    print("    Confidence:     MIN_CONFIDENCE drops low-quality extractions; the store is a")
    print("                    positive cache, not a log.")
    print("    Vector store:   in-memory dict for the demo; pgvector / Qdrant / Weaviate in prod.")
    print("    Privacy:        PII stays out of the store without explicit consent; the model")
    print("                    card documents the data scope.")
    print()

    print("=" * 70)


if __name__ == "__main__":
    demo()
