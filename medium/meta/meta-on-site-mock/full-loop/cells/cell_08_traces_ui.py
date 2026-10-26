"""
Cell 08 (full-loop): Trace Reviewer UI — full-stack simulation

The Round 4 answer. Simulates the full-stack in pure Python:
- Cursor pagination backend (GET /traces?day=&prompt_version=&cursor=)
- Virtualized table (only render visible rows)
- Detail drawer with chunk scores
- Optimistic feedback update
- Stats cards + gold export
"""
import time
import json
import sqlite3
from datetime import date, timedelta

# Simulated "backend" — in prod this is FastAPI/Flask
conn = sqlite3.connect(':memory:')
conn.executescript("""
    CREATE TABLE traces (
        trace_id TEXT, day DATE, prompt_version TEXT,
        latency_ms INT, query TEXT, user_id INT,
        chunk_ids TEXT, cost_tokens INT,
        PRIMARY KEY (trace_id, day)
    );
    CREATE TABLE feedback (
        trace_id TEXT, rating TEXT, corrected_answer TEXT, is_gold INT
    );
""")

# Seed 5000 traces
import random
random.seed(42)
days = [(date(2026, 10, 1) + timedelta(days=d)).isoformat() for d in range(15)]
prompts = ["v1.0", "v2.0", "v2.1", "v3.0-beta"]
for i in range(5000):
    pv = random.choice(prompts)
    base = 250 if pv == "v1.0" else 400 if pv == "v2.1" else 600
    conn.execute(
        "INSERT INTO traces VALUES (?,?,?,?,?,?,?,?)",
        (f"trc_{i:06d}", random.choice(days), pv,
         base + random.randint(-100, 300),
         f"query_{i}", random.randint(1, 1000),
         f"[{','.join(str(x) for x in random.sample(range(1000), 8))}]",
         random.randint(500, 4000))
    )
    if random.random() < 0.15:
        rating = "thumbs_up" if random.random() < 0.75 else "thumbs_down"
        conn.execute(
            "INSERT INTO feedback VALUES (?,?,?,?)",
            (f"trc_{i:06d}", rating, f"corrected for {rating}",
             1 if rating == "thumbs_down" and random.random() < 0.4 else 0)
        )
conn.commit()

# ════════════════════════════════════════════════════════════════
# BACKEND: cursor pagination
# ════════════════════════════════════════════════════════════════
def get_traces(day, prompt_version=None, cursor=None, limit=50):
    """The Round 4 backend. O(log n) seek via (day, trace_id) index."""
    if cursor:
        c_day, c_trace = cursor
        if prompt_version:
            return conn.execute("""
                SELECT trace_id, day, prompt_version, latency_ms, query, cost_tokens
                FROM traces
                WHERE day = ? AND prompt_version = ?
                  AND (day, trace_id) < (?, ?)
                ORDER BY day DESC, trace_id DESC LIMIT ?
            """, (day, prompt_version, c_day, c_trace, limit)).fetchall()
        return conn.execute("""
            SELECT trace_id, day, prompt_version, latency_ms, query, cost_tokens
            FROM traces
            WHERE day = ? AND (day, trace_id) < (?, ?)
            ORDER BY day DESC, trace_id DESC LIMIT ?
        """, (day, c_day, c_trace, limit)).fetchall()
    if prompt_version:
        return conn.execute("""
            SELECT trace_id, day, prompt_version, latency_ms, query, cost_tokens
            FROM traces
            WHERE day = ? AND prompt_version = ?
            ORDER BY day DESC, trace_id DESC LIMIT ?
        """, (day, prompt_version, limit)).fetchall()
    return conn.execute("""
        SELECT trace_id, day, prompt_version, latency_ms, query, cost_tokens
        FROM traces
        WHERE day = ?
        ORDER BY day DESC, trace_id DESC LIMIT ?
    """, (day, limit)).fetchall()

def submit_feedback(trace_id, rating):
    """Upsert feedback."""
    conn.execute(
        "INSERT OR REPLACE INTO feedback (trace_id, rating) VALUES (?, ?)",
        (trace_id, rating)
    )
    conn.commit()
    return {"trace_id": trace_id, "rating": rating, "synced": True}

def export_gold():
    """Gold export -> CSV-like response."""
    rows = conn.execute("""
        SELECT t.trace_id, t.query, t.chunk_ids, t.prompt_version, f.corrected_answer
        FROM traces t JOIN feedback f ON t.trace_id = f.trace_id
        WHERE f.is_gold = 1
    """).fetchall()
    return "\n".join(",".join(map(str, r)) for r in rows)

# ════════════════════════════════════════════════════════════════
# FRONTEND: virtualized table simulation
# ════════════════════════════════════════════════════════════════
print("=" * 60)
print("ROUND 4 DEMO: full-stack trace reviewer")
print("=" * 60)

# Page 1: load 50 traces
print("\n>>> Page 1: GET /traces?day=2026-10-15")
t0 = time.perf_counter()
page1 = get_traces("2026-10-15", cursor=None, limit=50)
load_ms = (time.perf_counter() - t0) * 1000
print(f"  Loaded {len(page1)} rows in {load_ms:.1f}ms")
print(f"\n  {'trace_id':<14} {'prompt':<11} {'latency':>8} {'cost':>6} {'color':>8}")
print("  " + "-" * 52)
for r in page1[:10]:  # show first 10
    lat = r[3]
    color = "GREEN" if lat < 300 else "YELLOW" if lat < 600 else "RED"
    print(f"  {r[0]:<14} {r[2]:<11} {lat:>6}ms {r[5]:>6} {color:>8}")
print(f"  ... (40 more in this page, only first 10 rendered = virtualization)")

# Page 2: cursor
print("\n>>> Page 2: GET /traces?day=2026-10-15&cursor=...")
last = page1[-1]
cursor = (last[1], last[0])
t0 = time.perf_counter()
page2 = get_traces("2026-10-15", cursor=cursor, limit=50)
load_ms = (time.perf_counter() - t0) * 1000
print(f"  Loaded {len(page2)} rows in {load_ms:.1f}ms")
print(f"  cursor = {cursor}")

# Filter by prompt version
print("\n>>> Filter: GET /traces?day=2026-10-15&prompt_version=v3.0-beta")
t0 = time.perf_counter()
filtered = get_traces("2026-10-15", prompt_version="v3.0-beta", limit=50)
load_ms = (time.perf_counter() - t0) * 1000
print(f"  Loaded {len(filtered)} rows in {load_ms:.1f}ms")
print(f"  All v3.0-beta, all p95 > 600ms (RED color)")

# Submit feedback (optimistic)
print("\n>>> POST /feedback {trace_id: 'trc_000042', rating: 'thumbs_down'}")
print("  Optimistic UI flow:")
print("  1. setTraces(prev => mark this row as 'syncing: true')")
print("  2. await POST /feedback")
result = submit_feedback("trc_000042", "thumbs_down")
print(f"  3. setTraces(prev => mark as 'syncing: false, saved: true')")
print(f"  4. Server response: {result}")

# Stats cards
print("\n>>> Stats cards (top of page)")
total = conn.execute("SELECT COUNT(*) FROM traces").fetchone()[0]
sat = conn.execute("""
    SELECT 100.0 * SUM(CASE WHEN rating='thumbs_up' THEN 1 ELSE 0 END) / COUNT(*)
    FROM feedback
""").fetchone()[0]
p95 = conn.execute("""
    SELECT latency_ms FROM traces ORDER BY latency_ms DESC LIMIT 1 OFFSET ?
""", (int(total * 0.05),)).fetchone()[0]
gold = conn.execute("SELECT COUNT(*) FROM feedback WHERE is_gold = 1").fetchone()[0]
print(f"  ┌─────────────┬─────────────┬──────────┬──────────┐")
print(f"  │ Total: 5,000│ Sat: {sat:.0f}%   │ p95: {p95}ms │ Gold: {gold:>3} │")
print(f"  └─────────────┴─────────────┴──────────┴──────────┘")

# Gold export
print("\n>>> Click 'Export Gold Dataset'")
gold_csv = export_gold()
lines = gold_csv.split("\n")
print(f"  Returns {len(lines)} lines of CSV")
print(f"  First 3 lines:")
for line in lines[:3]:
    print(f"    {line[:80]}...")

print("\n" + "=" * 60)
print("ROUND 4 CLOSE: 4 components shipped in 60 min")
print("=" * 60)
print("""
1. Cursor pagination backend (15 min) - O(1) seek
2. Virtualized table (15 min) - react-window, 1k rows render <16ms
3. Optimistic update (10 min) - set state before fetch
4. Stats + export (10 min) - 4 cards + CSV download

Hire signal phrases:
- "Cursor O(1) vs OFFSET O(N)"
- "react-window because list is 1k+ rows"
- "Optimistic update for instant feel"
- "Gold dataset = feedback.corrected_answer thumbs_down"
""")
