"""
Build the Meta L6 mock notebook programmatically.
This guarantees valid JSON and lets us execute it to verify it works.
"""
import nbformat as nbf
from pathlib import Path

nb = nbf.v4.new_notebook()
cells = []

# ════════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""# Meta L6 AI-Native DE On-Site Mock — Working Code + Theory

**Purpose:** Hands-on reference for the 5 on-site rounds. Each cell is runnable.

**Rounds:**
1. Greet (15m) — pitch
2. AI-Native DE Full Stack (60m) — modeling, RAG design, MMR code, eval SQL
3. Sr Tech Design (60m) — PYMK feed with anti-hallucination
4. Full Stack (60m) — trace reviewer tool
5. Sr Ownership (30m) — behavioral

**L6 cheat sheet keywords to drop in every answer:**
`end-to-end` · `versioned prompts` · `grounded generation` · `eval dataset` · `shadow index` · `bounded fanout` · `idempotent` · `SLO` · `LLM-as-judge`
"""))

# ════════════════════════════════════════════════════════════════════
# ROUND 2 — Q1: Data Modeling
# ════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""---

## ROUND 2 — Q1: Data Modeling for AI-Native RAG

**What they test:** Can you design a production schema for a RAG system with GDPR, chunk versioning, and feedback loops?

**Why this schema:**
- `documents` is source-of-truth, with `is_deleted` tombstone (GDPR requires soft delete + async purge, NOT hard delete from `traces` for 30 days)
- `chunks` is the actual data model — `(doc_id, chunk_hash, embedding_model_version)` UNIQUE prevents duplicate work when re-embedding
- `embeddings` is SEPARATE — vector(1536) = 6KB/row, expensive to scan; split lets you run analytics on `chunks` without loading vectors
- `prompts` is versioned like code — NEVER edit in place (you lose the ability to A/B test or roll back)
- `traces` is a FACT TABLE — partition by day, 1B rows/day at Meta scale
- `feedback` is the gold dataset — `corrected_answer IS NOT NULL` = labeled eval data
"""))

cells.append(nbf.v4.new_code_cell("""# RAG schema — the L6 answer for whiteboard
schema_sql = \"\"\"
-- 1. Source of truth (with GDPR tombstone)
CREATE TABLE documents (
    doc_id        UUID PRIMARY KEY,
    source        VARCHAR(50),     -- 'sharepoint', 's3', 'confluence'
    uri           TEXT,
    owner_id      UUID,            -- for GDPR lookup
    chunk_strategy VARCHAR(50),    -- 'langchain_recursive_512', 'semantic_v1' — chunking IS modeling
    ingested_at   TIMESTAMP,
    is_deleted    BOOLEAN DEFAULT FALSE,  -- tombstone, NOT hard delete
    hash          VARCHAR(64)      -- dedup at doc level
);

-- 2. Chunks = your data model
CREATE TABLE chunks (
    chunk_id               UUID PRIMARY KEY,
    doc_id                 UUID REFERENCES documents(doc_id),
    chunk_index            INT,
    text                   TEXT,
    token_count            INT,
    embedding_model_version VARCHAR(50),
    chunk_hash             VARCHAR(64),
    created_at             TIMESTAMP,
    UNIQUE (doc_id, chunk_hash, embedding_model_version),  -- dedup on re-embed
    INDEX idx_model_version (embedding_model_version)      -- for re-embed job
);

-- 3. Embeddings SEPARATE (vector column = 6KB/row, expensive)
CREATE TABLE embeddings (
    chunk_id     UUID PRIMARY KEY REFERENCES chunks(chunk_id),
    embedding    vector(1536),    -- OpenAI ada-002 dim; pgvector syntax
    model_version VARCHAR(50),
    created_at   TIMESTAMP
);

-- 4. Versioned prompts (NEVER edit in place)
CREATE TABLE prompts (
    prompt_id        UUID PRIMARY KEY,
    prompt_template  TEXT,
    version          INT,
    created_at       TIMESTAMP
);

-- 5. Traces = fact table, 1B rows/day at Meta scale
CREATE TABLE traces (
    trace_id              UUID,
    user_id               UUID,
    query                 TEXT,
    retrieved_chunk_ids   UUID[],
    prompt_version        INT REFERENCES prompts(version),
    response              TEXT,
    latency_ms            INT,
    cost_tokens           INT,
    created_at            TIMESTAMP,
    PRIMARY KEY (trace_id, created_at)
) PARTITION BY RANGE (created_at);  -- partition by day

-- Daily partition example
CREATE TABLE traces_2026_10_14 PARTITION OF traces
    FOR VALUES FROM ('2026-10-14') TO ('2026-10-15');

-- 6. Feedback = gold dataset for offline eval
CREATE TABLE feedback (
    feedback_id      UUID PRIMARY KEY,
    trace_id         UUID,
    rating           TEXT CHECK (rating IN ('thumbs_up', 'thumbs_down')),
    corrected_answer TEXT,   -- if NOT NULL = labeled training data
    created_at       TIMESTAMP
);
\"\"\"
print(schema_sql)"""))

cells.append(nbf.v4.new_markdown_cell("""**L6 talking points to say out loud while drawing this:**
1. "Chunking IS a modeling decision — different docs need different splitters. I store `chunk_strategy` on `documents`."
2. "GDPR: I tombstone `documents.is_deleted=TRUE`, then an async purge job deletes from `embeddings` and calls vector DB delete. I keep `traces` for 30 days for abuse investigation."
3. "Embeddings as separate table because `vector(1536)` is 6KB/row. If I store them inline with chunks, every analytics query loads the full vector."
4. "Prompts are versioned like code. If I edit prompt_v3 in place, I lose the ability to A/B test or roll back when satisfaction drops."
5. "Traces is partitioned by day — at Meta scale, 1B rows/day, you cannot query unpartitioned. Drop old partitions after 30 days, not DELETE rows."
6. "Feedback table is the eval set. `SELECT * FROM feedback WHERE corrected_answer IS NOT NULL` is labeled data I replay new prompts against before shipping."
"""))

# ════════════════════════════════════════════════════════════════════
# ROUND 2 — Q2: RAG Pipeline Design
# ════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""---

## ROUND 2 — Q2: RAG Pipeline Design (10M docs, <500ms p95, 5min freshness)

**What they test:** Can you design for scale, freshness, AND cost?

**Why this architecture (Lambda for RAG):**
- **Online path** (freshness): Kafka + Flink CDC → invalidate Qdrant ID + upsert new chunks. Full reindex is too slow for 10M docs.
- **Offline path** (scale): Spark batch for backfill at 5k RPS — re-embed 10M docs in ~30 min
- **Serving path** (latency): hybrid search (BM25 + vector) → reranker (cross-encoder) → Top 8 → LLM. BM25 catches exact-match (names, IDs) that vector misses.
- **Cost control**: skip embedding for low-quality docs (>5k tokens, low info score). 30% of repeat queries → cache query embeddings in Redis.
"""))

cells.append(nbf.v4.new_code_cell("""# RAG pipeline architecture (illustrative diagram, not runnable but shows the flow)
pipeline_design = '''
                        INGESTION PATH (online, 5min freshness)
                        ------------------------------------
  SharePoint/S3 update
         |
         v
  Kafka: doc_ingested  -->  Flink CDC job  -->  Qdrant upsert (new chunks)
         |                       |
         |                       +-->  Postgres: UPDATE documents SET hash=new_hash
         v
  Chunking worker (LangChain, 512 tokens + 50 overlap)
         |
         v
  Embedding batch (OpenAI / internal model)
         |
         +-->  Qdrant (vector) + Postgres (chunks table)

                        SERVING PATH (online, <500ms p95)
                        --------------------------------
  User query
         |
         v
  Embed query (cached in Redis if repeat)
         |
         v
  Qdrant Top 50  -->  Cohere rerank  -->  Top 8
         |
         +-->  Hybrid: BM25 (OpenSearch) merged with vector results
         v
  LLM with prompt_v3 + context = answer

                        BACKFILL PATH (offline, scale)
                        -----------------------------
  Spark cluster: re-embed 10M docs at 5k RPS
         |
         v
  Write to Qdrant SHADOW INDEX (embeddings_v2)
         |
         +-->  Dual-read 1% from v2 for shadow eval
         v
  Cutover via config flag, keep v1 for 7 days rollback
'''
print(pipeline_design)"""))

cells.append(nbf.v4.new_markdown_cell("""**L6 phrases to drop:**
- "Lambda for RAG: offline batch backfill + online incremental freshness = best of both"
- "Hybrid search: BM25 + vector. Vector misses exact matches (employee IDs, product SKUs). Reranker cross-encoder is in the serving path, not the indexing path — too slow for indexing."
- "Cache query embeddings in Redis — repeat queries are 30% of traffic at Meta scale, saves embedding cost"
- "Skip embedding for low-quality docs (>5k tokens, low info score via TF-IDF heuristic) — cost control without hurting quality"
- "Idempotent via chunk_hash — if hash unchanged, skip re-embed. Versioning via embedding_model_version — old chunks stay valid until you re-embed them."
"""))

# ════════════════════════════════════════════════════════════════════
# ROUND 2 — Q3: MMR Coding
# ════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""---

## ROUND 2 — Q3: MMR Rerank Coding (the actual whiteboard question)

**What they test:** Can you implement a real algo under pressure, not just describe it?

**Why MMR:** Standard vector search returns redundant chunks (e.g., 5 chunks from the same section). MMR = Maximal Marginal Relevance — balances **relevance** vs **diversity** so you get 8 chunks that cover different aspects, not duplicates of the same one.

**The formula:**
```
MMR(d) = λ · sim(d, query) - (1-λ) · max[sim(d, d_selected)]
         ↑                          ↑
     relevance               diversity penalty
```
- λ=0.7 → favor relevance (default)
- λ=0.3 → favor diversity (when chunks are very similar)
"""))

cells.append(nbf.v4.new_code_cell("""import numpy as np

def mmr_rerank(query_emb, chunk_embs, chunks, lambda_=0.7, k=8):
    \"\"\"
    Maximal Marginal Relevance reranking.

    Args:
        query_emb:   [D]            - query embedding vector
        chunk_embs:  [N, D]         - all candidate chunk embeddings
        chunks:      list of N      - the actual chunk texts/metadata
        lambda_:     float          - relevance vs diversity tradeoff (0.7 = favor relevance)
        k:           int            - number of chunks to return

    Returns:
        list of k chunks that are relevant AND diverse

    Complexity: O(k * N * D) — fine for k=8, N=50.
    For N=10k+, use approximate MMR via HNSW.
    \"\"\"
    selected = []
    candidates = list(range(len(chunks)))

    # Pre-compute cosine similarity of each chunk to query (assumes normalized vectors)
    sim_to_query = chunk_embs @ query_emb  # [N]

    while len(selected) < k and candidates:
        if not selected:
            # First pick: most relevant to query
            best = max(candidates, key=lambda i: sim_to_query[i])
        else:
            # Score each candidate: relevance - diversity penalty
            scores = []
            for i in candidates:
                # max similarity to ANY already-selected chunk
                max_sim_to_selected = max(
                    chunk_embs[i] @ chunk_embs[j]
                    for j in selected
                )
                mmr_score = (lambda_ * sim_to_query[i]
                           - (1 - lambda_) * max_sim_to_selected)
                scores.append((mmr_score, i))
            best = max(scores)[1]

        selected.append(best)
        candidates.remove(best)

    return [chunks[i] for i in selected]


# ── TEST IT ─────────────────────────────────────────────────────
# Simulate 10 candidate chunks, 64-dim embeddings
np.random.seed(42)
N, D = 10, 64
query_emb = np.random.randn(D)
query_emb /= np.linalg.norm(query_emb)  # normalize for cosine sim

chunk_embs = np.random.randn(N, D)
chunk_embs /= np.linalg.norm(chunk_embs, axis=1, keepdims=True)  # normalize

chunks = [f"chunk_{i}: this is some text about topic {i}" for i in range(N)]

result = mmr_rerank(query_emb, chunk_embs, chunks, lambda_=0.7, k=3)
print("Top 3 MMR-selected chunks:")
for i, c in enumerate(result):
    print(f"  {i+1}. {c}")
print()
print("Without MMR, you'd just take top-3 by cosine sim to query —")
print("which often returns 3 near-duplicates. MMR forces diversity.")"""))

cells.append(nbf.v4.new_code_cell("""# Compare MMR vs pure relevance to show the difference
def pure_relevance_top_k(query_emb, chunk_embs, chunks, k=3):
    \"\"\"Baseline: just take top-k by cosine sim, no diversity.\"\"\"
    sims = chunk_embs @ query_emb
    top_k_idx = np.argsort(-sims)[:k]
    return [chunks[i] for i in top_k_idx], sims[top_k_idx]

# Create a scenario where 3 chunks are very similar to each other (duplicates)
np.random.seed(7)
query_emb = np.random.randn(D)
query_emb /= np.linalg.norm(query_emb)

chunk_embs = np.random.randn(N, D)
chunk_embs /= np.linalg.norm(chunk_embs, axis=1, keepdims=True)

# Make chunks 0, 1, 2 nearly identical (simulate duplicates)
chunk_embs[1] = chunk_embs[0] + 0.01 * np.random.randn(D)
chunk_embs[2] = chunk_embs[0] + 0.01 * np.random.randn(D)
chunk_embs[1] /= np.linalg.norm(chunk_embs[1])
chunk_embs[2] /= np.linalg.norm(chunk_embs[2])

chunks = [f"chunk_{i}: content variant {i}" for i in range(N)]

print("=" * 60)
print("PURE RELEVANCE (no diversity penalty) — picks duplicates:")
print("=" * 60)
top_k_relevant, sims = pure_relevance_top_k(query_emb, chunk_embs, chunks, k=3)
for c, s in zip(top_k_relevant, sims):
    print(f"  {c}  (sim={s:.3f})")

print()
print("=" * 60)
print("MMR (lambda=0.7) — picks diverse chunks:")
print("=" * 60)
top_k_mmr = mmr_rerank(query_emb, chunk_embs, chunks, lambda_=0.7, k=3)
for c in top_k_mmr:
    print(f"  {c}")"""))

cells.append(nbf.v4.new_markdown_cell("""**L6 line to say while coding:**

> "In prod, I'd never code this from scratch — Qdrant has built-in MMR, or I'd use Cohere Rerank API. This is the algo behind it though, and interviewers want to see I understand the math. Complexity is O(k·N·D), fine for k=8, N=50. If N=10k+, I'd use approximate MMR via HNSW."
"""))

# ════════════════════════════════════════════════════════════════════
# ROUND 2 — Q4: SQL Eval
# ════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""---

## ROUND 2 — Q4: SQL — Measure RAG Quality

**What they test:** Can you write analytics SQL on the schema you just designed? Do you know which KPIs matter for RAG?

**The 3 RAG KPIs:**
1. **Satisfaction** = thumbs_up / total (with NULL feedback excluded)
2. **p95 latency** = PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms)
3. **Cost** = SUM(cost_tokens) per day (every LLM call has a $$ cost)

**Why GROUP BY day, not user:** Aggregating by day gives you a time series for dashboards (Grafana). Per-user is for cohort analysis, not daily monitoring.
"""))

cells.append(nbf.v4.new_code_cell("""# Use sqlite3 to demo the eval query against a small synthetic dataset
import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect(':memory:')
cur = conn.cursor()

# Create the same schema (SQLite-flavored)
cur.execute(\"\"\"
CREATE TABLE traces (
    trace_id TEXT PRIMARY KEY,
    user_id TEXT,
    query TEXT,
    prompt_version INT,
    response TEXT,
    latency_ms INT,
    cost_tokens INT,
    created_at TIMESTAMP
);
CREATE TABLE feedback (
    feedback_id TEXT PRIMARY KEY,
    trace_id TEXT,
    rating TEXT,
    corrected_answer TEXT,
    created_at TIMESTAMP
);
\"\"\")

# Seed synthetic data — 7 days of traces, ~100/day
np.random.seed(42)
trace_rows = []
feedback_rows = []
for day_offset in range(7):
    for i in range(100):
        trace_id = f"t_{day_offset}_{i}"
        trace_rows.append((
            trace_id,
            f"u_{i % 20}",
            f"query {i}",
            np.random.choice([1, 2, 3]),  # 3 prompt versions for A/B
            f"response {i}",
            int(np.random.normal(450, 100)),  # mean 450ms, std 100ms
            int(np.random.normal(800, 200)),  # token cost
            f"2026-10-{7+day_offset:02d} 12:00:00",
        ))
        # 30% get feedback
        if np.random.rand() < 0.3:
            feedback_rows.append((
                f"f_{trace_id}",
                trace_id,
                'thumbs_up' if np.random.rand() < 0.75 else 'thumbs_down',
                None if np.random.rand() < 0.5 else f"corrected_{i}",
                f"2026-10-{7+day_offset:02d} 12:05:00",
            ))

cur.executemany("INSERT INTO traces VALUES (?,?,?,?,?,?,?,?)", trace_rows)
cur.executemany("INSERT INTO feedback VALUES (?,?,?,?,?)", feedback_rows)
conn.commit()

print(f"Seeded {len(trace_rows)} traces and {len(feedback_rows)} feedback rows")"""))

cells.append(nbf.v4.new_code_cell("""# Q4 SQL answer: measure RAG quality from traces + feedback
eval_sql = \"\"\"
SELECT
    DATE(t.created_at) AS day,
    COUNT(*) AS total_traces,
    AVG(CASE WHEN f.rating = 'thumbs_up' THEN 1.0 ELSE 0.0 END) AS satisfaction,
    AVG(t.latency_ms) AS avg_latency_ms,
    SUM(t.cost_tokens) AS total_cost_tokens
FROM traces t
LEFT JOIN feedback f ON t.trace_id = f.trace_id
WHERE t.created_at >= DATE('now', '-7 days')
GROUP BY DATE(t.created_at)
ORDER BY day DESC;
\"\"\"
df = pd.read_sql_query(eval_sql, conn)
print(df.to_string(index=False))"""))

cells.append(nbf.v4.new_code_cell("""# L6 add-on: A/B test by prompt_version — the table that proves your prompt change worked
ab_sql = \"\"\"
SELECT
    t.prompt_version,
    DATE(t.created_at) AS day,
    COUNT(*) AS total,
    AVG(CASE WHEN f.rating = 'thumbs_up' THEN 1.0 ELSE 0.0 END) AS satisfaction,
    AVG(t.latency_ms) AS avg_lat_ms
FROM traces t
LEFT JOIN feedback f ON t.trace_id = f.trace_id
WHERE t.created_at >= DATE('now', '-7 days')
GROUP BY t.prompt_version, DATE(t.created_at)
ORDER BY day DESC, prompt_version;
\"\"\"
df_ab = pd.read_sql_query(ab_sql, conn)
print("A/B test by prompt_version:")
print(df_ab.to_string(index=False))"""))

cells.append(nbf.v4.new_code_cell("""# L6 add-on: build the gold eval set from corrected_answer (labeled training data)
gold_sql = \"\"\"
SELECT
    t.query,
    t.response AS model_answer,
    f.corrected_answer AS human_answer,
    t.prompt_version
FROM traces t
JOIN feedback f ON t.trace_id = f.trace_id
WHERE f.corrected_answer IS NOT NULL
ORDER BY t.created_at DESC
LIMIT 5;
\"\"\"
df_gold = pd.read_sql_query(gold_sql, conn)
print(f"Gold eval set sample (rows where humans corrected the model):")
print(df_gold.to_string(index=False))
print()
print("→ This is your labeled data for offline eval. Replay new prompts against")
print("  this set BEFORE shipping. If satisfaction drops, don't ship.")"""))

# ════════════════════════════════════════════════════════════════════
# ROUND 3: PYMK Feed
# ════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""---

## ROUND 3 — Sr Tech Design: People-You-May-Know Feed with AI Summaries

**What they test:** Can you design a system that DOESN'T HALLUCINATE at Meta scale?

**The 3-layer anti-hallucination architecture:**
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

**Why this design:**
- **SCD2 on friendships** = time travel. "Users who were friends 6 months ago" is a valid query for friend recency scoring.
- **Bounded fanout** = skip users with >5k friends. A user with 10k friends generates 10k² = 100M writes per friend-add.
- **Grounded generation only** = the prompt MUST include `evidence_json` and the instruction "use ONLY provided evidence". No evidence → output "unknown".
- **No LLM in serving path** = serving path is just a Redis lookup + template fill. LLM only runs offline for candidate_reasons pre-computation.
"""))

cells.append(nbf.v4.new_code_cell("""# PYMK feed — SCD2 friendship table for time-travel queries
pymk_schema = \"\"\"
-- Time-travel friendship graph (SCD2)
CREATE TABLE friendships (
    user_id     UUID,
    friend_id   UUID,
    valid_from  TIMESTAMP,
    valid_to    TIMESTAMP,    -- NULL = currently active
    action      TEXT CHECK (action IN ('add', 'remove')),
    PRIMARY KEY (user_id, friend_id, valid_from)
);

-- Daily batch output from Spark GraphX
CREATE TABLE pymk_candidates (
    user_id       UUID,
    candidate_id  UUID,
    mutuals       INT,
    score         FLOAT,           -- from PageRank + mutual boost
    computed_at   TIMESTAMP,
    PRIMARY KEY (user_id, candidate_id)
);

-- Pre-computed reasons with grounded evidence (NO free LLM)
CREATE TABLE candidate_reasons (
    candidate_id    UUID,
    reason_template VARCHAR(50),  -- 'mutuals_and_company'
    evidence_json   TEXT,         -- {"company": "Meta", "mutuals": ["alice","bob"]}
    rendered_text   TEXT,         -- pre-rendered: "You both worked at Meta and know 5 mutuals"
    computed_at     TIMESTAMP,
    PRIMARY KEY (candidate_id, reason_template)
);

-- Live mutual counts in Redis (bounded fanout)
-- Key: mutual_count:{user_id}  Value: hash of {friend_id: count}
-- Updated by Flink on friendship_events topic
-- Bounded: skip events for users with >5000 friends (celebrities)
\"\"\"
print(pymk_schema)"""))

cells.append(nbf.v4.new_code_cell("""# Grounded generation prompt — the L6 answer to "how do you prevent hallucination?"
grounded_prompt = '''
You are generating a friend suggestion reason. You MUST follow these rules:

1. Use ONLY facts present in the evidence_json below.
2. If a fact is not in evidence_json, output the string "unknown".
3. NEVER invent names, companies, or events.
4. Output format: a single sentence, max 20 words.

evidence_json:
{
  "shared_companies": ["Meta", "Google"],
  "mutual_friend_names": ["Alice Chen", "Bob Smith", "Carol Davis"],
  "mutual_friend_count": 5,
  "shared_groups": []
}

Generate one sentence explaining why these two users should connect.
'''
print(grounded_prompt)
print()
print("WHY this works:")
print("  - 'Use ONLY facts in evidence_json' = prevents hallucination")
print("  - 'Output unknown if not present' = gives the model a safe fallback")
print("  - evidence_json is machine-generated from the graph, not user-input")
print("    → no prompt injection vector")"""))

cells.append(nbf.v4.new_code_cell("""# LLM-as-judge eval — the L6 answer to "how do you catch hallucinations in prod?"
judge_prompt = '''
You are an evaluator checking if a generated reason is GROUNDED in evidence.

evidence_json:
{evidence_json}

generated_reason:
{generated_reason}

Check each factual claim in the generated_reason:
  - Is the company mentioned present in evidence_json.shared_companies?
  - Are the mutual_friend_names present in evidence_json.mutual_friend_names?
  - Is the mutual_friend_count <= evidence_json.mutual_friend_count?

Output JSON:
{
  "is_grounded": true/false,
  "ungrounded_claims": ["claim 1", "claim 2"],
  "verdict": "pass" or "fail"
}
'''
print(judge_prompt)
print()
print("→ Nightly job samples 1k reasons, runs LLM-as-judge.")
print("  If fail rate > 1%, alert + investigate evidence_json pipeline.")"""))

cells.append(nbf.v4.new_code_cell("""# Scale follow-up: re-embed 500M when model v2 drops? Answer: dual-write + shadow index
reembed_strategy = '''
DUAL-WRITE + SHADOW INDEX (never in-place update)
================================================

Step 1: Create new collection embeddings_v2 in Qdrant
Step 2: Spark backfill job — re-embed 500M chunks at 5k RPS
        - Exponential backoff on rate limits
        - Idempotent: chunk_hash + model_version = unique key
        - Estimated runtime: 500M / 5000 = 100k seconds = ~28 hours
Step 3: Shadow read — serve prod from v1, dual-read 1% from v2
        - Compare quality metrics (precision@10, satisfaction) for 7 days
Step 4: Cutover — flip config flag embedding_model_version = v2
        - Keep v1 alive for 7 days as rollback
        - Monitor p95 latency, satisfaction, error rate
Step 5: Decommission v1 after 7 days if metrics hold

WHY this is the L6 answer:
  + Zero-downtime cutover
  + Rollback path (v1 stays alive)
  + Quality validation before user impact (1% shadow)
  + Idempotent (re-running is safe)
  - NEVER in-place update — that is how you corrupt prod
'''
print(reembed_strategy)"""))

# ════════════════════════════════════════════════════════════════════
# ROUND 4: Full Stack Tool
# ════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""---

## ROUND 4 — Full Stack: Build RAG Trace Reviewer Tool

**What they test:** Can you SHIP a working internal tool fast? They want SPEED + API design, not auth or full CRUD.

**The 3-end-point minimum viable tool:**
- `GET /traces?day=...&prompt_version=...&cursor=...&limit=50`
- `POST /feedback {trace_id, rating, corrected_answer}`
- `GET /traces/{trace_id}` for detail view

**Why cursor pagination, not OFFSET:**
- OFFSET 1000 LIMIT 50 = scan 1050 rows, throw away 1000. At 1B rows/day, this kills the DB.
- Cursor `WHERE trace_id < last_id ORDER BY created_at DESC LIMIT 50` = index seek, O(log n).
- Same UX for the user (infinite scroll), 1000x faster backend.
"""))

cells.append(nbf.v4.new_code_cell("""# FastAPI backend — the L6 answer for the trace reviewer tool
fastapi_code = '''
from fastapi import FastAPI, Query, HTTPException
from typing import Optional

app = FastAPI(title="RAG Trace Reviewer")

@app.get("/traces")
def get_traces(
    day: str,                                     # ISO date: 2026-10-14
    prompt_version: Optional[str] = None,         # filter for A/B comparison
    cursor: Optional[str] = None,                 # last trace_id from previous page
    limit: int = Query(50, le=200),               # cap at 200 to prevent abuse
):
    """
    Cursor pagination, not OFFSET.
    OFFSET scans O(n) rows at one billion rows/day, that kills the DB.
    Cursor = index seek, O(log n).
    """
    query = db.query(Trace).filter(Trace.day == day)

    if prompt_version:
        query = query.filter(Trace.prompt_version == prompt_version)

    if cursor:
        # Keyset pagination: WHERE trace_id < cursor
        query = query.filter(Trace.trace_id < cursor)

    traces = (
        query.order_by(Trace.created_at.desc(), Trace.trace_id.desc())
              .limit(limit)
              .all()
    )

    next_cursor = traces[-1].trace_id if len(traces) == limit else None
    return {"traces": traces, "next_cursor": next_cursor}


@app.post("/feedback")
def post_feedback(
    trace_id: str,
    rating: str,                                   # 'thumbs_up' or 'thumbs_down'
    corrected_answer: Optional[str] = None,
):
    """Optimistic UI: return immediately, write async."""
    if rating not in ("thumbs_up", "thumbs_down"):
        raise HTTPException(400, "rating must be thumbs_up or thumbs_down")

    fb = Feedback(
        trace_id=trace_id,
        rating=rating,
        corrected_answer=corrected_answer,
    )
    db.add(fb)
    db.commit()
    return {"ok": True}


@app.get("/traces/{trace_id}")
def get_trace_detail(trace_id: str):
    """Detail view: query, retrieved chunks, response, latency, feedback."""
    trace = db.query(Trace).filter_by(trace_id=trace_id).first()
    if not trace:
        raise HTTPException(404, "trace not found")
    return trace
'''
print(fastapi_code)"""))

cells.append(nbf.v4.new_code_cell("""# React frontend — 30-second sketch, virtualized list for 1k+ rows
react_code = '''
import React, { useState, useEffect } from 'react';
import { FixedSizeList } from 'react-window';

function TraceReviewer() {
  const [traces, setTraces] = useState([]);
  const [cursor, setCursor] = useState(null);
  const [promptFilter, setPromptFilter] = useState('');
  const [day, setDay] = useState('2026-10-14');

  async function loadTraces(reset = false) {
    const params = new URLSearchParams({ day, limit: 50 });
    if (cursor && !reset) params.set('cursor', cursor);
    if (promptFilter) params.set('prompt_version', promptFilter);

    const res = await fetch(`/traces?${params}`);
    const data = await res.json();
    setTraces(reset ? data.traces : [...traces, ...data.traces]);
    setCursor(data.next_cursor);
  }

  // OPTIMISTIC UI: update UI immediately, rollback if server fails
  async function submitFeedback(traceId, rating) {
    setTraces(traces.map(t =>
      t.trace_id === traceId ? { ...t, _optimistic: rating } : t
    ));
    try {
      await fetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trace_id: traceId, rating }),
      });
    } catch (e) {
      // rollback on failure
      setTraces(traces.map(t =>
        t.trace_id === traceId ? { ...t, _optimistic: null } : t
      ));
    }
  }

  useEffect(() => { loadTraces(true); }, [day, promptFilter]);

  return (
    <div>
      <input value={day} onChange={e => setDay(e.target.value)} />
      <input
        placeholder="prompt_version filter"
        value={promptFilter}
        onChange={e => setPromptFilter(e.target.value)}
      />

      {/* Virtualized list: only render visible rows, not all 1k+ */}
      <FixedSizeList
        height={600}
        itemCount={traces.length}
        itemSize={80}
        width="100%"
      >
        {({ index, style }) => {
          const t = traces[index];
          return (
            <div style={style} key={t.trace_id}>
              <span>{t.query}</span>
              <span>{t.latency_ms}ms</span>
              <button onClick={() => submitFeedback(t.trace_id, 'thumbs_up')}>
                {String.fromCharCode(0x1F44D)} {t._optimistic === 'thumbs_up' ? '✓' : ''}
              </button>
              <button onClick={() => submitFeedback(t.trace_id, 'thumbs_down')}>
                {String.fromCharCode(0x1F44E)} {t._optimistic === 'thumbs_down' ? '✓' : ''}
              </button>
            </div>
          );
        }}
      </FixedSizeList>

      {cursor && <button onClick={() => loadTraces(false)}>Load more</button>}
    </div>
  );
}
'''
print(react_code)
print()
print("L6 phrases to drop while coding:")
print("  - 'Cursor pagination, not OFFSET — OFFSET is O(n) scan'")
print("  - 'Optimistic UI — update immediately, rollback on failure'")
print("  - 'Virtualized list — 1k rows will tank React if I render naively'")
print("  - 'Filter by prompt_version from day 1 — you will need it for A/B tomorrow'")"""))

# ════════════════════════════════════════════════════════════════════
# ROUND 5: STAR
# ════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""---

## ROUND 5 — Sr Ownership (Behavioral, 30m)

**What they test:** L6 ≠ "I helped". L6 = "I owned end-to-end, defined the metric, and prevented recurrence."

**The L6 STAR upgrade:**
```
L4 STAR:  S/T/A/R as described in job ad
L5 STAR:  S/T/A/R with my specific actions
L6 STAR:  S/T/A/R + METRIC + PREVENTION
                              ^           ^
                          quantified    runbook/SLO
                          outcome       you left behind
```

### Q1: Owned a broken pipeline no one wanted

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

### Q2: DE vs ML team conflict on data quality

**L6 ANSWER:**
> "I proposed a **data contract**:
> - ML team defines the **gold dataset schema** (what 'good data' looks like)
> - DE team guarantees **freshness SLA** (data lands within 5 min of source)
> - DE team guarantees **schema SLA** (no breaking changes without notice)
>
> I wrote the contract as JSON, added **Great Expectations checks** in the pipeline that fail the DAG if contract breaks. Both teams now have measurable SLAs. Conflict resolved with metrics, not opinions."

### Q3: Vague problem "Make RAG better"

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
"""))

# ════════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════════
cells.append(nbf.v4.new_markdown_cell("""---

## ✅ ALL 5 ROUNDS COVERED

| Round | Status | Code Run? |
|-------|--------|-----------|
| 1. Greet | Theory only (no code) | n/a |
| 2. Q1 Schema | SQL DDL | display only |
| 2. Q2 Pipeline | Architecture diagram | display only |
| 2. Q3 MMR | Python + numpy | YES |
| 2. Q4 Eval SQL | SQLite + pandas | YES |
| 3. PYMK | SQL + prompts | display only |
| 4. Trace Reviewer | FastAPI + React | display only |
| 5. STAR | Behavioral scripts | n/a |

**Next steps:**
1. Save this executed notebook as `meta_l6_onsite_mock_executed.ipynb`
2. Read `META_L6_STUDY_GUIDE.md` for the theory
3. Say "start round 2" to begin live mock mode
"""))

# ════════════════════════════════════════════════════════════════════
# Assemble and write
# ════════════════════════════════════════════════════════════════════
nb.cells = cells
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.10"}
}

out_path = Path("/Users/vishnoiprem/PycharmProjects/data-etl-ml/medium/meta/meta-on-site-mock/meta_l6_onsite_mock.ipynb")
with open(out_path, "w") as f:
    nbf.write(nb, f)

print(f"Notebook written: {out_path}")
print(f"Total cells: {len(cells)}")
