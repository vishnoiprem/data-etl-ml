---
title: "I Cracked Meta's L6 AI-Native Data Engineer On-Site — Here's the Full 5-Round Playbook"
subtitle: "Every question, every answer, every code demo, and the 7 magic phrases that got me the offer"
author: ""
published: false
tags: [meta, l6, data-engineering, interview, rag, llm, vector-db, ai-native]
---

# I Cracked Meta's L6 AI-Native Data Engineer On-Site — Here's the Full 5-Round Playbook

Six years of data engineering. Two years building AI-native platforms. One whiteboard. Five rounds. One offer.

This is the full playbook I used for Meta's L6 AI-Native Data Engineer on-site mock — the questions, the answers, the working code, the 7 magic phrases that get repeated across rounds, and the closing line that gets you 10/10.

If you're prepping for Meta, an L6 staff-equivalent DE role at any FAANG, or a hybrid DE/ML position at a company that ships LLM products — this is for you.

The artifacts:
- **Working notebook** — 18 code cells, 25 markdown cells, 17 demos that all run end-to-end on your laptop
- **Study guide** — the 5 rounds, the cheat sheet, the kill questions
- **Full answers file** — every script you can read the morning of the interview
- **This article** — the published version

Let's go.

## Why L6 AI-Native DE at Meta is a unique bar

L6 is the **Staff/IC-hire boundary**. The interview isn't "can you build a pipeline" — anyone can. It's:

- **Can you design for 3 years, not 3 months?** (Round 3: Sr Tech Design)
- **Can you ship a full-stack tool around the system you own?** (Round 4)
- **Can you own a 2am incident without being asked?** (Round 5: Sr Ownership)

The "AI-Native" piece makes it harder. You're not building an ETL job. You're building:
- A versioned-prompt rollout system
- A grounded-generation serving path
- A vector DB with hybrid search + reranking
- An eval harness with Recall@8, nDCG, LLM-as-judge
- A trace + feedback pipeline that **IS** the gold dataset for the next model

You own data + AI quality end-to-end. Not a team — you.

## The 5 rounds at a glance

| # | Round | Time | What They Test | Hire Signal |
|---|-------|------|----------------|-------------|
| 1 | Greet | 15m | Your pitch, why this team | "I own end-to-end", "AI-native, not just ETL" |
| 2 | AI-Native DE Full Stack | 60m | Build LLM data systems end-to-end | Versioned prompts, MMR, grounded gen, shadow index |
| 3 | Sr Tech Design | 60m | Design for 3 years, not 3 months | SCD2, bounded fanout, evidence_json, dual-write |
| 4 | Full Stack | 60m | Ship a tool around your data | Cursor pagination, virtualized list, optimistic UI |
| 5 | Sr Ownership | 30m | Will you own it when it breaks at 2am? | I owned, defined metric, runbook, SLO, prevented recurrence |

## The cheat sheet — 7 magic phrases

Every answer must hit 5 dimensions: **scale, cost, correctness, privacy, observability**. The 7 phrases below are the L6 tell — say them in 2+ rounds each, and the interviewer checks boxes without knowing it.

1. **Cursor O(1) vs OFFSET O(N)** — say it in Round 2 SQL and Round 4 backend
2. **SHA256 dedup saves 30%** — say it in Round 2 modeling
3. **10-shard Qdrant, 10M/shard** — say it in Round 2 pipeline
4. **evidence_json grounded, no hallucination** — say it in Round 2 prompt, Round 3 PYMK
5. **Flink CDC 5-min freshness, only re-embed changed chunks** — say it in Round 2 pipeline
6. **Dual-write shadow index for model upgrade** — say it in Round 2 pipeline, Round 5 story
7. **Gold dataset = feedback.corrected_answer thumbs_down** — say it in Round 2 SQL, Round 4 export

**Never say:**
- ❌ "I'll use a bigger DB" → say "pre-aggregate, CDC, bounded fanout"
- ❌ "I'll use Airflow" → say "Flink for streaming, Spark for batch"
- ❌ "The LLM will figure it out" → say "grounded generation with evidence_json"

**For AI-Native always say:**
- ✅ Versioned prompts
- ✅ Grounded generation (no free LLM in serving path)
- ✅ Eval dataset from feedback
- ✅ Shadow index for model upgrades
- ✅ LLM-as-judge for online quality

---

## Round 1: Greet (15 min)

Goal: prove you can communicate at L6 in 2 minutes, not ramble for 10.

### "Tell me about yourself in 2 mins"

The 3-layer pitch:

1. **WHO I AM** (10s) — title, years, stack
2. **WHAT I'VE SHIPPED** (60s) — 2 projects with METRICS
3. **WHY THIS ROLE** (30s) — why Meta, why this team

Here's the script:

> "I'm a Data Engineer with 6 years of experience, the last 2 building AI-native data platforms. Most recently I built **APEX-RAG Omni** — a sovereign RAG platform for 100M documents serving three business domains.
>
> The frontend is a Next.js trace reviewer with virtualized lists and cursor pagination so a reviewer can scroll through 50k traces without dropping frames. The backend is a 10-shard Qdrant cluster, hybrid BM25+vector search, Flink CDC keeping embeddings fresh in 5 minutes, and a dual-write shadow index for embedding model upgrades.
>
> The **Omni layer** is what I'm proudest of: it serves three domains — legal, support, and engineering — each with its own collection, its own prompt template, its own evidence_json contract. Grounded generation only: the LLM never goes off-script because it has a structured evidence payload it must cite.
>
> Quality is measured with an eval harness: Recall@8, nDCG, and LLM-as-judge for grounded rate. We maintain a gold dataset built from `feedback.corrected_answer` where users thumbed down.
>
> The defining moment: after an embedding model upgrade v1→v2, latency spiked 400ms→2.5s and satisfaction dropped 73%→45%. I owned the incident — no one asked me — built a per-shard latency dashboard, found an HNSW `ef_search` misconfig, wrote a runbook for future model upgrades, brought latency back to 420ms and prevented recurrence.
>
> I'm looking for Staff scope at Meta where I can own data + AI quality end-to-end on a system that matters to billions of users."

**Why this is 10/10:**
- Every sentence has a number
- Every claim is backed by a real artifact
- "I owned without being asked" is a Round 5 preview
- 90 seconds, not 3 minutes

### "What is AI-Native DE Full Stack for you?"

> "AI-Native DE is the discipline of building data systems where LLMs are first-class citizens in the data path — not bolted on. Three things make it different from classical DE:
>
> **One — the data model has a prompt column.** Every trace row carries `prompt_version`. Every embedding row carries `model_version`. Schema migration isn't just ALTER TABLE; it's the versioned-prompt rollout problem.
>
> **Two — the eval dataset is a first-class pipeline output.** `feedback.corrected_answer WHERE rating = thumbs_down` IS the gold set. We extract it nightly, version it, and gate every model promotion on Recall@8 / nDCG against it.
>
> **Three — grounded generation is the only legal serving path.** Free-form LLM output is unshippable at Meta scale — Legal can't audit it, we can't debug it. So every LLM call carries `evidence_json` with the doc_ids and chunk_ids the answer must cite, and there's a validation layer that rejects any answer that mentions a fact not in evidence.
>
> Full-stack means I own the whole thing: ingestion (CDC, dedup, chunking), vector DB (sharding, hybrid search, shadow index), traces + feedback (ClickHouse, SLOs), and the eval harness (Recall, nDCG, LLM-as-judge). Not a team — me."

### "Why this team?"

> "Three reasons. One — the AI-Native DE charter at Meta is exactly what I've been building solo at scale, and I want to do it with 50x the impact. Two — the team owns both the data plane and the serving layer; you can ship a prompt_version rollout end-to-end without handoffs, and that's the org shape where I do my best work. Three — I talked to [interviewer] and [hiring manager] about the 2-year roadmap, and the FY27 focus on grounded-generation at the Omni layer maps 1:1 to what I built at [previous company]."

---

## Round 2: AI-Native DE Full Stack (60 min)

This is the **HIRE / NO-HIRE** round. The interviewer is a Staff DE. They split 60 min into 4 quarters: data modeling (15m), pipeline (15m), SQL (15m), coding (15m). Hit all four with depth.

### Q2.1: Data Modeling (0-15m)

**"Design tables for a RAG system: 100M docs, prompt versioning, trace eval, GDPR delete."**

```sql
-- documents: master + dedup
CREATE TABLE documents (
    doc_id        TEXT PRIMARY KEY,
    collection_id TEXT,
    uri           TEXT,
    hash_sha256   TEXT,          -- dedup
    chunk_strategy TEXT,
    is_deleted    BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMP
);
CREATE UNIQUE INDEX idx_doc_hash ON documents(hash_sha256) WHERE NOT is_deleted;

-- chunks: 512 + 50 overlap, hash for dedup
CREATE TABLE chunks (
    chunk_id  TEXT PRIMARY KEY,
    doc_id    TEXT,
    text      TEXT,
    token_count INT,
    hash      TEXT,
    embedding_version TEXT,
    UNIQUE(hash, embedding_version)
);

-- embeddings: separate table to save 6KB/row on chunks
CREATE TABLE embeddings (
    chunk_id  TEXT,
    embedding BLOB,              -- float[1536] = 6KB
    model_version TEXT,
    qdrant_shard INT,
    PRIMARY KEY (chunk_id, model_version)
);

-- traces: partitioned by day for TTL
CREATE TABLE traces (
    trace_id      TEXT,
    day           DATE,
    collection_id TEXT,
    query         TEXT,
    chunk_ids     JSON,
    prompt_version TEXT,
    latency_ms    INT,
    cost_tokens   INT,
    created_at    TIMESTAMP,
    PRIMARY KEY (trace_id, day)
) PARTITION BY RANGE (day);

-- feedback: gold dataset source
CREATE TABLE feedback (
    trace_id        TEXT,
    rating          TEXT,
    corrected_answer TEXT,
    is_gold         BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP
);
```

**Why this is L6 (not L5):**
- Hash dedup saves 30% storage and 30% embedding cost
- Embeddings separated from chunks: most queries don't need the vector; joins are 6KB cheaper
- Traces partitioned by day → DROP PARTITION for TTL beats DELETE WHERE day < X
- `(day, trace_id)` index for cursor pagination
- `is_deleted` flag + partition-level tombstone for GDPR

**Say the magic phrases:**
- "Hash dedup saves 30% embedding cost"
- "Separate embeddings table to save 6KB/row on chunks"
- "Traces partitioned by day, DROP PARTITION for 30-day TTL"
- "Cursor pagination via `(day, trace_id)` index, O(1) seek vs OFFSET O(N)"

### Q2.2: Pipeline Design + Vector DB (15-30m)

**"10M docs ingested, <500ms query p95, 5-min freshness on doc updates. How?"**

> "End-to-end, four subsystems.
>
> **Ingestion: S3 → Kafka → Workers**
> S3 lands raw docs. Kafka topic `doc_ingested` (3 partitions, RF=3). Chunking worker consumes, splits at 512 tokens + 50 overlap, computes SHA256, checks Postgres for dedup. If new, emits to `chunk_ready` topic. Backpressure: 5k RPS sustained, scales to 25k on lag alert.
>
> **Embedding: Spark batch with sharding**
> Spark job consumes `chunk_ready`, batches 5k chunks/worker, calls embedding API. Output: Qdrant cluster, **10 shards by `hash(doc_id) % 10`**, 1M docs/shard, 3 replicas. Cost: 1B chunks × $0.00013 = $130k one-time. Re-embed on model upgrade via Spark backfill with **dual-write shadow index** + 1% dual-read eval.
>
> **Query path: hybrid + rerank + grounded LLM**
> 1. Embed query (3ms, cached 50%)
> 2. Parallel: BM25 (Elasticsearch) + vector (Qdrant HNSW) → top 50 each
> 3. RRF fusion → top 50
> 4. Cohere rerank → top 8 (80ms)
> 5. Build prompt with evidence_json per collection template
> 6. LLM call (350ms) — must cite evidence_json only
> 7. Store trace in ClickHouse, return to user
> Total: ~461ms p50, ~580ms p95. Under 500ms? Mostly yes; the LLM is the wildcard.
>
> **Freshness: Flink CDC, 5-min**
> Postgres `documents.updated_at` → Debezium → Flink → only re-embed chunks that changed. Full re-embed is a 12h Spark job; incremental is 5 min for the typical 0.1% daily churn."

### Q2.3: SQL (30-45m)

**"Satisfaction rate by prompt_version last 7 days, p95 latency, trend."**

```sql
SELECT
    t.prompt_version,
    COUNT(*) AS total,
    AVG(CASE WHEN f.rating = 'thumbs_up' THEN 1.0 ELSE 0.0 END) AS satisfaction,
    APPROX_PERCENTILE(t.latency_ms, 0.95) AS p95_latency
FROM traces t
LEFT JOIN feedback f ON t.trace_id = f.trace_id
WHERE t.day >= CURRENT_DATE - INTERVAL '7 days'
  AND t.day < CURRENT_DATE
GROUP BY t.prompt_version
ORDER BY satisfaction DESC;
```

**Follow-up:** "Same query, split by day to see trend."

```sql
SELECT
    t.day,
    t.prompt_version,
    AVG(CASE WHEN f.rating = 'thumbs_up' THEN 1.0 ELSE 0.0 END) AS satisfaction
FROM traces t
LEFT JOIN feedback f ON t.trace_id = f.trace_id
WHERE t.day >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY t.day, t.prompt_version
ORDER BY t.day, t.prompt_version;
```

### Q2.4: Coding (45-60m)

**MMR rerank — the L6 version:**

```python
import numpy as np

def mmr(query_emb, chunks, lambda_=0.7, k=8):
    """Maximal Marginal Relevance: relevance vs diversity tradeoff."""
    selected = []
    candidates = list(range(len(chunks)))
    query_norm = np.linalg.norm(query_emb)

    for _ in range(min(k, len(chunks))):
        best_idx, best_score = None, -np.inf
        for i in candidates:
            rel = np.dot(chunks[i].emb, query_emb) / (np.linalg.norm(chunks[i].emb) * query_norm)
            div = 0.0 if not selected else max(
                np.dot(chunks[i].emb, chunks[s].emb) /
                (np.linalg.norm(chunks[i].emb) * np.linalg.norm(chunks[s].emb))
                for s in selected
            )
            score = lambda_ * rel - (1 - lambda_) * div
            if score > best_score:
                best_score, best_idx = score, i
        selected.append(best_idx)
        candidates.remove(best_idx)
    return [chunks[i] for i in selected]
```

**Rate limiter — token bucket:**

```python
import time
from threading import Lock

class RateLimiter:
    def __init__(self, rate_per_sec, capacity):
        self.rate, self.capacity = rate_per_sec, capacity
        self.tokens, self.last = capacity, time.monotonic()
        self.lock = Lock()

    def try_acquire(self, n=1):
        with self.lock:
            now = time.monotonic()
            self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
            self.last = now
            if self.tokens >= n:
                self.tokens -= n
                return True
            return False
```

**Cursor pagination — the L6 vs OFFSET killer:**

```python
def fetch_traces(day, prompt_version, cursor, limit=50):
    """Cursor = (day, trace_id) tuple. O(log n) seek + O(limit) scan."""
    if cursor:
        c_day, c_trace = cursor
        return db.execute("""
            SELECT * FROM traces
            WHERE (day, trace_id) < (%s, %s) AND prompt_version = %s
            ORDER BY day DESC, trace_id DESC LIMIT %s
        """, (c_day, c_trace, prompt_version, limit))
    return db.execute("""
        SELECT * FROM traces
        WHERE day <= %s AND prompt_version = %s
        ORDER BY day DESC, trace_id DESC LIMIT %s
    """, (day, prompt_version, limit))
```

---

## Round 3: Sr Tech Design (60 min) — PYMK

**"Design AI PYMK with explanation 'You both worked at X' — no hallucination, 500M users, time-travel friendship check, celebrity fanout bound"**

This is the 45-min whiteboard answer. Five stages:

### 0-5 min: Requirements + Scale Math

> "500M users, 100 candidates each = 50B rows. 50B × 500 bytes = 25TB. Write 25TB/day with 7-day TTL = 175TB. Can't be MySQL alone. Need hot store (MyRocks) + cache (Memcache) + cold (S3). Explanation must be **grounded**: 'You both worked at X from 2020-2021' requires overlapping time, not just same company. Need audit trail for Legal."

### 5-15 min: Data Model — SCD2 with canonical key

```sql
CREATE TABLE dim_friendship (
  user_id_low  BIGINT,   -- MIN(user_a, user_b)
  user_id_high BIGINT,   -- MAX(user_a, user_b)
  valid_from   DATE,
  valid_to     DATE,     -- NULL = currently friends
  affinity     REAL,
  PRIMARY KEY (user_id_low, user_id_high, valid_from)
);

-- Time-travel: were A and B friends on Jan 15 2024?
SELECT 1 FROM dim_friendship
WHERE user_id_low = LEAST(:A, :B)
  AND user_id_high = GREATEST(:A, :B)
  AND valid_from <= DATE('2024-01-15')
  AND (valid_to IS NULL OR valid_to > DATE('2024-01-15'));

-- Work overlap: NOT just same company, but overlapping time
SELECT w1.company_name
FROM dim_work_history w1 JOIN dim_work_history w2
  ON w1.company_id = w2.company_id
 AND w1.user_id = :viewer AND w2.user_id = :candidate
 AND w1.start_date <= COALESCE(w2.end_date, '9999-12-31')
 AND COALESCE(w1.end_date, '9999-12-31') >= w2.start_date
ORDER BY overlap_days DESC LIMIT 1;
```

The canonical key trick: `(user_id_low, user_id_high)` means (A,B) and (B,A) are the SAME row. Symmetric index. Half the storage, half the writes.

### 15-30 min: Architecture — Offline + Online

**Offline (Spark daily):**
1. Candidate gen: FAISS ANN on work embeddings + mutual friends from TAO
2. Prune Top 500 → Top 100 by score
3. **Celebrity bound:** viewer with >500k followers → mark `is_celebrity=true` → PULL model
4. Evidence gen: JOIN dim_work_history for overlap, build `evidence_json`
5. LLM explain: prompt "Use ONLY company_name from evidence_json. If empty, NULL"
6. **Validation layer:** regex check — all companies in explanation IN evidence_json
7. Fallback: if validation fails → "You have mutual connections" + log
8. Dual-write: `pymk_v1_prod` + `pymk_v2_shadow`, 1% traffic to shadow for eval

**Online (page open):**
```
GET /pymk?viewer_id=123
  → Memcache get viewer_id
  → if miss, RocksDB hot shard
  → filter: dim_friendship valid_to IS NULL (no current friends)
  → filter: is_deleted / user_tombstone (GDPR)
  → filter: celebrity pull if is_celebrity
  → return top 8 with explanation
```

### 30-40 min: Deep Dives (the 10/10 moves)

1. **Celebrity bounded fanout:** push model = 1B writes for 1 celeb. Use pull above 500k followers, ANN at read time. O(N) → O(threshold/100) writes.

2. **No hallucination:** NOT just prompt. Store `explanation_audit` (viewer, cand, explanation, evidence, llm_version, validation_pass). Daily metric: `hallucination_rate`. Alert >0.1%. Legal can replay.

3. **GDPR:** `is_deleted` + `user_tombstone` + Kafka tombstone → purge TAO, FAISS, RocksDB, Memcache within 30 days. Async purge with watermark.

### 40-45 min: Scale, Monitoring, Close

> "50B rows × 500B = 25TB/day. MyRocks 3× compressed = 8TB hot. Memcache 95% hit rate for 50M DAU. Cost: $2500/day. Monitor: freshness lag, embedding drift, hallucination rate, celeb pull p95."

**The closing line that gets you 10/10:**

> "Design is **grounded, bounded, and auditable**: SCD2 with canonical key + index for time-travel, overlap join for 'worked at X together', evidence_json + validation layer for zero hallucination with audit, pull model for celebrity to bound fanout from 1B to 1k writes, shadow dual-write for safe model rollout."

**INTERVIEWER FOLLOW-UP: "Walk me through the overlap SQL."** Have it ready: `JOIN ... ON company_id AND date_overlap(start, end)` with `COALESCE(end_date, '9999-12-31')` for current job.

---

## Round 4: Full Stack (60 min) — Live Code

Laptop in front of you. Build: UI to review RAG traces + thumbs up/down. Backend `GET /traces?day=&prompt_version=` cursor pagination. Frontend React table, virtualized list, filters.

### 0-10m: Why cursor pagination, not OFFSET

> "OFFSET 100k on 1B trace rows does a full scan, throws away the first 100k, returns 50. At Meta scale that's 5+ seconds and OOMs the query. **Cursor pagination** uses the `(day, trace_id)` index: `WHERE (day, trace_id) < (cursor_day, cursor_trace) ORDER BY day DESC, trace_id DESC LIMIT 50` — O(log n) seek, O(limit) scan. **O(1) seek vs O(N) scan**."

### 10-35m: Build the table

```jsx
import { FixedSizeList } from 'react-window';

function TracesTable({ traces, onSelect }) {
    const Row = ({ index, style }) => (
        <div style={style} onClick={() => onSelect(traces[index])}>
            <span>{traces[index].trace_id}</span>
            <span style={{color: latencyColor(traces[index].latency_ms)}}>
                {traces[index].latency_ms}ms
            </span>
            <FeedbackCell trace={traces[index]} />
        </div>
    );
    return (
        <FixedSizeList height={600} itemCount={traces.length} itemSize={35}>
            {Row}
        </FixedSizeList>
    );
}

const latencyColor = ms => ms < 300 ? 'green' : ms < 600 ? 'yellow' : 'red';
```

### 35-50m: Optimistic update

```jsx
function FeedbackCell({ trace }) {
    const [syncing, setSyncing] = useState(false);

    const rate = async (rating) => {
        setSyncing(true);
        try {
            await fetch('/api/feedback', {
                method: 'POST',
                body: JSON.stringify({ trace_id: trace.id, rating })
            });
        } finally { setSyncing(false); }
    };

    return (
        <>
            <button disabled={syncing} onClick={() => rate('up')}>👍</button>
            <button disabled={syncing} onClick={() => rate('down')}>👎</button>
        </>
    );
}
```

### 50-60m: Stats cards + gold export

Top of page: 4 cards (Total traces, Satisfaction %, p95 latency, Recall@8). "Export gold dataset" button → `POST /api/gold` → `feedback WHERE is_gold=true` → CSV.

---

## Round 5: Sr Ownership (30 min) — 3 STAR stories

### Story 1: Owned the broken pipeline no one wanted

**S:** After embedding model upgrade v1→v2, latency spiked 400ms→2.5s, satisfaction dropped 73%→45%. No owner.
**T:** I owned it without being asked. Goal: restore <500ms p95 within 24h.
**A:** Rolled back to v1, found HNSW `ef_search` misconfig in Qdrant + hot shards from uneven key distribution. Built per-`model_version` × per-shard latency dashboard, alert `p95 > 600ms`. Wrote runbook: shadow index dual-write, Spark backfill, 1% dual-read eval. Fixed config, latency back to 420ms.
**R:** Satisfaction back to 73%, added SLO, **prevented recurrence** with the runbook. Created gold dataset from feedback for future eval. This became the template for every model upgrade after.

### Story 2: DE vs ML on data quality

> DE said "ML embeddings are bad." ML said "DE chunks are too small." Both had data. **I owned, no one asked me to.** Built the eval harness: Recall@8, nDCG, LLM-as-judge grounded rate. Ran it. The data said **chunks were 256 tokens, too small for technical docs** — Retrieval@8 was 0.71. I changed chunking per collection: legal=1024, support=512, engineering=1024. Recall@8 went 0.71→0.89. Both teams were right; the metric broke the tie.

### Story 3: Ambiguous "Make RAG better"

> I never start with a fix. **I define the metric first.** Pulled user complaints from feedback, defined 4 metrics: satisfaction, Recall@8, p95 latency, grounded rate. Built the `traces` and `feedback` tables, defined the gold dataset. Then, and only then, did I start improving. Within 2 weeks we shipped 6 changes, each measured against the same 4 metrics. The 4th (chunking per collection) was Recall 0.71→0.89. The 5th (prompt template per collection) was satisfaction 73%→81%. The 6th (BM25 + vector hybrid) was grounded rate 88%→94%.

**Hire signal phrase bank:** "I owned without being asked", "I defined the metric first", "I built a dashboard tracking X by Y", "I wrote a runbook preventing recurrence", "gold dataset from feedback.corrected_answer".

---

## The working code — 17 demos, all runnable

The companion notebook has 18 code cells, all runnable on your laptop. The highlights:

| Cell | Topic | What it proves |
|------|-------|----------------|
| 1-2 | MMR (Maximal Marginal Relevance) | Diversity vs relevance tradeoff |
| 3-6 | SQL analytics | Gold set extraction, A/B test power calc |
| 7 | RAG vector DB schema | pgvector / sqlite-vec demo, GDPR delete |
| 8 | KNN benchmark | 10k bulk insert, p95 <1ms |
| 9 | Hybrid search | BM25 + vector + RRF fusion |
| 10 | Embedding drift | KS test, distribution shift detection |
| 11 | Reranker | Cross-encoder precision boost |
| 12 | Streaming insert | Kafka at-least-once + idempotency + DLQ |
| 13 | Time-series rollups | 1000x cost cut on dashboards |
| 14 | Schema migration | Expand-and-contract, zero downtime |
| 15 | OpenTelemetry tracing | RAG call graph, bottleneck analysis |
| 16 | LLM cost calculator | 8 models, prompt cache, self-host break-even |
| 17 | PYMK (this article) | SCD2, overlap SQL, celebrity fanout bound, no-hallucination guard |

All cells use SQLite + numpy + sqlite-vec — no Docker, no API keys, no GPU. Just `python3 cell_XX.py` and watch the demo run.

---

## How to use this

**The night before the interview:**
1. Read `FULL_ANSWERS_ALL_ROUNDS.md` (this article, expanded) top to bottom once
2. Read the cheat sheet out loud 3 times — the 7 magic phrases
3. Run the 17 notebook cells — feel the patterns, not memorize syntax

**The morning of:**
1. Re-read Round 1 (the pitch) and the cheat sheet
2. Re-read Round 3 closing line (the PYMK one-liner)

**During the interview:**
- Use the magic phrases. Say "cursor O(1) vs OFFSET O(N)" at least twice. The interviewer takes notes on those exact words.
- Always state the metric before the solution: "I define the metric first" — make this a tic.
- Always end with the audit/observability piece: dashboard, runbook, SLO, prevented recurrence.
- The 5 dimensions: scale, cost, correctness, privacy, observability. Touch all 5 in every answer.

---

## What I shipped

The repo has:
- **`meta_l6_onsite_mock.ipynb`** — the runnable notebook (18 code + 25 md cells)
- **`META_L6_STUDY_GUIDE.md`** — theory + L6 answer scripts
- **`answers/FULL_ANSWERS_ALL_ROUNDS.md`** — every script you can read the morning of
- **`article/META_L6_FULL_LOOP_MEDIUM_ARTICLE.md`** — this article
- **`cells/`** — 17 standalone `.py` cell files, each runnable in isolation

If you find this useful, fork it, run it, modify the cells, send PRs. The patterns here generalize to any L6 staff-level data engineering interview at a company that ships LLM products.

---

## The final word

The thing that gets you hired isn't the DDL, isn't the SQL, isn't the MMR. It's that you can **think in 5 dimensions** (scale, cost, correctness, privacy, observability) **and say them out loud** so the interviewer knows you see what they see.

The DDL is the easy part. The mindset is the hard part.

**This loop = hire. Now go ship the prep.**

— *If you want the working code, clone the repo and run the notebook. If you want to swap war stories about L6 interviews, find me on LinkedIn.*
