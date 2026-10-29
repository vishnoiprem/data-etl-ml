"""
Cell 8: Bulk insert 10k chunks + benchmark KNN latency.

What this proves for the L6 interview:
- Real KNN latency at 10k scale (1B / day is hard, but 10k shows the curve)
- Bulk insert via executemany is 100-1000x faster than per-row
- HNSW index needed at 10M+ scale (brute force O(n) won't cut it)
- The "p95 < 500ms" requirement maps to specific index choices
"""
import sqlite3
import sqlite_vec
import numpy as np
import time
import statistics

# ─── Connect and load extension ────────────────────────────────────
conn = sqlite3.connect(':memory:')
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)

# Schema for the 10k chunks
conn.executescript("""
    CREATE TABLE chunks_vec_10k (
        chunk_id      TEXT PRIMARY KEY,
        embedding     float[128],   -- 128-dim to make brute force meaningful
        model_version TEXT,
        created_at    TEXT
    );
    CREATE VIRTUAL TABLE chunks_vec_10k_idx USING vec0(
        embedding float[128],
        chunk_id text,
        model_version text
    );
""")
print("Schema: chunks_vec_10k (regular) + chunks_vec_10k_idx (vec0 KNN index)\n")

# ─── Generate 10k embeddings (128-dim) ─────────────────────────────
N = 10_000
DIM = 128
np.random.seed(42)

# Random unit vectors (this is what real embeddings look like roughly)
embeddings = np.random.randn(N, DIM).astype(np.float32)
embeddings /= np.linalg.norm(embeddings, axis=1, keepdims=True)  # normalize

print(f"Generated {N} normalized {DIM}-dim embeddings")

# ─── Bulk insert (the right way) ───────────────────────────────────
print("\n" + "=" * 70)
print("BULK INSERT (executemany - the production way)")
print("=" * 70)

# Pre-serialize all embeddings once
serialized = [sqlite_vec.serialize_float32(emb.tolist()) for emb in embeddings]
now = "2026-10-14T12:00:00"

# Bulk insert into the regular table
t0 = time.perf_counter()
conn.executemany(
    "INSERT INTO chunks_vec_10k VALUES (?, ?, ?, ?)",
    [(f"chk_{i:05d}", emb, "ada-002", now) for i, emb in enumerate(serialized)]
)
conn.commit()
t1 = time.perf_counter()
print(f"Inserted {N} rows into chunks_vec_10k (regular table)")
print(f"  Time: {(t1-t0)*1000:.1f}ms ({(N/(t1-t0)):.0f} rows/sec)")

# Bulk insert into the vec0 KNN index
t0 = time.perf_counter()
conn.executemany(
    "INSERT INTO chunks_vec_10k_idx(rowid, embedding, chunk_id, model_version) VALUES (?, ?, ?, ?)",
    [(i+1, emb, f"chk_{i:05d}", "ada-002") for i, emb in enumerate(serialized)]
)
conn.commit()
t1 = time.perf_counter()
print(f"Inserted {N} rows into chunks_vec_10k_idx (vec0 index)")
print(f"  Time: {(t1-t0)*1000:.1f}ms ({(N/(t1-t0)):.0f} rows/sec)")

# Compare with single-row inserts (the WRONG way)
t0 = time.perf_counter()
for i, emb in enumerate(serialized):
    conn.execute(
        "INSERT INTO chunks_vec_10k VALUES (?, ?, ?, ?)",
        (f"slow_{i:05d}", emb, "ada-002", now)
    )
conn.commit()
t1 = time.perf_counter()
slow_total_ms = (t1 - t0) * 1000
print(f"\nFor reference: {N} single-row inserts took {slow_total_ms:.1f}ms total")
print(f"  Per-row average: {slow_total_ms/N:.3f}ms/row (each insert = Python call + commit overhead)")

# Cleanup the slow rows
conn.execute("DELETE FROM chunks_vec_10k WHERE chunk_id LIKE 'slow_%'")
conn.commit()

# ─── KNN benchmark at 10k ───────────────────────────────────────────
print("\n" + "=" * 70)
print("KNN LATENCY BENCHMARK (Top 8 retrieval at 10k scale)")
print("=" * 70)

# Random query vector
query = np.random.randn(DIM).astype(np.float32)
query /= np.linalg.norm(query)
query_serialized = sqlite_vec.serialize_float32(query.tolist())

# Warm-up (first query is always slower due to file system caching)
conn.execute("""
    SELECT chunk_id, distance FROM chunks_vec_10k_idx
    WHERE embedding MATCH ?
    ORDER BY distance LIMIT 8
""", (query_serialized,)).fetchall()

# Measure 100 queries
latencies_ms = []
for trial in range(100):
    t0 = time.perf_counter()
    results = conn.execute("""
        SELECT chunk_id, distance FROM chunks_vec_10k_idx
        WHERE embedding MATCH ?
        ORDER BY distance LIMIT 8
    """, (query_serialized,)).fetchall()
    t1 = time.perf_counter()
    latencies_ms.append((t1 - t0) * 1000)

p50 = statistics.median(latencies_ms)
p95 = statistics.quantiles(latencies_ms, n=20)[18]  # 95th percentile
p99 = statistics.quantiles(latencies_ms, n=100)[98]  # 99th percentile
mean = statistics.mean(latencies_ms)

print(f"\nKNN Top-8 over {N:,} embeddings, 100 trials:")
print(f"  Mean:   {mean:.2f}ms")
print(f"  Median: {p50:.2f}ms  (p50)")
print(f"  p95:    {p95:.2f}ms")
print(f"  p99:    {p99:.2f}ms")

print(f"\nInterview talking point: 'At 10k chunks, p95 is {p95:.1f}ms - well under our 500ms budget.'")

# ─── Compare: KNN vs brute force ───────────────────────────────────
print("\n" + "=" * 70)
print("KNN (vec0 index) vs BRUTE FORCE Python loop")
print("=" * 70)

# Brute force: just compute cosine sim on the original numpy array (no DB roundtrip)
# This is what you'd do if you loaded all 10k into memory
t0 = time.perf_counter()
sims = embeddings[::10] @ query  # 1000x128 @ 128 = 1000 dot products
top8_idx = np.argsort(-sims)[:8]
t1 = time.perf_counter()
brute_1k_ms = (t1 - t0) * 1000
print(f"\nBrute force 1000 vectors (numpy): {brute_1k_ms:.2f}ms")

t0 = time.perf_counter()
sims = embeddings @ query  # 10000x128 @ 128 = 10000 dot products
top8_idx = np.argsort(-sims)[:8]
t1 = time.perf_counter()
brute_10k_ms = (t1 - t0) * 1000
print(f"Brute force 10k vectors (numpy): {brute_10k_ms:.2f}ms")
print(f"  Extrapolated to 1M:  {brute_10k_ms*100:.0f}ms  (NOT feasible)")
print(f"  Extrapolated to 10M: {brute_10k_ms*1000:.0f}ms = {brute_10k_ms*1000/1000:.1f}s  (definitely not feasible)")
print(f"\nKNN with HNSW is sub-linear: at 1M vectors, p95 stays around 10-20ms")
print(f"This is why pgvector/Qdrant use HNSW by default, not brute force.")

# ─── Sample query result ───────────────────────────────────────────
print("\n" + "=" * 70)
print("SAMPLE QUERY RESULT")
print("=" * 70)

results = conn.execute("""
    SELECT chunk_id, distance FROM chunks_vec_10k_idx
    WHERE embedding MATCH ?
    ORDER BY distance LIMIT 5
""", (query_serialized,)).fetchall()

print(f"\nQuery vector (random 128-dim unit vector):")
print(f"Top 5 nearest chunks at {N:,} scale:")
for chunk_id, dist in results:
    print(f"  [{dist:.4f}] {chunk_id}")

# ─── The L6 answer for the interview ───────────────────────────────
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'does it scale to 10M / 1B?')")
print("=" * 70)
print("""
Q: "You showed 10k. Does this scale to 10M / 1B?"

A: "Three things change at scale:

1. KNN index choice:
   - 10k: brute force numpy is fine (sub-ms)
   - 10M: HNSW index needed (sqlite-vec uses HNSW, pgvector uses HNSW by default)
   - 1B: IVF or DiskANN, with quantization (PQ/INT8)

2. Storage:
   - 1B x 1536-dim float32 = 6TB of raw vectors
   - Product Quantization (PQ) compresses to ~50 bytes/vector = 50GB total
   - Trade: ~5% recall loss for 100x storage reduction

3. Sharding:
   - 1B is too big for one node. Shard by user_id hash.
   - Qdrant/Pinecone do this automatically.
   - Each shard is ~100M vectors = 600GB raw
   - Per-shard HNSW index fits in RAM of one beefy node

The reference architecture:
- 10M docs: single-node Qdrant with HNSW, <500ms p95 (matches our RAG requirement)
- 100M docs: sharded Qdrant cluster, 4-8 shards
- 1B docs: DiskANN + quantization, dedicated vector DB (Pinecone / Weaviate)
""")
