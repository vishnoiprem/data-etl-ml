# Google's Official Interview Guidance — and How to Apply It to Your DE Round

> Source: Google's own "How to prepare for Google's technical interview questions" video, presented by Okwus (technical recruiter) and Jules (program manager). This is the most authoritative source in your prep set — it's Google telling you directly what they evaluate. Use it for the universal **behaviors and mindset**; keep your **topic** prep calibrated to the data-engineer-specific sources (medium SQL + Python + code comprehension, not NP-complete proofs or OS internals).

---

## LOGISTICS (confirmed by Google)
- Interviews are virtual, on **Google Meet**.
- You'll get an email with date, time, and the Meet link from recruiting.
- Have ready: a Meet-compatible computer, a webcam, a phone as audio/video backup, and your preferred method for note-taking / sharing code.
- Interviewers take notes on paper or laptop — normal, don't read into it.
- You work in a **shared document** — **no IDE, no compiler, no autocomplete, no run button.**
  - **Action:** practice all coding on a whiteboard, Google Doc, or paper. (This is now the *third* source telling you this — treat it as mandatory.)

---

## WHAT GOOGLE IS ACTUALLY EVALUATING
> "We're not just evaluating your technical abilities, we're also interested in understanding how you approach and try to solve problems."

Translation: **how you think out loud is scored alongside whether your code works.** A silent correct answer scores worse than a well-narrated, slightly-imperfect one.

---

## THE 4 BEHAVIORS GOOGLE REWARDS (use as a per-question checklist)

### 1. Explain and clarify — out loud, the whole time
> "Talk to us. Show us your work and explain your thought process and decision making throughout the entire interview."
- Narrate continuously. Don't go silent while thinking.

### 2. Verbalize and check your assumptions
> "Many of the questions asked in our interviews are deliberately vague because our engineers are looking to see how you engage the problem."
- Ask clarifying questions before coding: input size? nulls? duplicates? sorted? expected output format?
- State assumptions explicitly: "I'll assume the file doesn't fit in memory, so I'll stream it."

### 3. Improve your first answer (don't stop at brute force)
> "Jumping immediately into presenting a brute-force solution will be less well-received than trying to take time to compose a more efficient solution."
- Nuance: it's fine to *name* the brute force ("naively this is O(n²)"), but then move toward the efficient solution rather than dumping the brute force and stopping.
- For design/algorithm questions: offer **multiple solutions and discuss their relative merits.**

### 4. Practice, test, and mind your pace
> "Be mindful of your pace because we do factor that into our evaluation."
- Test your own code; make it readable and bug-free.
- Volunteer edge cases without being asked.

---

## TESTING — GOOGLE CALLS THIS OUT TWICE (don't forget it)
Be ready to answer:
- "How would you unit test the code you write?"
- "What interesting inputs or test cases can you think of?"

For your DE round, good edge cases to volunteer: empty input, single element, all duplicates, nulls/None, malformed rows, very large input that won't fit in memory, and boundary timestamps.

---

## TECHNICAL AREAS GOOGLE LISTS (generalist) — vs. WHAT MATTERS FOR YOUR DE ROUND

| Google's generalist list | Relevance to your DE Code-Comprehension round |
|--------------------------|----------------------------------------------|
| Data structures (arrays, hash tables, linked lists, stacks, queues, priority queues) | **HIGH** — especially arrays, hash tables, sets |
| Big-O / time & space complexity | **HIGH** — your round literally asks "what's the complexity / how to improve" |
| Recursion | **MEDIUM** — know it; used for flattening nested structures |
| Sorting & trees | **MEDIUM** — know basics; heaps for top-N are useful |
| Dynamic programming | **LOW–MEDIUM** — know popular ones (climbing stairs level), not exotic DP |
| Graphs (BFS/DFS, representations, cycle detection) | **LOW** — basic awareness only, per DE sources |
| NP-complete (traveling salesman, knapsack) | **LOW** — recognize the names; you won't be solving them |
| Probability & combinatorics (n-choose-k) | **LOW** — unlikely for DE |
| OS concepts (threads, mutexes, semaphores, deadlock) | **LOW** — only if a systems-design round, not your coding round |

> Google explicitly says: "exact interview types will vary by role... ask your recruiter for more specific technical expectations." **This is a direct nudge to take your recruiter's prep call** — it's the single best way to confirm exactly what your round covers.

---

## THE PER-QUESTION ROUTINE (built from Google's own advice)
1. **Clarify** — restate the problem, ask about ambiguity, state assumptions.
2. **Approach aloud** — name a brute force, then propose something better; for design, offer 2 options + trade-offs.
3. **Code while narrating** — explain each decision as you write.
4. **Test** — walk an edge case yourself; mention how you'd unit test it.
5. **Complexity** — state time and space, then how you'd improve further.
6. **Pace** — keep moving; don't freeze in silence.

---

## BOTTOM LINE
- Use this video for **universal behaviors**: talk, clarify, improve, test, pace.
- Use your **DE-specific transcripts** for **topic scope**: medium SQL (window functions, partitioning), medium Python (data structures, streaming/generators), and the "output / complexity / improve" code-comprehension format.
- Don't over-prepare NP-complete, OS internals, or heavy DP/graphs for a DE coding round.
- **Take the recruiter prep call** — Google itself tells you to confirm expectations with your recruiter.
