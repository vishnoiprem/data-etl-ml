# 14 — Managing Cross-Team Dependencies

> **Lesson 14 of 21 — Managing Team Execution** · ~20 min

RACI, project tracking, escalation paths, and the dependency-
mapping exercise. Dependencies are where most projects slip —
not because the work is hard, but because the team is waiting
on someone else. The senior move is to surface dependencies
early, name the escalation path, and unblock them before they
become the project's bottleneck.

---

## 1. The 3 types of dependency

Every dependency falls into one of 3 categories, and each
needs a different unblocking strategy.

| Type | What it looks like | Unblocking strategy |
|---|---|---|
| **Information dependency** | "I need to know X before I can do Y." | Direct ask, async doc, scheduled sync. Fastest to unblock. |
| **Work dependency** | "I need [other team] to ship [thing] before I can ship [my thing]." | Negotiation, escalation, scope reduction. Medium to unblock. |
| **Decision dependency** | "I need [leader] to decide between A and B before I can proceed." | Pre-work, escalation, deadline calendar. Slowest to unblock. |

The mistake new EMs make: treating all 3 the same way
(messaging the other team and hoping). The senior move is to
diagnose the type first, then apply the right strategy.

---

## 2. The dependency-mapping exercise

The dependency-mapping exercise is a 1-2 hour meeting the
EM runs with the team at the start of every project (or
quarter). The goal is to surface every dependency, name its
type, and assign an unblocking strategy.

The format:

```
DEPENDENCY MAP — [Project] — [Date]

UPSTREAM DEPENDENCIES (we're waiting on others):

| Dependency | Type | Owner on their side | Our owner | Unblock strategy | Due date | Status |
|---|---|---|---|---|---|---|
| [Need 1] | Info/Work/Decision | [Name] | [Name] | [Strategy] | [Date] | [Status] |
| [Need 2] | ... | ... | ... | ... | ... | ... |

DOWNSTREAM DEPENDENCIES (others are waiting on us):

| Dependency | Type | Their owner | Our owner | What we ship | Due date | Status |
|---|---|---|---|---|---|---|
| [Need 1] | ... | [Name] | [Name] | [What] | [Date] | [Status] |
| [Need 2] | ... | ... | ... | ... | ... | ... |

ESCALATION PATHS:
- If [owner] is unresponsive, escalate to [their manager]
  on [date]
- If the decision is stalled, escalate to [decision-maker]
  by [date]

RISKS:
- [Risk 1: dependency X slips past Y, mitigation Z]
```

The senior move is to **review this map weekly** and to
update the status field every Friday. The map that lives
in a doc and never gets opened is worse than no map at all
— it gives false confidence.

---

## 3. RACI

RACI is a 4-letter framework for clarifying roles on a
project. It sounds corporate, but the underlying move is
what matters: **name who's Responsible, who's Accountable,
who's Consulted, and who's Informed, for each major piece
of the project**.

| Letter | What it means | Example |
|---|---|---|
| **R**esponsible | The person doing the work | Priya is Responsible for the schema migration code |
| **A**ccountable | The person who owns the outcome | Sam (EM) is Accountable for the migration shipping on time |
| **C**onsulted | The people whose input is needed before decisions | Data science team is Consulted on the schema design |
| **I**nformed | The people who need to know what's happening | Director is Informed on the migration's weekly status |

The mistake new EMs make: assigning everyone as "R" or
skipping the exercise because "we all know who does what."
The senior move is to write the RACI down, share it with
the team, and revisit when the project changes.

The senior move with Accountable: **there should be exactly
one Accountable person for each piece of the project**.
Multiple Accountable means no one is Accountable. Zero
Accountable means the EM is implicitly Accountable for
everything.

---

## 4. Escalation paths

Escalation paths are how dependencies get unblocked when the
normal channels fail. The senior move is to **name the
escalation path before you need it**.

The pattern:

1. **First attempt:** the direct owner asks directly. Slack
   DM, email, scheduled sync.
2. **Second attempt:** the EM reaches out to the peer EM.
   "Hey [peer], I need [X] from your team by [date]. Can
   you make sure it happens?"
3. **Third attempt:** escalate to both managers. "We need
   [X] from [team], [peer] isn't unblocking, can you help?"
4. **Fourth attempt:** escalate to the org leader. "We've
   tried [the 3 attempts], we need [X] or [Y consequence]."

The mistake: skipping from attempt 1 to attempt 4. The
peer EM will resent you for going over their head, and the
org leader will ask "why didn't you work this out?"

The senior move: **always start at the lowest level of
escalation**. Most dependencies unblock at attempt 1 or 2.
Save attempt 3 and 4 for the genuinely stuck.

---

## 5. The unblocking 1:1

Sometimes the dependency isn't a process issue — it's a
relationship issue. The other EM is unresponsive, or the
other team has deprioritized your work, or the peer EM
doesn't have the context to know your work is urgent.

The senior move is to schedule an **unblocking 1:1** — a
30-minute meeting with the peer EM specifically to align on
the work. The unblocking 1:1 is different from a regular
sync: it's structured to produce a decision, not a status
update.

The script:

> *"I want to schedule 30 minutes specifically to unblock
> [X]. Here's what I need from your team: [specific ask].
> Here's my understanding of your team's priorities: [what
> I think is taking precedence]. Here's what I propose: [a
> specific path]. If we can't agree in this meeting, I'll
> escalate to [manager] — I want to flag that now so we're
> not surprised."*

The senior move: **flag the escalation in advance**. The
peer EM will either agree to the path or escalate
themselves, but they won't be surprised. The "surprise"
escalation is the move that damages cross-team
relationships.

---

## 6. A worked example: unblocking the Kafka cluster

The new Kafka cluster from infra is 4 days late. Sam is
running the unblocking 1:1 with the infra EM.

> **Sam:** "I want to schedule 30 minutes specifically to
> unblock the Kafka cluster for our streaming migration.
> Here's what I need: the cluster provisioned by Aug 15.
> Here's my understanding of your priorities: the SAML
> rollout is consuming most of your team's capacity this
> month. Here's what I propose: you keep 1 engineer on the
> Kafka provisioning (instead of the 2 I'd been assuming),
> we extend the timeline by 1 week to Aug 22, and you give
> me a specific date by end of this meeting. If we can't
> agree, I'll need to escalate to [director] — I want to
> flag that now."
>
> **Infra EM:** "Let me check with my lead... Actually,
> we can have 1 engineer on it, and I can commit to
> Aug 20. The SAML rollout is still my top priority, so
> I can't move faster."
>
> **Sam:** "Aug 20 works. Let me update my roadmap and
> my skip. I'll send you a confirmation by end of day."

**What makes this land:** The unblocking 1:1 has a specific
ask, a specific proposal, and a flagged escalation path.
The infra EM has cover for the SAML tradeoff. The
outcome is a specific date by end of meeting, not a "let me
circle back." The senior move is the explicit
pre-escalation — Sam named the next step before the peer
EM had to guess.

---

## 7. Canonical questions this lesson answers

From `docs/reference/em_interview_canonical_questions.md`:

- Behavioral #3: *"Tell me about a time you had to
  influence a peer team."*
- Behavioral #34: *"Tell me about a time when you had to
  work with a team that had different priorities."*
- Behavioral #78: *"Tell me about a time when you had to
  coordinate multiple teams."*
- Behavioral #122: *"Tell me about a time when you had to
  resolve a conflict between teams."*

---

## Try it

Run the dependency-mapping exercise for your current project.
Use the format above. If you can't fill it in completely,
the gaps are your highest-leverage unblocking priorities
for the week.

If you're an IC interviewing for an EM role, the equivalent
exercise: write a dependency map for a current project
you've been working on. The skill is the same.

---

## Action item

This week, identify the 1 dependency that's most likely to
slip your current sprint. Use the 3-attempt escalation
pattern to unblock it. Start at attempt 1 (the direct
owner), but name attempts 2 and 3 before you need them.