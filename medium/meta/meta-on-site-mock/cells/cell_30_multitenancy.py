"""
Cell 30: Multi-Tenancy Isolation Patterns — per-tenant DB, schema, RLS, shard

The interview question:
'B2B SaaS, 1000 enterprise tenants, each has private data. How do you
 isolate tenants in Postgres? In Qdrant? In the embedding index?
 What's the cost in query latency and ops complexity?'

L6 answer structure:
- 4 patterns: shared DB, schema-per-tenant, DB-per-tenant, row-level security
- Each has trade-offs: isolation vs cost vs ops complexity
- Vector DB: shard by tenant_id, NOT per-tenant collection (overhead)
- The L6 default: row-level security + tenant_id everywhere
- Cardinal sin: implicit cross-tenant data leak via JOIN
"""
import time
import random
import sqlite3
from collections import defaultdict

# ════════════════════════════════════════════════════════════════
# THE 4 PATTERNS for Postgres (the L6 trade-off table)
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("THE 4 ISOLATION PATTERNS (the L6 trade-off table)")
print("=" * 70)
print("""
┌──────────────────┬──────────┬──────────┬──────────┬─────────────────┐
│ Pattern          │ Isolation│ Cost/mo  │ Ops      │ Use when        │
├──────────────────┼──────────┼──────────┼──────────┼─────────────────┤
│ Shared DB + RLS  │ Low      │ $        │ Simple   │ < 100 tenants   │
│ Schema-per-tenant│ Medium   │ $$       │ Medium   │ 100-1k tenants  │
│ DB-per-tenant    │ High     │ $$$$     │ Hard     │ > 1k OR strict  │
│ Pool per region  │ Varies   │ $$$      │ Medium   │ data residency  │
└──────────────────┴──────────┴──────────┴──────────┴─────────────────┘

RLS = Row-Level Security (Postgres policy: USING tenant_id = current_setting('app.tenant_id'))
""")

# ════════════════════════════════════════════════════════════════
# SIMULATION: 1000 tenants, 1M rows, query latency comparison
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("SIMULATION: 1000 tenants, 1M rows, query latency")
print("=" * 70)

random.seed(42)
N_TENANTS = 1000
N_ROWS = 1_000_000
ROWS_PER_TENANT = N_ROWS // N_TENANTS

# Pattern 1: Shared DB with RLS (simulated via WHERE clause)
print("\n--- Pattern 1: Shared DB + tenant_id filter ---")
conn_shared = sqlite3.connect(':memory:')
conn_shared.executescript("""
    CREATE TABLE documents (
        doc_id INTEGER PRIMARY KEY,
        tenant_id INTEGER,
        text TEXT,
        is_deleted INTEGER DEFAULT 0
    );
    CREATE INDEX idx_tenant ON documents(tenant_id);
""")
# Seed
t0 = time.perf_counter()
batch = []
for i in range(N_ROWS):
    tenant_id = i % N_TENANTS
    batch.append((i, tenant_id, f"text_{i}", 0))
    if len(batch) >= 10_000:
        conn_shared.executemany("INSERT INTO documents VALUES (?, ?, ?, ?)", batch)
        batch = []
if batch:
    conn_shared.executemany("INSERT INTO documents VALUES (?, ?, ?, ?)", batch)
conn_shared.commit()
seed_time = time.perf_counter() - t0
print(f"  Seeded {N_ROWS:,} rows in {seed_time:.1f}s")

# Query: tenant 42, top 5 docs
t0 = time.perf_counter()
for _ in range(100):
    rows = conn_shared.execute(
        "SELECT doc_id, text FROM documents WHERE tenant_id = ? AND is_deleted = 0 LIMIT 5",
        (42,)
    ).fetchall()
rls_time = (time.perf_counter() - t0) / 100 * 1000
print(f"  Query latency: {rls_time:.2f}ms (avg of 100)")
print(f"  Index used: idx_tenant (cheap, shared)")
print(f"  Tenant isolation: WHERE tenant_id = current_setting('app.tenant')")

# Cross-tenant leak check (the cardinal sin)
print("\n  Cross-tenant leak check:")
tenant_42_count = conn_shared.execute(
    "SELECT COUNT(*) FROM documents WHERE tenant_id = 42"
).fetchone()[0]
all_count = conn_shared.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
print(f"    Tenant 42 sees: {tenant_42_count} rows (should only see their own)")
print(f"    Total in table: {all_count} rows")
print(f"    => RLS MUST be enforced in the application layer (or Postgres policy)")

# Pattern 2: Schema-per-tenant
print("\n--- Pattern 2: Schema-per-tenant (separate SQLite per tenant) ---")
print("  Simulated: 10 tenants, 10k rows each, separate DBs")
TENANT_DBS = {}
for tid in range(10):
    conn_t = sqlite3.connect(f':memory:')
    conn_t.execute("""
        CREATE TABLE documents (
            doc_id INTEGER PRIMARY KEY,
            text TEXT,
            is_deleted INTEGER DEFAULT 0
        )
    """)
    # Each tenant has 1000 rows
    conn_t.executemany(
        "INSERT INTO documents VALUES (?, ?, 0)",
        [(i, f"text_{i}") for i in range(1000)]
    )
    conn_t.commit()
    TENANT_DBS[tid] = conn_t

# Query tenant 5
t0 = time.perf_counter()
for _ in range(100):
    rows = TENANT_DBS[5].execute(
        "SELECT doc_id, text FROM documents WHERE is_deleted = 0 LIMIT 5"
    ).fetchall()
schema_time = (time.perf_counter() - t0) / 100 * 1000
print(f"  Query latency: {schema_time:.2f}ms (avg of 100)")
print(f"  No tenant_id needed: physically isolated")
print(f"  Ops: 1000 tenants = 1000 connections per app server")

# Pattern 3: DB-per-tenant
print("\n--- Pattern 3: DB-per-tenant (separate Postgres instance) ---")
print(f"  1000 tenants x 1 Postgres = 1000 instances")
print(f"  Cost: $50/instance/mo (small) = $50k/mo")
print(f"  Cost: $500/instance/mo (HA replica) = $500k/mo")
print(f"  Ops: 1000 migrations, 1000 backups, 1000 monitoring alerts")

# ════════════════════════════════════════════════════════════════
# VECTOR DB SHARDING (the L6 critical question)
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("VECTOR DB SHARDING: tenant isolation in Qdrant/Pinecone")
print("=" * 70)
print("""
THE QUESTION: 'How do you isolate tenants in the vector index?'

THE WRONG WAY: one collection per tenant
  - 1000 tenants = 1000 collections
  - Each collection = 1 HNSW index = ~50MB overhead
  - Total overhead: 50GB just for indices, not data
  - Backup/restore: 1000 collections to manage
  - Cross-tenant search: not possible (sometimes needed for admin)

THE L6 WAY: ONE collection, tenant_id in payload
  - 1 HNSW index, ~50MB total overhead
  - Each vector has payload: {tenant_id: 42, doc_id: ..., text: ...}
  - Query: filter by tenant_id before/after ANN
  - Pre-filter (Qdrant): pushes filter into HNSW traversal
  - Post-filter: get top 100, filter, take top 8

THE TRADE-OFF:
  - Pre-filter: 10-30% slower for high-selectivity tenants (most)
  - Post-filter: faster but may return < 8 results
  - L6 default: pre-filter with HNSW ef_search boost

THE COST:
  - 1000 tenants, 1M vectors each = 1B total vectors
  - One index: 1B * 4 bytes * 1536 dim = 6TB raw, 30GB HNSW
  - Per-tenant overhead: 0 (shared index)
  - Per-collection overhead: 50MB * 1000 = 50GB (10x worse)

THE MATH at Meta scale:
  - 100M tenants, 10K vectors each = 1B vectors total
  - One index: $30k/mo storage
  - Per-tenant: $3M/mo storage (impossible)
""")

# ════════════════════════════════════════════════════════════════
# THE L6 DECISION MATRIX
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("THE L6 DECISION MATRIX")
print("=" * 70)
print("""
How many tenants?     → What pattern?

< 100 tenants         → Schema-per-tenant (good isolation, ops OK)
100 - 1000            → RLS + shard by tenant_id (L6 default)
1000 - 100k           → RLS + tenant_id everywhere, NO per-tenant infra
> 100k                → Hash tenant_id to physical shard (Citus, Vitess)

WHAT ABOUT COMPLIANCE?
  - HIPAA / SOC2:    DB-per-tenant (audit trails per tenant)
  - GDPR + EU only:  Region-pinned (DB in eu-west-1)
  - Fin data:        Schema-per-tenant + encryption per schema

WHAT ABOUT THE BIGGEST 10-K?
  - Top 10 tenants = 80% of revenue
  - Special-case them: dedicated cluster, custom SLOs
  - Long tail: shared infra, RLS, accept some noise
""")

# ════════════════════════════════════════════════════════════════
# THE CROSS-TENANT LEAK (the cardinal sin)
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("THE CROSS-TENANT LEAK (the cardinal sin)")
print("=" * 70)
print("""
Bug: forgot WHERE tenant_id = ? in a JOIN.

SELECT t.name, c.text
FROM tenants t
JOIN chats c ON c.tenant_id = t.tenant_id
WHERE t.tenant_id = ?

If you forget the WHERE clause, you leak data across tenants.
Worst case: customer A sees customer B's chat history.

How the L6 prevents this:
1. Postgres RLS policy on every table (defense in depth)
2. CI test: 'delete WHERE tenant_id = X, verify COUNT = 0'
3. ORM: every query has automatic tenant_id filter
4. Audit log: every query logs tenant_id, alert on missing

Example Postgres RLS:
  ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
  CREATE POLICY tenant_isolation ON documents
    USING tenant_id = current_setting('app.current_tenant')::INT;

This GUARANTEES no query can read another tenant's data,
even if the developer forgets the WHERE clause.
""")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("L6 ANSWER (when they ask 'how do you isolate tenants?')")
print("=" * 70)
print("""
Q: "B2B SaaS, 1000 enterprise tenants, private data. How do you
    isolate tenants in Postgres, Qdrant, the embedding index?"

A: "4 patterns, each for a different scale. L6 default for 1000
   tenants: RLS + tenant_id everywhere, ONE shared index.

THE 4 PATTERNS (the trade-off table):

1. Shared DB + RLS (< 100 tenants)
   - tenant_id column on every table
   - Postgres policy: USING tenant_id = current_setting('app.tenant_id')
   - Cheap, simple, but blast radius = whole DB

2. Schema-per-tenant (100-1000 tenants)
   - 1000 schemas in 1 DB
   - Strong isolation, easy backup per tenant
   - 1000 connections per app server (pool carefully)

3. DB-per-tenant (> 1000 OR strict compliance)
   - 1000 Postgres instances
   - HIPAA, SOC2 compliance made easy
   - $50k-$500k/mo on dedicated instances
   - 1000 migrations, 1000 backups = ops nightmare

4. Shard by tenant_id (> 100k tenants)
   - hash(tenant_id) % N shards
   - Citus, Vitess, or custom routing
   - Re-shard when one shard gets too big

VECTOR DB (the critical question):
  - WRONG: one collection per tenant (1000 collections = 50GB overhead)
  - RIGHT: ONE collection, tenant_id in payload, filter in HNSW
  - Pre-filter (Qdrant): pushes tenant_id into HNSW traversal
  - Post-filter: get top 100, filter, take top 8 (fallback)

THE CARDINAL SIN: implicit cross-tenant data leak.
  - Missing WHERE tenant_id = ? in a JOIN = data leak
  - Postgres RLS = defense in depth (impossible to forget)
  - CI test: 'delete WHERE tenant_id = X, verify COUNT = 0'
  - Audit log: alert on any query with NULL tenant_id

The L6 line: 'I default to RLS + shared index, with the option to
shard by tenant_id when compliance demands it. Vector DB is always
one collection with payload filtering, never per-tenant collections.'
""")