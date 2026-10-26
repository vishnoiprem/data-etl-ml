"""
Cell 14: Zero-Downtime Schema Migration (the expand-and-contract pattern)

What this proves for the L6 interview:
- ALTER TABLE on a 1B row table takes HOURS and locks the table
- In prod, you NEVER do big ALTERs directly
- The expand-and-contract pattern lets you migrate with zero downtime:
  1. EXPAND: add new column (nullable, no default)
  2. DUAL-WRITE: app writes to BOTH old and new columns
  3. BACKFILL: async job populates new column for existing rows
  4. SWITCH: app reads from new column
  5. CONTRACT: drop old column (after 30-day bake)
"""
import sqlite3
import time
import random

conn = sqlite3.connect(':memory:')

# ─── Simulate a "production" table ────────────────────────────────
N = 100_000  # 100k rows = "small prod" in our demo
print(f"Setting up 'prod' table with {N:,} rows...")

conn.executescript("""
    CREATE TABLE chunks_v1 (
        chunk_id    TEXT PRIMARY KEY,
        text        TEXT,
        token_count INTEGER,
        embedding   BLOB,
        model_version TEXT  -- pretend this was just added by naive ALTER
    );
""")

import numpy as np
np.random.seed(42)
DIM = 64

for i in range(N):
    vec = np.random.randn(DIM).astype(np.float32)
    conn.execute(
        "INSERT INTO chunks_v1 VALUES (?, ?, ?, ?, ?)",
        (f"chk_{i:06d}", f"text of chunk {i}", int(np.random.randint(50, 500)), vec.tobytes(), None)
    )
conn.commit()
print(f"Inserted {N:,} rows with old schema (chunk_id, text, token_count, embedding)\n")

# ════════════════════════════════════════════════════════════════
# THE NAIVE WAY: ALTER TABLE (DON'T DO THIS IN PROD)
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("METHOD 1 (NEVER DO THIS): ALTER TABLE adds column with default")
print("=" * 70)
print("""
Why this is bad at Meta scale:
- ALTER TABLE on 1B row table = 30+ minutes of ACCESS EXCLUSIVE lock
- All readers and writers blocked during the rewrite
- Even adding a NULLABLE column rewrites the table in PostgreSQL < 11
- In PG 11+, adding a nullable column without default is fast (metadata only)
- Adding a column WITH a default STILL rewrites the table

Cost: 30+ min downtime on a 1B row table. NEVER acceptable in prod.
""")

# Demonstrate the slowness on a 100k table
# (already added in CREATE TABLE for demo purposes, so measure a different naive ALTER)
t0 = time.perf_counter()
conn.execute("ALTER TABLE chunks_v1 ADD COLUMN last_edited_by TEXT DEFAULT 'unknown'")
naive_ms = (time.perf_counter() - t0) * 1000
print(f"On our {N:,} row demo: ALTER took {naive_ms:.0f}ms")
print(f"Extrapolated to 1B rows: ~{naive_ms * 10000 / 1000:.0f} seconds = ~{naive_ms * 10000 / 60000:.0f} minutes\n")

# ════════════════════════════════════════════════════════════════
# METHOD 2: EXPAND-AND-CONTRACT (the prod pattern)
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("METHOD 2 (THE RIGHT WAY): Expand-and-contract")
print("=" * 70)

# STEP 1: EXPAND - add new columns, nullable, no default
print("\n[STEP 1] EXPAND: add new columns (nullable, no default)")
print("  ALTER TABLE chunks ADD COLUMN created_at TIMESTAMP;")
print("  ALTER TABLE chunks ADD COLUMN model_version TEXT;")
print("  Cost: milliseconds (metadata-only change in PG 11+)\n")

t0 = time.perf_counter()
conn.execute("ALTER TABLE chunks_v1 ADD COLUMN created_at TIMESTAMP")  # no default!
expand_ms = (time.perf_counter() - t0) * 1000
print(f"  Time on {N:,} rows: {expand_ms:.1f}ms (vs {naive_ms:.0f}ms for naive)\n")

# STEP 2: DUAL-WRITE - app writes to BOTH old and new columns
print("[STEP 2] DUAL-WRITE: app code now writes to old AND new columns")
print("  INSERT INTO chunks VALUES (..., 'ada-002', '2026-10-14');")
print("  Cost: 0ms (just app code change, deploy in 1 hour)\n")

# STEP 3: BACKFILL - async job populates new column for existing rows
print("[STEP 3] BACKFILL: async Spark job populates new column for existing rows")
print("  UPDATE chunks SET created_at = NOW() WHERE created_at IS NULL;")
print("  Run in batches of 10k to avoid long transactions\n")

t0 = time.perf_counter()
# Backfill in batches to simulate real Spark job
BATCH = 10_000
batches_done = 0
while True:
    result = conn.execute(
        f"UPDATE chunks_v1 SET created_at = '2026-10-14 00:00:00' "
        f"WHERE chunk_id IN (SELECT chunk_id FROM chunks_v1 "
        f"WHERE created_at IS NULL LIMIT {BATCH})"
    )
    if result.rowcount == 0:
        break
    batches_done += 1
conn.commit()
backfill_ms = (time.perf_counter() - t0) * 1000
print(f"  Backfilled {N:,} rows in {batches_done} batches, {backfill_ms:.0f}ms")
print(f"  Extrapolated to 1B rows: ~{backfill_ms * 10:.0f}s = {backfill_ms * 10 / 60:.0f} min (Spark would be 4x faster)\n")

# STEP 4: SWITCH reads to new column
print("[STEP 4] SWITCH READS: app code now reads from new column")
print("  SELECT ... FROM chunks WHERE created_at >= '2026-10-13';")
print("  Cost: 0ms (just app code change, deploy in 1 hour)\n")

# STEP 5: CONTRACT - drop old column (after 30-day bake)
print("[STEP 5] CONTRACT: drop old column AFTER 30-day bake")
print("  Wait 30 days to confirm no rollbacks needed")
print("  ALTER TABLE chunks DROP COLUMN last_edited_by;")
print("  Cost: 30 day bake + 1 min ALTER on the bake day\n")

# Verify the migration
nulls = conn.execute("SELECT COUNT(*) FROM chunks_v1 WHERE created_at IS NULL").fetchone()[0]
total = conn.execute("SELECT COUNT(*) FROM chunks_v1").fetchone()[0]
print(f"VERIFICATION:")
print(f"  Total rows: {total:,}")
print(f"  Rows with model_version: {total - nulls:,}")
print(f"  Rows with NULL: {nulls:,} (should be 0)\n")

# ════════════════════════════════════════════════════════════════
# THE VECTOR DIMENSION MIGRATION (the hardest one)
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("HARD CASE: changing vector dimension (1536 -> 3072)")
print("=" * 70)
print("""
This is the worst migration - you CANNOT change a vector column type
in pgvector without a full table rewrite. Pattern:

1. Add new column: embedding_v2 float[3072]
2. Dual-write: ingest job writes to BOTH embedding and embedding_v2
3. Backfill: Spark job re-embeds all chunks with new model
4. Search: queries union both columns, dedup by chunk_id
5. Cutover: flip read flag, search only embedding_v2
6. Drop embedding (old column)

Total downtime: ZERO. Bake period: 7 days.
""")

# Demonstrate the dual-write phase
import sqlite_vec
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)

# Mock the new dimension
conn.execute("ALTER TABLE chunks_v1 ADD COLUMN embedding_v2 BLOB")
print(f"  Added embedding_v2 column to {total:,} rows (zero downtime)")

# Simulate: in prod, app now writes to both
# Backfill would re-embed all chunks with new model (the cell_08_benchmark showed this is 2.8h for 10M)
# For 1B chunks: ~280 hours = 11 days of Spark (with 8-way sharding: ~1.4 days)

total_chunks = 1_000_000_000
embed_rate = 5000  # per sec
sharded_rate = embed_rate * 8
hours = total_chunks / sharded_rate / 3600
print(f"  Backfill cost for 1B chunks: {hours:.1f} hours = {hours/24:.1f} days (8-way sharded Spark)")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'how do you change a schema in prod?')")
print("=" * 70)
print("""
Q: "How do you migrate a 1B-row table without downtime?"

A: "Expand-and-contract, every time. Five steps:

1. EXPAND (milliseconds):
   - ALTER TABLE ... ADD COLUMN x TEXT  (no default, nullable)
   - PG 11+ does this as metadata-only, no table rewrite
   - Deploy in 1 hour

2. DUAL-WRITE (0ms, just code change):
   - App code writes to BOTH old and new columns
   - Old column remains the source of truth
   - Deploy in 1 hour

3. BACKFILL (hours to days):
   - Spark job in batches of 10k rows
   - For 1B rows: ~12 hours with 8-way sharding
   - Throttle to avoid replica lag

4. SWITCH READS (0ms, just code change):
   - App code now reads from new column
   - Old column is now dead weight
   - Deploy in 1 hour

5. CONTRACT (after 30-day bake):
   - ALTER TABLE ... DROP COLUMN old_col
   - Bake period catches any rollbacks needed
   - Schedule during low-traffic window

Total downtime: ZERO. Total time: 2 weeks (most is the 30-day bake).

The cardinal sin: ALTER TABLE ... ADD COLUMN x TEXT DEFAULT 'y'
on a 1B row table. That rewrites the entire table. 30+ min of
ACCESS EXCLUSIVE lock. Every reader and writer blocked.

For vector dimension changes (1536 -> 3072), it's the same pattern
but the backfill is expensive: re-embed 1B chunks = 11 days of Spark.
Plan the bake period accordingly.
""")
