# Day 15 — Testing

## 1. Analogy
Tests are a **seatbelt**. You don't need them until you crash.

## 2. Technical concept
- **Unit:** test one function in isolation.
- **Integration:** test multiple modules together.
- **Contract:** verify the API matches the spec.
- **E2E (Playwright):** simulate a real user in a real browser.

## 3. Why
Without tests, refactoring is a coin flip. With tests, refactoring is a coin flip you can verify.

## 4. Data flow
Test sets up DB → calls endpoint → asserts response.

## 5. Example (already in `tests/test_traces.py`)

## 6. Line-by-line
- `TestClient(app)` from FastAPI gives us a synchronous client over the ASGI app.
- `@pytest.fixture(autouse=True)` resets the DB before every test.

## 7. I/O
- Test passes: 14 green dots.
- Test fails: red dot + stack trace.

## 8. Bugs
- Tests that depend on each other.
- Tests that hit the real DB.
- Tests that don't assert anything.

## 9. Tests (already present)

## 10. Performance
- Use `pytest-xdist` for parallel runs.
- Use `freezegun` for time-dependent code.

## 11. Five Q&As
1. **Unit vs integration?** Unit is fast and isolated; integration is slower and uses real I/O.
2. **What is a fixture?** Reusable test setup.
3. **What is mocking?** Replacing a real dependency with a fake.
4. **What is a contract test?** Verifies the producer and consumer agree on a schema.
5. **What's the test pyramid?** Many units, fewer integration, very few E2E.

## 12. Coding assignment
Write a Playwright test that opens the app, clicks a row, and submits 👍 feedback.

## 13. Solution (already in `e2e/trace-flow.spec.ts`)

- 0: test doesn't run
- 4: opens page
- 6: clicks row
- 8: submits feedback
- 10: asserts optimistic + persisted state

**Time: 90 min**