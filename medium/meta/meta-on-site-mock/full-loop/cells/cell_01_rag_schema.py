"""
Cell 01 (full-loop): RAG Schema for 100M docs — dedup, partitions, GDPR

The Round 2.1 answer. L6 demos the magic phrases:
- SHA256 dedup saves 30% (UNIQUE INDEX on hash)
- Embeddings separate table saves 6KB/row on chunks
- Traces partitioned by day, DROP PARTITION for TTL
- is_deleted flag for GDPR (async purge)
"""
import sqlite3
import time
import hashlib

conn = sqlite3.connect(':memory:')

# The schema — what you'd put on the whiteboard
conn.executescript("""
    CREATE TABLE documents (
        doc_id        TEXT PRIMARY KEY,
        collection_id TEXT,
        uri           TEXT,
        hash_sha256   TEXT,
        chunk_strategy TEXT,
        is_deleted    BOOLEAN DEFAULT 0,
        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE UNIQUE INDEX idx_doc_hash ON documents(hash_sha256) WHERE is_deleted = 0;

    CREATE TABLE chunks (
        chunk_id  TEXT PRIMARY KEY,
        doc_id    TEXT,
        text      TEXT,
        token_count INT,
        hash      TEXT,
        embedding_version TEXT,
        UNIQUE(hash, embedding_version)
    );

    CREATE TABLE embeddings (
        chunk_id  TEXT,
        embedding BLOB,
        model_version TEXT,
        qdrant_shard INT,
        PRIMARY KEY (chunk_id, model_version)
    );

    CREATE TABLE traces (
        trace_id      TEXT,
        day           DATE,
        collection_id TEXT,
        query         TEXT,
        chunk_ids     TEXT,
        prompt_version TEXT,
        latency_ms    INT,
        cost_tokens   INT,
        created_at    TIMESTAMP,
        PRIMARY KEY (trace_id, day)
    );
    CREATE INDEX idx_trace_lookup ON traces(day, trace_id DESC);

    CREATE TABLE feedback (
        trace_id        TEXT,
        rating          TEXT,
        corrected_answer TEXT,
        is_gold         INTEGER DEFAULT 0,
        created_at      TIMESTAMP
    );
""")
print("Created: documents, chunks, embeddings, traces, feedback\n")

# Demo: SHA256 dedup
def insert_doc(uri, text):
    """Insert with dedup via SHA256. Returns (doc_id, was_duplicate)."""
    h = hashlib.sha256(text.encode()).hexdigest()
    # Try insert; on UNIQUE conflict, return existing
    try:
        doc_id = f"doc_{h[:12]}"
        conn.execute(
            "INSERT INTO documents (doc_id, hash_sha256, uri) VALUES (?, ?, ?)",
            (doc_id, h, uri)
        )
        conn.commit()
        return doc_id, False
    except sqlite3.IntegrityError:
        return f"doc_{h[:12]}", True

print("=" * 60)
print("DEMO: SHA256 dedup saves 30% on re-ingest")
print("=" * 60)
N = 1000
seen_texts = [f"text {i}" for i in range(N // 2)]  # only 500 unique
duplicates = 0
new_docs = 0
t0 = time.perf_counter()
for i in range(N):
    text = seen_texts[i % 500]  # every other doc is a dup
    _, was_dup = insert_doc(f"s3://bucket/doc_{i}.pdf", text)
    if was_dup:
        duplicates += 1
    else:
        new_docs += 1
elapsed = time.perf_counter() - t0
print(f"  Inserted {N:,} docs in {elapsed:.2f}s")
print(f"  New:      {new_docs}")
print(f"  Deduped:  {duplicates} ({100*duplicates/N:.0f}%)")
print(f"  Storage saved: ~{duplicates * 50}KB (assume 50KB/doc avg)")

# Demo: partition by day for TTL
print("\n" + "=" * 60)
print("DEMO: traces partitioned by day for 30-day TTL")
print("=" * 60)
print("""
In prod (PostgreSQL/MyRocks):

  CREATE TABLE traces (
      trace_id TEXT, day DATE, ...
  ) PARTITION BY RANGE (day);

  -- Auto-create daily partitions:
  CREATE TABLE traces_2026_10_15 PARTITION OF traces
      FOR VALUES FROM ('2026-10-15') TO ('2026-10-16');

  -- 30-day TTL: drop the old partition (instant, no row scan)
  DROP TABLE traces_2026_09_15;

Compare to DELETE WHERE day < '2026-09-15' which does a full scan,
holds row locks, generates WAL traffic, and bloats vacuum.
""")

# GDPR purge demo
print("=" * 60)
print("DEMO: GDPR is_deleted + async purge")
print("=" * 60)
# Mark a doc as deleted
conn.execute("UPDATE documents SET is_deleted = 1 WHERE doc_id = 'doc_' || substr(?, 1, 12)",
             (hashlib.sha256(b"text 0").hexdigest(),))
conn.commit()
print("  Marked doc as is_deleted=1")
print("  Async purge job (daily) will:")
print("    1. Hard-delete from documents WHERE is_deleted=1 AND deleted_at < NOW()-30d")
print("    2. Cascade to chunks, embeddings")
print("    3. Remove from Qdrant shards")
print("    4. Purge from Memcache")
print("    5. Kafka tombstone event for downstream consumers")

print("\n" + "=" * 60)
print("L6 KEY POINT: hash dedup + partition TTL + GDPR = the 3 unglamorous")
print("decisions that make a 100M-doc system shippable.")
print("=" * 60)
