# Day 12 — RAG Trace Inspection

## 1. Analogy
A trace is a **flight's black box**. The detail page is the analyst's readout: where it went, what fuel it used, what altitude, who was on board.

## 2. Technical concept
The trace detail page shows: user query, prompt template, retrieved chunks (with scores), the model's response, citations, latency, token usage, and feedback. All this comes from `GET /traces/{id}`.

## 3. Why
Engineers need to see what the model saw and decided. Without it, debugging is guesswork.

## 4. Data flow
Click row → set selected id → useQuery(['trace', id]) → fetch /traces/{id} → render sections.

## 5. Example (already in `TraceDetail.tsx`)

## 6. Line-by-line
- `useQuery({ enabled: !!traceId })` skips the fetch until we have an id.
- Sections are JSX, each backed by a single field.
- Citations are clickable to scroll to the chunk.

## 7. I/O
- `GET /traces/trace_000123` returns the full record including `retrieved_chunks` and `citations`.

## 8. Bugs
- Loading state missing → blank screen.
- 404 not handled → empty UI.
- Long text overflows the layout → use `whitespace-pre-wrap`.

## 9. Tests
- Render with mock data, assert sections are present.
- Render with 404, assert error message.

## 10. Performance
- JSON parse is O(n); for huge chunks use `useMemo`.

## 11. Five Q&As
1. **What goes in retrieved_chunks?** The top-k text chunks the retriever returned.
2. **What is a citation?** A pointer from a sentence in the response back to a chunk.
3. **What's the difference between score and rank?** Score is continuous; rank is position.
4. **Why store chunks as JSON in SQLite?** Small scale, single table, simple queries.
5. **When would you split them out?** When chunks are shared across traces or need full-text search.

## 12. Coding assignment
Highlight the cited chunks in the chunks list (e.g. add a `border` to chunks with matching `chunk_id` in `citations`).

## 13. Solution
```tsx
const cited = new Set(d.citations.map(c => c.chunk_id));
// in render:
className={`p-2 ${cited.has(c.chunk_id) ? 'border-2 border-blue-500' : ''}`}
```
- 0: no highlight
- 4: highlights all chunks
- 6: only cited
- 8: uses Set for O(1) lookup
- 10: animates the highlight

**Time: 90 min**