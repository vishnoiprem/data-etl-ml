# LOOP 5: Eval + Observability + Gold Dataset

**Theme:** Recall@8, nDCG, LLM-as-judge — Staff bar skill
**Total Duration:** 3 hours 15 min
**Difficulty:** Medium (eval is core L6 muscle)

---

## Architecture Diagram (Master)

```
┌────────────────────────────────────────────────────────────────────┐
│         RAG EVAL PLATFORM - NIGHTLY, 10K GOLD QUERIES              │
└────────────────────────────────────────────────────────────────────┘

TRIGGER (Airflow, 2am daily)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ Airflow DAG: nightly_rag_eval                           │
│                                                         │
│ 1. Read gold_dataset (10k queries)                      │
│ 2. For each prompt_version in [v1.2.0, v1.3.0-beta]:    │
│    a. Embed query                                       │
│    b. Retrieve top 8 chunks                             │
│    c. Generate answer with LLM                          │
│    d. Compute metrics:                                  │
│       - Recall@8, nDCG@8                                │
│       - LLM-as-judge grounded score                     │
│       - cost_usd                                        │
│       - latency_ms                                      │
│ 3. Compare vs yesterday, alert if regression >2%       │
│ 4. Generate HTML report, email stakeholders             │
│ 5. Update dashboard (Grafana)                           │
└─────────────────────────────────────────────────────────┘

DATA FLOW
─────────

gold_dataset                  eval_runs                    eval_examples
(thumbs_down +              (one row per                 (one row per
 corrected_answer)            run)                         example)
       │                          │                             │
       ▼                          ▼                             ▼
┌──────────────┐           ┌────────────┐               ┌──────────────┐
│ feedback     │           │ run_id PK  │               │ example_id PK│
│ +scrub PII   │──────────▶│ prompt_ver │──────────────▶│ run_id    FK │
│ +judge 90%   │           │ day        │               │ query        │
│ +split 80/20 │           │ status     │               │ expected_ch  │
└──────────────┘           │ total_ex   │               │ actual_ch    │
                           └────────────┘               │ recall_at_8  │
                                                        │ ndcg_at_8    │
                                                        │ judge_score  │
                                                        │ cost_usd     │
                                                        │ latency_ms   │
                                                        └──────────────┘
```

---

## Greet (15 min)

### Q1: How do you know RAG is good? What metrics?

**L6 Answer (60 sec):**

> "Three layers of metrics, not one:
>
> 1. **Offline quality:** Recall@8 (0.89), nDCG@8 (0.91) on a gold set of 10k queries. These measure retrieval accuracy.
>
> 2. **Online quality:** Thumbs-up rate (73%), session length, friend-accept-rate. These measure user satisfaction.
>
> 3. **Generation quality:** LLM-as-judge grounded score (96%) — second LLM checks if the answer is in the evidence_json. Catches hallucination.
>
> I track all three in Grafana, alert if any drops >2% week-over-week. If offline is good but online is bad, the gold set is stale. If both are bad, the model or retrieval broke."

**L6 Keywords:** three layers, Recall@8, nDCG, LLM-as-judge, gold set, >2% alert.

---

### Q2: Tell me about time your eval was wrong

**L6 STAR (60 sec):**

**S:** Eval said Recall@8 = 0.92, we shipped. Online thumbs-up dropped 73% → 62%.

**T:** Find why offline ≠ online.

**A:**
1. Checked query distribution: online had 30% new query types not in the gold set
2. Built online query sampler, added new queries to gold set weekly
3. Re-ran eval: Recall@8 0.92 → 0.85, now matched online
4. Built automated weekly gold set refresh from production traffic

**R:** Eval now matches online within 3%. Caught 4 future regressions before users.

**Lesson:** gold set is not static. It must evolve with the query distribution.

---

## AI-Native DE Full Stack (60 min)

### Q1 Data Model (15 min)

```
┌────────────────────────────────────────────────────────────┐
│              EVAL HARNESS DATA MODEL                       │
└────────────────────────────────────────────────────────────┘

eval_runs                          eval_examples
┌────────────────────────┐         ┌──────────────────────────┐
│ run_id            PK   │◀───────▶│ example_id     PK        │
│ prompt_version         │  1:N   │ run_id       FK          │
│ model_version          │         │ query                   │
│ collection             │         │ gold_chunks  JSON       │
│ started_at             │         │ predicted_chunks JSON   │
│ completed_at           │         │ gold_answer  TEXT       │
│ total_examples   INT   │         │ predicted_answer TEXT   │
│ status                 │         │ recall_at_8   FLOAT     │
│   running/completed    │         │ ndcg_at_8     FLOAT     │
│   failed               │         │ grounded_score FLOAT   │
└────────────────────────┘         │ cost_usd      FLOAT    │
                                   │ latency_ms    INT      │
                                   │ judged_at     TIMESTAMP│
                                   └────────────────────────┘

gold_dataset
┌──────────────────────────┐
│ gold_id        PK        │
│ trace_id       FK        │
│ query                   │
│ original_chunks JSON    │
│ original_answer         │
│ corrected_answer        │
│ rating                  │
│ is_pii_scrubbed BOOL    │
│ pii_types  ARRAY        │
│ is_quality_passed BOOL  │
│ created_at              │
└──────────────────────────┘
```

**SQL schema:**

```sql
CREATE TABLE eval_runs (
  run_id          BIGINT PRIMARY KEY,
  prompt_version  STRING NOT NULL,
  model_version   STRING,
  collection      STRING,
  started_at      TIMESTAMP,
  completed_at    TIMESTAMP,
  total_examples  INT,
  status          STRING  -- 'running', 'completed', 'failed'
);

CREATE TABLE eval_examples (
  example_id        BIGINT PRIMARY KEY,
  run_id            BIGINT REFERENCES eval_runs(run_id),
  query             STRING,
  gold_chunks       JSON,        -- [{chunk_id, doc_id, relevance}]
  predicted_chunks  JSON,        -- [{chunk_id, doc_id, score}]
  gold_answer       STRING,
  predicted_answer  STRING,
  recall_at_8       FLOAT,
  ndcg_at_8         FLOAT,
  grounded_score    FLOAT,        -- LLM-as-judge 0-1
  cost_usd          FLOAT,
  latency_ms        INT,
  judged_at         TIMESTAMP
) PARTITIONED BY (DATE(judged_at));

CREATE TABLE gold_dataset (
  gold_id           BIGINT PRIMARY KEY,
  trace_id          BIGINT,
  query             STRING,
  original_chunks   JSON,
  original_answer   STRING,
  corrected_answer  STRING,
  rating            STRING,  -- 'thumbs_down'
  is_pii_scrubbed   BOOLEAN DEFAULT FALSE,
  pii_types         ARRAY<STRING>,
  is_quality_passed BOOLEAN DEFAULT FALSE,
  created_at        TIMESTAMP
);
```

---

### Q2 Pipeline (15 min) - Gold Dataset → Fine-tune Job

```
┌────────────────────────────────────────────────────────────────┐
│   GOLD DATASET PIPELINE → FINE-TUNING JOB                      │
└────────────────────────────────────────────────────────────────┘

Feedback (thumbs_down + corrected_answer)
        │
        ▼
┌────────────────────┐
│ Flink job          │ Listens for thumbs_down
│ (event-driven)     │ with non-null corrected_answer
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ gold_dataset raw   │ Stores original_chunks + corrected_answer
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ PII Scrubber       │ Presidio + regex
│ (presidio_worker)  │ scrubs email/SSN/phone
└────────┬───────────┘
         │ is_pii_scrubbed=true, pii_types=[...]
         ▼
┌────────────────────┐
│ LLM-as-judge       │ "Is corrected_answer grounded in
│ (data_quality)     │  original_chunks?" If yes → pass
└────────┬───────────┘
         │ grounded_score >= 0.5 → is_quality_passed=true
         ▼
┌────────────────────┐
│ Daily Spark job    │ 80% train, 20% eval split
│ (split)            │ generates prompt template + completion
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Fine-tune job      │ Calls OpenAI fine-tune API
│ (creator)          │ tracks training_loss
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Eval on holdout    │ 20% gold queries
│ (20% holdout)      │ Recall@8, nDCG, grounded
└────────┬───────────┘
         │ if +2% vs prod → promote
         ▼
┌────────────────────┐
│ Shadow deploy      │ New model serves 1% traffic
│ (v1.3.0-beta)      │ via feature flag prompt_version
└────────────────────┘
```

---

### Q3 SQL (15 min) - Compare Prompt Versions

```sql
-- Compare prompt versions over last 7 days
SELECT
  r.prompt_version,
  r.model_version,
  COUNT(e.example_id)               AS eval_count,
  AVG(e.recall_at_8)                AS avg_recall,
  AVG(e.ndcg_at_8)                  AS avg_ndcg,
  AVG(e.grounded_score)             AS avg_grounded,
  AVG(e.cost_usd)                   AS avg_cost,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY e.latency_ms) AS p95_latency
FROM eval_runs r
JOIN eval_examples e ON r.run_id = e.run_id
WHERE r.started_at >= CURRENT_DATE - INTERVAL '7' DAY
  AND r.status = 'completed'
GROUP BY r.prompt_version, r.model_version
HAVING AVG(e.grounded_score) > 0.7
ORDER BY avg_recall DESC;
```

**Output (expected):**
| prompt_version | model_version | eval_count | avg_recall | avg_ndcg | avg_grounded | avg_cost | p95_latency |
|----------------|---------------|------------|------------|----------|--------------|----------|-------------|
| v1.3.0-beta    | large         | 10,000     | 0.91       | 0.93     | 0.96         | $0.0045  | 380ms       |
| v1.2.0         | large         | 10,000     | 0.89       | 0.91     | 0.95         | $0.0042  | 420ms       |
| v1.1.0         | small         | 10,000     | 0.82       | 0.85     | 0.88         | $0.0011  | 180ms       |

**Decision:** v1.3.0-beta wins Recall@8 (+2%), grounded similar, cost +7%. Promote to 100%.

---

### Q4 Coding (15 min) - Recall@K, nDCG@K, LLM-as-Judge

```python
import math
from typing import List, Dict, Set


def recall_at_k(predicted: List[str], gold: List[str], k: int = 8) -> float:
    """
    Recall@K = |predicted_top_k ∩ gold| / |gold|
    If gold is empty, return 0.
    """
    if not gold:
        return 0.0
    predicted_top_k: Set[str] = set(predicted[:k])
    gold_set: Set[str] = set(gold)
    return len(predicted_top_k & gold_set) / len(gold_set)


def ndcg_at_k(predicted: List[str], gold_relevance: Dict[str, int], k: int = 8) -> float:
    """
    nDCG@K = DCG / IDCG
    gold_relevance = {chunk_id: relevance_score} (0-3 typical)
    """
    def dcg(scores: List[float]) -> float:
        return sum(score / math.log2(i + 2) for i, score in enumerate(scores))

    predicted_relevances = [gold_relevance.get(doc_id, 0) for doc_id in predicted[:k]]
    actual_dcg = dcg(predicted_relevances)

    ideal_relevances = sorted(gold_relevance.values(), reverse=True)[:k]
    ideal_dcg = dcg(ideal_relevances)

    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0


def llm_as_judge_grounded(answer: str, evidence_json: List[Dict]) -> float:
    """
    Use LLM to check if answer is fully grounded in evidence.
    Returns 0-1 score. 1 = fully grounded, 0 = hallucinated.
    """
    evidence_text = "\n".join(
        f"- {e.get('text', e.get('content', str(e)))}" for e in evidence_json
    )

    prompt = f"""You are evaluating whether an AI answer is grounded in evidence.

EVIDENCE:
{evidence_text}

ANSWER:
{answer}

Question: Is the answer fully supported by the evidence above?
- Score 1.0 if every claim is in the evidence
- Score 0.5 if partially grounded
- Score 0.0 if it contains claims not in the evidence (hallucination)

Return ONLY a single number between 0 and 1."""

    import openai
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=10,
    )
    return float(response.choices[0].message.content.strip())


# Example usage
if __name__ == "__main__":
    predicted = ["doc_1", "doc_5", "doc_3", "doc_8", "doc_2", "doc_7", "doc_4", "doc_6"]
    gold      = ["doc_1", "doc_2", "doc_3"]

    print(f"Recall@8: {recall_at_k(predicted, gold, k=8):.3f}")  # 1.0
    print(f"Recall@3: {recall_at_k(predicted, gold, k=3):.3f}")  # 0.667

    gold_rel = {"doc_1": 3, "doc_2": 2, "doc_3": 1}
    print(f"nDCG@8:   {ndcg_at_k(predicted, gold_rel, k=8):.3f}")  # ~0.92

    score = llm_as_judge_grounded(
        "Q3 revenue was $4.2B",
        [{"text": "Q3 revenue: $4.2B (Table 2, row 3)"}, {"text": "..."}]
    )
    print(f"Grounded: {score:.2f}")  # 1.0
```

---

## Sr Tech Design (60 min) - RAG Eval Platform

```
┌────────────────────────────────────────────────────────────────┐
│         RAG EVAL PLATFORM - NIGHTLY BATCH                      │
└────────────────────────────────────────────────────────────────┘

TRIGGER: Airflow cron "0 2 * * *"
        │
        ▼
┌────────────────────────────────────────────────────────────┐
│ 1. Read gold_dataset (10k queries, last 30 days)           │
│ 2. For each prompt_version:                                │
│    a. Spark distributed: 100 partitions, 100 queries each  │
│    b. Embed (text-embedding-3-large, batch 100)             │
│    c. Qdrant search top 20                                 │
│    d. Cohere rerank top 8                                  │
│    e. LLM answer (gpt-4, prompt template v1.3.0)            │
│    f. Compute metrics per example                           │
│ 3. Write to eval_examples (partitioned by day)              │
│ 4. Aggregate to eval_runs summary                          │
│ 5. Compare vs yesterday:                                   │
│    - If Recall@8 drop >2% → PagerDuty alert                │
│    - If cost increase >10% → Slack warning                 │
│ 6. Generate HTML report:                                   │
│    - Side-by-side v1.2.0 vs v1.3.0-beta metrics            │
│    - Worst 50 examples (lowest recall)                      │
│    - Distribution charts                                   │
│ 7. Email to #ai-platform Slack channel                      │
│ 8. Update Grafana dashboard via API                        │
└────────────────────────────────────────────────────────────┘

COST: 10k queries × $0.005 = $50/night = $1.5k/month
RUNTIME: 90 min on 100 Spark cores
REPORT: HTML + Slack post + email
```

**Three evaluation layers:**

1. **Offline retrieval:** Recall@8, nDCG@8 on gold chunks
2. **Offline generation:** LLM-as-judge grounded score, answer relevance
3. **Operational:** cost, latency, error rate per prompt version

**Key design: holdout set**
- 80% of gold → train/eval
- 20% holdout → never used in training, final unbiased measurement
- Prevents overfitting to gold set

**Alerting rules:**
- Recall@8 drop > 2% on prod prompt_version → page oncall
- Grounded score < 0.85 → Slack warning (hallucination risk)
- Cost increase > 10% → Slack (regression)

---

## Sr Ownership (30 min)

### Q1: RAG looked good offline, failed online

**L6 STAR (60 sec):**

**S:** Recall@8 = 0.89, shipped. Online satisfaction 73% → 45% in 3 days.

**T:** Find why offline ≠ online.

**A:**
1. Pulled online queries, compared to gold set: 30% were new types (typos, abbreviations, multi-hop)
2. Built online query sampler, added 3k new queries to gold set
3. Re-ran eval: Recall@8 0.89 → 0.84, now matched online
4. Built automated weekly gold set refresh from prod traffic

**R:** Eval now matches online within 3%. Caught 4 regressions pre-ship.

---

### Q2: Built observability from scratch

**L6 STAR (60 sec):**

**S:** New team, no dashboards, debugging blind. MTTR 4 hours.

**T:** Build observability in 1 week.

**A:**
1. **ClickHouse** for traces (free, fast, columnar) — schema: `(trace_id, query, latency_ms, model_version, chunk_ids, cost_usd, ts)`
2. **Grafana dashboards:** p50/p95/p99 latency, Recall@8, satisfaction, cost-per-query
3. **Alerts:** p95 > 600ms, Recall drop > 2%, satisfaction < 70%
4. **PagerDuty** integration
5. **Runbook** for each alert with 3-5 common causes

**R:** MTTR 4h → 30min. Team velocity 2x. Caught 2 silent regressions in first week.

---

## Full Stack (60 min) - Eval Comparison Dashboard

```tsx
import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend } from "recharts";

const EvalComparisonDashboard = () => {
  const [runs, setRuns] = useState([]);
  const [selectedVersions, setSelectedVersions] = useState([]);
  const [winnerId, setWinnerId] = useState(null);

  useEffect(() => {
    fetch("/api/eval/runs?days=7")
      .then(r => r.json())
      .then(setRuns);
  }, []);

  const promoteWinner = async (runId) => {
    await fetch(`/api/eval/promote/${runId}`, { method: "POST" });
    setWinnerId(runId);
  };

  // Group by prompt_version for time series
  const timeSeries = runs.reduce((acc, r) => {
    const key = r.prompt_version;
    if (!acc[key]) acc[key] = [];
    acc[key].push({
      date: r.started_at,
      recall: r.avg_recall,
      ndcg: r.avg_ndcg,
      grounded: r.avg_grounded,
    });
    return acc;
  }, {});

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Eval Comparison (last 7 days)</h1>

      {/* Side-by-side table */}
      <table className="w-full border-collapse border mb-6">
        <thead className="bg-gray-100">
          <tr>
            <th className="border p-2">Run ID</th>
            <th className="border p-2">Prompt Version</th>
            <th className="border p-2">Model</th>
            <th className="border p-2">Recall@8</th>
            <th className="border p-2">nDCG</th>
            <th className="border p-2">Grounded</th>
            <th className="border p-2">Cost</th>
            <th className="border p-2">p95 Latency</th>
            <th className="border p-2">Action</th>
          </tr>
        </thead>
        <tbody>
          {runs.map(r => (
            <tr key={r.run_id} className={winnerId === r.run_id ? "bg-green-100" : ""}>
              <td className="border p-2">{r.run_id}</td>
              <td className="border p-2 font-mono">{r.prompt_version}</td>
              <td className="border p-2">{r.model_version}</td>
              <td className="border p-2">{r.avg_recall?.toFixed(3)}</td>
              <td className="border p-2">{r.avg_ndcg?.toFixed(3)}</td>
              <td className="border p-2">{r.avg_grounded?.toFixed(2)}</td>
              <td className="border p-2">${r.avg_cost?.toFixed(4)}</td>
              <td className="border p-2">{r.p95_latency}ms</td>
              <td className="border p-2">
                <button
                  onClick={() => promoteWinner(r.run_id)}
                  disabled={winnerId === r.run_id}
                  className="bg-blue-500 text-white px-3 py-1 rounded disabled:bg-gray-300"
                >
                  {winnerId === r.run_id ? "✓ Promoted" : "Promote"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Time series chart */}
      <h2 className="text-xl font-semibold mb-2">Recall@8 Over Time</h2>
      <LineChart width={800} height={300} className="mb-6">
        <XAxis dataKey="date" />
        <YAxis domain={[0.7, 1.0]} />
        <Tooltip />
        <Legend />
        {Object.entries(timeSeries).map(([version, points]) => (
          <Line
            key={version}
            data={points}
            type="monotone"
            dataKey="recall"
            name={version}
            stroke={version.includes("beta") ? "#10b981" : "#3b82f6"}
            strokeWidth={2}
          />
        ))}
      </LineChart>

      {/* Prompt diff */}
      <h2 className="text-xl font-semibold mb-2">Prompt Diff (v1.2.0 → v1.3.0-beta)</h2>
      <div className="grid grid-cols-2 gap-4">
        <div className="border p-3 bg-red-50">
          <h3 className="font-mono text-sm">v1.2.0</h3>
          <pre className="text-xs">{`Answer using context:
{evidence}
Question: {query}`}</pre>
        </div>
        <div className="border p-3 bg-green-50">
          <h3 className="font-mono text-sm">v1.3.0-beta</h3>
          <pre className="text-xs">{`You are an expert assistant.
Answer using ONLY the context below.
If not in context, say "Not found".

Context:
{evidence}

Question: {query}
Answer with citations.`}</pre>
        </div>
      </div>
    </div>
  );
};
```

---

## Day 3 Checkpoint

Before moving on, can you:
- [ ] Explain **3 layers of metrics** (offline, online, generation)?
- [ ] Compute **prompt version comparison SQL** with `HAVING` and `PERCENTILE_CONT`?
- [ ] Code `recall_at_k`, `ndcg_at_k`, and `llm_as_judge_grounded`?
- [ ] Draw **RAG Eval Platform** with nightly Airflow + Spark + report?
- [ ] State the **stale gold set** problem and weekly refresh solution?

If yes to all 5, you're ready for Loop 6. If not, re-read.
