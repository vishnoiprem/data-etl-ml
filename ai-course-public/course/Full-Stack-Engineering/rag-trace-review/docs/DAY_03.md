# Day 3 — React Foundations
**Module 3** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
React is a **theater play**.
- The **script** is your JSX.
- The **actors** are components.
- The **director** (React) decides when each actor walks on stage.
- If a costume prop changes, only the actor wearing it re-dresses; the rest stay the same.

That's why React is fast: it doesn't redraw the whole stage, just the actors whose props changed.

---

## 2. Technical concepts (20 min)

React is a **declarative UI library**. You describe what the screen should look like for any state. React diffs the new description against the previous one and applies the minimum DOM mutations (the *reconciliation* algorithm).

### Hooks
- `useState` — local state. Returns `[value, setter]`.
- `useEffect(fn, deps)` — side effects. `deps` is the dependency array.
- `useMemo(fn, deps)` — memoize a value.
- `useCallback(fn, deps)` — memoize a function reference.
- `useRef` — mutable cell that does **not** trigger renders.

### Controlled inputs
```tsx
<input value={name} onChange={e => setName(e.target.value)} />
```
React state is the single source of truth.

### Reconciliation + keys
React identifies children with **keys**. Bad keys → wrong DOM reuse, lost state. Always use stable ids.

---

## 3. Coding (30 min)

Create `frontend/src/components/Counter.tsx` + test.

```tsx
import { useState, useEffect } from 'react';

export function Counter({ initial = 0 }: { initial?: number }) {
  const [n, setN] = useState(initial);
  useEffect(() => { document.title = `count ${n}`; }, [n]);
  return <button onClick={() => setN(n + 1)}>{n}</button>;
}
```

```tsx
// Counter.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Counter } from './Counter';
test('increments', () => {
  render(<Counter />);
  fireEvent.click(screen.getByRole('button'));
  expect(screen.getByRole('button')).toHaveTextContent('1');
});
```

**Sample I/O:** Initial render shows `0`, after click shows `1`, `document.title === "count 1"`.

**Line-by-line:**
- `useState(initial)` returns `[value, setter]`.
- `useEffect(fn, [n])` runs `fn` when `n` changes (and on mount).
- `onClick` is the React event prop.

---

## 4. Debugging & tests (20 min)

### Bug 1 — stale closure
`useEffect(() => { setX(x + 1); }, [x])` works, but `useEffect(() => { setX(x + 1); }, [])` only runs once. Always list deps.

### Bug 2 — missing key
`{items.map(i => <li>{i.name}</li>)}` warns. Use `<li key={i.id}>`.

### Bug 3 — mutating state
`arr.push(x); setArr(arr)` doesn't re-render. Use `setArr([...arr, x])`.

### Bug 4 — infinite render
Calling `setX` during render without a guard. Fix: guard in a `useEffect` or `useMemo`.

### Tests
Use `@testing-library/react`. Avoid `getByTestId` when role-based queries work.

---

## 5. Mock interview practice (20 min)

**Q1 — "What is the virtual DOM?"**
> A plain JS object tree representing the desired UI. React diffs it against the previous tree, then applies the minimum DOM mutations.

**Q2 — "Why do we need keys?"**
> So React can match children between renders and reuse DOM nodes.

**Q3 — "What's the dependency array for?"**
> Tells React when to re-run the effect. `[]` = once. Omit = every render.

**Q4 — "What is StrictMode?"**
> Renders twice in dev to surface side-effect bugs.

**Q5 — "useState vs useReducer?"**
> Reducer for complex state transitions, useState for simple values.

---

## 6. Success criteria check
- [ ] I can write a component with state, props, and effect.
- [ ] I can list hooks and when to use each.
- [ ] I can write a Vitest + RTL test.
- [ ] I can name the 4 bugs above and fix them.

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
**Implement `useLocalStorage<T>(key, initial): [T, (v: T) => void]`.**

### Rubric (0–10)
- 0: doesn't compile
- 4: writes to localStorage
- 6: reads on init + tuple
- 8: handles JSON parse error
- 10: SSR-safe (window check)

### Solution
```ts
import { useEffect, useState } from 'react';
export function useLocalStorage<T>(key: string, initial: T) {
  const [v, setV] = useState<T>(() => {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : initial;
  });
  useEffect(() => { localStorage.setItem(key, JSON.stringify(v)); }, [key, v]);
  return [v, setV] as const;
}
```

**Time: 90 min**