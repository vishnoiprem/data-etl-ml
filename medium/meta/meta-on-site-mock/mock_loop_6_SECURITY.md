# LOOP 6: Security + ACL + PII + GDPR

**Theme:** Private docs, no leak, GDPR compliance
**Total Duration:** 3 hours 15 min
**Difficulty:** Hard (P0 incident risk if wrong)

---

## Architecture Diagram (Master)

```
┌────────────────────────────────────────────────────────────────────┐
│     SECURE WORKPLACE SEARCH - ACL + PII + GDPR                     │
└────────────────────────────────────────────────────────────────────┘

INGEST PATH (with PII scrubbing + ACL tagging)
──────────────────────────────────────────────

Source Doc ──▶ PII Scrubber (Presidio) ──▶ Embed ──▶ Qdrant
                      │                              │
                      ▼                              ▼
              ┌──────────────┐              ┌──────────────────┐
              │ pii_scrub_log│              │ payload:         │
              │ audit trail  │              │  - team_id       │
              └──────────────┘              │  - is_private    │
                                            │  - is_pii        │
                                            └──────────────────┘

QUERY PATH (ACL filter BEFORE LLM)
───────────────────────────────────

User query
    │
    ▼
┌────────────────────────────┐
│ ACL filter on Qdrant       │ ◀── SAVES COST, prevents leak
│ WHERE team_id IN user_teams│
└────────────┬───────────────┘
             │ Top 20
             ▼
       LLM with filtered chunks only
             │
             ▼
       Grounded answer
             │
             ▼
       Audit log:
       - user_id
       - doc_ids accessed
       - permission used
       - timestamp

GDPR DELETE PATH (5-min SLA)
────────────────────────────

User requests delete
        │
        ▼
GDPR Flink job (per user_id)
        │
        ├─▶ Qdrant: DELETE points WHERE user_id=X
        ├─▶ Postgres: DELETE FROM documents WHERE user_id=X
        ├─▶ S3: DeleteObjects batch
        ├─▶ ClickHouse: ALTER TABLE traces DELETE WHERE user_id=X
        │
        ▼
gdpr_audit row: (user_id, action, target, completed_at)
        │
        ▼
Notification to user + security team
```

---

## Greet (15 min)

### Q1: How do you handle private repos/docs in RAG?

**L6 Answer (60 sec):**

> "Three layers, all enforced server-side:
>
> 1. **Ingestion:** Mark every doc with `team_id` and `is_private` boolean. This happens at parse time, before embedding.
>
> 2. **Retrieval:** Filter by `team_id IN user_teams` **BEFORE** the LLM call. This is critical — filtering after the LLM means the private content reached the model, even if not shown to the user. Filter at the vector store level (Qdrant payload filter), not in Python.
>
> 3. **Audit:** Every access is logged with `user_id`, `doc_ids`, `permission_used`. Suspicious patterns (e.g., user accessing 100 private docs in 1 hour) trigger alerts.
>
> Why filter before LLM? It saves LLM cost (smaller context) AND prevents three real leak vectors: (1) PII leak in retrieved context if an unauthorized user gets through, (2) prompt injection where a malicious chunk hijacks the model, (3) training data extraction where leaked content ends up in fine-tunes. Filter at the storage layer, not in Python."

**L6 Keywords:** three layers, filter BEFORE LLM, audit log, defense in depth.

---

### Q2: Tell me about GDPR delete you owned

**L6 STAR (75 sec):**

**S:** User requested GDPR delete. Their data spread across Qdrant (20 shards), Postgres, S3, ClickHouse traces. 5-min rollback SLA, complex because of shards.

**T:** Delete everywhere within 5 minutes, full audit trail.

**A:**
1. Wrote GDPR delete Flink job triggered by user request
2. Scans Qdrant by `user_id` filter, deletes matching points from all 20 shards in parallel
3. `DELETE FROM documents WHERE user_id=X` in Postgres
4. S3 `DeleteObjects` API call with batch of 1000 keys
5. ClickHouse `ALTER TABLE traces DELETE WHERE user_id=X` (async)
6. Writes `gdpr_audit(user_id, action, target, completed_at)` row
7. Tested with 1M docs: completed in 12 minutes

**R:** 100% deletion verified, full audit trail, 12 min vs 5-day SLA. Used for 50+ requests since. SOC2 audit passed.

---

## AI-Native DE Full Stack (60 min)

### Q1 Data Model (15 min)

```
┌────────────────────────────────────────────────────────────────┐
│           ACL + PII + GDPR DATA MODEL                          │
└────────────────────────────────────────────────────────────────┘

repos                          repo_acl
┌────────────────────────┐     ┌────────────────────────────┐
│ repo_id        PK      │◀───▶│ repo_id     FK             │
│ name                   │ 1:N │ user_id     FK             │
│ is_private  BOOL       │     │ permission                │
│ team_id                │     │   'read'|'write'|'admin'  │
│ created_at             │     │ granted_at  TIMESTAMP     │
└────────────────────────┘     │ granted_by  BIGINT         │
                               └────────────────────────────┘

documents                       traces
┌────────────────────────┐     ┌────────────────────────────┐
│ doc_id         PK      │◀───▶│ trace_id      PK           │
│ repo_id        FK      │ 1:N │ user_id                   │
│ content                │     │ doc_id       FK            │
│ team_id                │     │ permission_used            │
│ is_private  BOOL       │     │ accessed_at TIMESTAMP      │
│ is_pii      BOOL       │     │ query_hash                 │
│ pii_types   ARRAY      │     └────────────────────────────┘
│ uploaded_by            │
│ created_at             │     pii_scrub_log
└────────────────────────┘     ┌────────────────────────────┐
                               │ scrub_id    PK             │
                               │ doc_id      FK             │
                               │ original_text              │
                               │ scrubbed_text              │
                               │ pii_found  ARRAY           │
                               │ scrubber_version           │
                               │ scrubbed_at                │
                               └────────────────────────────┘

gdpr_audit
┌────────────────────────────┐
│ audit_id    PK             │
│ user_id                    │
│ action  'gdpr_delete'|...  │
│ target  system names       │
│ completed_at               │
│ requested_at               │
│ sla_met   BOOL             │
└────────────────────────────┘
```

**SQL schema:**

```sql
CREATE TABLE repos (
  repo_id      BIGINT PRIMARY KEY,
  name         STRING NOT NULL,
  is_private   BOOLEAN DEFAULT FALSE,
  team_id      BIGINT,
  created_at   TIMESTAMP
);

CREATE TABLE repo_acl (
  repo_id      BIGINT REFERENCES repos(repo_id),
  user_id      BIGINT,
  permission   STRING,  -- 'read', 'write', 'admin'
  granted_at   TIMESTAMP,
  granted_by   BIGINT,
  PRIMARY KEY (repo_id, user_id)
);

CREATE TABLE documents (
  doc_id       BIGINT PRIMARY KEY,
  repo_id      BIGINT REFERENCES repos(repo_id),
  content      STRING,
  team_id      BIGINT,
  is_private   BOOLEAN DEFAULT FALSE,
  is_pii       BOOLEAN DEFAULT FALSE,
  pii_types    ARRAY<STRING>,  -- ['email', 'ssn', 'phone']
  uploaded_by  BIGINT,
  created_at   TIMESTAMP
);

CREATE TABLE pii_scrub_log (
  scrub_id         BIGINT PRIMARY KEY,
  doc_id           BIGINT REFERENCES documents(doc_id),
  original_text    STRING,
  scrubbed_text    STRING,
  pii_found        ARRAY<STRING>,
  scrubber_version STRING,
  scrubbed_at      TIMESTAMP
);

CREATE TABLE gdpr_audit (
  audit_id      BIGINT PRIMARY KEY,
  user_id       BIGINT,
  action        STRING,
  target        STRING,  -- 'all_systems', 'qdrant_only', etc.
  completed_at  TIMESTAMP,
  requested_at  TIMESTAMP,
  sla_met       BOOLEAN
);
```

---

### Q2 Pipeline (15 min) - PII Scrubbing + GDPR Delete

```
┌────────────────────────────────────────────────────────────────┐
│          PII SCRUBBING + GDPR DELETE PIPELINE                  │
└────────────────────────────────────────────────────────────────┘

INGEST
──────

Document Upload
      │
      ▼
┌──────────────────────┐
│ PII Scrubber Worker  │
│ ──────────────────── │
│ 1. Presidio analyzer │
│ 2. Regex backup:     │
│    - email regex     │
│    - SSN \d{3}-\d{2}-\d{4}│
│    - phone regex     │
│ 3. Replace PII with  │
│    [EMAIL], [SSN]    │
└──────────┬───────────┘
           │ scrubbed text + pii_found
           ▼
┌──────────────────────┐
│ Embed with team_id   │
│ in Qdrant payload    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ pii_scrub_log row    │  (audit trail)
└──────────────────────┘

GDPR DELETE
───────────

User requests delete
      │
      ▼
┌──────────────────────────────┐
│ GDPR Delete Flink Job        │
│ ──────────────────────────── │
│ 1. Qdrant: scroll + delete  │
│    by user_id filter,        │
│    20 shards in parallel     │
│ 2. Postgres: DELETE WHERE   │
│    uploaded_by=user_id       │
│ 3. S3: DeleteObjects batch   │
│ 4. ClickHouse: ALTER TABLE  │
│    traces DELETE            │
│ 5. gdpr_audit: log completion│
└──────────────────────────────┘
```

**Pseudocode for the Flink job:**

```python
# Triggered by Kafka message on 'gdpr_request' topic
def gdpr_delete_user(user_id: int):
    deleted_count = {"qdrant": 0, "postgres": 0, "s3": 0, "clickhouse": 0}

    # 1. Qdrant - delete across all shards in parallel
    for shard in range(20):
        qdrant_client.delete(
            collection_name="documents",
            points_selector=models.FilterSelector(
                filter=models.Filter(must=[
                    models.FieldCondition(
                        key="uploaded_by",
                        match=models.MatchValue(value=user_id)
                    )
                ])
            ),
            shard=shard
        )
    deleted_count["qdrant"] = count_for_user(user_id)

    # 2. Postgres
    result = postgres.execute(
        "DELETE FROM documents WHERE uploaded_by = %s", (user_id,)
    )
    deleted_count["postgres"] = result.rowcount

    # 3. S3 batch delete
    keys = list_s3_keys_for_user(user_id)
    for batch in chunks(keys, 1000):
        s3.delete_objects(Bucket="docs", Delete={"Objects": batch})
    deleted_count["s3"] = len(keys)

    # 4. ClickHouse (async)
    clickhouse.execute(
        f"ALTER TABLE traces DELETE WHERE user_id = {user_id}"
    )

    # 5. Audit
    audit_log(user_id, "gdpr_delete", deleted_count)

    # 6. Notification
    notify_user_and_security(user_id, deleted_count)
```

---

### Q3 SQL (15 min) - ACL Audit + PII Leak Rate

**ACL audit: which users accessed private docs (and how many):**

```sql
SELECT
  t.user_id,
  COUNT(DISTINCT t.doc_id)  AS private_docs_accessed,
  COUNT(DISTINCT t.permission_used) AS unique_permissions,
  MIN(t.accessed_at)        AS first_access,
  MAX(t.accessed_at)        AS last_access,
  COUNT(*)                  AS total_traces
FROM traces t
JOIN documents d ON t.doc_id = d.doc_id
JOIN repo_acl a ON d.repo_id = a.repo_id AND t.user_id = a.user_id
WHERE d.is_private = TRUE
  AND t.permission_used = 'read'
  AND t.accessed_at >= NOW() - INTERVAL '30' DAY
GROUP BY t.user_id
HAVING COUNT(DISTINCT t.doc_id) > 100    -- suspicious threshold
ORDER BY private_docs_accessed DESC;
```

**PII leak rate: still has PII after scrubbing:**

```sql
SELECT
  DATE_TRUNC('day', scrubbed_at) AS day,
  COUNT(*) AS total_scrubbed,
  SUM(CASE WHEN still_has_pii THEN 1 ELSE 0 END) AS leaks,
  ROUND(
    100.0 * SUM(CASE WHEN still_has_pii THEN 1 ELSE 0 END) / COUNT(*),
    2
  ) AS leak_rate_pct,
  ARRAY_AGG(DISTINCT pii_found[0]) AS leak_types
FROM (
  SELECT
    scrub_id,
    scrubbed_at,
    pii_found,
    -- Re-check if PII patterns still in scrubbed text
    (scrubbed_text ~* '[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}'
     OR scrubbed_text ~* '\b\d{3}-\d{2}-\d{4}\b'
     OR scrubbed_text ~* '\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
    ) AS still_has_pii
  FROM pii_scrub_log
  WHERE scrubbed_at >= NOW() - INTERVAL '7' DAY
) checks
GROUP BY DATE_TRUNC('day', scrubbed_at)
ORDER BY day DESC;
```

**Alert:** leak_rate_pct > 1% → page security team (PII leak = P0).

---

### Q4 Coding (15 min) - ACL Filter + PII Scrubber + GDPR Delete

```python
import re
from typing import List, Dict, Tuple
from qdrant_client import models

PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "ssn":   r"\b\d{3}-\d{2}-\d{4}\b",
    "phone": r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "cc":    r"\b(?:\d[ -]*?){13,16}\b",
}


def scrub_pii(text: str) -> Tuple[str, List[str]]:
    """
    Returns (scrubbed_text, pii_types_found).
    Replaces PII with tokens like [EMAIL], [SSN], [PHONE].
    Audit trail preserved in pii_scrub_log.
    """
    pii_found = []
    scrubbed = text
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, scrubbed)
        if matches:
            pii_found.append(pii_type)
            scrubbed = re.sub(pattern, f"[{pii_type.upper()}]", scrubbed)
    return scrubbed, pii_found


def acl_filter_before_llm(user_id: int, candidate_chunks: List[Dict]) -> List[Dict]:
    """
    Filter chunks by ACL BEFORE LLM call.
    Saves cost (smaller context) AND prevents leak via embeddings.
    Raises SecurityError if a private chunk would have been returned
    (for audit purposes).
    """
    user_teams = get_user_teams(user_id)  # cache: SET team_id WHERE user_id=X

    filtered = []
    blocked = []
    for chunk in candidate_chunks:
        if chunk["is_private"] and chunk["team_id"] not in user_teams:
            blocked.append(chunk["doc_id"])
            continue
        filtered.append(chunk)

    if blocked:
        # Audit log: tried to access private docs
        log_blocked_access(user_id, blocked)

    return filtered


def gdpr_delete_user(user_id: int) -> Dict[str, int]:
    """
    Delete all user data across Qdrant, Postgres, S3, ClickHouse.
    SLA: 5 minutes for 1M docs.
    """
    counts = {"qdrant": 0, "postgres": 0, "s3": 0, "clickhouse": 0}

    # 1. Qdrant - delete across all shards
    qdrant.delete(
        collection_name="documents",
        points_selector=models.FilterSelector(
            filter=models.Filter(must=[
                models.FieldCondition(
                    key="uploaded_by",
                    match=models.MatchValue(value=user_id)
                )
            ])
        )
    )

    # 2. Postgres
    result = postgres.execute(
        "DELETE FROM documents WHERE uploaded_by = %s", (user_id,)
    )
    counts["postgres"] = result.rowcount

    # 3. S3 batch delete
    keys = list_s3_keys_for_user(user_id)
    for batch in chunks(keys, 1000):
        s3.delete_objects(Bucket="user-docs", Delete={"Objects": batch})
    counts["s3"] = len(keys)

    # 4. ClickHouse (async, eventually consistent)
    clickhouse.execute(f"ALTER TABLE traces DELETE WHERE user_id = {user_id}")

    # 5. Audit
    audit_log(user_id, "gdpr_delete", counts)
    return counts


# Example: query path with ACL filter
def query_rag(user_id: int, query_text: str) -> dict:
    # 1. Embed query
    query_emb = embed(query_text)

    # 2. Qdrant search (with team_id filter at storage layer)
    user_teams = get_user_teams(user_id)
    raw_results = qdrant.search(
        collection_name="documents",
        query_vector=query_emb,
        query_filter=models.Filter(should=[
            models.FieldCondition(key="team_id", match=models.MatchAny(any=list(user_teams))),
            models.FieldCondition(key="is_private", match=models.MatchValue(value=False))
        ]),
        limit=20,
    )

    # 3. Defense in depth: Python-level ACL check
    safe_results = acl_filter_before_llm(user_id, raw_results)

    # 4. LLM with only safe chunks
    answer = llm_generate(query_text, safe_results)

    # 5. Audit
    audit_log(
        user_id=user_id,
        action="rag_query",
        doc_ids=[r["doc_id"] for r in safe_results],
        n_chunks=len(safe_results),
    )

    return answer
```

---

## Sr Tech Design (60 min) - Secure Workplace Search

```
┌────────────────────────────────────────────────────────────────┐
│          SECURE WORKPLACE SEARCH - 100M DOCS                   │
└────────────────────────────────────────────────────────────────┘

KEY DESIGN PRINCIPLES
─────────────────────
1. ACL filter at STORAGE layer (Qdrant payload filter), not in Python
2. PII scrubbed at INGEST, never reaches embeddings
3. Audit log every access
4. GDPR delete parallel across all systems
5. Defense in depth: filter at storage + Python check + LLM prompt

ARCHITECTURE
────────────

INGEST
──────
Doc → PII scrub (Presidio + regex) → is_pii=true, pii_types=[...]
   → Embed (text-embedding-3-large)
   → Qdrant payload: {team_id, is_private, is_pii, uploaded_by}
   → pii_scrub_log (audit)

QUERY (p95 < 500ms)
───────────────────
User query → embed → Qdrant search:
  query_filter: WHERE team_id IN user_teams OR is_private=false
  limit 20
  → Python ACL check (defense in depth)
  → LLM answer (only safe chunks)
  → audit_log (user_id, doc_ids, timestamp)

GDPR DELETE (5-min SLA)
───────────────────────
User request → Flink job → parallel delete:
  - Qdrant: 20 shards, DELETE by user_id filter
  - Postgres: DELETE WHERE uploaded_by=X
  - S3: DeleteObjects batch
  - ClickHouse: ALTER TABLE traces DELETE
  → gdpr_audit row
  → notify user + security

NO EMBEDDING LEAK
─────────────────
Even if attacker queries without auth:
  Qdrant filter rejects if team_id not authorized
  Embeddings never returned to client
  Original doc text never returned
  Only LLM answer (which had no PII chunks) returned

AUDIT TRAIL
───────────
Every access logged:
  (user_id, doc_ids, permission_used, timestamp, query_hash)
Retention: 1 year for compliance
Suspicious patterns:
  - User accesses >100 private docs/hour → alert
  - Cross-team access attempt → alert + block
```

---

## Sr Ownership (30 min)

### Q1: Security incident you owned

**L6 STAR (75 sec):**

**S:** Audit log caught that a user NOT on the engineering team retrieved 3 private engineering docs. P0 incident.

**T:** Patch ACL bug, audit all users, prevent recurrence.

**A:**
1. **Root cause:** ACL filter was AFTER LLM call, not before. Private chunks leaked into LLM context, then into response.
2. **Immediate patch:** Moved ACL filter to Qdrant query layer (storage-side).
3. **Audit:** Searched last 30 days traces for similar leaks. Found 12 users got 3 private docs each = 36 leaked docs.
4. **Notification:** Notified security team + affected doc owners + GDPR officer.
5. **GDPR:** Since leaked doc owners were EU users, filed GDPR breach notification within 72 hours.
6. **Prevent:** Added test — every private doc must NOT be retrievable by non-team users. CI gate fails if missing.

**R:** 100% patched in 24h, full audit completed in 72h, GDPR compliant, security team happy. Retro ran.

**Lesson:** filter at the lowest layer, never trust application code alone.

---

### Q2: Time you said no due to privacy

**L6 STAR (60 sec):**

**S:** PM wanted to log full query text for 30 days for analytics.

**T:** Push back on privacy grounds.

**A:**
1. Showed PM: queries contain PII (SSN, email when users ask "what's the policy on SSN 123-45-6789?"). Logs full text = GDPR violation.
2. Proposed alternative: log `query_hash` (SHA256), not text. Store query text 24h hot for debugging, then drop.
3. Aggregated statistics (query length, topic) kept for 30 days with PII scrubbed.
4. PM agreed.

**R:** Privacy compliant, analytics still work, avoided potential GDPR fines (up to 4% of global revenue). Privacy by design.

---

## Full Stack (60 min) - ACL Debugger

```tsx
import { useState } from "react";

const ACLDebugger = () => {
  const [docId, setDocId] = useState("");
  const [userId, setUserId] = useState("");
  const [testUserId, setTestUserId] = useState("");
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  const checkACL = async (uid = userId) => {
    const res = await fetch(
      `/api/acl/check?doc_id=${docId}&user_id=${uid}`
    );
    const data = await res.json();
    setResult(data);
    setHistory(h => [{ ...data, checked_at: new Date() }, ...h.slice(0, 9)]);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">ACL Debugger</h1>

      {/* Input */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium mb-1">Document ID</label>
          <input
            value={docId}
            onChange={e => setDocId(e.target.value)}
            placeholder="doc_12345"
            className="w-full border p-2 rounded"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">User ID</label>
          <input
            value={userId}
            onChange={e => setUserId(e.target.value)}
            placeholder="user_678"
            className="w-full border p-2 rounded"
          />
        </div>
      </div>

      <button
        onClick={() => checkACL()}
        className="bg-blue-500 text-white px-4 py-2 rounded mb-6"
      >
        Check ACL
      </button>

      {/* Result */}
      {result && (
        <div className={`p-4 mb-6 rounded ${
          result.allowed ? "bg-green-100 border-green-500" : "bg-red-100 border-red-500"
        } border-l-4`}>
          <h2 className="text-lg font-bold mb-2">
            {result.allowed ? "✓ ALLOWED" : "✗ DENIED"}
          </h2>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <strong>Document:</strong>
              <ul className="mt-1 space-y-1">
                <li>doc_id: <code>{result.doc.doc_id}</code></li>
                <li>team_id: <code>{result.doc.team_id}</code></li>
                <li>is_private: <code>{result.doc.is_private ? "true" : "false"}</code></li>
                <li>is_pii: <code>{result.doc.is_pii ? "true" : "false"}</code></li>
                {result.doc.pii_types?.length > 0 && (
                  <li>pii_types: <code>{result.doc.pii_types.join(", ")}</code></li>
                )}
              </ul>
            </div>
            <div>
              <strong>User:</strong>
              <ul className="mt-1 space-y-1">
                <li>user_id: <code>{result.user.user_id}</code></li>
                <li>teams: <code>{result.user.teams?.join(", ") || "[]"}</code></li>
                <li>permission: <code>{result.permission || "none"}</code></li>
              </ul>
            </div>
          </div>

          {result.reason && (
            <div className="mt-3 text-sm">
              <strong>Reason:</strong> {result.reason}
            </div>
          )}

          {/* Test as user */}
          <div className="mt-4 pt-4 border-t">
            <label className="block text-sm font-medium mb-1">
              Test as different user:
            </label>
            <div className="flex gap-2">
              <input
                value={testUserId}
                onChange={e => setTestUserId(e.target.value)}
                placeholder="user_999"
                className="flex-1 border p-2 rounded"
              />
              <button
                onClick={() => checkACL(testUserId)}
                className="bg-gray-500 text-white px-3 py-2 rounded"
              >
                Test
              </button>
            </div>
          </div>
        </div>
      )}

      {/* History */}
      <h2 className="text-lg font-semibold mb-2">Check History</h2>
      <table className="w-full border-collapse text-sm">
        <thead className="bg-gray-100">
          <tr>
            <th className="border p-2">Time</th>
            <th className="border p-2">User</th>
            <th className="border p-2">Result</th>
            <th className="border p-2">Reason</th>
          </tr>
        </thead>
        <tbody>
          {history.map((h, i) => (
            <tr key={i}>
              <td className="border p-2">{h.checked_at.toLocaleTimeString()}</td>
              <td className="border p-2">{h.user.user_id}</td>
              <td className="border p-2">
                <span className={h.allowed ? "text-green-600" : "text-red-600"}>
                  {h.allowed ? "Allowed" : "Denied"}
                </span>
              </td>
              <td className="border p-2">{h.reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

---

## Day 4 Checkpoint

Before moving on, can you:
- [ ] Explain **why ACL filter must be BEFORE LLM** (cost + leak)?
- [ ] Design **GDPR delete** across Qdrant + Postgres + S3 + ClickHouse?
- [ ] Write **PII leak detection SQL** with regex re-check?
- [ ] Code `scrub_pii`, `acl_filter_before_llm`, `gdpr_delete_user`?
- [ ] Draw the **secure search** flow with audit at every step?

If yes to all 5, you're ready for Loop 7.
