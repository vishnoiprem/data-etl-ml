# 02 — Workshop: Quantifying Impact

> **Lesson 2 of 5 — Workshops** · ~12 min

6 categories of numbers you can use, and how to extract or
estimate each one. Numbers are the single biggest senior
signal. This workshop gives you a number even when you think
you don't have one.

---

## 1. The 6 categories

Almost every story can be quantified in at least one of these
6 ways:

| # | Category | Example |
|---|---|---|
| 1 | **Time saved** | "Cut processing time from 8 hours to 45 minutes" |
| 2 | **Scale** | "Now serves 4x more users without a re-architect" |
| 3 | **Money** | "Saved $40k/year in cloud spend" |
| 4 | **People** | "3 engineers now use this pattern as their default" |
| 5 | **Frequency** | "Reduced on-call pages from 2x/week to 1x/month" |
| 6 | **Reliability** | "Zero incidents in the 6 months since" |

If your story has a number from any one of these categories,
it scores higher than a story with no number. Two categories
is even better.

---

## 2. How to extract the number

For each story in your bank, ask the 6 questions:

1. **Time:** Did I save anyone's time? How much, per what
   period? ("Saved 10 hours/week of manual work for the CS
   team")
2. **Scale:** Did the system handle more load, more users,
   more data? ("Now handles 4x the QPS")
3. **Money:** Did it save or make money? ("Saved $40k/year
   in cloud spend")
4. **People:** Did the pattern propagate? ("3 teams adopted
   it within 6 months")
5. **Frequency:** Did anything happen less often? ("Reduced
   data-quality incidents from 8/quarter to 1/quarter")
6. **Reliability:** Is the system more reliable now? ("Zero
   outages in the 8 months since")

If you can answer 1-2 of these with a specific number, you
have a senior story. If you can answer 3+, you have a
*strong* senior story.

---

## 3. How to estimate when you don't have the number

Sometimes the number isn't in your head. You didn't write it
down at the time. The project is from 4 years ago. The data
is gone. You have 3 options:

### Option 1: Reconstruct from artifacts

You probably have *some* artifact. Pull request descriptions,
design docs, postmortems, performance dashboards (if the
project is still running), manager feedback. The number may
not be in your head, but it's probably in your email,
Slack, or Notion somewhere. 15 minutes of searching usually
finds it.

### Option 2: Estimate from inference

If the artifacts are gone, estimate. The estimate doesn't
have to be exact — the interviewer is grading whether you
*think in numbers*, not whether you have a precise figure.

Use the "order of magnitude" framing:

- "Saved roughly 10 hours/week of manual work" (vs "saved
  precisely 11.4 hours/week")
- "Cut p99 latency by roughly 5x" (vs "from 1200ms to 245ms")
- "Probably saved about $30-50k/year in cloud spend" (vs
  "saved $42,318.27")

The estimate with a range ("$30-50k") is actually more
believable than a precise number. Real engineers estimate.

### Option 3: Substitute a related number

If you genuinely don't have a number for the *outcome*,
substitute a number for a *related dimension*:

- "We don't have a direct $ number, but the change freed up
  about 30% of one engineer's time, which we reallocated to
  the X project."
- "We don't have a direct user-facing number, but the
  on-call burden dropped from 2 pages/week to 1/month."
- "We don't have a direct adoption number, but the design
  doc was cited by 4 subsequent project proposals."

The substitute is honest if you flag it ("we don't have a
direct number, but..."). The interviewer will accept the
substitute as evidence of numerical thinking.

---

## 4. The 4 traps to avoid

### Trap 1: Fake precision

> "I improved the system by 47.3%"

No one believes this. Real engineers round. Real engineers
say "about half" or "roughly 5x" or "close to 10x." Fake
precision signals dishonesty or naivety.

### Trap 2: Vague numbers

> "Significant improvement" / "substantial cost savings" /
  "many more users"

These are not numbers. The interviewer reads them as
"this person doesn't have a number." Always have a
specific number, even if it's an estimate.

### Trap 3: Numbers without context

> "Reduced latency to 180ms"

So what? 180ms is great for some systems and terrible for
others. The number needs context: "Reduced p99 from 1.2
seconds to 180ms" or "Reduced p99 to 180ms, which is well
under our 500ms SLO."

### Trap 4: Numbers that don't match the question

> "I saved 5 minutes per day" (when the question was about
  a 6-month project)

The number should be *proportional* to the story. A 5-minute
saving on a 6-month project is rounding error. A 5-minute
saving on a per-transaction process that runs 10M times a
day is huge. **Scale the number to the story.**

---

## 5. Worked example: turning a numberless story
into a numbered one

**Before:**

> *"I refactored the API to use async/await. It was much
> faster and the team was happy."*

No number. Vague outcome. "Much faster." "The team was
happy." Both are red flags.

**After (extracted numbers):**

> *"I refactored the API from sync request handlers to
> async/await. The work was prompted by our p99 latency
> creeping up as the user base grew. The refactor took
> p99 from 1.2 seconds to 180ms — about a 6x improvement
> — and freed up 2 of our 4 application servers because
> the async model handles concurrent load with less
> memory. The cloud spend drop was about $40k/year. The
> 2 reclaimed servers went to the new search service
> the team had been wanting to launch for 2 quarters."*

Three numbers, three categories (latency, infrastructure,
money), and the third number has a follow-on story
(2 servers reclaimed for the search service). Strong.

---

## 6. The number-finding pass

Take every story in your bank. For each, write down:

- The number I have: [Y/N]
- If yes, the number: ___
- If no, the 3 most likely places to find it: ___
- If I can't find it, my best estimate: ___

The output is a story bank where every story has a number.
This is the single biggest upgrade you can make to your
interview performance, and it takes 1-2 hours.

---

## Try it

Take 3 stories from your bank that don't have a number.
Spend 20 minutes on each, applying the 6-category test
from Section 2 and the 3 estimation strategies from
Section 3. By the end, all 3 stories should have a
specific number.

The "before" and "after" of those 3 stories is the most
concrete measure of progress in this whole course.
