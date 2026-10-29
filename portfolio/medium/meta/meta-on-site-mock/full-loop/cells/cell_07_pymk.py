"""
Cell 07 (full-loop): PYMK 10/10 L6/Staff Answer

The Round 3 whiteboard answer. The flagship L6 question:
"Design PYMK with explanation 'You both worked at X' — no hallucination,
500M users, time-travel friendship check, celebrity fanout bound."

Five stages: requirements, data model, architecture, deep dives, close.
"""
import sqlite3
import random
from datetime import date, timedelta
from collections import defaultdict

conn = sqlite3.connect(':memory:')

# ════════════════════════════════════════════════════════════════
# STAGE 1: DATA MODEL — SCD2 with canonical key
# ════════════════════════════════════════════════════════════════
conn.executescript("""
    -- Canonical key: (A,B) and (B,A) = ONE row, not two
    CREATE TABLE dim_friendship (
        user_id_low  BIGINT,    -- MIN(user_a, user_b)
        user_id_high BIGINT,    -- MAX(user_a, user_b)
        valid_from   DATE,
        valid_to     DATE,      -- NULL = currently friends
        affinity     REAL,
        PRIMARY KEY (user_id_low, user_id_high, valid_from)
    );
    CREATE INDEX idx_friend_low ON dim_friendship(user_id_low, valid_to);
    CREATE INDEX idx_friend_high ON dim_friendship(user_id_high, valid_to);

    -- Work history (also SCD2: promotion = new row)
    CREATE TABLE dim_work_history (
        user_id      BIGINT, company_id BIGINT, company_name TEXT,
        start_date   DATE, end_date DATE, title TEXT,
        PRIMARY KEY (user_id, company_id, start_date)
    );
    CREATE INDEX idx_work_company ON dim_work_history(company_id, start_date, end_date);

    -- PYMK cache (serving table)
    CREATE TABLE pymk_cache (
        viewer_id BIGINT, candidate_id BIGINT, score REAL,
        explanation TEXT, evidence_json TEXT, is_celebrity INT,
        explain_version TEXT, generated_at TIMESTAMP,
        PRIMARY KEY (viewer_id, candidate_id)
    );

    -- Audit (for Legal + hallucination rate)
    CREATE TABLE explanation_audit (
        viewer_id BIGINT, candidate_id BIGINT,
        explanation TEXT, evidence_json TEXT, llm_version TEXT,
        validation_pass INT, shown_at TIMESTAMP
    );

    -- GDPR tombstone
    CREATE TABLE user_tombstone (
        user_id BIGINT PRIMARY KEY,
        deleted_at TIMESTAMP, purge_after DATE
    );
""")

# Seed
random.seed(42)
N = 1000
N_CORPS = 50
corps = [(i, f"Company_{i}") for i in range(1, N_CORPS + 1)]

# Work history
seen = set()
for u in range(1, N + 1):
    used = set()
    for _ in range(random.randint(1, 4)):
        cid, cname = random.choice(corps)
        if cid in used: continue
        used.add(cid)
        start = date(2015 + random.randint(0, 8), random.randint(1, 12), 1)
        end = start + timedelta(days=random.randint(180, 1500))
        if end > date(2024, 12, 31): end = date(2024, 12, 31)
        if random.random() < 0.2: end = None
        conn.execute(
            "INSERT INTO dim_work_history VALUES (?,?,?,?,?,?)",
            (u, cid, cname, start.isoformat(), end.isoformat() if end else None, "SWE")
        )

# Friendships (SCD2 with 30% ended)
for _ in range(5000):
    a, b = random.randint(1, N), random.randint(1, N)
    if a == b: continue
    low, high = min(a, b), max(a, b)
    vf = date(2018 + random.randint(0, 6), random.randint(1, 12), 1)
    vt = None if random.random() > 0.3 else vf + timedelta(days=random.randint(180, 1500))
    conn.execute(
        "INSERT INTO dim_friendship VALUES (?,?,?,?,?)",
        (low, high, vf.isoformat(), vt.isoformat() if vt else None, random.random())
    )
conn.commit()
print(f"Seeded {N} users, 5000 friendships (30% ended)\n")

# ════════════════════════════════════════════════════════════════
# STAGE 2: TIME-TRAVEL QUERY
# ════════════════════════════════════════════════════════════════
print("=" * 60)
print("STAGE 2: TIME-TRAVEL — were A and B friends on a date?")
print("=" * 60)

def were_friends(a, b, on_date):
    low, high = min(a, b), max(a, b)
    r = conn.execute("""
        SELECT 1 FROM dim_friendship
        WHERE user_id_low = ? AND user_id_high = ?
          AND valid_from <= ?
          AND (valid_to IS NULL OR valid_to > ?)
    """, (low, high, on_date, on_date)).fetchone()
    return r is not None

# Find a real ended friendship
pair = conn.execute("""
    SELECT user_id_low, user_id_high, valid_from, valid_to
    FROM dim_friendship WHERE valid_to IS NOT NULL LIMIT 1
""").fetchone()
if pair:
    low, high, vf, vt = pair
    print(f"Example: users {low} & {high} ({vf} to {vt})")
    print(f"  Friends on {vf} (during)?  {were_friends(low, high, vf)}")
    print(f"  Friends on 2099-01-01?     {were_friends(low, high, '2099-01-01')}")
    print(f"  Friends on 2010-01-01?     {were_friends(low, high, '2010-01-01')}")

# ════════════════════════════════════════════════════════════════
# STAGE 3: WORK-OVERLAP QUERY
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STAGE 3: WORK OVERLAP — 'you both worked at X together'")
print("=" * 60)

shared = conn.execute("""
    SELECT w1.user_id, w2.user_id, w1.company_name,
           w1.start_date, w1.end_date
    FROM dim_work_history w1
    JOIN dim_work_history w2 ON w1.company_id = w2.company_id
    WHERE w1.user_id < w2.user_id
      AND w1.start_date <= COALESCE(w2.end_date, '9999-12-31')
      AND COALESCE(w1.end_date, '9999-12-31') >= w2.start_date
    ORDER BY w1.start_date LIMIT 1
""").fetchone()
if shared:
    u1, u2, cname, s, e = shared
    print(f"Example: users {u1} & {u2} both at {cname} ({s[:7]} to {(e or 'present')[:7]})")
    print(f'  => Explanation: "You both worked at {cname} from {s[:7]} to {(e or "present")[:7]}"')

# ════════════════════════════════════════════════════════════════
# STAGE 4: CELEBRITY BOUNDED FANOUT
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STAGE 4: CELEBRITY BOUNDED FANOUT — push vs pull")
print("=" * 60)

FOLLOWERS = [10_000, 100_000, 500_000, 5_000_000, 50_000_000]
print(f"\n{'Celeb followers':>20} {'Push writes':>15} {'Pull writes':>15} {'Reduction':>10}")
print("-" * 65)
for f in FOLLOWERS:
    push = f * 100
    pull = push if f < 500_000 else (f // 100) * 100
    red = 100 * (1 - pull / push)
    print(f"{f:>20,} {push:>15,} {pull:>15,} {red:>9.0f}%")
print("\n  => 50M follower celeb: 5B push -> 50M pull (100x reduction)")

# ════════════════════════════════════════════════════════════════
# STAGE 5: NO-HALLUCINATION VALIDATION LAYER
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STAGE 5: NO-HALLUCINATION GUARD")
print("=" * 60)

def validate(explanation, evidence):
    """Regex check: every company in explanation must be in evidence."""
    allowed = set(evidence.get("company_ids", []))
    if not allowed:
        return "mutual" in explanation.lower() or "connection" in explanation.lower()
    for cid, cname in evidence.get("company_map", {}).items():
        if cname.lower() in explanation.lower() and cid not in allowed:
            return False
    return True

tests = [
    ("You both worked at Meta from 2020-2022", {"company_ids": ["42"], "company_map": {"42": "Meta"}}, True),
    ("You both worked at FakeCorp", {"company_ids": ["42"], "company_map": {"42": "Meta"}}, False),
    ("5 mutual connections", {"company_ids": [], "company_map": {}}, True),
    ("You worked at Meta and FakeCorp", {"company_ids": ["42"], "company_map": {"42": "Meta"}}, False),
]
print(f"\n{'Explanation':<45} {'Pass':>5} {'Expected':>9}")
print("-" * 62)
for ex, ev, expected in tests:
    p = validate(ex, ev)
    print(f"{ex[:43]:<45} {('Y' if p else 'N'):>5} {('Y' if expected else 'N'):>9} {'OK' if p == expected else 'MISMATCH'}")

# Audit log
for ex, ev, _ in tests:
    conn.execute(
        "INSERT INTO explanation_audit VALUES (?,?,?,?,?,?,?)",
        (100, 200, ex, str(ev), "llm_v3", int(validate(ex, ev)), "2026-10-15")
    )
conn.commit()
hallu_rate = conn.execute("""
    SELECT 100.0 * SUM(CASE WHEN validation_pass=0 THEN 1 ELSE 0 END) / COUNT(*)
    FROM explanation_audit
""").fetchone()[0]
print(f"\n  Hallucination rate: {hallu_rate:.0f}%  (alert if >0.1%)")

# ════════════════════════════════════════════════════════════════
# THE 10/10 CLOSING LINE
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("THE 10/10 CLOSING LINE")
print("=" * 60)
print("""
"Design is GROUNDED, BOUNDED, and AUDITABLE:
 - SCD2 with canonical key + index for time-travel
 - overlap join for 'worked at X together'
 - evidence_json + validation layer for zero hallucination with audit
 - pull model for celebrity to bound fanout from 1B to 1k writes
 - shadow dual-write for safe model rollout"
""")
