# Day 10 — Virtualized Lists
**Module 10** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
Imagine 10,000 people in a stadium, but only ~100 can fit in your TV screen. **Virtualization is the camera operator** — they point the camera at the people you can see, and the rest don't render.

Without virtualization: the camera tries to film all 10,000. Slow, janky.
With virtualization: the camera films 20 + a 8-row buffer. Smooth.

---

## 2. Technical concepts (20 min)

We keep a **scaled container** with `height = totalRows × rowHeight`. The `useVirtualizer` hook returns the indices of rows visible in the scroll viewport plus an `overscan` buffer. We render only those rows, positioned absolutely.

### Why
DOM cost is O(rendered rows), not O(total rows). 10,000 rows without virtualization: ~500ms render, janky scroll. With virtualization: <16ms render, smooth.

### What virtualization does NOT do
- It does NOT shrink the API response. You still received 10,000 rows over the wire.
- It does NOT help if your data fetching is slow.
- It does NOT work for accessibility-friendly tables without `role="rowgrid"` and proper ARIA.

### Variable row heights
Use `measureElement` so the virtualizer learns real heights.

### Sticky header
`position: sticky; top: 0; z-index: 10;`.

---

## 3. Coding (30 min)

Open `frontend/src/components/TraceRow.tsx` and read the `useVirtualizer` block. Add a sticky header.

```tsx
<thead className="bg-gray-50 sticky top-0 z-10">
  <tr><th>Trace</th><th>Created</th><th>Prompt</th><th>Query</th><th>Tokens</th><th>Latency</th><th>Status</th><th>Feedback</th></tr>
</thead>
```

Then add a `measureElement` callback for variable height (optional):

```tsx
const virt = useVirtualizer({
  count: rows.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 44,
  overscan: 8,
  measureElement: (el) => el.getBoundingClientRect().height,
});
```

### Sample I/O
- Scroll 10,000 rows: ~36 DOM nodes rendered at any time.

### Line-by-line
- `position: relative` on the scroll container.
- `position: absolute` on each row with `transform: translateY(vi.start)`.
- `contain: strict` for layout containment (perf).

---

## 4. Debugging & tests (20 min)

### Bug 1: non-`position: relative` parent
**Symptom:** rows appear at the top of the page.
**Fix:** `position: relative` on the container.

### Bug 2: mixing `display: table-row` with absolute positioning
**Symptom:** rows don't position.
**Fix:** use absolute positioning only.

### Bug 3: variable row heights without `measureElement`
**Symptom:** rows overlap.
**Fix:** `measureElement`.

### Bug 4: missing `key` on rows
**Symptom:** rows flicker on scroll.
**Fix:** `key={t.trace_id}`.

### Test
```tsx
test('renders only visible rows', () => {
  const rows = Array.from({length: 10_000}, (_,i) => ({trace_id: `t${i}`, latency_ms: 0, ...}));
  const { container } = render(<TraceTable rows={rows} onSelect={()=>{}} />);
  const rendered = container.querySelectorAll('[data-testid^="row-"]').length;
  expect(rendered).toBeLessThan(100);
});
```

---

## 5. Mock interview practice (20 min)

**Q1 — "What is overscan?"**
> Extra rows rendered above/below the viewport to avoid pop-in.

**Q2 — "Does virtualization shrink the API response?"**
> No — only DOM.

**Q3 — "What if rows have variable height?"**
> `measureElement` to get real height.

**Q4 — "Why not just `overflow: scroll` with all rows?"**
> DOM cost is too high; 10,000+ rows cause jank.

**Q5 — "What is the scroll restoration trick?"**
> Save `scrollOffset` in `sessionStorage` and restore on mount.

---

## 6. Success criteria check
- [ ] I can use `useVirtualizer`.
- [ ] I can add overscan.
- [ ] I can use `measureElement` for variable height.
- [ ] I can sticky-position the header.
- [ ] I can test that DOM count is bounded.

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
**Add a "Jump to top" button that appears after scrolling 1000px.**

### Rubric (0–10)
- 0: no button
- 4: appears
- 6: scrolls
- 8: smooth scroll
- 10: accessible (keyboard, focus management)

### Solution
```tsx
const [show, setShow] = useState(false);
useEffect(() => {
  const onScroll = () => setShow(parentRef.current!.scrollTop > 1000);
  parentRef.current?.addEventListener('scroll', onScroll);
  return () => parentRef.current?.removeEventListener('scroll', onScroll);
}, []);
return show ? <button onClick={() => parentRef.current!.scrollTo({top: 0, behavior: 'smooth'})}>↑</button> : null;
```

**Time: 90 min**