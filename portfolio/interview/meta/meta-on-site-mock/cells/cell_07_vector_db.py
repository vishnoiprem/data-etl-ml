"""
Vector DB demo - SQLite + sqlite-vec (drop-in for pgvector)
Same SQL concepts as pgvector: CREATE TABLE ... embedding float[N], KNN queries with distance.
"""
import sqlite3
import sqlite_vec
import numpy as np
import json
import uuid
from datetime import datetime

# ─── Connect and enable the vector extension ───────────────────────
conn = sqlite3.connect(':memory:')
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)

print(f"sqlite-vec version: {sqlite_vec.__version__}")
print("Vector extension loaded OK\n")

# ─── Schema (the L6 RAG model) ─────────────────────────────────────
conn.executescript("""
-- 1. documents: source of truth with GDPR tombstone
CREATE TABLE documents (
    doc_id          TEXT PRIMARY KEY,
    source          TEXT,
    uri             TEXT,
    owner_id        TEXT,
    chunk_strategy  TEXT,
    ingested_at     TEXT,
    is_deleted      INTEGER DEFAULT 0,  -- tombstone, NOT hard delete
    hash            TEXT
);

-- 2. chunks: the actual data model
CREATE TABLE chunks (
    chunk_id               TEXT PRIMARY KEY,
    doc_id                 TEXT REFERENCES documents(doc_id),
    chunk_index            INTEGER,
    text                   TEXT,
    token_count            INTEGER,
    embedding_model_version TEXT,
    chunk_hash             TEXT,
    created_at             TEXT,
    UNIQUE (doc_id, chunk_hash, embedding_model_version)
);

-- 3. embeddings: separate table (vector(1536) is 6KB/row)
CREATE TABLE chunks_vec (
    chunk_id      TEXT PRIMARY KEY,
    embedding     float[8],          -- using 8-dim for demo speed
    model_version TEXT,
    created_at    TEXT
);

-- 4. prompts: versioned like code
CREATE TABLE prompts (
    prompt_id       TEXT PRIMARY KEY,
    prompt_template TEXT,
    version         INTEGER,
    created_at      TEXT
);

-- 5. traces: fact table (would be PARTITIONED in prod)
CREATE TABLE traces (
    trace_id            TEXT PRIMARY KEY,
    user_id             TEXT,
    query               TEXT,
    retrieved_chunk_ids TEXT,   -- JSON array
    prompt_version      INTEGER,
    response            TEXT,
    latency_ms          INTEGER,
    cost_tokens         INTEGER,
    created_at          TEXT
);

-- 6. feedback: gold dataset
CREATE TABLE feedback (
    feedback_id      TEXT PRIMARY KEY,
    trace_id         TEXT,
    rating           TEXT CHECK (rating IN ('thumbs_up', 'thumbs_down')),
    corrected_answer TEXT,
    created_at       TEXT
);
""")
print("Schema created: 6 tables (documents, chunks, chunks_vec, prompts, traces, feedback)\n")

# ─── Seed sample data ──────────────────────────────────────────────
now = datetime.utcnow().isoformat()

# 4 sample documents
docs = [
    ("doc_001", "sharepoint", "https://meta.sharepoint.com/meta-history", "user_alice", "langchain_512", "meta_history_overview"),
    ("doc_002", "confluence", "https://meta.atlassian.net/rag-design",  "user_bob",   "semantic_v1",   "rag_architecture_doc"),
    ("doc_003", "s3",         "s3://meta-internal/eval-results-2026",  "user_carol", "langchain_512", "eval_results_q3"),
    ("doc_004", "sharepoint", "https://meta.sharepoint.com/llm-traces", "user_dave",  "langchain_512", "llm_tracing_guide"),
]

for doc_id, source, uri, owner, strategy, hash_val in docs:
    conn.execute(
        "INSERT INTO documents VALUES (?,?,?,?,?,?,?,?)",
        (doc_id, source, uri, owner, strategy, now, 0, hash_val)
    )
print(f"Inserted {len(docs)} documents\n")

# Sample chunks - each doc has 2-3 chunks
chunk_seeds = [
    # (chunk_id, doc_id, idx, text, tokens, model_ver, chunk_hash)
    ("chk_001", "doc_001", 0, "Meta was founded in 2004 by Mark Zuckerberg at Harvard.",            18, "ada-002", "h001"),
    ("chk_002", "doc_001", 1, "The company went public in 2012 with the largest tech IPO at the time.", 22, "ada-002", "h002"),
    ("chk_003", "doc_001", 2, "Meta acquired Instagram in 2012 and WhatsApp in 2014.",                14, "ada-002", "h003"),
    ("chk_004", "doc_002", 0, "RAG combines retrieval from a vector DB with LLM generation.",         16, "ada-002", "h004"),
    ("chk_005", "doc_002", 1, "Hybrid search uses both BM25 keyword search and vector similarity.",    14, "ada-002", "h005"),
    ("chk_006", "doc_002", 2, "Cross-encoder rerankers improve precision at the cost of latency.",    13, "ada-002", "h006"),
    ("chk_007", "doc_003", 0, "Eval dataset size correlates with offline metric reliability.",       12, "ada-002", "h007"),
    ("chk_008", "doc_003", 1, "LLM-as-judge achieves 85% agreement with human raters on factual QA.", 15, "ada-002", "h008"),
    ("chk_009", "doc_004", 0, "Every LLM call should be traced with prompt version, latency, and cost.", 16, "ada-002", "h009"),
    ("chk_010", "doc_004", 1, "Traces are partitioned by day. Drop partitions after 30 days.",      12, "ada-002", "h010"),
]

for chunk_id, doc_id, idx, text, tokens, model_ver, c_hash in chunk_seeds:
    conn.execute(
        "INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?)",
        (chunk_id, doc_id, idx, text, tokens, model_ver, c_hash, now)
    )
print(f"Inserted {len(chunk_seeds)} chunks\n")

# ─── Generate fake embeddings (8-dim for demo) ─────────────────────
np.random.seed(42)

# Make semantically related chunks have similar embeddings
# docs about Meta history -> one cluster
# docs about RAG -> another cluster
# docs about eval -> third
# docs about tracing -> fourth
embeddings_map = {
    "chk_001": np.array([0.9, 0.1, 0.0, 0.0, 0.0, 0.1, 0.0, 0.0]),
    "chk_002": np.array([0.85, 0.15, 0.05, 0.0, 0.0, 0.1, 0.0, 0.0]),
    "chk_003": np.array([0.8, 0.2, 0.1, 0.0, 0.0, 0.1, 0.0, 0.0]),
    "chk_004": np.array([0.0, 0.0, 0.9, 0.1, 0.0, 0.0, 0.1, 0.0]),
    "chk_005": np.array([0.0, 0.0, 0.85, 0.15, 0.0, 0.0, 0.1, 0.05]),
    "chk_006": np.array([0.0, 0.0, 0.8, 0.2, 0.0, 0.0, 0.1, 0.05]),
    "chk_007": np.array([0.0, 0.1, 0.0, 0.0, 0.9, 0.1, 0.0, 0.0]),
    "chk_008": np.array([0.0, 0.1, 0.0, 0.0, 0.85, 0.15, 0.0, 0.0]),
    "chk_009": np.array([0.0, 0.0, 0.1, 0.0, 0.0, 0.0, 0.9, 0.1]),
    "chk_010": np.array([0.0, 0.0, 0.1, 0.0, 0.0, 0.0, 0.85, 0.15]),
}

# Create a vec0 VIRTUAL TABLE for true KNN (the production-style pattern)
conn.execute("CREATE VIRTUAL TABLE chunks_vec_idx USING vec0(embedding float[8], chunk_id text, model_version text)")

# Insert into both: the regular table (analytics) AND the vec0 index (KNN)
for chunk_id, vec in embeddings_map.items():
    # Regular table for metadata queries
    conn.execute(
        "INSERT INTO chunks_vec VALUES (?, ?, ?, ?)",
        (chunk_id, sqlite_vec.serialize_float32(vec.tolist()), "ada-002", now)
    )
    # vec0 virtual table for fast KNN
    conn.execute(
        "INSERT INTO chunks_vec_idx(rowid, embedding, chunk_id, model_version) VALUES (?, ?, ?, ?)",
        (hash(chunk_id) & 0x7FFFFFFF, sqlite_vec.serialize_float32(vec.tolist()), chunk_id, "ada-002")
    )
print(f"Inserted {len(embeddings_map)} 8-dim embeddings into chunks_vec + chunks_vec_idx\n")

# ─── Versioned prompts ────────────────────────────────────────────
prompts = [
    ("prm_001", "You are a helpful assistant. Use the context to answer: {context}\nQ: {query}", 1, now),
    ("prm_002", "You are a Meta engineer. Ground answers in the docs. If unknown say 'unknown'.\n{context}\nQ: {query}", 2, now),
    ("prm_003", "Cite your sources. If the docs don't say, say 'I don't have that info'.\n{context}\nQ: {query}", 3, now),
]
for p_id, template, ver, ts in prompts:
    conn.execute("INSERT INTO prompts VALUES (?,?,?,?)", (p_id, template, ver, ts))
print(f"Inserted {len(prompts)} prompt versions (v1, v2, v3)\n")

# ─── Sample traces (3 example queries) ───────────────────────────
traces = [
    ("trc_001", "user_alice", "When was Meta founded?",          json.dumps(["chk_001","chk_002"]), 1, "Meta was founded in 2004.",         420, 850,  now),
    ("trc_002", "user_bob",   "How does RAG work?",              json.dumps(["chk_004","chk_005"]), 2, "RAG combines retrieval and gen.",   480, 920,  now),
    ("trc_003", "user_carol", "Is LLM-as-judge reliable?",       json.dumps(["chk_008"]),           2, "Yes, 85% agreement with humans.",  390, 750,  now),
]
for trc in traces:
    conn.execute("INSERT INTO traces VALUES (?,?,?,?,?,?,?,?,?)", trc)
print(f"Inserted {len(traces)} traces\n")

# ─── Feedback (gold set) ──────────────────────────────────────────
feedback = [
    ("fdb_001", "trc_001", "thumbs_up",   None,                now),
    ("fdb_002", "trc_002", "thumbs_down", "RAG = retrieval + generation step.",  now),
    ("fdb_003", "trc_003", "thumbs_up",   None,                now),
]
for fb in feedback:
    conn.execute("INSERT INTO feedback VALUES (?,?,?,?,?)", fb)
print(f"Inserted {len(feedback)} feedback rows\n")

conn.commit()

# ═══════════════════════════════════════════════════════════════════
# DEMO 1: Vector similarity search (the actual RAG retrieval)
# ═══════════════════════════════════════════════════════════════════
print("=" * 70)
print("DEMO 1: Vector similarity search")
print("=" * 70)

# Query: "When was the company started?" -> should match Meta history chunks
query = np.array([0.88, 0.12, 0.0, 0.0, 0.0, 0.1, 0.0, 0.0])  # close to chk_001/002/003
query_serialized = sqlite_vec.serialize_float32(query.tolist())

# KNN via vec0 virtual table (production-style: this is the pgvector equivalent)
results = conn.execute("""
    SELECT
        chunk_id,
        distance
    FROM chunks_vec_idx
    WHERE embedding MATCH ?
    ORDER BY distance
    LIMIT 3
""", (query_serialized,)).fetchall()

print(f"\nQuery: 'When was the company started?'\n")
print("Top 3 chunks by cosine distance (KNN):")
for chunk_id, dist in results:
    row = conn.execute("SELECT text FROM chunks WHERE chunk_id = ?", (chunk_id,)).fetchone()
    print(f"  [{dist:.4f}] {chunk_id}: {row[0]}")

# ═══════════════════════════════════════════════════════════════════
# DEMO 2: GDPR tombstone + vector delete
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DEMO 2: GDPR tombstone (user_dave deletes their account)")
print("=" * 70)

# Tombstone the document
conn.execute("UPDATE documents SET is_deleted = 1 WHERE owner_id = 'user_dave'")
print("Tombstoned doc_004 (owner user_dave)")

# Show what would happen in the async purge job
print("\nAsync purge job would now:")
print("  1. Find is_deleted = 1 documents")
print("  2. DELETE FROM chunks WHERE doc_id IN (...)")
print("  3. DELETE FROM chunks_vec WHERE chunk_id IN (...)")
print("  4. Keep traces for 30 days for abuse investigation")

# Simulate the purge
deleted = conn.execute("""
    SELECT COUNT(*) FROM chunks c
    JOIN documents d ON c.doc_id = d.doc_id
    WHERE d.is_deleted = 1
""").fetchone()[0]
print(f"\nWould purge {deleted} chunks from vector DB")

# ═══════════════════════════════════════════════════════════════════
# DEMO 3: Re-embedding with new model (dual-write pattern)
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DEMO 3: Re-embed with new model version (dual-write)")
print("=" * 70)

# New model: text-embedding-3-large (different distribution)
np.random.seed(99)
new_embeddings = {
    "chk_001": np.array([0.95, 0.05, 0.0, 0.0, 0.0, 0.05, 0.0, 0.0]),
    "chk_002": np.array([0.92, 0.08, 0.0, 0.0, 0.0, 0.05, 0.0, 0.0]),
}
# Write to a SHADOW vec0 index (embeddings_v2) - the dual-write pattern
conn.execute("""
    CREATE VIRTUAL TABLE chunks_vec_v2 USING vec0(embedding float[8], chunk_id text, model_version text)
""")

for chunk_id, vec in new_embeddings.items():
    conn.execute(
        "INSERT INTO chunks_vec_v2(rowid, embedding, chunk_id, model_version) VALUES (?, ?, ?, ?)",
        (hash(chunk_id + "_v2") & 0x7FFFFFFF, sqlite_vec.serialize_float32(vec.tolist()), chunk_id, "text-embedding-3-large")
    )
print(f"Dual-wrote {len(new_embeddings)} chunks to chunks_vec_v2 (shadow index)")
print("In prod: serve prod from v1, dual-read 1% from v2 for 7 days, then cutover")

# ═══════════════════════════════════════════════════════════════════
# DEMO 4: Analytics query (the SQL eval from notebook cell 5)
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DEMO 4: RAG quality analytics")
print("=" * 70)

import pandas as pd
df = pd.read_sql_query("""
    SELECT
        t.prompt_version,
        COUNT(*) AS total,
        AVG(CASE WHEN f.rating = 'thumbs_up' THEN 1.0 ELSE 0.0 END) AS satisfaction,
        AVG(t.latency_ms) AS avg_latency
    FROM traces t
    LEFT JOIN feedback f ON t.trace_id = f.trace_id
    GROUP BY t.prompt_version
    ORDER BY t.prompt_version
""", conn)
print("\nA/B test by prompt_version:")
print(df.to_string(index=False))

# ═══════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
counts = {
    "documents":     conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
    "chunks":        conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],
    "embeddings":    conn.execute("SELECT COUNT(*) FROM chunks_vec").fetchone()[0],
    "prompts":       conn.execute("SELECT COUNT(*) FROM prompts").fetchone()[0],
    "traces":        conn.execute("SELECT COUNT(*) FROM traces").fetchone()[0],
    "feedback":      conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0],
}
for table, n in counts.items():
    print(f"  {table:15s}: {n} rows")
print(f"\nVector DB working. Same SQL would run on pgvector in prod.")
