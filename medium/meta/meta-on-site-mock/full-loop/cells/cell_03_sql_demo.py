"""
Cell 03 (full-loop): SQL on Traces + Feedback

The Round 2.3 answer. The 4 SQL queries an L6 will be asked:
1. Satisfaction by prompt_version, last 7 days, p95
2. Same, split by day for trend
3. User 123's 10 worst queries on prompt v2
4. Gold dataset extraction
"""
import sqlite3
import random
from datetime import date, timedelta

conn = sqlite3.connect(':memory:')

conn.executescript("""
    CREATE TABLE traces (
        trace_id TEXT, day DATE, user_id INT,
        prompt_version TEXT, latency_ms INT, query TEXT,
        chunk_ids TEXT,
        PRIMARY KEY (trace_id, day)
    );
    CREATE TABLE feedback (
        trace_id TEXT, rating TEXT,  -- 'thumbs_up' | 'thumbs_down'
        corrected_answer TEXT, is_gold INT
    );
""")

random.seed(42)
counter = 0

# Seed 30 days of traces for 1000 users, 3 prompt versions
start = date(2026, 9, 15)
for day_offset in range(30):
    day = start + timedelta(days=day_offset)
    n_traces = random.randint(800, 1500)
    for _ in range(n_traces):
        counter += 1
        trace_id = f"trc_{counter:08d}"
        prompt_v = random.choice(["v1.0", "v2.0", "v2.1", "v3.0-beta"])
        # v3.0-beta is slower but better
        if prompt_v == "v3.0-beta":
            latency = random.randint(400, 900)
            satisfaction_p = 0.85
        elif prompt_v == "v2.1":
            latency = random.randint(250, 500)
            satisfaction_p = 0.75
        else:
            latency = random.randint(200, 400)
            satisfaction_p = 0.65
        conn.execute(
            "INSERT INTO traces VALUES (?, ?, ?, ?, ?, ?, ?)",
            (trace_id, day.isoformat(), random.randint(1, 1000),
             prompt_v, latency, f"query {random.randint(0, 1000)}",
             f"[{','.join(str(x) for x in random.sample(range(1000), 8))}]")
        )
        # 10% have feedback
        if random.random() < 0.1:
            rating = "thumbs_up" if random.random() < satisfaction_p else "thumbs_down"
            is_gold = 1 if rating == "thumbs_down" and random.random() < 0.3 else 0
            conn.execute(
                "INSERT INTO feedback VALUES (?, ?, ?, ?)",
                (trace_id, rating, f"corrected {rating}", is_gold)
            )
conn.commit()
total_traces = conn.execute("SELECT COUNT(*) FROM traces").fetchone()[0]
print(f"Seeded {total_traces:,} traces over 30 days, ~10% with feedback\n")

# Q1: Satisfaction by prompt_version, last 7 days, p95
print("=" * 60)
print("Q1: Satisfaction by prompt_version, last 7 days")
print("=" * 60)
result = conn.execute("""
    SELECT
        t.prompt_version,
        COUNT(*) AS total,
        ROUND(100.0 * AVG(CASE WHEN f.rating = 'thumbs_up' THEN 1.0 ELSE 0.0 END), 1) AS satisfaction_pct,
        -- p95 latency approximation (SQLite doesn't have percentile_cont)
        MAX(t.latency_ms) AS max_latency
    FROM traces t
    LEFT JOIN feedback f ON t.trace_id = f.trace_id
    WHERE t.day >= '2026-10-08'
    GROUP BY t.prompt_version
    ORDER BY satisfaction_pct DESC
""").fetchall()
print(f"\n{'prompt_version':<14} {'total':>8} {'satisfaction':>13} {'max_ms':>8}")
print("-" * 46)
for row in result:
    print(f"{row[0]:<14} {row[1]:>8,} {row[2]:>12}% {row[3]:>8}")

# Q2: Trend by day for v3.0-beta
print("\n" + "=" * 60)
print("Q2: Satisfaction trend for v3.0-beta (last 7 days, by day)")
print("=" * 60)
result = conn.execute("""
    SELECT t.day,
           COUNT(*) AS total,
           ROUND(100.0 * AVG(CASE WHEN f.rating = 'thumbs_up' THEN 1.0 ELSE 0.0 END), 1) AS sat
    FROM traces t
    LEFT JOIN feedback f ON t.trace_id = f.trace_id
    WHERE t.prompt_version = 'v3.0-beta'
      AND t.day >= '2026-10-08'
    GROUP BY t.day
    ORDER BY t.day
""").fetchall()
print(f"\n{'day':<12} {'total':>8} {'sat %':>8}")
print("-" * 30)
for day, total, sat in result:
    print(f"{day:<12} {total:>8,} {sat:>7}%")

# Q3: User 123's worst queries on v2.0
print("\n" + "=" * 60)
print("Q3: User 123's 10 worst queries on v2.0 (thumbs_down)")
print("=" * 60)
result = conn.execute("""
    SELECT t.trace_id, t.query, t.latency_ms, f.corrected_answer
    FROM traces t
    JOIN feedback f ON t.trace_id = f.trace_id
    WHERE t.user_id = 123
      AND t.prompt_version = 'v2.0'
      AND f.rating = 'thumbs_down'
    ORDER BY t.latency_ms DESC
    LIMIT 10
""").fetchall()
print(f"\n{'trace_id':<30} {'latency_ms':>11} {'corrected_answer':<25}")
print("-" * 70)
for row in result[:10]:
    print(f"{row[0]:<30} {row[2]:>11} {row[3] or '':<25}")

# Q4: GOLD DATASET (the L6 phrase)
print("\n" + "=" * 60)
print("Q4: Extract GOLD DATASET for eval (the magic phrase)")
print("=" * 60)
print("""
Gold set = feedback.corrected_answer WHERE rating = thumbs_down AND is_gold = 1

This is the eval input for every model promotion. Recall@8 / nDCG
must be >= baseline on this set, or the promotion is blocked.
""")
gold = conn.execute("""
    SELECT t.trace_id, t.query, t.chunk_ids, t.prompt_version, f.corrected_answer
    FROM traces t
    JOIN feedback f ON t.trace_id = f.trace_id
    WHERE f.is_gold = 1
    LIMIT 5
""").fetchall()
gold_total = conn.execute("SELECT COUNT(*) FROM feedback WHERE is_gold = 1").fetchone()[0]
print(f"Gold dataset size: {gold_total} traces")
print(f"\nFirst 5 entries (this is what you'd feed to Recall@8):")
for row in gold:
    print(f"  {row[0]}: {row[1][:50]}  (corrected: {row[4]})")

# Bonus: cursor pagination (the OTHER magic phrase)
print("\n" + "=" * 60)
print("BONUS: CURSOR pagination (the O(1) vs OFFSET O(N) phrase)")
print("=" * 60)
print("""
WRONG: SELECT * FROM traces ORDER BY day DESC LIMIT 50 OFFSET 100000
       -> scans first 100050 rows, throws away 100k, returns 50
       -> 5+ seconds on 1B rows, OOMs

RIGHT: cursor = (day, trace_id) tuple
       SELECT * FROM traces
       WHERE (day, trace_id) < (:cursor_day, :cursor_trace)
       ORDER BY day DESC, trace_id DESC LIMIT 50
       -> O(log n) seek + O(limit) scan via (day, trace_id) index
       -> 5ms regardless of offset
""")
