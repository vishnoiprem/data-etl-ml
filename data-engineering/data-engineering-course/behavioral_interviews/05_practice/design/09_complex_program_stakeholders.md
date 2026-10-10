# Lesson 09 — "Tell me about a relevant complex program you've managed. How did you handle stakeholder & team management, and escalating issues while prioritizing work?"

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Companion:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)
>
> **Pattern:** Program ≠ project. 7 stakeholders, 3 streams, 1 slipped deadline is the minimum viable complexity.

---

## Why this lesson

This question probes for **scope expansion** — the ability to manage
*across* teams, not just *within* one. Candidates at L5+ (Meta IC5,
Google L5) are expected to have at least one program in the last 2
years where they coordinated 3+ work streams and 5+ stakeholders
without direct authority over all of them.

What most candidates miss:

- A **project** has one team, one stakeholder, one decision-maker.
- A **program** has multiple teams, **competing priorities**, **shared
  dependencies**, and a **decision-maker who is rarely in the room**.
- The interview is asking whether you can name the *coordination
  machinery* you used, not just the work you did.

## The framework — 5 components

| # | Component | Example sentence |
|---|---|---|
| 1 | **Stakeholder map** | "I had 7 stakeholders across product, data science, infra, finance, legal, and two external vendors." |
| 2 | **Decision matrix** | "Finance owned the budget call. Product owned the launch-call. I owned the technical sequencing call. We disagreed on 3 things; I escalated 1." |
| 3 | **Failure story** | "The infra team's milestone slipped by 2 weeks. I had to make a tradeoff: hold the launch or drop scope." |
| 4 | **Escalation** | "I escalated to the VP only twice. Both were scope-versus-deadline calls I couldn't resolve at director level." |
| 5 | **Outcome** | "Launched 3 weeks late with 4 of 6 scope items. The 2 dropped items were deferred, not abandoned." |

## Worked example — ride-share data foundation

> **The program.** We had to rebuild the ride-share data foundation
> to support an ML-driven surge-pricing model. Three streams: (1)
> event-collection SDK in the mobile apps (mobile team), (2)
> streaming pipeline into the lakehouse (platform team — *my* team),
> (3) feature store + serving (ML platform team). Six-month timeline,
> $2.4M budget, two external vendors.
>
> **Stakeholders.** Product (PM + director), Data Science (3 leads),
> Mobile Eng (eng manager), ML Platform (eng manager), Finance
> (budget owner), Legal (privacy review), Security (PII handling).
> Seven stakeholders, four of whom I had no direct authority over.
>
> **Decision matrix.** I owned the technical sequencing. Mobile
> owned the SDK release schedule. ML Platform owned the serving
> layer. Finance owned the budget. Privacy and Security had veto
> power on the data contract. Product owned the launch call. We
> agreed on the matrix in week 2.
>
> **What slipped.** In month 4, the mobile SDK slipped by 3 weeks
> because of an iOS 17 release conflict. That cascaded into the
> streaming pipeline (we couldn't test end-to-end without it) and
> into the feature store (we couldn't validate the schema). Three
> of seven streams were now blocked.
>
> **Tradeoff.** I had three options: (1) hold the launch and let
> all four blocked teams drift, (2) drop the iOS half of the launch
> (Android-only) and ship 70% of value, (3) decouple the pipeline
> from the SDK by using the legacy event format and a parallel
> bridge. I picked (3). It cost us 2 weeks of engineering effort
> on the bridge but unblocked all four teams.
>
> **Escalation.** I escalated to the VP twice. (1) When the
> decision matrix broke down over the Privacy review on the new
> event fields. (2) When Finance proposed pulling 30% of the
> budget because of a reorg mid-program. Both were scope-vs-money
> calls I couldn't resolve at director level.
>
> **Outcome.** Launched 3 weeks late, all six scope items shipped,
> $0.2M under budget. The bridge was retired in month 9 when the
> SDK was finally migrated. We measured 4.1% improvement in surge
> revenue in the first 90 days.
>
> **What I learned.** A program is run by *decisions you enable*,
> not *decisions you make*. The matrix is the work. The bridge
> was the easy part.

## What the interviewer is grading

**Google — Datavidhya 2026:** *"comfort with ambiguity"* and
*"collaboration."* Did you name the matrix, or did you give a
hero-narrator story about how you saved the launch?

**Meta — Aced 2026:** *"Be Open,"* *"Focus on Long-Term Impact,"*
and *"Move Fast."* Did you show the tradeoff honestly? Did you
escalate appropriately (twice is correct — zero means you didn't
need help; ten means you couldn't unstick anything)?

## The 4 failure modes

1. **Hero-narrator story** — "I single-handedly…" Wrong. Programs
   are team sports.
2. **No matrix** — if you can't name the decision rights, you
   didn't actually run the program; you ran a project.
3. **No failure beat** — every program slips. If your story has no
   slip, the interviewer assumes you're hiding it.
4. **No escalation** — running a program *requires* escalation. If
   you didn't escalate, either the program was too small to count
   or you weren't actually driving.

## Try it — your turn

Take any program from the last 2 years. Map it on the 5-component
framework:

1. Stakeholders — name them, count them, tag which you had
   authority over.
2. Matrix — write down who owned what decision.
3. Failure — name the slip. If there wasn't one, the program was
   too small to count for this question; pick another.
4. Escalation — count them. The right number for a 6-month
   program is 1-3.
5. Outcome — quantify (launch date, scope delivered, dollars,
   downstream impact).

## Pair with

- `06_de_project_deep_dive.md` — the 5-act project deep-dive is
  the *single-stream* version of this.
- `10_data_product_pride.md` — the program often produces the
  product you'll brag about later.
- `02_quantifying_impact.md` — every component needs a number.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
