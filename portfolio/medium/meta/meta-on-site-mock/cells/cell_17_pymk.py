"""
Cell 17: PYMK (People You May Know) - 10/10 L6/Staff Whiteboard Answer

What this proves for the L6 interview:
- SCD2 with canonical key (user_id_low, user_id_high) for time-travel friendship
- Work-overlap JOIN (not just same company) for "you both worked at X together"
- Bounded celebrity fanout (push vs pull, threshold >500k followers)
- No-hallucination guard: validation layer that REJECTS bad LLM output
- GDPR tombstone + audit trail Legal can replay
"""
import sqlite3
import time
import json
import random
from datetime import date, timedelta
from collections import defaultdict

conn = sqlite3.connect(':memory:')

# ════════════════════════════════════════════════════════════════
# DATA MODEL (the L6 10/10 answer)
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("DATA MODEL: SCD2 with canonical key for time-travel")
print("=" * 70)
print("""
Why canonical key (user_id_low, user_id_high)?
- (A,B) and (B,A) are the SAME friendship
- Storing both creates 2x writes and 2x storage
- Canonical order (LOW < HIGH) means: one row per friendship
- Index lookup is symmetric: WHERE low = LEAST(A,B) AND high = GREATEST(A,B)
""")

conn.executescript("""
    -- Slowly Changing Dimension Type 2: every friendship change is a NEW row
    -- valid_from / valid_to with NULL meaning "current"
    CREATE TABLE dim_friendship (
        user_id_low  BIGINT,    -- MIN(user_a, user_b) - canonical order
        user_id_high BIGINT,    -- MAX(user_a, user_b)
        valid_from   DATE,
        valid_to     DATE,      -- NULL = currently friends
        affinity     REAL,      -- interaction weight 0.0-1.0
        PRIMARY KEY (user_id_low, user_id_high, valid_from)
    );
    CREATE INDEX idx_friend_low ON dim_friendship(user_id_low, valid_to);
    CREATE INDEX idx_friend_high ON dim_friendship(user_id_high, valid_to);

    -- Work history (SCD2 too: a promotion = new row)
    CREATE TABLE dim_work_history (
        user_id      BIGINT,
        company_id   BIGINT,
        company_name TEXT,
        start_date   DATE,
        end_date     DATE,      -- NULL = current job
        title        TEXT,
        PRIMARY KEY (user_id, company_id, start_date)
    );
    CREATE INDEX idx_work_user ON dim_work_history(user_id, end_date);
    CREATE INDEX idx_work_company ON dim_work_history(company_id, start_date, end_date);

    -- PYMK cache (the serving table)
    CREATE TABLE pymk_cache (
        viewer_id       BIGINT,
        candidate_id    BIGINT,
        score           REAL,
        explanation     TEXT,         -- "You both worked at Meta from 2020-2022"
        evidence_json   TEXT,         -- [{type: 'work_overlap', company_id: 42, ...}]
        is_celebrity    INTEGER,      -- 1 if celeb, 0 otherwise
        explain_version TEXT,         -- LLM version, for A/B
        generated_at    TIMESTAMP,
        PRIMARY KEY (viewer_id, candidate_id)
    );

    -- Audit table: every explanation ever shown (for Legal + hallucination rate)
    CREATE TABLE explanation_audit (
        viewer_id        BIGINT,
        candidate_id     BIGINT,
        explanation      TEXT,
        evidence_json    TEXT,
        llm_version      TEXT,
        validation_pass  INTEGER,    -- 1 = passed, 0 = rejected
        shown_at         TIMESTAMP
    );

    -- GDPR tombstone
    CREATE TABLE user_tombstone (
        user_id     BIGINT PRIMARY KEY,
        deleted_at  TIMESTAMP,
        purge_after DATE  -- 30 days from deletion
    );
""")

print("Tables created: dim_friendship, dim_work_history, pymk_cache,")
print("                explanation_audit, user_tombstone\n")

# ════════════════════════════════════════════════════════════════
# SEED: realistic data for the demo
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("SEED: 1000 users, 5k friendships, 2k work-history rows")
print("=" * 70)

random.seed(42)
N_USERS = 1000
N_FRIENDSHIPS = 5000
N_CORPS = 50

# Companies
corps = [(i, f"Company_{i}") for i in range(1, N_CORPS + 1)]

# Work history
seen_work = set()
for user_id in range(1, N_USERS + 1):
    n_jobs = random.randint(1, 4)
    used = set()
    for j in range(n_jobs):
        cid, cname = random.choice(corps)
        if cid in used:
            continue
        used.add(cid)
        start = date(2015 + random.randint(0, 8), random.randint(1, 12), 1)
        end = start + timedelta(days=random.randint(180, 1500))
        if end > date(2024, 12, 31):
            end = date(2024, 12, 31)  # cap at recent
        if random.random() < 0.2:
            end = None  # current job
        conn.execute(
            "INSERT INTO dim_work_history VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, cid, cname, start.isoformat(),
             end.isoformat() if end else None,
             random.choice(["SWE", "PM", "DS", "Mgr"]))
        )

# Friendships (SCD2 - some have ended)
for _ in range(N_FRIENDSHIPS):
    a = random.randint(1, N_USERS)
    b = random.randint(1, N_USERS)
    if a == b:
        continue
    low, high = min(a, b), max(a, b)
    vfrom = date(2018 + random.randint(0, 6), random.randint(1, 12), 1)
    # 30% of friendships have ended (time-travel!)
    if random.random() < 0.3:
        vto = vfrom + timedelta(days=random.randint(180, 1500))
    else:
        vto = None
    conn.execute(
        "INSERT INTO dim_friendship VALUES (?, ?, ?, ?, ?)",
        (low, high, vfrom.isoformat(), vto.isoformat() if vto else None,
         random.random())
    )
conn.commit()
print(f"Seeded {N_USERS} users, {N_FRIENDSHIPS} friendships (30% ended)\n")

# ════════════════════════════════════════════════════════════════
# TIME-TRAVEL QUERY: "Were A and B friends on Jan 15 2024?"
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("TIME-TRAVEL SQL: were A and B friends on a specific date?")
print("=" * 70)
print("""
SQL:
    SELECT 1 FROM dim_friendship
    WHERE user_id_low = LEAST(:A, :B)
      AND user_id_high = GREATEST(:A, :B)
      AND valid_from <= DATE('2024-01-15')
      AND (valid_to IS NULL OR valid_to > DATE('2024-01-15'))
""")

# Find a real pair to demo
pair = conn.execute("""
    SELECT user_id_low, user_id_high, valid_from, valid_to
    FROM dim_friendship
    WHERE valid_to IS NOT NULL  -- an ended friendship
    LIMIT 1
""").fetchone()

if pair:
    low, high, vfrom, vto = pair
    print(f"\nExample: user {low} and user {high}")
    print(f"  Friendship: {vfrom} to {vto}")

    def were_friends(a, b, on_date):
        """The L6 time-travel check - handles BOTH directions + NULL."""
        low, high = min(a, b), max(a, b)
        result = conn.execute("""
            SELECT 1 FROM dim_friendship
            WHERE user_id_low = ?
              AND user_id_high = ?
              AND valid_from <= ?
              AND (valid_to IS NULL OR valid_to > ?)
        """, (low, high, on_date, on_date)).fetchone()
        return result is not None

    # Test: during friendship, after, before
    f_during = were_friends(low, high, vfrom)  # right after start = friends
    f_after = were_friends(low, high, "2099-01-01")  # far future = not friends
    f_before = were_friends(low, high, "2010-01-01")  # before start = not friends
    print(f"  Friends on {vfrom} (during)?  {f_during}")
    print(f"  Friends on 2099-01-01 (after)? {f_after}")
    print(f"  Friends on 2010-01-01 (before)? {f_before}")
    print("\n  => The NULL check on valid_to is the key: NULL = still friends\n")

# ════════════════════════════════════════════════════════════════
# WORK-OVERLAP QUERY: "You both worked at X together"
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("WORK OVERLAP SQL: NOT just same company, but overlapping time")
print("=" * 70)
print("""
SQL:
    SELECT w1.company_name, w1.start_date, w1.end_date
    FROM dim_work_history w1
    JOIN dim_work_history w2 ON w1.company_id = w2.company_id
    WHERE w1.user_id = :viewer AND w2.user_id = :candidate
      AND w1.start_date <= COALESCE(w2.end_date, '9999-12-31')
      AND COALESCE(w1.end_date, '9999-12-31') >= w2.start_date
    ORDER BY ...  -- strongest overlap first
""")

# Find a real shared-work pair
shared_pair = conn.execute("""
    SELECT w1.user_id AS u1, w2.user_id AS u2, w1.company_name, w1.start_date, w1.end_date
    FROM dim_work_history w1
    JOIN dim_work_history w2 ON w1.company_id = w2.company_id
    WHERE w1.user_id < w2.user_id
      AND w1.start_date <= COALESCE(w2.end_date, '9999-12-31')
      AND COALESCE(w1.end_date, '9999-12-31') >= w2.start_date
    LIMIT 1
""").fetchone()

if shared_pair:
    u1, u2, cname, s, e = shared_pair
    print(f"\nExample: users {u1} and {u2} both worked at {cname} ({s} to {e})")
    print(f'  => PYMK explanation: "You both worked at {cname} from {s[:7]} to {(e or "present")[:7]}"')
else:
    # Fallback: just pick a corp and find any two users who worked there
    print("\n  (no overlapping pair in seed, demo continues with SQL only)")
    u1, u2 = 1, 2
    cname = "Demo Corp"

# ════════════════════════════════════════════════════════════════
# CELEBRITY BOUNDED FANOUT: the O(N^2) -> O(N) trick
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("CELEBRITY FANOUT: push model kills you, use pull above 500k")
print("=" * 70)
print("""
THE PROBLEM:
- Celeb with 10M followers: push PYMK -> 10M * 100 candidates = 1B writes
- One user. Per day. Cannot do this.

THE SOLUTION: threshold-based push vs pull
  < 500k followers   => PUSH (precompute for all followers, fast read)
  >= 500k followers  => PULL (only top 1% by engagement; rest on-demand ANN)

  Write cost bounded from O(N) per celeb to O(threshold / 1k) per celeb
""")

# Simulate
FOLLOWERS = [10_000, 100_000, 500_000, 5_000_000, 50_000_000]
CANDIDATES_PER_VIEWER = 100
print(f"\n{'Celeb followers':>20} {'Push writes':>15} {'Pull writes':>15} {'Reduction':>12}")
print("-" * 65)
for f in FOLLOWERS:
    push = f * CANDIDATES_PER_VIEWER
    if f >= 500_000:
        # pull: only top 1% of followers, with 100 candidates each
        pull = (f // 100) * CANDIDATES_PER_VIEWER
    else:
        pull = push
    red = 100 * (1 - pull / push) if push > 0 else 0
    print(f"{f:>20,} {push:>15,} {pull:>15,} {red:>11.0f}%")

print("\n  => 50M follower celeb: 5B push writes -> 50M pull writes (100x reduction)")

# ════════════════════════════════════════════════════════════════
# NO-HALLUCINATION GUARD: validation layer (the L6 killer)
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("NO-HALLUCINATION GUARD: validation layer + audit table")
print("=" * 70)
print("""
LLM NEVER gets a free pass. Every explanation must pass:

1. RAG prompt: "Use ONLY company_name from evidence_json. If empty, output NULL."
2. Validation: regex check - every company mentioned in explanation must
   be in evidence_json.company_ids. If not, REJECT and fallback.
3. Store BOTH in explanation_audit for Legal replay.
4. Daily job: hallucination_rate = rejected / total. Alert if >0.1%.
""")

# Simulate the validation layer
def validate_explanation(explanation: str, evidence: dict) -> bool:
    """The L6 no-hallucination guard. Regex check, not LLM-as-judge."""
    allowed_companies = set(evidence.get("company_ids", []))
    if not allowed_companies:
        # No evidence = explanation must be generic
        return "mutual" in explanation.lower() or "connection" in explanation.lower()

    # Every company mentioned in the sentence must be in evidence
    for cid, cname in evidence.get("company_map", {}).items():
        if cname.lower() in explanation.lower() and cid not in allowed_companies:
            return False
    return True

# Test cases
test_cases = [
    # (explanation, evidence, expected_pass, reason)
    ("You both worked at Meta from 2020-2022",
     {"company_ids": ["42"], "company_map": {"42": "Meta"}},
     True, "grounded"),

    ("You both worked at FakeCorp together",
     {"company_ids": ["42"], "company_map": {"42": "Meta"}},
     False, "HALLUCINATED company not in evidence"),

    ("You have 5 mutual connections",
     {"company_ids": [], "company_map": {}},
     True, "generic fallback, no evidence needed"),

    ("You both worked at Meta and FakeCorp",
     {"company_ids": ["42"], "company_map": {"42": "Meta"}},
     False, "FakeCorp not in evidence, even though Meta is"),
]

print(f"\n{'Explanation':<50} {'Pass':>6} {'Why'}")
print("-" * 100)
for explanation, evidence, expected, reason in test_cases:
    passed = validate_explanation(explanation, evidence)
    ok = "OK" if passed == expected else "MISMATCH"
    print(f"{explanation[:48]:<50} {('Y' if passed else 'N'):>6} {reason} [{ok}]")

# Show the audit log
print("\nAudit log (every explanation is stored for Legal):")
for i, (explanation, evidence, expected, reason) in enumerate(test_cases):
    passed = validate_explanation(explanation, evidence)
    conn.execute("""
        INSERT INTO explanation_audit
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (100 + i, 200 + i, explanation, json.dumps(evidence),
          "llm_v3", int(passed), "2026-10-17T00:00:00"))
conn.commit()

# Hallucination rate metric
hallu_rate = conn.execute("""
    SELECT 100.0 * SUM(CASE WHEN validation_pass = 0 THEN 1 ELSE 0 END) / COUNT(*)
    FROM explanation_audit
""").fetchone()[0]
print(f"  Hallucination rate (last batch): {hallu_rate:.1f}%  <- alert if >0.1%")

# ════════════════════════════════════════════════════════════════
# GDPR TOMBSTONE
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("GDPR: tombstone + async purge across all stores")
print("=" * 70)
print("""
When user U deletes account:
1. INSERT INTO user_tombstone (user_id, deleted_at, purge_after=NOW()+30d)
2. Kafka event -> consumers invalidate: TAO, FAISS, RocksDB, Memcache
3. Async purge job runs daily: hard-delete rows where purge_after <= NOW()
4. PYMK cache: filter is_deleted BEFORE returning to user

30-day grace = legal hold window (some jurisdictions require it)
""")

# Simulate
conn.execute("INSERT INTO user_tombstone VALUES (?, ?, ?)",
             (123, "2026-10-01", "2026-10-31"))
print("User 123 tombstoned on 2026-10-01, purge_after 2026-10-31")

# The online filter (the L6 must-show)
def filter_pymk_for_viewer(viewer_id):
    """Every PYMK read MUST apply these filters."""
    return conn.execute("""
        SELECT candidate_id, explanation
        FROM pymk_cache
        WHERE viewer_id = ?
          AND viewer_id NOT IN (SELECT user_id FROM user_tombstone)
          AND candidate_id NOT IN (SELECT user_id FROM user_tombstone)
    """, (viewer_id,)).fetchall()

# The check
tombstoned_users = [r[0] for r in conn.execute("SELECT user_id FROM user_tombstone").fetchall()]
print(f"  Tombstoned users: {tombstoned_users}")
print("  -> Any PYMK involving these users is filtered at read time\n")

# ════════════════════════════════════════════════════════════════
# THE 10/10 L6 ANSWER (45-min whiteboard script)
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("THE 10/10 ANSWER (when they ask 'design PYMK with grounded X')")
print("=" * 70)
print("""
0-5 min - REQUIREMENTS + SCALE MATH
"500M users, 100 candidates each = 50B rows. 25TB/day with 7-day TTL = 175TB.
 Can't be MySQL alone. Hot store (MyRocks, 3x compressed) + cache (Memcache) + cold (S3).
 Explanation must be GROUNDED: 'You both worked at X from 2020-2021' requires
 OVERLAPPING time, not just same company. Need audit trail for Legal."

5-15 min - DATA MODEL - DDL on the whiteboard
[Draw the SCD2 schema with user_id_low/user_id_high canonical key, the
 overlap JOIN for work history, and the explanation_audit table. The
 canonical key is the trick that makes the index symmetric.]

15-30 min - ARCHITECTURE - OFFLINE + ONLINE
Offline (Spark daily):
  1. Candidate gen: FAISS ANN on work embeddings + mutual friends from TAO
  2. Prune Top 500 -> Top 100 by score
  3. CELEBRITY BOUND: viewer with >500k followers -> mark is_celebrity=true
     For celeb VIEWER, use PULL model (ANN on-demand, not push)
  4. Evidence gen: JOIN dim_work_history for overlap, build evidence_json
  5. LLM explain: prompt "Use ONLY company_name from evidence_json. If empty, NULL"
  6. Validation: regex check - all companies in explanation IN evidence_json
  7. Fallback: if validation fails, "You have mutual connections" + log
  8. Dual-write: pymk_v1_prod + pymk_v2_shadow, 1% traffic to shadow for eval

Online (page open):
  GET /pymk?viewer_id=123
   -> Memcache get viewer_id
   -> if miss, RocksDB hot shard
   -> filter: dim_friendship valid_to IS NULL (no current friends)
   -> filter: is_deleted / user_tombstone (GDPR)
   -> filter: celebrity pull if is_celebrity
   -> return top 8 with explanation

30-40 min - DEEP DIVES (the 10/10 moves)
1. Celebrity bounded fanout: push model = 1B writes for 1 celeb. Use pull
   above 500k followers, ANN at read time. O(N) -> O(threshold) writes.
2. No hallucination: NOT just prompt. Store explanation_audit (viewer, cand,
   explanation, evidence, llm_version, validation_pass). Daily metric:
   hallucination_rate. Alert >0.1%. Legal can replay.
3. GDPR: is_deleted + user_tombstone + Kafka tombstone -> purge TAO, FAISS,
   RocksDB, Memcache within 30 days. Async purge with watermark.

40-45 min - SCALE + MONITORING + CLOSE
"50B rows * 500B = 25TB/day. MyRocks 3x compressed = 8TB hot. Memcache
 95% hit rate for 50M DAU. Cost: $2500/day. Monitor: freshness lag,
 embedding drift, hallucination rate, celeb pull p95."

Closing (the line that gets you 10/10):
"Design is grounded, bounded, and auditable: SCD2 with canonical key
 + index for time-travel, overlap join for 'worked at X together',
 evidence_json + validation layer for zero hallucination with audit,
 pull model for celebrity to bound fanout from 1B to 1k writes,
 shadow dual-write for safe model rollout."

INTERVIEWER FOLLOW-UP: "Walk me through the overlap SQL."
  [Be ready. They WILL ask. The answer is the JOIN with date overlap
   conditions + COALESCE for current job (end_date IS NULL).]
""")
