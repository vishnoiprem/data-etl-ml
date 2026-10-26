"""
Cell 25: GDPR Right-to-Erasure — tombstone + async purge

The interview question:
'A user in the EU deletes their account. How do you erase their data
 across your vector DB, traces, feedback, logs, caches — in 30 days,
 with a legal audit trail?'

L6 answer structure:
- Right-to-erasure is a 30-day SLA, not instant
- Tombstone in primary store (logical delete)
- Kafka event fans out to all secondary stores
- Async purge job hard-deletes after legal hold (30d)
- Audit trail: who requested, when, what was purged, by which job
- Idempotency: re-request is a no-op, not a re-purge
"""
import sqlite3
import time
import json
import random
import hashlib
from datetime import date, datetime, timedelta
from collections import defaultdict

conn = sqlite3.connect(':memory:')

# ════════════════════════════════════════════════════════════════
# THE 5 STORES where PII lives
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("THE 5 STORES WHERE PII LIVES (and the purge strategy)")
print("=" * 70)
print("""
Store              Volume   Strategy        Latency
1. Postgres         GBs      Logical + hard  Instant logical, 30d hard
2. Vector DB (Qdrant) 100s GB Logical + hard  Instant logical, 30d hard
3. ClickHouse (traces) TBs    Logical + hard  Instant logical, 30d hard
4. S3 (raw logs)     PBs      Lifecycle policy 30d (S3 rule)
5. Memcache          GBs      TTL-based      ~30s (cache miss = purge)

The pattern: LOGICAL DELETE everywhere, HARD DELETE in 30 days.
- Logical delete: instant, reversible (in case of legal hold reversal)
- Hard delete: required for GDPR (data must actually be erased)
- 30-day window: balance user rights vs legal hold requirements
""")

conn.executescript("""
    -- Tombstone table (the source of truth for "is this user erased?")
    CREATE TABLE user_tombstone (
        user_id     BIGINT PRIMARY KEY,
        email_hash  TEXT,        -- hash of email for dedup
        deleted_at  TIMESTAMP,
        purge_after DATE,        -- deleted_at + 30 days
        request_id  TEXT,        -- unique ID for audit trail
        source      TEXT         -- 'user_request' | 'admin_action' | 'gdpr_automation'
    );

    -- Audit trail (Legal can replay: who, what, when)
    CREATE TABLE erasure_audit (
        audit_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     BIGINT,
        request_id  TEXT,
        store       TEXT,        -- 'postgres' | 'qdrant' | 'clickhouse' | 's3' | 'memcache'
        action      TEXT,        -- 'logical_delete' | 'hard_delete' | 'cache_invalidate'
        rows_affected INT,
        performed_at TIMESTAMP,
        performed_by TEXT        -- 'purge_job_v2' | 'admin_123'
    );

    -- Simulated user tables
    CREATE TABLE users (user_id BIGINT PRIMARY KEY, email TEXT, name TEXT);
    CREATE TABLE chunks (chunk_id TEXT, user_id BIGINT, text TEXT, is_deleted INT DEFAULT 0);
    CREATE TABLE embeddings (chunk_id TEXT, vec BLOB, is_deleted INT DEFAULT 0);
    CREATE TABLE traces (trace_id TEXT, user_id BIGINT, query TEXT, is_deleted INT DEFAULT 0);
    CREATE TABLE feedback (trace_id TEXT, user_id BIGINT, rating TEXT, is_deleted INT DEFAULT 0);
""")

# Seed
random.seed(42)
for u in range(1, 101):
    conn.execute("INSERT INTO users VALUES (?, ?, ?)", (u, f"user{u}@example.com", f"User {u}"))
    # 50 chunks per user
    for c in range(50):
        cid = f"chunk_{u}_{c}"
        conn.execute("INSERT INTO chunks VALUES (?, ?, ?, 0)", (cid, u, f"text {c}"))
        conn.execute("INSERT INTO embeddings VALUES (?, ?, 0)", (cid, b"vec"))
    # 20 traces per user
    for t in range(20):
        tid = f"trace_{u}_{t}"
        conn.execute("INSERT INTO traces VALUES (?, ?, ?, 0)", (tid, u, f"query {t}"))
        conn.execute("INSERT INTO feedback VALUES (?, ?, ?, 0)", (tid, u, "thumbs_up"))
conn.commit()
total_chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
total_traces = conn.execute("SELECT COUNT(*) FROM traces").fetchone()[0]
print(f"  Seeded 100 users, {total_chunks} chunks, {total_traces} traces")

# ════════════════════════════════════════════════════════════════
# PHASE 1: User requests deletion (the 1st of 5 phases)
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 1: user requests deletion (instant)")
print("=" * 70)

def request_erasure(user_id, source='user_request'):
    """User clicks 'Delete my account'. Instant logical delete everywhere."""
    request_id = hashlib.sha256(f"{user_id}-{time.time()}".encode()).hexdigest()[:16]
    deleted_at = datetime.now().isoformat()
    purge_after = (date.today() + timedelta(days=30)).isoformat()
    email = conn.execute("SELECT email FROM users WHERE user_id=?", (user_id,)).fetchone()
    email_hash = hashlib.sha256(email[0].encode()).hexdigest() if email else None

    # 1. Insert tombstone (source of truth)
    conn.execute(
        "INSERT INTO user_tombstone VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, email_hash, deleted_at, purge_after, request_id, source)
    )

    # 2. Logical delete in primary store
    n_chunks = conn.execute(
        "UPDATE chunks SET is_deleted=1 WHERE user_id=?", (user_id,)
    ).rowcount
    n_traces = conn.execute(
        "UPDATE traces SET is_deleted=1 WHERE user_id=?", (user_id,)
    ).rowcount
    n_emb = conn.execute(
        "UPDATE embeddings SET is_deleted=1 WHERE chunk_id IN "
        "(SELECT chunk_id FROM chunks WHERE user_id=?)", (user_id,)
    ).rowcount
    n_fb = conn.execute(
        "UPDATE feedback SET is_deleted=1 WHERE user_id=?", (user_id,)
    ).rowcount

    # 3. Kafka event (async fanout)
    kafka_event = {
        "event": "user.erasure.requested",
        "user_id": user_id,
        "request_id": request_id,
        "deleted_at": deleted_at,
        "purge_after": purge_after
    }

    # 4. Audit trail
    for store, rows in [('postgres', n_chunks + n_traces + n_fb),
                         ('qdrant', n_emb)]:
        conn.execute(
            "INSERT INTO erasure_audit (user_id, request_id, store, action, rows_affected, performed_at, performed_by) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, request_id, store, 'logical_delete', rows, deleted_at, 'purge_job_v2')
        )

    conn.commit()
    return {
        "request_id": request_id,
        "kafka_event": kafka_event,
        "rows_logically_deleted": n_chunks + n_traces + n_fb + n_emb
    }

# Simulate user 42 requesting deletion
result = request_erasure(42)
print(f"  Request ID: {result['request_id']}")
print(f"  Kafka event: {json.dumps(result['kafka_event'])}")
print(f"  Logical deletes: {result['rows_logically_deleted']} rows")
print(f"  Time: <100ms (instant from user's perspective)")

# ════════════════════════════════════════════════════════════════
# PHASE 2: Reads filter tombstoned users
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 2: every read filters tombstoned users (the L6 line)")
print("=" * 70)
print("""
Every read in the system must apply this filter:

  SELECT * FROM chunks
  WHERE user_id NOT IN (SELECT user_id FROM user_tombstone)
    AND is_deleted = 0

This is a 2-line check that MUST be in:
  - Get user data endpoint
  - Search query path
  - Feedback lookup
  - Trace aggregation
  - Any query that touches user data
""")

# Demo: read with filter
def safe_get_chunks(user_id):
    """Get user's chunks, filtered for erasure."""
    return conn.execute("""
        SELECT chunk_id, text FROM chunks
        WHERE user_id = ?
          AND is_deleted = 0
          AND user_id NOT IN (SELECT user_id FROM user_tombstone)
    """, (user_id,)).fetchall()

# User 42 (erased) should see 0 chunks
# User 1 (not erased) should see 50
chunks_42 = safe_get_chunks(42)
chunks_1 = safe_get_chunks(1)
print(f"\n  safe_get_chunks(42) [erased]: {len(chunks_42)} chunks")
print(f"  safe_get_chunks(1)  [active]: {len(chunks_1)} chunks")
print(f"  => User 42 sees nothing, user 1 sees their data")

# ════════════════════════════════════════════════════════════════
# PHASE 3: Kafka event fans out to all stores
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 3: Kafka event -> all secondary stores (1-5 min)")
print("=" * 70)
print("""
Topic: user.erasure.requested

Consumers:
  1. vector_db_consumer   -> marks chunks is_deleted=1 in Qdrant
  2. cache_consumer       -> evicts user from Memcache
  3. search_index_consumer -> removes from Elasticsearch
  4. analytics_consumer   -> marks traces is_deleted=1 in ClickHouse
  5. s3_lifecycle         -> adds to lifecycle policy (30d)
  6. ml_training_consumer -> removes from training datasets

Each consumer:
  - Idempotent (re-process same request = no-op)
  - Has its own SLO (cache: 1min, vector: 5min, S3: 30d)
  - Logs to erasure_audit

Failure mode: if any consumer fails, retry until success.
              if retry exhausted, page on-call, manual cleanup.
""")

# ════════════════════════════════════════════════════════════════
# PHASE 4: Async purge after 30 days
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 4: hard delete after 30-day legal hold")
print("=" * 70)

def hard_purge_due_rows():
    """The daily purge job. Hard-deletes rows where purge_after <= today."""
    today = date.today().isoformat()
    purged = defaultdict(int)

    # Find users whose 30-day hold has expired
    due = conn.execute(
        "SELECT user_id, request_id FROM user_tombstone WHERE purge_after <= ?",
        (today,)
    ).fetchall()

    for user_id, request_id in due:
        # Hard delete in primary store
        for table in ['chunks', 'traces', 'feedback']:
            n = conn.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,)).rowcount
            purged[table] += n
        n = conn.execute(
            "DELETE FROM embeddings WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks)"
        ).rowcount
        purged['embeddings'] += n
        # Hard delete user record
        purged['users'] += conn.execute("DELETE FROM users WHERE user_id=?", (user_id,)).rowcount
        # Remove tombstone itself
        conn.execute("DELETE FROM user_tombstone WHERE user_id=?", (user_id,))
        # Audit
        for store, rows in purged.items():
            conn.execute(
                "INSERT INTO erasure_audit (user_id, request_id, store, action, rows_affected, performed_at, performed_by) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, request_id, store, 'hard_delete', rows, datetime.now().isoformat(), 'purge_job_v2')
            )
    conn.commit()
    return dict(purged)

# Fast-forward: simulate 30 days later by setting purge_after to past
conn.execute(
    "UPDATE user_tombstone SET purge_after = ? WHERE user_id = 42",
    ("2020-01-01",)  # way in the past
)
conn.commit()
print("  Simulating 'today is 2026-11-15' (30 days after erasure)...")
purged = hard_purge_due_rows()
print(f"  Hard-deleted: {purged}")

# Verify user 42 is GONE
gone = conn.execute("SELECT COUNT(*) FROM users WHERE user_id=42").fetchone()[0]
chunks_left = conn.execute("SELECT COUNT(*) FROM chunks WHERE user_id=42").fetchone()[0]
print(f"\n  Verification: user 42 in users table: {gone} (should be 0)")
print(f"  Verification: chunks for user 42:    {chunks_left} (should be 0)")

# ════════════════════════════════════════════════════════════════
# PHASE 5: Audit trail for Legal
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 5: audit trail (Legal can replay)")
print("=" * 70)
print("""
For every erasure request, the audit trail records:
  - who requested (user_id, request_id, source)
  - when (deleted_at, purge_after)
  - what was done (per-store rows_affected)
  - who did it (purge_job_v2, or admin_123)
  - when it was done (performed_at)

Legal can answer:
  Q: "Was user 42's data erased?"
  A: SELECT * FROM erasure_audit WHERE user_id=42
     (returns: logical_delete at T0, hard_delete at T0+30d, by purge_job_v2)

The audit table is APPEND-ONLY. Never deleted. Retained for 7 years
(legal requirement varies by jurisdiction).
""")
print("\nAudit trail for user 42:")
for row in conn.execute(
    "SELECT store, action, rows_affected, performed_at FROM erasure_audit WHERE user_id=42"
).fetchall():
    print(f"  {row[0]:<12} {row[1]:<18} {row[2]:>3} rows  {row[3]}")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'how do you handle GDPR deletion?')")
print("=" * 70)
print("""
Q: "User in EU clicks 'Delete my account'. How do you erase their data
    across vector DB, traces, logs, caches in 30 days?"

A: "5 phases, all idempotent:

PHASE 1: USER REQUEST -> TOMBSTONE (instant, <100ms)
  - INSERT INTO user_tombstone (user_id, request_id, deleted_at, purge_after)
  - Kafka event user.erasure.requested
  - Logical delete in primary store (is_deleted=1)
  - Audit log row

PHASE 2: EVERY READ FILTERS TOMBSTONE (the L6 line)
  - WHERE user_id NOT IN (SELECT user_id FROM user_tombstone) AND is_deleted=0
  - In EVERY query path: search, feedback, trace aggregation
  - User 42's data is invisible from request time

PHASE 3: KAFKA FANOUT (1-5 min)
  - 6 consumers: vector DB, cache, search index, analytics, S3 lifecycle, ML
  - Each marks its store is_deleted=1 or evicts cache
  - Each writes to erasure_audit
  - Idempotent: re-process = no-op

PHASE 4: ASYNC HARD PURGE (T+30 days)
  - Daily job: hard delete WHERE purge_after <= today
  - Cascades to embeddings, traces, feedback
  - Removes from ML training datasets

PHASE 5: AUDIT TRAIL (7-year retention)
  - Append-only erasure_audit table
  - Legal can replay: who, what, when, by which job
  - 30-day SLA met, 7-year proof for compliance audits

The cardinal sin: hard delete instantly with no tombstone.
  - No rollback (Legal might reverse)
  - No audit trail (compliance violation)
  - No propagation (other stores still have the data)
  - Crashes if any store is offline

The L6 pattern: logical delete first, hard delete in 30 days,
audit every step. Idempotent, auditable, reversible within 30 days.
""")
