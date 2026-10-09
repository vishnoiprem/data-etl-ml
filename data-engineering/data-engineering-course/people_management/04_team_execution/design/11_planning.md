# 11 — Project Planning and Sprint Execution

> **Lesson 11 of 21 — Managing Team Execution** · ~20 min

Sprint planning, capacity planning, dependency mapping, and how
to scope a quarter. Planning is where the EM's job shifts from
"managing people" to "running a team." Most senior ICs have
never done this work as a primary responsibility.

---

## 1. The 3 planning horizons

EMs plan at 3 horizons. Each has a different cadence, a
different artifact, and a different audience.

| Horizon | Cadence | Artifact | Audience |
|---|---|---|---|
| **Quarter** | Every 3 months | Roadmap doc, OKRs (Lesson 05) | Skip-level, peer EMs, PM partner, your team |
| **Sprint** (or month) | Every 2-4 weeks | Sprint plan, capacity sheet | Your team, your PM partner |
| **Week** | Every Monday | Status doc, dependencies list | Your team, your skip-level |

The mistake new EMs make: spending all their time on the weekly
status and not enough on the quarterly roadmap. The roadmap is
where you set direction; the weekly status is where you track
it. If the roadmap is fuzzy, the weekly status is just
tactically executing on something you haven't decided.

The other mistake: planning the quarter once and never
revisiting. The senior move is to **revisit the quarterly plan
every 4-6 weeks** and adjust based on what's actually happened.
The market shifted, the customer churned, the project slipped
— the plan should adjust.

---

## 2. The quarterly roadmap doc

A 1-2 page doc that names the 3-5 most important things the
team will ship in the next quarter. The structure:

```
QUARTERLY ROADMAP — [Team] — [Quarter]

THEMES (1-2):
[One-line description of the strategic themes. E.g., "Reliability
and scale" or "Migration to the streaming platform."]

TOP 3-5 COMMITMENTS:
- [Commitment 1] — [Owner] — [Definition of done] — [Target date]
- [Commitment 2] — [Owner] — [Definition of done] — [Target date]
- [Commitment 3] — [Owner] — [Definition of done] — [Target date]
- [Commitment 4] — [Owner] — [Definition of done] — [Target date]
- [Commitment 5] — [Owner] — [Definition of done] — [Target date]

NON-GOALS:
- [Specific thing we are explicitly NOT doing this quarter]
- [Specific thing we are explicitly NOT doing this quarter]
- [Specific thing we are explicitly NOT doing this quarter]

DEPENDENCIES:
- [Upstream team / vendor] — [What we need from them, by when]
- [Upstream team / vendor] — [What we need from them, by when]

RISKS:
- [Risk 1] — [Mitigation]
- [Risk 2] — [Mitigation]
```

The "non-goals" section is the most-skipped and the most
useful. Naming what you're not doing pre-empts the conversations
where a stakeholder asks for something that's not on the plan.
The senior move: the non-goals are public, shared with the PM
partner, and the EM holds the line on them.

The "dependencies" section is the second most-skipped. Most
EMs treat dependencies as something to discover mid-sprint
instead of something to plan around. The senior move is to
name the dependencies at the start of the quarter, with a
specific ask and a specific date.

---

## 3. Capacity planning

The senior move is to **plan against capacity, not against
aspiration**. Most teams plan for 100% utilization and end up
over-committed and burned out. The realistic capacity is:

- **70-80%** for engineers doing project work
- **20-30%** for ops, on-call, meetings, interviews, and
  unplanned work

If your team is 5 engineers at 70% utilization, that's 3.5
FTE-months of project work per month. The senior move is to
plan against 3.5, not 5, and to keep the 1.5 FTE-month buffer
for the unplanned work that will definitely come.

The mistake: planning for 5, hitting 4, and being surprised
by the 1 you missed. The senior move is to plan for 3.5, hit
4, and have a 0.5 FTE-month buffer to handle the unplanned.

The exception: a hard deadline (a customer commitment, a
reorg, a launch) where over-commitment is the right call.
Even then, name it explicitly: "we're committing to 5 FTE
this month, which means 2 of you will be on critical projects
and the rest of the queue slips. We re-baseline next month."

---

## 4. Sprint planning

The sprint is 2-4 weeks (varies by team). The sprint plan
answers 3 questions:

1. **What are we committing to ship by end of sprint?**
2. **Who owns each commitment?**
3. **What's the risk if we slip?**

A useful sprint plan format:

```
SPRINT [N] — [Date range] — [Theme: e.g., "Migration v1"]

COMMITMENTS (with owners):
- [Engineer] — [Commitment 1] — [Definition of done]
- [Engineer] — [Commitment 2] — [Definition of done]
- [Engineer] — [Commitment 3] — [Definition of done]

STRETCH (if we have capacity):
- [Stretch commitment 1]
- [Stretch commitment 2]

DEPENDENCIES (we're waiting on):
- [Upstream team] — [What we need, by when, what we do if
  it slips]

AT RISK:
- [Commitment that's likely to slip, with the mitigation]
```

The "stretch" section is the senior move. Naming the
stretch commitments explicitly means (a) the team has
something to aim for if the main commitments ship early, and
(b) the stretch doesn't get treated as a real commitment
if it slips.

The "at risk" section is the senior move for surfacing
problems early. If a commitment is at risk on day 3 of a
10-day sprint, the EM has 7 days to mitigate. If the
"at risk" is named on day 8, the EM has 2 days and the
options are bad.

---

## 5. A worked example: the Q3 roadmap for the data platform
team

> **QUARTERLY ROADMAP — Data Platform Team — Q3 2026**
>
> **THEME:** Reliability and scale
>
> **TOP 4 COMMITMENTS:**
> 1. **Streaming migration v1** — Priya — 0 P0 bugs in
>    production for 30 days post-launch, full test coverage,
>    on-call runbook signed off — target Sep 15
> 2. **On-call rotation redesign** — Aarav — new rotation
>    live, no engineer carrying more than 1 in 4 weekends,
>    "no on-call after Sev1" rule — target Aug 1
> 3. **Customer data quality dashboard** — Jordan —
>    dashboard live for top 5 customers, with error rate
>    SLO — target Sep 30
> 4. **Q4 platform planning** — Sam (EM) — 1-page doc
>    naming 3 strategic themes for Q4, signed off by
>    director — target Sep 25
>
> **NON-GOALS:**
> - New ML features (deferred to Q4)
> - Migration of the analytics pipeline (deferred to Q4)
> - New dashboards for the finance team (deferred to Q4)
>
> **DEPENDENCIES:**
> - **Data Science team** — schema signoff on the migration
>    by Aug 1; if slips, migration slips to Sep 30
> - **Infra team** — new Kafka cluster provisioned by
>    Aug 15; if slips, we run shadow mode for 2 extra
>    weeks
>
> **RISKS:**
> - Priya is also mentoring Jordan; if Jordan's commits
>    slip, Priya's commits slip — mitigation: pull a
>    senior from the sister team to mentor Jordan for
>    August
> - Q4 platform planning depends on the director's
>    strategic priorities, which are still TBD —
>    mitigation: Sam to confirm priorities by Aug 15

**What makes this land:** Each commitment has an owner, a
definition of done, and a target date. The non-goals are
explicit. The dependencies are named with specific dates and
mitigations. The risks are surfaced with mitigations. The EM
owns one of the 4 commitments personally — that's the senior
move, not pretending the EM is "above" the project work.

---

## 6. Canonical questions this lesson answers

From `docs/reference/em_interview_canonical_questions.md`:

- Behavioral #22: *"Tell me about a time when you had to
  set goals for your team."*
- Behavioral #46: *"Tell me about a time when you had to
  re-prioritize."*
- Behavioral #81: *"Tell me about a time when you had to
  manage changing priorities."*
- Behavioral #100: *"Tell me about a time you delivered a
  complex project."*

---

## Try it

Write a 1-page quarterly roadmap for your team, even if
you're not at the start of a quarter. Use the format above.
Notice which commitments have vague definitions of done
("improve reliability") and which have specific ones ("0 P0
bugs in production for 30 days"). The vague ones are where
sprints slip.

If you're an IC interviewing for an EM role, write a 1-page
plan for a current project. Same format. The skill is the
same; the scope is smaller.

---

## Action item

This week, write the "non-goals" section for your current
quarter. Even if you've already planned the quarter, naming
the non-goals explicitly is the highest-leverage move you can
make to protect the team's focus.