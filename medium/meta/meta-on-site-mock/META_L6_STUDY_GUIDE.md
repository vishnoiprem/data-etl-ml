# Meta L6 AI-Native Data Engineer — On-Site Mock Study Guide

> **Companion to:** `meta_l6_onsite_mock.ipynb` (run all cells for hands-on practice)

## 🎯 The 5 Rounds at a Glance

| # | Round | Time | What They Test | Hire Signal |
|---|-------|------|----------------|-------------|
| 1 | Greet | 15m | Your pitch, why this team | "I own end-to-end", "AI-native, not just ETL" |
| 2 | AI-Native DE Full Stack | 60m | Build LLM data systems end-to-end | Versioned prompts, MMR, grounded gen, shadow index |
| 3 | Sr Tech Design | 60m | Design for 3 years, not 3 months | SCD2, bounded fanout, evidence_json, dual-write |
| 4 | Full Stack | 60m | Ship a tool around your data | Cursor pagination, virtualized list, optimistic UI |
| 5 | Sr Ownership | 30m | Will you own it when it breaks at 2am? | I owned, defined metric, runbook, SLO, prevented recurrence |

---

## 🚨 THE CHEAT SHEET (Memorize This)

**Every answer must hit 5 dimensions:**
1. **Scale** — "at 1B traces/day", "fanout O(d²) = 90k writes", "10M docs"
2. **Cost** — "skip embedding low-quality docs", "separate embeddings table to save 6KB/row"
3. **Correctness** — "idempotent writes", "versioned prompts", "grounded generation, no free LLM"
4. **Privacy** — "GDPR tombstone + async purge", "check blocks table in gateway"
5. **Observability** — "trace_id everywhere", "p95 by prompt_version dashboard"

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

## 📚 ROUND-BY-ROUND DEEP DIVE

### ROUND 1: GREET (15m)

#### Q: "Tell me about yourself in 2 mins"

**THEORY — The 3-Layer Pitch:**
```
1. WHO I AM (10s)        → Title + years + stack one-liner
2. WHAT I'VE SHIPPED (60s) → 2 projects with METRICS (not duties)
3. WHY THIS ROLE (30s)    → Why Meta + why this team + what I'll own
```

**L6 ANSWER:**
> "I'm a Data Engineer who's gone AI-native. 5+ years building data platforms — Kafka, Flink/Spark, Postgres, ClickHouse. Last 1.5 years I pivoted: built RAG pipelines, an eval harness, and agent memory systems. I own pipelines end-to-end — ingestion, data quality, LLM eval, the whole loop.
>
> Most recent win: I built a RAG system on 10M docs with <500ms p95 retrieval. Drove chunk versioning, eval dataset from user feedback, and dual-write shadow index for model upgrades.
>
> I'm looking for Staff scope where I can own the AI data platform — not just ETL, but prompts, embeddings, eval — at Meta's scale."

**Keywords that signal L6:** end-to-end, own, versioned, eval, data quality for LLM, staff scope

#### Q: "What is AI-Native DE for you?"

**THEORY — The Parallel:**
```
Traditional DE          →  AI-Native DE
─────────────────       ─────────────────
Move data               →  Move data + context
Schema design           →  Chunking strategy = schema
Schema drift            →  Embedding drift = data quality
Unit tests              →  Eval dataset = test suite
Pipeline logs           →  LLM traces = fact table
Airflow DAG             →  Versioned prompts + traces
```

**L6 ANSWER:**
> "Traditional DE moves data. AI-Native DE moves **data + context**. Concretely:
> - Chunking strategy IS data modeling — bad chunks = bad retrieval = bad answers
> - Embedding drift IS data quality — re-embed when model changes
> - Eval dataset IS our test suite — built from feedback.corrected_answer
> - LLM traces ARE a fact table — partition by day, group by prompt_version for A/B
> - Prompts are versioned like code — never edit in place
>
> I treat prompts, embeddings, and traces as **first-class data assets**, not side effects."

**Then ASK THEM:**
> "What's the biggest bottleneck on this team today — eval harness, retrieval latency, or grounding/data quality for RAG?"

**FAIL SIGNAL:** Talking about Airflow + Hive. They're testing AI fluency, not 2018 DE.

---

### ROUND 2: AI-NATIVE DE FULL STACK (60m)

#### Q1: Data Modeling (10m) — RAG schema with GDPR, chunk versioning, feedback

**WHY this schema (the 6 tables):**

| Table | Purpose | L6 Design Choice |
|-------|---------|------------------|
| `documents` | Source of truth, GDPR tombstone | `is_deleted BOOLEAN` NOT hard delete |
| `chunks` | The actual data model | `UNIQUE(doc_id, chunk_hash, embedding_model_version)` for dedup |
| `embeddings` | Separate from chunks | `vector(1536)` = 6KB/row, expensive to scan inline |
| `prompts` | Versioned like code | Never edit in place, you lose A/B + rollback |
| `traces` | Fact table | Partition by day, 1B rows/day at Meta |
| `feedback` | Gold eval dataset | `corrected_answer IS NOT NULL` = labeled training data |

**L6 talking points:**
1. "Chunking IS a modeling decision — different docs need different splitters. I store `chunk_strategy` on `documents`."
2. "GDPR: I tombstone `documents.is_deleted=TRUE`, then async purge job deletes from `embeddings` and calls vector DB delete. Keep `traces` for 30 days for abuse investigation."
3. "Embeddings as separate table because `vector(1536)` is 6KB/row. If I store them inline with chunks, every analytics query loads the full vector."
4. "Prompts are versioned like code. If I edit prompt_v3 in place, I lose the ability to A/B test or roll back when satisfaction drops."
5. "Traces is partitioned by day — at Meta scale, 1B rows/day, you cannot query unpartitioned. Drop old partitions after 30 days, not DELETE rows."
6. "Feedback table is the eval set. `SELECT * FROM feedback WHERE corrected_answer IS NOT NULL` is labeled data I replay new prompts against before shipping."

#### Q2: RAG Pipeline (20m) — 10M docs, <500ms p95, 5min freshness

**THEORY — Lambda for RAG:**
```
           INGESTION (online, 5min freshness)
Doc update → Kafka → Flink CDC → invalidate Qdrant ID → upsert new chunks

           SERVING (online, <500ms p95)
Query → embed → Qdrant Top 50 → Cohere rerank → Top 8 → LLM
        ↓
   Redis cache query embedding (30% repeat queries)

           BACKFILL (offline, scale)
Spark batch: re-embed 10M docs at 5k RPS, write to Qdrant shadow index
```

**L6 phrases to drop:**
- "Hybrid search: BM25 + vector, then cross-encoder rerank in serving path"
- "BM25 catches exact-match (names, IDs) that vector misses"
- "Cache query embeddings in Redis — repeat queries are 30% of traffic"
- "Skip embedding for low-quality docs (>5k tokens, low info score) — cost control"
- "Lambda for RAG: offline batch backfill + online incremental freshness = best of both"
- "Idempotent via chunk_hash — if hash unchanged, skip re-embed"

#### Q3: MMR Rerank Coding (20m) — Avoid duplicate chunks

**WHY MMR:** Standard vector search returns redundant chunks (5 from same section). MMR balances **relevance** vs **diversity**.

**Formula:**
```
MMR(d) = λ · sim(d, query) - (1-λ) · max[sim(d, d_selected)]
         ↑                          ↑
     relevance               diversity penalty
```
- λ=0.7 → favor relevance (default)
- λ=0.3 → favor diversity (when chunks are very similar)

**Complexity:** O(k·N·D) — fine for k=8, N=50. If N=10k, use approximate MMR via HNSW.

**L6 line while coding:**
> "In prod, I'd never code this from scratch — Qdrant has built-in MMR, or I'd use Cohere Rerank API. This is the algo behind it though, and interviewers want to see I understand the math."

#### Q4: SQL — Measure RAG Quality (10m)

**The 3 RAG KPIs:**
1. **Satisfaction** = `AVG(CASE WHEN rating='thumbs_up' THEN 1 ELSE 0 END)`
2. **p95 latency** = `PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms)`
3. **Cost** = `SUM(cost_tokens)` per day (every LLM call has $$ cost)

**WHY GROUP BY day, not user:** Time series for dashboards (Grafana). Per-user is for cohort analysis, not daily monitoring.

**L6 add-ons:**
1. **A/B test by prompt_version** — add `t.prompt_version` to GROUP BY
2. **Build gold eval set** — `SELECT * FROM feedback WHERE corrected_answer IS NOT NULL`

---

### ROUND 3: SR TECH DESIGN — PYMK Feed (60m)

**What they test:** Can you design a system that **DOESN'T HALLUCINATE** at Meta scale?

**THEORY — The 3-Layer Anti-Hallucination Architecture:**
```
Layer 1: GRAPH (offline)
   friendships SCD2 → Spark GraphX → pymk_candidates (user, candidate, mutuals, score)

Layer 2: REASONS (offline, NO free LLM generation)
   candidate_reasons with TEMPLATE + evidence_json
   LLM only FILLS template with grounded evidence — never invents

Layer 3: SERVING (online)
   API → merge offline candidates + Redis live mutuals + privacy check
   NO LLM at request time — reasons are pre-computed
```

**WHY this design:**
- **SCD2 on friendships** = time travel. "Users who were friends 6 months ago" is a valid query for recency scoring.
- **Bounded fanout** = skip users with >5k friends. A user with 10k friends generates 10k² = 100M writes per friend-add.
- **Grounded generation only** = the prompt MUST include `evidence_json` and "use ONLY provided evidence". No evidence → "unknown".
- **No LLM in serving path** = serving path is just Redis lookup + template fill. LLM only runs offline for candidate_reasons pre-computation.

**TRAP: "What if LLM hallucinates the reason?"**
> "Two defenses:
> 1. **Grounded generation only** — prompt MUST say: 'Use ONLY the evidence_json provided. If a fact isn't there, output "unknown". Never invent.'
> 2. **LLM-as-judge eval** — nightly job, sample 1k reasons, judge checks: does summary mention a company not in evidence_json? If yes → fail + alert."

**Scale follow-up: "Re-embed 500M when model v2 drops?"**
> "**Dual-write + shadow index**:
> - Create `embeddings_v2` collection
> - Spark backfill at 5k RPS with exponential backoff
> - Serve reads from v1, dual-read 1% from v2 for shadow eval
> - Compare quality metrics for 7 days
> - Cutover via config flag, keep v1 for 7 days rollback
> - **Never in-place update** — that's how you corrupt prod"

**Hire words:** SCD2, grounded generation, evidence_json, dual-write, bounded fanout, idempotency.

---

### ROUND 4: FULL STACK — Build Trace Reviewer Tool (60m)

**What they test:** Can you SHIP a working internal tool fast? They want SPEED + API design, not auth or full CRUD.

**The 3-end-point minimum viable tool:**
- `GET /traces?day=...&prompt_version=...&cursor=...&limit=50`
- `POST /feedback {trace_id, rating, corrected_answer}`
- `GET /traces/{trace_id}` for detail view

**WHY cursor pagination, not OFFSET:**
- `OFFSET 1000 LIMIT 50` = scan 1050 rows, throw away 1000. At 1B rows/day, this kills the DB.
- Cursor `WHERE trace_id < last_id ORDER BY created_at DESC LIMIT 50` = index seek, O(log n).
- Same UX for the user (infinite scroll), 1000x faster backend.

**L6 phrases while coding:**
- "Cursor pagination, not OFFSET — OFFSET is O(n) scan"
- "Optimistic UI on feedback — don't wait for server, just show thumbs-up"
- "Filter by prompt_version from day 1 — you'll need it for A/B analysis tomorrow"
- "Virtualized list — 1k rows will tank React if I render naively"

**FAIL SIGNAL:** Building auth, roles, full CRUD. They want a working slice in 60m, not a finished product.

---

### ROUND 5: SR OWNERSHIP (30m)

**What they test:** L6 ≠ "I helped". L6 = "I owned end-to-end, defined the metric, and prevented recurrence."

**THEORY — The L6 STAR Upgrade:**
```
L4 STAR:  S/T/A/R as described in job ad
L5 STAR:  S/T/A/R with my specific actions
L6 STAR:  S/T/A/R + METRIC + PREVENTION
                              ↑           ↑
                          quantified    runbook/SLO
                          outcome       you left behind
```

#### Q1: Owned a broken pipeline no one wanted

**L6 ANSWER:**
> **S:** RAG p95 latency went from 400ms to 2.5s after we upgraded the embedding model.
>
> **T:** No owner. On-call was getting paged at 2am. Leadership wanted answers.
>
> **A:** I owned it end-to-end:
> 1. Rolled back the index to v1 to stop the bleeding — 10 min MTTR
> 2. Found root cause: smaller batch size caused Qdrant HNSW graph fragmentation
> 3. Built a dashboard: `embedding_drift_by_model_version` + `p95_by_version`
> 4. Wrote a runbook: how to roll back, how to detect drift, on-call playbook
> 5. Added an alert: p95 > 1s for 5 min pages on-call
>
> **R:** Latency back to 380ms. New SLO: p95 < 500ms. My dashboard is now the team's standard. Zero similar incidents in 6 months.

**L6 keywords:** owned, rolled back, root cause, dashboard, runbook, SLO, prevented recurrence.

#### Q2: DE vs ML team conflict on data quality

**L6 ANSWER:**
> "I proposed a **data contract**:
> - ML team defines the **gold dataset schema** (what 'good data' looks like)
> - DE team guarantees **freshness SLA** (data lands within 5 min of source)
> - DE team guarantees **schema SLA** (no breaking changes without notice)
>
> I wrote the contract as JSON, added **Great Expectations checks** in the pipeline that fail the DAG if contract breaks. Both teams now have measurable SLAs. Conflict resolved with metrics, not opinions."

#### Q3: Vague problem "Make RAG better"

**L6 ANSWER:**
> "First, I defined 'better' — I refused to optimize without a metric.
>
> 1. **Defined the metric:** satisfaction = thumbs_up / total, weighted by latency
> 2. **Built the eval set:** mined `feedback.corrected_answer` from prod, got 2k labeled examples
> 3. **Hypothesized:** chunk size 512 + reranker > current 256 no reranker
> 4. **Ran A/B:** 12% satisfaction lift, +50ms latency (acceptable)
> 5. **Shipped it** with monitoring and rollback plan
>
> The key was refusing to start work without a measurable definition of success."

**L6 keywords:** defined metric, eval set, A/B test, shipped, monitored.

---

## 🎯 5 L6 POWER PHRASES (Memorize)

When you say these, interviewers' ears perk up:
1. **"I own it end-to-end"** (not "I worked on")
2. **"Tradeoff: relevance vs diversity, picked X because..."** (shows decision-making)
3. **"Grounded generation only — never free-form LLM in serving path"** (shows AI maturity)
4. **"Idempotent, with DLQ and backfill from S3"** (shows prod experience)
5. **"I'd measure success as <metric> before shipping"** (shows data-driven thinking)

---

## 💀 KILLER QUESTIONS TO ASK THEM (at the end of any round)

These signal senior curiosity and dig for red flags:
1. "How do you detect embedding drift today?"
2. "Is your eval harness human-labeled or LLM-as-judge?"
3. "How do you handle prompt regressions in prod — auto-rollback?"
4. "What's the team's philosophy on grounded vs free-form LLM generation?"
5. "What's the biggest bottleneck — eval harness, retrieval latency, or grounding?"
6. "How do you version prompts — git, registry, or feature flag system?"

---

## 🏃 MOCK MODE: How to Run This

1. **Open the notebook** — `jupyter notebook meta_l6_onsite_mock.ipynb`
2. **Run all cells** — verify the code works (MMR, SQL, schema all run)
3. **Tell me "start round 2"** — I'll be the interviewer, 60-min timer
4. **Type your answer out loud** — I'll cut you off if you ramble, then critique
5. **After each answer** — I'll tell you what was L6 vs L5 vs L4

---

## 📁 Files in This Folder

| File | Purpose |
|------|---------|
| `meta_l6_onsite_mock.ipynb` | Hands-on code: schema, MMR, SQL, FastAPI, React, PYMK design |
| `META_L6_STUDY_GUIDE.md` | Theory, frameworks, scripts, cheat sheet (this file) |

**Recommended study order:**
1. Read this guide end-to-end (theory + scripts)
2. Open the notebook, run all cells (verify the code works)
3. Modify the MMR lambda, see how diversity changes
4. Modify the SQL, try different GROUP BYs
5. Say "start round 2" to me — live mock mode
