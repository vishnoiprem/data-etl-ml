# Day 12 — RAG Trace Inspection
**Module 12** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
A trace is a **flight's black box**. The detail page is the analyst's readout: where it went, what fuel it used, what altitude, who was on board, what the pilot said.

Without the black box, after a crash you just shrug. With it, you find the cause.

---

## 2. Technical concepts (20 min)

The trace detail page shows:
- user query
- prompt template
- retrieved chunks (with scores)
- model response
- citations
- latency
- token usage
- feedback

All this comes from `GET /traces/{id}`.

### Data flow
Click row → set selected id → `useQuery(['trace', id])` → fetch `/traces/{id}` → render sections.

### State management
- Selected trace id lives in the parent (`TraceList`).
- Detail page receives the id as a prop.
- We do **not** put the detail in the same cache as the list — different query keys.

### Error states
- Loading: skeleton or "Loading trace…".
- 404: red message.
- 500: "Failed to load trace: 500".

---

## 3. Coding (30 min)

Open `frontend/src/pages/TraceDetail.tsx`. Add a **highlight** for cited chunks:

```tsx
const cited = new Set(data.citations.map(c => c.chunk_id));
// in render
className={`p-2 rounded text-sm ${cited.has(c.chunk_id) ? 'border-2 border-blue-500' : 'bg-gray-50'}`}
```

Add a **latency breakdown** (assume we have server-side timing data; for now show the total as a horizontal bar).

### Sample I/O
- `GET /traces/trace_000123` returns the full record.
- Citations: `[{chunk_id: 'c0', source: 'wiki.md', score: 0.92}, ...]`.
- The c0 chunk in the chunks list has a blue border.

### Line-by-line
- `new Set(...)` for O(1) lookup.
- `border-2 border-blue-500` — Tailwind utility for a 2px blue border.

---

## 4. Debugging & tests (20 min)

### Bug 1: long text overflows
**Fix:** `whitespace-pre-wrap break-words` and `max-w-full`.

### Bug 2: 404 not handled
**Fix:** `if (error) return <Error />`.

### Bug 3: chunk score is `undefined`
**Cause:** JSON parse failed.
**Fix:** try/catch and default to 0.

### Bug 4: citations link to a chunk that doesn't exist
**Fix:** skip the highlight for missing chunks.

### Test
```tsx
test('highlights cited chunks', () => {
  const detail = { ...mockDetail, citations: [{chunk_id:'c0', source:'wiki', score:1}], retrieved_chunks: [{chunk_id:'c0', text:'x', score:1}, {chunk_id:'c1', text:'y', score:0.5}] };
  render(<TraceDetail traceId="x" />, { wrapper: withDetail(detail) });
  expect(screen.getByText('x').closest('li')).toHaveClass('border-blue-500');
});
```

---

## 5. Mock interview practice (20 min)

**Q1 — "What goes in `retrieved_chunks`?"**
> The top-k text chunks the retriever returned.

**Q2 — "What is a citation?"**
> A pointer from a sentence in the response back to a chunk.

**Q3 — "Score vs rank?"**
> Score is continuous; rank is position.

**Q4 — "Why store chunks as JSON in SQLite?"**
> Small scale, single table, simple queries.

**Q5 — "When would you split them out?"**
> When chunks are shared across traces or need full-text search.

---

## 6. Success criteria check
- [ ] I can render every section of the detail page.
- [ ] I can highlight cited chunks.
- [ ] I can handle 404 and 500.
- [ ] I can render a long response without overflow.

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
**Add a "Copy response" button that copies the model_response to the clipboard.**

### Rubric (0–10)
- 0: no button
- 4: shows button
- 6: copies to clipboard
- 8: shows confirmation
- 10: handles clipboard failure

### Solution
```tsx
const onCopy = async () => {
  try { await navigator.clipboard.writeText(data.model_response); setCopied(true); }
  catch { setError('Copy failed'); }
};
<button onClick={onCopy}>{copied ? '✓' : 'Copy'}</button>
```

**Time: 90 min**