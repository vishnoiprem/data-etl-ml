# Lesson 7 — Quiz: RAG & LLM Data Infrastructure

> **Type:** Quiz · Module 5 · RAG & LLM Data Infrastructure
> Self-check on the seven lessons. Answers at the bottom.

---

## Section A — Conceptual

**Q1.** Which is **not** part of the typical RAG pipeline at query time?
- A) Embedding the query
- B) Hybrid retrieval
- C) Re-embedding all source documents
- D) LLM generation

**Q2.** The most-debated stage of a RAG pipeline is:
- A) Embedding model choice
- B) Vector DB choice
- C) Chunking strategy
- D) LLM choice

**Q3.** For ACL filtering, the right place to filter is:
- A) Inside the LLM prompt
- B) At retrieval time, before the LLM sees the data
- C) After generation, in the response filter
- D) At the vector DB only if tenant_id == user.tenant_id

**Q4.** The "M" in MRR stands for:
- A) Marginal
- B) Mean (arithmetic)
- C) Multi
- D) (Reciprocal rank itself is its own metric)

**Q5.** Which is the cheapest way to recover 5–10% recall in a RAG pipeline?
- A) Switch embedding models
- B) Add a cross-encoder rerank
- C) Add a hybrid index
- D) Increase chunk size

**Q6.** Which is the highest-quality multimodal document parser in 2026?
- A) `pypdf` with OCR
- B) AWS Textract / Google Document AI
- C) `BeautifulSoup`
- D) `whisper`

**Q7.** For a 100M-vector production RAG, what is the recommended LLM strategy?
- A) Always use the largest LLM (GPT-4o or Claude Opus)
- B) Always use the smallest LLM
- C) Tier: small model for filtering/routing, large model for the answer
- D) Use the LLM with the lowest per-token cost

---

## Section B — Scenario

**Q8.** Your team is rolling out a RAG bot over 50K internal Slack messages. What 5 things do you build before launch?

**Q9.** Your RAG bot is producing plausible-but-wrong answers 15% of the time. Walk through debugging steps.

**Q10.** A stakeholder asks: "Why is RAG so much engineering? Can't we just call the LLM with all our docs in the context?" Write the response.

---

## Section C — Practical

**Q11.** Write the metadata schema you would use for a multi-tenant RAG system over a knowledge base of policy docs.

**Q12.** List 5 components in the eval harness, and one metric for each.

**Q13.** Describe the migration plan for switching from `text-embedding-3-small` to Cohere `embed-v3` for 50M chunks.

---

## Section D — Open

**Q14.** Pick a real RAG failure you've seen (or imagine one). What did retrieval look like? What did the answer look like? What fix would you propose?

---

## Answer Key

<details>
<summary>A1</summary>

**C** — Re-embedding all source documents happens at ingest time (offline), not at query time. A, B, D are part of the query-time flow.

</details>

<details>
<summary>A2</summary>

**C** — Chunking. It determines whether the answer is even in the chunks the LLM sees.

</details>

<details>
<summary>A3</summary>

**B** — At retrieval time, before the LLM sees the data. Filtering after the fact leaks, filtering in the LLM prompt is unreliable.

</details>

<details>
<summary>A4</summary>

**D** — MRR = Mean Reciprocal Rank. The M is the "Mean" over multiple queries.

</details>

<details>
<summary>A5</summary>

**B** — Cross-encoder rerank. Adds ~50 ms to top-50 candidates, recovers the most quality per dollar.

</details>

<details>
<summary>A6</summary>

**B** — AWS Textract / Google Document AI / Azure Document Intelligence. Production-grade for tables, forms, handwriting; ~$1.50 per 1000 pages.

</details>

<details>
<summary>A7</summary>

**C** — Tier. Small LLM for routing / classification / metadata extraction; large LLM for the final answer. Best cost-quality tradeoff.

</details>

<details>
<summary>A8</summary>

A model answer:

1. **ACL model.** Which Slack channels can each user see? Apply filters at retrieval.
2. **Freshness SLO.** How stale can the index be? (probably minutes for chat).
3. **Citations.** Every claim cites a Slack message URL + timestamp.
4. **Eval set.** 100+ hand-labelled Q&A pairs with expected source message.
5. **Guardrails.** PII (don't reveal DMs), prompt injection ("ignore previous instructions"), off-topic ("what's the weather?").
</details>

<details>
<summary>A9</summary>

A model answer — debugging steps:

1. **Check retrieval quality.** For the bad answers, what was actually retrieved? Was the right chunk there?
2. **If retrieval is bad → chunking, embedding model, hybrid search.**
3. **If retrieval is fine → check the prompt.** Is the LLM ignoring context? "Answer only using..." present?
4. **If prompt is fine → check the model.** Try a different LLM, compare.
5. **Check the eval set.** Is the eval set representative of the production distribution?
6. **Run LLM-as-judge** on the bad answers to find patterns.
</details>

<details>
<summary>A10</summary>

A model answer:

> Three reasons:
>
> 1. **Cost.** Stuffing 1000 pages into a GPT-4o prompt is millions of tokens per query. At 100 queries/day, that's $100k+ per year. Retrieval cuts it to $5k.
> 2. **Latency.** Long prompts = slow generation. Retrieval = fast, focused prompts.
> 3. **Recency.** With "all docs in context," every doc change requires re-running. With retrieval, you re-embed the changed docs and the next query picks them up. No LLM call.
>
> Beyond the engineering reasons, there are correctness reasons:
>
> - LLMs lose focus in long contexts (the "lost in the middle" problem). Retrieval keeps the context short and focused.
> - You can cite sources. With everything-in-context, citations are noisy.
> - You can enforce ACL. With everything-in-context, you can't.
>
> The "all docs in context" version is a demo. Retrieval is production.

</details>

<details>
<summary>A11</summary>

A model answer:

```yaml
metadata:
  tenant_id: string         # multi-tenant isolation
  doc_id: string            # chunk → document
  chunk_index: int
  doc_type: string          # "policy", "runbook", "spec"
  source_url: string        # citation
  page_number: int          # PDF grounding
  heading_path: list        # ["Refund", "> Eligibility"]
  created_at: timestamp
  updated_at: timestamp
  visibility: string        # "public", "internal", "restricted"
  owner_team: string        # who can edit / get notified
  acl: list[string]         # row-level
  tags: list[string]
  language: string
  embedding_model: string   # "text-embedding-3-large@2026-01"
  embedding_version: int
```

</details>

<details>
<summary>A12</summary>

A model answer:

| Component | Metric |
|---|---|
| Retrieval quality | recall@10 |
| Retrieval ranking | MRR or NDCG@10 |
| Generation faithfulness | LLM-as-judge 1–5 |
| Citation accuracy | % of citations that reference the right source |
| Latency | p95 end-to-end latency |
| Cost | $/query, $/tenant/month |
| Guardrail | prompt-injection pass rate |
| User satisfaction | thumbs-up rate |

</details>

<details>
<summary>A13</summary>

A model answer — embedding migration in 7 steps:

1. **Build new index** alongside old, with `embedding_model = "cohere-embed-v3"`.
2. **Re-chunk and re-embed** all 50M chunks. Batched, throttled. ~24 hours.
3. **A/B test.** 10% of queries → new index, 90% old. Compare recall, faithfulness, latency on the eval set.
4. **Tune alpha** (lexical/semantic weight) and reranker threshold on Cohere-specific behaviour.
5. **Cut over** when new matches or beats old. 100% queries → new.
6. **Delete old index** after 7 days of stable production traffic.
7. **Update docs** — embedding model, version, costs.

</details>

<details>
<summary>A14</summary>

This is a personal reflection. For any RAG failure, the question to ask is: **at which stage did it break?**
- Bad chunking (the right info was in the doc but not the chunk)
- Bad embedding (the chunk was there but the retriever didn't rank it highly)
- Bad rerank (cross-encoder missed it)
- Bad generation (LLM hallucinated despite good context)
- Bad prompt (LLM ignored context)
- Bad ACL (wrong data shown to wrong user)

The fix is different at each stage. Without instrumentation, you can't tell.

</details>

---

*End of Module 5. Move to [Module 6 — Feature Stores & ML Data Infra](../06-feature-stores-ml-data-infra/README.md).*
