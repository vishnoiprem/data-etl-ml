# 03 — The 4 Leadership Principles (Meta/Amazon-style)

> **Lesson 3 of 7 — Theory** · ~10 min

How to map your stories to a principles-based rubric. Most senior
companies (Meta, Amazon, Google, Stripe) use some form of leadership
principles or values rubric. Understanding the structure lets you
*target* your story to the principle being tested.

---

## 1. What "leadership principles" actually are

A leadership principles rubric is just a **checklist of behaviors
the company has decided are non-negotiable for senior engineers**.
At Amazon, it's the 16 Leadership Principles. At Meta, it's
roughly 9 "People & Purpose" attributes. At Google, it's the
"Googleyness" + leadership rubrics. At Stripe, it's 7 operating
principles.

The exact list doesn't matter for this lesson. What matters is the
**pattern**: the company is using these principles as a proxy for
"if you exhibit these behaviors, you'll probably be a good senior
engineer here." The interviewer is looking for **evidence of each
principle** in your stories.

This is good news: if you know the principles in advance, you can
*deliberately* tell stories that demonstrate them. The interviewer
isn't testing whether you stumbled into the right behavior; they're
testing whether you can recognize and articulate it.

---

## 2. The 4 universal principles

Most senior companies' rubrics, when you collapse them, hit these
four things. Memorize them. Every story should demonstrate at
least one, ideally two.

### Principle 1: Earn Trust

**What it sounds like at the company:**
- "Earn Trust" (Amazon)
- "Build trust through transparency" (Stripe)
- "Trust and respect" (Googleyness)
- "Direct, respectful, inclusive" (Meta)

**What the interviewer is looking for:** you tell the truth
even when it's uncomfortable, you don't blame, you don't
exaggerate, you admit what you don't know, and you credit others
where credit is due.

**Stories that demonstrate Earn Trust:**
- "I had a deadline I was going to miss. I told my manager 2
  weeks before, not the day of. We re-scoped together."
- "I disagreed with my PM's framing of the project. I told
  them directly, in private, with my reasoning. We changed
  course."
- "I made a mistake in production. I wrote a public postmortem,
  including the part where I was at fault."

**Stories that FAIL to demonstrate Earn Trust:**
- Anything that blames another person.
- Anything that overstates your contribution.
- Anything that hides bad news.

### Principle 2: Bias for Action

**What it sounds like at the company:**
- "Bias for Action" (Amazon)
- "Move fast and fix things" (Stripe)
- "Bias toward action" (Meta)
- "Comfort with ambiguity" (Google)

**What the interviewer is looking for:** you don't wait for
perfect information, you make calls with what you have, and you
iterate. The opposite — analysis paralysis, consensus-seeking,
escalating every decision — scores low.

**Stories that demonstrate Bias for Action:**
- "I had a 1-line mandate. I interviewed 4 users, identified
  the real problem, scoped to it, and shipped in 6 weeks."
- "Production was down. I didn't have full root cause but the
  mitigation was clear. I rolled the mitigation, then debugged
  the root cause in parallel."
- "I had a 70% solution and a 100% solution. The 100% took 3
  more weeks. I shipped the 70% and iterated based on usage."

**Stories that FAIL to demonstrate Bias for Action:**
- "We held a series of meetings to align stakeholders..."
  (alignment without action)
- "I escalated to my manager because I wasn't sure..."
  (escalation as a substitute for action)
- "We waited until we had a complete picture..." (waiting
  without a decision trigger)

### Principle 3: Dive Deep

**What it sounds like at the company:**
- "Dive Deep" (Amazon)
- "Strong opinions, loosely held" (Stripe)
- "Go deep" (Meta)
- "Technical depth" (Google)

**What the interviewer is looking for:** you actually understand
the system, the data, the code, the tradeoffs — at a level below
the surface. You can be specific. You know the *why* of the
decisions, not just the *what*.

**Stories that demonstrate Dive Deep:**
- "I noticed the p99 spike was concentrated on a specific
  shard. I dug into the query plan, found the index was missing
  on the tenant_id column, and added a covering index. p99
  dropped from 1.2s to 180ms."
- "I read the source of the library we were using. Found a
  memory leak in the connection pool. Reported upstream,
  contributed the fix, and we shipped a patched version."

**Stories that FAIL to demonstrate Dive Deep:**
- Anything that's all architecture diagrams and no specifics.
- "We used the right tool for the job" (which tool? why?)
- "I delegated the deep work to X" (you weren't the diver).

### Principle 4: Deliver Results

**What it sounds like at the company:**
- "Deliver Results" (Amazon)
- "Raise the bar" (Google)
- "High bar" (Meta)
- "Make impact" (most companies)

**What the interviewer is looking for:** you finish. You have
specific, measurable outcomes. The work didn't just happen to
you — you drove it.

**Stories that demonstrate Deliver Results:**
- "We shipped on Aug 14, the partner renewed for $2.4M ARR,
  and the pattern is now the default for the team."
- "P99 went from 2.4s to 380ms. We saved 2 application servers
  ($40k/year). The fix is now a standard library we open-sourced."

**Stories that FAIL to demonstrate Deliver Results:**
- "We did a lot of good work" (vague)
- "It was a great experience" (no outcome)
- "It was eventually deprecated" (passive voice, no one shipped)

---

## 3. The matrix

The four principles, with which question categories they map to
most cleanly:

|  | Earn Trust | Bias for Action | Dive Deep | Deliver Results |
|---|---|---|---|---|
| Leadership | X | X | | X |
| Conflict | X | | | X |
| Failure | X | | | |
| Ambiguity | | X | X | X |
| Technical depth | | | X | X |
| Ownership | X | X | | X |
| Helping | X | | X | |

Notice: **Earn Trust** shows up in almost every category, because
trust is the foundation. **Dive Deep** is concentrated in technical
depth and helping. **Bias for Action** is concentrated in
ambiguity and ownership.

The senior move: when you build your story bank, **tag each story
with which principle(s) it most cleanly demonstrates**. Then when
you walk into the interview, you can pull the right story for the
right question.

---

## 4. The trap

The trap with principles-based interviewing is **story-shipping**
— cramming your story with as many principle keywords as possible
to maximize your score.

> *"I earned trust by being direct, I had a bias for action by
> moving fast, I dove deep by reading the source, and I delivered
> results with measurable impact..."*

This is obviously performative. The interviewer can hear the
keyword salad. The senior move is to **let the story demonstrate
the principle**, not to announce it. The interviewer will
recognize Earn Trust in a story where you admitted a mistake and
wrote a postmortem. You don't have to say "this demonstrates Earn
Trust."

---

## Try it

Take your 4 strongest stories and tag each with the principle it
most cleanly demonstrates. Then ask: which of the 4 principles is
*least* covered by your stories? That's the one to work on in
the Story Bank module.
