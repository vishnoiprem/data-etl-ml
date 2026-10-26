# Risk Register

AI initiatives get killed by risks nobody put on paper until they
fired. This document names the ones I expect to hit, names their
probability honestly, and names the response ahead of time. The
document is intentionally short — every line is a risk I'd defend
in a steering committee, not a comprehensive-but-shallow catalog.

## Scoring convention

- **L** = likelihood (1 = unlikely, 5 = near-certain).
- **I** = impact (1 = fixed in a day, 5 = program-ending).
- **Score = L × I**, scale 1–25.

I keep scores off the dashboard. They are conversation-starters, not
metrics. People anchor on numbers that look precise and forget that
"I'm 60% confident this is a 12" is exactly as firm as the underlying
opinion, which is not at all.

## The 12 risks I'll defend

| # | Risk | L | I | Score | Trigger | Response |
|---|---|---|---|---|---|---|
| R1 | **Fine-tune shows no measurable improvement.** | 4 | 4 | 16 | Tier-2 holdout improvement < 3 pts after 6 weeks training | Trigger kill criterion (Q4 → Q5 gate in `roadmap.md`); migrate to bigger base via vendor evaluation |
| R2 | **Eval set is wrong / task is underspecified.** | 3 | 5 | 15 | Raters disagree on > 20% of rows; "improved" doesn't correlate with user-reported quality | Stop modeling. Re-do eval design. This is the foundation. |
| R3 | **Base model is deprecated / pricing changes mid-program.** | 4 | 3 | 12 | Vendor announces new pricing or sunset; HF base yanked | Open base pinning (`base_model_revision` in `architecture.md`); swap base; re-evaluate adapter; document `migration-cost` row for leadership |
| R4 | **Drift causes silent quality regression.** | 4 | 4 | 16 | Drift score > 0.3 for 5 consecutive days, no obvious upstream cause | Forced re-evaluation; freeze training; point `@Champion` at previous alias |
| R5 | **Single-engineer bus factor on serving stack.** | 4 | 5 | 20 | One engineer owns vLLM, Prometheus, and the FastAPI wrapper | Pair across two engineers immediately; kill this risk by Q1.5; per `constraints.md` §5 |
| R6 | **Annotation/eval vendor misses the deadline.** | 3 | 3 | 9 | Rater deliverable slipped two weeks | In-house fallback; if it's a chronic miss, switch rater vendors |
| R7 | **Customer data lands in training set without consent.** | 3 | 5 | 15 | Audit discovers PII in adapter training set; ticket-corpus provenance undocumented | Hard stop; not a 4-week fix. Origin of this constraint: `constraints.md` §2 |
| R8 | **Inference spend exceeds budget without a gate trip.** | 2 | 4 | 8 | Cost panel climbs without alerting | Gates must be live before GA; verify per `cost-model.md` |
| R9 | **MitM or prompt-injection breaches the API boundary.** | 4 | 4 | 16 | Public report of similar attack; red-team finds it in our system | Kill switch in `gates.py`; rate-limit by source; incident review per `incident-postmortem.md` template (TBD) |
| R10 | **First rerun of training produces a worse model and ships.** | 2 | 5 | 10 | `@Champion` alias rolled to a bad run | Alias is two-step: human approval + automated regression-check before promotion |
| R11 | **Hallucinated output reaches customer; no audit trail.** | 4 | 5 | 20 | Customer reports a confidently-wrong answer we can't trace | This is the reason for `run_id` everywhere. Investigate; patch; document |
| R12 | **AI hype cycle moves funding away from AI** | 3 | 4 | 12 | Macro budget cuts; AI ROI pressure | Have the cost-model number ready; quarterly "what we're buying with the next dollar" |

The two 20-scores are the ones to over-defend: R5 (bus factor on
serving) and R11 (no audit trail). Both are pre-existing conditions
in most 200-person AI programs; both fail loudly only when they've
already cost a quarter.

## The kill-criterion is itself a risk-handling artifact

The Q4 kill criterion in
`../04-delivery/roadmap.md#what-the-gates-look-like-concretely`
exists specifically to compress R1 from "we'll handle it" to "we
named the handling in advance." Without that, R1 is the one that
eats 6 months.

## Risk register vs. risk register-and-forget

I am explicit about the cost of treating this document as inert:

- A risk not assigned an owner is a risk nobody acts on.
- A risk not on a quarterly review is a risk we never recover from.
- A risk with a response that can't be triggered by a real signal
  is a wish.

So:

- Every row above has a trigger and an owner (the column is the
  trigger; the owner is the [role in `resourcing.md`](./resourcing.md#the-minimum-composition)).
- The register is reviewed at the quarterly steering meeting.
- A risk whose trigger fires is treated as a `P0`-equivalent for
  one cycle; that decision lives in `incident-postmortem.md`.

## Risks I deliberately don't track here

| Out | Why |
|---|---|
| "Model gives different answer same input" | Operational phenomenon handled by R4; not a strategic risk |
| "Vendor raises prices 10%" | Bake into cost sensitivity table in `cost-model.md` |
| "Engineer leaves" | Owned by `resourcing.md`; bus-factor risk is R5 |
| "GPU supply tightens" | Cost consequence; revisit if capex gates re-open |
| "EU AI Act changes" | Compliance handles in their own register; ours tracks only the impact on our risk tier |
| "AI does/will replace us" | Out of scope |

The temptation is to list every hypothetical. Resist it. A 60-row
risk register is unread. A 12-row register with triggers is read.

## What I expect to happen in the first 12 weeks

The honest pre-mortem:

- **R4 (drift) will fire in some form** within the first 3 months.
  Drift *always* happens; what matters is response time and not
  pretending it didn't.
- **R5 (bus factor) will get tested** if the serving engineer is
  sick for a week in month 2. Pair for resilience starting day
  one; don't wait for the test.
- **R7 (data provenance) will be the long pole.** It always is.
  Legal review is the constraint, not engineering.

Each of these is named so I am *less surprised* when they fire.
Not naming them doesn't prevent them; it just means I show up
unprepared.

## The rule I hold

> A risk register without triggers is fiction. A risk register
> without owners is aspiration. The one that earns its keep has
> both, reviewed quarterly, with one or two rows changed.

That's what this is.