"""
Cell 26: Cost-Based Query Optimizer — when to scan, when to seek

The interview question:
'Query takes 30s. Walk me through how the optimizer decides:
 full table scan vs index seek, hash join vs nested loop, partition pruning.'

L6 answer structure:
- Cost = I/O + CPU + Network
- Estimating rows: histograms, sampling
- Plan: table scan < index seek only when selectivity > 5-10%
- Join order: smallest driving table, build hash on larger
- The 5 knobs: statistics freshness, index choice, join order, partition pruning, parallel degree
"""
import sqlite3
import time
import random
import math
from collections import defaultdict

conn = sqlite3.connect(':memory:')

# ════════════════════════════════════════════════════════════════
# SETUP: 1M row table, with and without index
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("COST MODEL: the 3 components")
print("=" * 70)
print("""
Total cost = I/O cost + CPU cost + Network cost
  I/O:      page reads (8KB pages, ~100k rows/GB)
  CPU:      row processing (1M rows = 100ms typical)
  Network:  distributed query (10x more than local)

For 1B-row table, naive scan = 1B * 8KB = 8TB read = 30+ min
With index seek: 1 row * 8KB = 1 page = 0.1ms

The optimizer picks the lowest cost plan.
""")

conn.executescript("""
    CREATE TABLE events (
        event_id BIGINT PRIMARY KEY,
        user_id INT,
        event_type TEXT,    -- 'click' | 'view' | 'purchase' | 'signup'
        country TEXT,       -- 'US' | 'IN' | 'BR' | ...
        revenue REAL,
        event_time TIMESTAMP
    );
""")

# Build index
conn.execute("CREATE INDEX idx_user ON events(user_id)")
conn.execute("CREATE INDEX idx_country ON events(country)")
conn.execute("CREATE INDEX idx_type ON events(event_type)")
conn.execute("CREATE INDEX idx_country_type ON events(country, event_type)")

# Seed 1M rows
random.seed(42)
COUNTRIES = ['US', 'IN', 'BR', 'JP', 'DE', 'UK', 'FR']
TYPES = ['click', 'view', 'purchase', 'signup']
TYPE_WEIGHTS = [0.85, 0.10, 0.04, 0.01]  # click is most common

print("Seeding 1M events...")
t0 = time.perf_counter()
for i in range(1_000_000):
    event_type = random.choices(TYPES, weights=TYPE_WEIGHTS)[0]
    country = random.choice(COUNTRIES)
    revenue = random.uniform(0, 100) if event_type == 'purchase' else 0
    conn.execute(
        "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
        (i, random.randint(1, 100_000), event_type, country, revenue,
         f"2026-10-{random.randint(1, 30):02d}")
    )
conn.commit()
print(f"  Seeded in {time.perf_counter()-t0:.1f}s")
print(f"  Distribution: click 85%, view 10%, purchase 4%, signup 1%")
print(f"  Distribution: 7 countries roughly equal")

# ════════════════════════════════════════════════════════════════
# DECISION 1: full scan vs index seek
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DECISION 1: full scan vs index seek (the L6 trade-off)")
print("=" * 70)
print("""
Rule of thumb: index seek wins if selectivity < 5-10%
              full scan wins if selectivity > 5-10%

Selectivity = rows_returned / total_rows

  1M rows total
  - 'WHERE event_type = signup' (~10k rows = 1%)  -> INDEX
  - 'WHERE event_type = click'  (~850k = 85%)    -> SCAN
  - 'WHERE user_id = 42'        (~10 rows = 0.001%) -> INDEX (very selective)
  - 'WHERE revenue > 50'        (~50k = 5%)        -> INDEX
""")

# Demo: index seek (cheap)
t0 = time.perf_counter()
n_signup = conn.execute("SELECT COUNT(*) FROM events WHERE event_type = 'signup'").fetchone()[0]
index_ms = (time.perf_counter() - t0) * 1000
print(f"  event_type='signup' (1% selective): {n_signup:,} rows in {index_ms:.1f}ms")
print(f"    -> Index seek on idx_type")

t0 = time.perf_counter()
n_click = conn.execute("SELECT COUNT(*) FROM events WHERE event_type = 'click'").fetchone()[0]
index2_ms = (time.perf_counter() - t0) * 1000
print(f"  event_type='click' (85% selective): {n_click:,} rows in {index2_ms:.1f}ms")
print(f"    -> Index seek scans 85% of index, slower than full scan")
print(f"    -> Optimizer SHOULD pick full scan, but SQLite is dumb")

# Force index vs scan
t0 = time.perf_counter()
conn.execute("SELECT COUNT(*) FROM events WHERE event_type = 'click' AND 1=1").fetchall()  # full scan via WHERE
n_scan = (time.perf_counter() - t0) * 1000
print(f"    Forcing full scan: {n_scan:.1f}ms (slight speedup)")

# ════════════════════════════════════════════════════════════════
# DECISION 2: composite index column order
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DECISION 2: composite index column order")
print("=" * 70)
print("""
Index (country, event_type):
  - WHERE country = 'US'             -> USES (country is leading)
  - WHERE event_type = 'click'       -> DOES NOT USE (event_type is not leading)
  - WHERE country = 'US' AND event_type = 'click' -> USES BOTH

Index (event_type, country):
  - WHERE event_type = 'click'       -> USES
  - WHERE country = 'US'             -> DOES NOT USE
  - WHERE event_type = 'click' AND country = 'US' -> USES BOTH

Rule: put the MOST SELECTIVE column FIRST.
""")

# Demo
t0 = time.perf_counter()
r = conn.execute("SELECT COUNT(*) FROM events WHERE country = 'US' AND event_type = 'click'").fetchall()
composite_ms = (time.perf_counter() - t0) * 1000
print(f"  Composite (country, event_type): {composite_ms:.1f}ms")

t0 = time.perf_counter()
r = conn.execute("SELECT COUNT(*) FROM events WHERE event_type = 'click' AND country = 'US'").fetchall()
reverse_ms = (time.perf_counter() - t0) * 1000
print(f"  Reverse (event_type, country):  {reverse_ms:.1f}ms")
print(f"  Same query, same plan, similar latency (SQLite is simple)")

# ════════════════════════════════════════════════════════════════
# DECISION 3: join order
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DECISION 3: join order matters")
print("=" * 70)
print("""
JOIN users (100k) events (1M) purchases (40k):

  Bad:  events JOIN users JOIN purchases
        -> 1M * 100k = 100B hash operations

  Good: purchases JOIN events JOIN users
        -> 40k * 1M = 40B operations, then 40k * 100k = 4B
        -> 100x faster

Rule: drive from the SMALLEST table that filters the most.
""")

# ════════════════════════════════════════════════════════════════
# DECISION 4: partition pruning
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DECISION 4: partition pruning")
print("=" * 70)
print("""
Table partitioned by month (ClickHouse MergeTree, Postgres declarative):

  events_2026_09, events_2026_10, ...

Query: WHERE event_time >= '2026-10-01' AND event_time < '2026-11-01'
  -> Skips 11 other monthly partitions
  -> 12x faster on 1 year of data

Rule: WHERE clause must include partition key, not just sort key.
""")

# ════════════════════════════════════════════════════════════════
# DECISION 5: statistics freshness (the L6 pitfall)
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DECISION 5: STATISTICS FRESHNESS (the L6 pitfall)")
print("=" * 70)
print("""
The optimizer uses TABLE STATISTICS to estimate cost:
  - Row count: 'events has 1M rows'
  - Distinct values: 'country has 7 values'
  - Histogram: 'event_type: 85% click, 10% view, 4% purchase, 1% signup'

If statistics are STALE (e.g., last ANALYZE 30 days ago, but you've
inserted 50% more rows), the optimizer picks the WRONG plan.

  Stale stats: optimizer thinks 1M rows, picks index seek
  Reality: 1.5M rows, full scan is faster
  Result: query is 5x slower than it should be

Rule: ANALYZE after every 10% row growth.
       Or: auto-analyze (Postgres default).
       Or: nightly job that re-analyzes hot tables.
""")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'why is my query slow?')")
print("=" * 70)
print("""
Q: "Query takes 30s. How do you debug it?"

A: "5-step diagnostic, in order:

1. EXPLAIN ANALYZE the query. See the chosen plan.
   - Is it scanning when it should seek? -> add index
   - Is it using the wrong index? -> composite index column order
   - Is the join order wrong? -> optimizer hint or restructure query

2. CHECK STATISTICS. ANALYZE the table.
   - Stale stats = wrong plan = slow query
   - Re-run after 10% row growth

3. CHECK SELECTIVITY.
   - WHERE col = 'value' returning 80%+ rows -> full scan is correct
   - WHERE col = 'value' returning 0.01% rows -> index seek is correct
   - Mismatch is the most common bug

4. CHECK PARTITION PRUNING.
   - WHERE clause includes partition key? -> prune
   - WHERE clause has function on partition key? -> DON'T prune
     (e.g., WHERE YEAR(event_time) = 2026 -> no prune,
             WHERE event_time >= '2026-01-01' -> prune)

5. CHECK PARALLEL DEGREE.
   - ClickHouse / Spark: parallel by default
   - Postgres: max_parallel_workers_per_gather (default 2)
   - For 1B rows: increase to 8-16

The 5 knobs to tune, in priority order:
  1. Statistics freshness (most common bug)
  2. Index choice (composite column order)
  3. Join order (drive from smallest filter)
  4. Partition pruning (include partition key in WHERE)
  5. Parallel degree (for very large tables)

The cardinal sin: 'just add an index'. Most slow queries are
caused by stale stats, wrong column order, or functions on
the partition key. The index is the LAST fix, not the first.
""")
