# Meta L6 Onsite Mock - LOOP 2 (5 Rounds, 3-4 hours)

**Role:** L6 AI-Native Data Engineer (Full Stack) - Meta
**Total Duration:** 3-4 hours
**Format:** 5 rounds, different interviewers per round, no question repeats from Loop 1

---

## Process Breakdown

| # | Round | Duration | Interviewer Type | Focus |
|---|-------|----------|------------------|-------|
| 1 | Greet | 15 min | NEW HM | Why AI-Native vs pure DE, hardest decision, weakness |
| 2 | AI-Native DE Full Stack | 60 min | Sr Engineer | Fine-tuning pipeline from gold dataset + PII scrubbing |
| 3 | Sr Tech Design | 60 min | Architect | AI Code Search + ACL + AST chunking |
| 4 | Sr Ownership | 30 min | Sr Manager | ES->Qdrant migration, disagreed with PM |
| 5 | Full Stack (UI/UX build) | 60 min | Frontend Sr | Prompt Playground side-by-side A/B |

---

## LOOP 2 - ROUND 1: Greet (15 mins) - NEW Questions

**Interviewer is different HM, wants different angle.**

---

### Q1: Walk me through your resume - but focus on why you switched from pure DE to AI-Native DE

**L6 Answer (2 mins):**

> "First 4 years pure DE - built Spark pipelines, Airflow, data warehouse. Last 2 years I realized pipelines without eval are useless for AI. Example: I built ingestion for 10M docs, but RAG satisfaction was 45% because chunks were wrong - pure DE would say pipeline green. AI-Native DE says pipeline must track Recall@8, grounded rate, cost per query. So I built APEX-RAG Omni with traces table day-partitioned, feedback gold dataset, prompts versioned SCD2, eval harness with LLM-as-judge. That's AI-Native - DE owns AI quality, not just data movement."

---

### Q2: What is the hardest technical decision you made in APEX-RAG?

**L6 Answer:**

> "Hardest: Qdrant vs Elasticsearch for 100M docs. ES BM25 is good but vector search O(N) slow at 1B chunks. Qdrant HNSW O(log N) but needs tuning ef_search. I benchmarked: ES 1.2s p95, Qdrant 320ms p95 with hybrid BM25+vector. Decision: Qdrant cluster 10 shards, 10M/shard, 3 replicas, hybrid search. Tradeoff: Qdrant needs manual shard rebalancing, ES auto. I chose latency, built dashboard for shard size skew."

---

### Q3: If I ask your previous teammate, what would they say is your weakness?

**L6 Answer (honest + growth):**

> "They'd say I over-own. Example: When latency spiked 400->2500ms, I owned without being asked, rolled back, built dashboard + runbook, but I didn't delegate - I fixed alone. Now I delegate shadow index backfill to junior DE and I own eval dashboard, so I scale."

---

## LOOP 2 - ROUND 2: AI-Native DE Full Stack (60 mins) - NEW Scenario

**Interviewer says:** "Last loop was RAG ingestion. This loop: Design fine-tuning data pipeline from your gold dataset."

---

### Q1 Data Modeling (0-15m): Design tables for LLM fine-tuning from feedback gold dataset

> "You have feedback table with corrected_answer where thumbs_down. Need to build fine-tuning dataset for LLM that improves grounded answers. Design tables with PII scrubbing, versioning, data quality."

**YOUR L6 ANSWER - Draw this (Different from Loop 1):**

```sql
-- Loop 1 was traces + documents. Loop 2 is fine-tuning dataset
gold_dataset(
  gold_id PK,
  trace_id FK,
  query TEXT,
  original_chunks JSON,
  original_answer TEXT,
  corrected_answer TEXT,
  rating thumbs_down,
  is_pii_scrubbed BOOL,
  pii_types ARRAY,
  created_at
)

fine_tuning_jobs(
  job_id PK,
  model_version v1.2.0->v1.3.0,
  gold_ids ARRAY,
  status pending/running/completed,
  training_loss FLOAT,
  eval_recall FLOAT,
  created_at
)

fine_tuning_examples(
  example_id PK,
  job_id FK,
  prompt TEXT,
  completion TEXT,
  evidence_json JSON,
  is_used BOOL
)

pii_scrub_log(
  gold_id FK,
  original_text TEXT,
  scrubbed_text TEXT,
  pii_found [email, ssn, phone],
  scrubber_version
)
```

**Say:** "Gold dataset from Loop 1 feedback.corrected_answer becomes training data. Must scrub PII before fine-tuning - email, SSN. I keep original + scrubbed + log for audit. Fine-tuning examples have prompt with evidence_json to keep grounded."

---

### Q2 Pipeline Design (15-30m): Design pipeline from thumbs_down to fine-tuned model

**YOUR ANSWER (Different from ingestion pipeline):**

> "Flow:
>
> 1. **Feedback table** -> Flink job listens `rating=thumbs_down AND corrected_answer IS NOT NULL` -> push to gold_dataset raw
> 2. **PII Scrubber Worker:** Presidio + regex, scrubs email/SSN/phone, writes pii_scrub_log, marks is_pii_scrubbed true
> 3. **Data Quality Check:** LLM-as-judge checks corrected_answer is grounded in original_chunks evidence_json, not hallucinating - if grounded rate <90% reject example
> 4. **Fine-tuning Job Creator:** Daily Spark job creates job_id, selects gold_ids where is_pii_scrubbed and quality passed, 80% train 20% eval, generates `prompt = PROMPT_TEMPLATE + evidence_json + query`, `completion = corrected_answer`
> 5. **Fine-tune:** Calls LLM fine-tune API, tracks training_loss
> 6. **Eval:** New model vs old on eval set - Recall@8, grounded rate, satisfaction - only promote if +2%
> 7. **Dual-write shadow:** New model serves 1% traffic via shadow prompt_version v1.3.0-beta"

**L6 Keywords:** PII scrubbing, LLM-as-judge for data quality, shadow 1%, grounded check.

---

### Q3 SQL (30-45m): New SQL - Cost + Data Quality, not satisfaction

> "Tables: gold_dataset, fine_tuning_jobs, traces. Write SQL: Cost per fine-tuning job + PII leak rate + which corrected answers still hallucinate"

**YOUR L6 SQL:**

```sql
-- Cost per job: embedding + fine-tune API cost
SELECT
  j.job_id,
  j.model_version,
  COUNT(e.example_id) AS examples,
  COUNT(e.example_id) * 0.0042 AS fine_tune_cost_usd,
  j.eval_recall,
  j.status
FROM fine_tuning_jobs j
JOIN fine_tuning_examples e ON j.job_id = e.job_id
GROUP BY j.job_id, j.model_version, j.eval_recall, j.status
ORDER BY j.created_at DESC;

-- PII leak rate: how many scrubbed examples still leak
WITH leak_check AS (
  SELECT
    g.gold_id,
    g.is_pii_scrubbed,
    g.corrected_answer,
    -- regex check if PII still present
    CASE
      WHEN g.corrected_answer ~* '[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}'
        OR g.corrected_answer ~* '\b\d{3}-\d{2}-\d{4}\b'
        OR g.corrected_answer ~* '\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
      THEN TRUE
      ELSE FALSE
    END AS still_has_pii
  FROM gold_dataset g
  WHERE g.is_pii_scrubbed = TRUE
)
SELECT
  COUNT(*) AS total_scrubbed,
  SUM(CASE WHEN still_has_pii THEN 1 ELSE 0 END) AS leaks,
  ROUND(
    100.0 * SUM(CASE WHEN still_has_pii THEN 1 ELSE 0 END) / COUNT(*),
    2
  ) AS leak_rate_pct
FROM leak_check;

-- Which corrected answers still hallucinate (grounded in evidence_json?)
SELECT
  g.gold_id,
  g.query,
  g.corrected_answer,
  -- LLM-as-judge score: 1 = grounded, 0 = hallucinated
  llm_judge_grounded(g.corrected_answer, g.original_chunks) AS grounded_score,
  g.pii_types
FROM gold_dataset g
WHERE llm_judge_grounded(g.corrected_answer, g.original_chunks) < 0.5
ORDER BY g.created_at DESC
LIMIT 100;
```

---

### Q4 Coding (45-60m): Code PII scrubber + Semantic Cache (Different from MMR)

```python
# PII Scrubber - must code in interview
import re
from typing import Tuple, List

PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "ssn":   r"\b\d{3}-\d{2}-\d{4}\b",
    "phone": r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "cc":    r"\b(?:\d[ -]*?){13,16}\b",
}

def scrub_pii(text: str) -> Tuple[str, List[str]]:
    """
    Returns (scrubbed_text, pii_types_found).
    Replaces PII with tokens like [EMAIL], [SSN], [PHONE].
    """
    pii_found = []
    scrubbed = text
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, scrubbed)
        if matches:
            pii_found.append(pii_type)
            scrubbed = re.sub(pattern, f"[{pii_type.upper()}]", scrubbed)
    return scrubbed, pii_found


# Semantic cache to save LLM cost - cache by query embedding
import hashlib
from collections import OrderedDict

class SemanticCache:
    """
    LRU cache keyed by SHA256(embedding). Capacity 10k.
    Save cost: cache hit avoids embedding + LLM call = $0.0042/query saved.
    """
    def __init__(self, capacity: int = 10_000):
        self.capacity = capacity
        self.cache: OrderedDict[str, dict] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def _key(self, query: str) -> str:
        # In real impl: embed first, hash embedding vector
        return hashlib.sha256(query.encode()).hexdigest()

    def get(self, query: str):
        key = self._key(query)
        if key in self.cache:
            self.hits += 1
            self.cache.move_to_end(key)
            return self.cache[key]
        self.misses += 1
        return None

    def put(self, query: str, response: dict):
        key = self._key(query)
        self.cache[key] = response
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def stats(self):
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        return {"hits": self.hits, "misses": self.misses, "hit_rate": hit_rate}
```

**Hire Signal:** PII scrubbing, semantic cache to save cost, dedup.

---

## LOOP 2 - ROUND 3: Sr Tech Design (60 mins) - NEW Design

**Interviewer:** "Loop 1 was PYMK. This loop: Design AI Code Search & Explanation - search 100M code files, explain code, no hallucination"

---

### YOUR L6 WHITEBOARD (45 mins):

#### 1. Requirements (5m)

- 100M code files, 500M users, search code + explain "What does this function do?"
- Must be grounded - no hallucination - cite file + line
- ACL: private repos only visible to team
- Time-travel: "What did this file look like on Jan 15?"
- Freshness: 5-min from commit

#### 2. Data Model (10m) - Different from PYMK SCD2

```sql
code_files(
  file_id PK,
  repo_id FK,
  path,
  content,
  commit_sha,
  valid_from,
  valid_to      -- SCD2 for time-travel
)

code_chunks(
  chunk_id PK,
  file_id FK,
  start_line,
  end_line,
  text,
  embedding,
  language
)

repos(
  repo_id PK,
  name,
  is_private BOOL,
  team_id
)

repo_acl(
  repo_id FK,
  user_id,
  permission read/write   -- ACL check
)
```

#### 3. Architecture (25m)

**Ingestion:**
- Git commit webhook -> Kafka commit_event
- Chunking by **function/class (AST parser, not 512 tokens)** - critical L6 differentiator
- Embed with code embedding model (CodeBERT/StarCoder)
- Qdrant 20 shards by `hash(repo_id) % 20`, 5M files/shard

**Query:**
1. User query "How to do checkpoint in Flink?" -> embed -> Qdrant search Top 50 across shards
2. **ACL filter BEFORE LLM**: JOIN `repo_acl` WHERE `user_id=:user_id AND permission=read` - filter before sending to LLM
3. LLM explanation prompt: `"Based on these code chunks: {evidence_json with file:line citations}, answer: {query}"`
4. **Grounded generation**: if not in evidence, return "Not found in accessible code"
5. Return: answer + list of `file:line` citations + confidence score

**Time-travel:**
- "What did this file look like on Jan 15?" -> query `code_files` with `valid_from <= '2024-01-15' AND valid_to > '2024-01-15'`
- Embed that snapshot, search Qdrant shadow index (snapshots indexed daily)

**Feedback loop:**
- Thumbs up/down on explanation
- LLM-as-judge: "Is the explanation grounded in cited code? yes/no"
- gold_dataset -> fine-tuning (Loop 2 Round 2)

#### 4. Scale (5m)

- 100M files * 10 chunks avg = 1B chunks, 20 shards, 50M/shard
- **ACL check in Qdrant filter, not after** - saves LLM cost
- Private repo: Qdrant payload team_id, filter by team_id

**L6 Keywords:** AST chunking not token, ACL filter before LLM, time-travel SCD2, grounded evidence_json with file:line citation, semantic cache for code.

**Different from Loop 1 PYMK:** PYMK was social graph + SCD2 friendships. This is code + ACL + AST.

---

## LOOP 2 - ROUND 4: Sr Ownership (30 mins) - NEW Story

### Q: Tell me about migration from ES to Qdrant - risk of data loss

**STAR - Different from latency spike:**

**S:** "We had Elasticsearch for 10M docs, cost $50k/month, latency 1.2s. Decision to migrate to Qdrant to save cost and latency. Risk: 10M docs, 100M chunks, downtime, data loss."

**T:** "Own migration with zero downtime and zero data loss."

**A:** 
1. Built dual-write: New docs written to both ES and Qdrant shadow collection `docs_v2_shadow` via Kafka.
2. Backfill: Spark job backfilled 10M docs from ES to Qdrant 10 shards, 5M/shard, verified count.
3. Shadow read: 1% traffic reads from Qdrant shadow, compared Recall@8 ES vs Qdrant - Qdrant 0.89 vs ES 0.82.
4. Cutover: When shadow Recall > ES for 7 days, cutover 100% to Qdrant, kept ES as backup 2 weeks.
5. Rollback plan: If Qdrant p95>600ms, rollback to ES in 5 mins via feature flag `prompt_version`.

**R:** "Migrated zero downtime, latency 1.2s->420ms, cost $50k->$12k/month, zero data loss. Wrote migration runbook used by 2 teams."

---

### Q2: Tell me about time you disagreed with PM on priority

**STAR:** Use cost vs freshness story from Set 2 - said no to real-time Flink for v1 with data.

> "S: PM wanted real-time Flink CDC for v1, 5-min freshness for 10M docs.
> T: Push back, propose batch v1 + incremental.
> A: Built cost model: 10M docs * 1B chunks real-time embedding = $130k/month, batch = $12k/month. Showed PM the data - freshness 5min vs 24hr, but cost 10x. PM agreed, we shipped batch v1, 95% use case covered, 1% premium tier got Flink CDC.
> R: Saved $118k/year, PM later thanked me - revenue was not there to justify 10x cost for v1."

---

## LOOP 2 - ROUND 5: Full Stack (60 mins) - NEW Build

**Interviewer:** "Loop 1 was trace reviewer. Loop 2: Build Prompt Playground - compare v1.2.0 vs v1.3.0-beta side-by-side"

---

### YOUR L6 BUILD (Different UI):

#### 0-10m API Design

> "API: `POST /compare {query, collection, prompt_versions: [v1.2.0, v1.3.0-beta]}` -> returns `{results: [{version, answer, chunks, latency, grounded}]}`. Cursor not needed here, but I keep grounded evidence_json."

#### 10-35m Side-by-side UI

```tsx
// Prompt Playground - side-by-side A/B comparison
import { useState } from "react";

const [versions, setVersions] = useState(["v1.2.0", "v1.3.0-beta"]);
const [query, setQuery] = useState("");
const [comparison, setComparison] = useState(null);
const [loading, setLoading] = useState(false);

const compare = async () => {
  setLoading(true);
  const res = await fetch("/api/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      collection: "tech_docs",
      prompt_versions: versions,
    }),
  });
  const data = await res.json();
  setComparison(data);
  setLoading(false);
};

return (
  <div className="grid grid-cols-2 gap-4 p-6">
    {/* Left panel - v1.2.0 */}
    <div className="border rounded p-4">
      <h3>v1.2.0 (control)</h3>
      <p>{comparison?.results[0]?.answer}</p>
      <small>Latency: {comparison?.results[0]?.latency}ms</small>
      <small>Grounded: {comparison?.results[0]?.grounded ? "yes" : "no"}</small>
      <button onClick={() => selectWinner("v1.2.0")}>Pick this</button>
    </div>
    {/* Right panel - v1.3.0-beta */}
    <div className="border rounded p-4">
      <h3>v1.3.0-beta (candidate)</h3>
      <p>{comparison?.results[1]?.answer}</p>
      <small>Latency: {comparison?.results[1]?.latency}ms</small>
      <small>Grounded: {comparison?.results[1]?.grounded ? "yes" : "no"}</small>
      <button onClick={() => selectWinner("v1.3.0-beta")}>Pick this</button>
    </div>
  </div>
);
```

#### 35-50m Add winner selection + gold dataset

```tsx
// Optimistic winner -> save to fine_tuning gold dataset
const selectWinner = async (winnerVersion: string) => {
  // Save to fine_tuning gold dataset (Loop 2 Round 2!)
  await fetch("/api/feedback/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      winner_version: winnerVersion,
      loser_version: versions.find((v) => v !== winnerVersion),
      comparison_id: comparison?.comparison_id,
    }),
  });
  // Optimistic UI - show checkmark
  setWinner(winnerVersion);
};
```

#### 50-60m Polish

> "Added **diff view** - highlight tokens that differ between v1.2.0 and v1.3.0-beta. Added **stats footer**: v1.2.0 satisfaction 73% vs v1.3.0 78%, p95 420 vs 380, Recall@8 0.89 vs 0.91 - so v1.3.0 wins."

**Different from Loop 1 Trace Reviewer:** Loop 1 was 1k-row table + cursor. Loop 2 is side-by-side A/B comparison + winner selection + diff.

---

## LOOP 2 vs LOOP 1 Summary

| Round | Loop 1 (Old) | Loop 2 (New) |
|-------|--------------|--------------|
| **AI-Native DE** | RAG ingestion 100M | Fine-tuning pipeline from gold + PII scrubbing + semantic cache |
| **Tech Design** | PYMK + time-travel friendship | Code Search + ACL + AST chunking + time-travel file |
| **Ownership** | Latency spike 400->2500ms | ES->Qdrant migration zero downtime |
| **Greet** | Why Meta, biggest impact | Why AI-Native vs pure DE, hardest decision, weakness |
| **Full Stack** | Trace reviewer 1k rows cursor | Prompt Playground side-by-side A/B |

**You now have 2 loops ready - no question repeats.**

---

## Want to run live mock for Loop 2 Tech Design?

Say "start mock loop 2 round 3" and I'll play the interviewer asking Code Search design questions - you whiteboard your answer.
