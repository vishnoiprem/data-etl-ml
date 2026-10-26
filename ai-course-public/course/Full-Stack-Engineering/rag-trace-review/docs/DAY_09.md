# Day 9 — React Data Tables (TanStack Table)
**Module 9** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
TanStack Table is a **headless chef**. You bring the plates, the menu, and the dining room. The chef prepares the recipes (sorting, filtering, pagination) and hands them to you. You decide how to serve.

You keep the design, the chef keeps the bookkeeping.

---

## 2. Technical concepts (20 min)

TanStack Table is **headless** — it provides state and helpers, not markup. You build the table with your own JSX. State can be controlled or uncontrolled.

### Key APIs
- `useReactTable({ data, columns, getCoreRowModel })`
- `column.accessorKey` — the field.
- `column.header` — what to display.
- `column.cell` — custom render.
- `getCoreRowModel` — required.
- `getSortedRowModel` — for sorting.
- `getFilteredRowModel` — for global filter.

### Controlled state
Pass `state` and `onStateChange` to control sorting/filtering. Use this to sync with URL params.

### Debouncing global filter
Each keystroke would re-filter every row. Debounce the input.

---

## 3. Coding (30 min)

Open `frontend/src/components/TraceRow.tsx`. Today: replace it with a TanStack Table version that supports client-side sorting.

```tsx
import { useReactTable, getCoreRowModel, getSortedRowModel, flexRender, ColumnDef } from '@tanstack/react-table';
import { useMemo, useState } from 'react';
import type { TraceSummary } from '../types';

const cols: ColumnDef<TraceSummary>[] = [
  { accessorKey: 'trace_id', header: 'Trace' },
  { accessorKey: 'created_at', header: 'Created' },
  { accessorKey: 'prompt_version', header: 'Prompt' },
  { accessorKey: 'latency_ms', header: 'Latency' },
  { accessorKey: 'status', header: 'Status' },
];

export function TraceTable({ rows, onSelect }: { rows: TraceSummary[]; onSelect: (id: string) => void }) {
  const [sorting, setSorting] = useState([]);
  const data = useMemo(() => rows, [rows]);
  const table = useReactTable({ data, columns: cols, state: { sorting }, onSortingChange: setSorting, getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel() });
  return <table>{table.getHeaderGroups().map(hg => <tr>{hg.headers.map(h => <th onClick={h.column.getToggleSortingHandler()}>{flexRender(h.column.columnDef.header, h.getContext())}</th>)}</tr>)}{table.getRowModel().rows.map(r => <tr onClick={() => onSelect(r.original.trace_id)}>{r.getVisibleCells().map(c => <td>{flexRender(c.column.columnDef.cell ?? c.column.columnDef.accessorKey, c.getContext())}</td>)}</tr>)}</table>;
}
```

### Sample I/O
- Click `Latency` header → rows sort ascending.
- Click again → sort descending.

### Line-by-line
- `ColumnDef<TraceSummary>` — typed column.
- `flexRender(c.column.columnDef.cell ?? c.column.columnDef.accessorKey, c.getContext())` — render the cell or the raw value.
- `h.column.getToggleSortingHandler()` — click handler.

---

## 4. Debugging & tests (20 min)

### Bug 1: empty rows
**Cause:** forgot `getCoreRowModel`.
**Fix:** pass it.

### Bug 2: mismatched accessor
**Symptom:** `undefined` in cells.
**Fix:** make sure `accessorKey` matches the data field.

### Bug 3: not memoizing columns
**Cause:** re-creating `cols` on every render triggers an effect.
**Fix:** `useMemo(() => cols, [])`.

### Bug 4: re-rendering the whole table
**Fix:** `React.memo` on rows, `useCallback` on row click.

### Test
```tsx
import { render, screen, fireEvent } from '@testing-library/react';
test('sorts by latency', () => {
  const rows = [{trace_id:'a', latency_ms:300}, {trace_id:'b', latency_ms:100}];
  render(<TraceTable rows={rows} onSelect={() => {}} />);
  fireEvent.click(screen.getByText('Latency'));
  expect(screen.getAllByRole('row')[1]).toHaveTextContent('b');
});
```

---

## 5. Mock interview practice (20 min)

**Q1 — "Why headless?"**
> Own your markup and accessibility.

**Q2 — "Sorting client vs server?"**
> Server when dataset is large; client when small.

**Q3 — "What is `flexRender`?"**
> Calls the cell render function with the cell context.

**Q4 — "What is a column def?"**
> An object describing a column: accessor, header, cell, sort fn, filter fn.

**Q5 — "What is `getCoreRowModel`?"**
> Returns the visible rows after core processing (no sort/filter).

---

## 6. Success criteria check
- [ ] I can define a typed column.
- [ ] I can wire sorting.
- [ ] I can memoize columns.
- [ ] I can test sort behavior.

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
**Add a `feedback` column that shows 👍/👎 and is sortable by rating.**

### Rubric (0–10)
- 0: doesn't render
- 4: shows emoji
- 6: sortable
- 8: handles null
- 10: colors the cell

### Solution
```tsx
{ accessorKey: 'feedback', header: 'Feedback',
  cell: ({ getValue }) => getValue() === 'up' ? '👍' : getValue() === 'down' ? '👎' : '',
  sortingFn: (a, b) => String(a.original.feedback ?? '').localeCompare(String(b.original.feedback ?? '')),
}
```

**Time: 90 min**