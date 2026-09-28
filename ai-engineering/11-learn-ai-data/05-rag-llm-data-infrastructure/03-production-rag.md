# Lesson 3 — Production RAG

> **Type:** Article · Module 5 · RAG & LLM Data Infrastructure
> The production version: ACL, freshness, observability, prompt engineering, citations, and the eval harness.

---

## The gap between demo and production

A demo is **the LLM getting the right 5 chunks**. Production is:
- Only returning chunks the user is allowed to see
- Returning chunks that are fresh enough to be useful
- Citing the source for every claim
- Logging every interaction for eval
- Performing within latency and cost budgets
- Failing gracefully when retrieval is poor

This lesson covers the production hard parts.

---

## The ACL model

**Every production RAG system has users that should see different data.** The naive approach (retrieve everything, filter in the LLM) leaks data. The right approach: filter at retrieval.

```
   query: "What's the refund policy?"
   user: alice@acme.com, tenant_id=acme
        │
        ▼
   ┌──────────────┐
   │  embed query │ + ACL context (user.tenant_id, user.roles, ...)
   └──────┬───────┘
          ▼
   ┌──────────────────────────────────────────┐
   │  retrieve WHERE                            │
   │    tenant_id = 'acme'                      │
   │    AND (visibility = 'public'              │
   │         OR visibility IN user.orgs         │
   │         OR owner = user.id)                │
   │    AND status != 'archived'                │
   │  ORDER BY cosine                          │
   │  LIMIT 50                                 │
   └──────┬───────────────────────────────────┘
          ▼
   top-k chunks (already filtered)
```

**Implementation options:**
1. **Vector DB ACL:** metadata filter at query time (Pinecone, Qdrant, Weaviate all support).
2. **Application ACL:** retrieve candidates, filter in app, return top-k.
3. **Hybrid:** vector DB filters by tenant + status; app filters by row-level ACL.

For large user bases, **row-level ACL is best done in the vector DB** for performance.

---

## The freshness story

```
   "Your data is X days old" — every RAG user eventually asks.

   Freshness tiers:
   - real-time (< 5 min):    CDC + streaming embed pipeline
   - hourly:                  5-min batched ingest
   - daily:                   overnight batch
   - weekly:                  weekly rebuild
   - real-time + :            Celonis-style live (rare, expensive)
```

**The honest trade-off:** real-time freshness costs money. Most teams are at **hourly to daily**. Tune the SLA to business need, not to "as fresh as possible."

```python
FRESHNESS_SLA = {
    "policies": "24h",     # rarely changes
    "tickets": "5min",     # changes constantly
    "code": "1h",          # changes every commit
    "runbooks": "1h",
}
```

---

## The observability story

What you log on every query:

```json
{
  "query_id": "uuid",
  "user_id": "alice@acme.com",
  "tenant_id": "acme",
  "timestamp": "2026-01-15T14:23:01Z",
  "query_text": "What's the refund policy?",
  "rewritten_query": "What is the refund policy for Stripe payments?",
  "retrieval": {
    "top_k": 50,
    "rerank_top": 10,
    "candidates": [
      {"doc_id": "doc-1", "score": 0.92, "acl_pass": true},
      {"doc_id": "doc-2", "score": 0.89, "acl_pass": true},
      ...
    ],
    "rerank_scores": [...],
    "filtered_count": 3,
    "latency_ms": 47
  },
  "llm": {
    "model": "gpt-4o",
    "prompt_tokens": 1823,
    "completion_tokens": 187,
    "latency_ms": 612,
    "cost_cents": 2
  },
  "answer_text": "...",
  "citations": [{"doc_id": "doc-1", "page": 3, "heading": "Refund Policy"}],
  "user_feedback": null  # filled in later
}
```

This is the **eval set's source of truth** at scale.

---

## The citation pattern

**Every claim should cite a source.** Without citations, the user has no way to verify, and the trust evaporates.

```python
def generate_answer(query, retrieved_chunks):
    context = "\n\n---\n\n".join([
        f"[Source {i+1}: {c.metadata['source']}, page {c.metadata.get('page_number', '?')}]\n{c.text}"
        for i, c in enumerate(retrieved_chunks)
    ])
    prompt = f"""Answer the question using ONLY the sources below.
Cite each claim with [Source N]. If the sources don't contain the answer,
say "I don't know" — do not make up information.

SOURCES:
{context}

QUESTION: {query}

ANSWER:"""
    return llm.complete(prompt)
```

Then parse `[Source N]` from the answer to attach source metadata.

---

## The "prompt assembly" pattern

```
   prompt =
     system_message          # role + rules + format
     + retrieved_context     # citations + text
     + conversation_history  # last N turns, summarised if long
     + user_query
```

```python
def assemble_prompt(query, context, history):
    system = (
        "You are a helpful assistant for ACME's internal knowledge base. "
        "Answer using ONLY the provided sources. Cite every claim. "
        "If the sources don't contain the answer, say so."
    )
    ctx = format_context(context)  # with citations
    hist = format_history(history) # summarise old turns if needed
    user = f"SOURCES:\n{ctx}\n\nCONVERSATION:\n{hist}\n\nQUESTION: {query}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
```

---

## The "fail gracefully" pattern

When retrieval fails (no good chunks), the LLM should know:

```
   if best_score < RELEVANCE_THRESHOLD:
       retrieved = []   # don't return low-quality context
       prompt += "\n\nNo relevant sources found. Ask the user to clarify."
```

**The hard rule:** if the retrieved chunks have no overlap with the query, the LLM is more dangerous than no LLM. "I don't know" is the right answer.

---

## The cost model

```
   Per query cost (2026 prices):
   ─────────────────────────────
   Embedding (query):               $0.000001
   Vector DB query:                 $0.0001    (Pinecone serverless)
   Rerank (cross-encoder):          $0.00001
   LLM (gpt-4o):                    $0.005      (1.5K tokens in)
   Total per query:                 ~$0.005     (≈ half a cent)

   At 100k queries/day:             $500/day = $15k/month

   Optimisation levers:
   1. Smaller LLM (gpt-4o-mini):    10× cheaper
   2. Smaller context (top-3):      3× cheaper
   3. Caching common queries:       avoid LLM entirely
   4. Cheaper embedder (3-small):   6× cheaper than -large
```

Cache aggressively. Common questions can be served from a cache without an LLM call.

---

## The 4 anti-patterns in production RAG

### 1. "The whole docs as context" anti-pattern
Stuffing the entire 100-page doc into the prompt. Costs explode, recall drops, latency huge.

### 2. "No citations" anti-pattern
LLM answers confidently, sources untraceable. Trust evaporates.

### 3. "No relevance threshold" anti-pattern
Forcing the LLM to answer even when retrieval fails. Hallucinations.

### 4. "One retrieval, no rerank" anti-pattern
Top-5 with no rerank misses 10–15% of good answers. Cross-encoder rerank is the cheapest quality boost.

---

## The "production checklist"

Before launch, verify:

- [ ] **ACL filtering works** — test with cross-tenant queries
- [ ] **Freshness SLO met** — measure source → vector lag
- [ ] **Citations returned** — every claim has a source
- [ ] **Relevance threshold set** — bad retrieval → "I don't know"
- [ ] **Eval harness runs nightly** — recall, faithfulness, cost
- [ ] **PII / sensitive docs excluded** — by tag, by ACL, by source
- [ ] **All interactions logged** — for eval and incident response
- [ ] **Cost per query measured** — within budget
- [ ] **Latency p95 < SLA** — measured across tenants
- [ ] **Eval set curated** — 100+ hand-labelled examples

---

## What Comes Next

> Lesson 4 — **RAG Evaluation** — building the eval harness: retrieval metrics, generation metrics, LLM-as-judge, and the dashboards that catch regression.
