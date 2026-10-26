# Performance Review Rubric

A review rubric is what you give the team when you can't be in the
room for every decision. This is the rubric I'd ship to the AI
team — the criteria a member of the AI team is reviewed against,
with the same weights and the same language both sides have to
work from.

## Why this exists

Performance reviews for AI roles are subtly different from reviews
for engineering or PM roles. Engineering: shipped code on time.
PM: shipped product on time. AI: shipped **measured outcomes**, and
"measured" is the part that doesn't have a default.

A team evaluated on shipped artifacts without measurement produces
artifacts that don't move the business. A team evaluated on
measurement without artifacts produces dashboards nobody acts on.
Both have to count, or you get the wrong one.

## The four dimensions, weighted equally

Most performance rubrics weight by hard-skills vs soft-skills. This
rubric doesn't, because the AI team is too small to special-case
reviewers. Each of the four dimensions is 25% of the score, no
exceptions:

| # | Dimension | What it means |
|---|---|---|
| **1. Decision quality** | The choices this person makes — model selection, eval criteria, taxonomy buckets — are they defensible? |
| **2. Operational excellence** | Does what they ship stay working? Do they handle on-call cleanly? Do they own things beyond the initial commit? |
| **3. Stakeholder alignment** | Does the rest of the company know what this person is doing, and trust their judgment? |
| **4. Leverage** | Are they making the team faster, not just doing their job? |

The four-dimension split is specific. An engineer who writes
beautiful code but doesn't handle incidents scores 4,4,2,1. A
stakeholder-friendly hire who can't ship scores 2,2,4,2. Neither is
a top performer; one is a "platform engineer I want to grow" and
the other is "an analyst I'll convert to engineering once they have
scope."

## Dimension 1 — Decision quality (with examples)

This is the AI-team-specific dimension. Reviewer grades the
*reasons*, not the outcomes, because outcomes are noisy.

**5 — Top decile**

- Argues against an initiative from a base-rate perspective.
- Picks models on cost-per-task, not on benchmarks.
- Wrote a failure taxonomy that survived a re-org and is still in use.
- Owned a kill decision that saved the program a quarter.

**3 — On track**

- Documents decisions in writing.
- Cites cost and quality in proposals.
- Updates the failure taxonomy when new buckets appear.

**1 — Below bar**

- Picks models based on leaderboard scores.
- Cannot articulate the trade-off between regression and quality signals.
- "Improve the model" is the default plan.

A team member at score 3 is a healthy contributor. Score 5 is what
you promote; score 1 is a coached-development conversation.

## Dimension 2 — Operational excellence (the boring one)

This is the dimension where most engineers grade themselves too
high. Reviewer grades the systems they leave behind, not the
artifacts they shipped.

**Indicators:**

- Uptime of systems they own (cumulative, last 12 months).
- Mean time to recovery.
- Alert volume (did they add alerts with no runbook entry?).
- Drift/quality response time.

A score of 5 here means the person shipped something that's been
up for 90+ days without escalations, and someone else can be on-call
for it without paging the original owner.

## Dimension 3 — Stakeholder alignment

The harder non-technical dimension. Reviewer grades it on evidence:
do other parts of the company know what this person does, and do
they trust them?

**Indicators:**

- Are the steering-committee reads from this person accurate and
  defensible?
- Does Finance get a number they trust?
- Does Product use the team's output without checking the
  underlying machinery?

A score of 5 here means the person is operating like a Head of AI
already, scaled down. A score of 1 means the rest of the company
hasn't heard from them.

## Dimension 4 — Leverage

A person who does their job well but doesn't make anyone else's
job easier is a sustainable hire but a flat ceiling. Leverage is
the dimension that grades "how much faster does the team move as
a function of this person's existence?"

**Indicators:**

- Onboarding materials they own.
- Code reviews paired with new-hire feedback.
- Runbooks, write-ups, and rubric design that scales beyond them.
- Adoption of artifacts they create by people who didn't create them.

A score of 5 here means removing the person from the team would
make every other team member slower. A score of 1 means removing
them would mostly be a task-rebalance.

## The anti-patterns this rubric protects against

| Anti-pattern | What the rubric does |
|---|---|
| Engineer who ships a fragile model that impresses in demo | Decision-quality 1, operational 1 — calibrated |
| Engineer who manages up well but can't debug | Stakeholder 4, decision-quality 1 |
| Engineer who builds great eval but ships nothing visible | Decision 5, operational 3 — solid contributor; promotion needs more |
| Head of AI builds a dashboard nobody trusts | All four drop on next cycle's downstream signal |

Each anti-pattern has a single dominant dimension, and the rubric
catches it because no dimension covers for the others.

## The half-year cadence

The rubric is read against the prior two quarters' evidence, not
just the most recent. AI work has compounding effects (a clean eval
set compounds for years; a fragile model compounds in failure). A
reviewer reading only the last quarter misses this.

For reviews:

- **Quarterly** informal read: peer feedback, no manager score.
- **Half-year** formal review: manager score on all four dimensions,
  calibrated by the peer feedback.
- **Annually** calibration: scores of 1's and 5's defended with
  evidence across the cohort.

Half-year is the right cadence. Quarterly reviews that rate-score
are too volatile; annual ones let problems compound.

## The rule I hold

> A review rubric with no anti-pattern is a self-assessment form.
> A review rubric with anti-patterns but no evidence threshold is
> a vibes-based manager review. The rubric that earns its keep
> names both, and a year from now still produces scores that
> nobody contests.

The first year of a new rubric produces arguments. The second year,
the arguments shrink. The third year, it's the team's reference.
That's the test I apply.