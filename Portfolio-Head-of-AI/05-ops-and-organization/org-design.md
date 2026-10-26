# Org Design

Org design is what you'd write if you had to fill out a P&L for an
org chart that doesn't exist yet. This document is the structure
I'd commit to at each size the company might be, and what the
team is *for* at each size — not the org chart for its own sake.

## The principle

> An org chart is a budget artifact before it's a people artifact.

Every role in a Head-of-AI organization has three questions
attached: who pays for it, what does it deliver, and what breaks if
it's missing. Org design without those questions attached is fan
fiction.

## At <200 people, <5 AI engineers (the common shape)

There is no AI org as such. There are people whose titles have AI in
them, and an engineering organization that owns the AI work. The
Head of AI, if there is one, is an eng-lead hybrid wearing a hat.

```
    VP of Engineering
            │
            ├─── Eng Lead (AI) — eng-lead hybrid
            │       │
            │       ├─── Senior ML Engineer
            │       │
            │       └─── Platform Engineer (serving + obs)
            │
            └─── (other engineering teams)
```

This is the structure the build-vs-buy doc and the resourcing doc
both assume. The bus factor risk [R5 in
`../04-delivery/risk-register.md`](./risk-register.md#the-12-risks-ill-defend)
is real here; if any one of those three people is unavailable for two
weeks, the program stalls. Pair programming for serving infra, on-
call rotation between ML and platform, and explicit documentation
ownership are the only mitigations that work at this size.

The "eng-lead hybrid" is what I'd call the most-load-bearing role.
It is part-time technical — they have commit rights on the codebase —
and part-time stakeholder-facing. Their job is to refuse to let the
team optimize the wrong metric, and that requires a seat at the
table, not an office.

## At 200–500 people, 5–15 AI engineers

The Head of AI exists as a role. The team still reports into
engineering for shared infrastructure, but the Head has direct
authority over the AI program and priority-setting.

```
              Head of AI
                  │
   ┌──────────────┼──────────────┬──────────────┐
   │              │              │              │
 ML Eng Lead   Platform Lead   Eval/         PM/GTM
 (training +    (serving +      Curation      (adoption +
 models)        observability)  Lead          comms)
```

Two changes from the <200 shape:

- The eng-lead hybrid role splits into a *PM* and an *ML Eng Lead*.
  The hybrid stops scaling at this size; you need both jobs done
  full-time.
- The Eval/Curation Lead becomes a real role. This is the team
  member who owns the eval set and the failure taxonomy; without
  it, R2 (eval set is wrong) becomes a near-certainty.

Headcount targets per area:

| Area | Headcount | What it owns |
|---|---|---|
| ML Eng | 4–6 | Models, training, evaluation rubric |
| Platform | 2–3 | Serving, infra, observability |
| Eval/Curation | 1–2 | Eval set, taxonomy, rater program |
| PM | 1 | Roadmap, leadership comms, adoption |
| **Total** | **8–12** | |

The 8–12 ceiling is a budget artifact as much as an org one. At
200 people, this team is already a substantial fraction of the
engineering org. Funding it means the AI program has a clear
6-quarter road map and the AI spend has CFO visibility. Both happen
in a real engagement; neither happens on a slide.

## At 500–2,000 people, 15–50 AI engineers

The team starts to specialize. Three structural changes:

1. **A separate serving team.** The serving stack now serves
   multiple AI applications; it can't sit inside the ML team's
   backlog. A 3–5 person SRE/serving team owns the gate, the vLLM
   hosts, and the OpenAI-compat layer.

2. **A research arm.** A small (<5%) team dedicated to evaluating
   new models, new serving patterns, and new datasets. Without this,
   the team re-implements every choice every quarter, and the
   re-implementation can't keep up with the field.

3. **A governance role.** Not a committee; an individual. Risk
   tiering, audit-trail QA, vendor compliance — this is its own
   job at this size, even if it's hard to fund because it has no
   visible deliverable.

```
                 Head of AI
                    │
   ┌────────────────┼────────────────┬─────────────┐
   │                │                │             │
 ML Eng        Serving/SRE       Eval/Curation  Governance
 Director      Director          Director       Lead
   │                │                │             │
 (4–8 people,    (5–10 people,    (3–6 people,  (1–3 people,
 multiple       vLLM, gates,     rater program,  risk tier,
 model          adapter routing, eval harness,  audit log,
 programs)      on-call)         taxonomy)       vendor due
                                               dil.)
```

The team is starting to look like a real AI org, but it isn't yet
a *platform*: that's the next size.

## At 2,000+ people, 50+ AI engineers

The team becomes a platform. Multiple business units consume shared
infra. New headcount is split between platform (sustaining, shared
infrastructure) and product (business-unit-specific applications).

I have less direct experience at this size; the structural lessons
I trust come from outside observation:

- A platform team that doesn't have product customers fails.
  Pick 2–3 internal customers in the first 6 months; build for
  them; resist the temptation to be a general-purpose platform.
- Headcount funded for "shared infra" is a great hide-and-seek
  game; every dollar needs a named internal customer.
- A research arm that's not connected to product engineering
  builds demos that don't ship. Co-location is the only thing
  that prevents this; org charts aren't.

I'd argue *against* a Head of AI org chart as a one-platform-team
self-contained function at this size; the right shape is an
enterprise AI platform with product-aligned application engineers
embedded in each business unit.

## What changes and what doesn't across all four sizes

| Element | <200 | 200–500 | 500–2,000 | 2,000+ |
|---|---|---|---|---|
| Head of AI role | Hat, hybrid | Dedicated | Director-level | VP-level |
| ML Eng | 1–2 | 4–6 | 4–8 | 8–20 |
| Platform/Serving | 1 | 2–3 | 5–10 | 10–30 |
| Eval/Curation | 0.5 (hybrid) | 1–2 | 3–6 | 5–10 |
| Governance | None | 1 part-time | 1–3 | 5–10 |
| Reporting line into Eng? | Yes | Yes | Mostly | Hybrid |
| Reporting line into Product? | No | Some | Mostly | Yes |

The "Eval/Curation" column is the one teams most under-fund at
every size. It's also the single function whose absence guarantees
quality complaints for years.

## The forbidden org-chart moves

| Move | Why |
|---|---|
| A "Head of AI" before n≥5 | The role's mandates don't materialize at n<5; you fund an empty chair |
| A separate "AI Ethics" team reporting to legal only | AI ethics is a *practice*, not a function. If it lives separately, it's an obstacle. |
| A "Prompt Engineer" as a full-time role | Prompting is a skill; in-house prompt engineering tends to optimize toward locally-better prompts that don't generalize |
| An "AI PM" team with no engineers | A PM team without engineering is a briefing document factory |
| Reporting structures that put AI under Data | Data orgs have different priorities (latency, freshness) than AI orgs (quality, audit). Under Data, AI is a workstream. |

The last point is the most controversial. There are real
arguments for AI-reporting-into-Data at smaller sizes, and I've
seen it work. The argument against is that Data's review cadence
and risk profile aren't built for the model-control-plane. If the
choice is between "AI under Data with no engineering influence" and
"AI under Engineering with no data infrastructure investment," I'd
pick Engineering. The third option — "a Head of AI who reports in
to neither, with direct budget authority" — is what earns the role
at scale.

## The rule I hold

> The first org-design mistake to avoid is adding people before
> adding clarity.

An org with a Head of AI, three directors, and no eval set has a
100k/month operating cost and no experiment in flight. An org with
three engineers and a working eval set has a 60k/month operating
cost and three experiments in flight. The second one is the better
AI program.