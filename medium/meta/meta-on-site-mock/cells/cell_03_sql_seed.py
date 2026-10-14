import sqlite3
import pandas as pd

conn = sqlite3.connect(':memory:')
cur = conn.cursor()

cur.executescript("""
CREATE TABLE traces (
    trace_id TEXT PRIMARY KEY,
    user_id TEXT,
    query TEXT,
    prompt_version INT,
    response TEXT,
    latency_ms INT,
    cost_tokens INT,
    created_at TIMESTAMP
);
CREATE TABLE feedback (
    feedback_id TEXT PRIMARY KEY,
    trace_id TEXT,
    rating TEXT,
    corrected_answer TEXT,
    created_at TIMESTAMP
);
""")

# Seed synthetic data - 7 days of traces, ~100/day
np.random.seed(42)
trace_rows = []
feedback_rows = []
for day_offset in range(7):
    for i in range(100):
        trace_id = f"t_{day_offset}_{i}"
        trace_rows.append((
            trace_id,
            f"u_{i % 20}",
            f"query {i}",
            int(np.random.choice([1, 2, 3])),
            f"response {i}",
            int(np.random.normal(450, 100)),
            int(np.random.normal(800, 200)),
            f"2026-10-{7+day_offset:02d} 12:00:00",
        ))
        if np.random.rand() < 0.3:
            feedback_rows.append((
                f"f_{trace_id}",
                trace_id,
                'thumbs_up' if np.random.rand() < 0.75 else 'thumbs_down',
                None if np.random.rand() < 0.5 else f"corrected_{i}",
                f"2026-10-{7+day_offset:02d} 12:05:00",
            ))

cur.executemany("INSERT INTO traces VALUES (?,?,?,?,?,?,?,?)", trace_rows)
cur.executemany("INSERT INTO feedback VALUES (?,?,?,?,?)", feedback_rows)
conn.commit()

print(f"Seeded {len(trace_rows)} traces and {len(feedback_rows)} feedback rows")
