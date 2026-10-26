# The AI Roadmap & ROI Framework

> **Section 3 deliverable.** Maps to *AI Project Roadmaps* (14:21),
> *Building AI Teams* (20:26), *Delivering AI ROI* (9:59),
> *AI Leadership: Fostering Adoption* (11:24).
>
> For the leader who already approved a project and now has to deliver it.

---

## The ROI question nobody asks

> **"What's the honest denominator?"**

Most AI ROI calculations divide by project cost and never divide by the
organisation's total AI spend. That produces a number your board cannot
reconcile, because they know what the *portfolio* cost, not what this project
cost.

The framing that holds up in a board meeting:

```
Net value      = (hours saved × loaded cost + revenue gained
                  + error cost avoided)  −  total cost of ownership

Total cost of ownership is NOT "the project budget."
It is: build + 12 months of inference + the FTE time to maintain it
       + the opportunity cost of the engineers who weren't building roadmap
```

The opportunity-cost line is the one people leave out, and it's the one a
finance-minded exec will ask about.

---

## The 90-day proof

The fastest way to kill a bad AI project is to make it small and real.

| Window | What happens | What you're proving |
|---|---|---|
| Days 1–30 | One workflow, one team, real data, human-in-the-loop throughout | Does it work on our data? |
| Days 31–60 | Same workflow, 3× volume, failure taxonomy built | Does it hold up under load? |
| Days 61–90 | Second workflow OR hard cutover | Is the ROI real at scale? |

**The rule:** no org-wide rollout before day 90. Every failed AI programme
you're aware of scaled before the failure modes were known.

---

## Managing uncertainty (the R&D case)

Not every AI project should have a business case in the traditional sense.
Some are genuine bets on capability. The mistake is pretending they're not —
giving a bet a P&L-shaped justification so it survives scrutiny it was never
meant to pass.

**Two portfolios, funded differently:**

| | **Core** | **Bet** |
|---|---|---|
| Purpose | Efficiency, measurable ROI | Capability the market may need in 12–18mo |
| Funding | Annual budget, business case | Ring-fenced, ring-fenced from Core |
| Success | P&L metric | Capability demonstrated, even if unmonetised |
| Failure | Kill on miss | Expected; judge on learning |
| Typical size | 60–80% of spend | 20–40% of spend |

The failure mode is Core projects quietly becoming bets ("we can't measure
this yet") — at which point you have no bets, just unmeasurable Core.

---

## Team structure

*Building AI Teams* (20:26). Three shapes that work, in order of how common
they get it right:

### 1. Central AI team (works up to ~50 engineers of AI surface area)

A small team owns models, evals, and shared tooling. Product teams consume.
**Risk:** becomes a bottleneck; the central team becomes the people who
"approve AI."

### 2. Embedded/platform (works at scale)

Shared platform (evals, guardrails, gateway) + embedded AI engineers in
product teams who own their own models. **Most common correct answer** for
organisations past the pilot stage.

### 3. Federated (works when data is the moat)

Each business unit owns its models; a thin centre sets standards. Only works
if the central team genuinely doesn't grow into a bottleneck.

**The critical skills gap** — the thing no course lists clearly enough:

| Role | Why it's scarce | Common mistake |
|---|---|---|
| **AI PM** | Doesn't exist as a career yet; poached from PM or consulting | Hiring a PM who's never run an AI project |
| **Evals engineer** | New discipline; nearest analogue is SRE or QA | Assuming "QA will cover it" — evals are model-quality, not test-coverage |
| **AI product engineer** | Rare; bridges ML and product | Splitting into "ML engineer" and "product engineer" and hoping they talk |

---

## Adoption: the boring failure

The most expensive AI failures are technical, but the most *frequent* are
adoption failures. The project worked; nobody changed their behaviour.

**What actually works** (ranked by effect size):

1. **Ship into an existing workflow.** Nobody adopts a new tool. They adopt
   something that removed a step from a tool they already open.
2. **Name a single accountable owner.** Not a committee. One person whose
   job includes "does this get used."
3. **Measure usage from week one.** If weekly active use isn't growing by
   week 4, fix adoption before building more features.
4. **Show the person's own time saved.** Not "the org saved $X." "You no
   longer do this task" converts; "we saved $X" does not.

---

## Positioning for change (workforce impact)

The workforce question is real and it's a leadership question, not an HR
question alone. The useful framing:

| Horizon | Change | What a leader actually does |
|---|---|---|
| Now | Task-level augmentation | Redesign the job, not the headcount |
| ~18mo | Role-level change | Re-train; decide honestly who can move |
| ~36mo | Org-level change | Fewer roles, more scope per role |

The trap is leading with "AI will replace X jobs," which is both
indefensible (too precise) and politically fatal (loses the room). Leading
with "here's what we're doing to make sure the people here are the ones AI
needs" keeps the same substance and doesn't poison the discussion.

---

## The one-page delivery review

Run this monthly. Four questions:

1. **What's the measured ROI so far**, against the baseline we recorded?
2. **What did we learn** that changes the next project's assumption?
3. **What's blocking adoption**, and is it technical or organisational?
4. **Kill, continue, or scale** — and what's the next kill criterion date?

If question 4 has no date attached, the project never dies and never frees
budget for the next one.

---

**Last updated:** 2026-10-21