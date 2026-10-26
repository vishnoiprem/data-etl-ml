# 04 — Approaching the 3 Question Types

> **Lesson 4 of 8 — Fast Track** · ~15 min

Every behavioral question falls into one of three buckets. Each
bucket has a slightly different optimal structure. Most candidates
treat them all the same way — and that costs them points.

---

## 1. The three buckets

Almost every question you'll be asked in the behavioral round is one
of these three:

1. **Past-behavioral** — "Tell me about a time you..."
2. **Hypothetical** — "What would you do if..."
3. **Values-and-judgment** — "Tell me about a time you disagreed
   with someone" / "How do you handle X" / "What's your biggest
   weakness"

They sound similar but the interviewer is grading different things
in each. The same story, told with the same structure, can score
high on one type and low on another. You need to **read the
question, identify the bucket, and pick the right structure**.

---

## 2. Type 1: Past-behavioral

**Form:** "Tell me about a time you [led a project / disagreed with
a coworker / missed a deadline / dealt with ambiguity]."

**What the interviewer is testing:** evidence. They want to know
*whether you have actually done the thing.* The past-behavioral
question is the most common and the most forgiving — you get to
draw from your actual experience.

**The structure:**

```
1. The setup (15 sec)        — context, who, what, when
2. The tension (15 sec)      — what was hard / conflicting / unclear
3. Your specific action (45s) — what YOU did, with specifics
4. The outcome + impact (30s)— what happened, with a number
5. The takeaway (15 sec)     — what you learned or would do differently
```

Total: ~2 minutes. Anything longer than 2:30 and you've lost the
interviewer.

**Sample answer** (for "Tell me about a time you led a project
with a hard deadline"):

> *"In Q2 last year I led the migration of our analytics pipeline
> from a batch system to streaming, with a hard deadline tied to a
> partner's launch on August 15. The tension was that the partner
> couldn't move, but the engineering team had realistic estimates
> of 12 weeks and we only had 10.*
>
> *What I did: I negotiated scope with the partner. They needed
> three specific metrics, not the full pipeline. I cut the project
> to those three, which got us to 8 weeks. I then negotiated the
> remaining 2 weeks by offering a 4-week shadow-mode period where
> both systems ran in parallel — the partner got their metrics
> on time and we got the safety net to migrate the rest.*
>
> *Outcome: we shipped the three metrics on August 14, the full
> migration finished in October with zero data incidents, and the
> partner renewed for a second year, which was about $2.4M in
> ARR.*
>
> *What I'd do differently: I'd set up the partner scoping
> conversation earlier. We wasted 2 weeks because I assumed
> 'full pipeline' was the deliverable when they would have
> accepted partial."*

Notice: setup is 30 sec, tension is 15 sec, action is 60 sec,
outcome is 30 sec, takeaway is 20 sec. ~2:30. There's a specific
number ($2.4M). The takeaway is a specific change, not a vague
"I learned to communicate."

See `02_theory/01_star_method.md` for the full STAR / CAR / PAR /
SOAR variants.

---

## 3. Type 2: Hypothetical

**Form:** "What would you do if you had 2 weeks to ship a feature
that normally takes 8?" / "How would you handle a teammate who
isn't pulling their weight?"

**What the interviewer is testing:** judgment under ambiguity. They
know you haven't faced *this exact* situation. They want to see how
you *reason* about it — what you prioritize, what you ignore, what
you'd push back on.

**The structure:**

```
1. Clarify the constraint (15 sec) — restate the tension in your
   own words
2. Name the options (30 sec)        — 2-3 distinct approaches you'd
   consider
3. Pick one and justify (45 sec)   — "I'd do X because Y, given Z"
4. Name the risks you'd watch (15s) — what would make you change
   your mind
```

Total: ~2 minutes.

**Sample answer** (for "2 weeks to ship an 8-week feature"):

> *"First, I'd want to clarify the constraint — is the deadline
> truly hard (contractual, regulatory) or is it a soft target
> (executive preference)? That changes everything.*
>
> *Assuming it's hard, I'd propose three options to my manager:
>  1. Cut scope to the smallest viable subset that meets the
>     deadline (e.g. one user segment, one geography, read-only).
>  2. Ship the full scope with reduced quality (skip the nice-to-
>     haves, defer the optimization) and a known-bugs list.
>  3. Push back on the deadline with a concrete cost-of-delay
>     argument.*
>
> *My default would be option 1 — cut scope ruthlessly. The
> trap with hypothetical deadlines is that everyone agrees to the
> full scope in week 1 and we end up with option 2 by week 2.
> Better to negotiate scope early and explicitly.*
>
> *What would make me change my mind: if the user-visible impact
> of cutting scope was worse than the impact of slipping, or if
> the underlying reason for the deadline was political rather than
> real."*

Notice: this answer is **structured as a framework, not a story**.
That's the right move for hypotheticals. The interviewer is testing
how you think, not what you did.

See `02_theory/04_signal_vs_noise.md` for what "thinking out loud
well" actually signals.

---

## 4. Type 3: Values-and-judgment

**Form:** "What's your biggest weakness?" / "Tell me about a time
you had to give someone hard feedback" / "Describe a time you
pushed back on a decision you disagreed with."

**What the interviewer is testing:** character. They're trying to
find out what you actually *value* — what you think good
collaboration looks like, what you think blame and ownership mean,
what you do when no one is watching.

**The structure:**

```
1. The value (15 sec)      — name the principle in plain language
2. The specific instance (60s) — a real past story that
   demonstrates it
3. The cost you paid (15s) — what was hard about living this value
4. The compounding (15 sec)  — what it earned you / the team / the
   org
```

Total: ~2 minutes.

**Sample answer** (for "Tell me about a time you had to give
someone hard feedback"):

> *"I believe that the earlier and more specifically you give
> feedback, the more it costs the giver and the more it saves
> the receiver. So I try to give feedback inside 48 hours of the
> behavior, in private, with a specific observation and a
> specific ask.*
>
> *Concrete instance: I had a peer on my team whose code reviews
> were taking 4-5 days, which was blocking the team. I could
> have gone to his manager. Instead I messaged him on a Friday
> afternoon — specific: 'the last three PRs I sent you sat for
> 4+ days, which delayed my work by a week.' Asked: 'what would
> unblock you — is it capacity, unclear specs, or something
> else?' It turned out his manager had piled two urgent asks
> on him that I didn't know about. We restructured the spec-
> review process so reviews were bundled, and his median review
> time went from 4 days to 18 hours.*
>
> *The cost: that conversation was uncomfortable and I
> procrastinated on it for two weeks. The compounding: he
> became one of my strongest collaborators and we co-led the
> next quarter's architecture review."*

Notice: the value is named up front, the story is specific, the
cost is acknowledged (no "I just love giving feedback" pretense),
and the outcome is concrete.

---

## 5. A cheat sheet for the room

| Question contains... | Bucket | Key move |
|---|---|---|
| "Tell me about a time you..." | Past-behavioral | STAR, 2 minutes, one number |
| "What would you do if..." | Hypothetical | Name 2-3 options, pick one, name the risks |
| "How do you handle..." / "What's your biggest weakness" | Values-and-judgment | Name the value, ground it in a specific story |

If you can't tell which bucket, **default to past-behavioral**. It's
the most forgiving, the most natural, and the most common.

---

## Try it

Take 3 questions (one from each bucket) and answer each using the
right structure. Time each at 2 minutes. Listen back.

The point of the exercise is to *feel* how the structure of the
answer changes with the bucket. Most candidates default to
past-behavioral structure on every question — and it costs them
on hypotheticals especially.
