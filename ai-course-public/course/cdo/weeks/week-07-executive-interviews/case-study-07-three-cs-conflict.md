# Case Study 7: The Three-C's Conflict

> **Week 7 · Case Study · 90 min**
> **Deliverable:** Resolve a CEO-wants-speed / CFO-wants-cost / CTO-wants-security conflict in 30 minutes.

## The brief

You are 6 months into the CDO role. Three C-level peers have a conflict that you have to resolve (or escalate). The board is watching.

**The conflict:**

- **CEO:** "Ship the AI mandate by year-end. Speed. We promised the board."
- **CFO:** "Cut the data budget by 15%. The macro is tightening. Show me the savings."
- **CTO:** "We're not secure enough to ship AI in production. We need a 6-month security uplift first. Compliance is non-negotiable."

Each C has a legitimate position. Each C is right. Each C is also wrong — they're not seeing the others' constraints.

**Your task:** Mediate. Find a path that:
- Ships something visible to the board (the CEO's win)
- Cuts 15% from the budget (the CFO's win)
- Doesn't compromise the security posture (the CTO's win)
- Doesn't break the data team or the BU relationships

You have 30 minutes in front of the three Cs. They will challenge every trade-off.

## The structure (30 minutes total)

| Section | Time | What to say |
|---|---|---|
| The framing | 3 min | Name the conflict; reframe as joint problem |
| The diagnosis | 5 min | What each C sees that the others don't |
| The proposal | 10 min | The path that hits all three |
| The trade-offs | 7 min | What each C gives up |
| The asks | 5 min | What each C commits to |

## The scoring rubric (out of 100)

| Competency | Weight | What "great" looks like |
|---|---|---|
| Leadership and executive influence | 30% | The 3 Cs sign off; nobody feels rolled |
| Strategic and business thinking | 20% | The path hits the strategy |
| Communication and structure | 20% | The 3 Cs feel heard; the room calms |
| Commercial and financial understanding | 15% | The CFO sees the savings; the math holds |
| Governance and risk | 15% | The CTO's posture is preserved |

A score below 90 means Week 7 is not done. Re-record.

## Acceptance criteria

- 30 minutes, no overrun
- 0 defensiveness in the opening 2 minutes
- Each C's position named and validated
- Joint problem framed
- Path that hits all three constraints
- Trade-offs explicit
- Each C's ask named
- "What if it still doesn't work?" answered

## Starter

Use Day 04 (influence), Day 25 (crisis), Day 26 (org design), Day 30 (FinOps). Synthesize.

## Solution sketch (do not copy — internalize and re-speak)

**Framing (3 min):**
- "We're here because we have three legitimate constraints, not three competing priorities. Let me name each of yours, then propose a path that hits all three."
- Validate each: "CEO, the board mandate is real. CFO, the macro is real. CTO, the security posture is real. All three. The job is to find a path that respects all three."

**Diagnosis (5 min):**
- CEO: speed, because the board mandate is a clock. The hidden cost: shipping insecure AI is worse than shipping late AI.
- CFO: cost, because the macro is tightening. The hidden cost: cutting the foundation cuts the AI ROI.
- CTO: security, because the AI Act + the breach risk are real. The hidden cost: 6 months of no AI is a board-level problem.

**Proposal (10 min):**

| Constraint | Path |
|---|---|
| CEO — ship by year-end | Ship 1 AI in production in 9 months (not 5), on a constrained scope (not 5 use cases) |
| CFO — cut 15% | Cut 15% from infrastructure (consolidate 3 warehouses → 1; renegotiate cloud commit), not from people or AI |
| CTO — secure posture | Run security review in parallel, not in sequence; cut 1-2 use cases from scope to lower attack surface |

The 1 AI: pick the one with the smallest data surface (e.g., document intelligence over internal documents, not customer-facing). Ship in 9 months, not 6, but the security review is concurrent, not blocking.

The 15% cut: $XM/year from infra, $Y from vendor renegotiation, $0 from people. Funded by the FinOps framework from Day 30.

The security posture: 5 high-priority controls implemented in the 9 months (IAM, encryption, lineage, audit, key mgmt). CTO's win: no AI ships without all 5.

**Trade-offs (7 min):**
- CEO gives up: 6-month timeline → 9-month timeline
- CFO gives up: cut concentrated in infra, not people (less politically clean)
- CTO gives up: 6-month security review → concurrent security review; 1-2 use cases cut from scope

**Asks (5 min):**
- CEO: back the 9-month plan with the board; defend the 1-AI scope
- CFO: approve the infra consolidation; back the FinOps framework
- CTO: own the security review; sign off on the 1-AI scope before ship

**Q&A — be ready for:**
- "What if the board doesn't accept 9 months?" (we go with 1 AI in 6 months on a smaller scope; quality trade-off is on the table)
- "What if the infra consolidation takes longer than expected?" (we have a phased plan; we cut 8% in the first 6 months, 7% in the second 6)
- "What if the security review finds a blocker?" (we cut scope further; we don't ship insecure AI)
- "What if a BU head still pushes for 5 AI?" (we communicate the trade-off; we offer the 1 AI as proof, then scale)

## What to watch for when you re-listen

- **Did you validate each C first?** If they don't feel heard, they won't sign off.
- **Did you reframe as joint problem?** If the room thinks it's "CEO vs. CFO," you've lost.
- **Did you name every trade-off?** A proposal without trade-offs is a wish.
- **Did you end on time?** If you run over, the Cs conclude you can't manage complexity.

## Re-record until you score ≥ 90

A CDO who can't mediate a 3-C conflict in 30 minutes is not a CDO. The 3-C mediation is the most-tested executive scenario.

---

**Next:** Week 8, Day 36 — Career Positioning.