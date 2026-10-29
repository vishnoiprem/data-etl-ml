# Lesson 7 — Quiz: AI DE System Design

> **Type:** Quiz · Module 8 · AI DE System Design
> Self-check on the framework + five design problems. Answers at the bottom.

---

## Section A — Framework

**Q1.** The 5 steps of the framework, in order, are:
- A) Sketch → Clarify → Tradeoffs → Deep-dive → Summary
- B) Clarify → Sketch → Deep-dive → Tradeoffs → Summary
- C) Clarify → Deep-dive → Sketch → Tradeoffs → Summary
- D) Sketch → Deep-dive → Clarify → Summary → Tradeoffs

**Q2.** In a 40-minute design question, the right time for **clarifying questions** is roughly:
- A) 0 minutes (just start)
- B) 5 minutes
- C) 15 minutes
- D) Until the interviewer is satisfied

**Q3.** The "deep-dive" step should focus on:
- A) All 15 boxes equally
- B) The 2–3 boxes that decide the outcome
- C) The boxes you know best
- D) The boxes with the most acronyms

**Q4.** The "tradeoffs" step is required because:
- A) It's a checklist item interviewers look for
- B) It forces you to defend your choices against alternatives
- C) Most candidates forget it
- D) The interview is timed

---

## Section B — Recommendation

**Q5.** For a billion-scale recommender, the **candidate generation** stage usually uses:
- A) Cross-encoder over all items
- B) Two-tower ANN + co-occurrence + trending
- C) LLM-as-recommender
- D) Random sampling

**Q6.** The biggest moat for a real-time personalised recommender is:
- A) The model architecture
- B) The feature store (online, low-latency)
- C) The vector DB
- D) The GPU cluster

**Q7.** Cold-start for a brand-new user is best handled by:
- A) Asking them 20 questions
- B) Popular / trending + demographic priors + multi-armed bandit
- C) Random items
- D) Returning empty recommendations

---

## Section C — Enterprise RAG

**Q8.** In enterprise RAG, ACL must be enforced at:
- A) The LLM prompt
- B) The response filter
- C) Retrieval time, before the LLM sees the data
- D) The vector DB only

**Q9.** Hybrid search (BM25 + vector) outperforms vector-only on:
- A) All queries
- B) Queries with exact terms, IDs, model numbers, error codes
- C) Queries about semantics
- D) Queries in non-English

**Q10.** The cheapest quality win in RAG (5–10% recall, ~50ms latency cost) is:
- A) Switch embedding models
- B) Add a cross-encoder reranker
- C) Increase chunk size
- D) Use a larger LLM

---

## Section D — Feature Platform

**Q11.** Training/serving skew exists because:
- A) Hardware differences
- B) Features computed differently in offline and online paths
- C) Random model variance
- D) Insufficient training data

**Q12.** Point-in-time joins are required to prevent:
- A) Slow training
- B) Future feature leakage into training data
- C) Memory issues
- D) Drift

**Q13.** A per-feature freshness SLA matters because:
- A) It's a compliance requirement
- B) Different features have different staleness tolerance; missing SLA = bad predictions
- C) Engineers like precision
- D) It's required for the audit

---

## Section E — Fraud Detection

**Q14.** The most important fraud-detection features are typically:
- A) Demographic (age, location)
- B) Velocity and recency (txns in last 5 min, geo distance from last)
- C) Credit score
- D) Account age

**Q15.** Fraud labels are typically available:
- A) Immediately
- B) Within 1 hour
- C) Within 24 hours
- D) Days or weeks (chargebacks)

**Q16.** A two-layer decision (rules + model) is preferred over model-only because:
- A) Rules are more accurate
- B) Rules provide fast updates + explainability for known patterns; model catches novel patterns
- C) Models are slow
- D) It's a regulatory requirement

---

## Section F — Multi-Modal

**Q17.** Cross-modal search requires:
- A) Separate indexes per modality
- B) All modalities in the same vector space (or transcribe-then-embed)
- C) A multi-modal LLM
- D) An LLM for every query

**Q18.** For audio search, the standard pattern in 2026 is:
- A) Direct audio embedding
- B) Transcribe with Whisper, embed the transcript
- C) Spectral features + nearest-neighbour
- D) Skip audio, only do text

**Q19.** The biggest ingest cost in a multi-modal platform is typically:
- A) Vector DB
- B) Transcription (audio/video) and vision-LLM captioning (images)
- C) Embedding
- D) Storage

---

## Section G — Scenario / Open

**Q20.** Sketch a 15-box architecture for a real-time ad CTR prediction system (100B events/day, p99 < 50ms, 100M ads).

**Q21.** You're told: "Build a RAG bot for our 1M-document legal archive. Each user can see only their firm's documents. Citation accuracy is non-negotiable." List the 5 design choices you'd defend.

**Q22.** A stakeholder says: "We don't need an eval set, we'll just check if users like the answers." Reply in 4 points.

**Q23.** Pick a system you know (recsys, RAG, fraud, feature platform, multi-modal). Identify the **single most likely silent failure** and what monitoring catches it.

---

## Answer Key

<details>
<summary>A1</summary>

**B** — Clarify → Sketch → Deep-dive → Tradeoffs → Summary. The interviewer wants to see you reason from constraints first.
</details>

<details>
<summary>A2</summary>

**B** — About 5 minutes for clarifying questions. Don't go over 10 unless the problem is genuinely ambiguous.
</details>

<details>
<summary>A3</summary>

**B** — Pick the 2–3 boxes that decide the outcome. Don't spread your time over all 15 boxes equally.
</details>

<details>
<summary>A4</summary>

**B** — Stating alternatives and defending your choice is the senior-engineer move. It also reveals what you'd change.
</details>

<details>
<summary>A5</summary>

**B** — Two-tower ANN (semantic) + co-occurrence (collaborative) + trending (fallback). Three sources, deduped, ACL-filtered.
</details>

<details>
<summary>A6</summary>

**B** — The feature store. Real-time personalisation needs online features at sub-50ms; without a feature store you can't do per-user real-time personalisation at all.
</details>

<details>
<summary>A7</summary>

**B** — Popular / trending + demographic priors + multi-armed bandit. As the user interacts, the bandit shifts to personalised ranking.
</details>

<details>
<summary>A8</summary>

**C** — Retrieval time, before the LLM sees the data. Filtering in the LLM prompt is unreliable; filtering in the response is too late.
</details>

<details>
<summary>A9</summary>

**B** — Queries with exact terms, IDs, model numbers, error codes. Vector-only often misses these.
</details>

<details>
<summary>A10</summary>

**B** — Cross-encoder reranker. ~50ms for top-50 candidates, recovers the most quality per dollar.
</details>

<details>
<summary>A11</summary>

**B** — Features computed differently in offline vs online paths is the classic source of skew. The model trains on one set and serves on another.
</details>

<details>
<summary>A12</summary>

**B** — Point-in-time joins prevent future feature values from leaking into past training rows. Without them, training metrics are inflated and the model fails online.
</details>

<details>
<summary>A13</summary>

**B** — Different features tolerate different staleness. Fraud features need sub-second; LTV can be daily. Missing SLA = bad predictions.
</details>

<details>
<summary>A14</summary>

**B** — Velocity (count in last 5 min / hour) and recency (distance from last txn) are the highest-signal fraud features.
</details>

<details>
<summary>A15</summary>

**D** — Fraud labels arrive via chargebacks, days or weeks after the transaction. The retrain pipeline must join delayed labels back to the original decision.
</details>

<details>
<summary>A16</summary>

**B** — Rules give fast updates (no retrain needed) and explainability; the model catches novel patterns. Together they cover both the known and the unknown.
</details>

<details>
<summary>A17</summary>

**B** — All modalities in the same vector space, or transcribe-then-embed (audio/video → text → vector). Without this, cross-modal search isn't possible.
</details>

<details>
<summary>A18</summary>

**B** — Whisper transcription + text embedding. Audio similarity is harder than text; transcribe first, then use text retrieval.
</details>

<details>
<summary>A19</summary>

**B** — Vision-LLM captioning (5M images × $0.00255) and audio transcription (200k hours × $0.006/min) dominate one-shot ingest cost.
</details>

<details>
<summary>A20</summary>

A model answer (boxes):

1. **User request** — ad request with user context
2. **API gateway** — auth + rate limit
3. **Ad candidate gen (ANN)** — two-tower model over 100M ads, top-500
4. **Contextual filter** — geo, brand-safety, frequency caps
5. **Feature fetch (online store)** — user features, ad features, context features, all < 50ms
6. **Light ranker** — GBDT, top-500 → top-50
7. **Heavy ranker (DNN)** — on GPU, top-50 → top-10
8. **Pricing / auction** — second-price, p99 < 5ms
9. **Response** — top ad + price
10. **Decision log** — every request logged for eval
11. **Streaming feature transform (Flink)** — sub-second
12. **Batch feature transform (Spark)** — hourly/daily
13. **Feature store** (online + offline)
14. **Model training pipeline** — hourly retrain
15. **Eval harness + monitoring + cost dashboard**

Total budget: 50ms (fetch: 15ms, light rank: 5ms, heavy rank: 25ms, auction: 5ms).
</details>

<details>
<summary>A21</summary>

A model answer — 5 design choices to defend:

1. **Vector DB with row-level ACL metadata** — every chunk tagged with `firm_id`; retrieval filters by `firm_id = user.firm_id`. Without this, cross-firm data leaks.
2. **Hybrid search (BM25 + vector) + reranker** — legal queries often have exact terms ("§ 5.2(b)"); pure semantic misses them. Cross-encoder rerank is the cheapest quality win.
3. **Citations returned with every answer** — for legal, citing the source is non-negotiable. Each `[Source N]` must reference a specific paragraph + page.
4. **Eval set of 200+ real legal queries with expected citations** — measured nightly, gate every PR. Citation accuracy > 95% is the bar.
5. **Audit log of every query + answer + retrieved chunk** — for compliance review, "who saw what when." Standard for legal / regulated industries.

Tradeoffs to call out:
- Managed vector DB (Pinecone) over self-hosted for ops simplicity
- Sonnet for answer quality (justified on faithfulness eval)
- Cache common queries (saves $X/mo)
</details>

<details>
<summary>A22</summary>

A model answer:

> Four reasons thumbs-up / thumbs-down is not a substitute for an eval set:
>
> 1. **Coverage bias.** Only a tiny fraction of users give feedback. The questions you get feedback on are not the questions users actually ask. You optimise for the wrong distribution.
> 2. **Cold-start.** Day-one, you have zero feedback. You can't ship without some baseline.
> 3. **Latency.** Feedback arrives hours or days later. A bad answer ship today, you won't know for days. Eval catches it before production.
> 4. **Diagnostic.** Thumbs tells you "users like / don't like." It doesn't tell you *why* — was retrieval bad? prompt bad? hallucination? An eval set with retrieval metrics, faithfulness, citation accuracy tells you which stage to fix.
>
> The eval set is the lab. Thumbs is the field. You need both, in that order. Ship the eval first, ship the thumbs tracking second.

</details>

<details>
<summary>A23</summary>

This is a personal reflection. A useful framework:

- **Pick the system** (recsys / RAG / fraud / features / multi-modal).
- **Identify the most likely silent failure** — the one that wouldn't trigger a 500 or a page.
- **Identify the monitoring that catches it** — drift, freshness, ACL audit, eval regression, etc.
- **Identify the fix** — what changes once you detect it?

Without this discipline, the system will fail silently in production. The MLOps / LLMOps layers exist exactly so silent failures don't stay silent.

</details>

---

*End of Module 8. End of course. See [resources/](../resources/) for shared cheat sheets and prompt libraries.*