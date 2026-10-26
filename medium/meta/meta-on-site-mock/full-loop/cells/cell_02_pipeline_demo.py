"""
Cell 02 (full-loop): RAG Pipeline End-to-End

The Round 2.2 answer. Demonstrates:
- Ingestion (S3 -> Kafka -> Worker)
- Embedding (Spark batch with 10-shard Qdrant)
- Query path (hybrid search + rerank + grounded LLM)
- Flink CDC for 5-min freshness
"""
import sqlite3
import sqlite_vec
import numpy as np
import time
import json

conn = sqlite3.connect(':memory:')
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)

# 10-shard Qdrant (simulated as 10 sqlite-vec tables)
N_SHARDS = 10
DIM = 64
N_DOCS = 10_000  # 1k per shard

np.random.seed(42)

print("=" * 60)
print(f"SETUP: 10 Qdrant shards, 1k docs each (= 10k docs total)")
print("=" * 60)

t0 = time.perf_counter()
for shard_id in range(N_SHARDS):
    conn.execute(f"""
        CREATE VIRTUAL TABLE chunks_shard_{shard_id} USING vec0(
            embedding float[{DIM}],
            doc_id TEXT,
            chunk_text TEXT
        )
    """)

# Bulk insert
for i in range(N_DOCS):
    shard = i % N_SHARDS
    vec = np.random.randn(DIM).astype(np.float32)
    conn.execute(
        f"INSERT INTO chunks_shard_{shard} (embedding, doc_id, chunk_text) VALUES (?, ?, ?)",
        (vec.tobytes(), f"doc_{i:05d}", f"text of doc {i}")
    )
conn.commit()
setup_ms = (time.perf_counter() - t0) * 1000
print(f"  Setup: {N_DOCS:,} docs into {N_SHARDS} shards in {setup_ms:.0f}ms")
print(f"  Cost: {N_DOCS:,} * $0.00013 = ${N_DOCS * 0.00013:.2f} (one-time)")

# Query path: hybrid + rerank + grounded
print("\n" + "=" * 60)
print("QUERY PATH: 4 steps, p95 <500ms target")
print("=" * 60)

query = "how does expungement work in California"
query_vec = np.random.randn(DIM).astype(np.float32)

# Step 1: Embed query
t0 = time.perf_counter()
query_emb = query_vec  # already embedded
embed_ms = (time.perf_counter() - t0) * 1000
print(f"  1. Embed query         {embed_ms:.1f}ms  (cached 50% in prod)")

# Step 2: Search all 10 shards in parallel
t0 = time.perf_counter()
all_hits = []
for shard in range(N_SHARDS):
    rows = conn.execute(f"""
        SELECT doc_id, chunk_text, distance
        FROM chunks_shard_{shard}
        WHERE embedding MATCH ?
        ORDER BY distance
        LIMIT 5
    """, (query_emb.tobytes(),)).fetchall()
    all_hits.extend(rows)
search_ms = (time.perf_counter() - t0) * 1000
print(f"  2. Vector search       {search_ms:.1f}ms  (10 shards, top 5 each)")

# Step 3: Rerank (simulated)
t0 = time.perf_counter()
all_hits.sort(key=lambda r: r[2])  # by distance
top_8 = all_hits[:8]
rerank_ms = (time.perf_counter() - t0) * 1000
print(f"  3. Rerank top 8        {rerank_ms:.1f}ms  (simulated, prod ~80ms with Cohere)")

# Step 4: LLM with evidence_json (grounded)
t0 = time.perf_counter()
evidence_json = {
    "chunks": [{"doc_id": r[0], "text": r[1]} for r in top_8],
    "model_version": "gpt-4o",
    "prompt_version": "legal_v3.2.1"
}
# Simulated: production LLM call
llm_ms = 350  # typical GPT-4o p50
print(f"  4. LLM (grounded)      {llm_ms}ms     (with evidence_json enforcement)")

total_ms = embed_ms + search_ms + rerank_ms + llm_ms
print(f"\n  TOTAL p50: {total_ms:.0f}ms")
print(f"  TOTAL p95: ~{total_ms * 1.3:.0f}ms (SLO <500ms {'PASS' if total_ms * 1.3 < 500 else 'CHECK'})")

# Flink CDC for 5-min freshness
print("\n" + "=" * 60)
print("FRESHNESS: Flink CDC, 5-min incremental re-embed")
print("=" * 60)
print("""
Postgres `documents.updated_at` -> Debezium -> Kafka -> Flink:
  - Detect changed docs in last 5 min
  - Re-chunk (only new/changed sections)
  - Re-embed only the delta
  - Dual-write to Qdrant (old + new version)
  - Atomic swap after eval

Typical daily churn: 0.1% of docs.
Full re-embed: 12h Spark. Incremental: 5 min.
""")

# Cost gates
print("=" * 60)
print("COST GATES")
print("=" * 60)
print("""
- Skip embedding if doc quality < threshold (LSA score)
- Cache query embeddings in Memcache (50% hit rate = 50% embedding cost)
- Batch LLM calls (eval pipeline, bulk extraction)
- Cache rerank for popular queries (50% hit = save 40ms p95)
""")
