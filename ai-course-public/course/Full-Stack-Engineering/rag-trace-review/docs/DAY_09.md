# Day 9 — React Data Tables (TanStack Table)

## 1. Analogy
TanStack Table is a **headless chef**. You bring the plates, the menu, and the dining room. The chef prepares the recipes (sorting, filtering) and hands them to you. You decide how to serve.

## 2. Technical concept
TanStack Table is **headless** — it provides state and helpers, not markup. You build the table with your own JSX. State can be controlled or uncontrolled.

## 3. Why
Most table libraries dictate styling. Headless means we own the design and accessibility.

## 4. Data flow
Rows + columns → `useReactTable` → state (sorting, filters) → your JSX reads `row.getValue()`, `row.getIsSelected()`, etc.

## 5. Example
```tsx
import { useReactTable, getCoreRowModel, flexRender } from '@tanstack/react-table';

export function BasicTable({ data, columns }) {
  const table = useReactTable({ data, columns, getCoreRowModel: getCoreRowModel() });
  return <table>{table.getRowModel().rows.map(r => <tr>{r.getVisibleCells().map(c => <td>{flexRender(c.column.columnDef.cell, c.getContext())}</td>)}</tr>)}</table>;
}
```

## 6. Line-by-line
- `useReactTable` is the hook.
- `getCoreRowModel` returns rows.
- `flexRender` calls a render function with the cell context.

## 7. I/O
- data: `TraceSummary[]`
- columns: `{ accessorKey: 'latency_ms', header: 'Latency' }`

## 8. Bugs
- Forgetting `getCoreRowModel` → empty rows.
- Mismatched `accessorKey` and data shape.
- Not memoizing `columns` (causes re-renders).

## 9. Tests
Use RTL with a few rows and assert the table renders the right cells.

## 10. Performance
- `columnResizeMode: 'onChange'` for live resize.
- Virtualize rows with TanStack Virtual (Day 10).
- Memoize columns with `useMemo`.

## 11. Five Q&As
1. **Why headless?** Own your markup.
2. **Sorting client vs server?** Server when dataset is large.
3. **What is `flexRender`?** Calls the cell render function.
4. **What is a column def?** An object describing a column.
5. **What is `getCoreRowModel`?** Returns the visible rows after core processing.

## 12. Coding assignment
Add a column for `feedback` that shows 👍/👎 and is sortable by rating.

## 13. Solution
```tsx
{ accessorKey: 'feedback', header: 'Feedback',
  cell: ({ getValue }) => getValue() === 'up' ? '👍' : getValue() === 'down' ? '👎' : '',
  sortingFn: (a, b) => String(a.original.feedback ?? '').localeCompare(String(b.original.feedback ?? ''))
}
```
- 0: doesn't render
- 4: shows emoji
- 6: sortable
- 8: handles null
- 10: colors the cell

**Time: 90 min**