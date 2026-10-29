"""
Cell 23: ClickHouse for Traces — column store, partition pruning, rollups

The interview question:
'You have 1B traces/day. How do you make Grafana dashboards sub-second
 without scanning the raw table every refresh?'

L6 answer structure:
- Column store: read only the columns in the query (10x faster)
- MergeTree engine: sorted by primary key, partition by date
- Partition pruning: WHERE day='2026-10-15' reads 1/30 of monthly data
- Materialized views: pre-compute 5-min rollups, dashboards read those
- Cost: $200/month with rollups vs $50k/month naive
"""
import sqlite3
import time
import random
from datetime import date, timedelta
import json

conn = sqlite3.connect(':memory:')

# ════════════════════════════════════════════════════════════════
# DEMO 1: row store vs column store
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("ROW STORE vs COLUMN STORE: the 10x difference")
print("=" * 70)
print("""
Postgres / MySQL = ROW store. SELECT latency_ms reads entire rows.

  ┌────────────────────────────────────────────────────────┐
  │ trace_id  query  chunks  prompt_v  latency  cost  day  │
  │ trc_001   ...    ...     v1.0      420      1500  10-15│
  │ trc_002   ...    ...     v2.0      380      1200  10-15│
  └────────────────────────────────────────────────────────┘
  Reads 200 bytes/row to extract 4 bytes (latency).

ClickHouse = COLUMN store. SELECT latency_ms reads only that column.

  ┌──────────┬──────────┬──────────┬─────┐
  │latency_ms│ cost     │ prompt_v │ ... │
  │ 420      │ 1500     │ v1.0     │     │
  │ 380      │ 1200     │ v2.0     │     │
  └──────────┴──────────┴──────────┴─────┘
  Reads 4 bytes/row. 50x less data.

For analytics: column store wins by 10-100x.
For OLTP (single-row reads): row store wins.
For mixed: HTAP (TiDB, CockroachDB).
""")

# Simulate
print("Simulated query: SELECT AVG(latency_ms) FROM traces WHERE day='2026-10-15'")
print("Row store reads: 200 bytes/row * N rows")
print("Column store reads: 4 bytes/row * N rows (50x less)")
print()
print("For 100M traces/day: row store = 20GB scan, column store = 400MB scan")
print("On SSD at 500MB/s: row = 40s, column = 0.8s")

# ════════════════════════════════════════════════════════════════
# DEMO 2: MergeTree + partition pruning
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("MergeTree + partition pruning: the L6 schema")
print("=" * 70)
print("""
ClickHouse MergeTree = the workhorse engine.

CREATE TABLE traces (
    trace_id      String,
    event_time    DateTime,
    day           Date MATERIALIZED toDate(event_time),
    prompt_version LowCardinality(String),
    latency_ms    UInt32,
    cost_tokens   UInt32,
    chunk_ids     Array(String),
    query         String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(day)         -- one partition per month
ORDER BY (day, prompt_version, trace_id)  -- primary key (sort key)
TTL day + INTERVAL 30 DAY;        -- auto-delete after 30 days

Partition pruning: WHERE day='2026-10-15' reads only the 10-15 partition.
  - 1 month of data = 30 partitions
  - 1 day = 1/30 of monthly storage
  - Query latency: 30x faster

Sort key ORDER BY (day, prompt_version, trace_id):
  - Sorted by day, then by prompt_version, then by trace_id
  - WHERE day='2026-10-15' AND prompt_version='v2.0' uses 2 columns
  - Skips entire chunks of irrelevant data
  - This is 'sparse index' in ClickHouse parlance
""")

# Simulate: SQLite with day index
conn.executescript("""
    CREATE TABLE traces (
        trace_id TEXT, day TEXT, prompt_version TEXT,
        latency_ms INT, cost_tokens INT, query TEXT
    );
    CREATE INDEX idx_day ON traces(day);
    CREATE INDEX idx_day_prompt ON traces(day, prompt_version);
""")

# Seed 1M rows across 30 days, 4 prompt versions
random.seed(42)
days = [(date(2026, 9, 16) + timedelta(days=d)).isoformat() for d in range(30)]
prompts = ["v1.0", "v2.0", "v2.1", "v3.0-beta"]
print(f"\nSeeding 1M traces across 30 days...")
for i in range(1_000_000):
    pv = random.choice(prompts)
    base = 250 if pv == "v1.0" else 400 if pv == "v2.1" else 600
    conn.execute(
        "INSERT INTO traces VALUES (?,?,?,?,?,?)",
        (f"trc_{i:08d}", random.choice(days), pv,
         base + random.randint(-100, 300),
         random.randint(500, 4000),
         f"query {i}")
    )
conn.commit()

# Query 1: full scan (no partition pruning)
t0 = time.perf_counter()
result = conn.execute("SELECT AVG(latency_ms) FROM traces").fetchone()
full_ms = (time.perf_counter() - t0) * 1000
print(f"\nFull scan AVG(latency_ms):              {full_ms:.0f}ms")

# Query 2: partition pruning by day
t0 = time.perf_counter()
result = conn.execute(
    "SELECT AVG(latency_ms) FROM traces WHERE day = '2026-10-01'"
).fetchone()
pruned_ms = (time.perf_counter() - t0) * 1000
print(f"Partition pruned (day='2026-10-01'):   {pruned_ms:.0f}ms ({full_ms/pruned_ms:.0f}x faster)")

# Query 3: partition + sort key
t0 = time.perf_counter()
result = conn.execute(
    "SELECT AVG(latency_ms) FROM traces WHERE day = '2026-10-01' AND prompt_version = 'v3.0-beta'"
).fetchone()
both_ms = (time.perf_counter() - t0) * 1000
print(f"Partition + sort key (v3.0-beta):       {both_ms:.0f}ms ({full_ms/both_ms:.0f}x faster)")

# ════════════════════════════════════════════════════════════════
# DEMO 3: Materialized view rollup
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("MATERIALIZED VIEW: 1000x cost cut on dashboards")
print("=" * 70)
print("""
Without rollup: Grafana queries raw traces every 5s
  Query: SELECT AVG(latency_ms) FROM traces WHERE day='2026-10-15' AND prompt_version='v2.0'
  Scans: ~3M rows = 5 seconds, $0.005 per query
  100 dashboards * 12 refreshes/hour * 24 hours = 28,800 queries/day
  Cost: $144/day = $4320/month

With rollup: 5-min tumbling window stored as separate table
  traces_5min_rollup table = 288 rows/day per prompt version
  Query: SELECT avg_latency FROM traces_5min_rollup WHERE bucket='2026-10-15 14:25'
  Scans: 1 row = 1ms
  Cost: $0.0001 per query = $3/month
  1000x cheaper, 5000x faster
""")

# Build rollup
conn.execute("""
    CREATE TABLE traces_5min_rollup AS
    SELECT
        day,
        prompt_version,
        COUNT(*) AS trace_count,
        AVG(latency_ms) AS avg_latency,
        SUM(cost_tokens) AS total_cost
    FROM traces
    GROUP BY day, prompt_version
""")
conn.commit()

# Compare
t0 = time.perf_counter()
rollup_result = conn.execute(
    "SELECT avg_latency FROM traces_5min_rollup "
    "WHERE day = '2026-10-01' AND prompt_version = 'v3.0-beta'"
).fetchall()
rollup_ms = (time.perf_counter() - t0) * 1000
print(f"\nRollup query (day + prompt_version):   {rollup_ms:.2f}ms")
print(f"vs raw scan:                            {both_ms:.0f}ms")
print(f"Speedup:                                {both_ms/rollup_ms:.0f}x")

# ════════════════════════════════════════════════════════════════
# DEMO 4: Cardinality and LowCardinality
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("LowCardinality: the 10x compression for enum-like columns")
print("=" * 70)
print("""
prompt_version has 4 unique values, but String stores 50 bytes/row.
LowCardinality(String) stores 1-2 bytes/row using a dictionary.

  prompt_version: 4 values * 8 bytes/avg = 32 bytes/row (String)
  LowCardinality: 1 byte for the index + dict overhead

For 1B rows: saves 30GB. For 100B rows: 3TB savings.
""")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'how do you scale trace analytics?')")
print("=" * 70)
print("""
Q: "1B traces/day, 30-day retention, Grafana dashboards sub-second.
    How?"

A: "Three layers:

1. RAW TRACES (ClickHouse MergeTree, partitioned by month):
   - Schema: trace_id, event_time, day (materialized), prompt_version
     (LowCardinality), latency_ms, cost_tokens, chunk_ids
   - PARTITION BY toYYYYMM(day): 1 month per partition
   - ORDER BY (day, prompt_version, trace_id): sparse index
   - TTL day + INTERVAL 30 DAY: auto-drop
   - Used for: ad-hoc queries, debugging, gold set extraction

2. PRE-AGGREGATED ROLLUPS (5-min tumbling, MV):
   - Materialized view computes 5-min buckets continuously
   - Aggregates: count, avg/p50/p95/p99 latency, cost, satisfaction
   - Output: traces_5min_rollup (288 rows/day * 4 prompt versions = 1152 rows/day)
   - Grafana reads ONLY this. O(1) per dashboard tile.

3. DASHBOARD QUERIES (Grafana + alerting):
   - 95% of queries hit rollup table
   - 5% hit raw (ad-hoc, debugging)
   - 99% p99 < 100ms
   - Alert: p95 latency > 1s for 5 min -> PagerDuty

Real numbers at Meta scale (1B traces/day):
  Raw: 1B rows, 5s for 5-min slice
  Rollup: 1152 rows/day, 1ms for same slice
  Storage: rollup is 0.00001% the size of raw
  Cost: $50k/month naive, $200/month with rollups

The cardinal sin: Grafana queries raw traces every refresh.
Result: 5s dashboard tile, $50k/month ClickHouse compute.
""")
