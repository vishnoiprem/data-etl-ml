# 06 — Delegation and Trust

> **Lesson 6 of 21 — Managing Individuals** · ~20 min

The 4 levels of delegation (do, show, supervise, delegate-and-trust),
how to climb the ladder with each direct report, and the 2-3
signals you're over- or under-delegating. Delegation is the
substrate for growth — if you can't delegate, you can't grow
people, and you'll end up doing the work yourself.

---

## 1. The 4 levels of delegation

Most new EMs delegate at one of 2 levels: "I'll do it" or
"figure it out." Both are wrong. The senior move is to operate
on a 4-level ladder and to deliberately climb the ladder with
each person over time.

| Level | What it looks like | When to use it |
|---|---|---|
| **Level 1: Do** | You do the work, the engineer shadows or assists. | First time the engineer has touched the work; high-stakes or irreversible. |
| **Level 2: Show** | You do the work while narrating, the engineer does it next time with your support. | Engineer has the context but not the muscle. |
| **Level 3: Supervise** | The engineer does the work, you review and give feedback. | Engineer is competent; you want to coach on quality, not just correctness. |
| **Level 4: Delegate-and-trust** | The engineer owns the work end-to-end. You get a status update at agreed intervals. | Engineer has demonstrated competence at Level 3; the work is bounded; the stakes are understood. |

Most engineers are at Level 1 or 2 for new work, and the
question is how fast they move to Level 4. The senior move is
to be **explicit about the level with the engineer**. The
script:

> *"For this project, I want you at Level 3 — you do the work,
> I'll review and give feedback weekly. After the project, if
> it's gone well, we move to Level 4 and you own it solo. The
> first 2 weeks I'll be in the design reviews; after that I'm
> out unless you ask me in."*

The mistake: staying at Level 3 forever because it's
comfortable for you. Once the engineer is consistently
shipping at Level 3, the right move is to drop to Level 4,
even if the work isn't perfect. Perfection is the enemy of
growth.

---

## 2. The 2-3 signals you're over- or under-delegating

### You're over-delegating if:

- **The engineer keeps coming back with the same question.** Level
  4 is too high; drop to Level 3 for a while.
- **The engineer is visibly anxious.** Quiet in standup, slow to
  flag issues, asking for permission on small calls. That's a
  Level 4 stress signal.
- **The work is being re-done by someone else.** Late catches
  mean the engineer's quality bar is below what's needed.
- **You're checking in more than once a week.** If you said
  Level 4 and you're checking in daily, you're not actually at
  Level 4.

### You're under-delegating if:

- **You're still doing the work yourself.** If you've been at
  Level 3 for more than 2-3 months on the same kind of work,
  the engineer should be at Level 4.
- **The engineer is bored.** A senior engineer who's been at
  Level 3 for a quarter starts interviewing. Don't be surprised.
- **You're the bottleneck on reviews.** If every PR or design
  doc comes through you, you're the constraint on the team's
  throughput.
- **The engineer can't articulate the project's "why."** If
  they only know the "what" and "how," they're at Level 1 or 2.
  Time to climb.

### The signal that matters most

The single most important signal is the engineer's response
to "what's the next hard decision on this project?" If they
can name the decision, name the tradeoff, and tell you what
they're going to do — they're at Level 4. If they look at you
blankly, they're at Level 3 or lower, and the next step is
climbing, not staying.

---

## 3. The "I would have done it myself" trap

The single biggest delegation failure mode for new EMs is
**taking it back**. The engineer is at Level 3 on a project.
They ship something that isn't quite what the EM would have
shipped. The EM silently re-does the work, or the EM escalates
their concerns to a level where the engineer's authority is
undermined.

The pattern looks like care ("I just wanted to make sure it
was good"). The pattern is actually corrosive — it tells the
engineer that the EM doesn't trust them, and the next time
they'll be even more cautious, ask for more permission, and
the team slows down.

The senior move is to **let the engineer ship the imperfect
work, and coach them on the gap afterward**. The coaching
1:1 the next week is "I noticed X, what would you do
differently next time?" — not "I changed X because I thought
it needed to be different."

The exception: the work is so high-stakes that shipping it
imperfect causes real damage. For that, drop to Level 3 or 2
temporarily. But the threshold for "real damage" is high. Most
of what feels like "real damage" is actually "rework," and
rework is a coaching opportunity, not a reason to take it
back.

---

## 4. Delegating to senior engineers

The hardest delegation problem isn't juniors — it's senior
engineers who've been independent for years and are now
managing. The pattern:

- Senior engineer has the technical skills.
- Senior engineer doesn't have the EM context (the
  cross-functional stakeholders, the political landscape, the
  escalation path).
- EM delegates a project at Level 4 because the senior
  engineer *looks* like they should be there.
- Senior engineer ships something that's technically correct
  and politically disastrous.

The fix: **start senior engineers at Level 3 for cross-functional
work, regardless of their technical level.** Level 4 is earned
on cross-functional context, not technical skill. The coaching
1:1 at Level 3 is the place where the senior engineer learns
the EM context, and 2-3 cycles later they're at Level 4.

---

## 5. A worked example: climbing with Aarav

Aarav, an E6 on Sam's team, has been at the company for 4
years. He's the team's Kafka expert. Sam is delegating the
runbook for the new streaming pipeline to him.

> **First 2 weeks (Level 2 — Show):**
> Sam wrote the first draft of the runbook while narrating
> the choices. Aarav took notes, asked 4 questions, and wrote
> the second draft. Sam reviewed and edited heavily.
>
> **Weeks 3-6 (Level 3 — Supervise):**
> Aarav owns the runbook. Sam reviews each section weekly,
> gives specific feedback, and co-presents the runbook in the
> on-call training. Aarav starts to flag tradeoffs in the
> 1:1s that Sam wouldn't have thought of.
>
> **Weeks 7+ (Level 4 — Delegate-and-trust):**
> Aarav owns the runbook end-to-end. He presents the
> quarterly runbook update to the team. Sam is in the room
> but doesn't speak unless asked. The on-call rotation
> defaults to Aarav's runbook for incident triage.
>
> **The signal that Level 4 was right:**
> Six months in, Aarav shipped a v2 of the runbook that was
> better than Sam's v1. He told Sam in a 1:1: "I rewrote the
> incident triage section because your version assumed a
> single-region failure mode and we've had 3 multi-region
> incidents since I started." Sam's response: "That's
> exactly right. Next time, propose the change before you
> ship it so I can review — but the change itself is correct."

**What makes this land:** The climb is explicit, time-boxed,
and signaled to the engineer. The senior move in the final
beat is that Aarav's improvement is treated as a promotion of
his ownership, not a critique of Sam's original. The next
step ("propose before you ship") is process coaching, not
delegation rollback.

---

## 6. Canonical questions this lesson answers

From `docs/reference/em_interview_canonical_questions.md`:

- People Management #5: *"Tell me about a time you delegated
  something important to someone on your team."*
- Behavioral #11: *"Tell me about a time when you had to trust
  your team to make a decision."*
- Behavioral #32: *"Tell me about a time when you had to let
  someone else make a decision."*
- Behavioral #60: *"Tell me about a time when you had to
  empower someone on your team."*
- Behavioral #104: *"How do you decide what to delegate?"*

---

## Try it

For each of your directs, write their name and the level
(1-4) they're at for each of their main workstreams. If
everyone is at Level 1-2 on everything, you're over-
managing. If everyone is at Level 4 on everything, you're
under-managing. The senior move is a portfolio — Level 4 on
the work they've owned for 6+ months, Level 3 on the work
they're climbing into, Level 1-2 on the new work.

---

## Action item

Pick one workstream you're currently at Level 2 or 3 with a
direct. Decide: are you going to climb them to Level 4 in
the next 4 weeks? If yes, write the climb plan — what does
the engineer do, what do you do, how do you know they've
made it. If no, write the reason — and be honest with
yourself about whether the reason is legitimate or whether
it's comfort.