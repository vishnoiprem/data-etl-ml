# Lesson 02 — Context Engineering and RAG Foundations

> **Stop putting the whole style guide in the prompt.** 50 minutes. Hands-on, runnable.

By the end of this lesson you can build a **retrieval-augmented drafter**: a service that takes a customer email, retrieves the most relevant policy chunks from the style guide and the most relevant shipment from the tracker, and feeds only those into the LLM prompt. The drafter is now grounded in **retrieved** context, not the **whole** context.

This is the lift Phase 2 is named for. The drafter can now answer emails that mention things the model never saw in training (PacificFreight's specific customs-duty policy, the specific shipment's last event) without growing the system prompt.

---

## 🎯 You will build

A `/retrieve` endpoint backed by a **mock vector store** that:
- Loads the style guide chunked into 7 H2 sections
- Loads the 15 shipments from Phase 1's tracker as 15 more chunks
- Ranks all 22 chunks by deterministic token-overlap score against the query
- Returns the top-k with scores

You wire the drafter to **augment** its system prompt with the retrieved chunks. Same `complete()` call, but the prompt now contains "the relevant slice of the style guide" instead of "the whole style guide." Same accuracy, ~10x less tokens, ~10x cheaper.

## 🧠 Concept (5 min)

**Context engineering** is the discipline of building the prompt **at call time** from retrieved content, instead of pasting the entire knowledge base into every call. The shape:

```
            ┌──────────────────┐
            │  Query (email)   │
            └────────┬─────────┘
                     │  embed (or hash-mock)
                     ▼
            ┌──────────────────┐
            │  Vector store    │  ←── pre-indexed at build time
            │  (chunks)        │
            └────────┬─────────┘
                     │  top-k
                     ▼
            ┌──────────────────┐
            │  System prompt   │  base persona + retrieved chunks
            └────────┬─────────┘
                     │
                     ▼
            ┌──────────────────┐
            │  LLM call        │
            └──────────────────┘
```

**Why RAG, not a bigger system prompt?**
- A bigger prompt costs more (every call pays the input-token price)
- A bigger prompt is slower (more tokens to process)
- A bigger prompt is **less focused** (the model can get confused by irrelevant rules)
- A bigger prompt doesn't scale — once you have 1000 policy docs, you can't paste them all

**Why a mock vector store, not a real one?**
- Phase 2 is about the *interface* of retrieval, not the ops of Pinecone
- The mock is deterministic (no API keys, no rate limits, no surprise cost) — perfect for the customer demo
- The interface (`retrieve(query, k) -> list[Chunk]`) is identical to a real vector store, so Phase 3's migration is a 1-function change
- The mock uses a real technique (token overlap with a length bonus) that the `course/hardcode/level-8-evaluation-testing/12-ragas-evaluation.py` file uses for the same reason

## 🛠️ Build It (40 min)

### Step 1 — chunk the style guide (5 min)

The whole style guide is ~130 lines. Pasting it into every prompt wastes ~600 tokens per call. Instead, we split it into **7 chunks** — one per H2 section — and retrieve the relevant section at call time.

[`../shared/build_policy_chunks.py`](../shared/build_policy_chunks.py) does this. Run it:

```bash
cd ../shared
python3 build_policy_chunks.py
# → Wrote 7 chunks to ../shared/policy_chunks.jsonl
```

The output looks like:
```json
{"id": "style-guide#1", "section": "1. The 4-line opener (always)", "text": "...", "source": "..."}
{"id": "style-guide#2", "section": "2. Tone rules", "text": "...", "source": "..."}
...
```

> **FDE tip:** the chunking strategy (H2 = chunk boundary) is the simplest thing that works. Phase 3 swaps in tiktoken-based chunking with overlap (the `capstone-starters/01-ai-doc-qa` pattern) when the policy docs are no longer well-structured markdown.

### Step 2 — build the mock vector store (15 min)

Open [`../service/rag.py`](../service/rag.py). The class:

```python
class MockVectorStore:
    def __init__(self, policy_chunks_path, shipments_path):
        # Load policy chunks from policy_chunks.jsonl
        # Build one chunk per shipment from shipments.json
        ...

    def retrieve(self, query: str, k: int = 5, source_filter=None) -> list[RetrievedChunk]:
        # Tokenize the query (lowercase, drop stop words)
        # Score every chunk by token-overlap F1 with a length bonus
        # Return the top-k
        ...
```

The scoring function is the interesting part:

```python
def _score(query_tokens: set[str], doc_tokens: set[str]) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    overlap = query_tokens & doc_tokens
    if not overlap:
        return 0.0
    recall = len(overlap) / len(query_tokens)
    precision = len(overlap) / len(doc_tokens)
    f1 = 2 * precision * recall / (precision + recall)
    # A longer doc gets a small bonus — more context to draw from.
    length_bonus = min(1.0, len(doc_tokens) / 30.0)
    return round(f1 * (0.6 + 0.4 * length_bonus), 4)
```

Three things to notice:
1. **Stop words are dropped** ("the", "a", "is") so common words don't dominate
2. **F1 balances precision and recall** — we want chunks that are both relevant to the query AND not full of irrelevant content
3. **The length bonus** prevents a 3-word chunk from outscoring a 30-word chunk just because it's smaller

> **FDE trap:** if you skip the length bonus, a tiny policy chunk (just the heading) outranks a long shipment chunk. The retrieval becomes useless. The bonus is the most important single line in this file.

### Step 3 — write `build_rag_prompt` (10 min)

Same file, lower down. The function takes the base system prompt + the email + the looked-up shipment + the retrieved chunks, and assembles the final system prompt:

```python
def build_rag_prompt(*, base_system, email, shipment, chunks):
    parts = [base_system]

    policy = [c for c in chunks if c.source == "policy"]
    ship = [c for c in chunks if c.source == "shipment"]

    if policy:
        parts.append("---")
        parts.append("Retrieved policy chunks (cite as [1], [2], ...):")
        for i, c in enumerate(policy, start=1):
            parts.append(f"[{i}] ({c.id}, score={c.score:.2f})\n{c.text}")

    if ship:
        parts.append("---")
        parts.append("Retrieved shipment chunks (cite as [S1], [S2], ...):")
        ...

    if shipment is not None:
        parts.append("---")
        parts.append("Provided shipment (explicit lookup):")
        parts.append(json.dumps(shipment, indent=2, ensure_ascii=False))

    parts.append("---")
    parts.append(f"Customer email:\n{email}")
    parts.append("Draft a reply in the customer's language. Output ONLY the reply.")

    return "\n\n".join(parts)
```

The structure is deliberate:
- **Persona** (top): who you are, how to write
- **Retrieved context** (middle): the relevant facts
- **Explicit shipment** (middle): the looked-up shipment, for grounding
- **The email** (bottom): what to respond to
- **The instruction** (bottom): what to do with all of it

> **FDE rule:** always put the persona first and the task last. The model attends more to the start and end of the prompt than to the middle (this is empirically true for all current LLMs). If you bury the persona in the middle of retrieved context, the model writes in OpenAI's voice, not PacificFreight's.

### Step 4 — wire the `/retrieve` endpoint (5 min)

In `app.py`:

```python
@app.get("/retrieve")
def retrieve(q: str, k: int = 5, source: Optional[str] = None) -> RetrieveResponse:
    store = _get_vector_store()
    chunks = store.retrieve(q, k=k, source_filter=source)
    return RetrieveResponse(ok=True, query=q, chunks=[...])
```

Test:
```bash
curl "localhost:8000/retrieve?q=customs%20duty&k=3&source=policy"
# → top chunk is style-guide#2 (Tone rules — mentions customs)

curl "localhost:8000/retrieve?q=PF-1003%20held%20at%20customs&k=3&source=shipment"
# → top chunk is shipment:PF-1003 (the customs-held shipment)
```

### Step 5 — wire the drafter to use retrieved context (5 min)

In `app.py:_draft_pipeline`:

```python
# BEFORE: just the base persona
system_prompt = PERSONA_AND_STYLE

# AFTER: base persona + retrieved policy chunks + retrieved shipment chunks
system_prompt = rag_mod.build_rag_prompt(
    base_system=PERSONA_AND_STYLE,
    email=req.email,
    shipment=shipment,  # the looked-up shipment, if any
    chunks=all_chunks,  # policy + shipment chunks
)
```

Test:
```bash
curl -X POST localhost:8000/draft -d '{"email":"Where is PF-1003? Stuck at customs.","shipment_id":"PF-1003"}' -H 'Content-Type: application/json'
# → draft is the same as before, BUT the contexts now include
#   style-guide#2 (Tone rules) and style-guide#4 (Hard rules) AND
#   shipment:PF-1003. The model had those in front of it when drafting.
```

The visible draft doesn't change much for the mock (the mock returns canned replies). With a real LLM, this is the moment the drafter starts **grounding** its answers in the retrieved policy instead of the model's general training — fewer hallucinations, more on-voice.

## 🏛️ FDE Lens

> **When to graduate from the mock vector store to a real one.**

The mock uses token overlap. It works because the style guide is small (7 chunks) and the tracker is small (15 shipments). The moment any of these become true, swap in a real vector store:

| Trigger | Migration |
|---|---|
| Style guide > 50 chunks | Swap token-overlap for embeddings (text-embedding-3-small, 5x cheaper than ada-002) |
| Tracker > 10K shipments | Add a real vector DB (Pinecone / Qdrant / pgvector) |
| Multi-language policy docs | Add a cross-lingual embedding model |
| Customer asks "why did it retrieve this?" | Add a re-ranker (Cohere Rerank or a cross-encoder) on top of the retriever |

ADR-0002 (in `consulting/03-adrs-and-tradeoffs.md`) records this decision in writing. The FDE's job is to make the migration trigger explicit, so the engineering team doesn't have to guess in 6 months.

## 🌙 Reflect

Write 3-5 sentences:

1. The mock scores by token overlap. Real embeddings score by cosine similarity. What does the mock **do worse** than embeddings, and what does it do **better**?
2. `build_rag_prompt` puts the persona first and the email last. The retrieved chunks go in the middle. Why this order? What happens if you reverse it?
3. The retrieval returns `k=2` policy chunks and `k=1` shipment chunk by default. The customer asks "why not 10?" How do you answer?
4. The mock vector store is **deterministic** — the same query always returns the same chunks. This is a feature in Phase 2 (the customer demo is reproducible) and a bug in Phase 3 (real embeddings have small variance). What's the FDE's responsibility here?
5. The system prompt now includes the retrieved chunks. What is the **worst case** if the retriever returns the wrong chunk? How do you detect it?

**What's next** — T3 adds the eval harness. The drafter is grounded, but the FDE still needs to know: "is it actually getting better?" The eval harness measures 4 RAGAS-style metrics, runs against a 30-row test set, and trips a regression check if a metric drops by more than 5%. That last bit is the "reliability" half of "evaluation, reliability, and application-layer patterns."
