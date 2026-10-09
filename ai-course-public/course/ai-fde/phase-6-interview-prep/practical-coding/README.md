# Module 3 — Practical Coding Interviews (AI-assisted)

> **The practical coding round is new.** Pioneered at Meta, Anthropic, and OpenAI in 2024-2025, this round replaces the classic "whiteboard algorithm" round. The format: 90 minutes, a realistic codebase, "build a feature" or "debug this" or "extend the API." You can use an AI assistant. **The signal: a candidate who uses the AI assistant well — to explore the codebase, to draft the code, to verify the test — is showing they can ship in 2026.**

---

## The 3 sub-rounds (the canonical format)

### Sub-round 1: Build a new project (greenfield, 90 min)

**The prompt:** "Build a small CLI tool that does X. You have 90 minutes. You can use any tools you want, including an AI assistant."

**The 3 phases:**

1. **Phase 1 (10 min): spec + eval set.** Define the input/output contract. Write 5-10 tests. The eval set is the spec.
2. **Phase 2 (60 min): implementation.** Write the code. Use the AI assistant to draft the boilerplate, but verify every line.
3. **Phase 3 (20 min): polish + tests.** Add edge cases, error handling, README. Run the tests.

**The 5 deliverables:**

1. **The code** (1-3 files, ~200-500 lines).
2. **The tests** (5-10 tests, including the spec).
3. **The README** (1 page: how to run, the design decisions, the tradeoffs).
4. **The cost model** (if applicable: $/month for the use case).
5. **The runbook** (1 paragraph: how to operate the tool).

### Sub-round 2: Extend a codebase (brownfield, 90 min)

**The prompt:** "Here's a codebase you've never seen. Add a feature. You have 90 minutes. You can use any tools you want, including an AI assistant."

**The 3 phases:**

1. **Phase 1 (20 min): explore the codebase.** Read the README, the architecture doc, the tests. Use the AI assistant to ask "what does this function do?" and "where is the rate limiter implemented?" Map the codebase to a 1-page mental model.
2. **Phase 2 (50 min): implement the feature.** Add the endpoint, the test, the doc. Use the AI assistant to draft the boilerplate, but verify every line against the existing patterns.
3. **Phase 3 (20 min): tests + polish.** Add 3-5 tests. Run the existing tests to confirm no regression. Update the README.

**The 5 deliverables:**

1. **The feature code** (1-2 files, ~50-200 lines).
2. **The tests** (3-5 tests).
3. **The README update** (1-2 paragraphs).
4. **The regression check** (existing tests still pass).
5. **The handoff note** (1 paragraph: what you changed, what the next engineer should know).

### Sub-round 3: Debug a codebase (90 min)

**The prompt:** "Here's a codebase. There's a bug. Find it, fix it, and write a postmortem. You have 90 minutes. You can use any tools you want, including an AI assistant."

**The 3 phases:**

1. **Phase 1 (20 min): reproduce the bug.** Run the existing tests. Identify the failing test or the broken behavior. Use the AI assistant to ask "what does this test expect?" and "what's the actual output?"
2. **Phase 2 (40 min): find the root cause.** Trace the code path. Use the AI assistant to ask "where is X called from?" and "what's the data flow?" Identify the bug.
3. **Phase 3 (30 min): fix + test + postmortem.** Fix the bug. Add a regression test. Write a 1-page postmortem (root cause, fix, prevention).

**The 5 deliverables:**

1. **The bug fix** (1-2 files, ~10-50 lines).
2. **The regression test** (1-3 tests).
3. **The postmortem** (1 page: timeline, root cause, fix, prevention).
4. **The runbook update** (1 paragraph: how to detect this bug in the future).
5. **The handoff note** (1 paragraph: what the next engineer should know).

---

## The 3 AI-assisted coding patterns

### Pattern 1: "AI as a typing accelerator"

- You know exactly what to build. You use the AI to draft the boilerplate, then you verify every line.
- **When to use:** Sub-round 1 (build a new project), where the spec is clear.
- **The risk:** the AI generates code that looks right but has subtle bugs. Verify every line.

### Pattern 2: "AI as a codebase explorer"

- You're in a new codebase. You use the AI to ask "what does this function do?" and "where is the rate limiter implemented?" You build a mental model.
- **When to use:** Sub-round 2 (extend a codebase), where the codebase is unfamiliar.
- **The risk:** the AI hallucinates the codebase structure. Verify by reading the actual code.

### Pattern 3: "AI as a debugging partner"

- You have a bug. You use the AI to ask "what does this test expect?" and "what's the data flow?" You trace the bug.
- **When to use:** Sub-round 3 (debug a codebase), where the bug is non-obvious.
- **The risk:** the AI proposes fixes that don't address the root cause. Verify by reproducing the bug + testing the fix.

---

## The 5 practical-coding anti-patterns

1. **Skipping the spec.** "I'll just start coding" is a junior answer. The spec is the eval set; the eval set is the contract.
2. **Trusting the AI's code without verification.** The AI generates code that looks right. The bug is in the line you didn't read.
3. **Spending 80 minutes on the code, 10 on the tests.** The tests are the proof. Without them, the code is unverified.
4. **Skipping the README + handoff note.** The handoff is the FDE signal. Without it, the code is a prototype.
5. **Going over time.** 90 minutes is 90 minutes. Practice with a timer. Going over is a red flag.

---

## The 5 AI assistant etiquette rules

1. **Tell the AI what you're building.** "I'm building a CLI tool that does X. Here's the spec." The AI needs context.
2. **Verify every line of AI-generated code.** Read it. Test it. Don't trust the AI.
3. **Use the AI to explore, not to think.** "Where is the rate limiter implemented?" is exploration. "What should the rate limiter look like?" is thinking. The thinking is your job.
4. **Cite the AI in the README.** "This code was drafted with Claude; I verified every line and added 5 tests." The citation is the signal.
5. **Know when to stop using the AI.** If the AI is hallucinating or going in circles, stop. Read the code yourself.

---

## How to use this module

1. **Pick a target company.** Meta = Sub-rounds 1, 2, 3 (all 3). Anthropic = Sub-rounds 1, 2. OpenAI = Sub-round 1 + 3.
2. **Practice the 3 sub-rounds.** 90 minutes each, timed.
3. **Use an AI assistant in the practice.** Cursor, Claude, Copilot, whichever you have. The interview will use one.
4. **Deliver all 5 deliverables per sub-round.** The 5 are the FDE signal.
5. **Rehearse with an AI assistant as the interviewer.** Have it score you on the 5 anti-patterns.
6. **Cite the AI in the README.** The citation is the meta-signal: you understand how to work with AI in production.

---

## The 3 most common practical-coding follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "How did you use the AI assistant?" | "I used it as a typing accelerator for the boilerplate. I drafted the spec, the AI drafted the code, I verified every line. I added 5 tests to verify the AI's code." |
| 2. "What would you do without an AI assistant?" | "I'd write the same code, just slower. The spec is the same; the tests are the same. The AI saves typing time; it doesn't change the design." |
| 3. "What's the bug you fixed, and how would you prevent it?" | "The bug was a race condition in the rate limiter — the in-process dict wasn't thread-safe. The fix was to add a lock. The prevention is to use Redis (Phase 5 P1) for cross-worker consistency. The postmortem is in the repo." |

**Memorize these 3.** They're the Q&A for 80% of practical-coding follow-ups.
