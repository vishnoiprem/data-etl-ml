# Day 3 — React Foundations

## 1. Analogy (10 min)
React is a **theater play**. The script is your JSX. The actors are components. The director (`React`) decides when each actor walks on stage. If a prop (costume) changes, only the actor wearing it re-dresses; the rest stay the same.

## 2. Technical concept (20 min)
React is a **declarative UI library**. You describe what the screen should look like for any state. React diffs the new description against the previous one and applies the minimum DOM mutations.

### Hooks
- `useState` — local state
- `useEffect` — side effects (network, subscriptions)
- `useMemo` — memoize a value
- `useCallback` — memoize a function
- `useRef` — mutable cell that doesn't trigger renders

### Reconciliation
React uses **keys** to identify which children changed. Bad keys → wrong DOM reuse, lost state.

## 3. Why this problem exists
Imperative DOM manipulation (`document.getElementById`...) is fast to write once and impossible to maintain at scale. React makes UIs predictable.

## 4. Data flow
State change → re-render → virtual DOM diff → DOM patch.

## 5. Complete example
```tsx
import { useState, useEffect } from 'react';

export function Counter({ initial = 0 }: { initial?: number }) {
  const [n, setN] = useState(initial);
  useEffect(() => {
    document.title = `count ${n}`;
  }, [n]);
  return <button onClick={() => setN(n + 1)}>{n}</button>;
}
```

## 6. Line-by-line
- `useState(initial)` returns `[value, setter]`.
- `useEffect(fn, [n])` runs `fn` when `n` changes (and on mount).
- `<button onClick={...}>` — JSX attribute = React event prop.

## 7. Sample I/O
- Initial render: `0`, `document.title === "count 0"`
- After click: `1`, `document.title === "count 1"`

## 8. Bugs
- **Stale closure in `useEffect`** — always list deps.
- **Missing key on lists** — React warns.
- **Mutating state directly** — `arr.push` doesn't re-render; use `setArr([...arr, x])`.

## 9. Tests (RTL)
```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Counter } from './Counter';
test('increments', () => {
  render(<Counter />);
  fireEvent.click(screen.getByRole('button'));
  expect(screen.getByRole('button')).toHaveTextContent('1');
});
```

## 10. Performance
- Use `useMemo` for expensive computations.
- Use `useCallback` when passing functions to memoized children.
- Use `React.memo` for pure presentational components.
- Avoid inline objects/arrays in JSX props.

## 11. Five Q&As
1. **What is the virtual DOM?** A JS object tree; React diffs it against the previous tree.
2. **Why keys?** So React can match children between renders.
3. **What's the dependency array for?** Tells React when to re-run the effect.
4. **What's StrictMode?** Renders twice in dev to surface side-effect bugs.
5. **`useState` vs `useReducer`?** Reducer for complex state transitions, useState for simple values.

## 12. Coding assignment
Build a `useLocalStorage<T>(key: string, initial: T): [T, (v: T) => void]` hook.

## 13. Solution + rubric
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
- 0: no compile
- 4: writes to localStorage
- 6: reads on init, returns tuple
- 8: handles JSON parse error
- 10: SSR-safe (checks `typeof window`)

**Time: 90 min**