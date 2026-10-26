# Meta L6 Onsite Mock - LOOP 3 to LOOP 10 (Theme Variations)

**Role:** L6 AI-Native Data Engineer (Full Stack) - Meta
**Format:** 7 additional loop themes, each with 5 rounds
**Purpose:** Practice different angles (multimodal, real-time, eval, security, migration, personalization, 0->1)

---

## Loop Coverage Map

| Loop | Theme | Difficulty | Key Differentiator |
|------|-------|------------|---------------------|
| 3 | Multimodal RAG + Cost at 100M | Hard | PDF tables, images, CLIP, OCR |
| 4 | Real-time + Streaming + Low Latency | Hard | Flink, backpressure, 1-sec granularity |
| 5 | Eval + Observability + Gold Dataset | Medium | LLM-as-judge, A/B prompt testing |
| 6 | Security + ACL + PII + GDPR | Hard | Presidio, GDPR delete, audit log |
| 7 | Migration + Model Upgrades + Dual-Write | Medium | Shadow index, $130k cost control |
| 8 | Personalization + Multi-tenant + 500M Users | Hard | Filter bubble, tenant isolation |
| 10 | Final Staff Bar - 0->1 Ambiguous Product | Hardest | No PM, you define requirements |

---

# LOOP 3 - Theme: Multimodal RAG + Cost at 100M

## Greet 15m

### Q1: Tell me about a time you had to work with non-text data - PDF tables, images?

**L6 Answer:**

> "At APEX-RAG, I added multimodal support for 10M PDFs. Pipeline: PyMuPDF extracts text + tables + images. Tables parsed to JSON with row/col preserved. Images embedded with CLIP. Text with text-embedding-3-large. Cost was the challenge - CLIP is $0.001/image, so 10M PDFs * 50 images avg = $500k. I deduped images by perceptual hash (pHash) before embedding, saved 40% = $200k. Each modality stored in separate Qdrant collection with cross-reference by doc_id."

### Q2: How do you measure cost of RAG at 100M scale?

**L6 Answer:**

> "Three cost buckets:
> 1. **Ingestion:** $0.0042/query * 100M docs = $420k one-time + $50k/month incremental (Flink CDC).
> 2. **Retrieval:** $0.0001/Qdrant query * 1B queries/month = $100k/month.
> 3. **Generation:** $0.003/LLM call * 1B = $3M/month (biggest).
>
> I track per-query cost in ClickHouse: `traces(cost_usd, embedding_cost, llm_cost, retrieval_cost)`. Goal: p50 cost <$0.005. Semantic cache saves 30% on LLM cost = $900k/month saved."

---

## AI-Native DE Full Stack 60m

### Q1 Data Model: Design tables for multimodal docs

```sql
-- Multimodal chunks - separate by modality
text_chunks(chunk_id PK, doc_id FK, text, embedding, token_count, chunk_index)
table_chunks(chunk_id PK, doc_id FK, table_json JSON, row_count, col_count, page_number, embedding)
image_chunks(chunk_id PK, doc_id FK, image_url, perceptual_hash, embedding CLIP, width, height, page_number)
documents(doc_id PK, source, modality_mask [text|table|image], total_pages, created_at)

-- Cross-reference: a doc can have all 3 modalities
-- Chunk strategy: tables preserve row/col structure
```

### Q2 Pipeline: PDF ingestion at 10M scale

> "1. **Ingest:** PyMuPDF parses PDF -> text, tables (json), images (PIL)
> 2. **Dedup:** pHash on images (40% dedup rate)
> 3. **Chunk table:** Each table = 1 chunk, JSON preserves row/col. Text 512 tokens.
> 4. **Embed:** 3 models in parallel - text-embedding-3-large (text), CLIP (images), custom table-encoder (tables)
> 5. **Store:** 3 Qdrant collections, cross-ref by doc_id
> 6. **OCR fallback:** If PyMuPDF returns empty text, Tesseract OCR for scanned PDFs
> 7. **Cost control:** Batch embed 1000 at a time for API rate limits, semaphore 100 concurrent"

### Q3 SQL: Cost breakdown by modality

```sql
SELECT
  CASE
    WHEN chunk_id IN (SELECT chunk_id FROM text_chunks) THEN 'text'
    WHEN chunk_id IN (SELECT chunk_id FROM table_chunks) THEN 'table'
    WHEN chunk_id IN (SELECT chunk_id FROM image_chunks) THEN 'image'
  END AS modality,
  SUM(embedding_cost) AS total_embed_cost,
  AVG(token_count) AS avg_tokens,
  COUNT(*) AS chunk_count
FROM (
  SELECT chunk_id, embedding_cost, token_count FROM text_chunks
  UNION ALL
  SELECT chunk_id, embedding_cost, 0 FROM table_chunks
  UNION ALL
  SELECT chunk_id, embedding_cost, 0 FROM image_chunks
) all_chunks
GROUP BY modality
ORDER BY total_embed_cost DESC;
```

### Q4 Coding: Table chunker + image dedup

```python
import fitz  # PyMuPDF
import imagehash
from PIL import Image
import io
import json

def chunk_pdf_tables(pdf_path: str) -> list[dict]:
    """Extract tables, preserve row/col structure as JSON."""
    doc = fitz.open(pdf_path)
    table_chunks = []
    for page_num, page in enumerate(doc):
        # PyMuPDF table extraction
        tables = page.find_tables()
        for table in tables:
            rows = table.extract()
            table_chunks.append({
                "page": page_num,
                "row_count": len(rows),
                "col_count": len(rows[0]) if rows else 0,
                "data": rows,  # preserves row/col
                "table_id": f"p{page_num}_t{len(table_chunks)}"
            })
    return table_chunks


def dedup_images(image_bytes_list: list[bytes]) -> list[bytes]:
    """Dedupe by perceptual hash - 40% dedup rate on PDFs."""
    seen_hashes = {}
    unique = []
    for img_bytes in image_bytes_list:
        img = Image.open(io.BytesIO(img_bytes))
        phash = imagehash.phash(img)
        if phash not in seen_hashes:
            seen_hashes[phash] = img_bytes
            unique.append(img_bytes)
    return unique
```

---

## Sr Tech Design 60m

### Design: AI Doc Parser

> "100M PDFs, answer 'What is Q3 revenue from table?' grounded to cell (row:3, col:2), no hallucination, 5-min freshness, OCR for scanned.

**Architecture:**

```
PDF Ingest (S3) -> Kafka -> PyMuPDF Parser (Flink) -> 3 streams
  -> Text stream: 512 token chunks -> text-embedding-3-large
  -> Table stream: row/col JSON -> table-encoder (custom) -> table_chunks
  -> Image stream: CLIP embedding -> image_chunks
  -> OCR fallback (Tesseract) for empty text pages
```

**Query path:**

1. User query 'Q3 revenue' -> embed
2. Hybrid search across 3 collections (text + table + image)
3. Rerank with Cohere, top 10
4. LLM prompt: `evidence_json = [{type: 'table', page:5, row:3, col:2, value: '$4.2B'}]`
5. **Grounded generation:** LLM must cite cell coordinates in response
6. **No hallucination guard:** LLM-as-judge verifies answer matches cited cell

**Scale:** 100M PDFs * 100 chunks = 10B chunks. 50 shards, 200M/shard. Qdrant can't handle 10B - need to **filter by date/recent** or **summarize older docs**."

---

## Sr Ownership 30m

### Q1: Tell me about time you reduced cost 50% at scale - what tradeoff?

**L6 Answer:**

> "S: APEX-RAG LLM cost $3M/month, unsustainabale.
> T: Reduce 50% without quality drop.
> A: 1. Semantic cache - SHA256(query embedding), 30% hit rate, saved $900k. 2. Switched gpt-4 to gpt-3.5 for simple queries, $2M -> $400k, Recall dropped 0.89->0.85, still acceptable. 3. Reduced context from top-20 to top-8 chunks, $500k saved, Recall dropped 0.85->0.83. Total $1.5M -> $750k, 50% reduction, Recall 0.83 (still above 0.80 SLA).
> R: Cost $1.5M/month, owner happy, users happy. Tradeoff: 6% Recall drop was acceptable for 50% cost."

### Q2: Tell me about time you had to handle corrupted PDFs breaking pipeline

**L6 Answer:**

> "S: 2% of PDFs were corrupted (10M * 0.02 = 200k), crashed PyMuPDF, pipeline stuck.
> T: Handle gracefully, don't break 98%.
> A: 1. Wrapped PyMuPDF in try/except, caught exceptions, sent to DLQ. 2. Added PyMuPDF validation pre-flight (file size > 0, header check). 3. Built quarantine table for corrupted, manual review UI. 4. Alert: DLQ depth > 1000 = page oncall. 5. Wrote runbook.
> R: 200k corrupted quarantined, 0 pipeline downtime, 99.8% of valid PDFs processed."

---

## Full Stack 60m

### Build: Multimodal Trace Viewer

```tsx
// Side-by-side: text chunks | table JSON | image thumbnail
const [trace, setTrace] = useState(null);

return (
  <div className="grid grid-cols-3 gap-4 p-6">
    {/* Text chunks column */}
    <div>
      <h3>Text</h3>
      {trace?.text_chunks.map(c => (
        <div className="border p-2 mb-2">
          <p>{c.text}</p>
          <small>chunk {c.chunk_index}</small>
        </div>
      ))}
    </div>

    {/* Table column with row/col highlight */}
    <div>
      <h3>Tables</h3>
      {trace?.table_chunks.map(t => (
        <table className="border">
          {t.data.map((row, ri) => (
            <tr>
              {row.map((cell, ci) => (
                <td className={ri === highlight.row && ci === highlight.col
                  ? "bg-yellow-300" : ""}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </table>
      ))}
    </div>

    {/* Image column with bounding box */}
    <div>
      <h3>Images</h3>
      {trace?.image_chunks.map(img => (
        <div className="relative">
          <img src={img.url} />
          {img.bbox && (
            <div className="absolute border-2 border-red-500"
              style={{left: img.bbox.x, top: img.bbox.y,
                width: img.bbox.w, height: img.bbox.h}} />
          )}
        </div>
      ))}
    </div>
  </div>
);
```

---

# LOOP 4 - Theme: Real-time + Streaming + Low Latency

## Greet 15m

### Q1: What is hardest part of real-time vs batch?

**L6 Answer:**

> "Three things: 1. **Backpressure** - if downstream is slow, upstream blocks. Batch just queues. 2. **Exactly-once** - duplicate events corrupt state. Batch is idempotent by nature. 3. **Debugging** - 1M events/sec, you can't sample. Need distributed tracing per event. Real-time is harder, costs 10x, only worth it for SLA-driven use cases."

### Q2: How do you handle backpressure in streaming?

**L6 Answer:**

> "Three mechanisms: 1. **Buffer + drop** - bounded queue, if full, drop oldest. 2. **Flow control** - Kafka consumer max.poll.records=100, fetch.max.bytes=1MB, slow down producer. 3. **Adaptive concurrency** - Flink with checkpointing, if checkpoint duration > 60s, reduce parallelism. I prefer #1 + #3 for RAG freshness."

---

## AI-Native DE Full Stack 60m

### Q1 Data Model: Real-time RAG traces

```sql
-- 1-sec granularity, partitioned by second for fast queries
traces_realtime(
  trace_id PK,
  user_id,
  query TEXT,
  latency_ms INT,
  embedding_model_version,
  shard_id,
  prompt_version,
  timestamp TIMESTAMP,  -- second precision
  WATERMARK FOR timestamp  -- Flink watermark
) PARTITIONED BY (DATE(timestamp), HOUR(timestamp));

-- Flink checkpoint state
flink_checkpoints(checkpoint_id PK, job_id, state_size_mb, duration_ms, status, created_at);
```

### Q2 Pipeline: Flink CDC 5-sec freshness

> "Postgres -> Debezium CDC -> Kafka -> Flink job:
> 1. Read commit_event from Kafka
> 2. Generate embedding (batch 100, semaphore 50 concurrent to avoid rate limit)
> 3. **Backpressure:** If embedding API returns 429, Flink slows down via checkpoint barrier
> 4. Write to Qdrant (async, with retry)
> 5. 5-sec SLA: p95 from commit to searchable
>
> **Rate limit handling:** 5k RPS API limit, we batch 100/chunk = 50 RPS, well within. If burst, exponential backoff 1s->2s->4s, max 3 retries."

### Q3 SQL: p95 latency spike detection

```sql
-- 1-min tumbling window, alert p95 > 600ms
SELECT
  TUMBLE_START(timestamp, INTERVAL '1' MINUTE) AS window_start,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95,
  COUNT(*) AS query_count
FROM traces_realtime
WHERE timestamp > NOW() - INTERVAL '1' HOUR
GROUP BY TUMBLE(timestamp, INTERVAL '1' MINUTE)
HAVING PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) > 600
ORDER BY window_start DESC;
```

### Q4 Coding: Rate limiter + Flink watermark

```python
import time
import random
from typing import Optional

class RateLimiter:
    """Token bucket, 5k RPS, burst 10k."""
    def __init__(self, rate: int, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.time()

    def acquire(self) -> bool:
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


def retry_with_backoff(fn, max_retries=3):
    """Exponential backoff: 1s, 2s, 4s."""
    for attempt in range(max_retries):
        try:
            return fn()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)


# Flink watermark: emit watermark every 1s, allow 5s lateness
# In PyFlink:
# env.set_stream_time_characteristic(TimeCharacteristic.EventTime)
# table_env.get_config().set("table.exec.emit.allowed-lateness", "5 s")
```

---

## Sr Tech Design 60m

### Design: Real-time Incident Search

> "1B logs + traces + docs, <500ms, 1M logs/sec ingest, time-travel log at T, no hallucination, grounded to log line.

**Architecture:**

```
Log sources -> Fluent Bit -> Kafka (1000 partitions) -> Flink
  -> Parse JSON -> Index to ES (logs) + ClickHouse (traces, 90d) + Qdrant (docs)
  -> Hot path: ES for recent, ClickHouse for time-travel, Qdrant for semantic
```

**Query path (p95 <500ms):**

1. Embed query (50ms)
2. Parallel search: ES (200ms) + Qdrant (150ms) + ClickHouse time-travel (200ms)
3. Merge top 50 from each, dedup, rerank (50ms)
4. LLM answer with citations (skipped if simple keyword match) - 200ms
5. Total: 450ms p95

**No hallucination:** evidence_json only contains log lines + trace IDs + doc chunks. LLM-as-judge validates answer."

---

## Sr Ownership 30m

### Q1: Tell me about time your streaming job lagged 2 hours - how did you own?

**L6 Answer:**

> "S: Flink job lag 2h, alerting fired. 1M events queued.
> T: Restore freshness, root cause, prevent.
> A: 1. Immediate: Restart Flink job with parallelism 100 (was 20), catchup in 30 min. 2. Root cause: One downstream Qdrant shard was slow, backpressure cascaded. 3. Fix: Added per-shard health check, auto-isolate slow shard. 4. Prevent: Lag alert > 30 min, parallel job for backfill.
> R: Lag 2h -> 5 min within 1 hour. Wrote runbook used 4x since."

### Q2: Tell me about time you had to choose between freshness vs cost

**L6 Answer:**

> "S: PM wanted 1-sec freshness for 100M docs. Cost $130k/month.
> T: Decide based on use case.
> A: Built cost model: 1M events/sec * 30 days = $130k. Showed PM: 95% of queries don't need 1-sec, 24-hr batch covers. Premium tier (1% users) gets Flink CDC, 5-sec. Saved $118k/year.
> R: Shipped v1 batch, 99% happy, premium tier grew 5x in 6 months (real revenue)."

---

## Full Stack 60m

### Build: Real-time Latency Dashboard (WebSocket)

```tsx
import { useEffect, useState } from "react";

const Dashboard = () => {
  const [p95, setP95] = useState(0);
  const [shardSkew, setShardSkew] = useState([]);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    const ws = new WebSocket("wss://api/latency-stream");
    ws.onmessage = (event) => {
      if (paused) return;
      const data = JSON.parse(event.data);
      setP95(data.p95);
      setShardSkew(data.shards);
      if (data.p95 > 600) alert("p95 spike!");
    };
    return () => ws.close();
  }, [paused]);

  return (
    <div>
      <h1>p95: {p95}ms</h1>
      <button onClick={() => setPaused(!paused)}>
        {paused ? "Resume" : "Pause"}
      </button>
      {shardSkew.map(s => (
        <div className={s.docs > 12_000_000 ? "text-red-500" : ""}>
          Shard {s.id}: {s.docs.toLocaleString()} docs
        </div>
      ))}
    </div>
  );
};
```

---

# LOOP 5 - Theme: Eval + Observability + Gold Dataset

## Greet 15m

### Q1: How do you know RAG is good? What metrics?

**L6 Answer:**

> "Three layers: 1. **Offline:** Recall@8, nDCG@8 on gold set. 2. **Online:** Thumbs up rate, session length, friend-accept-rate (for PYMK). 3. **Quality:** LLM-as-judge grounded rate. I track all 3 in dashboard, alert if any drops >2%."

### Q2: Tell me about time your eval was wrong

**L6 Answer:**

> "S: Eval said Recall@8 0.92, shipped. Online thumbs-up dropped 73%->62%.
> T: Find why offline != online.
> A: Gold set was stale - 6 months old, didn't reflect new query patterns. Updated gold set with last 30 days of accepted answers, re-ran eval, Recall 0.92 -> 0.85, matched online. Built pipeline to refresh gold set weekly.
> R: Eval now matches online within 3%."

---

## AI-Native DE Full Stack 60m

### Q1 Data Model: Eval harness

```sql
eval_runs(
  run_id PK,
  prompt_version,
  model_version,
  started_at,
  completed_at,
  total_examples,
  status running/completed/failed
);
eval_examples(
  example_id PK,
  run_id FK,
  query,
  gold_chunks JSON,
  predicted_chunks JSON,
  recall_at_8 FLOAT,
  ndcg_at_8 FLOAT,
  grounded_score FLOAT,  -- LLM-as-judge
  cost_usd FLOAT,
  latency_ms INT
);
```

### Q2 Pipeline: Gold dataset

> "1. Feedback.corrected_answer (thumbs_down) -> gold_dataset raw
> 2. PII scrub (Presidio)
> 3. LLM-as-judge: is corrected_answer grounded in original_chunks? If grounded_rate < 90%, reject
> 4. Daily Spark job: 80/20 train/eval split
> 5. Fine-tuning job: train new prompt_version, eval on 20% holdout
> 6. Compare new vs prod: ship if +2% Recall"

### Q3 SQL: Compare prompt versions

```sql
SELECT
  prompt_version,
  AVG(satisfaction) AS avg_sat,
  AVG(recall_at_8) AS avg_recall,
  COUNT(*) AS eval_count
FROM eval_runs r
JOIN eval_examples e ON r.run_id = e.run_id
WHERE r.started_at >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY prompt_version
HAVING AVG(satisfaction) > 0.7
ORDER BY avg_recall DESC;
```

### Q4 Coding: LLM-as-judge + Recall@K

```python
def recall_at_k(predicted: list, gold: list, k: int = 8) -> float:
    """predicted = doc_ids retrieved, gold = doc_ids known correct."""
    if not gold:
        return 0.0
    predicted_top_k = set(predicted[:k])
    return len(predicted_top_k & set(gold)) / len(gold)


def ndcg_at_k(predicted: list, gold_relevance: dict, k: int = 8) -> float:
    """gold_relevance = {doc_id: relevance_score}."""
    dcg = sum(
        gold_relevance.get(doc_id, 0) / math.log2(i + 2)
        for i, doc_id in enumerate(predicted[:k])
    )
    idcg = sum(
        sorted(gold_relevance.values(), reverse=True)[i] / math.log2(i + 2)
        for i in range(min(k, len(gold_relevance)))
    )
    return dcg / idcg if idcg > 0 else 0.0


def llm_judge_grounded(answer: str, evidence_json: list) -> float:
    """Use LLM to check if answer is grounded in evidence. Returns 0-1."""
    prompt = f"""Is this answer fully grounded in the evidence?
    Answer: {answer}
    Evidence: {evidence_json}
    Score 0-1, where 1 = fully grounded, 0 = hallucinated.
    Only return the number."""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return float(response.choices[0].message.content.strip())
```

---

## Sr Tech Design 60m

### Design: RAG Eval Platform

> "Nightly, 10k gold queries, 2 prompt versions, Recall@8, nDCG, LLM-judge, cost, report, alert if regression >2%.

**Architecture:**

```
Airflow daily 2am -> Spark job reads gold_dataset (10k queries)
  -> For each prompt_version: embed + retrieve + LLM answer
  -> Compute Recall@8, nDCG@8, grounded_score, cost
  -> Write to eval_examples table
  -> Compare vs yesterday: if Recall drop >2%, alert
  -> Generate report (HTML), email stakeholders
  -> Dashboard: time-series chart of Recall@8 over 30 days
```

**Cost:** 10k queries * $0.005 = $50/night = $1.5k/month. Cheap.

**Alert:** PagerDuty if Recall drop >2% on prod prompt_version."

---

## Sr Ownership 30m

### Q1: Tell me about time your RAG looked good offline but failed online

**L6 Answer:**

> "S: Recall@8 0.92, shipped. Online satisfaction 73%->62%.
> T: Find discrepancy.
> A: 1. Checked query distribution - online had 30% new query types not in gold set. 2. Built online query sampling, added to gold set. 3. Re-ran eval, Recall 0.92->0.86, matched online. 4. Built weekly gold set refresh.
> R: Eval now matches online within 3%."

### Q2: Tell me about time you built observability from scratch

**L6 Answer:**

> "S: New team, no dashboards, debugging blind.
> T: Build observability in 1 week.
> A: 1. ClickHouse for traces (free, fast). 2. Grafana dashboards: latency p50/p95/p99, Recall@8, satisfaction, cost. 3. Alerts: p95>600ms, Recall drop>2%, satisfaction<70%. 4. PagerDuty integration. 5. Runbook for each alert.
> R: MTTR from 4 hours to 30 minutes. Team velocity 2x."

---

## Full Stack 60m

### Build: Eval Comparison Dashboard

```tsx
// Table of eval runs, side-by-side metrics, diff of prompts, chart, promote button
const EvalDashboard = () => {
  const [runs, setRuns] = useState([]);
  const [selected, setSelected] = useState([]);

  return (
    <div>
      <h1>Eval Runs (last 7 days)</h1>
      <table>
        <thead>
          <tr>
            <th>Version</th><th>Recall@8</th><th>nDCG</th>
            <th>Grounded</th><th>Cost</th><th>Action</th>
          </tr>
        </thead>
        <tbody>
          {runs.map(r => (
            <tr key={r.run_id}>
              <td>{r.prompt_version}</td>
              <td>{r.recall_at_8.toFixed(3)}</td>
              <td>{r.ndcg_at_8.toFixed(3)}</td>
              <td>{r.grounded_score.toFixed(2)}</td>
              <td>${r.cost_usd.toFixed(2)}</td>
              <td>
                <button onClick={() => promoteWinner(r.run_id)}>
                  Promote
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {/* Chart: Recall@8 over time */}
      <LineChart data={runs} xKey="started_at" yKey="recall_at_8" />
    </div>
  );
};
```

---

# LOOP 6 - Theme: Security + ACL + PII + GDPR

## Greet 15m

### Q1: How do you handle private repos/docs in RAG?

**L6 Answer:**

> "Three layers: 1. **Ingestion:** Mark docs with team_id, is_private bool. 2. **Retrieval:** Filter by team_id in Qdrant payload before LLM call. 3. **Generation:** Audit log every access. ACL filter BEFORE LLM saves cost and prevents leak via embeddings."

### Q2: Tell me about GDPR delete you owned

**L6 Answer:**

> "S: User requested GDPR delete of all their docs. Spread across Qdrant (10 shards), Postgres, S3, ClickHouse.
> T: Delete everywhere within 5 days SLA.
> A: 1. Wrote GDPR delete Flink job: scan Qdrant by user_id, delete. 2. Postgres DELETE. 3. S3 lifecycle rule. 4. ClickHouse ALTER TABLE DELETE. 5. Audit log in `gdpr_audit(user_id, deleted_from, timestamp)`. 6. Tested: 1M docs deleted in 30 min.
> R: 100% deletion, audit trail, 30 min vs 5 day SLA. Used for 50+ requests."

---

## AI-Native DE Full Stack 60m

### Q1 Data Model: ACL + PII

```sql
repos(repo_id PK, name, is_private BOOL, team_id);
repo_acl(repo_id FK, user_id, permission read/write/admin);
documents(doc_id PK, repo_id FK, content, team_id, is_pii BOOL, pii_types ARRAY);
traces(trace_id PK, user_id, doc_id, accessed_at, permission_used);
pii_scrub_log(scrub_id PK, doc_id, original_hash, scrubbed_hash, pii_types, scrubber_version);
gdpr_audit(audit_id PK, user_id, action, target, completed_at);
```

### Q2 Pipeline: PII + GDPR

> "1. Presidio on ingest, marks is_pii=true, pii_types=[email, ssn]
> 2. GDPR delete Flink job: triggered by user request
> 3. Scans Qdrant by user_id, DELETE points
> 4. Postgres DELETE FROM documents WHERE user_id=X
> 5. S3 DeleteObjects batch
> 6. ClickHouse ALTER TABLE traces DELETE WHERE user_id=X
> 7. Writes gdpr_audit row
> 8. SLA: 5 min for 1M docs"

### Q3 SQL: ACL audit + PII leak

```sql
-- ACL audit: who accessed what
SELECT
  t.user_id,
  COUNT(DISTINCT t.doc_id) AS private_docs_accessed,
  MIN(t.accessed_at) AS first_access,
  MAX(t.accessed_at) AS last_access
FROM traces t
JOIN repo_acl a ON t.doc_id = a.doc_id
WHERE a.permission = 'read'
  AND t.accessed_at > NOW() - INTERVAL '30' DAY
GROUP BY t.user_id
ORDER BY private_docs_accessed DESC;

-- PII leak rate
SELECT
  COUNT(*) AS total_scrubbed,
  SUM(CASE WHEN is_pii_after_scrub THEN 1 ELSE 0 END) AS leaks,
  ROUND(100.0 * SUM(CASE WHEN is_pii_after_scrub THEN 1 ELSE 0 END) / COUNT(*), 2) AS leak_pct
FROM pii_scrub_log
WHERE scrubbed_at > NOW() - INTERVAL '7' DAY;
```

### Q4 Coding: ACL filter + PII scrubber + GDPR delete

```python
def acl_filter_before_llm(user_id: int, candidate_chunks: list) -> list:
    """Filter chunks by ACL BEFORE LLM call - saves cost + prevents leak."""
    user_teams = get_user_teams(user_id)  # [team_1, team_2]
    return [
        c for c in candidate_chunks
        if not c.is_private or c.team_id in user_teams
    ]


def gdpr_delete_user(user_id: int):
    """Delete all user data across Qdrant, Postgres, S3, ClickHouse."""
    # Qdrant - delete by user_id filter
    qdrant.delete(
        collection_name="docs",
        points_selector=models.FilterSelector(
            filter=models.Filter(must=[
                models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
            ])
        )
    )
    # Postgres
    postgres.execute("DELETE FROM documents WHERE user_id = %s", (user_id,))
    # S3
    s3.delete_objects(Bucket="docs", Delete={"Objects": list_s3_keys(user_id)})
    # ClickHouse
    clickhouse.execute(f"ALTER TABLE traces DELETE WHERE user_id = {user_id}")
    # Audit
    audit_log(user_id, "gdpr_delete", "all_systems")
```

---

## Sr Tech Design 60m

### Design: Secure Workplace Search

> "100M docs, ACL per doc, search only returns docs user can read, no leak via embeddings, PII scrub, GDPR delete 5-min, audit log.

**Architecture:**

```
Ingestion: PII scrub (Presidio) -> embed -> Qdrant with team_id payload
Query: 
  1. User query -> embed -> Qdrant search Top 100
  2. ACL filter: WHERE team_id IN (user_teams) -- BEFORE LLM
  3. LLM with filtered chunks only
  4. Audit log: user_id, doc_ids, permission_used
GDPR: Flink job triggered by user request, deletes from 4 systems
```

**No embedding leak:** Even if attacker queries without auth, Qdrant filter rejects. Embeddings never exposed to client."

---

## Sr Ownership 30m

### Q1: Tell me about security incident you owned

**L6 Answer:**

> "S: Found bug - private repo doc was retrievable by user NOT on team. Audit log caught it.
> T: Patch ACL bug, audit all users.
> A: 1. Root cause: ACL filter was AFTER LLM, not before. Chunks leaked via LLM response. 2. Moved ACL filter to Qdrant query. 3. Audited last 30 days traces, found 12 users got 3 private docs each. 4. Notified security, GDPR notification. 5. Wrote test: every private doc must NOT be retrievable by non-team.
> R: 100% patch, 0 leak after, security team happy, ran retro."

### Q2: Tell me about time you had to say no due to privacy

**L6 Answer:**

> "S: PM wanted to log full query text for 30 days for analytics.
> T: Push back on privacy.
> A: Showed PM: PII in queries (SSN, email) violates GDPR. Proposed: log query_hash, not text. Store 24h hot, 7d aggregated. PM agreed.
> R: Privacy compliant, analytics still work. Avoided $500k GDPR fine risk."

---

## Full Stack 60m

### Build: ACL Debugger

```tsx
// UI shows why doc is visible/invisible to user, with test-as-user feature
const ACLDebugger = () => {
  const [docId, setDocId] = useState("");
  const [userId, setUserId] = useState("");
  const [result, setResult] = useState(null);

  const checkACL = async () => {
    const res = await fetch(`/api/acl/check?doc=${docId}&user=${userId}`);
    setResult(await res.json());
  };

  return (
    <div className="p-6">
      <input placeholder="doc_id" onChange={e => setDocId(e.target.value)} />
      <input placeholder="user_id" onChange={e => setUserId(e.target.value)} />
      <button onClick={checkACL}>Check</button>
      {result && (
        <div>
          <h2>Result: {result.allowed ? "ALLOWED" : "DENIED"}</h2>
          <p>Doc team: {result.doc.team_id}</p>
          <p>User teams: {result.user.teams.join(", ")}</p>
          <p>Permission: {result.permission}</p>
          {result.reason && <p>Reason: {result.reason}</p>}
        </div>
      )}
    </div>
  );
};
```

---

# LOOP 7 - Theme: Migration + Model Upgrades + Dual-Write

## Greet 15m

### Q1: How do you upgrade embedding model without downtime?

**L6 Answer:**

> "Four steps: 1. Create shadow collection (v2_shadow). 2. Dual-write new docs to both v1 and v2. 3. Spark backfill 10% daily. 4. Dual-read 1% traffic to v2 for eval. 5. Compare Recall@8. 6. When v2 >= v1 for 7 days, cutover 100%. Rollback via feature flag in 5 min."

### Q2: Tell me about migration you owned

**L6 Answer:**

> "ES -> Qdrant for 10M docs, zero downtime. Dual-write via Kafka, Spark backfill, shadow read 1% for 7 days, cutover when Qdrant Recall > ES. Saved $38k/month, latency 1.2s->420ms. Wrote runbook used by 2 teams."

---

## AI-Native DE Full Stack 60m

### Q1 Data Model: Shadow collections

```sql
-- Track model versions
model_versions(
  model_version PK,
  created_at,
  is_production BOOL,
  is_shadow BOOL,
  traffic_pct FLOAT
);
-- Shadow collections
qdrant_collections(
  collection_name PK,  -- 'docs_v1', 'docs_v2_shadow'
  model_version,
  shard_count,
  doc_count
);
-- Dual-write logs
dual_write_log(
  log_id PK,
  doc_id,
  v1_status,  -- success/fail
  v2_status,
  timestamp
);
```

### Q2 Pipeline: Dual-write + backfill

> "1. New docs -> Kafka -> Flink writes to v1 (prod) + v2_shadow
> 2. Spark job: 10% backfill daily from v1 -> v2_shadow
> 3. Dual-read: 1% queries go to v2_shadow, log both responses
> 4. Compare: Recall@8 v2 vs v1 daily
> 5. When v2 >= v1 for 7 days -> cutover 100%
> 6. Rollback: feature flag `embedding_model_version`, 5 min to switch"

### Q3 SQL: Shadow vs prod comparison

```sql
SELECT
  model_version,
  AVG(recall_at_8) AS avg_recall,
  AVG(latency_ms) AS avg_latency,
  COUNT(*) AS query_count
FROM traces
WHERE model_version IN ('v1', 'v2_shadow')
  AND timestamp > NOW() - INTERVAL '7' DAY
GROUP BY model_version
ORDER BY avg_recall DESC;
```

### Q4 Coding: Shadow + dual-read + rollback

```python
class EmbeddingModelRouter:
    def __init__(self):
        self.shadow_pct = 0.01  # 1% shadow traffic
        self.feature_flag = "embedding_v2_enabled"
        self.v1_model = load_model("text-embedding-3-small")
        self.v2_model = load_model("text-embedding-3-large")

    def embed(self, text: str) -> tuple[list, str]:
        # Check feature flag for 100% cutover
        if feature_flag_enabled(self.feature_flag):
            return self.v2_model.encode(text), "v2"

        # 1% shadow traffic
        if random.random() < self.shadow_pct:
            v1_emb = self.v1_model.encode(text)
            v2_emb = self.v2_model.encode(text)
            log_shadow_comparison(text, v1_emb, v2_emb)
            return v1_emb, "v1"  # still return v1 to user

        return self.v1_model.encode(text), "v1"

    def rollback(self):
        """5-min rollback via feature flag."""
        disable_feature_flag(self.feature_flag)
        # All traffic back to v1
```

---

## Sr Tech Design 60m

### Design: Embedding Model Upgrade System

> "text-embedding-3-small -> large, 1B chunks, zero downtime, $130k cost control, eval before cutover, 5-min rollback.

**Architecture:**

```
1. Create v2_shadow collection (10 shards, 100M/shard)
2. Dual-write: Kafka -> Flink writes to v1 + v2
3. Spark backfill: 10% daily, 10 days = 100% backfilled
4. Dual-read: 1% queries, log Recall@8, latency, cost
5. Compare daily: if v2_recall >= v1_recall + 2% for 7 days -> cutover
6. Cutover: feature flag embedding_v2_enabled = true, 100% v2
7. Rollback: feature flag = false, 5 min
8. Cost: $130k one-time backfill + $0.0001/query extra
```

**Eval:** Daily 10k gold queries run against v2_shadow, compare to v1. Only promote if +2% Recall."

---

## Sr Ownership 30m

### Q1: Tell me about migration that went wrong - how rollback?

**L6 Answer:**

> "S: Qdrant cutover 100%, after 1h, p95 spiked 420ms->2s, satisfaction dropped 73%->50%.
> T: Rollback in 5 min.
> A: 1. Flipped feature flag embedding_v2_enabled = false, all traffic back to v1. 2. Latency back to 420ms in 3 min. 3. Root cause: v2 model was 3x larger, Qdrant shards undersized. 4. Upgraded Qdrant shard memory 2x, retried. 5. Cutover 1 week later, smooth.
> R: MTTR 5 min, prevented 1h outage. Feature flag was key."

### Q2: Tell me about time you had to convince team to invest in shadow infra

**L6 Answer:**

> "S: Team said shadow infra 'too expensive, never needed'.
> T: Convince with data.
> A: Showed 3 past incidents where shadow infra would have prevented: 1. Embedding upgrade caused 2h outage, cost $50k revenue. 2. Schema migration broke 5% queries. 3. New feature regressed Recall. Total cost: $300k. Shadow infra cost: $30k one-time. 10x ROI.
> R: Team approved, built in 1 month. Prevented 2 more incidents since."

---

## Full Stack 60m

### Build: Model Upgrade Dashboard

```tsx
const ModelUpgradeDashboard = () => {
  const [progress, setProgress] = useState(0);
  const [comparison, setComparison] = useState(null);

  return (
    <div className="p-6">
      <h1>Model Upgrade: v1 -> v2</h1>
      <ProgressBar value={progress} max={100} />
      <p>{progress}% backfilled</p>

      <table>
        <thead>
          <tr><th>Version</th><th>Recall@8</th><th>Latency</th><th>Cost</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>v1 (prod)</td>
            <td>{comparison?.v1.recall.toFixed(3)}</td>
            <td>{comparison?.v1.latency}ms</td>
            <td>${comparison?.v1.cost}</td>
          </tr>
          <tr>
            <td>v2 (shadow)</td>
            <td>{comparison?.v2.recall.toFixed(3)}</td>
            <td>{comparison?.v2.latency}ms</td>
            <td>${comparison?.v2.cost}</td>
          </tr>
        </tbody>
      </table>

      <button onClick={promoteV2} disabled={!canPromote}>
        Promote v2 to 100%
      </button>
      <button onClick={rollback} className="bg-red-500">
        Rollback to v1
      </button>
    </div>
  );
};
```

---

# LOOP 8 - Theme: Personalization + Multi-tenant + 500M Users

## Greet 15m

### Q1: How do you personalize RAG?

**L6 Answer:**

> "Three signals: 1. **User history:** Last 100 queries + clicks, build user embedding. 2. **Team context:** Filter by user's team docs first. 3. **Time-of-day:** Morning = work docs, evening = personal. Combine via rerank: boost docs similar to user embedding, filter by team, weight by recency."

### Q2: How handle multi-tenant?

**L6 Answer:**

> "Qdrant payload `team_id` field, filter at query time. Each tenant gets own logical collection, but physical shards shared. Per-tenant rate limit, per-tenant cost tracking. Audit log for cross-tenant access attempts (alert if any)."

---

## AI-Native DE Full Stack 60m

### Q1 Data Model: Personalization

```sql
user_preferences(
  user_id PK,
  user_embedding VECTOR,  -- from click history
  preferred_collections ARRAY,
  preferred_languages ARRAY,
  updated_at
);
user_history(
  user_id,
  query,
  clicked_doc_id,
  feedback_rating,
  timestamp
) PARTITIONED BY (DATE(timestamp));
tenants(tenant_id PK, name, shard_strategy, rate_limit_rps);
```

### Q2 Pipeline: Personalization

> "1. User clicks -> Flink aggregates to user_embedding (avg of clicked doc embeddings, decayed)
> 2. Query: embed user query -> Qdrant search with filter `team_id IN user_teams`
> 3. Rerank: boost docs similar to user_embedding * 0.3
> 4. Multi-tenant: per-tenant sharding by `hash(tenant_id) % 50`
> 5. Audit: log cross-tenant access attempts"

### Q3 SQL: Personalization lift

```sql
SELECT
  team_id,
  AVG(CASE WHEN personalized = TRUE THEN satisfaction ELSE NULL END) -
  AVG(CASE WHEN personalized = FALSE THEN satisfaction ELSE NULL END) AS lift
FROM traces t
JOIN users u ON t.user_id = u.user_id
WHERE timestamp > NOW() - INTERVAL '30' DAY
GROUP BY team_id
ORDER BY lift DESC;
```

### Q4 Coding: Personalized rerank

```python
def personalized_rerank(query_emb, user_emb, candidates, boost=0.3):
    """Boost docs similar to user history."""
    scores = []
    for doc in candidates:
        # Cosine similarity
        base_score = cosine_sim(query_emb, doc.embedding)
        user_sim = cosine_sim(user_emb, doc.embedding) if user_emb else 0
        # Combined
        final = base_score + boost * user_sim
        scores.append((doc, final))
    return sorted(scores, key=lambda x: x[1], reverse=True)


def tenant_isolation_filter(user_id, candidates):
    """Ensure no cross-tenant leak."""
    user_tenant = get_user_tenant(user_id)
    return [c for c in candidates if c.tenant_id == user_tenant]
```

---

## Sr Tech Design 60m

### Design: Personalized Workplace Search

> "500M users, personalized, multi-tenant, no cross-team leak, 500ms p95.

**Architecture:**

```
User query -> embed -> Qdrant search
  -> Filter 1: team_id IN user_teams (mandatory)
  -> Filter 2: user_tenant_id = user_tenant (mandatory)
  -> Top 100 -> Rerank with user_embedding boost
  -> LLM answer
  -> Audit: log user_id, doc_ids, tenant_id
```

**Multi-tenant:** 50 logical tenants, 100 physical shards, `hash(tenant_id) % 100` for routing. Per-tenant rate limit, per-tenant cost dashboard. No cross-tenant joins.

**Personalization:** User embedding updated nightly from click history. Boost 0.3 weight in rerank."

---

## Sr Ownership 30m

### Q1: Tell me about personalization that went wrong - filter bubble?

**L6 Answer:**

> "S: Personalized RAG, user only saw docs from their team. Echo chamber.
> T: Add diversity.
> A: 1. Added diversity constraint: top 20 must have >= 3 different 'social clusters' (workplace, school, mutual friends). 2. Measured by graph conductance. 3. A/B test: diversity group had +5% long-term retention vs control.
> R: Shipped diversity, prevented filter bubble, +5% retention."

### Q2: Tell me about multi-tenant incident

**L6 Answer:**

> "S: Tenant A's user accidentally saw Tenant B's private doc. P0 incident.
> T: Patch in 1 hour.
> A: 1. Root cause: tenant_id filter was missing in Qdrant query. 2. Added mandatory tenant_id filter. 3. Audit log caught it, only 1 user affected. 4. Notified Tenant B, GDPR audit. 5. Added test: every query MUST have tenant_id filter. 6. CI gate fails if missing.
> R: 1h MTTR, 1 user affected, prevented future leaks."

---

## Full Stack 60m

### Build: Personalization Debugger

```tsx
const PersonalizationDebugger = () => {
  const [userId, setUserId] = useState("");
  const [docId, setDocId] = useState("");
  const [debug, setDebug] = useState(null);

  return (
    <div>
      <h1>Why is this doc ranked high for this user?</h1>
      <div>
        <label>Personalization: <input type="checkbox" /></label>
      </div>
      {debug && (
        <div>
          <p>Base score (query-doc sim): {debug.base_score}</p>
          <p>User history match: {debug.user_sim}</p>
          <p>Team match: {debug.team_match ? "yes" : "no"}</p>
          <p>Final score: {debug.final_score}</p>
          <p>Personalization boost: {debug.boost}</p>
        </div>
      )}
    </div>
  );
};
```

---

# LOOP 10 - Theme: Final Staff Bar - 0->1 Ambiguous Product (Hardest)

## Greet 15m

### Q1: Tell me about 0->1 you built with no requirements

**L6 Answer:**

> "Built APEX-RAG from scratch. No PM, no spec, no user. I defined: problem (RAG satisfaction 45%), solution (eval harness first), success metrics (Recall@8, satisfaction, cost), built MVP in 3 months, validated with 10 users, iterated to 500. Most 0->1 fails because people code before defining success. I defined metrics first."

### Q2: What would you build if you had 6 months free?

**L6 Answer:**

> "AI Meeting Summarizer. Problem: 1B meetings/year at Meta, no searchable record, knowledge lost. Solution: record -> transcribe -> chunk -> embed -> searchable, with citations to transcript + referenced docs. Success metrics: time saved per user, citation accuracy, search recall. 0->1, I'd ship MVP in 2 months, iterate 4."

---

## AI-Native DE Full Stack 60m

### Q1 Data Model: AI Meeting Summarizer (you define)

```sql
meetings(meeting_id PK, title, host_id, started_at, ended_at, attendee_ids ARRAY);
transcripts(meeting_id FK, segment_id, speaker_id, text, start_ts, end_ts, embedding);
referenced_docs(meeting_id FK, doc_id, referenced_at, context);
meeting_summaries(summary_id PK, meeting_id FK, summary_text, action_items JSON, citations JSON, generated_by);
traces(trace_id PK, user_id, query, meeting_id, accessed_at);
```

### Q2 Pipeline: 0->1 Meeting Summarizer

> "1. Meeting ends -> recording -> Whisper transcription -> chunks by speaker turn
> 2. Embed each chunk with text-embedding-3-large
> 3. Identify referenced docs (NER + URL extraction)
> 4. Embed referenced docs, link to meeting
> 5. LLM summary: prompt = `transcript + referenced_docs, output summary + action_items + citations`
> 6. Citations: {transcript_segment_id, doc_id, chunk_id}
> 7. Store in Qdrant, search by query
> 8. Eval: LLM-as-judge on summary quality + citation accuracy"

### Q3 SQL: Define success metrics

```sql
-- Metric 1: time saved per user
SELECT
  user_id,
  COUNT(*) AS summaries_read,
  AVG(time_saved_minutes) AS avg_saved
FROM meeting_summary_usage
GROUP BY user_id;

-- Metric 2: citation accuracy (LLM-as-judge)
SELECT
  AVG(citation_accuracy) AS avg_acc,
  COUNT(*) AS summaries
FROM meeting_summaries
WHERE created_at > NOW() - INTERVAL '7' DAY;

-- Metric 3: search recall
SELECT
  AVG(recall_at_8) AS avg_recall
FROM eval_runs
WHERE feature = 'meeting_search';
```

### Q4 Coding: Meeting chunker + citation extractor

```python
def chunk_meeting_transcript(segments: list) -> list[dict]:
    """Chunk by speaker turn + topic shift."""
    chunks = []
    current_chunk = {"speakers": [], "text": "", "start_ts": None, "end_ts": None}
    for seg in segments:
        if not current_chunk["text"]:
            current_chunk["start_ts"] = seg.start_ts
        current_chunk["speakers"].append(seg.speaker_id)
        current_chunk["text"] += f"{seg.speaker_id}: {seg.text}\n"
        current_chunk["end_ts"] = seg.end_ts
        if len(current_chunk["text"]) > 1000:  # ~250 tokens
            chunks.append(current_chunk)
            current_chunk = {"speakers": [], "text": "", "start_ts": None, "end_ts": None}
    if current_chunk["text"]:
        chunks.append(current_chunk)
    return chunks


def extract_citations(summary: str, evidence: list) -> list[dict]:
    """Extract citations from LLM summary, verify against evidence."""
    import re
    citations = []
    # LLM output format: [transcript:seg_123] or [doc:doc_456]
    pattern = r"\[(transcript|doc):([a-zA-Z0-9_-]+)\]"
    for match in re.finditer(pattern, summary):
        kind, ref_id = match.groups()
        # Verify reference exists in evidence
        if any(e.get("id") == ref_id and e.get("type") == kind for e in evidence):
            citations.append({"type": kind, "id": ref_id, "valid": True})
        else:
            citations.append({"type": kind, "id": ref_id, "valid": False})
    return citations
```

---

## Sr Tech Design 60m

### Design: 0->1 "Ask Meta" - You define

> "Single search box, searches code + docs + people + meetings, explains with citations, ACL, freshness, 500M users. No PM - I define requirements.

**My requirements (L6+ = define the problem):**

- **Scale:** 500M users, 100M docs, 1B meetings, 1B code files
- **Latency:** p95 <500ms
- **Quality:** grounded citations, no hallucination
- **ACL:** private repos/people visible only to team
- **Freshness:** 5-min for new content
- **Success metrics:** daily active users, queries/user, satisfaction, citation accuracy

**Architecture:**

```
Query -> embed -> parallel search:
  1. Code (Qdrant, AST chunked)
  2. Docs (Qdrant + BM25 hybrid)
  3. People (TAO social graph)
  4. Meetings (Qdrant, transcript chunks)
  -> Merge top 50, dedup, rerank
  -> LLM with grouped answer: "Here's code, docs, and people that match..."
  -> Citations: [code:file.py:42] [doc:wiki:123] [person:alice]
  -> ACL filter BEFORE LLM
```

**0->1 milestones:**
- Month 1: Docs only, 10 users
- Month 2: Add code, 100 users
- Month 3: Add people, 1000 users
- Month 4: Add meetings, 10K users
- Month 5: Polish, scale to 100K
- Month 6: 500M users"

---

## Sr Ownership 30m

### Q1: Tell me about time you defined problem when no one knew what to build

**L6 Answer:**

> "S: Team had vague 'improve search' mandate, no PM, no spec.
> T: Define problem + success metrics in 1 week.
> A: 1. Interviewed 10 users, found top 3 pain points. 2. Defined success: satisfaction 73%->85%, p95 1.2s->500ms, Recall@8 0.71->0.85. 3. Built eval harness, ran baseline. 4. Proposed 3 options to director with cost/benefit. 5. Picked one, shipped.
> R: 4-month project, hit all 3 metrics, director happy, became team template."

### Q2: Tell me about time you killed a project

**L6 Answer:**

> "S: 3 months into real-time Flink CDC, cost $50k/month, 5% usage.
> T: Kill or pivot.
> A: 1. Built cost/usage dashboard: 95% of users on 24h batch, 5% on real-time. 2. Showed director: 50x cost for 5% users. 3. Proposed: keep Flink for premium tier only. 4. Killed general rollout. 5. Reassigned 2 engineers to other work.
> R: Saved $500k/year, freed 2 engineers for higher-impact work. Director respected data-driven kill."

---

## Full Stack 60m

### Build: 0->1 "Ask Meta" UI

```tsx
// Single search box, results grouped by type, citations, follow-up
const AskMeta = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [feedback, setFeedback] = useState(null);

  return (
    <div className="max-w-3xl mx-auto p-6">
      <input
        type="text"
        placeholder="Ask anything..."
        value={query}
        onChange={e => setQuery(e.target.value)}
        className="w-full p-4 text-lg border rounded"
      />
      <button onClick={search}>Ask</button>

      {results && (
        <div>
          {/* Group by type */}
          {results.code && <CodeResults items={results.code} />}
          {results.docs && <DocResults items={results.docs} />}
          {results.people && <PeopleResults items={results.people} />}
          {results.meetings && <MeetingResults items={results.meetings} />}

          {/* Citations */}
          <div className="mt-4 text-sm text-gray-500">
            Sources: {results.citations.map(c => (
              <span>[{c.type}:{c.id}]</span>
            ))}
          </div>

          {/* Follow-up questions */}
          <div>
            <h3>Follow-up:</h3>
            {results.follow_ups.map(q => (
              <button onClick={() => setQuery(q)}>{q}</button>
            ))}
          </div>

          {/* Feedback */}
          <Feedback onRate={(r) => setFeedback(r)} />
        </div>
      )}
    </div>
  );
};
```

---

# Cross-Loop Summary: How to Use These 7 Themes

| Loop | Best For | Practice Order |
|------|----------|----------------|
| 5 | Warm-up (eval is core L6 skill) | 1st |
| 7 | Most common (model upgrades happen often) | 2nd |
| 6 | High-stakes (security/PII is critical) | 3rd |
| 3 | Differentiator (multimodal is rare skill) | 4th |
| 4 | Hard tech (streaming is interview-killer) | 5th |
| 8 | Advanced (personalization is L7 territory) | 6th |
| 10 | Final bar (0->1 = Staff test) | 7th |

**Recommended practice:** Do 1 loop per day, 1 hour each. 7 days = all 7 themes covered.

---

**Good luck with the mocks. You have 7 angles ready. The bar is the same across all loops: define the problem, ship with metrics, leave a system behind.**
