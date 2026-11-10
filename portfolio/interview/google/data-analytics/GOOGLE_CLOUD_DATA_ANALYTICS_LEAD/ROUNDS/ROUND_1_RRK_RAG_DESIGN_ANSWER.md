# RRK: Enterprise Design, Real-Time RAG on Google Cloud

**Scenario:** 10M documents, retrieval-augmented generation (RAG), p95 latency under 500 ms, freshness within 5 minutes of a document update, "no hallucinations".
**Question:** Design it on Google Cloud.
**Follow-up:** The LLM hallucinated a company that isn't in the evidence.
**Time:** about 6 minutes, then 1 minute for the follow-up.
**Pass signal:** grounded generation with structured evidence, a shadow index for safe changes, freshness without full reindex, an evaluation loop, and honest limits ("no hallucinations" can't be guaranteed).

> Service capabilities and latencies change. Treat every latency figure here as a **budget to validate by load test**, and check current product documentation before quoting limits.

---

## 1. Short answer (the version that was supplied, kept for reference)

Cloud Storage event to Pub/Sub to Dataflow for chunking (512 tokens, 50 overlap, hash dedup), Vertex AI embeddings in batch, BigQuery Vector Search with hybrid retrieval, Vertex AI Ranking to the top 8, Gemini given `evidence_json`, query-embedding cache in Memorystore. Freshness by CDC and upsert, no full reindex. Evaluation from traces and feedback into a gold set. Follow-up: grounded generation, instruct the model to use only the evidence, an LLM-as-judge check that fails any output mentioning a company not in the evidence.

Good skeleton. Fixes needed:
- **BigQuery Vector Search is not the usual choice for a sub-500 ms online path.** It is built for analytical workloads and typically has higher latency. For low-latency serving at 10M documents, **Vertex AI Vector Search** is the usual candidate; BigQuery fits batch, analytical and governance-heavy retrieval. Say so, and validate by load test.
- **No latency budget.** "Under 500 ms p95" has to be split across steps and checked. Also ask **what is under 500 ms**: time to first token, or the full answer? Full LLM generation alone often exceeds 500 ms.
- **"No hallucinations" can't be guaranteed.** Promise a measured, low rate, with abstention when evidence is weak.
- **The shadow index is missing** from the body, but it's what makes embedding-model, chunking or index changes safe.
- **Access control is missing.** A RAG system must filter results by the user's permissions at query time.
- **Deletes and updates:** freshness must also remove deleted or superseded chunks.

---

## 2. Improved answer

**Restate (10 s):** "A RAG system over 10 million documents, answers in under 500 ms at p95, new or changed documents searchable within five minutes, and no unsupported claims. I'll clarify, set a latency budget, then design ingestion, retrieval, generation and evaluation."

### Step 1. Clarify (or state assumptions)
- What is under 500 ms: retrieval only, time to first token, or the full response? (Assumption: time to first token, with streaming.)
- Users, query volume (peak QPS), document types and size, languages.
- Access rules: are documents permissioned per user or group? PII? Residency?
- What does a wrong answer cost (customer-facing, regulated, internal)? That sets the abstain threshold.

### Step 2. Ingestion and freshness (target: 5 minutes, no full reindex)
- **Event path:** Cloud Storage object notification (or source CDC) to **Pub/Sub** to **Dataflow**.
- **Parse and chunk:** structure-aware chunking (headings, tables), starting point around 300 to 500 tokens with some overlap, **tuned by retrieval evaluation, not fixed in advance**. Keep metadata: document ID, version, section, ACL, timestamps, source URL.
- **Dedup and change detection:** content hash per chunk; only changed chunks are re-embedded.
- **Embed** with a Vertex AI embedding model, batched, with retries and a dead-letter path.
- **Upsert** into the index by `(doc_id, chunk_id, version)`. **Delete or tombstone** removed or superseded chunks, otherwise stale answers persist.
- **Freshness SLO:** end-to-end from document update to searchable, measured at p95, alerted on breach.

### Step 3. Serving path with a latency budget (illustrative, validate by load test)
| Step | Budget | Notes |
|---|---|---|
| Query embedding | about 30 to 80 ms | Cache embeddings for repeated queries (for example Memorystore) |
| Retrieval (hybrid: vector plus keyword) | about 50 to 150 ms | Use a low-latency vector service; apply **ACL filters** here |
| Rerank top 30 to 50 down to about 8 | about 50 to 150 ms | Vertex AI ranking or similar |
| LLM first token | about 150 to 300 ms | Stream the answer |

**Do the sum out loud — the interviewer will.** The ranges total roughly **280–680 ms**, so the 500 ms p95 target is **not met at the pessimistic end**. That is the point of the exercise, and you should be the one to say it:

> "Summed, that's about 280 to 680 milliseconds. The p95 target of 500 is achievable in the happy path but **not at the tail**, and p95 is exactly the tail. So the design levers are: drop the rerank stage for most queries and rerank only when retrieval confidence is low; cache embeddings; use a smaller model for the common case and escalate to a larger one; and keep context short. If the target is a hard contractual SLO, I'd say that now and propose the smaller-model path as the committed design, rather than discover the miss in production."

If the **full** answer must be under 500 ms rather than first token, the design changes more fundamentally: smaller model, shorter context, or precomputed answers for frequent questions. **Say which definition you are using before you commit to a number.**

### Step 4. Generation that stays grounded
- Pass the model a structured **`evidence_json`**: chunk ID, text, source, version, date, for each retrieved chunk.
- Instruct: answer only from the evidence; **cite chunk IDs**; if the evidence is insufficient, say "I don't have enough information" (abstain).
- **Post-checks:** every claim must map to a cited chunk; entity and number checks (any company, person or figure in the answer must appear in the evidence); a groundedness check by a separate model or rules; fail closed to abstention.
- Safety: DLP before indexing, prompt-injection defences for retrieved text, output filtering (for example Model Armor), audit logging of prompts and answers.

### Step 5. Access control, residency and governance
- Carry document ACLs into index metadata, and **filter at query time**. Never retrieve then hide.
- Index, embeddings, models and logs in the required region; keep PII out of prompts and logs.
- Cache design: a query-embedding cache is safe; a **response cache** must be keyed by the user's permission set.

### Step 6. Evaluation and safe change (the shadow index)
- **Gold set** of questions with expected sources and answers, grown from real traces and user feedback.
- Metrics: retrieval recall@k, answer groundedness and faithfulness, abstain rate, latency p50 and p95, cost per query.
- **Shadow index:** to change the embedding model, chunking or index settings, build the new index alongside the old one, run both on the same traffic or gold set, compare metrics, then **switch by alias** with a rollback. Never reindex in place.
- Regression-test every prompt, model and index change before release.

### Step 7. Risks and what I'd build first
Risks: stale or deleted content, ACL leaks, a latency budget that can't hold, prompt injection, cost per query. Build first: ingestion plus retrieval with an evaluation harness on a thin slice, then add generation, then scale.

---

## 3. Follow-up: "The LLM hallucinated a company that isn't in the evidence."

**Answer:** "First I'd reproduce it and look at the trace: was the right chunk retrieved, was it in the prompt, and did the prompt allow outside knowledge? Then I'd fix it in layers:
1. **Prompt:** answer only from `evidence_json`, cite chunk IDs, abstain if the evidence is insufficient.
2. **Deterministic check:** extract named entities in the answer and verify each appears in the evidence; if not, block or regenerate.
3. **Judge check:** an LLM-as-judge groundedness scorer as a second layer (not the only one).
4. **Evaluation:** add this case to the gold set and track an *unsupported-entity rate* as a release gate.
5. **Retrieval:** if the right evidence wasn't retrieved, improve chunking, hybrid weights or reranking, because the model fills gaps when retrieval fails.
The aim is a measurable, low hallucination rate and a safe fallback, not a promise of zero."

---

## 4. Pass checklist

- [ ] Clarify what the 500 ms covers; give a latency budget
- [ ] An online vector service suited to low latency (and a reason if you use BigQuery for some paths)
- [ ] Ingestion with change detection, upsert, **delete handling** and a freshness SLO
- [ ] Hybrid retrieval, reranking, and **ACL filtering at query time**
- [ ] `evidence_json`, citations, abstention, and post-generation checks
- [ ] Evaluation gold set and metrics; a **shadow index** with alias switch and rollback
- [ ] Residency, PII and logging controls
- [ ] Honest statement: reduce and measure hallucinations, don't promise zero

## 5. Likely probes

| Probe | One-line answer |
|---|---|
| "Why not BigQuery vector search?" | Good for analytical and batch retrieval and governance; for an interactive sub-500 ms path I'd use a low-latency vector service, and I'd load-test both. |
| "How do you guarantee no hallucinations?" | I don't. I constrain to evidence, check outputs, abstain when unsure, and gate releases on a measured unsupported-claim rate. |
| "How do you handle a document someone just lost access to?" | ACL metadata is updated by the same pipeline and filtered at query time; revocation has its own SLO. |
| "How do you change the embedding model?" | Build a shadow index, compare on the gold set and live traffic, switch by alias, keep the old one for rollback. |
| "What does it cost?" | Embedding cost per changed chunk, index serving cost, and LLM cost per query; I'd track cost per query and set a budget. |
