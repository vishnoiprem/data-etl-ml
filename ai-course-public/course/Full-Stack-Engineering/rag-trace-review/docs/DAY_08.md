# Day 8 — Cursor Pagination (Deep Dive)

## 1. Analogy
Reading a book with bookmarks is cursor pagination. Re-counting pages from the start every time is OFFSET. Bookmarks are faster but you can't jump to chapter 7 without re-walking.

## 2. Technical concept
A cursor is an **opaque pointer to a position in a sorted sequence**. Given a sort key `(created_at, trace_id)`, the cursor encodes the last seen values. The next query becomes `WHERE (created_at, trace_id) < (cursor.created_at, cursor.trace_id) ORDER BY ... LIMIT n+1`.

## 3. Why
- OFFSET scans and discards rows → O(n).
- Cursor walks the index → O(log n + page_size).
- OFFSET is unstable when rows are inserted.

## 4. Data flow
Client sends cursor → server decodes → adds `WHERE col < cursor` → runs index scan → returns `next_cursor` based on the last row.

## 5. Example (already in `routes/traces.py`)
```python
where.append("(created_at < ? OR (created_at = ? AND trace_id < ?))")
params.extend([c_at, c_at, c_id])
```

## 6. Line-by-line
- The OR pattern handles ties on `created_at`.
- The index `(created_at DESC, trace_id DESC)` matches the ORDER BY exactly.

## 7. I/O
- Request: `cursor=eyJ...`
- Decoded: `2026-01-15T...|trace_0042`
- SQL becomes: `WHERE created_at < '2026-01-15T...' OR (created_at = '...' AND trace_id < 'trace_0042')`

## 8. Bugs
- Forgetting the tie-breaker → duplicate rows when `created_at` ties.
- Returning `next_cursor` even when `has_more=false`.
- Using `>` instead of `<` for DESC order.

## 9. Tests
- Walk all pages, assert no duplicates and no skips.
- Combine cursor with filter.
- Test invalid cursor → 400.

## 10. Performance
- Index lookup vs full scan: at 10k rows, ~50× faster.
- `LIMIT n+1` avoids a second count query.

## 11. Five Q&As
1. **Why not offset 0?** Slow.
2. **Why opaque?** We can change format without breaking clients.
3. **What if rows are deleted mid-walk?** Cursor skips them. That's fine.
4. **What if rows are inserted?** Cursor may show new rows on the next page. Acceptable for traces.
5. **Can you jump to page 7?** No. Walk from start.

## 12. Coding assignment
Implement a `next_cursor` validator that ensures the cursor decodes to a string of the form `iso|tid`.

## 13. Solution
```python
import re
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*")
def is_valid_cursor(s: str) -> bool:
    try:
        a, b = base64.urlsafe_b64decode(s).decode().split("|", 1)
        return bool(ISO.match(a)) and bool(b)
    except Exception:
        return False
```
- 0: doesn't compile
- 4: decodes
- 6: validates ISO
- 8: validates trace_id
- 10: rejects empty parts, whitespace

**Time: 90 min**