# 03 — Mock Interview: Staff Engineer (E6) at Google

> **Lesson 3 of 5 — Practice** · ~20 min

A full mock at the Google L6 bar (Staff Software Engineer).
Sam is now 8 years experienced and interviewing for a Staff
Data Engineer role on the Core Data Platform team.

The L6 bar is materially different from the L5 bar. The
interviewer is looking for **technical strategy across
multiple teams**, **org-level influence**, and **judgment
under novel situations**. Stories that were 4/4 at E5 will
be 2/4 at E6 if they're framed at the team level.

---

## 1. The setup

- **Candidate:** Sam, 8 years experience, currently Senior
  Data Engineer at a mid-size SaaS.
- **Interviewer:** Alex, Staff Software Engineer on the Core
  Data Platform team at Google, 7 years at the company.
- **Round:** 50 minutes, 6 questions, behavioral only.
- **Bar:** L6 (Staff). The interviewer will be looking for
  *cross-team* and *strategy* signals.

---

## 2. The transcript

### Q1: "Tell me about yourself."

> *"I'm a data engineer with 8 years of experience, currently
> at [SaaS Co] where I lead a 6-person data platform team. The
> work I'm proudest of is the cross-org platform initiative
> I drove last year — we replaced our per-team batch pipelines
> with a shared streaming platform, which 4 teams now use as
> their default. It cut our aggregate infrastructure cost by
> about $400k/year and reduced the time-to-first-pipeline for
> new teams from 6 weeks to 4 days.*
>
> *Three things I'd want you to know about me. First, I think
> a lot about the boundary between team-level and org-level
> work — I deliberately take on projects that have org-level
> leverage, not just team-level wins. Second, I've gotten
> good at writing technical strategy docs that survive the
> transition from idea to execution — my last strategy doc
> was referenced by 3 different teams in their planning the
> following year. Third, I care a lot about reducing the
> cognitive load of the teams that consume my work — I'd
> rather they have a simple API than a powerful one.*
>
> *I'm talking to Google because the Core Data Platform team
> is solving exactly the org-level data infrastructure
> problems I've been working on at smaller scale, and the
> published work on Borg and Spanner is the kind of strategic
> thinking I want to be part of."*

**Analysis:** 70 seconds — a touch over 60, but appropriate
for L6. The signature work is *org-level* (4 teams, $400k),
not team-level. The 3 signals are *senior-engineer* signals
(org leverage, strategy docs, cognitive load). The "why here"
references their public technical work. 4/4.

### Q2: "Tell me about a time you had to make a technical
decision that affected multiple teams."

> *"Last year we had a problem where each of our 4 product
> teams had built their own batch ETL pipeline. The pipelines
> were slightly different — different schedulers, different
> schemas, different reliability characteristics. The org
> was spending about $1.2M/year on duplicate infrastructure
> and new teams took 6+ weeks to onboard a new pipeline.*
>
> *I proposed building a shared streaming platform that all
> 4 teams would use. The hard decision was the API surface:
> I could build either a low-level primitive (more flexible,
> but each team had to do more work) or a high-level
> opinionated framework (less flexible, but faster
> adoption).*
>
> *I chose the opinionated framework. The reasoning: the
> common case (a team wanting to ingest a Kafka topic into
> BigQuery) was 80% of all use cases, and the low-level
> primitive would have forced each team to reinvent the
> same logic. I built a thin escape hatch for the 20% case
> that needed flexibility, but the default was opinionated.*
>
> *It was a controversial choice. The 2 teams that had
> invested heavily in their custom pipelines pushed back
> — they didn't want to throw away their work. I worked
> with each of them individually to map their existing
> pipelines onto the new framework. One team migrated in
> 2 weeks. The other took 2 months because their pipeline
> had features that the framework didn't support, and I
> ended up adding 2 of those features to the framework
> (which benefited 2 other teams too).*
>
> *Outcome: 4 teams adopted the platform within 6 months.
> Aggregate infra cost dropped from $1.2M to $800k.
> Time-to-first-pipeline dropped from 6 weeks to 4 days.
> The 2 added features are now the most-used extensions
> in the framework."*

**Analysis:** L6-caliber story. The decision is named
(opinionated vs. low-level). The reasoning is specific
(80/20 use case distribution). The cost is acknowledged
(2 teams pushed back). The synthesis is described (added
2 features that benefited 2 other teams). Measurable
outcome. 4/4.

### Q3: "Tell me about a time you had to influence someone
more senior than you."

> *"My director wanted to sunset a legacy data warehouse
> that was costing us $300k/year. I disagreed — I thought
> there were 2 use cases still depending on it that didn't
> have a clean migration path. The director had already
> aligned with his VP on the timeline.*
>
> *What I did: I spent a week instrumenting the legacy
> warehouse. I found that 2 of the 14 teams using it
> accounted for 80% of the queries, and that both teams
> had specific technical blockers to migration (one was
> using a SQL feature the new warehouse didn't support;
> the other was on a hard-to-migrate schema). I wrote a
> 2-page memo: the data, the proposed alternative
> (migrate the 12 small teams on schedule, give the 2
> large teams a 6-month extension with a clear
> migration plan), and the cost of the extension
> ($75k/year for 6 months vs. $300k/year forever).*
>
> *The director agreed. The 2 large teams migrated on
> schedule 6 months later. The legacy warehouse was
> decommissioned a quarter ahead of the original plan
> because the smaller teams migrated faster than
> expected once the 2 large teams were out of the
> way."*

**Analysis:** L6-caliber. The influence is *upward* (a
director), the data-gathering is specific (a week of
instrumentation), the proposal has a *named* alternative
(not just disagreement), and the cost is quantified
($75k vs $300k). The outcome is better than the original
plan (decommissioned a quarter early). 4/4.

### Q4: "Tell me about a time you had to navigate significant
ambiguity to deliver results."

> *"I was given a mandate by my VP: 'make our data
> platform self-serve for product teams.' That was the
> brief. The mandate was ambiguous because 'self-serve'
> could mean anything from 'product teams can read from
> our warehouse without a ticket' to 'product teams can
> onboard a new data source without talking to us.' I
> spent 2 weeks doing 14 user interviews with PMs and
> engineers across the 4 product teams. I asked each of
> them: 'what's the thing you wish you could do with
> data that you can't do today, and what's the smallest
> change that would unblock it?'*
>
> *The interviews converged on 3 specific requests
> that 11 of 14 mentioned: (1) a way to query the
> warehouse from their own tools (Tableau, Looker), (2)
> a way to subscribe to a dataset and get notified when
> it changed, (3) a way to add a new data source without
> filing a ticket with the data team. I scoped a 3-quarter
> project around those 3 capabilities, with each as a
> separate deliverable.*
>
> *I shipped all 3 in 9 months. Adoption: 4 of 4 product
> teams adopted (1) and (2) within 2 months of launch.
> (3) was adopted by 3 of 4 teams within 4 months. The
> fourth team (which had a custom legacy stack) adopted
> in month 11. The 'self-serve' mandate, which had been
> a vague goal for 2 years, became a measurable program."*

**Analysis:** L6-caliber. The mandate is named. The
ambiguity-cutting tactic is named (14 interviews, 1
specific question). The synthesis is specific (3
requests, 11 of 14 mentioned). The scoping decision is
named. Measurable adoption. The vague 2-year goal became
a measurable program. 4/4.

### Q5: "Tell me about a time you failed and what you learned."

> *"I overcommitted my team to a 6-month project to
> rebuild our metrics platform. I had estimated 3
> engineer-quarters of work; it took 7. The cause was
> that I had under-estimated the cross-team coordination
> cost — 3 of the 4 product teams needed schema changes
> that I hadn't pre-aligned, and each schema change
> turned into a 2-3 week negotiation cycle.*
>
> *What I changed: I now require a stakeholder-alignment
> sprint (1-2 weeks) before any cross-team project,
> with explicit pre-agreements from each affected team
> on the scope of changes. I also build a 30% buffer
> into any cross-team estimate. We delivered the last
> 3 cross-team projects within 10% of estimate."*

**Analysis:** L6-caliber. The cause is *specific*
(cross-team coordination cost, schema change
negotiations). The change is *specific* (alignment
sprint, 30% buffer). The follow-up is *measurable*
(3 of 3 cross-team projects within 10%). 4/4.

### Q6: "What questions do you have for me?"

> *"Three things. First, where does the Core Data
> Platform team disagree with the rest of Google about
> how data infrastructure should evolve? Second, what's
> the technical decision you're most uncertain about
> right now, and what would change your mind? And third
> — the Spanner paper mentioned a tradeoff between
> consistency and availability in cross-region
> replication. How does that play out in the data
> platform layer?"*

**Analysis:** All three are L6-caliber reverse-interview
questions. The third is exceptional — it references
specific published technical work, signals deep
familiarity, and asks a question that the interviewer
will *want* to engage with. 4/4.

---

## 3. Overall assessment

**6 answers, all 4/4. Net: 24/24.**

This is a **strong hire at the L6 bar**. The candidate:

- Frames every story at the *org* level, not the team
  level
- Demonstrates *upward* influence, not just peer
  influence
- Names specific decisions, accepts specific costs,
  and quantifies specific outcomes
- Asks reverse-interview questions that signal Staff+
  engagement
- Shows the *meta-pattern* of "I take on org-leverage
  work, I write strategy docs, I reduce cognitive load
  for the teams that consume my work"

The Google hiring committee would put this in the
"strong L6, possibly L7" bucket. The candidate would
get an offer at the L6 band, with possible upside.

---

## 4. The L5-to-L6 shift

Compare this transcript to the L5 transcript in
Lesson 02. The candidate is the same person (Sam),
with 2 more years of experience. The stories are
similar in structure (STAR / SOAR / PAR), but the
*framing* is different:

| L5 framing | L6 framing |
|---|---|
| "I led the migration on my team" | "I drove the cross-org platform initiative" |
| "I influenced the data science team" | "I influenced my director with a data-grounded memo" |
| "We cut infra cost by $180k" | "We cut aggregate org cost by $400k, touching 4 teams" |
| "I learned to align stakeholders" | "I now require a stakeholder-alignment sprint on every cross-team project" |
| "I'd want to know about the team's work" | "Where does the team disagree with the rest of Google?" |

The shift is from *team-level wins* to *org-level
leverage*. The shift is from *learning specific
tactics* to *creating patterns that propagate*. The
shift is from *I built X* to *I changed how X is
done*.

If you're interviewing for L6, every story in your
bank needs to be re-examined through this lens. A
team-level story can become an L6 story if you
reframe it around the org-level impact — but the
reframe has to be honest, not inflated. See
`02_theory/05_calibration.md` for the calibration
trap.

---

## Try it

Take your 3 strongest stories. Re-frame each one
to demonstrate *org-level leverage* instead of
*team-level wins*. Don't inflate — reframe. If
the org-level impact isn't there, the story isn't
L6 material. Find a different story.
