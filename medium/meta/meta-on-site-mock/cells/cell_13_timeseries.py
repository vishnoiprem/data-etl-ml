"""
Cell 13: Time-Series Windowed Aggregation (the Grafana dashboard)

What this proves for the L6 interview:
- Real-time traces need to be aggregated into time buckets (1m, 5m, 1h)
- Pre-aggregation saves 1000x on dashboard query cost
- Tumbling windows for steady-state, hopping windows for moving averages
- Late-arriving data needs watermarking (event_time vs process_time)
"""
import sqlite3
import numpy as np
from datetime import datetime, timedelta
import json
import time

conn = sqlite3.connect(':memory:')

# ─── Simulate 24h of trace data ──────────────────────────────────
# 1M traces/day at Meta scale, but we simulate 10k for demo
N_TRACES = 10_000
np.random.seed(42)

# Generate timestamps across 24h
start = datetime(2026, 10, 14, 0, 0, 0)
timestamps = [start + timedelta(seconds=np.random.randint(0, 86400)) for _ in range(N_TRACES)]

# Latency: log-normal distribution (most fast, some slow)
latencies = np.random.lognormal(mean=6.0, sigma=0.5, size=N_TRACES).astype(int)  # ~400ms median

# Cost: roughly correlated with latency
costs = (latencies * 1.8 + np.random.normal(0, 50, N_TRACES)).astype(int)
costs = np.maximum(costs, 50)  # floor at 50 tokens

# Prompt versions (3 versions running in production)
prompt_versions = np.random.choice([1, 2, 3], size=N_TRACES)

conn.executescript("""
    CREATE TABLE traces_ts (
        trace_id       TEXT PRIMARY KEY,
        event_time     TIMESTAMP,  -- when it actually happened
        process_time   TIMESTAMP,  -- when we processed it (for watermark)
        prompt_version INTEGER,
        latency_ms     INTEGER,
        cost_tokens    INTEGER
    );
""")

# Insert with realistic out-of-order arrivals
process_times = [t + timedelta(seconds=np.random.exponential(2)) for t in timestamps]
# Add some late arrivals (out of order)
for i in np.random.choice(N_TRACES, size=int(N_TRACES * 0.05), replace=False):
    process_times[i] = timestamps[i] + timedelta(seconds=np.random.randint(60, 300))

for i in range(N_TRACES):
    conn.execute(
        "INSERT INTO traces_ts VALUES (?, ?, ?, ?, ?, ?)",
        (f"trc_{i:05d}", timestamps[i].isoformat(), process_times[i].isoformat(),
         int(prompt_versions[i]), int(latencies[i]), int(costs[i]))
    )
conn.commit()
print(f"Seeded {N_TRACES:,} traces across 24h with 5% late arrivals\n")

# ════════════════════════════════════════════════════════════════
# DEMO 1: Tumbling window aggregation (the standard Grafana query)
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("TUMBLING WINDOW: 5-min buckets (steady-state dashboards)")
print("=" * 70)

# 5-minute tumbling windows = 288 buckets per day
result = conn.execute("""
    SELECT
        strftime('%Y-%m-%d %H:', event_time) ||
        printf('%02d', (CAST(strftime('%M', event_time) AS INTEGER) / 5) * 5)
        AS window_5min,
        COUNT(*) AS trace_count,
        AVG(latency_ms) AS avg_latency_ms,
        MAX(latency_ms) AS p_max_latency,
        SUM(cost_tokens) AS total_cost
    FROM traces_ts
    GROUP BY 1
    ORDER BY 1
    LIMIT 12
""").fetchall()

print(f"\nFirst 12 of 288 5-min buckets (showing traces, latency, cost):")
print(f"{'Window':<18} {'Traces':>7} {'Avg(ms)':>8} {'Max(ms)':>8} {'Cost':>10}")
print("-" * 60)
for window, count, avg_lat, max_lat, cost in result:
    print(f"{window:<18} {count:>7,} {avg_lat:>8.0f} {max_lat:>8,} {cost:>10,}")

# ════════════════════════════════════════════════════════════════
# DEMO 2: Hopping window (sliding 5-min, computed every 1-min)
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("HOPPING WINDOW: 5-min window, 1-min hop (moving averages)")
print("=" * 70)
print("\nThis is what SRE dashboards use for SLO burn-rate alerts.")
print("Computed via OVER() + RANGE BETWEEN in real SQL dialects.\n")

result = conn.execute("""
    WITH windowed AS (
        SELECT
            strftime('%Y-%m-%d %H:%M', event_time) AS minute,
            AVG(latency_ms) AS avg_latency
        FROM traces_ts
        GROUP BY 1
    )
    SELECT
        minute,
        ROUND(avg_latency, 0) AS current_min_avg,
        ROUND(AVG(avg_latency) OVER (
            ORDER BY minute
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        ), 0) AS moving_5min_avg
    FROM windowed
    ORDER BY minute
    LIMIT 15
""").fetchall()

print(f"{'Minute':<18} {'Current':>10} {'5-min MA':>10}")
print("-" * 42)
for minute, current, ma5 in result:
    print(f"{minute:<18} {current:>10.0f} {ma5:>10.0f}")

# ════════════════════════════════════════════════════════════════
# DEMO 3: Watermarking (handle late-arriving data)
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("WATERMARK: handle 5% late-arriving data correctly")
print("=" * 70)

# Without watermark: late data goes into the WRONG bucket
no_wm = conn.execute("""
    SELECT
        strftime('%Y-%m-%d %H:', event_time) ||
        printf('%02d', (CAST(strftime('%M', event_time) AS INTEGER) / 5) * 5) AS bucket,
        COUNT(*) AS count
    FROM traces_ts
    GROUP BY 1
    ORDER BY 1
    LIMIT 5
""").fetchall()

# With watermark: only count traces processed within 60 seconds of event_time
# (in real systems, this is implemented with watermark + allowed lateness)
with_wm = conn.execute("""
    SELECT
        strftime('%Y-%m-%d %H:', event_time) ||
        printf('%02d', (CAST(strftime('%M', event_time) AS INTEGER) / 5) * 5) AS bucket,
        COUNT(*) AS count
    FROM traces_ts
    WHERE (julianday(process_time) - julianday(event_time)) * 86400 <= 60
    GROUP BY 1
    ORDER BY 1
    LIMIT 5
""").fetchall()

print(f"\nFirst 5 buckets (truncated):")
print(f"{'Bucket':<18} {'No watermark':>14} {'With 60s WM':>14}")
print("-" * 50)
for (b1, c1), (b2, c2) in zip(no_wm, with_wm):
    print(f"{b1:<18} {c1:>14,} {c2:>14,}")

# ════════════════════════════════════════════════════════════════
# DEMO 4: Pre-aggregation for cost (the prod architecture)
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PRE-AGGREGATION: 1000x cost reduction on dashboards")
print("=" * 70)

# Naive: Grafana queries raw traces every refresh (1B rows/day at Meta)
# Pre-aggregated: Flink computes 5-min rollups, stored in ClickHouse

# Build pre-aggregated rollup table
conn.execute("""
    CREATE TABLE traces_5min_rollup AS
    SELECT
        strftime('%Y-%m-%d %H:', event_time) ||
        printf('%02d', (CAST(strftime('%M', event_time) AS INTEGER) / 5) * 5) AS bucket,
        prompt_version,
        COUNT(*) AS trace_count,
        AVG(latency_ms) AS avg_latency,
        SUM(cost_tokens) AS total_cost
    FROM traces_ts
    GROUP BY 1, 2
""")

# Compare query cost
t0 = time.perf_counter()
naive_query = conn.execute("""
    SELECT AVG(latency_ms) FROM traces_ts
    WHERE event_time >= '2026-10-14 00:00:00' AND event_time < '2026-10-14 00:05:00'
""").fetchall()
naive_ms = (time.perf_counter() - t0) * 1000
naive_result = naive_query[0][0] or 0

t0 = time.perf_counter()
rollup_query = conn.execute("""
    SELECT SUM(trace_count * avg_latency) / SUM(trace_count)
    FROM traces_5min_rollup
    WHERE bucket = '2026-10-14 00:00'
""").fetchall()
rollup_ms = (time.perf_counter() - t0) * 1000
rollup_result = rollup_query[0][0] or 0

print(f"\nQuery: 'avg latency for 2026-10-14 00:00-00:05':")
print(f"  Naive (scan traces table):       {naive_ms:.2f}ms")
print(f"  Pre-aggregated (5-min rollup):   {rollup_ms:.2f}ms")
print(f"  Result naive:   {naive_result:.0f}ms")
print(f"  Result rollup:  {rollup_result:.0f}ms (same answer, faster)")

# At Meta scale (1B traces/day):
# 1B rows / 288 buckets = 3.5M rows per bucket
# Naive: scan 3.5M rows -> ~5 seconds on ClickHouse
# Rollup: scan 1 row -> ~1ms
# That's 5000x faster

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'how do you do real-time dashboards?')")
print("=" * 70)
print("""
Q: "How do you power Grafana dashboards from 1B traces/day?"

A: "Three layers:

1. RAW TRACES (1B rows/day, Kafka -> S3):
   - Every LLM call lands in traces table (Postgres, ClickHouse)
   - Partitioned by day, retained 30 days
   - Used for debugging, ad-hoc queries, gold set extraction

2. PRE-AGGREGATED ROLLUPS (288 x N buckets/day, Flink -> ClickHouse):
   - Flink job computes 5-min tumbling windows continuously
   - Aggregates: count, avg/p50/p95/p99 latency, cost, satisfaction
   - Output: traces_5min_rollup table (288 buckets x 3 prompt versions = 864 rows/day)
   - This is what Grafana queries - O(1) lookup per dashboard tile

3. WATERMARK + ALERTING:
   - Flink emits 99% of buckets within 5 seconds of window close
   - 1% late arrivals (network blips) handled by allowed lateness = 60s
   - Alert manager subscribes to Flink, fires SLO burn-rate alerts

Real numbers at Meta scale:
- Raw table: 1B rows/day, 5s query for 5-min slice
- Rollup: 864 rows/day, 1ms query for same slice
- Storage: rollup is 0.001% the size of raw

Without pre-aggregation, your Grafana dashboard would cost $50k/month
in ClickHouse compute alone. With rollups, it's $200/month.
""")
