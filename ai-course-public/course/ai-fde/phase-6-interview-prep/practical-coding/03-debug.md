# Practical Coding Sub-Lesson 3 — Debug a Codebase (90 min, AI-assisted)

> **This is the third most common practical-coding sub-round.** The format: 90 minutes, a realistic codebase, "there's a bug. Find it, fix it, and write a postmortem." You can use an AI assistant. **The signal: a candidate who reproduces the bug first, traces the root cause, and writes a postmortem that prevents the bug from recurring — is showing they can debug in production.**

---

## Why this sub-round is the FDE signal

The 4 things the interviewer is testing:

1. **Can you reproduce the bug?** The candidate who fixes the bug without reproducing it first is signaling they don't have the discipline to debug in production.
2. **Can you trace the root cause?** The candidate who fixes the symptom, not the cause, is signaling they'll see the bug again in 2 weeks.
3. **Can you write a postmortem?** The postmortem is the artifact that prevents the bug from recurring. The candidate who writes a 1-line "fixed it" is signaling they can't operate.
4. **Can you add a regression test?** The regression test is the proof. Without it, the bug will come back.

**The FDE pattern:** reproduce, trace, fix, test, postmortem. Same as production debugging, compressed to 90 minutes.

---

## The prompt template (the most common format)

> "Here's a codebase. There's a bug. Find it, fix it, and write a postmortem. You have 90 minutes. You can use any tools you want, including an AI assistant."

**The bug is one of:**

- **Race condition:** a shared resource is accessed without a lock.
- **Off-by-one error:** a loop iterates one too many or one too few times.
- **Null pointer:** a field is accessed without checking for null.
- **Memory leak:** a resource is allocated but not freed.
- **Logic error:** the code does the wrong thing in a specific case.

**The 5 deliverables (always):**

1. **The bug fix** (1-2 files, ~10-50 lines).
2. **The regression test** (1-3 tests).
3. **The postmortem** (1 page: timeline, root cause, fix, prevention).
4. **The runbook update** (1 paragraph: how to detect this bug in the future).
5. **The handoff note** (1 paragraph: what you changed, what the next engineer should know).

---

## The 3-phase plan (90 minutes)

### Phase 1: Reproduce the Bug (20 minutes)

**Goal:** find the failing test or the broken behavior.

**The 5 sub-tasks:**

1. **Read the README.** 5 minutes. What does the codebase do? What's the architecture?
2. **Read the failing test (if there is one).** 5 minutes. What does the test expect? What's the actual output?
3. **Run the existing tests.** 5 minutes. Which tests fail? What's the error message?
4. **Use the AI to ask questions.** 5 minutes. "What does this test expect?" "What's the actual output?" "Where is this function called from?"
5. **Reproduce the bug manually.** Run the code with a specific input. Verify the bug is reproducible.

**The 3 deliverables for Phase 1:**

- A failing test (or a manual reproduction script)
- The error message
- The expected vs actual output

### Phase 2: Find the Root Cause (40 minutes)

**Goal:** trace the bug to the line of code that causes it.

**The 5 sub-tasks:**

1. **Trace the code path.** Use the AI to ask "where is X called from?" and "what's the data flow?"
2. **Add logging if needed.** Add a `print()` or a `logger.info()` to trace the bug.
3. **Use the AI to ask questions.** "What does this function do?" "What's the data flow?" "Where is the bug?"
4. **Identify the root cause.** The line of code that causes the bug.
5. **Verify the root cause.** Write a minimal test that reproduces the bug. Run it. Verify it fails.

**The 3 deliverables for Phase 2:**

- The root cause (the line of code)
- The minimal test that reproduces the bug
- The fix (the change to the code)

### Phase 3: Fix + Test + Postmortem (30 minutes)

**Goal:** ship the fix with the 5 deliverables.

**The 5 sub-tasks:**

1. **Fix the bug.** Change the line of code that causes the bug. Keep the fix minimal.
2. **Run the test suite.** All existing tests should pass. The new regression test should pass.
3. **Write the postmortem.** 1 page: timeline, root cause, fix, prevention.
4. **Update the runbook.** 1 paragraph: how to detect this bug in the future.
5. **Write the handoff note.** 1 paragraph: what you changed, what the next engineer should know.

**The 3 anti-patterns to avoid in Phase 3:**

1. **Skipping the regression test.** The regression test is the proof. Without it, the bug will come back.
2. **Skipping the postmortem.** The postmortem is the artifact that prevents the bug from recurring.
3. **Going over time.** 90 minutes is 90 minutes. Practice with a timer.

---

## The worked example: "The rate limiter has a race condition"

### Phase 1: Reproduce the Bug (20 minutes)

**The bug report (hypothetical):**

> "The rate limiter is allowing more requests than the limit. The limit is 10 req/min, but we're seeing 15-20 req/min in production."

**The failing test:**

```python
def test_rate_limiter_concurrent():
    """Test that the rate limiter allows exactly 10 requests per minute."""
    limiter = TokenBucketRateLimiter(capacity=10, refill_rate=10/60)

    def make_request():
        return limiter.allow(user_id="alice")

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_request) for _ in range(20)]
        results = [f.result() for f in futures]

    assert sum(results) == 10  # FAILS: sum is 15
```

**The error message:**

```
AssertionError: assert 15 == 10
```

**The expected vs actual:**

- Expected: 10 requests allowed in 1 minute.
- Actual: 15-20 requests allowed in 1 minute.

### Phase 2: Find the Root Cause (40 minutes)

**The code (`service/circuit.py`):**

```python
class TokenBucketRateLimiter:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets = {}  # user_id -> (tokens, last_refill)

    def allow(self, user_id):
        # BUG: this is not thread-safe!
        if user_id not in self.buckets:
            self.buckets[user_id] = (self.capacity, time.time())

        tokens, last_refill = self.buckets[user_id]
        now = time.time()
        elapsed = now - last_refill
        tokens = min(self.capacity, tokens + elapsed * self.refill_rate)

        if tokens >= 1:
            tokens -= 1
            self.buckets[user_id] = (tokens, now)
            return True
        else:
            self.buckets[user_id] = (tokens, now)
            return False
```

**The root cause:**

The `allow()` method is not thread-safe. Multiple threads can read `self.buckets[user_id]`, decrement `tokens`, and write back to `self.buckets[user_id]` concurrently. This is a classic read-modify-write race condition.

**The fix:**

Add a lock around the read-modify-write section.

### Phase 3: Fix + Test + Postmortem (30 minutes)

**The bug fix (`service/circuit.py`):**

```python
import threading

class TokenBucketRateLimiter:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets = {}
        self.lock = threading.Lock()  # ADD THIS

    def allow(self, user_id):
        with self.lock:  # ADD THIS
            if user_id not in self.buckets:
                self.buckets[user_id] = (self.capacity, time.time())

            tokens, last_refill = self.buckets[user_id]
            now = time.time()
            elapsed = now - last_refill
            tokens = min(self.capacity, tokens + elapsed * self.refill_rate)

            if tokens >= 1:
                tokens -= 1
                self.buckets[user_id] = (tokens, now)
                return True
            else:
                self.buckets[user_id] = (tokens, now)
                return False
```

**The regression test (`tests/test_circuit.py`):**

```python
def test_rate_limiter_concurrent():
    """Test that the rate limiter allows exactly 10 requests per minute."""
    limiter = TokenBucketRateLimiter(capacity=10, refill_rate=10/60)

    def make_request():
        return limiter.allow(user_id="alice")

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_request) for _ in range(20)]
        results = [f.result() for f in futures]

    assert sum(results) == 10  # PASSES after the fix
```

**The postmortem (`POSTMORTEM.md`):**

```markdown
# Postmortem: Rate Limiter Race Condition (2026-10-10)

## Timeline
- 2026-10-10 09:00: Production alert: rate limiter allowing 15-20 req/min instead of 10.
- 2026-10-10 09:15: Investigated; reproduced the bug with a concurrent test.
- 2026-10-10 09:30: Found the root cause: read-modify-write race condition in `allow()`.
- 2026-10-10 09:45: Fixed by adding a lock around the read-modify-write section.
- 2026-10-10 10:00: Deployed the fix to production. Rate limiter now allows exactly 10 req/min.

## Root cause
The `TokenBucketRateLimiter.allow()` method was not thread-safe. Multiple threads could read `self.buckets[user_id]`, decrement `tokens`, and write back to `self.buckets[user_id]` concurrently. This is a classic read-modify-write race condition.

## Fix
Added `threading.Lock` around the read-modify-write section. The lock is acquired at the start of `allow()` and released at the end. This ensures that only one thread can read-modify-write `self.buckets[user_id]` at a time.

## Prevention
1. Add a regression test that runs 20 concurrent requests and asserts the rate limit.
2. Add a code review checklist item: "Are all shared resources protected by a lock?"
3. For Phase 5 P1 (multi-worker), replace the in-process dict with Redis (which is atomic).
```

**The runbook update (`RUNBOOK.md`):**

```markdown
## Rate Limiter

- If the rate limiter is allowing more requests than the limit, check the rate limiter logs.
- If the rate limiter is allowing fewer requests than the limit, check the rate limiter configuration.
- For multi-worker deployments, use Redis instead of the in-process dict (see Phase 5 P1).
```

**The handoff note (`HANDOFF.md`):**

```markdown
## Handoff note: Rate limiter race condition

- Fixed a race condition in `TokenBucketRateLimiter.allow()` by adding a `threading.Lock`.
- Added a regression test in `tests/test_circuit.py`.
- The next engineer should: (1) review the lock usage, (2) consider replacing the in-process dict with Redis for multi-worker deployments, (3) add more concurrent tests.
```

---

## The 3 AI assistant patterns for debugging

### Pattern 1: "AI as a debugging partner"

You have a bug. You use the AI to ask "what does this test expect?" and "what's the data flow?" You trace the bug.

**The risk:** the AI proposes fixes that don't address the root cause. Verify by reproducing the bug + testing the fix.

**The example prompts:**

- "What does this test expect?"
- "What's the actual output?"
- "Where is this function called from?"
- "What's the data flow?"

### Pattern 2: "AI as a code reviewer"

You found the root cause. You use the AI to review the fix: "Does this fix address the root cause?" "Are there any edge cases I'm missing?" "Is the fix minimal?"

**The risk:** the AI proposes changes that don't match the existing patterns. Verify by reading the existing code.

**The example prompts:**

- "Does this fix address the root cause?"
- "Are there any edge cases I'm missing?"
- "Is the fix minimal?"

### Pattern 3: "AI as a postmortem writer"

You fixed the bug. You use the AI to write the postmortem: "What was the timeline?" "What was the root cause?" "What was the fix?" "What was the prevention?"

**The risk:** the AI writes a generic postmortem. Verify by adding the specific details from your debugging.

**The example prompts:**

- "What was the timeline?"
- "What was the root cause?"
- "What was the fix?"
- "What was the prevention?"

---

## The 5 anti-patterns

1. **Skipping the reproduction phase.** "I'll just start fixing" is a junior answer. Reproducing the bug is the FDE signal.
2. **Fixing the symptom, not the cause.** The bug will come back in 2 weeks if you fix the symptom.
3. **Skipping the regression test.** The regression test is the proof. Without it, the bug will come back.
4. **Skipping the postmortem.** The postmortem is the artifact that prevents the bug from recurring.
5. **Going over time.** 90 minutes is 90 minutes. Practice with a timer.

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../take-home/01-prototype.md` | The 4-hour build plan (the same pattern, compressed) |
| `../swe-coding/README.md` | The 8 SWE patterns (the foundation for the code) |
| `../practical-coding/01-build-new-project.md` | The 5 deliverables (the same list) |
| `../practical-coding/02-extend-codebase.md` | The brownfield pattern (read first, code second) |

---

## The thesis

**Debug a codebase is the third most common practical-coding sub-round.** The candidate who reproduces the bug first, traces the root cause, and writes a postmortem that prevents the bug from recurring — is showing they can debug in production.

**The 3-phase plan (20 min reproduce + 40 min trace + 30 min fix+test+postmortem) is the muscle memory.** The 5 deliverables (fix + test + postmortem + runbook + handoff) are the FDE signal. The 3 AI patterns (debugging partner + code reviewer + postmortem writer) are the meta-signal.

**General prep gets you past the resume screen. Practical-coding prep gets you past the centerpiece round at Meta, Anthropic, and OpenAI.**