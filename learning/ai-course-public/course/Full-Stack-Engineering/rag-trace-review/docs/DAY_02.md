# Day 2 — JavaScript and TypeScript
**Module 2** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
JavaScript is a giant box of LEGO. You can snap pieces in any order, and if you make a typo the box doesn't complain.
**TypeScript is the same LEGO box with labels on every piece** — the lid won't close until everything matches.

So you spend a few more seconds building, but you don't accidentally stick a wheel on the roof.

---

## 2. Technical concepts (20 min)

**JS = dynamic + weakly typed.** Variables can hold anything and change types mid-program. TS adds a **static type system** that runs at compile time. TS never changes runtime behavior; it just catches mistakes before shipping.

```ts
// JS
function add(a, b) { return a + b; }
add(1, "2");   // "12" — surprise!

// TS
function add(a: number, b: number): number { return a + b; }
add(1, "2");   // compile error
```

### Core types
- Primitives: `string`, `number`, `boolean`, `null`, `undefined`, `bigint`, `symbol`
- Arrays: `number[]` or `Array<number>`
- Objects: `{ name: string; age: number }`
- Unions: `string | null`
- Generics: `<T>(items: T[]): T`
- Discriminated unions: `{ kind: "ok"; data } | { kind: "err"; err }`

### Map / filter / reduce
```ts
[1, 2, 3].map(n => n * 2);    // [2, 4, 6]
[1, 2, 3].filter(n => n > 1); // [2, 3]
[1, 2, 3].reduce((a, n) => a + n, 0); // 6
```

### Promises + async/await
```ts
const r = await fetch('/traces');
const body: TracePage = await r.json();
```

### Null handling
- `T | null` is the explicit "may be missing".
- Use `??` for default values, `?.` for safe access.
- `!` (non-null assertion) is a code smell.

---

## 3. Coding (30 min)

Create `frontend/src/lib/sum.ts` and `frontend/src/lib/sum.test.ts`.

```ts
// sum.ts
export function sum(nums: number[]): number {
  return nums.reduce((acc, n) => acc + n, 0);
}
```
```ts
// sum.test.ts
import { describe, it, expect } from 'vitest';
import { sum } from './sum';
describe('sum', () => {
  it('handles empty', () => expect(sum([])).toBe(0));
  it('handles positives', () => expect(sum([1,2,3])).toBe(6));
  it('handles negatives', () => expect(sum([-1,1])).toBe(0));
});
```

**Run:** `cd frontend && npm install && npm test`

**Expected:** `3 passed`

### Sample I/O
| Input | Output |
|---|---|
| `[]` | `0` |
| `[1, 2, 3]` | `6` |
| `[-1, 1]` | `0` |

### Line-by-line
- `export` — ES module syntax.
- `nums: number[]` — TS type.
- `reduce` — accumulator + current + initial value.

---

## 4. Debugging & tests (20 min)

### Bug 1: Type coercion surprise
`"5" - 1 === 4` (subtraction coerces), `"5" + 1 === "51"` (addition concatenates).
**Fix:** parse with `Number()` or `parseInt`.

### Bug 2: `undefined` vs `null`
Pick one convention. We use `null = intentionally empty`. Configure `tsconfig` with `"strictNullChecks": true`.

### Bug 3: forgetting `await`
`const data = fetch(...)` gives a Promise, not the data. Always `await` or `.then()`.

### Bug 4: tests don't run
**Cause:** missing `vitest` in `package.json`.
**Fix:** `npm install -D vitest`.

---

## 5. Mock interview practice (20 min)

**Q1 — "What's `unknown` vs `any`?"**
> `any` opts out of types. `unknown` is type-safe: you must narrow with `typeof` or `instanceof` before use.

**Q2 — "What is structural typing?"**
> TS cares about the *shape*, not the name. Two types with the same fields are assignable.

**Q3 — "What is a discriminated union?"**
> A union of object types sharing a literal tag. Lets the compiler narrow via `if (x.kind === 'ok')`.

**Q4 — "What is a generic?"**
> A type parameter — like a function for types. Example: `function first<T>(arr: T[]): T | undefined`.

**Q5 — "What does `as const` do?"**
> Tells TS to infer literal types so `'v1.0'` stays `'v1.0'`, not `string`.

---

## 6. Success criteria check
- [ ] I can write a typed function with primitives, arrays, unions.
- [ ] I can write a generic.
- [ ] I can write a discriminated union.
- [ ] I can run a Vitest test and read failures.
- [ ] I can avoid the 4 common bugs above.

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

Pass: ≥ 56/80. Aim: ≥ 64/80.

---

## 8. Coding assignment
**Implement `percentile(nums: number[], p: number): number`** returning the p-th percentile (0–100). Handle empty arrays and out-of-range p.

### Rubric (0–10)
- 0: doesn't compile
- 4: works for happy path
- 6: handles empty + range
- 8: sorts defensively (no in-place mutation)
- 10: linear interpolation between adjacent samples

### Solution
```ts
export function percentile(nums: number[], p: number): number {
  if (nums.length === 0) throw new Error('empty');
  if (p < 0 || p > 100) throw new Error('p out of range');
  const sorted = [...nums].sort((a, b) => a - b);
  const idx = Math.min(sorted.length - 1, Math.floor((p / 100) * sorted.length));
  return sorted[idx];
}
```

**Time: 90 min**