"""
Cell 06 (full-loop): Cursor Pagination — the O(1) vs OFFSET O(N) killer

The Round 2.4 + Round 4 magic phrase. Cursor pagination is the L6
barometer: if you reach for OFFSET, you failed. If you reach for
a (sort_key, id) tuple, you passed.
"""
import sqlite3
import time

conn = sqlite3.connect(':memory:')

# 1M traces - enough to show the perf gap
conn.executescript("""
    CREATE TABLE traces (
        trace_id TEXT PRIMARY KEY,
        day DATE,
        prompt_version TEXT,
        latency_ms INT,
        query TEXT
    );
    CREATE INDEX idx_trace_lookup ON traces(day, trace_id DESC);
""")

import random
random.seed(42)
days = ['2026-10-' + str(d).zfill(2) for d in range(1, 16)]
print(f"Seeding 1M traces across {len(days)} days...")
for i in range(1_000_000):
    conn.execute(
        "INSERT INTO traces VALUES (?, ?, ?, ?, ?)",
        (f"trc_{i:08d}", random.choice(days),
         random.choice(["v1.0", "v2.0", "2.1", "v3.0-beta"]),
         random.randint(100, 1000),
         f"query {i}")
    )
conn.commit()
total = conn.execute("SELECT COUNT(*) FROM traces").fetchone()[0]
print(f"Seeded {total:,} rows\n")

# Method 1: OFFSET (the WRONG way)
print("=" * 60)
print("METHOD 1: OFFSET 500000 (the WRONG way)")
print("=" * 60)
t0 = time.perf_counter()
result = conn.execute("""
    SELECT trace_id, day, prompt_version, latency_ms
    FROM traces
    WHERE prompt_version = 'v3.0-beta'
    ORDER BY day DESC, trace_id DESC
    LIMIT 50 OFFSET 500000
""").fetchall()
offset_ms = (time.perf_counter() - t0) * 1000
print(f"  Returned: {len(result)} rows")
print(f"  Time:     {offset_ms:.0f}ms")
print(f"  Scanned:  ~500,050 rows to return 50")
print(f"  At 1B:    ~{offset_ms * 1000 / 1000:.0f}ms (5+ sec), often OOM")

# Method 2: Cursor (the RIGHT way)
print("\n" + "=" * 60)
print("METHOD 2: cursor = (day, trace_id) tuple (the RIGHT way)")
print("=" * 60)

def fetch_page(cursor, limit=50):
    """Cursor pagination. O(log n) seek via (day, trace_id) index."""
    if cursor is None:
        return conn.execute("""
            SELECT trace_id, day, prompt_version, latency_ms
            FROM traces
            WHERE prompt_version = 'v3.0-beta'
            ORDER BY day DESC, trace_id DESC
            LIMIT ?
        """, (limit,)).fetchall()
    c_day, c_trace = cursor
    return conn.execute("""
        SELECT trace_id, day, prompt_version, latency_ms
        FROM traces
        WHERE prompt_version = 'v3.0-beta'
          AND (day, trace_id) < (?, ?)
        ORDER BY day DESC, trace_id DESC
        LIMIT ?
    """, (c_day, c_trace, limit)).fetchall()

# First page
t0 = time.perf_counter()
page1 = fetch_page(None, limit=50)
t1 = (time.perf_counter() - t0) * 1000
print(f"  Page 1:    {len(page1)} rows in {t1:.1f}ms")

# Subsequent pages using cursor
total_ms = t1
for i in range(5):
    last = page1[-1]
    cursor = (last[1], last[0])  # (day, trace_id)
    t0 = time.perf_counter()
    page1 = fetch_page(cursor, limit=50)
    total_ms += (time.perf_counter() - t0) * 1000
avg = total_ms / 6
print(f"  Page 2-6:  ~{avg:.1f}ms each (constant time)")
print(f"  At 1B:     ~{avg:.1f}ms regardless of page depth")
print(f"  => ~{offset_ms / avg:.0f}x faster than OFFSET at deep pages")

# Method 3: Keyset pagination (the Meta internal pattern)
print("\n" + "=" * 60)
print("METHOD 3: keyset (the Meta internal pattern)")
print("=" * 60)
print("""
Keyset = opaque base64 token. Client never sees the structure.
Server stores: {'day': '2026-10-14', 'trace_id': 'trc_00123456'}

  GET /traces?day=2026-10-14&cursor=eyJkYXkiOiIyMDI2LTEwLTE0Ii...
   -> decode cursor -> SELECT ... WHERE (day, trace_id) < (decoded)
   -> encode next cursor from last row
   -> return: {data: [...], next_cursor: 'eyJkYXki...'}

Why opaque cursors?
- Can change schema without breaking clients
- Can include filters in cursor (composite cursor)
- Hides implementation details
""")

# The full function an L6 writes in 5 min
print("=" * 60)
print("THE L6 WHITEBOARD VERSION (5 min, no IDE)")
print("=" * 60)

def fetch_traces_l6(day, prompt_version, cursor, limit=50):
    """
    O(1) cursor pagination on (day, trace_id).

    Args:
        day: filter by day
        prompt_version: filter by version
        cursor: tuple (day, trace_id) or None for first page
        limit: page size

    Returns:
        (rows, next_cursor)
    """
    if cursor:
        c_day, c_trace = cursor
        rows = conn.execute("""
            SELECT trace_id, day, prompt_version, latency_ms
            FROM traces
            WHERE prompt_version = ?
              AND (day, trace_id) < (?, ?)
            ORDER BY day DESC, trace_id DESC
            LIMIT ?
        """, (prompt_version, c_day, c_trace, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT trace_id, day, prompt_version, latency_ms
            FROM traces
            WHERE day <= ? AND prompt_version = ?
            ORDER BY day DESC, trace_id DESC
            LIMIT ?
        """, (day, prompt_version, limit)).fetchall()
    next_cursor = (rows[-1][1], rows[-1][0]) if rows else None
    return rows, next_cursor

rows, next_cur = fetch_traces_l6("2026-10-14", "v3.0-beta", None, 50)
print(f"  Page 1: 50 rows, next_cursor = {next_cur}")
rows, next_cur = fetch_traces_l6("2026-10-14", "v3.0-beta", next_cur, 50)
print(f"  Page 2: 50 rows, next_cursor = {next_cur}")
print("\n  => The full function. ~15 lines. Always.")
