# 20 — Stakeholder Communication and Upward Reporting

> **Lesson 20 of 21 — Cross-functional Collaboration** · ~20 min

Weekly status reports, exec readouts, and the 3 formats for
upward communication. The senior move is to make upward
communication a system, not a series of ad-hoc reports. The
EM who has a predictable cadence, predictable format, and
predictable tone is the EM who gets resources when they ask.

---

## 1. The 3 formats for upward communication

Every upward communication falls into one of 3 formats. The
senior move is to **use the right format for the right
purpose**, and to not mix them.

| Format | Length | Purpose | Audience | Cadence |
|---|---|---|---|---|
| **Weekly status note** | 1 page | Track progress, surface blockers, show predictability | Skip-level | Weekly |
| **Monthly exec readout** | 3-5 pages | Strategic context, decisions needed, big bets | Skip-level, skip-skip, execs | Monthly |
| **Ad-hoc escalation** | 1-2 pages | Surface a specific issue that needs a decision | Whoever can make the decision | When needed |

The mistake: using one format for all three. The weekly
note that tries to be a strategic readout is too long and
loses its tracking value. The exec readout that tries to
be a weekly note is too tactical and loses its strategic
value.

---

## 2. The weekly status note (refresher from Lesson 13)

The weekly status note is the EM's most-frequent upward
communication. The senior move is to **write it so the
skip can forward it to their skip with no edits**.

The structure (from Lesson 13):

```
WEEKLY NOTE — [Team] — [Date range]

HEADLINE:
[One sentence on the most important thing that happened
this week.]

PROGRESS (3-5 bullets):
- [Specific shipped work, with engineer credited]
- [...]

BLOCKERS (1-3 bullets):
- [Blocker 1: what, who, what we need to unblock]
- [...]

DECISIONS MADE (1-3 bullets):
- [Decision 1: what was decided, by whom, with rationale]
- [...]

HEADCOUNT / HIRING (1-2 bullets):
- [Where we are on open roles]

NEXT WEEK (3-5 bullets):
- [The most important things for next week]
```

The senior move is to **write the headline so it can
stand alone**. The skip who reads only the headline should
know what they need to know.

---

## 3. The monthly exec readout

The monthly exec readout is the strategic document. It's
the document that gets read at the leadership level, the
document that informs the org strategy, and the document
the EM is most judged on.

The structure:

```
MONTHLY EXEC READOUT — [Team] — [Month]

EXECUTIVE SUMMARY (3-5 sentences):
[What we shipped, what's at risk, what we need from
leadership. This is the section the CTO reads.]

KEY WINS (3-5):
- [Win 1: specific, with impact, with numbers]
- [...]

KEY RISKS (2-3):
- [Risk 1: specific, with impact, with the mitigation
  in progress]
- [...]

KEY DECISIONS NEEDED (1-3):
- [Decision 1: what we need from leadership, by when,
  with the options]
- [...]

HEADCOUNT (1-2 sentences):
[Where we are vs. plan, any specific asks]

UPCOMING (3-5 bullets):
[The most important things for next month]
```

The senior move is the **"decisions needed"** section.
Most exec readouts don't have a decisions-needed section
because the EM doesn't want to ask for things. The
senior move is to ask explicitly — the leadership
who isn't asked isn't allocating.

The mistake: writing the exec readout as a victory lap.
The leadership who only hears wins is the leadership
who's surprised by the next quarter's miss. The senior
move is to be honest about the risks in the same
document that has the wins.

---

## 4. The ad-hoc escalation

The ad-hoc escalation is the most important format to
get right, because it's the format that gets used when
something is on fire. The senior move is to **have a
template for the escalation so the format is consistent
under stress**.

The structure:

```
ESCALATION — [Topic] — [Date]

THE SITUATION (3-5 sentences):
[What's happening, how long it's been happening, the
impact.]

WHAT WE'VE TRIED (3-5 bullets):
- [What we did, what happened]
- [...]

WHAT WE NEED (1-2 sentences):
[The specific decision or unblock we need, by when.]

THE OPTIONS (1-3 bullets):
- [Option 1: what it would take, what it would cost]
- [Option 2]
- [Option 3]

THE RECOMMENDATION (1-2 sentences):
[Which option we recommend and why.]
```

The senior move is to **bring options, not just the
problem**. The EM who escalates with "we have a problem
and we need help" gets a generic response. The EM who
escalates with "we have a problem, here are 3 options,
here's my recommendation" gets a specific decision.

The mistake: escalating too late. The escalation that
comes after the deadline has already missed is the
escalation that damages trust. The senior move is to
escalate **as soon as you know you need the
escalation**, not after you've exhausted your own
options.

---

## 5. The 3 things leadership wants to see

Most leadership has 3 things on their mind at any time.
The senior move is to **frame your upward communication
around those 3 things**, so the leadership sees the
relevance immediately.

1. **Are we on track?** The weekly status note answers
   this. The headline sentence is the answer.
2. **What are the risks I should worry about?** The
   exec readout's "key risks" section answers this.
3. **What do you need from me?** The "decisions needed"
   section of the exec readout, or the ad-hoc
   escalation, answers this.

The mistake: writing the upward communication for the
EM's perspective, not the leadership's. The senior
move is to **start every doc with the answer to the
leadership's question**, not with the context.

---

## 6. A worked example: the ad-hoc escalation for the
Kafka cluster delay

The Kafka cluster from infra is now 8 days late. The
migration's full cutover is at risk. Sam is escalating
to the director.

> **ESCALATION — Kafka cluster delay puts Q3 migration
> at risk — 2026-08-22**
>
> **THE SITUATION:** The new Kafka cluster needed for
> the streaming migration is 8 days late against the
> original Aug 15 commitment. Without the cluster, the
> migration's full cutover (currently scheduled for
> Sep 15) slips by 2-4 weeks. The top customer renewal
> ($4.2M ARR) is at material risk if the cutover slips
> past Oct 1.
>
> **WHAT WE'VE TRIED:**
> - Worked with the infra EM to scope a 1-engineer
>   path; they committed to Aug 20 (5 days late vs.
>   original).
> - Identified the SAML rollout as the competing
>   priority; agreed the SAML rollout takes precedence.
> - Assessed whether we can run shadow mode for 2 extra
>   weeks to absorb a 1-week cluster delay.
>
> **WHAT WE NEED:** A decision by EOD Friday on whether
> to (a) accept the 2-4 week cutover slip, (b) re-
> prioritize the SAML rollout to free up a 2nd
> infra engineer, or (c) escalate to the CTO for
> additional infra capacity.
>
> **THE OPTIONS:**
> - **Option A (accept slip):** Cutover slips to Oct 6.
>   Customer renewal at risk. Cost: 0 additional
>   engineering effort. Risk: customer churns.
> - **Option B (re-prioritize SAML):** Pulls 1 infra
>   engineer from SAML for 2 weeks. SAML slips by 2
>   weeks. Cost: SAML roadmap impact. Risk: SAML team
>   misses their Oct 15 commitment.
> - **Option C (escalate to CTO):** Asks for a
>   contractor or borrowed engineer. Cost: high
>   political cost. Risk: 0; pure upside if approved.
>
> **THE RECOMMENDATION:** Option B. The SAML slip is
> recoverable; the customer renewal is not. I'd take
> the conversation with the SAML EM if you approve.

**What makes this land:** The situation is specific, with
the impact in numbers ($4.2M ARR). What-we've-tried
shows the EM exhausted their own options. What-we-need
is specific (decision by EOD Friday). The options have
tradeoffs and recommendations. The recommendation is
defended with reasoning.

---

## 7. Canonical questions this lesson answers

From `docs/reference/em_interview_canonical_questions.md`:

- Behavioral #1: *"Tell me about a time when you handled
  a difficult stakeholder."*
- Behavioral #39: *"Tell me about a time when you had to
  push back on a decision."*
- Behavioral #84: *"Tell me about a time when you had to
  build a relationship with a stakeholder."*
- Behavioral #112: *"Tell me about a time when you had to
  influence a decision that you disagreed with."*

---

## Try it

If you have a real escalation coming up, write it using
the template above. Notice how the template forces you
to bring options, not just the problem. The discipline
of the template is the senior move that gets the
decision you need.

If you don't have a real escalation, write a 90-second
answer for "Tell me about a time you had to escalate
something to leadership" using a real example from
any context — a work situation, a community
situation, a personal situation. The skill is the
same: bring options, make a recommendation, name the
tradeoffs.

---

## Action item

This week, review your last 3 weekly notes. Do they all
follow the same structure? Do they all have a
forwardable headline? If not, the next 3 weekly notes
are an opportunity to standardize the format. The
senior move is to **make the format predictable** so
the leadership can read the note in 30 seconds.