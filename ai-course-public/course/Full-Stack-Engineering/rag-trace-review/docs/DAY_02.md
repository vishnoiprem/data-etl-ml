# Day 2 — JavaScript and TypeScript
## Time: 90 min

## 1. Analogy (10 min)
JavaScript is a giant box of LEGO. You can snap pieces in any order, and if you make a typo the box doesn't complain. **TypeScript is the same LEGO box with labels on every piece** — the lid won't close unless everything matches.

## 2. Technical concept (20 min)
JS is **dynamic and weakly typed** — variables can hold anything and change types mid-program. TS adds a **static type system** that runs at compile time. TS never changes runtime behavior; it just catches mistakes before the code ships.

```ts
// JS
function add(a, b) { return a + b; }
add(1, "2");   // "12"  — surprise!

// TS
function add(a: number, b: number): number { return a + b; }
add(1, "2");   // compile error
```

### The type system
- **Primitives:** `string`, `number`, `boolean`, `null`, `undefined`
- **Arrays:** `number[]` or `Array<number>`
- **Objects:** `{ name: string; age: number }`
- **Unions:** `string | null`
- **Generics:** `<T>(items: T[]): T`
- **Discriminated unions:** `{ kind: "ok"; data } | { kind: "error"; err }`

## 3. Why this problem exists
Bugs in dynamic languages only surface at runtime, often in production. TS moves those errors to the editor, where the cost of fixing is zero.

## 4. Frontend/backend data flow
Frontend sends `Promise<TracePage>`; backend returns that exact shape. We define the contract once in `frontend/src/types/index.ts` and the compiler enforces every consumer.

## 5. Complete runnable example
**File: `frontend/src/lib/sum.ts`**
```ts
export function sum(nums: number[]): number {
  return nums.reduce((acc, n) => acc + n, 0);
}
```
**File: `frontend/src/lib/sum.test.ts`**
```ts
import { describe, it, expect } from 'vitest';
import { sum } from './sum';
describe('sum', () => {
  it('handles empty', () => expect(sum([])).toBe(0));
  it('handles positives', () => expect(sum([1,2,3])).toBe(6));
  it('handles negatives', () => expect(sum([-1,1])).toBe(0));
});
```

## 6. Line-by-line
- `export function` — ES module syntax, makes it importable.
- `nums: number[]` — TS type. `[]` is a shortcut for `Array<number>`.
- `reduce((acc, n) => acc + n, 0)` — `0` is the initial value. Without it, the empty array would throw.

## 7. Sample I/O
| Input | Output |
|---|---|
| `[]` | `0` |
| `[1,2,3]` | `6` |
| `[-1,1]` | `0` |

## 8. Common bugs
- **Type coercion:** `"5" - 1 === 4` (subtraction coerces, addition concatenates).
- **`undefined` vs `null`:** pick one convention; we use `null = "intentionally empty"`.
- **Async forgetting await:** `await Promise.all([fetchA(), fetchB()])` is the cure.

## 9. Tests
3 cases above, plus an edge case:
```ts
it('handles large arrays', () => {
  const big = Array.from({length:1_000_000}, (_,i)=>i);
  expect(sum(big)).toBe(499_999_500_000);
});
```

## 10. Performance
`reduce` is O(n); fine for 1M. For 100M+ use a loop. For concurrent I/O use `Promise.all`.

## 11. Five Meta-style interview Q&As
1. **What's `unknown` vs `any`?** `any` opts out of types; `unknown` is type-safe (you must narrow).
2. **What is structural typing?** TS cares about the *shape*, not the name. Two types with the same fields are assignable.
3. **What is a discriminated union?** A union of objects with a common literal tag.
4. **What is a generic?** A type placeholder — like a function for types.
5. **What is `as const`?** Tells TS to infer literal types so `'v1.0'` stays `'v1.0'`, not `string`.

## 12. Coding assignment
Write `percentile(nums: number[], p: number): number` that returns the p-th percentile (0–100). Handle empty arrays and out-of-range p.

## 13. Solution + rubric
```ts
export function percentile(nums: number[], p: number): number {
  if (nums.length === 0) throw new Error('empty');
  if (p < 0 || p > 100) throw new Error('p out of range');
  const sorted = [...nums].sort((a, b) => a - b);
  const idx = Math.min(sorted.length - 1, Math.floor((p / 100) * sorted.length));
  return sorted[idx];
}
```
- 0: doesn't compile
- 4: works for happy path
- 6: handles empty + range
- 8: sorts defensively (no in-place mutation)
- 10: linear interpolation between adjacent samples

**Time: 90 min**