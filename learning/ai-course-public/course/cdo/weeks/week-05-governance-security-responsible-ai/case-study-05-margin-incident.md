# Case Study 5: The Margin Incident

> **Week 5 · Case Study · 90 min**
> **Deliverable:** Walk the recovery from a wrong-margin-during-board-review incident in 30 minutes.

## The brief

You are 15 minutes into a board review. The CFO presents the Q2 numbers. The board member who chairs the audit committee interrupts: "These margins don't match what I saw last week. We're 2 points below what we projected in May." The CFO looks at the deck. The deck shows 28% gross margin. The board member has a printout showing 30%. The room goes quiet.

**You are the CDO.** The deck numbers came from the data platform you own. You have 30 minutes to:
- Acknowledge the discrepancy (in the room, in real time)
- Investigate the cause
- Communicate the resolution
- Defend the recovery to the board

## The structure (30 minutes total)

| Section | Time | What to say |
|---|---|---|
| Acknowledge | 2 min | In the room, immediately |
| Investigate | 8 min | Pull the data; find the discrepancy; identify the cause |
| Communicate | 5 min | What the right number is, why it was wrong, who's accountable |
| Remediate | 10 min | What you'll do in the next 24h, 1 week, 1 month |
| Defend | 5 min | Take questions from the board |

## The scoring rubric (out of 100)

| Competency | Weight | What "great" looks like |
|---|---|---|
| Governance and risk | 30% | The root cause is in the data flow, not the people |
| Leadership and executive influence | 25% | The board trusts you; the CFO is supported, not thrown under the bus |
| Communication and structure | 20% | The room calms; the message is clear |
| Ownership and measurable impact | 15% | The action items have owners and dates |
| Strategic and business thinking | 10% | The fix is a system change, not a one-off |

A score below 90 means Week 5 is not done. Re-record.

## Acceptance criteria

- 30 minutes, no overrun
- Acknowledge in the first 2 minutes (no defensiveness)
- Find the root cause (not the symptom)
- Name the right number with a source
- Name the "what changed" between May and Q2
- Name the action items (24h / 1 week / 1 month) with owners
- "How do we prevent this from happening again?" answered
- "Who is accountable?" answered

## Starter

Use Day 25's crisis playbook. The phases are: detect, triage, contain, communicate, post-mortem. Adapt to a wrong-number-in-deck scenario.

## Solution sketch (do not copy — internalize and re-speak)

**Acknowledge (2 min):**
- "Chair, you're right to flag this. I own the data behind that number. Let me look at it right now."
- "I don't have an answer in the room. I'll come back with one within 30 minutes."
- (Do not defend the deck. Do not blame the CFO. Acknowledge and commit to investigate.)

**Investigate (8 min):**
- Step out; bring the data team into a war-room
- Pull the source data: orders, COGS, returns, allocations
- Compare the Q2 actuals vs. the May projection
- Find the discrepancy: likely a definition change, a late allocation, or a data pipeline break
- **The cause is almost always one of:**
  - A change in the definition of "gross margin" between May and Q2
  - A late allocation (returns, freight, marketing) that hit Q2 but not the May projection
  - A data pipeline break (one source system stopped sending)
  - A semantic layer change that wasn't propagated to the deck
- Identify the right number with a single source of truth

**Communicate (5 min):**
- Return to the room
- "The right number is 30.1%. The deck shows 28% because [one specific cause]."
- "The discrepancy is $XM, driven by [Y category / Z allocation]."
- "This is my accountability. The deck is generated from [system]. The cause is [root cause]."
- (Do not blame the CFO. Do not blame the team. Own it.)

**Remediate (10 min):**
- **24h:** Correct the deck; re-issue to the board; brief the CEO and audit chair
- **1 week:** Fix the data pipeline / semantic layer; add a data quality check that would have caught this
- **1 month:** Implement a pre-board-review validation: every number in the deck traced to source, signed off by data + finance
- **Quarterly:** Add the metric to the data quality scorecard; assign an owner

**Defend (5 min) — be ready for:**
- "How did this get through?" (it didn't; we caught it because the audit chair was prepared)
- "Who is accountable?" (me; the CFO owns the number, I own the data)
- "How do we prevent this from happening again?" (validation process + DQ scorecard + sign-off)
- "Should we re-state Q1?" (if the same issue existed in Q1, yes; if not, no)

## What to watch for when you re-listen

- **Did you acknowledge in the first 2 minutes?** Defensiveness kills trust.
- **Did you own it without throwing the team under the bus?** The CDO is accountable for the data; the team is accountable for execution.
- **Did you name the root cause, not the symptom?** "The pipeline broke" is a symptom. "The pipeline broke because the source system changed its schema and we didn't have a contract" is a root cause.
- **Did you end on time?** If you run over, the board concludes you can't manage a crisis.

## Re-record until you score ≥ 90

A CDO who can't handle a wrong-number-in-the-board-deck is not a CDO. This is the most-tested executive crisis scenario.

---

**Next:** Week 6, Day 26 — Organization Design.