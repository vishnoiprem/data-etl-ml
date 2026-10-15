# Day 5 — SQL and Persistence

## 1. Analogy
A database is a **filing cabinet**. Each drawer is a table. Each folder is a row. The **index** is the label on the front of each drawer so you can find a folder without flipping through every page.

## 2. Technical concept
SQL is a **declarative language**: you say *what* you want, not *how*. The query planner picks the strategy.

### Indexes
- A B-tree index speeds up equality and range queries.
- A composite index helps queries that filter/sort on its leading columns.
- An index is a **copy** of the data, sorted differently — it's not free (write cost).

### Transactions
ACID: **A**tomic, **C**onsistent, **I**solated, **D**urable. SQLite's default mode is autocommit-ish; we use `conn.commit()` explicitly.

### Parameterized queries
Always use `?` placeholders. String concatenation is **SQL injection**.

## 3. Why this problem exists
Without indexes, every query is a full table scan. Without transactions, partial writes corrupt data. Without parameterization, attackers steal the database.

## 4. Data flow
API → SQL with placeholders → SQLite planner → B-tree lookup → rows → Pydantic → JSON → client

## 5. Example
```python
with db_cursor(commit=True) as cur:
    cur.execute(
        "INSERT INTO traces(trace_id, created_at, prompt_version, user_query, prompt, retrieved_chunks, model_response, citations, token_usage, latency_ms) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (tid, ts, pv, q, p, rc, mr, cits, tu, lat),
    )
```

## 6. Line-by-line
- `?` placeholders. The DB driver escapes the values for us.
- `commit=True` flushes the transaction.

## 7. I/O
- Insert returns `cursor.lastrowid`.
- `SELECT *` returns all rows; for huge tables use `LIMIT`.

## 8. Bugs
- **N+1** — looping a query for each row. Use `IN (?, ?, ?)`.
- **Wrong index** — query uses `idx_latency` instead of the composite. Check with `EXPLAIN QUERY PLAN`.
- **Timezone confusion** — store UTC, format on display.

## 9. Tests
```python
def test_index_used():
    plan = cur.execute("EXPLAIN QUERY PLAN SELECT * FROM traces ORDER BY created_at DESC, trace_id DESC LIMIT 50").fetchall()
    assert "idx_traces_created_id" in str(plan)
```

## 10. Performance
- Index lookup O(log n) vs full scan O(n).
- `journal_mode=WAL` lets readers and writers not block.
- `EXPLAIN` your slow queries.

## 11. Five Q&As
1. **What's a composite index?** An index on multiple columns.
2. **What is WAL?** Write-Ahead Log — readers see the snapshot at start; writers append.
3. **Why `ON CONFLICT`?** Idempotent upsert.
4. **What's the difference between `WHERE` and `HAVING`?** WHERE filters rows; HAVING filters groups.
5. **When to denormalize?** When reads vastly outnumber writes and joins are hot.

## 12. Coding assignment
Add a `status='error'` index and write a query that counts errors per prompt_version.

## 13. Solution
```python
cur.execute("CREATE INDEX IF NOT EXISTS idx_traces_status_pv ON traces(status, prompt_version)")
cur.execute("SELECT prompt_version, COUNT(*) FROM traces WHERE status='error' GROUP BY prompt_version")
```
- 0: doesn't run
- 4: returns counts
- 6: uses index
- 8: includes v1.0, v1.1, v1.2, v2.0 even when count=0
- 10: returns P95 latency per version

**Time: 90 min**