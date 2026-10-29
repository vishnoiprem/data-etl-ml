# Day 5 — SQL and Persistence
**Module 5** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
A database is a **filing cabinet**.
- Each drawer is a table.
- Each folder is a row.
- The **index** is the label on the front of each drawer so you can find a folder without flipping every page.

Without indexes, every search flips through the whole cabinet. With indexes, you jump straight to the drawer.

---

## 2. Technical concepts (20 min)

SQL is a **declarative language**: you say *what* you want, not *how*. The query planner picks the strategy.

### Indexes
- B-tree index: speeds up equality and range.
- Composite index: matches queries that filter/sort on its leading columns.
- An index is a **copy** of the data, sorted differently — writes pay for it.

### Transactions (ACID)
Atomic, Consistent, Isolated, Durable. SQLite default is autocommit-ish; we use explicit `conn.commit()`.

### Parameterized queries
Always use `?` placeholders. String concatenation = SQL injection.

### Connection management
Open, do work, commit-or-rollback, close. Use a context manager.

---

## 3. Coding (30 min)

Open `backend/app/database.py` and read `init_db()`. Add an extra index that supports the day filter:

```python
cur.execute(
    "CREATE INDEX IF NOT EXISTS idx_traces_day "
    "ON traces(substr(created_at, 1, 10))"
)
```

Then write a function `count_by_prompt_version() -> list[dict]` in `backend/app/routes/traces.py`:

```python
@router.get("/stats/by-prompt-version")
def stats_by_pv():
    with db_cursor() as cur:
        rows = cur.execute(
            "SELECT prompt_version, COUNT(*) AS c, "
            "AVG(latency_ms) AS avg_latency "
            "FROM traces GROUP BY prompt_version"
        ).fetchall()
    return [dict(r) for r in rows]
```

### Sample I/O
```bash
curl http://localhost:8000/traces/stats/by-prompt-version
# [{"prompt_version":"v1.0","c":2512,"avg_latency":1200.4}, ...]
```

### Line-by-line
- `GROUP BY prompt_version` — one row per version.
- `AVG(latency_ms)` — aggregate function. SQLite returns a float.
- `dict(r)` — convert `sqlite3.Row` to a JSON-able dict.

---

## 4. Debugging & tests (20 min)

### Bug 1: N+1
```python
for tid in ids:
    cur.execute("SELECT * FROM traces WHERE trace_id=?", (tid,))
```
**Fix:** `WHERE trace_id IN (?, ?, ?)`.

### Bug 2: Wrong index used
**Fix:** `EXPLAIN QUERY PLAN` and look for `SCAN` vs `SEARCH ... USING INDEX`.

### Bug 3: Timezone confusion
Store UTC, format on display.

### Test
```python
def test_stats_by_pv(client, seed):
    r = client.get("/traces/stats/by-prompt-version")
    body = r.json()
    assert {b["prompt_version"] for b in body} == {"v1.0", "v1.1", "v1.2"}
    assert all(b["c"] > 0 for b in body)
```

---

## 5. Mock interview practice (20 min)

**Q1 — "What's a composite index?"**
> An index on multiple columns. Order matters.

**Q2 — "What is WAL?"**
> Write-Ahead Log. Readers see a snapshot; writers append.

**Q3 — "Why ON CONFLICT?"**
> Idempotent upsert — INSERT or UPDATE on conflict.

**Q4 — "WHERE vs HAVING?"**
> WHERE filters rows; HAVING filters groups.

**Q5 — "When do you denormalize?"**
> When reads vastly outnumber writes and joins are hot.

---

## 6. Success criteria check
- [ ] I can read and write a parameterized query.
- [ ] I can use `EXPLAIN QUERY PLAN`.
- [ ] I can write a GROUP BY.
- [ ] I can manage a connection safely.
- [ ] I can write a test for a query.

## 7. Grade yourself 0–10
| Area | Score |
|---|---|
| Correctness | /10 |
| Code quality | /10 |
| Debugging | /10 |
| API design | /10 |
| Frontend implementation | /10 |
| Performance | /10 |
| Testing | /10 |
| Communication | /10 |
| **Total** | **/80** |

## 8. Coding assignment
**Add `GET /traces/stats/errors` returning error counts per prompt version.**

### Rubric (0–10)
- 0: doesn't run
- 4: returns counts
- 6: filters status='error'
- 8: indexed
- 10: returns P95 latency per version for errors only

### Solution
```python
@router.get("/stats/errors")
def error_stats():
    with db_cursor() as cur:
        rows = cur.execute(
            "SELECT prompt_version, COUNT(*) AS c "
            "FROM traces WHERE status='error' "
            "GROUP BY prompt_version"
        ).fetchall()
    return [dict(r) for r in rows]
```

**Time: 90 min**