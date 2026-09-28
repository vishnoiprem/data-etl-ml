# Lesson 4 — RAG Evaluation

> **Type:** Article · Module 5 · RAG & LLM Data Infrastructure
> Building the eval harness: retrieval metrics, generation metrics, LLM-as-judge.

---

## Why evaluation is the moat

Most RAG projects die not from bad retrieval, but from **inability to tell when retrieval got worse**. Without eval, you're flying blind. With eval, you can ship confidently and iterate fast.

```
   NO EVAL                              WITH EVAL
   ────────                             ────────
   "Is the bot getting better           recall@10: 0.85 → 0.91
    or worse? I don't know."            faithfulness: 92%
                                       cost/query: $0.005
                                       p95 latency: 1.4s
                                       → ship this version
```

---

## The two halves of RAG eval

| Half | Metrics |
|---|---|
| **Retrieval** | recall@k, MRR, NDCG, latency, ACL correctness |
| **Generation** | faithfulness, answer relevance, citation accuracy, completeness |

The retrieval half is **objective** (right answer in top-k? yes/no). The generation half is **subjective** (is the answer faithful to sources? is it complete?), and benefits from **LLM-as-judge**.

---

## The retrieval metrics

```
   given:  query q
           list of relevant doc IDs R(q)
           list of retrieved doc IDs in rank order A(q)

   recall@k      = (R(q) ∩ A(q)[:k]) / |R(q)|
                  "Did the relevant docs appear in my top-k?"

   MRR           = 1 / rank of first relevant doc
                  "How high was the first hit?"

   NDCG@k        = DCG@k / ideal_DCG@k
                  "How good was the ordering?"
```

Build an eval set:

```json
{
  "query": "How do I refund a Stripe payment?",
  "relevant_doc_ids": ["doc-refund-001", "doc-stripe-help-042"],
  "must_cite": "doc-refund-001",
  "difficulty": "easy"
}
```

100–500 of these, hand-curated, refreshed quarterly. **This is the highest-ROI artefact in any RAG project.**

---

## The generation metrics

These are subjective. Two ways to measure:

### 1. Heuristic metrics
- **Faithfulness:** does the answer use only retrieved sources? (regex / NLI model)
- **Answer relevance:** cosine similarity between query and answer.
- **Citation accuracy:** does each `[Source N]` actually support the claim?

### 2. LLM-as-judge

```python
JUDGE_PROMPT = """You are evaluating a RAG system.

QUESTION: {query}
SOURCES: {sources}
ANSWER: {answer}

Evaluate on:
1. FAITHFULNESS (1-5): Does the answer use only the sources?
2. RELEVANCE (1-5): Does the answer address the question?
3. CITATION (1-5): Are citations accurate?
4. COMPLETENESS (1-5): Is anything important missing?
5. HALLUCINATION (yes/no): Did the answer include info not in the sources?

Return JSON.
"""
```

**LLM-as-judge is approximate but fast.** Calibrate against human eval on 50–100 examples first.

---

## The "split your eval set" pattern

```
   ┌─────────────────────────────────────────┐
   │  EVAL SET (300 queries)                  │
   │                                          │
   │   ┌─────────────┐   ┌────────────────┐  │
   │   │  250 queries │   │ 50 "guardrail" │  │
   │   │  general     │   │ queries        │  │
   │   │  quality     │   │                │  │
   │   └─────────────┘   │ - PII attempts │  │
   │                     │ - off-topic    │  │
   │                     │ - adversarial  │  │
   │                     └────────────────┘  │
   │                                          │
   │  General eval runs on every PR + nightly │
   │  Guardrail eval runs on every PR         │
   └─────────────────────────────────────────┘
```

Guardrails catch **PII extraction attempts**, **prompt injection**, **off-topic queries**. They're the security eval.

---

## The eval harness architecture

```
   ┌─────────────────────┐
   │  Eval set (JSON)    │ (versioned in git)
   └─────────┬───────────┘
             │
             ▼
   ┌─────────────────────┐
   │  Eval runner        │ runs each query against the live RAG pipeline
   └─────────┬───────────┘
             │
             ▼
   ┌─────────────────────┐
   │  Metrics calculator │ recall, MRR, faithfulness, latency, cost
   └─────────┬───────────┘
             │
             ▼
   ┌─────────────────────┐
   │  Dashboard          │ tracked over time, alerted on regression
   └─────────────────────┘
```

Every CI / nightly run produces a JSON of `{metric: value}`. Tracked over time.

---

## The "nightly eval" workflow

```
   01:00  run eval set against current prod pipeline
   01:30  compute metrics
   01:35  compare to:
            - last 7 days:    regression?
            - last release:    regressed by which change?
   01:40  write to dashboard
   01:45  alert if any metric regressed > 2% vs 7-day baseline
```

Tools: **RAGAS**, **DeepEval**, **Phoenix (Arize)**, **LangSmith**, custom.

---

## The "what to alert on"

| Metric | Alert threshold |
|---|---|
| `recall@10` | drop > 2% vs 7-day baseline |
| `faithfulness` | drop > 1 point (1–5 scale) |
| `p95 latency` | > SLA |
| Cost / query | > budget |
| Citation accuracy | drop > 5% |
| Guardrail pass rate | drop > 1% (potential attack) |

---

## The "human eval" calibration

LLM-as-judge isn't ground truth. Calibrate it.

```
   Every 100 examples:
   - 50 of LLM-judge-yes is human-yes        (judge precision)
   - 50 of LLM-judge-no is human-no          (judge specificity)

   Target: 80%+ agreement with human eval.
   Refresh sample quarterly.
```

If judge and human disagree often, your LLM-as-judge isn't accurate enough — improve it or use a stronger model.

---

## The "online eval from user feedback" pattern

```python
# After each answer, show thumbs-up/thumbs-down
# Track: query, answer, user_id, feedback, latencies

# Build an eval set from thumbs-down
THUMBS_DOWN_QUERIES = [
    {
        "query": ...,
        "answer": ...,
        "feedback": "wrong",
        "user_comment": "...",
    }
]
```

These are **the highest-signal eval examples** because they're real user disagreements.

---

## The "what to measure in production" dashboards

```
   REAL-TIME (Grafana):
   - QPS
   - p50/p95/p99 latency
   - error rate
   - cost per query
   - top tenants by volume

   DAILY (Looker / Mode):
   - retrieval: recall@10 by query type
   - generation: faithfulness, citation accuracy
   - cost: by tenant, by query type
   - user satisfaction: thumbs-up rate

   WEEKLY (review meeting):
   - eval trends
   - guardrail triggers
   - top failure modes
   - regressions to investigate
```

---

## The eval-driven development loop

```
   PR raised (e.g. change chunk size)
       │
       ▼
   CI runs eval set against the new pipeline
       │
       ▼
   if metrics degrade:    ❌ reject the PR
   if metrics improve:   ✅ accept
   if metrics same:      ✅ accept (cost or latency improvement)
```

This is **RAG eval done right**: every change is measured, every regression caught.

---

## What Comes Next

> Lesson 5 — **Unstructured at Scale** — processing PDFs, images, audio, and HTML at billion-doc scale. OCR, vision models, multimodal pipelines.
