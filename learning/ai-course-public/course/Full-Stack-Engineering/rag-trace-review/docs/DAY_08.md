# Day 8 — Cursor Pagination (Deep Dive)
**Module 8** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
Reading a book with **bookmarks** is cursor pagination. **Re-counting pages from the start** every time is OFFSET. Bookmarks are faster but you can't jump to chapter 7 without re-walking. With 10,000 pages, OFFSET is a slog; with 1,000,000 it's impossible.

---

## 2. Technical concepts (20 min)

A cursor is an **opaque pointer to a position in a sorted sequence**. Given a sort key `(created_at, trace_id)`, the cursor encodes the last seen values. The next query becomes:

```sql
WHERE (created_at, trace_id) < (cursor.created_at, cursor.trace_id)
ORDER BY ... LIMIT n+1
```

### Why
- OFFSET scans and discards rows → O(n).
- Cursor walks the index → O(log n + page_size).
- OFFSET is unstable when rows are inserted.

### Composite cursor
- Sort key: `created_at`.
- Tie-breaker: `trace_id`.

### The `limit + 1` trick
Ask for one extra row. If you get it, there's a next page; drop the extra and emit `next_cursor`.

### Stability
- Inserts: new rows may appear on the next page (acceptable for traces).
- Deletes: rows disappear (acceptable).
- Updates: same row may re-appear (we never update `created_at` or `trace_id`).

---

## 3. Coding (30 min)

Open `backend/app/routes/traces.py`. Read `_encode_cursor`, `_decode_cursor`, and the WHERE-clause builder. Write a unit test for the boundary cases:

```python
def test_cursor_walks_all_rows(client, seed):
    seen = []
    cursor = None
    while True:
        url = "/traces?limit=1"
        if cursor:
            url += f"&cursor={cursor}"
        body = client.get(url).json()
        seen.extend(i["trace_id"] for i in body["items"])
        if not body["meta"]["has_more"]:
            break
        cursor = body["meta"]["next_cursor"]
    assert seen == ["t003", "t002", "t001"]
    assert len(set(seen)) == len(seen)  # no duplicates
```

### Sample I/O
- First page: `{"items":[t003], "meta":{"next_cursor":"abc", "has_more":true}}`
- Second page: `{"items":[t002], "meta":{"next_cursor":"def", "has_more":true}}`
- Third page: `{"items":[t001], "meta":{"next_cursor":null, "has_more":false}}`

### Line-by-line
- `seen.extend` flattens all pages into one list.
- `assert len(set(seen)) == len(seen)` checks for duplicates.

---

## 4. Debugging & tests (20 min)

### Bug 1: duplicate rows
**Cause:** missing tie-breaker on `trace_id`.
**Fix:** use `(created_at, trace_id)` as the sort key.

### Bug 2: skipping rows
**Cause:** `>` instead of `<` for DESC order, or forgetting to flip when ordering asc.
**Fix:** careful, manual trace through the index.

### Bug 3: `next_cursor` even when `has_more=False`
**Fix:** only set `next_cursor` when `has_more` is True.

### Bug 4: invalid cursor → 500
**Fix:** wrap `_decode_cursor` in try/except and raise 400.

---

## 5. Mock interview practice (20 min)

**Q1 — "Why not offset 0?"**
> Slow on large tables.

**Q2 — "Why opaque?"**
> We can change format without breaking clients.

**Q3 — "What if rows are deleted mid-walk?"**
> Cursor skips them. That's fine for traces.

**Q4 — "What if rows are inserted?"**
> Cursor may show new rows on the next page. Acceptable.

**Q5 — "Can you jump to page 7?"**
> No. Walk from start.

---

## 6. Success criteria check
- [ ] I can explain keyset vs OFFSET.
- [ ] I can write the WHERE clause for the next page.
- [ ] I can encode/decode an opaque cursor.
- [ ] I can test pagination boundaries.
- [ ] I can debug the 4 bugs above.

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
**Add a `?sort=latency_desc` query param that orders by `latency_ms DESC, trace_id DESC`.**

### Rubric (0–10)
- 0: doesn't compile
- 4: sorts
- 6: accepts `latency_asc`
- 8: works with cursor
- 10: indexed + tested for ties

### Solution
```python
sort = Query("created_at_desc", regex="^(created_at_desc|latency_desc|latency_asc)$")
# then in handler:
if sort == "latency_desc":
    order_sql = "ORDER BY latency_ms DESC, trace_id DESC"
else:
    order_sql = "ORDER BY created_at DESC, trace_id DESC"
```

**Time: 90 min**