# Hiring Plan

The resourcing doc says "3 people is the smallest team that doesn't
have a bus factor of 1; 4 is the smallest team that doesn't have
key-person dependency." This document is about the *hiring* that gets
us there, not the steady state — because the most-overlooked failure
mode in AI programs is assuming the team is staffed at the level
that's written in the org chart.

## The principle

> A hiring plan that doesn't account for time-to-hire is a wish list
> with a start date.

The "3 people, 6-quarter program" assumption in `resourcing.md` is
*steady state*. The realistic first 6 months have one of those seats
unfilled for some portion; my job is to plan around that, not to
pretend it isn't true.

## The base plan

Steady state per `resourcing.md`:

| Seat | Quarter it's filled |
|---|---|
| Senior ML engineer (eval + training) | Q1 |
| Platform engineer (serving + observability) | Q1 |
| Eng-lead hybrid (data curation, eval ownership) | Q1 |

So all three are "filled" at the start of Q1. Reality is different:

| Seat | Realistic fill-by | Why |
|---|---|---|
| Platform engineer | Q1 mid | Most advertised role; good candidates available |
| Senior ML engineer | Q2 (4–6 months) | Cold-market reality |
| Eng-lead hybrid | Q2 (6–8 months) | The role's ambiguity is the bottleneck |

Q1 starts with 1.5 of 3 seats filled. The plan accounts for that.

## What I do during the gap

This is the part most AI hiring plans ignore. The default answer is
"wait for the headcount to land." The right answer is something else.

### If the senior ML engineer hasn't been hired by mid-Q1

- The eng-lead hybrid ships the eval harness and the failure
  taxonomy, which are the most domain-specific deliverables.
- The platform engineer ships the serving skeleton with synthetic
  data.
- An **external consultant** is engaged, scoped to a 4-week
  deliverable: an independent review of the eval strategy and the
  first failure-taxonomy pass. Cost: $30k–$50k.
- The consultant's deliverable becomes a hiring signal: candidates
  who respond well to the rubric are interviewed; candidates who
  push back on it are rejected.

The consultant is not a substitute for the hire. The consultant is
the bridge that lets the program not stall.

### If the eng-lead hybrid hasn't been hired by mid-Q1

This is the bigger risk. The eng-lead hybrid owns the eval set —
the artifact the build-vs-buy doc says we can't proceed without.

- The senior ML engineer takes ownership of the eval-set design as
  a placeholder, with the trade-off that they are not the
  stakeholder-facing voice.
- Product hires a temporary "AI PM" contractor to do stakeholder
  alignment, scoped to the quarter. Cost: $30k for the quarter.
- The senior ML engineer and the AI PM contractor together produce
  enough of the eval set to unblock Q2.

Neither of these fixes the underlying gap, which is why the
consultant / AI PM contractor is *always* in the budget. The
question is when, not whether.

## The explicit four scores for evaluating senior ML candidates

The eval set in `../02-data-and-eval/eval-strategy.md` is the same
artifact I'd hire against. Five things I'd test a senior ML
candidate on:

| Test | What I'm looking for |
|---|---|
| **Calibration on eval design** | Does the candidate know the difference between a regression signal and a quality signal? |
| **Failure taxonomy instinct** | Given three example errors, can they bucket them and name the right lever? |
| **Cost-led reasoning** | Can they reason about $/task, not just quality? |
| **Bus-factor humility** | Do they ship work, or do they centralize expertise? |
| **Writing** | Will they leave behind a written record of decisions? |

The bar isn't calibration on a specific framework; it's calibration
on the *idea* of model work as measurement work.

## What the platform engineer looks like

The platform seat is "vLLM, Prometheus, Grafana, the OpenAI-compat
layer." That sentence covers roughly half the role. The other half
is:

- Budget gates and gate enforcement at the serving boundary.
- Adapter routing and alias management.
- Cost dashboard in cooperation with Finance.

This is *not* a pure-Infra engineer; the seat wants somebody who
can write application code in Python. A purely-Infra person
delivered without a Python application tends to treat the
application layer as someone else's job, and the budget gate ends
up living in a stub.

## What the eng-lead hybrid looks like

The hardest seat to fill and the one I'll spend the most time
sourcing for.

- Has shipped a public ML product before, end to end.
- Has stakeholder-facing experience (giving steering-committee
  reads).
- Can write code, but doesn't pretend to be the best engineer in
  the room.
- Has opinions about failure taxonomies.

I'd rather have a 0.6× ML engineer who can lead the team than a
1.0× ML engineer who can't talk to Finance. The team can backfill
technical depth with a fourth hire; it can't backfill stakeholder
trust.

## The red flags in the hiring funnel

| Flag | Why I'd pass |
|---|---|
| The candidate treats eval as a benchmark to defeat | Eval is a measurement, not a competition; defensiveness about it is disqualifying |
| The candidate overclaims LoRA fine-tune success | It's a 2-axis trade-off; "yes" or "no" without numbers is suspect |
| The candidate can't write code in a script review | Even the eng-lead hybrid has to ship |
| The candidate admits the org chart is more important than the work | Bus factor and trust are the same problem; if they don't see it, they aren't going to fix it |
| The candidate doesn't ask about budgets | A team member who doesn't see cost as part of the work is going to spend like it's not |

## The pipeline-build pattern

For a 200-person company with no AI infrastructure in place, the
candidate pipeline takes 6–9 months to be reliable. Things you can
do to compress that:

1. **Open-source contribution visibility.** The team's `agentic-ai/`
   projects are public. A candidate whose first question is about
   the code, not the salary, is the one to interview deeply.
2. **Adjacent referrals from network.** Most senior ML hires come
   through referrals; an active network is a multiplier.
3. **A senior-ML-as-advisor first.** A 1-day-a-week external
   advisor is a 6-month bridge to a real hire, and the advisor is
   often the network that surfaces the hire.
4. **Open-spec contract roles.** A 3-month "ML eval/curation
   engineer" contract role with a defined deliverable is how you
   ship Q3's eval-set refresh without adding headcount pressure.

## What I would not do

| Out | Why |
|---|---|
| Hire a Head of AI before n=5 is realistic | Empty chair costs $200k+ and no working team |
| Hire a second senior ML engineer before the first is productive | You don't know what your senior ML role actually is until the first one has shipped |
| Hire a research-only ML engineer | Path C is product-bound; research drifts |
| Hire on a single score-card | Pipeline needs more than one filter |
| Hire into a team whose eval set isn't there | Eager candidates, bad hires; the lack of a spec means you can't tell who's good |
| Cheap out on the eng-lead hybrid | The first hybrid hire sets the hiring pattern; mediocre hires beget mediocre hires |

## The rule I hold

> The first three hires set the team's ceiling. Cheap or rushed
> here and the team is expensive forever.

The third hire is the most important of the three. By then, the
first two hires have decided what their manager looks like; the
candidate you pick has to clear the bar they set, not the bar you
hoped for. This is also the hire most often under-discussed in
hiring plans.