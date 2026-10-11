# Lesson 10 — "What product that you led are you most proud of and why?"

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
>
> **Companion:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)
>
> **Pattern:** DE-flavored pride question. The "product" is a pipeline, dashboard, feature store, or model — not a UI.

---

## Why this lesson

The pride question is asked at every consumer-internet company — Meta,
Google, Netflix, Airbnb, Stripe, Uber. The trap is that most DE
candidates answer with *the project they shipped*, not *the product
they led*. The two are different:

- A **project** has a deadline, a launch, and an end-state.
- A **product** has users, a roadmap, and an adoption curve.

Interviewers want to hear that you have shipped something **that
people use**, not just something that exists. The signal of seniority
is whether you can describe adoption, retention, and iteration —
language that doesn't exist in a project narrative.

## The framework — 5 acts (the product version)

Use the same 5-act structure as `06_de_project_deep_dive.md`, but
swap the verbs:

| Project verb | Product verb |
|---|---|
| Shipped | Launched |
| Worked with | Served |
| Stakeholders aligned | Users adopted |
| Delivered | Iterated |
| Outcome | Outcome + retention |

## Worked example — ride-share driver-funnel dashboard

> **Act 1 — The user.** The dashboard serves three audiences: (1)
> driver operations — the people who intervene when a driver is
> churning, (2) product managers — the people who A/B-test the
> funnel, (3) ML engineers — the people who tune the
> recommendation models. Each audience has a different entry
> question; the dashboard serves all three.
>
> **Act 2 — Why it had to exist.** Before this, the funnel lived
> in three different notebooks maintained by three different
> analysts. Each one disagreed with the others by ±15%. The
> driver-ops team couldn't act on data they didn't trust. We had
> to consolidate, with one canonical funnel.
>
> **Act 3 — What I built.** A dbt-modeled star schema with `rides`
> as the fact and `drivers`, `riders`, `cities`, `surge_multipliers`
> as the dimensions, plus a `driver_funnel_daily` aggregate mart
> and a `surge_revenue_by_city` mart. The Looker layer sits on
> top, with three pre-built dashboards. ~9,000 lines of dbt SQL,
> 240 tests, 4 weekly stakeholders.
>
> **Act 4 — The launch and adoption.** Launched in Q2. By end of
> Q3, 11 of 14 driver-ops teams had migrated off the legacy
> notebooks. By end of Q4, 91% of all driver-churn investigations
> started from this dashboard (measured by Looker query patterns).
>
> **Act 5 — The iteration.** Q3 — added city-level surge revenue
> decomposition (operations request). Q4 — added A/B-test
> significance markers (ML eng request). Q1 — added a "data
> freshness" banner (operations request after a 6-hour outage
> that nobody knew was happening). The product is now on its 3rd
> major version.
>
> **Why I'm proud of it.** It replaced three incompatible
> notebooks with one canonical funnel that 14 teams trust. The
> pride isn't in the dbt SQL — it's that operations teams reach
> for it as their first tool, not their last.

## What the interviewer is grading

**Google — Datavidhya 2026:** *"Focus on Long-Term Impact."* Did
the product have a multi-quarter arc, or did you describe a
launch-and-forget project?

**Meta — Aced 2026:** *"Build Social Value"* + *"Focus on Long-Term
Impact."* Did the product serve *external* users (analysts,
operators, ML engineers, etc.) or only your own team?

**Stripe / Airbnb / Databricks:** *"Customer obsession."* Same
question, different framing — can you describe the user, not just
the architecture?

## The 4 failure modes

1. **Project, not product** — "I shipped a pipeline." That's a
   project. Where are the users? Where is the adoption curve?
2. **Architecture-only** — 4 minutes on the dbt models and 30
   seconds on the adoption. Reversed.
3. **No iteration** — products iterate. If your story ends at
   "launch," it isn't a product.
4. **No users, only stakeholders** — name the humans. Not "the
   analytics team." "Priya, who runs the India driver-ops pod,
   uses the city-level view 3x a day."

## The 30-second version (for the warm-up beat)

"My product is the driver-funnel dashboard. It replaced three
incompatible notebooks with one canonical funnel that 14 teams
trust. I'm proudest that operations teams reach for it as a first
tool — that's what tells me it's a product, not a project."

## Try it — your turn

Pick one DE artifact from the last 3 years. Run it through the
5-act framework. For each act, write down:

1. **User** — name them.
2. **Why it had to exist** — what was broken without it.
3. **What I built** — the artifact, in 2 sentences.
4. **Adoption** — quantified (number of teams / number of users /
   query volume).
5. **Iteration** — at least 2 cycles.

If any act is empty, the artifact is a project, not a product. Pick
another.

## Pair with

- `06_de_project_deep_dive.md` — the project deep-dive structure.
- `09_complex_program_stakeholders.md` — often the product came out
  of the program.
- `02_quantifying_impact.md` — adoption, retention, and iteration
  all need numbers.

---

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
