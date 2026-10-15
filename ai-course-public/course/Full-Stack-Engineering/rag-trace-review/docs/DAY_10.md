# Day 10 — Virtualized Lists

## 1. Analogy
Imagine 10,000 people at a stadium, but only ~100 can fit in your TV screen. **Virtualization is the camera operator** — they point the camera at the people you can see and the rest don't render.

## 2. Technical concept
We keep a **scaled container** with `height = totalRows × rowHeight`. The `useVirtualizer` hook returns the indices of rows visible in the scroll viewport plus an `overscan` buffer. We render only those rows positioned absolutely.

## 3. Why
DOM cost is O(rendered rows), not O(total rows). 10,000 rows without virtualization: ~500ms render, janky scroll. With virtualization: <16ms render, smooth scroll.

## 4. Data flow
Scroll event → useVirtualizer recalculates visible range → React renders only those rows.

## 5. Example (already in `TraceRow.tsx`)
```tsx
const virt = useVirtualizer({ count: rows.length, getScrollElement: () => parentRef.current, estimateSize: () => 44, overscan: 8 });
```

## 6. Line-by-line
- `count` is logical rows.
- `getScrollElement` is the scrollable container.
- `estimateSize` is the row height.
- `overscan` is the buffer above/below the viewport.

## 7. I/O
- Render: 20 visible + 16 overscan = ~36 DOM rows for 10,000 logical rows.

## 8. Bugs
- Using a non-`position: relative` parent.
- Mixing `display: table-row` with absolute positioning.
- Variable row heights without `measureElement`.

## 9. Tests
- Render 10,000 rows; assert <50 DOM rows present.

## 10. Performance
- Use `position: absolute` on rows, `position: relative` on container.
- Avoid reflows by setting `contain: strict`.
- Profile with React DevTools Profiler.

## 11. Five Q&As
1. **What is overscan?** Extra rows rendered to avoid pop-in.
2. **Does virtualization shrink the API response?** No — only DOM.
3. **What if rows have variable height?** Use `measureElement`.
4. **Why not just `overflow: scroll` with all rows?** DOM is too expensive.
5. **What is the scroll restoration trick?** Save `scrollOffset` to sessionStorage.

## 12. Coding assignment
Add a sticky header to the virtualized table.

## 13. Solution
```tsx
<thead className="bg-gray-50 sticky top-0 z-10">
```
- 0: doesn't render
- 4: header visible at top
- 6: header stays during scroll
- 8: z-index prevents row overlap
- 10: header has its own shadow when scrolled

**Time: 90 min**