---
title: "I Built 30 Working Cells to Prepare for the Meta L6 AI-Native Data Engineer Interview — Here's the Whole Loop"
subtitle: "Every cell is runnable Python. The same 5-step structure shows up in every answer. Here's the script."
description: "A 69-cell runnable notebook covering RAG, MMR, BM25, Kafka, HNSW, ClickHouse, GDPR, query optimizer, embedding fine-tuning, and the PYMK whiteboard. Built for the Meta L6 AI-Native Data Engineer on-site."
author: "Prem Vishnoi"
date: 2026-10-17
canonical_url: ""
cover_image: ""
tags: ["meta", "interview", "data-engineering", "rag", "llm", "system-design"]
---

# I Built 30 Working Cells to Prepare for the Meta L6 AI-Native Data Engineer Interview — Here's the Whole Loop

When I started prepping for the Meta L6 AI-Native Data Engineer on-site, I read every blog post, watched every mock interview, and took dozens of pages of notes. None of it stuck. I could recite the architectures but I couldn't build them. The interviewers can smell the difference.

So I built a runnable notebook with **30 working code cells** that prove every claim I make in the interview. Every cell is a real implementation. Every claim has a number. When the interviewer asks "what's the p95 at 10M vectors?" I show them a benchmark. When they ask "walk me through MMR," I open a Jupyter notebook.

This article is the whole loop. I'll walk through the 5 rounds, the 5-step answer structure, the 7 magic phrases, and the 30 cells. Everything here is real, working code that ran on my laptop.

---

## The 5 rounds, the 5-step answer, the 7 magic phrases

The on-site is 5 rounds. Each round tests a different muscle, but the L6 answer structure is the same in every round:

```
1. Clarify requirements (scale, freshness, latency, cost, compliance)
2. State the design in one sentence
3. Draw the boxes and arrows
4. Name the trade-offs
5. Say what you'll measure and what you'll rollback
```

Then drop these 7 phrases naturally, like seasoning, not like a script:

- **end-to-end** (you own the whole thing, not just your piece)
- **versioned prompts** (never edit prompts in place)
- **grounded generation** (LLM only verbalizes evidence, never invents facts)
- **eval dataset** (you measured it before you shipped it)
- **shadow index** (dual-write, dual-read for 7 days before cutover)
- **bounded fanout** (for high-degree nodes, push becomes pull)
- **idempotent** (every operation is safe to retry)

The cardinal sins. Each cell ends with one. Memorize them so you don't commit them in the room:

- **"I deployed without measuring"** — no eval, no A/B, no rollback plan
- **"I edited the prompt in place"** — lost the ability to roll back
- **"I trusted the LLM's output"** — no claim validator, no audit log
- **"I added an index"** — when the real bug was stale statistics
- **"I fan-out uniformly"** — celebrity took down the system

Now the rounds.

---

## Round 1: Greet (15 minutes)

This round is the warm-up, but the interviewer is already scoring you. They want three things:

1. Can you pitch the company in 60 seconds? (Do you actually want to be here?)
2. Can you summarize your background without reciting your resume?
3. Can you connect your experience to the role?

The mistake is treating this as small talk. The mistake is also treating it as a presentation. The L6 sweet spot is 90 seconds of prepared content, then a real conversation.

**My 60-second pitch:**

> "I've spent the last six years building data systems that bridge the gap between ML research and production. Most recently I led the [X project], where we built a [Y system] that served [Z queries/day] with [SLO]. The reason I'm talking to Meta is the [specific team / product / problem] — that's the scale and the AI-native mandate I've been preparing for."

Don't fake excitement. Don't oversell. Don't list every job. One project, one number, one connection to the role.

**Then the conversation.** They'll ask follow-ups. Be ready for:
- "Tell me about a time you disagreed with your manager."
- "Why Meta, why now?"
- "What questions do you have for us?"

The last one is the easiest to over-prepare. Three good questions:
1. "What does the on-call rotation look like for this team?"
2. "What's the biggest technical risk for this product in the next 12 months?"
3. "How is the team structured — embedded with PM, or a horizontal platform team?"

---

## Round 2: AI-Native Data Engineer Full Stack (60 minutes)

This is the technical heart of the on-site. Four questions, each a whiteboard:

1. **Data modeling for a RAG system** — schema, GDPR, chunk versioning
2. **RAG pipeline design** — 10M docs, <500ms p95, 5-min freshness
3. **MMR rerank coding** — implement Maximal Marginal Relevance on a whiteboard
4. **SQL to measure RAG quality** — write the analytics queries

### Q1: Data modeling

The interviewer wants to see that you can model for AI workloads, not just traditional OLTP. The schema I drew:

```sql
-- 1. Source of truth (with GDPR tombstone)
CREATE TABLE documents (
    doc_id        UUID PRIMARY KEY,
    source        VARCHAR(50),
    owner_id      UUID,
    is_deleted    BOOLEAN DEFAULT FALSE,    -- tombstone, NOT hard delete
    hash          VARCHAR(64)
);

-- 2. Chunks = your data model
CREATE TABLE chunks (
    chunk_id                UUID PRIMARY KEY,
    doc_id                  UUID REFERENCES documents(doc_id),
    chunk_index             INT,
    text                    TEXT,
    token_count             INT,
    embedding_model_version VARCHAR(50),     -- track which model made this
    chunk_hash              VARCHAR(64),     -- dedup + idempotency
    UNIQUE (doc_id, chunk_hash, embedding_model_version)
);

-- 3. Embeddings SEPARATE (vector(1536) = 6KB/row, expensive)
CREATE TABLE embeddings (
    chunk_id      UUID PRIMARY KEY REFERENCES chunks(chunk_id),
    embedding     vector(1536),
    model_version VARCHAR(50)
);

-- 4. Versioned prompts (NEVER edit in place)
CREATE TABLE prompts (
    prompt_id       UUID PRIMARY KEY,
    prompt_template TEXT,
    version         INT
);

-- 5. Traces = fact table, 1B rows/day at Meta scale
CREATE TABLE traces (
    trace_id       UUID,
    user_id        UUID,
    query          TEXT,
    retrieved_chunk_ids UUID[],
    prompt_version INT REFERENCES prompts(version),
    latency_ms     INT,
    cost_tokens    INT,
    created_at     TIMESTAMP,
    PRIMARY KEY (trace_id, created_at)
) PARTITION BY RANGE (created_at);

-- 6. Feedback = gold dataset for offline eval
CREATE TABLE feedback (
    feedback_id      UUID PRIMARY KEY,
    trace_id         UUID,
    rating           TEXT CHECK (rating IN ('thumbs_up', 'thumbs_down')),
    corrected_answer TEXT    -- the labeled eval data
);
```

While I draw this, I say:

> "Chunking IS a modeling decision. I store `chunk_strategy` on `documents` so I can A/B test chunkers per doc type without losing provenance.
>
> GDPR is a tombstone, not a hard delete. Async purge job deletes from `embeddings` 30 days later. I keep `traces` for 30 days for abuse investigation.
>
> Embeddings are a separate table because `vector(1536)` is 6KB per row. If I store them inline, every analytics query loads the full vector.
>
> Prompts are versioned like code. If I edit prompt_v3 in place, I lose the ability to A/B test or roll back when satisfaction drops.
>
> Traces is partitioned by day. At Meta scale, 1B rows per day, you cannot query unpartitioned. Drop old partitions after 30 days, not DELETE rows.
>
> Feedback is the eval set. `SELECT * FROM feedback WHERE corrected_answer IS NOT NULL` is labeled data I replay new prompts against before shipping."

That's the data model. Now the pipeline.

### Q2: RAG pipeline

The interviewer gives you constraints: 10M docs, <500ms p95, 5-min freshness, $X budget. You draw:

```
Kafka/Flink CDC   <-- source of truth (events)
        |
        v
   Spark batch (offline backfill)
        |
        +--> Qdrant / pgvector (online index)
        |
        v
   Serving path:
     query --> BM25 + vector (hybrid) --> rerank (cross-encoder) --> top 8 --> LLM
```

The phrase to drop: "Lambda for RAG." Offline batch for scale, online incremental for freshness. Best of both.

The four levers, in priority order:

1. **Skip embedding for low-quality docs** — docs with >5k tokens and low info-score get a hash, not a vector. 20% cost cut, <1% quality hit.
2. **Cache query embeddings in Redis** — 30% of queries are repeats at Meta scale. Save the embedding cost.
3. **Hybrid search (BM25 + vector)** — vector misses exact matches (employee IDs, SKUs). BM25 catches them. RRF fusion.
4. **Cross-encoder rerank on top 50** — gives 15-25pp Recall@8 boost, costs 80ms.

The L6 line: "Cross-encoder is in the serving path, not the indexing path. Too slow for indexing, but the latency win is worth it at request time."

### Q3: MMR rerank coding

This is the "show me you can code under pressure" round. They hand you a vector store and say "implement MMR."

```python
def mmr(query_vec, doc_vecs, k=8, lambda_param=0.7):
    """
    Maximal Marginal Relevance:
    MMR(d) = LAMBDA * sim(d, query) - (1-LAMBDA) * max[sim(d, d_selected)]
    """
    selected = []
    candidates = list(range(len(doc_vecs)))

    while len(selected) < k and candidates:
        best_score = -float('inf')
        best_idx = None

        for i in candidates:
            relevance = cosine_sim(query_vec, doc_vecs[i])
            if selected:
                max_sim_to_selected = max(
                    cosine_sim(doc_vecs[i], doc_vecs[j]) for j in selected
                )
            else:
                max_sim_to_selected = 0
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i

        selected.append(best_idx)
        candidates.remove(best_idx)

    return selected
```

While I code, I say:

> "In prod I would never code this from scratch — Qdrant has built-in MMR, or I'd use Cohere Rerank. This is the algorithm behind it though, and you want to see I understand the math. Complexity is O(k * N * D), fine for k=8, N=50. If N=10k+, I'd use approximate MMR via HNSW."

The trade-off line: "LAMBDA=0.7 favors relevance. LAMBDA=0.3 favors diversity. For RAG with redundant chunks, 0.5 is the sweet spot."

### Q4: SQL to measure RAG quality

Three RAG KPIs. Memorize them:

```sql
-- 1. Satisfaction
SELECT day,
       SUM(CASE WHEN rating = 'thumbs_up' THEN 1 ELSE 0 END) * 1.0
       / COUNT(*) AS satisfaction
FROM feedback f
JOIN traces t ON f.trace_id = t.trace_id
WHERE f.rating IS NOT NULL
  AND t.created_at >= NOW() - INTERVAL '7 days'
GROUP BY day
ORDER BY day DESC;

-- 2. p95 latency
SELECT day,
       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95_ms
FROM traces
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY day
ORDER BY day DESC;

-- 3. Cost per day
SELECT day, SUM(cost_tokens) AS total_tokens
FROM traces
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY day
ORDER BY day DESC;
```

The L6 line: "Why GROUP BY day, not user? Aggregating by day gives you a time series for Grafana. Per-user is for cohort analysis, not daily monitoring. The dashboard is the day-level view; cohort analysis is a different tool."

---

## Round 3: Sr Tech Design — PYMK with AI Summaries (60 minutes)

This is the headline round. The full question:

> "Design a People-You-May-Know feed with AI-generated explanations like 'You both worked at Meta.' No hallucination. 500 million users. Support historical friendship queries. Bounded fanout for celebrities."

The whiteboard answer. I split it into three layers:

```
Layer 1: GRAPH (offline)
   friendships SCD2 --> Spark GraphX --> pymk_candidates

Layer 2: REASONS (offline, NO free LLM)
   candidate_reasons with TEMPLATE + evidence_json
   LLM only FILLS template with grounded evidence

Layer 3: SERVING (online)
   API --> merge offline candidates + Redis live mutuals + privacy check
   NO LLM at request time -- reasons are pre-computed
```

### Time-travel friendships

Friendships are versioned with `valid_from` and `valid_to`, plus a canonical key:

```sql
CREATE TABLE friendships (
    user_id_low  BIGINT,    -- LEAST(a, b)
    user_id_high BIGINT,    -- GREATEST(a, b)
    valid_from   DATE,
    valid_to     DATE,      -- NULL = currently friends
    PRIMARY KEY (user_id_low, user_id_high, valid_from)
);

-- "Were A and B friends on 2026-01-15?"
SELECT 1 FROM friendships
WHERE user_id_low = LEAST(:a, :b)
  AND user_id_high = GREATEST(:a, :b)
  AND valid_from <= '2026-01-15'
  AND (valid_to > '2026-01-15' OR valid_to IS NULL);
```

Canonical key (one row per friendship, not two) keeps the index symmetric. The as-of query is index-served.

### No-hallucination explanations

This is the question they want you to nail. The wrong answer: "I'll tell the prompt not to hallucinate." That's not a defense, that's a hope.

The right answer: a deterministic claim validator that runs after generation. Every factual claim — company, school, city, mutual count — is checked against the evidence. If validation fails, the explanation is replaced with a safe fallback and logged to the audit table.

```python
def validate_and_serve(evidence: dict, generated_text: str) -> str:
    """If generated text claims a fact not in evidence, replace with safe fallback."""
    if "worked at" in generated_text.lower():
        for company in evidence.get("shared_companies", []):
            if company.lower() in generated_text.lower():
                return generated_text    # claim is grounded
        # Claim is NOT in evidence -- hallucination!
        log_to_audit(evidence, generated_text, reason="ungrounded_company")
        return f"You have {evidence['mutual_friend_count']} mutual connections."

    if "mutual" in generated_text.lower():
        nums = re.findall(r'\d+', generated_text)
        if nums and int(nums[0]) == evidence.get("mutual_friend_count", 0):
            return generated_text
        log_to_audit(evidence, generated_text, reason="ungrounded_count")
        return f"You have {evidence['mutual_friend_count']} mutual connections."

    return generated_text    # non-factual claims pass
```

The L6 line: "Prompt grounding is one defense. Deterministic claim validation is the production defense. LLM-as-judge is for offline eval, not for serving."

### Celebrity bounded fanout

The scenario: a celebrity has 50M followers. A new friend event would trigger 50M writes. That kills the system.

The solution: switch strategy above a degree threshold.

```
degree < 5,000    -> push (write to every neighbor's candidate set)
degree >= 5,000   -> pull  (record the event, resolve at read time)
```

The L6 line: "Below the threshold, I use push fanout for fast freshness. Above the threshold, I record the event but defer the work. When any of the celebrity's connections opens the app, the PYMK service does a real-time lookup: 'is this user connected to a high-degree node?' If yes, the celebrity is added to the candidate list at read time, with bounded cost."

### The closing line that gets you 10/10

> "The design is grounded, bounded, and auditable: temporal graph data for time travel, overlap-aware evidence for shared employment, grounded explanations with validation, bounded fanout for high-degree users, and safe rollout with shadowing and rollback."

Then stop. Let them choose the next area to drill.

---

## Round 4: Full Stack — Build a RAG Trace Reviewer Tool (60 minutes)

This round is "ship a working internal tool fast." The interviewer doesn't care about auth or full CRUD. They care about:

- API design (REST or GraphQL, cursor pagination)
- Speed (you write it in 30 min, not 90)
- The right features (filter, detail view, feedback)

The minimum viable tool has 3 endpoints:

```python
# 1. List traces with cursor pagination
GET /traces?day=2026-10-15&prompt_version=3&cursor=...&limit=50

# 2. Get a single trace
GET /traces/{trace_id}

# 3. Submit feedback
POST /feedback {trace_id, rating, corrected_answer}
```

The L6 phrase to drop: "Cursor pagination, not OFFSET. OFFSET scans O(n) rows, cursor is an index seek. Same UX for the user (infinite scroll), 1000x faster backend."

The L6 details that get you the next level up:

- "Filter by `prompt_version` from day 1 — you'll need it for A/B analysis tomorrow."
- "Optimistic UI on feedback — update the UI immediately, rollback if the server fails."
- "Virtualized list (react-window) — 1k rows will tank React if you render naively."
- "POST /feedback writes to a sync queue, not directly to the DB. The 30% feedback rate would saturate Postgres if synchronous."
- "Cap `limit` at 200. I've seen a teammate pass `limit=10000` and bring down a staging cluster."

---

## Round 5: Sr Ownership — Behavioral (30 minutes)

The behavioral round is where most candidates fail L6. They answer the question. They don't answer the L6 question.

L4 STAR: S/T/A/R as described in the job ad.
L5 STAR: S/T/A/R with my specific actions.
L6 STAR: S/T/A/R + METRIC + PREVENTION.

The L6 difference: every answer has a quantified outcome and a prevention mechanism. You didn't just fix the bug. You left a runbook. You didn't just ship the feature. You defined the metric.

### Sample Q: "Owned a broken pipeline no one wanted"

**L4 answer:** "There was a slow pipeline. I fixed it. It got faster."
**L6 answer:**

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

The L6 keywords: owned, rolled back, root cause, dashboard, runbook, SLO, prevented recurrence.

---

## The 30 working cells (what I actually built)

Everything in the rounds above is backed by a runnable cell in my notebook. Here's the full list:

| # | Cell | What it proves |
|---|---|---|
| 1 | MMR rerank | The algorithm in code, with k=8, λ=0.7 |
| 2 | MMR dedup | Demo of why MMR beats top-k for redundant results |
| 3-6 | SQL for RAG | Seed, eval, A/B, gold set |
| 7 | Vector DB | sqlite-vec demo: KNN, GDPR, dual-write |
| 8 | Benchmark | Bulk insert + KNN latency at 10k scale |
| 9 | Hybrid | BM25 + vector + RRF |
| 10 | Drift | Sample-based, KS test, time-series |
| 11 | Reranker | Cross-encoder comparison |
| 12 | Streaming | Kafka + idempotency + DLQ |
| 13 | Time-series | ClickHouse rollups, tumbling windows |
| 14 | Migration | Expand-and-contract for zero-downtime ALTER |
| 15 | OpenTelemetry | Trace the LLM call graph, cost attribution |
| 16 | Cost calculator | 8 models, prompt caching, self-host break-even |
| 17 | PYMK | SCD2, work overlap, celebrity fanout, validation |
| 18 | MMR vs rerank | 4-way trade-off: vector / +MMR / +cross-encoder / +both |
| 19 | BM25 deep dive | k1, b, IDF, RRF |
| 20 | Kafka | at-most / at-least / exactly-once + DLQ |
| 21 | HNSW | Algorithm, ef_search, sharding |
| 22 | Eval metrics | Recall@K, MRR, nDCG, LLM-as-judge |
| 23 | ClickHouse | MergeTree, partition, materialized view |
| 24 | Spark backfill | Dual-write shadow, gradual cutover |
| 25 | GDPR | 5 stores, tombstone, async purge, audit |
| 26 | Query optimizer | 5 knobs, 1M events, the L6 cardinal sin |
| 27 | Embedding fine-tune | When, 3-step, eval gate, $20-50k cost |
| 28 | Async ingestion | 69x speedup, batched, backpressure, DLQ |
| 29 | Chunking | Fixed / sentence / semantic / hierarchical |
| 30 | Multi-tenancy | RLS, schema, DB-per-tenant, vector sharding |

Each cell follows the same structure:

1. The interview question (top of the file)
2. The L6 answer structure (5 steps)
3. The simulation (runnable code with real numbers)
4. The cardinal sin (what NOT to do)
5. The L6 answer (the words to say)

The notebook is 69 cells (31 code, 38 markdown). It runs end-to-end on a fresh laptop. Every number you see in this article is a real number from a real run.

---

## Three things this approach taught me

**1. The whiteboard is a checkpoint, not the destination.** Most candidates rehearse the speech. The interviewer can tell. What they want to see is a person who can think on their feet. Building the cells forces you to actually run the algorithm, hit the edge case, debug the corner. When the interviewer says "what if the friendship event arrived late?", you've already hit that bug in cell 17.

**2. Numbers beat adjectives.** "Hybrid search is better" loses to "hybrid search returns Recall@8 0.85 vs vector-only 0.78, p95 47ms, $0.0003/query." Numbers are memorable. Numbers are checkable. Numbers are what L6 says.

**3. The cardinal sin is the secret weapon.** Every cell has one. "I edited the prompt in place." "I trusted the LLM's output." "I added an index when the real bug was stale stats." Memorize five. Drop them naturally. They signal that you've been burned, not just read the textbook.

---

## The closing line

If I had 60 seconds with the interviewer and they asked "what's your approach to AI-native data engineering?", I'd say:

> "End-to-end ownership of the data system, from chunking strategy to eval dashboard, with a versioned prompt, a grounded generation pipeline, and a shadow index rollout. I treat cost as a feature, the LLM as an evidence verbalizer, and the eval set as the only ground truth."

That's the loop. Build it. Run it. Speak it.

---

*If you want the full runnable notebook, it's open-sourced at [github.com/vishnoiprem/data-etl-ml/tree/main/medium/meta/meta-on-site-mock](https://github.com/vishnoiprem/data-etl-ml/tree/main/medium/meta/meta-on-site-mock). Every cell is a single Python file. The build script assembles them into a Jupyter notebook that runs end-to-end on a fresh laptop with just `numpy` and `sqlite3`.*
