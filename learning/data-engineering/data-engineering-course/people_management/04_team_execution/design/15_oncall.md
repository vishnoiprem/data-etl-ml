# 15 — On-Call, Incidents, and Operational Excellence

> **Lesson 15 of 21 — Managing Team Execution** · ~20 min

Rotation design, postmortem process, action items, and the EM's
role during an incident. The on-call rotation is the EM's
operational muscle — it's where the team either functions well
under pressure or burns out. Most senior ICs have been on
rotations, but the EM's role is different: the EM designs the
rotation, runs the incidents, and writes the postmortems.

---

## 1. The on-call rotation

A well-designed on-call rotation has 4 properties:

| Property | What it means |
|---|---|
| **Equal distribution** | No engineer carries more than their share. Most teams target 1-in-N weekends (where N is the rotation size), with no one carrying 2 in a row. |
| **Bounded hours** | No one is on call 24/7. A common pattern: weekday primary, weekday secondary, weekend primary, weekend secondary, with explicit handoff times. |
| **Compensated** | On-call pay (a flat fee + per-incident fee) is the norm. The exact amount varies, but on-call should never be "free." |
| **Recoverable** | Hard rule: no on-call the week after a Sev1. The engineer who handled a 4-hour Sev1 on Sunday shouldn't be on call the following weekend. |

The mistake new EMs make: designing a rotation that's
"balanced on paper" but uneven in practice (one engineer
keeps ending up on the worst weekends because of personal
schedule patterns). The senior move is to **audit the
rotation every quarter** and adjust for actual distribution,
not just nominal.

The other mistake: making on-call a chore. The senior move
is to **celebrate on-call work** — shout-outs in staff
meetings, public thank-yous, comp adjustments for the
engineers who carry the most. On-call is high-stress, low-
visibility work, and the EM's job is to make it visible.

---

## 2. The incident — the EM's role

During an incident, the EM is **the commander**, not the
fixer. The EM coordinates the response; the engineers do
the technical work. The 3 things the EM owns during an
incident:

1. **The incident channel.** The EM opens a Slack channel
   (or the equivalent), sets the topic with the incident
   summary, and triages who's in the channel.
2. **The role assignments.** The EM assigns the Incident
   Commander (IC), the Comms Lead, and the Subject Matter
   Experts (SMEs). The IC runs the technical response. The
   Comms Lead updates stakeholders. The SMEs do the work.
3. **The escalation.** The EM decides when to escalate
   (Sev1, customer-facing, all-hands) and to whom (the
   skip-level, the on-call director, the CEO).

The mistake new EMs make: **doing the technical work**. The
EM who jumps into the code during a Sev1 has left the
coordination role unfilled, and the response gets chaotic.
The senior move is to **stay out of the code unless the
incident requires the EM's specific context** (e.g., the
incident is about a system only the EM has historical
context on).

The other mistake: the EM is silent during the incident.
The senior move is to **post regular updates** — every
15-30 minutes, even if the update is "no change, still
investigating." The silence is what makes stakeholders
panic.

---

## 3. The postmortem

The postmortem is a 1-2 page doc written within 1-2 weeks
of the incident. The senior move is to **write the
postmortem as a blameless document** — the postmortem is
about the system, not the people.

The structure:

```
POSTMORTEM — [Incident title] — [Date] — [Severity]

SUMMARY:
[2-3 sentences on what happened, how long it lasted, and
the customer impact.]

TIMELINE:
- [Time] — [Event]
- [Time] — [Event]
- [Time] — [Event]
- [Time] — [Event]
- [Time] — [Resolution]

ROOT CAUSE:
[1-2 sentences on the actual root cause. Not "human error" —
the system that allowed the human error to cause an incident.]

CONTRIBUTING FACTORS:
- [Factor 1]
- [Factor 2]
- [Factor 3]

WHAT WENT WELL:
- [Thing 1 — celebrate this]
- [Thing 2]

WHAT WENT WRONG:
- [Thing 1]
- [Thing 2]

ACTION ITEMS (with owners and dates):
- [Action 1] — [Owner] — [Due date]
- [Action 2] — [Owner] — [Due date]
- [Action 3] — [Owner] — [Due date]

LESSONS LEARNED:
[1-2 sentences on the transferable lesson. This is the
section that gets shared beyond the team.]
```

The "action items" section is the load-bearing part. Most
postmortems have action items that never get done, and the
same incident pattern recurs 6 months later. The senior
move is to **track action items in the team's sprint
plan** with explicit owners and due dates, and to report
on them in the weekly note until they're done.

---

## 4. The "Sev1 a month" pattern

The most diagnostic signal of operational health is the
"Sev1 a month" pattern: a team that has roughly one Sev1
per month is operating at a healthy tempo. A team that
has one Sev1 per quarter is either very mature or
under-reporting. A team that has one Sev1 per week is in
crisis.

The senior move is to **track Sev1 frequency publicly** —
in the weekly note, in the staff meeting, in the all-
hands. The data is what drives the prioritization. A
team that hides its Sev1 count from leadership is a
team that will keep having the same incident.

---

## 5. A worked example: the Sev1 postmortem for the
schema migration

> **POSTMORTEM — Schema migration dropped 8% of events
> silently — 2026-08-22 — Sev1**
>
> **SUMMARY:** A schema version mismatch in the Flink
> deserializer caused 8% of events to be silently dropped
> for 4 days, affecting the customer-facing analytics
> dashboard. Detected by the data science team noticing
> missing data. Fixed within 30 minutes of detection.
> Customer impact: 4 days of incomplete analytics for
> the top 5 customers.
>
> **TIMELINE:**
> - 2026-08-18 (10:00) — Schema version 3.2 deployed
>   to the producer.
> - 2026-08-18 (10:05) — Flink job started silently
>   dropping events with the new schema version.
> - 2026-08-22 (14:30) — Data science team noticed
>   missing data in the dashboard; paged on-call.
> - 2026-08-22 (14:35) — Aarav (on-call) joined the
>   incident channel.
> - 2026-08-22 (15:00) — Root cause identified:
>   deserializer didn't have the new schema version.
> - 2026-08-22 (15:30) — Fix deployed; events recovered.
>
> **ROOT CAUSE:** The deserializer in the Flink job was
> not updated when the new schema version was deployed
> to the producer. The deserialization failure was
> silent — events were dropped without any error log.
>
> **CONTRIBUTING FACTORS:**
> 1. No schema-version compatibility check in CI for
>    services that do deserialization.
> 2. The "silent drop" behavior was the default in the
>    deserialization library we use.
> 3. The dashboard's data quality SLO was set to 95%,
>    which the 92% delivery was within tolerance for.
>
> **WHAT WENT WELL:**
> - Aarav (on-call) identified the root cause in 30
>   minutes.
> - The data science team escalated promptly when they
>   noticed the missing data.
> - The fix was a 1-line config change.
>
> **WHAT WENT WRONG:**
> - 4 days passed before the issue was detected.
> - The dashboard's data quality SLO was too loose to
>   catch the issue.
>
> **ACTION ITEMS:**
> - Add schema-version compatibility check to CI —
>   Priya — 2026-09-15
> - Change deserializer to log on schema-version
>   mismatch — Aarav — 2026-09-01
> - Tighten dashboard SLO from 95% to 99% — Jordan —
>   2026-09-30
>
> **LESSONS LEARNED:** Any time you have multiple
> producers/consumers with independent schema evolution,
> silent deserialization failures are the highest-
> probability failure mode. A schema-version compatibility
> check in CI is now a hard requirement for any service
> that does deserialization.

**What makes this land:** The root cause is about the
system, not the people ("the deserializer wasn't
updated"), not ("Priya forgot to update the deserializer").
The action items have owners and dates. The "lessons
learned" is transferable beyond the team.

---

## 6. Canonical questions this lesson answers

From `docs/reference/em_interview_canonical_questions.md`:

- People Management #9: *"Tell me about a time you had to
  lead during a crisis."*
- Behavioral #16: *"Tell me about a time you had to make a
  decision under time pressure."*
- Behavioral #44: *"Tell me about a time you led a team
  through a difficult situation."*
- Behavioral #76: *"Tell me about a time when you had to
  make an unpopular decision."*

---

## Try it

If you've been through a real incident, write the
postmortem in the format above. Even if you don't share
it with the team, the exercise of writing it forces you
to identify the systemic cause and the action items.

If you haven't been through a real incident as an EM,
write a 90-second answer for "Tell me about a time you
had to lead during a crisis" using a non-engineering
example (a personal crisis, a customer situation, a
community incident). The EM's role is the same:
coordinate, don't fix.

---

## Action item

This week, audit your on-call rotation. Check the actual
distribution (who's carried how many weekends in the last
quarter) against the nominal distribution. If there's a
gap, redesign the rotation to fix it. If there's no
gap, the audit is the senior move that prevents the
gap from forming.