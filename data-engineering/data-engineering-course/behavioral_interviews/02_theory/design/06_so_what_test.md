# 06 — The "So What?" Test: Adding Impact to Every Story

> **Lesson 6 of 7 — Theory** · ~10 min

A 5-question gut-check that every answer must pass before you
tell it. The "so what" test is the difference between an answer
that describes work and an answer that demonstrates senior
judgment.

---

## 1. The test

For every story, ask these 5 questions. If you can't answer
"yes" to at least 4 of them, don't tell the story.

1. **Did I make a call?** — Is there a moment in the story
   where I made a decision, not just executed?
2. **Was the call hard?** — Was there a real tradeoff, real
   ambiguity, or real cost?
3. **Did something change because of me?** — Is the outcome
   a function of my action, not a function of luck or other
   people?
4. **Can I quantify the change?** — Is there a number (time,
   money, scale, count) attached to the outcome?
5. **Did I learn or grow something transferable?** — Is there
   a takeaway that applies to more than just this one project?

If you can answer 5/5, you have a strong senior story. If you
can answer 3-4/5, you have a workable story that may need a
rewrite. If you can answer 0-2/5, retire the story.

---

## 2. Worked examples

### Story A: "I led the streaming migration"

| # | Question | Answer |
|---|---|---|
| 1 | Did I make a call? | Yes — chose dual-write with shadow validation over big-bang cutover |
| 2 | Was the call hard? | Yes — partner had a hard deadline, my team was risk-averse |
| 3 | Did something change because of me? | Yes — 14 schema mismatches caught before production |
| 4 | Can I quantify the change? | Yes — 24h to sub-minute freshness, $0 in incident cost, partner renewed $2.4M |
| 5 | Did I learn something transferable? | Yes — the dual-write pattern is now used for the next 2 migrations |

**Score: 5/5.** Strong story.

### Story B: "I refactored the API to use async/await"

| # | Question | Answer |
|---|---|---|
| 1 | Did I make a call? | Hmm, it was sort of the obvious next step |
| 2 | Was the call hard? | No, the rest of the team agreed it was the right move |
| 3 | Did something change because of me? | Yes, the API got faster |
| 4 | Can I quantify the change? | Yes, p99 went from 1.2s to 180ms |
| 5 | Did I learn something transferable? | Not really, it was just a normal refactor |

**Score: 3/5.** Workable but weak. The hard call and the
transferable lesson are missing. To fix: reframe as a
*performance-driven* decision, not a refactor. The "hard call"
becomes "I had to choose between async/await (faster, riskier
because of existing sync dependencies) and a thread pool (safer,
slower). I prototyped both and chose async/await." The
transferable lesson becomes "the prototype-both pattern has
saved me from bad calls on the next two similar decisions."

### Story C: "I attended the architecture review"

| # | Question | Answer |
|---|---|---|
| 1 | Did I make a call? | No, I just attended |
| 2 | Was the call hard? | No |
| 3 | Did something change because of me? | No |
| 4 | Can I quantify the change? | No |
| 5 | Did I learn something transferable? | Maybe |

**Score: 0-1/5.** Do not tell this story. It is a task, not a
story. Find a different story from the same time period, or
reframe to surface the actual decision you made (you may have
participated in the decision without realizing it).

---

## 3. The "so what" pass

Once you have a story that passes the 5-question test, do a
final pass. Read the story out loud. After every sentence, ask
yourself: *"So what?"* If the sentence doesn't earn its place
by answering "so what," cut it.

Example:

> *"I was working on a project at my company. The project was
> a migration from batch to streaming. The team was in San
> Francisco. The system processed 50M events per day. I had
> been at the company for 3 years. So I was assigned to lead
> the project."*

Each of these sentences can be cut without losing the story.
The "so what" of "I was at the company for 3 years" is
nothing. Cut. The "so what" of "the system processed 50M
events per day" is the scale. Keep.

The senior move is to **delete every sentence that doesn't
answer "so what"**. This is the single highest-ROI edit you
can make to a story.

---

## 4. What to do when the numbers are gone

A common frustration: "I don't have a number for that." The
project was important but the impact was qualitative. You can't
manufacture a number that doesn't exist.

The fix is in `05_workshops/02_quantifying_impact.md`. Short
version:

- **Time:** "We cut processing time from 8 hours to 45 minutes"
- **Scale:** "It now serves 4x more users without a re-architect"
- **Money:** "Saved ~$40k/year in cloud spend"
- **People:** "3 engineers now use this pattern as their default"
- **Frequency:** "Reduced on-call pages from 2x/week to 1x/month"
- **Reliability:** "Zero incidents in the 6 months since"

If you genuinely don't have *any* of these, the story may not
be a senior story. Find a different story.

---

## Try it

Take 3 stories from your story bank. Run each through the
5-question test. Score each 0-5. If any story scores below
3, retire it. If any scores 3-4, rewrite the missing pieces
using the worked examples above as a template.

The goal: every story in your bank scores 4 or 5.
