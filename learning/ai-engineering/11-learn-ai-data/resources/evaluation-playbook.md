# Evaluation Playbook

> How to evaluate RAG, classification, extraction, and ML pipelines in production. The eval-driven development loop.

---

## The "eval first" principle

```
   ┌──────────────────────────────────────────────────────────┐
   │                                                          │
   │  THE SINGLE RULE:                                         │
   │                                                          │
   │   No production change ships without a passing eval.      │
   │   No model retrain ships without a passing regression.    │
   │   Every LLM-as-judge is calibrated against human eval.    │
   │   Every alert is wired to a metric with a baseline.       │
   │                                                          │
   └──────────────────────────────────────────────────────────┘
```

If you can't measure, you can't iterate. The eval is the moat.

---

## 1. The eval set

### What goes in it

```
   EVAL SET = (300–1000 query, expected_output) pairs
   ──────────────────────────────────────────────────

   Categories:
   - 60-70% "production-realistic" queries (broad coverage)
   - 15-20% "hard" queries (multi-hop, edge cases)
   - 10-15% "guardrail" queries (adversarial, off-policy, PII)
   - 5-10%  "freshness" queries (recently changed data)

   Per query:
   {
     "id": "q-123",
     "query": "...",                 // the user-facing input
     "expected_output": "...",        // the expected answer
     "expected_doc_ids": ["doc-1"],   // for retrieval eval (RAG)
     "category": "factual",           // factual / multi-hop / adversarial / ...
     "difficulty": "easy",            // easy / medium / hard
     "freshness_required": false,    // must include freshly-ingested content
     "tenant_id": "...",              // for multi-tenant ACL eval
     "user_context": {...}            // identity, roles, permissions
   }
```

### How to build it

1. **Seed (50–100):** hand-written by the team. Covers core use cases.
2. **Production (50–200):** sampled real user queries (with thumbs-down prioritised).
3. **Synthetic (100+):** LLM-generated, validated by human spot-check.
4. **Adversarial (50+):** hand-crafted injection / PII / off-policy probes.

Refresh quarterly. The set grows; never shrinks.

---

## 2. Metrics

### Retrieval metrics (RAG)

```python
# recall@k — was at least one relevant doc in top-k?
def recall_at_k(retrieved, relevant, k):
    retrieved_ids = {c["doc_id"] for c in retrieved[:k]}
    relevant_ids = {r for r in relevant}
    return len(retrieved_ids & relevant_ids) / len(relevant_ids)

# MRR — how high was the FIRST relevant doc?
def mrr(retrieved, relevant):
    for rank, c in enumerate(retrieved, 1):
        if c["doc_id"] in relevant:
            return 1.0 / rank
    return 0.0

# NDCG@k — was the ORDERING good?
def ndcg_at_k(retrieved, relevant, k):
    # binary relevance: 1 if relevant, 0 otherwise
    relevance = [1 if c["doc_id"] in relevant else 0 for c in retrieved[:k]]
    dcg = sum(r / np.log2(i + 2) for i, r in enumerate(relevance))
    ideal_relevance = sorted(relevance, reverse=True)
    idcg = sum(r / np.log2(i + 2) for i, r in enumerate(ideal_relevance))
    return dcg / idcg if idcg > 0 else 0.0
```

| Metric | Targets |
|---|---|
| `recall@5` | ≥ 0.85 (85% of the time, relevant doc in top-5) |
| `recall@10` | ≥ 0.95 |
| `MRR` | ≥ 0.75 (first hit in top-3 most of the time) |
| `NDCG@10` | ≥ 0.85 |

### Generation metrics (RAG / LLM)

| Metric | How to measure | Target |
|---|---|---|
| **Faithfulness** | NLI model or LLM-as-judge: "is this entailed by sources?" | ≥ 0.90 (1-5 scale) |
| **Answer relevance** | LLM-as-judge: "does it address the question?" | ≥ 0.90 |
| **Citation accuracy** | Regex + LLM-as-judge: "does [Source N] support the claim?" | ≥ 0.95 |
| **Hallucination rate** | LLM-as-judge: "any fact not in sources?" | ≤ 0.05 |
| **Helpfulness** | LLM-as-judge or thumbs-up rate | ≥ 0.80 |

### Classification metrics

For category classifiers (sentiment, intent, routing):

```
   PRECISION     correct positives / flagged positives
   RECALL        correct positives / actual positives
   F1            harmonic mean of P and R
   MACRO-F1      F1 averaged across classes (balance)
   CONFUSION     which class↔class pairs are mixed
```

Target: ≥ 0.85 macro-F1 for production classifiers.

### Extraction metrics

```
   EXACT MATCH       (extracted == expected, all fields)
   FIELD-LEVEL F1    (per field: precision, recall, F1)
   ROBUST F1         (F1 over fields that should be present)
```

Target: ≥ 0.90 field-level F1 for high-value fields (amounts, dates).

### Operational metrics

```
   LATENCY       p50 / p95 / p99 end-to-end
   THROUGHPUT    QPS, requests/min
   ERROR RATE    % 5xx or unanswered
   COST          $/query, $/tenant/month
   UPTIME        % of time available
```

---

## 3. LLM-as-judge

### When to use

- Subjective quality (helpfulness, faithfulness)
- Open-ended generation
- Cost-effective at scale (1000s of queries)

### When NOT to use

- Pure accuracy on a labelled set (just compute directly)
- Legal or compliance (human required)
- When ground truth is known and cheap (just compute)

### How to do it well

```python
JUDGE_PROMPT = """You are evaluating an AI system's output.

QUESTION: {query}
SOURCES (when applicable): {sources}
ANSWER: {answer}
EXPECTED (when applicable): {expected}

Score each dimension honestly. Do not give the benefit of the doubt.

faithfulness (1-5): Does the answer only use the sources / context provided?
relevance (1-5): Does the answer address the question?
completeness (1-5): Is anything important missing?
citation_accuracy (1-5): Are citations accurate? (N/A if no citations)
hallucination (yes/no): Does the answer contain info NOT in the sources?

Return JSON only:
{
  "faithfulness": int,
  "relevance": int,
  "completeness": int,
  "citation_accuracy": int,
  "hallucination": "yes" | "no",
  "reasons": "1-3 sentences"
}
"""
```

```python
response = openai.chat.completions.create(
    model="claude-sonnet",
    messages=[{"role": "user", "content": JUDGE_PROMPT.format(...)}],
    response_format={"type": "json_object"},
)
judgement = json.loads(response.choices[0].message.content)
```

### Calibrate against human eval

```
   EVERY 100 EXAMPLES
   ───────────────────
   - 50 where LLM-judge says "good" → spot-check 50 against human
   - 50 where LLM-judge says "bad"  → spot-check 50 against human

   TARGET: 80%+ agreement with human eval

   If not:
   - Use a stronger model as judge
   - Add more criteria to the rubric
   - Provide reference answers in the prompt
   - Or switch to a different scoring approach
```

---

## 4. The eval harness architecture

```python
# eval.py
class EvalRunner:
    def __init__(self, pipeline, eval_set, metrics_calculator, judge):
        self.pipeline = pipeline
        self.eval_set = eval_set  # List[EvalQuery]
        self.metrics = metrics_calculator
        self.judge = judge

    def run(self):
        results = []
        for query in self.eval_set:
            t0 = time.time()
            result = self.pipeline.run(query.query, user_context=query.user_context)
            latency = time.time() - t0

            scores = {
                "recall@k": self.metrics.recall_at_k(result.candidates, query.expected_doc_ids, k=10),
                "mrr": self.metrics.mrr(result.candidates, query.expected_doc_ids),
                "faithfulness": self.judge.faithfulness(query.query, result.citations, result.answer),
                "citation_accuracy": self.judge.citation_accuracy(result.citations, result.answer),
                "latency_ms": latency * 1000,
                "cost_cents": result.cost_cents,
            }
            results.append(scores)

        return self.aggregate(results)

    def aggregate(self, results):
        keys = results[0].keys()
        return {k: sum(r[k] for r in results) / len(results) for k in keys}
```

```
   ┌────────────────┐
   │ Eval set       │ (versioned in git)
   └────────┬───────┘
            ▼
   ┌────────────────┐
   │ Eval runner    │ runs each query, captures results
   └────────┬───────┘
            ▼
   ┌────────────────┐
   │ Metrics calc   │ recall, MRR, faithfulness, latency, cost
   └────────┬───────┘
            ▼
   ┌────────────────┐
   │ Dashboard      │ tracked over time, alerted on regression
   └────────────────┘
```

---

## 5. The CI gate

Every PR (and every release) runs the eval set:

```yaml
# .github/workflows/eval.yml
name: RAG eval gate

on: [pull_request]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run eval
        run: |
          python -m eval.run \
            --pipeline=current \
            --eval-set=evals/v3.json \
            --output=eval-results.json

      - name: Check thresholds
        run: |
          python -m eval.check_thresholds \
            --results=eval-results.json \
            --baseline=eval-baseline.json \
            --rules=eval-rules.yml
          # rules:
          # recall@10: must not drop more than 2%
          # faithfulness: must not drop more than 0.2 points
          # latency_p95: must not exceed 1500ms
          # cost_per_query: must not exceed $0.01

      - name: Comment on PR
        run: python -m eval.comment --results=eval-results.json
```

If thresholds fail, the PR is blocked. Forces every change to be measured.

---

## 6. The nightly eval

```
   01:00    run full eval set against production pipeline
   01:30    compute metrics
   01:35    compare to:
              - last 7 days: regression?
              - last release: which change regressed?
   01:40    write to dashboard (Grafana / Looker / Mode)
   01:45    alert if any metric dropped > threshold
```

Tools: RAGAS, DeepEval, Phoenix (Arize), LangSmith, custom.

---

## 7. The "alert thresholds" cheat sheet

| Metric | Alert threshold | Why |
|---|---|---|
| `recall@10` | drop > 2% vs 7-day baseline | Retrieval got worse |
| `faithfulness` | drop > 1 point (1-5) | LLM ignoring sources |
| `citation_accuracy` | drop > 5% | Wrong attributions |
| `p95 latency` | > SLA | UX issues |
| `cost per query` | > budget | Cost blowout |
| `guardrail pass rate` | drop > 1% | Possible attack |
| `user thumbs-up rate` | drop > 5% | Users unhappy |
| `error rate` | > 0.5% | Things breaking |

Wire these to PagerDuty / Slack / OpsGenie. Decide what's a page vs a Slack ping.

---

## 8. The online eval signal

After each answer, log:

```json
{
  "query_id": "uuid",
  "user_id": "alice@acme.com",
  "tenant_id": "acme",
  "query_text": "...",
  "answer_text": "...",
  "citations": ["doc-1", "doc-2"],
  "user_feedback": null,
  "feedback_at": null,
  "latency_ms": 950,
  "cost_cents": 0.5,
  "model_id": "claude-3-5-sonnet-20240620",
  "embedding_model_id": "cohere-embed-v3",
  "rag_config_version": "v2.1",
  "kb_version": "kb-2026-01-15",
  "timestamp": "2026-01-15T14:23:01Z"
}
```

Thumbs-down signal flows back into triage → eval set → regression test.

```
   THUMBS DOWN (in production)
        │
        ▼
   triage queue (human reviews)
        │
        ├──► retrieval failure → fix chunking / reranker / KB
        ├──► prompt failure   → fix prompt
        ├──► model failure    → switch model / add guardrail
        └──► KB gap           → add doc to KB

   After fix:
        │
        ▼
   add query + expected answer to eval set
```

The eval set grows from real user disagreements. **The highest-signal eval set you can build.**

---

## 9. The "evaluator anti-patterns"

1. **Eval set drifts toward the easy.** Make sure it has hard / guardrail / adversarial in proportion.
2. **LLM-as-judge not calibrated.** Always spot-check vs human. Re-calibrate quarterly.
3. **Single-metric obsession.** Track multiple. Faithfulness without citation accuracy = hallucinations with sources.
4. **Cosmetic thresholds.** Don't alert on metrics no one looks at. If a metric doesn't drive a decision, drop it.
5. **Pre-production eval, no production eval.** Production feedback (thumbs, downstream metrics) is the gold.
6. **Eval set never grows.** Set should grow with real user disagreements.
7. **Forget eval set version control.** Versioned eval set, versioned prompts, versioned KB. Reproducibility.

---

## 10. Putting it together

The eval-driven development loop:

```
   PR raised (change chunk size, or prompt, or model)
        │
        ▼
   CI runs eval set against the new pipeline
        │
        ├── metrics OK ──► accept PR
        │
        ├── metrics same ──► accept (cost / latency win)
        │
        └── metrics regressed ──► reject PR
                                │
                                ▼
                             iterate on the change
```

Every change is measured. Every regression is caught before production. This is **eval-driven development**.

---

## Appendix: a minimal eval-driven RAG scaffold

```python
# eval/runner.py
import json
from typing import List, Dict

class EvalRunner:
    def __init__(self, rag_pipeline):
        self.pipeline = rag_pipeline

    def run(self, eval_set_path: str) -> Dict:
        with open(eval_set_path) as f:
            eval_set = json.load(f)

        results = []
        for q in eval_set:
            r = self.pipeline.run(q["query"], user_context=q.get("user_context"))
            results.append({
                "query_id": q["id"],
                "category": q["category"],
                "recall_at_10": recall_at_k(r.candidates, q.get("expected_doc_ids", []), 10),
                "faithfulness": judge_faithfulness(q["query"], r.citations, r.answer),
                "citation_accuracy": judge_citations(r.citations, r.answer),
                "latency_ms": r.latency_ms,
                "cost_cents": r.cost_cents,
            })

        return aggregate(results)

# GitHub Action / cron runs this nightly + on every PR.
# Compares to baseline, alerts on regression.
```

The whole thing is ~150 lines. The eval is your moat, not your LLM choice.