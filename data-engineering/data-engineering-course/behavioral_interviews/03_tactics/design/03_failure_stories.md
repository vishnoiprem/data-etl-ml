# 03 — Failure Stories: Showing Growth, Not Blame

> **Lesson 3 of 6 — Story Bank** · ~12 min

3 templates for failure stories, with worked examples. The
failure story is the most common downlevel vector at senior+.
Done well, it's also the highest-leverage story you have.

---

## 1. Why failure stories are the highest-leverage

A leadership story shows the interviewer what you did. A
failure story shows them what you *learned*. The interviewer's
internal question on leadership is "can this person drive
outcomes?" On failure, the question is "will this person
*get better* on the job?"

A senior engineer who can't articulate a clean failure story
reads as someone who either (a) doesn't take responsibility,
or (b) hasn't been in roles hard enough to fail at. Both are
bad. The candidate who tells a clean failure story — with a
specific cause, a specific change, and a measurable
follow-up — reads as someone who will be a better engineer
in year 2 than year 1.

---

## 2. Template 1: The missed-estimate story

**The shape:**

> I committed to [X] by [date]. I missed. The cause was
> [specific, not generic]. The change I made was [specific].
> The result has been [measurable].

**Worked example:**

> *I committed to delivering the new analytics dashboard by
> end of Q3. I missed by 4 weeks. The proximate cause was
> scope creep — 3 new requirements came in during the
> project. The root cause was mine: I had treated each new
> requirement as a one-off request instead of a signal that
> I didn't have a shared definition of done with the PM. I
> just kept absorbing the changes.*
>
> *What I changed: at the start of every project now, I
> write a 1-page "definition of done" doc with my PM
> counterpart, signed off by both of us before any code is
> written. Any change to the doc is treated as a scope
> change, with an explicit re-estimate and a decision from
> the PM about whether to slip the deadline or cut scope.*
>
> *Outcome: we have been within 10% of estimate on the last
> 4 projects, and the PM team has started adopting the same
> practice.*

**The senior signals:**
- A *specific* cause (no shared definition of done) — not
  "the requirements changed" or "I was busy"
- A *specific* change (definition of done doc, signed off)
  — not "I learned to communicate better"
- A *measurable* follow-up (within 10% on 4 projects) — not
  "I've been more careful"
- A *propagated* practice (PM team adopted it) — not "it's
  helped me"

---

## 3. Template 2: The wrong-technical-decision story

**The shape:**

> I designed/built [X] using [approach Y]. It turned out to
> be the wrong approach because [specific reason]. The fix
> was [what we did]. The lesson is [transferable].

**Worked example:**

> *I designed the new logging pipeline using a pull-based
> model — services would query the log aggregator on demand.
> It worked for 2 months. Then we scaled to 30 services and
> the query load on the aggregator exploded. P99 latency
> went from 200ms to 12 seconds. The fundamental mistake:
> pull-based logging doesn't scale linearly with the number
> of services, because each service has independent query
> patterns and they don't batch.*
>
> *What we did: we ripped out the pull layer and replaced it
> with a push-based model where each service streams to a
> Kafka topic, and a downstream consumer indexes into
> Elasticsearch. Migration took 3 weeks. P99 came back down
> to 180ms.*
>
> *The lesson: for any system where the read pattern is
> "many small queries from many sources," pull-based
> doesn't scale. The threshold I now use is: if the number
> of producers × the per-producer query rate exceeds
> [number], push-based is the right default. I've used this
> rule on 3 systems since.*

**The senior signals:**
- A *specific* technical mistake (pull-based doesn't scale
  with N producers)
- A *named* threshold or rule (the "if producers × rate
  exceeds N, push" rule)
- A *transferable* takeaway (used on 3 systems since)
- A *measure* of the recovery (12s → 180ms)

**The trap:** it's easy to tell this story as "we tried X,
it didn't work, we tried Y, it worked." The senior move is
to extract a *generalizable rule* — what threshold tells
you which approach is right, and what would you do
*differently* in the design phase to avoid needing to
migrate.

---

## 4. Template 3: The people-failure story

**The shape:**

> I had a [person / team / situation] and I [handled it
> wrong]. The impact was [specific]. The change I made was
> [specific]. The result is [measurable].

**Worked example:**

> *A peer on my team was consistently missing sprint
> commitments — about 60% of his stories slipped by a week
> or more. My first instinct was to escalate to my manager.
> I didn't. Instead, I avoided the conversation for 2
> months. The cost: the team started picking up his slack,
> morale dropped, and 2 of the affected engineers came to
> me privately to ask what was going on. The thing I did
> wrong: by not surfacing the issue, I let it become a
> team-wide morale problem instead of a 1:1 problem.*
>
> *What I changed: I now raise performance concerns within
> 2 weeks of seeing a pattern, in private, with specific
> observations. I frame it as "I'm noticing X, what would
> unblock you?" rather than "you have a problem." I also
> explicitly ask my manager for help if the 1:1 doesn't
> resolve it within a sprint.*
>
> *Result: I had to have 2 of these conversations in the
> following year. One resolved quickly (the person was
> dealing with a personal issue and didn't realize it was
> visible). The other was a more serious performance
> conversation that I escalated to my manager after 2
> weeks. Both situations improved faster than the
> avoidance pattern would have.*

**The senior signals:**
- A *self-aware* acknowledgment (you were wrong, you
  avoided)
- A *specific* cost (team morale dropped, 2 engineers came
  to you)
- A *named* rule (raise within 2 weeks, in private, with
  specifics)
- *Measured* follow-up (2 conversations in the next year,
  both resolved)

**The trap:** people-failure stories can sound like bragging
("I saved the team by intervening"). The senior framing is
the *growth* — what you now do, what you learned, and how
the team is better for the change.

---

## 5. What to do if you can't find a senior failure

If you're a senior engineer with 5+ years of experience, you
have failure stories. If you think you don't, you're not
looking hard enough. The Workshop in
`05_workshops/01_story_mining.md` walks you through the
extraction process.

If you genuinely don't have a senior failure — i.e. your
biggest failure is "I missed a small deadline once" — that's
information. It might mean you haven't been in roles with
enough scope to have senior-level failures. In which case
the interview may be calibrated wrong, or you may need to
get a more senior role first.

---

## Try it

Pick one of the 3 templates. Write your own version using your
career. Apply the 5-question "so what" test from
`02_theory/06_so_what_test.md`. The bar for failure stories is
especially high — they have to be specific, self-aware, and
show measurable growth. If your draft feels generic, dig
deeper.
