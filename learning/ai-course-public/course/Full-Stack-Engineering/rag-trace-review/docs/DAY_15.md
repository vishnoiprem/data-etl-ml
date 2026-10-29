# Day 15 — Testing
**Module 15** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
Tests are a **seatbelt**. You don't need them until you crash. Then you're very glad you had them.

Three kinds:
- **Unit:** one function, no I/O.
- **Integration:** multiple modules, real I/O.
- **End-to-end (Playwright):** a real user in a real browser.

You want lots of unit, some integration, few E2E.

---

## 2. Technical concepts (20 min)

- **Unit:** test one function in isolation. Fast.
- **Integration:** test multiple modules together. Slower.
- **Contract:** verify the API matches the spec. Most valuable for teams.
- **E2E (Playwright):** simulate a real user in a real browser. Slowest, most realistic.

### Test pyramid
Many unit → fewer integration → very few E2E.

### Tools
- pytest + httpx.TestClient (backend)
- Vitest + React Testing Library (frontend)
- Playwright (E2E)
- msw (network mocking)

### Test isolation
Each test should set up its own state. We use a `_fresh_db` fixture.

---

## 3. Coding (30 min)

Add a test for the new SSE endpoint:

```python
def test_sse_stream(client):
    with client.stream("GET", "/traces/stream/demo") as r:
        chunks = []
        for line in r.iter_lines():
            if line.startswith("data: "):
                chunks.append(line[6:])
            if len(chunks) >= 5:
                break
    assert "".join(chunks) == "Hello streaming world"
```

Add a Vitest test for `useDebouncedValue`:

```ts
import { renderHook, act } from '@testing-library/react';
import { useDebouncedValue } from './useDebouncedValue';
test('debounces', () => {
  vi.useFakeTimers();
  const { result, rerender } = renderHook(({ v }) => useDebouncedValue(v, 100), { initialProps: { v: 1 } });
  rerender({ v: 2 });
  expect(result.current).toBe(1);
  act(() => vi.advanceTimersByTime(150));
  expect(result.current).toBe(2);
});
```

### Sample I/O
- Backend test passes: 15/15.
- Frontend test passes.

### Line-by-line
- `client.stream(...)` — httpx streaming.
- `vi.useFakeTimers()` — control time in tests.

---

## 4. Debugging & tests (20 min)

### Bug 1: tests depend on each other
**Fix:** use fixtures; reset DB in `autouse=True`.

### Bug 2: tests hit the real network
**Fix:** msw for the frontend; TestClient for the backend.

### Bug 3: tests don't assert
**Fix:** `expect(...)` is mandatory.

### Bug 4: flaky E2E
**Fix:** `await page.waitFor(...)` instead of `sleep`.

---

## 5. Mock interview practice (20 min)

**Q1 — "Unit vs integration?"**
> Unit is fast and isolated; integration is slower and uses real I/O.

**Q2 — "What is a fixture?"**
> Reusable test setup.

**Q3 — "What is mocking?"**
> Replacing a real dependency with a fake.

**Q4 — "What is a contract test?"**
> Verifies producer and consumer agree on a schema.

**Q5 — "Test pyramid?"**
> Many units, fewer integration, very few E2E.

---

## 6. Success criteria check
- [ ] I can write a unit test for a function.
- [ ] I can write an integration test for an API.
- [ ] I can write a component test with RTL.
- [ ] I can mock the network.
- [ ] I can run the test pyramid.

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
**Write a Playwright test that opens the app, clicks a row, and submits 👍 feedback.**

### Rubric (0–10)
- 0: test doesn't run
- 4: opens page
- 6: clicks row
- 8: submits feedback
- 10: asserts optimistic + persisted state

### Solution (already in `frontend/e2e/trace-flow.spec.ts`)

**Time: 90 min**